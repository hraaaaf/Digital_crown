import React, { useState, useEffect, useCallback } from 'react';
import {
  Camera, Printer, FileText, CheckCircle2, AlertTriangle,
  XCircle, ChevronDown, ChevronUp, Loader2, Archive, Eye,
  Activity, Shield,
} from 'lucide-react';
import { useOrthoStore } from '../stores/useOrthoStore';
import { REQUIRED_LANDMARKS } from '../cephaloShared';
import { api } from '../../../services/api';
import toast from 'react-hot-toast';

interface Step4DocumentsProps {
  P: any;
}

// --- Angle metadata for summary cards ---
const ANGLE_CARDS = [
  { key: 'SNA',            label: 'SNA',         unit: '°', lo: 76, hi: 88,   flo: 60,  fhi: 105 },
  { key: 'SNB',            label: 'SNB',         unit: '°', lo: 74, hi: 86,   flo: 58,  fhi: 102 },
  { key: 'ANB',            label: 'ANB',         unit: '°', lo: -2, hi: 6,    flo: -10, fhi: 15  },
  { key: 'I_Francfort',    label: '1 / Francfort', unit: '°', lo: 102, hi: 112, flo: 60, fhi: 155 },
  { key: 'IMPA',           label: 'IMPA',        unit: '°', lo: 85, hi: 95,   flo: 60,  fhi: 125 },
  { key: 'Inter_Incisif',  label: 'Inter-Inc.',  unit: '°', lo: 118, hi: 144, flo: 80,  fhi: 180 },
  { key: 'Angle_Nasolabial', label: 'Nasolabial', unit: '°', lo: 92, hi: 112, flo: 50, fhi: 160 },
] as const;

// Miroir de MM_KEYWORDS (backend/services/cephalo_measure_registry.py) — source unique
// de vérité pour distinguer les métriques en mm (non fiables sans calibration) des angles.
const MM_KEYWORDS = ['ligne', 'surplomb', 'recouvrement', 'decalage', 'décalage', 'situation', 'profondeur', 'i_na_mm', 'i_nb_mm', 'wits', 'longueur', 'differentiel', 'etage'];
function isMmMetric(name: string): boolean {
  const n = name.toLowerCase();
  return MM_KEYWORDS.some(kw => n.includes(kw));
}

type AngleStatus = 'ok' | 'warning' | 'fatal' | 'missing';

function getAngleStatus(val: number | undefined, card: typeof ANGLE_CARDS[number]): AngleStatus {
  if (val === undefined || val === null || isNaN(val)) return 'missing';
  if (val < card.flo || val > card.fhi) return 'fatal';
  if (val < card.lo || val > card.hi) return 'warning';
  return 'ok';
}

const STATUS_COLORS: Record<AngleStatus, { bg: string; text: string; border: string }> = {
  ok:      { bg: '#f0fdf4', text: '#16a34a', border: '#86efac' },
  warning: { bg: '#fffbeb', text: '#d97706', border: '#fcd34d' },
  fatal:   { bg: '#fef2f2', text: '#dc2626', border: '#fca5a5' },
  missing: { bg: '#f8fafc', text: '#94a3b8', border: '#e2e8f0' },
};

// --- Validation API result ---
interface ValidationResult {
  is_valid: boolean;
  fatals: string[];
  warnings: string[];
}

// --- AngleCard sub-component ---
const AngleCard: React.FC<{
  card: typeof ANGLE_CARDS[number];
  value: number | undefined;
  P: any;
}> = ({ card, value, P }) => {
  const status = getAngleStatus(value, card);
  const colors = STATUS_COLORS[status];
  const fmtVal = value !== undefined && !isNaN(value) ? value.toFixed(1) : '--';

  return (
    <div
      className="rounded-xl p-3 flex flex-col gap-1 border transition-all"
      style={{ background: colors.bg, borderColor: colors.border }}
    >
      <span className="text-[9px] font-black uppercase tracking-widest" style={{ color: colors.text }}>
        {card.label}
      </span>
      <div className="flex items-end gap-1">
        <span className="text-xl font-black" style={{ color: colors.text }}>{fmtVal}</span>
        <span className="text-xs font-bold mb-0.5" style={{ color: colors.text, opacity: 0.6 }}>{card.unit}</span>
      </div>
      <span className="text-[8px]" style={{ color: colors.text, opacity: 0.7 }}>
        norme {card.lo}–{card.hi}{card.unit}
      </span>
    </div>
  );
};

// --- Checklist item ---
const CheckItem: React.FC<{
  label: string;
  status: 'ok' | 'warning' | 'fail' | 'loading';
  detail?: string;
}> = ({ label, status, detail }) => {
  const iconMap = {
    ok:      <CheckCircle2 size={15} className="text-emerald-500 shrink-0" />,
    warning: <AlertTriangle size={15} className="text-amber-500 shrink-0" />,
    fail:    <XCircle size={15} className="text-red-500 shrink-0" />,
    loading: <Loader2 size={15} className="text-slate-400 animate-spin shrink-0" />,
  };
  const textColor = { ok: '#16a34a', warning: '#d97706', fail: '#dc2626', loading: '#94a3b8' }[status];

  return (
    <div className="flex items-start gap-2 py-1.5">
      {iconMap[status]}
      <div>
        <span className="text-xs font-semibold" style={{ color: '#334155' }}>{label}</span>
        {detail && (
          <p className="text-[10px] mt-0.5" style={{ color: textColor }}>{detail}</p>
        )}
      </div>
    </div>
  );
};

// --- Main Component ---
export const Step4Documents: React.FC<Step4DocumentsProps> = ({ P }) => {
  const store = useOrthoStore();
  const {
    photos,
    handlePhotoUpload: onUpload,
    handlePrint: onGeneratePDF,
    handlePreview: onPreviewPDF,
    isPrinting: isGenerating,
    isPreviewLoading,
    etape3Data,
    diag,
    setEtape3Data,
    anglesData,
    patientId,
    patientName,
    analysisId,
    imageSrc,
    isCalibrated,
    local,
  } = store;

  const [showDetails, setShowDetails] = useState(false);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);
  const [isBrouillon, setIsBrouillon] = useState(false);

  // Checklist derived state
  const hasImage = Boolean(imageSrc);
  const hasCalibration = isCalibrated;
  const reqSet = new Set<string>(REQUIRED_LANDMARKS as readonly string[]);
  const landmarkCount = local.landmarks.filter(l => reqSet.has(l.id)).length;
  const landmarkPct = Math.round((landmarkCount / REQUIRED_LANDMARKS.length) * 100);
  const landmarksOk = landmarkPct === 100;
  const diagOk = Boolean(diag.synthese_diagnostique?.trim());

  // Fetch validation on mount if analysisId is present
  const fetchValidation = useCallback(async () => {
    if (!patientId || !analysisId) return;
    setIsValidating(true);
    try {
      const { data } = await api.get(`/patients/${patientId}/cephalo-validation`);
      setValidation(data);
    } catch {
      setValidation(null);
    } finally {
      setIsValidating(false);
    }
  }, [patientId, analysisId]);

  useEffect(() => {
    fetchValidation();
  }, [fetchValidation]);

  // Angles from anglesData — data is nested under metrics.analyse_xxx.Key.valeur
  const getAngleVal = (key: string): number | undefined => {
    const m = anglesData?.metrics;
    if (m) {
      for (const section of [m.analyse_osseuse, m.analyse_dentaire, m.analyse_esthetique]) {
        if (section && section[key] !== undefined) {
          const raw = section[key]?.valeur ?? section[key];
          if (raw === undefined || raw === null) return undefined;
          const n = parseFloat(raw);
          return isNaN(n) ? undefined : n;
        }
      }
    }
    // Fallback: top-level flat key (anciens enregistrements)
    const v = anglesData?.[key];
    if (v === undefined || v === null || v === '') return undefined;
    const n = parseFloat(v);
    return isNaN(n) ? undefined : n;
  };

  const hasFatals = (validation?.fatals?.length ?? 0) > 0;
  const hasWarnings = (validation?.warnings?.length ?? 0) > 0;

  // --- Actions ---
  const handlePrevisualiser = async () => {
    await onPreviewPDF();
  };

  const handleBrouillon = async () => {
    if (!patientId || !analysisId) return;
    setIsBrouillon(true);
    try {
      await store.silentSave();
      const { data } = await api.post(
        `/patients/${patientId}/pdf`,
        {},
        { responseType: 'arraybuffer' }
      );
      const blob = new Blob([data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `brouillon-bilan-${(patientName || 'patient').replace(/\s+/g, '-')}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Brouillon téléchargé.');
    } catch (e: any) {
      const msg = e?.response?.data ? (() => {
        try { return JSON.parse(new TextDecoder().decode(e.response.data)).detail; } catch { return null; }
      })() : null;
      toast.error(msg || 'Erreur lors de la génération du brouillon.');
    } finally {
      setIsBrouillon(false);
    }
  };

  const handleValiderEtArchiver = async () => {
    if (!patientId || !analysisId) return;

    // Re-validate before archiving
    setIsArchiving(true);
    try {
      const { data: vResult } = await api.get<ValidationResult>(`/patients/${patientId}/cephalo-validation`);
      setValidation(vResult);

      if ((vResult.fatals?.length ?? 0) > 0) {
        toast.error(`Impossible d'archiver : ${vResult.fatals[0]}`);
        setIsArchiving(false);
        return;
      }
      if ((vResult.warnings?.length ?? 0) > 0) {
        toast(`Attention : ${vResult.warnings.length} avertissement(s). Archivage en cours...`, { icon: '⚠️' });
      }

      await onGeneratePDF();
    } catch (e: any) {
      const msg = e?.response?.data?.detail;
      toast.error(msg || 'Erreur lors de l\'archivage.');
    } finally {
      setIsArchiving(false);
    }
  };

  const canArchive = !hasFatals && hasImage && landmarksOk;

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

      {/* Fatal banner */}
      {hasFatals && (
        <div className="flex items-start gap-3 px-4 py-3 rounded-xl border"
             style={{ background: '#fef2f2', borderColor: '#fca5a5' }}>
          <XCircle size={18} className="text-red-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-black text-red-700 uppercase tracking-wider">Erreurs cliniques bloquantes</p>
            <ul className="mt-1 space-y-0.5">
              {validation!.fatals.map((f, i) => (
                <li key={i} className="text-xs text-red-600">{f}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* ── COLONNE GAUCHE : Synthèse + Photos ── */}
        <div className="lg:col-span-5 space-y-6">

          {/* Section 1 : Synthèse céphalométrique */}
          <div className="rounded-2xl p-5 border" style={{ background: P.bgPanel, borderColor: P.border }}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Activity size={16} style={{ color: P.accent }} />
                <h3 className="text-xs font-black uppercase tracking-widest" style={{ color: P.text }}>
                  Synthèse Céphalométrique
                </h3>
              </div>
              <button
                onClick={() => setShowDetails(v => !v)}
                className="flex items-center gap-1 text-[9px] font-black uppercase tracking-wider px-2 py-1 rounded-lg transition-all hover:opacity-70"
                style={{ color: P.textMuted, background: `${P.border}60` }}
              >
                {showDetails ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                {showDetails ? 'Masquer détails' : 'Voir détails'}
              </button>
            </div>

            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
              {ANGLE_CARDS.map(card => (
                <AngleCard key={card.key} card={card} value={getAngleVal(card.key)} P={P} />
              ))}
            </div>

            {/* Collapsible technical table */}
            {showDetails && (
              <div className="mt-4 pt-4 border-t" style={{ borderColor: P.border }}>
                <p className="text-[9px] font-black uppercase tracking-widest mb-3" style={{ color: P.textMuted }}>
                  Tous les angles calculés
                </p>
                {anglesData?.calibration_status === 'unverified' && (
                  <p className="text-[9px] font-black uppercase tracking-wider mb-2 px-2 py-1 rounded-lg" style={{ color: '#d97706', background: '#fffbeb' }}>
                    ⚠ Calibration non vérifiée — les mesures en mm ci-dessous ne sont pas fiables
                  </p>
                )}
                <div className="space-y-1">
                  {(() => {
                    const m = anglesData?.metrics;
                    if (!m) return null;
                    const uncalibrated = anglesData?.calibration_status === 'unverified';
                    const entries: [string, number | null][] = [];
                    for (const section of [m.analyse_osseuse, m.analyse_dentaire, m.analyse_esthetique]) {
                      if (!section) continue;
                      for (const [k, v] of Object.entries(section as Record<string, any>)) {
                        const val = v?.valeur ?? null;
                        entries.push([k, typeof val === 'number' ? val : null]);
                      }
                    }
                    return entries.map(([k, val]) => {
                      const flagged = uncalibrated && val !== null && isMmMetric(k);
                      return (
                        <div key={k} className="flex justify-between items-center py-1 border-b" style={{ borderColor: `${P.border}50` }}>
                          <span className="text-[10px] font-semibold" style={{ color: P.textMuted }}>
                            {k}{flagged && ' ⚠'}
                          </span>
                          <span className="text-[10px] font-black" style={{ color: flagged ? '#d97706' : P.text }}>
                            {val !== null ? val.toFixed(1) : '--'}
                          </span>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>
            )}
          </div>

          {/* Section 3 : Dossier photographique */}
          <div className="rounded-2xl p-5 border" style={{ background: P.bgPanel, borderColor: P.border }}>
            <h3 className="text-xs font-black uppercase tracking-widest mb-4" style={{ color: P.text }}>
              Dossier Photographique
            </h3>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {photos.map((photo) => (
                <div
                  key={photo.id}
                  className="group relative aspect-square rounded-xl overflow-hidden border-2 border-dashed transition-all"
                  style={{
                    background: P.bgCard,
                    borderColor: photo.preview ? '#86efac' : P.border,
                    borderStyle: photo.preview ? 'solid' : 'dashed',
                  }}
                >
                  {photo.preview ? (
                    <>
                      <img src={photo.preview} alt={photo.label} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <label className="cursor-pointer p-1.5 bg-white/20 backdrop-blur-md rounded-full text-white">
                          <Camera size={16} />
                          <input type="file" className="hidden" accept="image/*"
                            onChange={(e) => e.target.files?.[0] && onUpload(photo.id, e.target.files[0])} />
                        </label>
                      </div>
                      <div className="absolute top-1 right-1 p-0.5 bg-emerald-500 rounded-full text-white shadow">
                        <CheckCircle2 size={10} />
                      </div>
                    </>
                  ) : (
                    <label className="flex flex-col items-center justify-center w-full h-full cursor-pointer p-2 text-center gap-1">
                      <Camera size={18} style={{ color: P.textDim }} />
                      <span className="text-[8px] font-black uppercase tracking-wider leading-tight" style={{ color: P.textMuted }}>
                        {photo.label}
                      </span>
                      <input type="file" className="hidden" accept="image/*"
                        onChange={(e) => e.target.files?.[0] && onUpload(photo.id, e.target.files[0])} />
                    </label>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── COLONNE DROITE : Validation + Plan ── */}
        <div className="lg:col-span-7 space-y-6">

          {/* Section 2 : Checklist de validation */}
          <div className="rounded-2xl p-5 border" style={{ background: P.bgPanel, borderColor: P.border }}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Shield size={16} style={{ color: P.accent }} />
                <h3 className="text-xs font-black uppercase tracking-widest" style={{ color: P.text }}>
                  Checklist de Validation
                </h3>
              </div>
              <button
                onClick={fetchValidation}
                disabled={isValidating}
                className="flex items-center gap-1 text-[9px] font-black uppercase tracking-wider px-2 py-1 rounded-lg transition-all hover:opacity-70 disabled:opacity-40"
                style={{ color: P.accent, background: `${P.accent}15` }}
              >
                {isValidating ? <Loader2 size={10} className="animate-spin" /> : null}
                Actualiser
              </button>
            </div>

            <div className="space-y-0.5 divide-y" style={{ borderColor: `${P.border}60` }}>
              <CheckItem
                label="Image céphalométrique chargée"
                status={hasImage ? 'ok' : 'fail'}
                detail={hasImage ? undefined : 'Aucune image uploadée en Étape 1'}
              />
              <CheckItem
                label="Calibration effectuée"
                status={hasCalibration ? 'ok' : 'warning'}
                detail={hasCalibration ? undefined : 'Calibration recommandée pour les mesures mm'}
              />
              <CheckItem
                label={`Landmarks complets (${landmarkCount}/${REQUIRED_LANDMARKS.length})`}
                status={landmarksOk ? 'ok' : landmarkCount > 0 ? 'warning' : 'fail'}
                detail={landmarksOk ? undefined : `${landmarkPct}% des points requis placés`}
              />
              <CheckItem
                label="Cohérence clinique des angles"
                status={
                  isValidating ? 'loading'
                  : !validation ? 'warning'
                  : hasFatals ? 'fail'
                  : hasWarnings ? 'warning'
                  : 'ok'
                }
                detail={
                  isValidating ? 'Vérification en cours...'
                  : !validation ? 'Non vérifié'
                  : hasFatals ? `${validation.fatals.length} erreur(s) fatale(s)`
                  : hasWarnings ? `${validation.warnings.length} avertissement(s)`
                  : 'Tous les angles sont cohérents'
                }
              />
              <CheckItem
                label="Diagnostic clinique rédigé"
                status={diagOk ? 'ok' : 'warning'}
                detail={diagOk ? undefined : 'Synthèse diagnostique vide (Étape 3)'}
              />
            </div>

            {hasWarnings && !hasFatals && validation && (
              <div className="mt-3 pt-3 border-t" style={{ borderColor: P.border }}>
                <p className="text-[9px] font-black uppercase tracking-wider mb-1.5" style={{ color: '#d97706' }}>
                  Avertissements
                </p>
                {validation.warnings.map((w, i) => (
                  <p key={i} className="text-[10px] text-amber-600 flex items-center gap-1">
                    <AlertTriangle size={10} className="shrink-0" />
                    {w}
                  </p>
                ))}
              </div>
            )}
          </div>

          {/* Section 4 : Plan de traitement */}
          <div className="rounded-2xl p-5 border" style={{ background: P.bgPanel, borderColor: P.border }}>
            <div className="flex items-center gap-2 mb-5">
              <FileText size={16} style={{ color: P.accent }} />
              <h3 className="text-xs font-black uppercase tracking-widest" style={{ color: P.text }}>
                Plan de Traitement
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 rounded-xl border" style={{ background: P.bgInput, borderColor: P.border }}>
                <label className="text-[9px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>
                  Technique Orthodontique
                </label>
                <select
                  value={etape3Data.preference_technique || 'DAMON'}
                  onChange={e => setEtape3Data(prev => ({ ...prev, preference_technique: e.target.value as any }))}
                  className="w-full bg-transparent font-bold text-sm outline-none"
                  style={{ color: P.text }}
                >
                  <option value="DAMON">Damon (Autoligaturant)</option>
                  <option value="CLASSIC">Multi-attaches Classique</option>
                  <option value="ALIGNEURS">Aligneurs (Invisalign)</option>
                </select>
              </div>

              <div className="p-3 rounded-xl border" style={{ background: P.bgInput, borderColor: P.border }}>
                <label className="text-[9px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>
                  Stade CVM
                </label>
                <select
                  value={etape3Data.cvm || ''}
                  onChange={e => setEtape3Data(prev => ({ ...prev, cvm: e.target.value as any }))}
                  className="w-full bg-transparent font-bold text-sm outline-none"
                  style={{ color: P.text }}
                >
                  <option value="">--</option>
                  {['CS1','CS2','CS3','CS4','CS5','CS6'].map(v => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
              </div>

              <div className="p-3 rounded-xl border col-span-2" style={{ background: P.bgInput, borderColor: P.border }}>
                <label className="text-[9px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>
                  Stratégie Thérapeutique (résumé pour le PDF)
                </label>
                <textarea
                  value={diag.strategie_therapeutique}
                  onChange={e => store.setDiag(prev => ({ ...prev, strategie_therapeutique: e.target.value }))}
                  rows={4}
                  className="w-full bg-transparent text-sm outline-none resize-none font-medium leading-relaxed"
                  style={{ color: P.text }}
                  placeholder="Décrivez le plan de traitement prévu..."
                />
              </div>

              {/* Phase d'orthopédie (visible si denture non permanente) */}
              {etape3Data.denture_type !== 'PERMANENTE' && (
                <div className="p-3 rounded-xl border col-span-2" style={{ background: P.bgInput, borderColor: P.border }}>
                  <label className="text-[9px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>
                    Appareil Orthopédique (phase 1)
                  </label>
                  <select
                    value={etape3Data.profil || ''}
                    onChange={e => setEtape3Data(prev => ({ ...prev, profil: e.target.value as any }))}
                    className="w-full bg-transparent font-bold text-sm outline-none"
                    style={{ color: P.text }}
                  >
                    <option value="">-- Sélectionner --</option>
                    <option value="d-gainer">D-Gainer</option>
                    <option value="quadhelix">QuadHelix</option>
                    <option value="disjoncteur">Disjoncteur</option>
                    <option value="activateur">Activateur</option>
                    <option value="fronde">Fronde</option>
                    <option value="perle-tuca">Perle de Tuca</option>
                  </select>
                </div>
              )}
            </div>
          </div>

          {/* ── Boutons d'action ── */}
          <div className="rounded-2xl p-5 border" style={{ background: P.bgPanel, borderColor: P.border }}>
            <p className="text-[9px] font-black text-center uppercase tracking-widest mb-4" style={{ color: P.textMuted }}>
              Actions disponibles
            </p>
            <div className="grid grid-cols-3 gap-3">
              {/* Prévisualiser */}
              <button
                onClick={handlePrevisualiser}
                disabled={isPreviewLoading || !analysisId}
                className="flex flex-col items-center justify-center gap-1.5 px-3 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 border shadow-sm hover:shadow-md"
                style={{ background: P.bgCard, borderColor: P.border, color: P.textMuted }}
              >
                {isPreviewLoading
                  ? <Loader2 size={20} className="animate-spin" />
                  : <Eye size={20} />}
                Prévisualiser
              </button>

              {/* Générer brouillon */}
              <button
                onClick={handleBrouillon}
                disabled={isBrouillon || !analysisId}
                className="flex flex-col items-center justify-center gap-1.5 px-3 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 border shadow-sm hover:shadow-md"
                style={{ background: P.bgCard, borderColor: P.border, color: P.text }}
              >
                {isBrouillon
                  ? <Loader2 size={20} className="animate-spin" />
                  : <FileText size={20} />}
                Brouillon PDF
              </button>

              {/* Valider et archiver */}
              <button
                onClick={handleValiderEtArchiver}
                disabled={isArchiving || isGenerating || !analysisId || !canArchive}
                className="flex flex-col items-center justify-center gap-1.5 px-3 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest text-white transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 shadow-xl"
                style={{
                  background: canArchive
                    ? `linear-gradient(135deg, ${P.accent}, #7c3aed)`
                    : '#94a3b8',
                  boxShadow: canArchive ? `0 4px 16px ${P.accent}40` : 'none',
                }}
              >
                {isArchiving || isGenerating
                  ? <Loader2 size={20} className="animate-spin" />
                  : <Archive size={20} />}
                Valider & Archiver
              </button>
            </div>

            {!canArchive && (
              <p className="text-center text-[9px] mt-3" style={{ color: P.textMuted }}>
                {hasFatals ? 'Corrigez les erreurs cliniques avant d\'archiver.'
                  : !hasImage ? 'Uploadez une image céphalométrique.'
                  : !landmarksOk ? `Placez tous les landmarks (${landmarkPct}% complétés).`
                  : ''}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

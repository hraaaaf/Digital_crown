import React, { useCallback, useEffect, useState } from 'react';
import {
  Activity, AlertTriangle, Archive, Camera, CheckCircle2, ChevronDown,
  ChevronUp, Eye, FileText, Loader2, Shield, XCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../../../services/api';
import { REQUIRED_LANDMARKS } from '../cephaloShared';
import { useOrthoStore } from '../stores/useOrthoStore';

interface Step4DocumentsProps {
  P: any;
}

const ANGLE_CARDS = [
  { key: 'SNA', label: 'SNA', unit: '°' },
  { key: 'SNB', label: 'SNB', unit: '°' },
  { key: 'ANB', label: 'ANB', unit: '°' },
  { key: 'I_Francfort', label: '1 / Francfort', unit: '°' },
  { key: 'IMPA', label: 'IMPA', unit: '°' },
  { key: 'Inter_Incisif', label: 'Inter-Inc.', unit: '°' },
] as const;

const MM_KEYWORDS = ['ligne', 'surplomb', 'recouvrement', 'decalage', 'décalage', 'situation', 'profondeur', 'i_na_mm', 'i_nb_mm', 'wits', 'longueur', 'differentiel', 'etage'];
function isMmMetric(name: string): boolean {
  const n = name.toLowerCase();
  return MM_KEYWORDS.some(kw => n.includes(kw));
}

interface ValidationResult {
  is_valid: boolean;
  fatals: string[];
  warnings: string[];
}

const AngleCard: React.FC<{
  card: typeof ANGLE_CARDS[number];
  value: number | undefined;
  P: any;
}> = ({ card, value, P }) => {
  const fmtVal = value !== undefined && !isNaN(value) ? value.toFixed(1) : '--';
  return (
    <div className="rounded-xl p-3 flex flex-col gap-1 border" style={{ background: P.bgCard, borderColor: P.border }}>
      <span className="text-[9px] font-black uppercase tracking-widest" style={{ color: P.textMuted }}>{card.label}</span>
      <div className="flex items-end gap-1">
        <span className="text-xl font-black" style={{ color: P.text }}>{fmtVal}</span>
        <span className="text-xs font-bold mb-0.5" style={{ color: P.textMuted }}>{card.unit}</span>
      </div>
      <span className="text-[8px]" style={{ color: P.textDim }}>Valeur brute · aucune norme locale</span>
    </div>
  );
};

const CheckItem: React.FC<{
  label: string;
  status: 'ok' | 'warning' | 'fail' | 'loading';
  detail?: string;
}> = ({ label, status, detail }) => {
  const iconMap = {
    ok: <CheckCircle2 size={15} className="text-emerald-500 shrink-0" />,
    warning: <AlertTriangle size={15} className="text-amber-500 shrink-0" />,
    fail: <XCircle size={15} className="text-red-500 shrink-0" />,
    loading: <Loader2 size={15} className="text-slate-400 animate-spin shrink-0" />,
  };
  const textColor = { ok: '#16a34a', warning: '#d97706', fail: '#dc2626', loading: '#94a3b8' }[status];
  return (
    <div className="flex items-start gap-2 py-1.5">
      {iconMap[status]}
      <div>
        <span className="text-xs font-semibold" style={{ color: '#334155' }}>{label}</span>
        {detail && <p className="text-[10px] mt-0.5" style={{ color: textColor }}>{detail}</p>}
      </div>
    </div>
  );
};

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

  const hasImage = Boolean(imageSrc);
  const hasCalibration = isCalibrated;
  const reqSet = new Set<string>(REQUIRED_LANDMARKS as readonly string[]);
  const landmarkCount = local.landmarks.filter(l => reqSet.has(l.id)).length;
  const landmarkPct = Math.round((landmarkCount / REQUIRED_LANDMARKS.length) * 100);
  const landmarksOk = landmarkPct === 100;
  const diagOk = Boolean(diag.synthese_diagnostique?.trim());

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

  useEffect(() => { fetchValidation(); }, [fetchValidation]);

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
    const v = anglesData?.[key];
    if (v === undefined || v === null || v === '') return undefined;
    const n = parseFloat(v);
    return isNaN(n) ? undefined : n;
  };

  const hasFatals = (validation?.fatals?.length ?? 0) > 0;
  const hasWarnings = (validation?.warnings?.length ?? 0) > 0;

  const handleBrouillon = async () => {
    if (!patientId || !analysisId) return;
    setIsBrouillon(true);
    try {
      await store.silentSave();
      const { data } = await api.post(`/patients/${patientId}/pdf`, {}, { responseType: 'arraybuffer' });
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

  const handleArchiveBilan = async () => {
    if (!patientId || !analysisId) return;
    setIsArchiving(true);
    try {
      const { data: vResult } = await api.get<ValidationResult>(`/patients/${patientId}/cephalo-validation`);
      setValidation(vResult);
      if ((vResult.fatals?.length ?? 0) > 0) {
        toast.error(`Impossible d'archiver : ${vResult.fatals[0]}`);
        return;
      }
      if ((vResult.warnings?.length ?? 0) > 0) {
        toast(`Attention : ${vResult.warnings.length} avertissement(s). Archivage en cours...`, { icon: '⚠️' });
      }
      await onGeneratePDF();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Erreur lors de l\'archivage.');
    } finally {
      setIsArchiving(false);
    }
  };

  const canArchive = !hasFatals && hasImage && landmarksOk;

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {hasFatals && (
        <div className="flex items-start gap-3 px-4 py-3 rounded-xl border" style={{ background: '#fef2f2', borderColor: '#fca5a5' }}>
          <XCircle size={18} className="text-red-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-black text-red-700 uppercase tracking-wider">Erreurs bloquantes de validation de cohérence</p>
            <ul className="mt-1 space-y-0.5">{validation!.fatals.map((f, i) => <li key={i} className="text-xs text-red-600">{f}</li>)}</ul>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 space-y-6">
          <div className="rounded-2xl p-5 border" style={{ background: P.bgPanel, borderColor: P.border }}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Activity size={16} style={{ color: P.accent }} />
                <h3 className="text-xs font-black uppercase tracking-widest" style={{ color: P.text }}>Mesures Céphalométriques</h3>
              </div>
              <button onClick={() => setShowDetails(v => !v)} className="flex items-center gap-1 text-[9px] font-black uppercase tracking-wider px-2 py-1 rounded-lg" style={{ color: P.textMuted, background: `${P.border}60` }}>
                {showDetails ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                {showDetails ? 'Masquer détails' : 'Voir détails'}
              </button>
            </div>

            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
              {ANGLE_CARDS.map(card => <AngleCard key={card.key} card={card} value={getAngleVal(card.key)} P={P} />)}
            </div>
            <p className="mt-3 text-[10px] leading-relaxed" style={{ color: P.textMuted }}>
              Aucune plage normale ni couleur diagnostique n'est calculée dans le frontend. L'interprétation normative autoritative appartient au registre scientifique backend.
            </p>

            {showDetails && (
              <div className="mt-4 pt-4 border-t" style={{ borderColor: P.border }}>
                {anglesData?.calibration_status === 'unverified' && (
                  <p className="text-[9px] font-black uppercase tracking-wider mb-2 px-2 py-1 rounded-lg" style={{ color: '#d97706', background: '#fffbeb' }}>
                    ⚠ Calibration non vérifiée — mesures en mm non fiables
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
                          <span className="text-[10px] font-semibold" style={{ color: P.textMuted }}>{k}{flagged && ' ⚠'}</span>
                          <span className="text-[10px] font-black" style={{ color: flagged ? '#d97706' : P.text }}>{val !== null ? val.toFixed(1) : '--'}</span>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>
            )}
          </div>

          <div className="rounded-2xl p-5 border" style={{ background: P.bgPanel, borderColor: P.border }}>
            <h3 className="text-xs font-black uppercase tracking-widest mb-4" style={{ color: P.text }}>Dossier Photographique</h3>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {photos.map(photo => (
                <div key={photo.id} className="group relative aspect-square rounded-xl overflow-hidden border-2 border-dashed" style={{ background: P.bgCard, borderColor: photo.preview ? '#86efac' : P.border, borderStyle: photo.preview ? 'solid' : 'dashed' }}>
                  {photo.preview ? (
                    <>
                      <img src={photo.preview} alt={photo.label} className="w-full h-full object-cover" />
                      <label className="absolute inset-0 cursor-pointer flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/30 text-white">
                        <Camera size={16} />
                        <input type="file" className="hidden" accept="image/*" onChange={e => e.target.files?.[0] && onUpload(photo.id, e.target.files[0])} />
                      </label>
                      <CheckCircle2 size={12} className="absolute top-1 right-1 text-emerald-500" />
                    </>
                  ) : (
                    <label className="flex flex-col items-center justify-center w-full h-full cursor-pointer p-2 text-center gap-1">
                      <Camera size={18} style={{ color: P.textDim }} />
                      <span className="text-[8px] font-black uppercase tracking-wider" style={{ color: P.textMuted }}>{photo.label}</span>
                      <input type="file" className="hidden" accept="image/*" onChange={e => e.target.files?.[0] && onUpload(photo.id, e.target.files[0])} />
                    </label>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-7 space-y-6">
          <div className="rounded-2xl p-5 border" style={{ background: P.bgPanel, borderColor: P.border }}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2"><Shield size={16} style={{ color: P.accent }} /><h3 className="text-xs font-black uppercase tracking-widest" style={{ color: P.text }}>Checklist de cohérence documentaire</h3></div>
              <button onClick={fetchValidation} disabled={isValidating} className="text-[9px] font-black uppercase tracking-wider px-2 py-1 rounded-lg disabled:opacity-40" style={{ color: P.accent, background: `${P.accent}15` }}>{isValidating ? 'Vérification…' : 'Actualiser'}</button>
            </div>
            <div className="space-y-0.5 divide-y">
              <CheckItem label="Image céphalométrique chargée" status={hasImage ? 'ok' : 'fail'} detail={hasImage ? undefined : 'Aucune image uploadée'} />
              <CheckItem label="Calibration effectuée" status={hasCalibration ? 'ok' : 'warning'} detail={hasCalibration ? undefined : 'Mesures mm non fiables sans calibration'} />
              <CheckItem label={`Landmarks complets (${landmarkCount}/${REQUIRED_LANDMARKS.length})`} status={landmarksOk ? 'ok' : landmarkCount > 0 ? 'warning' : 'fail'} detail={landmarksOk ? undefined : `${landmarkPct}% des points requis placés`} />
              <CheckItem label="Cohérence des mesures" status={isValidating ? 'loading' : !validation ? 'warning' : hasFatals ? 'fail' : hasWarnings ? 'warning' : 'ok'} detail={!validation ? 'Non vérifiée' : hasFatals ? `${validation.fatals.length} erreur(s)` : hasWarnings ? `${validation.warnings.length} avertissement(s)` : 'Sans erreur bloquante'} />
              <CheckItem label="Note diagnostique libre legacy présente" status={diagOk ? 'ok' : 'warning'} detail={diagOk ? 'Contenu non autoritaire, provenance non certifiée' : 'Note libre vide'} />
            </div>
          </div>

          <div className="rounded-2xl p-5 border" style={{ background: P.bgPanel, borderColor: P.border }}>
            <div className="flex items-center gap-2 mb-2"><FileText size={16} style={{ color: P.accent }} /><h3 className="text-xs font-black uppercase tracking-widest" style={{ color: P.text }}>Notes thérapeutiques legacy — provenance non certifiée</h3></div>
            <p className="mb-5 text-[10px] leading-relaxed" style={{ color: P.textMuted }}>
              Ces champs peuvent contenir une saisie manuelle ou un contenu historique dont l'auteur n'est pas attesté par le contrat legacy. Ils restent hors R13/R14 et ne valent jamais validation clinique finale.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-3 rounded-xl border" style={{ background: P.bgInput, borderColor: P.border }}>
                <label className="text-[9px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>Préférence technique — saisie manuelle hors R13</label>
                <select value={etape3Data.preference_technique || ''} onChange={e => setEtape3Data(prev => ({ ...prev, preference_technique: e.target.value as any }))} className="w-full bg-transparent font-bold text-sm outline-none" style={{ color: P.text }}>
                  <option value="">-- Non renseignée --</option>
                  <option value="DAMON">Damon (Autoligaturant)</option>
                  <option value="CLASSIC">Multi-attaches Classique</option>
                  <option value="ALIGNEURS">Aligneurs</option>
                </select>
              </div>
              <div className="p-3 rounded-xl border" style={{ background: P.bgInput, borderColor: P.border }}>
                <label className="text-[9px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>Stade CVM — saisie manuelle</label>
                <select value={etape3Data.cvm || ''} onChange={e => setEtape3Data(prev => ({ ...prev, cvm: e.target.value as any }))} className="w-full bg-transparent font-bold text-sm outline-none" style={{ color: P.text }}>
                  <option value="">-- Non renseigné --</option>
                  {['CS1','CS2','CS3','CS4','CS5','CS6'].map(v => <option key={v} value={v}>{v}</option>)}
                </select>
              </div>
              <div className="p-3 rounded-xl border sm:col-span-2" style={{ background: P.bgInput, borderColor: P.border }}>
                <label className="text-[9px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>Note thérapeutique libre legacy — hors preuve R14</label>
                <textarea value={diag.strategie_therapeutique} onChange={e => store.setDiag(prev => ({ ...prev, strategie_therapeutique: e.target.value }))} rows={5} className="w-full bg-transparent text-sm outline-none resize-none font-medium leading-relaxed" style={{ color: P.text }} placeholder="Saisie libre ou contenu historique — provenance non certifiée. Aucune stratégie R14 n'est générée ou validée ici." />
              </div>
            </div>
          </div>

          <div className="rounded-2xl p-5 border" style={{ background: P.bgPanel, borderColor: P.border }}>
            <p className="text-[9px] font-black text-center uppercase tracking-widest mb-1" style={{ color: P.textMuted }}>Actions documentaires</p>
            <p className="mb-4 text-center text-[9px]" style={{ color: P.textDim }}>Prévisualiser ou archiver un PDF ne valide jamais R14.</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <button onClick={onPreviewPDF} disabled={isPreviewLoading || !analysisId} className="flex flex-col items-center justify-center gap-1.5 px-3 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest disabled:opacity-40 border" style={{ background: P.bgCard, borderColor: P.border, color: P.textMuted }}>{isPreviewLoading ? <Loader2 size={20} className="animate-spin" /> : <Eye size={20} />}Prévisualiser</button>
              <button onClick={handleBrouillon} disabled={isBrouillon || !analysisId} className="flex flex-col items-center justify-center gap-1.5 px-3 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest disabled:opacity-40 border" style={{ background: P.bgCard, borderColor: P.border, color: P.text }}>{isBrouillon ? <Loader2 size={20} className="animate-spin" /> : <FileText size={20} />}Brouillon PDF</button>
              <button onClick={handleArchiveBilan} disabled={isArchiving || isGenerating || !analysisId || !canArchive} className="flex flex-col items-center justify-center gap-1.5 px-3 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest text-white disabled:opacity-40" style={{ background: canArchive ? `linear-gradient(135deg, ${P.accent}, #7c3aed)` : '#94a3b8' }}>{isArchiving || isGenerating ? <Loader2 size={20} className="animate-spin" /> : <Archive size={20} />}Archiver le bilan</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
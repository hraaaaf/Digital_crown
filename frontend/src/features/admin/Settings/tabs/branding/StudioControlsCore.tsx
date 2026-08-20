import React, { useState, useEffect } from 'react';
import { cn } from '../../../../../utils/cn';
import { BRAND_IDENTITIES, PREMIUM_FONTS } from '../../../constants';
import { DENSITY_DEFAULTS } from './presets';
import type { Density } from './types';
import { Upload, Check, QrCode, UserCircle, Link, Instagram, MessageCircle, MapPin, Shield, CreditCard, ChevronDown, ChevronUp, ChevronLeft, ChevronRight, Trash2, FileText, RotateCcw } from 'lucide-react';
import { useSettingsStore } from '../../hooks/useSettingsStore';
import { API_BASE } from '../../../../../services/api';
import { useAuthenticatedImage } from '../../../../../hooks/useAuthenticatedImage';

interface StudioControlsProps {
  profile: any;
  updateProfile: (data: any) => void;
}

// Manette de positionnement (D-pad) : nudge x/y en cm, appliqué en superposition
// de la position calculée par le template (jamais en remplacement).
const POSITION_PAD_RANGE = 3;
const POSITION_PAD_STEP = 0.1;

const PositionPad = ({ x, y, onChange }: { x: number; y: number; onChange: (x: number, y: number) => void }) => {
  const clamp = (v: number) => Math.max(-POSITION_PAD_RANGE, Math.min(POSITION_PAD_RANGE, v));
  // Axe Y ReportLab : positif = vers le haut de la page (cohérent avec la flèche ▲).
  const nudge = (dx: number, dy: number) => onChange(clamp(x + dx), clamp(y + dy));
  const padBtn = "flex items-center justify-center w-8 h-8 rounded-lg border border-[var(--border-color)] text-[var(--text-muted)] hover:text-[var(--primary)] hover:border-[var(--primary)] active:scale-90 transition-all";
  return (
    <div className="flex items-center gap-4">
      <div className="grid grid-cols-3 grid-rows-3 gap-1 w-[108px]">
        <div />
        <button type="button" onClick={() => nudge(0, POSITION_PAD_STEP)} className={padBtn} aria-label="Monter"><ChevronUp size={16} /></button>
        <div />
        <button type="button" onClick={() => nudge(-POSITION_PAD_STEP, 0)} className={padBtn} aria-label="Déplacer à gauche"><ChevronLeft size={16} /></button>
        <button type="button" onClick={() => onChange(0, 0)} className={cn(padBtn, "text-[var(--text-muted)]")} aria-label="Réinitialiser la position"><RotateCcw size={13} /></button>
        <button type="button" onClick={() => nudge(POSITION_PAD_STEP, 0)} className={padBtn} aria-label="Déplacer à droite"><ChevronRight size={16} /></button>
        <div />
        <button type="button" onClick={() => nudge(0, -POSITION_PAD_STEP)} className={padBtn} aria-label="Descendre"><ChevronDown size={16} /></button>
        <div />
      </div>
      <div className="text-[11px] text-[var(--text-muted)] font-mono leading-relaxed">
        X : {x.toFixed(1)}cm<br />
        Y : {y.toFixed(1)}cm
      </div>
    </div>
  );
};

export const StudioControls: React.FC<StudioControlsProps> = ({ profile, updateProfile }) => {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [isUploadingLocal, setIsUploadingLocal] = useState(false);
  const [stripBody, setStripBody] = useState(false);
  const [headerPct, setHeaderPct] = useState(25);
  const [footerPct, setFooterPct] = useState(18);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [pendingPreviewUrl, setPendingPreviewUrl] = useState<string | null>(null);

  const { uploadLetterhead, deleteLetterhead } = useSettingsStore();
  const customDesignActive = Boolean(profile.use_letterhead && profile.letterhead_path);

  const getLetterheadUrl = (path: string | null | undefined) => {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    const cleanPath = path.replace(/^\/+/, '');
    if (cleanPath.startsWith('static/uploads/')) return `${API_BASE}/${cleanPath}`;
    return `${API_BASE}/static/uploads/${cleanPath}`;
  };
  const letterheadSrc = useAuthenticatedImage(getLetterheadUrl(profile.letterhead_path));

  useEffect(() => {
    const saved = localStorage.getItem('branding_advanced_open');
    if (saved === '1') setAdvancedOpen(true);
  }, []);

  const toggleAdvanced = () => {
    const next = !advancedOpen;
    setAdvancedOpen(next);
    localStorage.setItem('branding_advanced_open', next ? '1' : '0');
  };

  const handleDensityClick = (d: Density) => {
    updateProfile(DENSITY_DEFAULTS[d]);
  };

  const currentDensity: Density = 
    (profile.margin_top === DENSITY_DEFAULTS.compact.margin_top) ? 'compact' :
    (profile.margin_top === DENSITY_DEFAULTS.etendu.margin_top) ? 'etendu' : 'confort';

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Nettoyage du corps demandé sur une image : on affiche un aperçu local
    // avec la zone qui sera effacée avant d'envoyer quoi que ce soit, pour
    // éviter d'uploader un fichier mal découpé (le contenu original blanchi
    // n'est pas récupérable ensuite sans ré-uploader le fichier source).
    if (stripBody && file.type.startsWith('image/')) {
      if (pendingPreviewUrl) URL.revokeObjectURL(pendingPreviewUrl);
      setPendingFile(file);
      setPendingPreviewUrl(URL.createObjectURL(file));
      e.target.value = '';
      return;
    }

    setIsUploadingLocal(true);
    try {
      await uploadLetterhead(file, { stripBody, headerPct, footerPct });
      e.target.value = '';
    } finally {
      setIsUploadingLocal(false);
    }
  };

  const cancelPendingUpload = () => {
    if (pendingPreviewUrl) URL.revokeObjectURL(pendingPreviewUrl);
    setPendingFile(null);
    setPendingPreviewUrl(null);
  };

  const confirmPendingUpload = async () => {
    if (!pendingFile) return;
    setIsUploadingLocal(true);
    try {
      await uploadLetterhead(pendingFile, { stripBody, headerPct, footerPct });
      cancelPendingUpload();
    } finally {
      setIsUploadingLocal(false);
    }
  };

  useEffect(() => {
    return () => { if (pendingPreviewUrl) URL.revokeObjectURL(pendingPreviewUrl); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const QR_TYPES = [
    { id: 'VCARD', label: 'Contact', icon: <UserCircle size={14}/> },
    { id: 'WEBSITE', label: 'Site Web', icon: <Link size={14}/> },
    { id: 'INSTAGRAM', label: 'Instagram', icon: <Instagram size={14}/> },
    { id: 'WHATSAPP', label: 'WhatsApp', icon: <MessageCircle size={14}/> },
    { id: 'LOCATION', label: 'Maps', icon: <MapPin size={14}/> },
    { id: 'VALIDATION', label: 'Signature', icon: <Shield size={14}/> },
    { id: 'PAYMENT', label: 'Paiement', icon: <CreditCard size={14}/> },
  ];
  const designLockedClass = customDesignActive ? "opacity-50 pointer-events-none" : "";

  return (
    <div className="flex flex-col gap-5">
      
      {/* 1. PALETTE */}
      <div className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-6 transition-shadow hover:shadow-[0_8px_24px_-16px_rgba(11,15,23,0.18)] hover:-translate-y-[2px]">
        <h3 className="font-bold text-[11px] text-[var(--text-muted)] tracking-[0.12em] uppercase mb-2">
          Palette
        </h3>
        <p className="text-[10px] text-slate-400 mb-4">Ces couleurs s'appliquent à l'application et aux documents générés.</p>
        {customDesignActive && (
          <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-[12px] text-amber-800">
            Les couleurs du document suivent actuellement le design uploadé.
          </div>
        )}
        <div className={cn("grid grid-cols-2 gap-3", designLockedClass)}>
          {BRAND_IDENTITIES.map(palette => {
            const isSelected = profile.primary_color === palette.primary;
            return (
              <button
                key={palette.id}
                onClick={() => updateProfile({ primary_color: palette.primary, secondary_color: palette.secondary, accent_color: palette.accent })}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-xl border transition-all text-left group",
                  isSelected ? "border-[var(--text-main)] bg-[var(--bg-medical-pearl)]" : "border-[var(--border-color)] hover:border-[var(--text-muted)]"
                )}
              >
                <div className="flex w-[32px] h-[32px] rounded-md overflow-hidden border border-[var(--border-color)] flex-shrink-0">
                  <div className="flex-1" style={{ backgroundColor: palette.primary }} />
                  <div className="flex-1" style={{ backgroundColor: palette.secondary }} />
                  <div className="flex-1" style={{ backgroundColor: palette.accent }} />
                </div>
                <span className={cn("text-[13px] font-medium leading-tight", isSelected ? "text-[var(--text-main)]" : "text-[var(--text-muted)] group-hover:text-[var(--text-main)]")}>
                  {palette.name}
                </span>
                {isSelected && <Check size={14} className="ml-auto text-[var(--text-main)]" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. TYPOGRAPHIE */}
      <div className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-6 transition-shadow hover:shadow-[0_8px_24px_-16px_rgba(11,15,23,0.18)] hover:-translate-y-[2px]">
        <h3 className="font-bold text-[11px] text-[var(--text-muted)] tracking-[0.12em] uppercase mb-5">
          Typographie
        </h3>
        <div className="flex flex-col gap-2">
          {PREMIUM_FONTS.map(font => {
            const isSelected = profile.font_fr === font.id;
            return (
              <button
                key={font.id}
                onClick={() => updateProfile({ font_fr: font.id })}
                className={cn(
                  "flex items-center justify-between p-4 rounded-xl border transition-all text-left",
                  isSelected ? "border-[var(--text-main)] bg-[var(--bg-medical-pearl)]" : "border-[var(--border-color)] hover:border-[var(--text-muted)]"
                )}
              >
                <div>
                  <div className={cn("text-[16px] text-[var(--text-main)] leading-tight mb-1", font.class)}>
                    {font.name}
                  </div>
                  <div className="text-[13px] text-[var(--text-muted)]">
                    {font.desc}
                  </div>
                </div>
                {isSelected && <div className="w-5 h-5 rounded-full bg-[var(--text-main)] text-white flex items-center justify-center shrink-0"><Check size={12} /></div>}
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. MODÈLES D'ORDONNANCE */}
      <div className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-6 transition-shadow hover:shadow-[0_8px_24px_-16px_rgba(11,15,23,0.18)] hover:-translate-y-[2px]">
        <h3 className="font-bold text-[11px] text-[var(--text-muted)] tracking-[0.12em] uppercase mb-5">
          Modèles d'Ordonnance
        </h3>
        <div className={cn("grid grid-cols-2 gap-3", designLockedClass)}>
          {[
            { id: 'swiss', name: 'Swiss Clinic', desc: 'Précision & Clarté' },
            { id: 'royal', name: 'Royal Elite', desc: 'Symétrie Absolue' },
            { id: 'clinical', name: 'Clinical Grid', desc: 'Rigueur Scientifique' },
            { id: 'modern', name: 'Modern Flush', desc: 'Aération Contemporaine' },
            { id: 'heritage', name: 'L\'Héritage', desc: 'Prestige Classique' }
          ].map(tpl => {
            const isSelected = profile.selected_template === tpl.id;
            return (
              <button
                key={tpl.id}
                onClick={() => updateProfile({ selected_template: tpl.id })}
                className={cn(
                  "flex flex-col items-start gap-1 p-3 rounded-xl border transition-all text-left",
                  isSelected ? "border-[var(--text-main)] bg-[var(--bg-medical-pearl)]" : "border-[var(--border-color)] hover:border-[var(--text-muted)]"
                )}
              >
                <span className={cn("text-[13px] font-bold leading-tight", isSelected ? "text-[var(--text-main)]" : "text-[var(--text-main)]")}>
                  {tpl.name}
                </span>
                <span className="text-[11px] text-[var(--text-muted)]">{tpl.desc}</span>
                {isSelected && <div className="absolute"><Check size={14} className="text-[var(--text-main)] opacity-0" /></div>}
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. MISE EN PAGE */}
      <div className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-6 transition-shadow hover:shadow-[0_8px_24px_-16px_rgba(11,15,23,0.18)] hover:-translate-y-[2px]">
        <h3 className="font-bold text-[11px] text-[var(--text-muted)] tracking-[0.12em] uppercase mb-5">
          Mise en page
        </h3>
        
        <div className="flex bg-[var(--bg-medical-pearl)] p-1 rounded-xl mb-6">
          {(['compact', 'confort', 'etendu'] as Density[]).map(d => (
            <button
              key={d}
              onClick={() => handleDensityClick(d)}
              className={cn(
                "flex-1 py-2 font-medium text-[13px] rounded-lg transition-all capitalize",
                currentDensity === d ? "bg-white text-[var(--text-main)] shadow-sm" : "text-[var(--text-muted)] hover:text-[var(--text-main)]"
              )}
            >
              {d}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-5">
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-[13px] text-[var(--text-muted)]">Marge supérieure</label>
              <span className="text-[13px] font-medium text-[var(--text-main)]">{profile.margin_top ?? 4.8}cm</span>
            </div>
            <input type="range" min="1" max="8" step="0.1" value={profile.margin_top ?? 4.8} onChange={e => updateProfile({ margin_top: parseFloat(e.target.value) })} className="w-full h-1.5 bg-[var(--border-color)] rounded-full appearance-none outline-none accent-[var(--text-main)]" />
          </div>
          <div className={cn(customDesignActive && "opacity-50 pointer-events-none")}>
            <div className="flex justify-between mb-2">
              <label className="text-[13px] text-[var(--text-muted)]">Taille du logo</label>
              <span className="text-[13px] font-medium text-[var(--text-main)]">{Math.round((profile.header_logo_scale ?? 1.0) * 100)}%</span>
            </div>
            <input type="range" min="0.5" max="2.0" step="0.05" value={profile.header_logo_scale ?? 1.0} onChange={e => updateProfile({ header_logo_scale: parseFloat(e.target.value) })} className="w-full h-1.5 bg-[var(--border-color)] rounded-full appearance-none outline-none accent-[var(--text-main)]" />
          </div>
          <div className={cn(customDesignActive && "opacity-50 pointer-events-none")}>
            <label className="text-[13px] text-[var(--text-muted)] mb-2 block">Position du logo</label>
            <PositionPad
              x={profile.header_logo_offset_x ?? 0}
              y={profile.header_logo_offset_y ?? 0}
              onChange={(x, y) => updateProfile({ header_logo_offset_x: x, header_logo_offset_y: y })}
            />
          </div>
        </div>

        <button 
          onClick={toggleAdvanced}
          className="mt-5 flex items-center gap-2 text-[13px] font-semibold text-[var(--text-muted)] hover:text-[var(--text-main)] transition-colors"
        >
          Réglages avancés {advancedOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        {advancedOpen && (
          <div className="mt-5 pt-5 border-t border-[var(--border-color)] flex flex-col gap-5">
            <div className={cn(customDesignActive && "opacity-50 pointer-events-none")}>
              <div className="flex justify-between mb-2"><label className="text-[13px] text-[var(--text-muted)]">Police en-tête</label></div>
              <input type="range" min="0.5" max="2.0" step="0.05" value={profile.header_font_scale ?? 1.0} onChange={e => updateProfile({ header_font_scale: parseFloat(e.target.value) })} className="w-full h-1.5 bg-[var(--border-color)] rounded-full appearance-none outline-none accent-[var(--text-main)]" />
            </div>
            <div>
              <div className="flex justify-between mb-2"><label className="text-[13px] text-[var(--text-muted)]">Interligne en-tête</label></div>
              <input type="range" min="0.5" max="2.0" step="0.05" value={profile.header_line_height ?? 1.0} onChange={e => updateProfile({ header_line_height: parseFloat(e.target.value) })} className="w-full h-1.5 bg-[var(--border-color)] rounded-full appearance-none outline-none accent-[var(--text-main)]" />
            </div>
            <div className={cn(customDesignActive && "opacity-50 pointer-events-none")}>
              <div className="flex justify-between mb-2"><label className="text-[13px] text-[var(--text-muted)]">Marge inférieure</label></div>
              <input type="range" min="1" max="6" step="0.1" value={profile.margin_bottom ?? 3.2} onChange={e => updateProfile({ margin_bottom: parseFloat(e.target.value) })} className="w-full h-1.5 bg-[var(--border-color)] rounded-full appearance-none outline-none accent-[var(--text-main)]" />
            </div>
            <div className={cn(customDesignActive && "opacity-50 pointer-events-none")}>
              <div className="flex justify-between mb-2"><label className="text-[13px] text-[var(--text-muted)]">Police pied de page</label></div>
              <input type="range" min="0.5" max="2.0" step="0.05" value={profile.footer_font_scale ?? 1.0} onChange={e => updateProfile({ footer_font_scale: parseFloat(e.target.value) })} className="w-full h-1.5 bg-[var(--border-color)] rounded-full appearance-none outline-none accent-[var(--text-main)]" />
            </div>
            <div className={cn(customDesignActive && "opacity-50 pointer-events-none")}>
              <div className="flex justify-between mb-2"><label className="text-[13px] text-[var(--text-muted)]">Interligne pied de page</label></div>
              <input type="range" min="0.5" max="2.0" step="0.05" value={profile.footer_line_height ?? 1.0} onChange={e => updateProfile({ footer_line_height: parseFloat(e.target.value) })} className="w-full h-1.5 bg-[var(--border-color)] rounded-full appearance-none outline-none accent-[var(--text-main)]" />
            </div>
            <div>
              <div className="flex justify-between mb-2"><label className="text-[13px] text-[var(--text-muted)]">Taille QR Code</label></div>
              <input type="range" min="0.5" max="2.0" step="0.05" value={profile.footer_qr_scale ?? 1.0} onChange={e => updateProfile({ footer_qr_scale: parseFloat(e.target.value) })} className="w-full h-1.5 bg-[var(--border-color)] rounded-full appearance-none outline-none accent-[var(--text-main)]" />
            </div>
            <div>
              <label className="text-[13px] text-[var(--text-muted)] mb-2 block">Position du QR Code</label>
              <PositionPad
                x={profile.qr_code_offset_x ?? 0}
                y={profile.qr_code_offset_y ?? 0}
                onChange={(x, y) => updateProfile({ qr_code_offset_x: x, qr_code_offset_y: y })}
              />
            </div>
          </div>
        )}
      </div>

      {/* 5. FOND DE PAGE (LETTERHEAD) */}
      <div className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-6 transition-shadow hover:shadow-[0_8px_24px_-16px_rgba(11,15,23,0.18)] hover:-translate-y-[2px]">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-bold text-[11px] text-[var(--text-muted)] tracking-[0.12em] uppercase">
            Fond de Page (Template Image)
          </h3>
          <button
            onClick={() => updateProfile({ use_letterhead: !profile.use_letterhead })}
            className={cn("w-10 h-5 rounded-full relative px-0.5 flex items-center transition-colors", profile.use_letterhead ? "bg-[var(--primary)]" : "bg-[var(--border-color)]")}
          >
            <div className={cn("w-4 h-4 bg-white rounded-full transition-transform", profile.use_letterhead ? "translate-x-5" : "translate-x-0")} />
          </button>
        </div>

        {profile.use_letterhead && (
          <div className="flex flex-col gap-3">
            {customDesignActive && (
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-[12px] text-slate-600">
                Le design importé remplace l’en-tête, le footer et la palette du document. Les marges et le QR restent configurables.
              </div>
            )}

            {/* Aperçu + suppression du modèle actuellement actif */}
            {customDesignActive && letterheadSrc && (
              <div className="flex items-center gap-3 p-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-medical-pearl)]">
                <img
                  src={letterheadSrc}
                  alt="Modèle de document du cabinet"
                  className="w-16 h-24 object-cover rounded-md border border-[var(--border-color)] bg-white"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-[12px] font-semibold text-[var(--text-main)]">Modèle actif</p>
                  <p className="text-[10px] text-[var(--text-muted)] truncate">Appliqué comme fond sur tous les documents générés</p>
                </div>
                <button
                  onClick={() => deleteLetterhead()}
                  aria-label="Supprimer le modèle de document"
                  className="p-2 rounded-lg text-[var(--text-muted)] hover:text-red-500 hover:bg-red-50 transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            )}

            {/* Option : document déjà rempli -> ne garder que l’en-tête et le footer */}
            <div className="flex items-center justify-between p-3 rounded-xl border border-[var(--border-color)]">
              <div className="flex items-center gap-2 min-w-0">
                <FileText size={14} className="text-[var(--text-muted)] shrink-0" />
                <span className="text-[12px] text-[var(--text-main)]">Document déjà rempli — ne garder que l’en-tête et le pied de page</span>
              </div>
              <button
                onClick={() => setStripBody(!stripBody)}
                aria-label="Nettoyer le corps du document uploadé"
                className={cn("w-10 h-5 rounded-full relative px-0.5 flex items-center transition-colors shrink-0", stripBody ? "bg-[var(--primary)]" : "bg-[var(--border-color)]")}
              >
                <div className={cn("w-4 h-4 bg-white rounded-full transition-transform", stripBody ? "translate-x-5" : "translate-x-0")} />
              </button>
            </div>

            {stripBody && (
              <div className="flex flex-col gap-3 px-1">
                <label className="flex flex-col gap-1 text-[11px] text-[var(--text-muted)]">
                  Hauteur de l’en-tête conservée : {headerPct}%
                  <input type="range" min={5} max={45} value={headerPct}
                         onChange={(e) => setHeaderPct(Number(e.target.value))} />
                </label>
                <label className="flex flex-col gap-1 text-[11px] text-[var(--text-muted)]">
                  Hauteur du pied de page conservée : {footerPct}%
                  <input type="range" min={5} max={45} value={footerPct}
                         onChange={(e) => setFooterPct(Number(e.target.value))} />
                </label>
                {!pendingFile && (
                  <p className="text-[10px] text-[var(--text-muted)]">
                    Sélectionnez une image ci-dessous pour prévisualiser la zone qui sera effacée avant de l’envoyer.
                  </p>
                )}
              </div>
            )}

            {/* Aperçu local avant envoi : montre précisément où passe la découpe
                sur l'image réelle, pour éviter d'uploader un document mal calé
                (le blanchiment n'est pas réversible sans ré-uploader l'original). */}
            {pendingFile && pendingPreviewUrl && (
              <div className="flex flex-col gap-3">
                <div className="relative rounded-xl overflow-hidden border border-[var(--border-color)]">
                  <img src={pendingPreviewUrl} alt="Aperçu du document avant découpe" className="w-full h-auto block" />
                  {/* Bande centrale qui sera blanchie */}
                  <div
                    className="absolute left-0 right-0 bg-red-500/25 border-y-2 border-red-500/70 flex items-center justify-center"
                    style={{ top: `${headerPct}%`, bottom: `${footerPct}%` }}
                  >
                    <span className="px-2 py-0.5 rounded-full bg-red-600 text-white text-[10px] font-black uppercase tracking-widest shadow">
                      Sera effacé
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={confirmPendingUpload}
                    disabled={isUploadingLocal}
                    className={cn(
                      "flex-1 p-2.5 rounded-xl text-[12px] font-bold text-white transition-all",
                      isUploadingLocal ? "opacity-50 cursor-not-allowed bg-[var(--primary)]" : "bg-[var(--primary)] hover:opacity-90"
                    )}
                  >
                    {isUploadingLocal ? "Envoi..." : "Confirmer et envoyer"}
                  </button>
                  <button
                    onClick={cancelPendingUpload}
                    disabled={isUploadingLocal}
                    className="p-2.5 rounded-xl text-[12px] font-bold text-[var(--text-muted)] border border-[var(--border-color)] hover:text-red-500 hover:border-red-200 transition-all disabled:opacity-50"
                  >
                    Annuler
                  </button>
                </div>
              </div>
            )}

            {!pendingFile && (
              <div className="flex items-center gap-3">
              <input
                type="file"
                accept="image/png,image/jpeg,application/pdf"
                id="letterhead-upload"
                className="hidden"
                onChange={handleFileUpload}
                disabled={isUploadingLocal}
              />
              <label
                htmlFor="letterhead-upload"
                className={cn(
                  "flex items-center justify-center gap-2 flex-1 p-3 rounded-xl border border-dashed text-[13px] font-medium transition-all cursor-pointer",
                  isUploadingLocal ? "opacity-50 cursor-not-allowed" : "hover:border-[var(--primary)] hover:text-[var(--primary)] text-[var(--text-muted)]"
                )}
              >
                <Upload size={16} />
                {isUploadingLocal ? "Envoi..." : "Uploader un modèle (image ou PDF)"}
              </label>
              </div>
            )}

            {stripBody && (
              <p className="text-[10px] text-[var(--text-muted)] px-1">
                Les PDF sont convertis côté serveur sans aperçu local — vérifiez le rendu généré après l’envoi.
              </p>
            )}
          </div>
        )}
      </div>

      {/* 6. CODE QR */}
      <div className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-6 transition-shadow hover:shadow-[0_8px_24px_-16px_rgba(11,15,23,0.18)] hover:-translate-y-[2px]">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-bold text-[11px] text-[var(--text-muted)] tracking-[0.12em] uppercase">
            Code QR
          </h3>
          <button 
            onClick={() => updateProfile({ qr_code_enabled: !profile.qr_code_enabled })} 
            className={cn("w-10 h-5 rounded-full relative px-0.5 flex items-center transition-colors", profile.qr_code_enabled ? "bg-[var(--primary)]" : "bg-[var(--border-color)]")}
          >
            <div className={cn("w-4 h-4 bg-white rounded-full transition-transform", profile.qr_code_enabled ? "translate-x-5" : "translate-x-0")} />
          </button>
        </div>

        {profile.qr_code_enabled && (
          <div className="grid grid-cols-2 gap-3">
            {QR_TYPES.map(t => {
              const isSelected = profile.qr_code_type === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => updateProfile({ qr_code_type: t.id })}
                  className={cn(
                    "flex flex-col items-center justify-center gap-2 p-3 rounded-xl border transition-all text-[11px] font-medium",
                    isSelected ? "border-[var(--text-main)] bg-[var(--bg-medical-pearl)] text-[var(--text-main)]" : "border-[var(--border-color)] hover:border-[var(--text-muted)] text-[var(--text-muted)] hover:text-[var(--text-main)]"
                  )}
                >
                  {t.icon}
                  {t.label}
                </button>
              );
            })}
          </div>
        )}

        {profile.qr_code_enabled && ['WEBSITE', 'WHATSAPP', 'INSTAGRAM'].includes(profile.qr_code_type) && (
          <div className="mt-5 flex flex-col gap-4">
             <div>
               <label className="block text-[11px] text-[var(--text-muted)] mb-1">Lien / Numéro / Identifiant</label>
               <input 
                 type="text" 
                 value={profile.qr_code_value || ''}
                 onChange={e => updateProfile({ qr_code_value: e.target.value })}
                 className="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-[13px] text-[var(--text-main)] outline-none focus:border-[var(--text-main)]"
                 placeholder="Ex: https://..."
               />
             </div>
             <div>
               <label className="block text-[11px] text-[var(--text-muted)] mb-1">Texte sous le QR Code</label>
               <input 
                 type="text" 
                 value={profile.qr_code_label || ''}
                 onChange={e => updateProfile({ qr_code_label: e.target.value })}
                 className="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-[13px] text-[var(--text-main)] outline-none focus:border-[var(--text-main)]"
                 placeholder="Ex: Prenez RDV"
               />
             </div>
          </div>
        )}
      </div>

    </div>
  );
};


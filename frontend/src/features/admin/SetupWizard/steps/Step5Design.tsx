import React, { useState } from 'react';
import { Image as ImageIcon, FileImage, Type, Palette, Upload, MousePointer2, Check, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import { BRAND_IDENTITIES, PREMIUM_FONTS } from '../../constants';
import type { HeaderOption, TemplateOption } from '../../types';
import Logo from '../../../../assets/logo.png';

const DENSITY_DEFAULTS = {
  compact: { margin_top: 2.6, margin_bottom: 2.4, header_logo_scale: 0.8,  header_font_scale: 0.9, footer_font_scale: 0.9, header_line_height: 0.95, footer_line_height: 0.95 },
  confort: { margin_top: 3.6, margin_bottom: 3.2, header_logo_scale: 1.0,  header_font_scale: 1.0, footer_font_scale: 1.0, header_line_height: 1.0,  footer_line_height: 1.0  },
  etendu:  { margin_top: 4.4, margin_bottom: 3.8, header_logo_scale: 1.15, header_font_scale: 1.1, footer_font_scale: 1.05, header_line_height: 1.1, footer_line_height: 1.1  },
};

type Density = 'compact' | 'confort' | 'etendu';

interface Props {
  headerOption: HeaderOption;
  setHeaderOption: (v: HeaderOption) => void;
  selectedIdentity: string;
  setSelectedIdentity: (v: string) => void;
  selectedFont: string;
  setSelectedFont: (v: string) => void;
  selectedTemplate: TemplateOption;
  setSelectedTemplate: (v: TemplateOption) => void;
  logoPreview: string | null;
  letterheadPreview: string | null;
  logoInputRef: React.RefObject<HTMLInputElement | null>;
  letterheadInputRef: React.RefObject<HTMLInputElement | null>;
  handleLogoChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleLetterheadChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  margins: { top: number; bottom: number };
  setMargins: React.Dispatch<React.SetStateAction<{ top: number; bottom: number }>>;
  headerScale: number;
  setHeaderScale: (v: number) => void;
  advanced?: {
    headerFontScale: number; setHeaderFontScale: (v: number) => void;
    headerLogoScale: number; setHeaderLogoScale: (v: number) => void;
    headerLineHeight: number; setHeaderLineHeight: (v: number) => void;
    footerFontScale: number; setFooterFontScale: (v: number) => void;
    footerQrScale: number; setFooterQrScale: (v: number) => void;
    footerLineHeight: number; setFooterLineHeight: (v: number) => void;
  };
}

const TEMPLATES = [
  { id: 'swiss', name: 'Swiss Clinic', desc: 'Précision & Clarté' },
  { id: 'royal', name: 'Royal Elite', desc: 'Symétrie Absolue' },
  { id: 'clinical', name: 'Clinical Grid', desc: 'Rigueur Scientifique' },
  { id: 'modern', name: 'Modern Flush', desc: 'Aération Contemporaine' },
  { id: 'heritage', name: 'L\'Héritage', desc: 'Prestige Classique' }
];

export const Step5Design: React.FC<Props> = ({
  headerOption, setHeaderOption,
  selectedIdentity, setSelectedIdentity,
  selectedFont, setSelectedFont,
  selectedTemplate, setSelectedTemplate,
  logoPreview, letterheadPreview,
  logoInputRef, letterheadInputRef,
  handleLogoChange, handleLetterheadChange,
  margins, setMargins,
  headerScale, setHeaderScale,
  advanced
}) => {
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const currentDensity: Density = 
    (margins.top === DENSITY_DEFAULTS.compact.margin_top) ? 'compact' :
    (margins.top === DENSITY_DEFAULTS.etendu.margin_top) ? 'etendu' : 'confort';

  const handleDensityClick = (d: Density) => {
    const vals = DENSITY_DEFAULTS[d];
    setMargins({ top: vals.margin_top, bottom: vals.margin_bottom });
    if (advanced) {
      advanced.setHeaderLogoScale(vals.header_logo_scale);
      advanced.setHeaderFontScale(vals.header_font_scale);
      advanced.setFooterFontScale(vals.footer_font_scale);
      advanced.setHeaderLineHeight(vals.header_line_height);
      advanced.setFooterLineHeight(vals.footer_line_height);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="text-center">
        <h2 className="text-2xl font-black text-slate-900 tracking-tight">Studio de Design</h2>
        <p className="text-slate-500 text-sm mt-1">Personnalisez l'apparence de vos documents officiels.</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={() => setHeaderOption('auto')}
          className={cn("p-5 rounded-2xl border-2 text-left transition-all", headerOption === 'auto' ? "border-primary bg-primary/5 shadow-lg" : "border-slate-200 bg-white")}
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary"><ImageIcon size={18} /></div>
            <span className="font-bold text-slate-900">Auto-Généré</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">Mise en page automatique avec votre logo et typo.</p>
        </button>

        <button
          onClick={() => setHeaderOption('letterhead')}
          className={cn("p-5 rounded-2xl border-2 text-left transition-all", headerOption === 'letterhead' ? "border-emerald-500 bg-emerald-50 shadow-lg" : "border-slate-200 bg-white")}
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600"><FileImage size={18} /></div>
            <span className="font-bold text-slate-900">Papier A5</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">Uploadez votre propre papier à en-tête pré-imprimé.</p>
        </button>
      </div>

      {headerOption === 'auto' ? (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h3 className="font-bold text-[11px] text-slate-400 tracking-[0.12em] uppercase mb-5">Palette</h3>
            <div className="grid grid-cols-2 gap-3">
              {BRAND_IDENTITIES.map(palette => {
                const isSelected = selectedIdentity === palette.id;
                return (
                  <button
                    key={palette.id}
                    onClick={() => {
                      setSelectedIdentity(palette.id);
                      document.documentElement.style.setProperty('--primary', palette.primary);
                      document.documentElement.style.setProperty('--accent', palette.accent);
                    }}
                    className={cn(
                      "flex items-center gap-3 p-3 rounded-xl border transition-all text-left group",
                      isSelected ? "border-primary bg-primary/5" : "border-slate-200 hover:border-slate-400"
                    )}
                  >
                    <div className="flex w-[32px] h-[32px] rounded-md overflow-hidden border border-slate-200 flex-shrink-0">
                      <div className="flex-1" style={{ backgroundColor: palette.primary }} />
                      <div className="flex-1" style={{ backgroundColor: palette.secondary }} />
                      <div className="flex-1" style={{ backgroundColor: palette.accent }} />
                    </div>
                    <span className={cn("text-[13px] font-medium leading-tight", isSelected ? "text-primary" : "text-slate-500 group-hover:text-slate-800")}>
                      {palette.name}
                    </span>
                    {isSelected && <Check size={14} className="ml-auto text-primary" />}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h3 className="font-bold text-[11px] text-slate-400 tracking-[0.12em] uppercase mb-5">Typographie</h3>
            <div className="flex flex-col gap-2">
              {PREMIUM_FONTS.map(font => {
                const isSelected = selectedFont === font.id;
                return (
                  <button
                    key={font.id}
                    onClick={() => setSelectedFont(font.id)}
                    className={cn(
                      "flex items-center justify-between p-4 rounded-xl border transition-all text-left",
                      isSelected ? "border-primary bg-primary/5" : "border-slate-200 hover:border-slate-400"
                    )}
                  >
                    <div>
                      <div className={cn("text-[16px] leading-tight mb-1", font.class, isSelected ? "text-primary" : "text-slate-800")}>
                        {font.name}
                      </div>
                      <div className="text-[13px] text-slate-500">{font.desc}</div>
                    </div>
                    {isSelected && <div className="w-5 h-5 rounded-full bg-primary text-white flex items-center justify-center shrink-0"><Check size={12} /></div>}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h3 className="font-bold text-[11px] text-slate-400 tracking-[0.12em] uppercase mb-5">Modèles d'Ordonnance</h3>
            <div className="grid grid-cols-2 gap-3">
              {TEMPLATES.map(tpl => {
                const isSelected = selectedTemplate === tpl.id;
                return (
                  <button
                    key={tpl.id}
                    onClick={() => setSelectedTemplate(tpl.id as TemplateOption)}
                    className={cn(
                      "flex flex-col items-start gap-1 p-3 rounded-xl border transition-all text-left relative",
                      isSelected ? "border-primary bg-primary/5" : "border-slate-200 hover:border-slate-400"
                    )}
                  >
                    <span className={cn("text-[13px] font-bold leading-tight", isSelected ? "text-primary" : "text-slate-800")}>{tpl.name}</span>
                    <span className="text-[11px] text-slate-500">{tpl.desc}</span>
                    {isSelected && <Check size={14} className="absolute top-3 right-3 text-primary" />}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h3 className="font-bold text-[11px] text-slate-400 tracking-[0.12em] uppercase mb-5">Mise en page</h3>
            <div className="flex bg-slate-50 p-1 rounded-xl mb-6 border border-slate-100">
              {(['compact', 'confort', 'etendu'] as Density[]).map(d => (
                <button
                  key={d}
                  onClick={() => handleDensityClick(d)}
                  className={cn(
                    "flex-1 py-2 font-medium text-[13px] rounded-lg transition-all capitalize",
                    currentDensity === d ? "bg-white text-primary shadow-sm" : "text-slate-500 hover:text-slate-800"
                  )}
                >
                  {d}
                </button>
              ))}
            </div>

            <div className="flex flex-col gap-5">
              <div>
                <div className="flex justify-between mb-2">
                  <label className="text-[13px] text-slate-500">Marge supérieure</label>
                  <span className="text-[13px] font-medium text-primary">{margins.top}cm</span>
                </div>
                <input type="range" min="1" max="8" step="0.1" value={margins.top} onChange={e => setMargins(m => ({ ...m, top: parseFloat(e.target.value) }))} className="w-full h-1.5 bg-slate-200 rounded-full appearance-none outline-none accent-primary cursor-pointer" />
              </div>
              {advanced && (
                <div>
                  <div className="flex justify-between mb-2">
                    <label className="text-[13px] text-slate-500">Taille du logo</label>
                    <span className="text-[13px] font-medium text-primary">{Math.round(advanced.headerLogoScale * 100)}%</span>
                  </div>
                  <input type="range" min="0.5" max="2.0" step="0.05" value={advanced.headerLogoScale} onChange={e => advanced.setHeaderLogoScale(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-200 rounded-full appearance-none outline-none accent-primary cursor-pointer" />
                </div>
              )}
            </div>

            {advanced && (
              <>
                <button 
                  onClick={() => setAdvancedOpen(!advancedOpen)}
                  className="mt-5 flex items-center gap-2 text-[13px] font-semibold text-slate-500 hover:text-slate-800 transition-colors"
                >
                  Réglages avancés {advancedOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>

                {advancedOpen && (
                  <div className="mt-5 pt-5 border-t border-slate-200 flex flex-col gap-5 animate-in fade-in slide-in-from-top-2">
                    <div>
                      <div className="flex justify-between mb-2"><label className="text-[13px] text-slate-500">Police en-tête</label></div>
                      <input type="range" min="0.5" max="2.0" step="0.05" value={advanced.headerFontScale} onChange={e => advanced.setHeaderFontScale(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-200 rounded-full appearance-none outline-none accent-primary cursor-pointer" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-2"><label className="text-[13px] text-slate-500">Interligne en-tête</label></div>
                      <input type="range" min="0.5" max="2.0" step="0.05" value={advanced.headerLineHeight} onChange={e => advanced.setHeaderLineHeight(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-200 rounded-full appearance-none outline-none accent-primary cursor-pointer" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-2"><label className="text-[13px] text-slate-500">Marge inférieure</label></div>
                      <input type="range" min="1" max="6" step="0.1" value={margins.bottom} onChange={e => setMargins(m => ({ ...m, bottom: parseFloat(e.target.value) }))} className="w-full h-1.5 bg-slate-200 rounded-full appearance-none outline-none accent-primary cursor-pointer" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-2"><label className="text-[13px] text-slate-500">Police pied de page</label></div>
                      <input type="range" min="0.5" max="2.0" step="0.05" value={advanced.footerFontScale} onChange={e => advanced.setFooterFontScale(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-200 rounded-full appearance-none outline-none accent-primary cursor-pointer" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-2"><label className="text-[13px] text-slate-500">Interligne pied de page</label></div>
                      <input type="range" min="0.5" max="2.0" step="0.05" value={advanced.footerLineHeight} onChange={e => advanced.setFooterLineHeight(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-200 rounded-full appearance-none outline-none accent-primary cursor-pointer" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-2"><label className="text-[13px] text-slate-500">Taille QR Code</label></div>
                      <input type="range" min="0.5" max="2.0" step="0.05" value={advanced.footerQrScale} onChange={e => advanced.setFooterQrScale(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-200 rounded-full appearance-none outline-none accent-primary cursor-pointer" />
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-24 h-12 flex items-center justify-center bg-white overflow-hidden p-1 shadow-sm rounded-lg">
                {logoPreview
                  ? <img src={logoPreview} className="w-full h-full object-contain" alt="Logo" />
                  : <img src={Logo} className="w-full h-full object-contain opacity-80" alt="Default Logo" />}
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Logo du cabinet</h4>
                <p className="text-[10px] text-slate-500">PNG ou SVG (Optionnel)</p>
              </div>
            </div>
            <button onClick={() => logoInputRef.current?.click()} className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-all shadow-sm">Uploader</button>
            <input ref={logoInputRef} type="file" className="hidden" accept="image/png,image/svg+xml" onChange={handleLogoChange} />
          </div>
        </div>
      ) : (
        <div className="p-8 bg-emerald-50 border border-emerald-200 rounded-[2rem] space-y-6">
          <div className="flex flex-col items-center">
            <div
              onClick={() => letterheadInputRef.current?.click()}
              className={cn(
                "w-full h-48 rounded-2xl border-2 border-dashed cursor-pointer flex flex-col items-center justify-center transition-all shadow-inner",
                letterheadPreview ? "border-emerald-500 bg-white" : "border-emerald-300 hover:bg-white"
              )}
            >
              {letterheadPreview
                ? <img src={letterheadPreview} className="h-full object-contain p-4" alt="Letterhead" />
                : (
                  <>
                    <Upload className="text-emerald-400 mb-2" size={32} />
                    <span className="text-xs font-bold text-emerald-600">Uploader votre Papier A5</span>
                  </>
                )}
            </div>
            <input ref={letterheadInputRef} type="file" className="hidden" accept="image/png,image/jpeg" onChange={handleLetterheadChange} />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block">Marge Haute ({margins.top} cm)</label>
              <input type="range" min="1" max="8" step="0.5" value={margins.top}
                onChange={e => setMargins(m => ({ ...m, top: parseFloat(e.target.value) }))}
                className="w-full h-1.5 bg-emerald-200 rounded-lg accent-emerald-600 cursor-pointer"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block">Marge Basse ({margins.bottom} cm)</label>
              <input type="range" min="1" max="6" step="0.5" value={margins.bottom}
                onChange={e => setMargins(m => ({ ...m, bottom: parseFloat(e.target.value) }))}
                className="w-full h-1.5 bg-emerald-200 rounded-lg accent-emerald-600 cursor-pointer"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

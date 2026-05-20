import React from 'react';
import { Image as ImageIcon, FileImage, Type, Palette, Upload, MousePointer2 } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import { BRAND_IDENTITIES, PREMIUM_FONTS, DESIGN_VARIANTS } from '../../constants';
import type { HeaderOption, TemplateOption } from '../../types';
import Logo from '../../../../assets/logo.png';

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
}

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
}) => (
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
        <div className="bg-slate-50 p-6 rounded-3xl border border-slate-200/60">
          <div className="flex items-center justify-between mb-4">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">Identité Visuelle & Harmonie</label>
            <span className="text-[9px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full">Mode Elite</span>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-6">
            {BRAND_IDENTITIES.map(id => (
              <button
                key={id.id}
                onClick={() => setSelectedIdentity(id.id)}
                className={cn(
                  "p-4 rounded-2xl border-2 transition-all text-left flex flex-col gap-3 group relative overflow-hidden",
                  selectedIdentity === id.id ? "border-primary bg-white shadow-lg scale-[1.02]" : "border-slate-200 bg-slate-50 hover:border-slate-300"
                )}
              >
                <div className="flex items-center justify-between">
                  <h5 className="text-[10px] font-black uppercase tracking-tighter text-slate-900">{id.name}</h5>
                  <div className="flex -space-x-2">
                    <div className="w-4 h-4 rounded-full border border-white shadow-sm" style={{ backgroundColor: id.primary }} />
                    <div className="w-4 h-4 rounded-full border border-white shadow-sm" style={{ backgroundColor: id.secondary }} />
                    <div className="w-4 h-4 rounded-full border border-white shadow-sm" style={{ backgroundColor: id.accent }} />
                  </div>
                </div>
                <p className="text-[9px] text-slate-500 leading-tight italic">{id.vibe}</p>
              </button>
            ))}
          </div>

          <div className="pt-6 border-t border-slate-200/60 space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <Palette size={14} className="text-primary" />
              <span className="text-[10px] font-black text-slate-900 uppercase tracking-widest">Ajustement Précis des Teintes</span>
            </div>
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: 'Primaire', prop: '--primary', defaultColor: BRAND_IDENTITIES.find(i => i.id === selectedIdentity)?.primary || '#003380' },
                { label: 'Accent', prop: '--accent', defaultColor: BRAND_IDENTITIES.find(i => i.id === selectedIdentity)?.accent || '#60a5fa' },
              ].map(({ label, prop, defaultColor }) => (
                <div key={prop} className="space-y-2">
                  <label className="text-[9px] font-bold text-slate-400 block uppercase">{label}</label>
                  <div className="flex items-center gap-2 bg-white p-2 rounded-xl border border-slate-200">
                    <input
                      type="color"
                      className="w-6 h-6 rounded-lg cursor-pointer border-none bg-transparent"
                      value={defaultColor}
                      onChange={e => document.documentElement.style.setProperty(prop, e.target.value)}
                    />
                    <span className="text-[10px] font-mono text-slate-500">HEX</span>
                  </div>
                </div>
              ))}
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-slate-400 block uppercase">Fond Paper</label>
                <div className="flex items-center gap-2 bg-white p-2 rounded-xl border border-slate-200">
                  <div className="w-6 h-6 rounded-lg bg-[#f8fafc] border border-slate-100" />
                  <span className="text-[9px] font-bold text-slate-400">Pearl</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-3">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2"><Type size={12} /> Typographie Premium</label>
            <div className="space-y-2">
              {PREMIUM_FONTS.map(f => (
                <button
                  key={f.id}
                  onClick={() => setSelectedFont(f.id)}
                  className={cn(
                    "w-full p-2.5 rounded-xl border text-left flex items-center justify-between transition-all",
                    selectedFont === f.id ? "border-primary bg-primary/5 ring-1 ring-primary/20" : "border-slate-200 bg-white hover:bg-slate-50"
                  )}
                >
                  <div>
                    <span className={cn("block text-sm font-bold", f.class)}>{f.name}</span>
                    <span className="text-[9px] text-slate-400">{f.desc}</span>
                  </div>
                  {selectedFont === f.id && <MousePointer2 size={12} className="text-primary" />}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2"><Palette size={12} /> Modèle de mise en page</label>
            <div className="space-y-2">
              {DESIGN_VARIANTS.map((v: any) => (
                <button
                  key={v.id}
                  onClick={() => setSelectedTemplate(v.id as TemplateOption)}
                  className={cn(
                    "w-full p-2.5 rounded-xl border text-left flex items-center gap-3 transition-all",
                    selectedTemplate === v.id ? "border-primary bg-primary/5" : "border-slate-200 bg-white"
                  )}
                >
                  <v.icon size={16} className={selectedTemplate === v.id ? "text-primary" : "text-slate-400"} />
                  <span className="text-xs font-bold text-slate-900">{v.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Header Scale Control (Elite v4.2) */}
        <div className="pt-4 border-t border-slate-200/60 space-y-4">
           <div className="flex justify-between items-end">
             <div className="flex items-center gap-2">
               <Type size={14} className="text-primary" />
               <span className="text-[10px] font-black text-slate-900 uppercase tracking-widest">Dimension des Textes (En-tête)</span>
             </div>
             <span className="text-sm font-black text-primary">{Math.round(headerScale * 100)}%</span>
           </div>
           <input 
             type="range" min="0.5" max="1.8" step="0.05" value={headerScale}
             onChange={e => setHeaderScale(parseFloat(e.target.value))}
             className="w-full h-1.5 bg-slate-200 rounded-lg accent-primary cursor-pointer"
           />
           <p className="text-[9px] text-slate-400 italic">Ajustez cette valeur si vous trouvez que les noms sont trop petits ou trop grands.</p>
        </div>

        <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-24 h-12 flex items-center justify-center bg-white overflow-hidden p-1">
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

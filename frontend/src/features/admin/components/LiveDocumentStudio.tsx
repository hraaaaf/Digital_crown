import React from 'react';
import { Sparkles, Image as ImageIcon, QrCode } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { 
  BRAND_IDENTITIES, 
  PREMIUM_FONTS 
} from '../constants';
import type { 
  IdentityState, 
  TemplateOption, 
  HeaderOption, 
} from '../types';

interface LiveDocumentStudioProps {
  identity: IdentityState;
  selectedIdentity: string;
  selectedTemplate: TemplateOption;
  selectedFont: string;
  headerOption: HeaderOption;
  logoPreview: string | null;
  letterheadPreview: string | null;
  margins: { top: number; bottom: number };
  cabinetType: 'PRIVE' | 'CLINIQUE';
  specialtyStrings: { fr: string; ar: string };
  contactString: string;
  qrConfig: { enabled: boolean; type: string; label: string; color: string | null; style: string };
  headerScale?: number;
  customColors?: { primary: string; secondary: string; accent: string };
}

export const LiveDocumentStudio: React.FC<LiveDocumentStudioProps> = React.memo(({
  identity,
  selectedIdentity,
  selectedTemplate,
  selectedFont,
  headerOption,
  logoPreview,
  letterheadPreview,
  margins,
  cabinetType,
  specialtyStrings,
  contactString,
  qrConfig,
  headerScale = 1.0,
  customColors
}) => {
  const activeIdentity = BRAND_IDENTITIES.find(i => i.id === selectedIdentity) || BRAND_IDENTITIES[0];
  const brandColor = customColors?.primary || activeIdentity.primary;
  const secondaryColor = customColors?.secondary || activeIdentity.secondary;
  const accentColor = customColors?.accent || activeIdentity.accent;
  const fontClass = PREMIUM_FONTS.find(f => f.id === selectedFont)?.class || 'font-sans';

  return (
    <div className="w-full bg-slate-100 rounded-[2.5rem] p-8 border border-slate-200/40 shadow-inner flex justify-center">
      <div className={cn(
        "w-full max-w-[360px] bg-white shadow-2xl rounded-sm overflow-hidden flex flex-col aspect-[1/1.414] border border-slate-100 relative transition-all duration-700",
        fontClass,
        selectedTemplate === 'minimal' && "max-w-[330px]"
      )}>
        {/* FILIGRANE DE FOND */}
        <div className="absolute inset-0 flex items-center justify-center opacity-[0.02] rotate-[-25deg] pointer-events-none">
          {logoPreview ? (
            <img src={logoPreview} className="w-[180px] grayscale" alt="" />
          ) : (
            <Sparkles size={200} style={{ color: secondaryColor }} />
          )}
        </div>

        {headerOption === 'letterhead' && letterheadPreview && (
          <div className="absolute inset-0 z-10 pointer-events-none overflow-hidden" style={{ paddingTop: `${margins.top * 10}px` }}>
            <img src={letterheadPreview} className="w-full object-contain opacity-50" alt="Header" />
          </div>
        )}

        {headerOption === 'auto' && (
          <div className={cn(
            "p-6 min-h-[140px] transition-all duration-700 relative z-20 overflow-hidden",
            selectedTemplate === 'classic' && "grid grid-cols-[1.5fr_1fr_1.5fr] items-center text-center px-4 border-b border-slate-50",
            selectedTemplate === 'elite' && "flex items-start gap-6 border-b border-slate-100",
            selectedTemplate === 'sidebar' && "flex flex-row-reverse justify-between items-start border-l-4 pr-6",
            selectedTemplate === 'royal' && "flex flex-col items-center text-center gap-4 py-8",
            selectedTemplate === 'prestige' && "flex flex-col items-center text-center pb-8 border-b-2 bg-slate-50/30",
            selectedTemplate === 'minimal' && "flex items-center justify-between py-6 px-8 border-none"
          )} style={selectedTemplate === 'sidebar' ? { borderLeftColor: brandColor } : {}}>
            
            {/* LOGIQUE SIDEBAR (MODERN SIDE) */}
            {selectedTemplate === 'sidebar' && (
              <>
                <div className="flex flex-col items-center gap-3">
                  {logoPreview ? (
                    <img src={logoPreview} className="w-14 h-14 object-contain shadow-sm rounded-xl p-1 bg-white" alt="Logo" />
                  ) : (
                    <div className="w-14 h-14 bg-slate-50 rounded-2xl flex items-center justify-center border border-slate-100"><ImageIcon className="text-slate-200" size={24} /></div>
                  )}
                </div>
                <div className="flex-1 space-y-2 pr-4">
                  <div>
                    <h4 className="font-black leading-none uppercase tracking-tighter" style={{ color: brandColor, fontSize: `${14 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                    {identity.nomPraticienAR && <h4 className="font-black font-arabic mt-1" style={{ color: brandColor, fontSize: `${16 * headerScale}px` }}>د. {identity.nomPraticienAR}</h4>}
                  </div>
                  <div className="space-y-1">
                    <p className="font-extrabold text-slate-500 uppercase tracking-widest" style={{ fontSize: `${8 * headerScale}px` }}>{specialtyStrings.fr || 'Chirurgien Dentiste'}</p>
                    {specialtyStrings.ar && <p className="font-bold text-slate-400 font-arabic" style={{ fontSize: `${9 * headerScale}px` }}>{specialtyStrings.ar}</p>}
                  </div>
                </div>
              </>
            )}

            {/* LOGIQUE ROYAL CENTERED */}
            {selectedTemplate === 'royal' && (
              <div className="flex flex-col items-center w-full space-y-4">
                {logoPreview ? (
                  <img src={logoPreview} className="w-20 h-20 object-contain drop-shadow-xl" alt="Logo" />
                ) : (
                  <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center border-2 border-double shadow-sm transition-all" style={{ borderColor: brandColor }}><Sparkles style={{ color: brandColor }} size={32} /></div>
                )}
                <div className="flex items-center gap-6 w-full px-4">
                   <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent to-slate-200" />
                   <div className="text-center">
                      <h4 className="font-black uppercase tracking-[0.2em] leading-none" style={{ color: brandColor, fontSize: `${15 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                      {identity.nomPraticienAR && <h4 className="font-black font-arabic mt-2" style={{ color: brandColor, fontSize: `${17 * headerScale}px` }}>د. {identity.nomPraticienAR}</h4>}
                   </div>
                   <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent to-slate-200" />
                </div>
                <p className="font-black text-slate-400 uppercase tracking-[0.4em]" style={{ fontSize: `${8 * headerScale}px` }}>{specialtyStrings.fr || 'EXCELLENCE & SOINS DENTAIRES'}</p>
              </div>
            )}

            {/* LOGIQUE CLASSIQUE */}
            {selectedTemplate === 'classic' && (
              <>
                <div className="text-left pr-2">
                  <h4 className="font-black uppercase tracking-tight leading-none" style={{ color: brandColor, fontSize: `${11 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM'}</h4>
                  <p className="font-extrabold text-slate-500 uppercase mt-1" style={{ color: secondaryColor, fontSize: `${7 * headerScale}px` }}>Dentiste</p>
                  <div className="h-[1px] w-4 my-2" style={{ backgroundColor: accentColor }} />
                  <p className="text-slate-400 font-medium leading-tight line-clamp-2" style={{ fontSize: `${6 * headerScale}px` }}>{specialtyStrings.fr || 'Spécialités'}</p>
                </div>

                <div className="flex flex-col items-center">
                  {logoPreview ? (
                    <img src={logoPreview} className="w-12 h-12 object-contain" alt="Logo" />
                  ) : (
                    <div className="w-12 h-12 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-center"><ImageIcon className="text-slate-200" size={20} /></div>
                  )}
                  <p className="text-[5px] font-black uppercase tracking-[0.2em] text-slate-300 mt-2">
                    {cabinetType === 'CLINIQUE' ? 'Centre Médical' : 'Cabinet Dentaire'}
                  </p>
                </div>

                <div className="text-right pl-2" dir="rtl">
                  <h4 className="font-black tracking-tight font-arabic leading-none" style={{ color: brandColor, fontSize: `${12 * headerScale}px` }}>د. {identity.nomPraticienAR || 'الاسم'}</h4>
                  <p className="font-extrabold text-slate-500 mt-1" style={{ color: secondaryColor, fontSize: `${8 * headerScale}px` }}>طبيب أسنان</p>
                  <div className="h-[1px] w-4 my-2 mr-0 ml-auto" style={{ backgroundColor: accentColor }} />
                  <p className="text-slate-400 font-arabic leading-tight line-clamp-2" style={{ fontSize: `${7 * headerScale}px` }}>{specialtyStrings.ar || 'التخصصات'}</p>
                </div>
              </>
            )}

            {/* LOGIQUE MODERN (ELITE, PRESTIGE, MINIMAL) */}
            {(selectedTemplate !== 'classic' && selectedTemplate !== 'sidebar' && selectedTemplate !== 'royal') && (
              <div className={cn(
                "flex-1 flex items-center transition-all duration-700",
                selectedTemplate === 'prestige' ? "flex-col gap-4" : "gap-6",
                selectedTemplate === 'minimal' && "justify-between w-full"
              )}>
                {selectedTemplate === 'minimal' ? (
                  <>
                    <div className="space-y-1 border-l-2 pl-4" style={{ borderLeftColor: brandColor }}>
                      <h4 className="font-black uppercase tracking-tight" style={{ color: brandColor, fontSize: `${13 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM'}</h4>
                      <p className="font-bold text-slate-400 uppercase tracking-widest" style={{ fontSize: `${8 * headerScale}px` }}>{specialtyStrings.fr || 'Chirurgien Dentiste'}</p>
                    </div>
                    {logoPreview && <img src={logoPreview} className="w-10 h-10 object-contain grayscale opacity-30" alt="" />}
                  </>
                ) : (
                  <>
                    <div className={cn(
                      "w-1 h-12 rounded-full transition-all", 
                      selectedTemplate === 'prestige' && "h-1 w-16"
                    )} style={{ backgroundColor: brandColor }} />
                    <div className={cn(selectedTemplate === 'prestige' && "text-center")}>
                      <h4 className="font-black uppercase tracking-tight leading-none" style={{ color: brandColor, fontSize: `${14 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                      {identity.nomPraticienAR && <h4 className="font-black font-arabic mt-2" style={{ color: brandColor, fontSize: `${16 * headerScale}px` }}>د. {identity.nomPraticienAR}</h4>}
                      <p className="font-bold text-slate-500 uppercase mt-3 tracking-[0.1em]" style={{ fontSize: `${8 * headerScale}px` }}>{specialtyStrings.fr || 'Chirurgien Dentiste'}</p>
                      {specialtyStrings.ar && <p className="font-bold text-slate-400 font-arabic mt-1" style={{ fontSize: `${10 * headerScale}px` }}>{specialtyStrings.ar}</p>}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        <div className="flex-1 p-8 relative flex flex-col z-10">
          <div className="flex-1 flex items-center justify-center">
             <div className="px-6 py-3 border-2 border-dashed border-slate-100 rounded-2xl animate-pulse">
                <p className="text-[8px] font-black uppercase tracking-[0.5em] text-slate-200 text-center">Contenu de l'ordonnance<br/>Simulé</p>
             </div>
          </div>

          {/* PIED DE PAGE ANCRÉ */}
          <div className="absolute bottom-8 left-0 right-0 px-8 flex flex-col items-center text-center transition-all duration-700">
            <div className="w-full h-[1px] bg-slate-100 mb-6 flex items-center justify-center overflow-hidden">
               <div className="w-16 h-1 rounded-full animate-bounce" style={{ backgroundColor: brandColor }} />
            </div>
            
            <div className="space-y-2 max-w-[300px]">
              <p className="text-[9px] font-bold text-slate-600 leading-relaxed uppercase tracking-tight">
                {identity.adresse || 'ADRESSE DU CABINET DENTAIRE'}
              </p>
              <div className="flex items-center justify-center gap-4">
                <div className="h-[1px] w-4 bg-slate-100" />
                <p className="text-[9px] font-black uppercase tracking-[0.15em]" style={{ color: brandColor }}>
                  {contactString || 'CONTACT : 05 XX XX XX XX'}
                </p>
                <div className="h-[1px] w-4 bg-slate-100" />
              </div>
            </div>

            {(identity.ice || identity.if || identity.inpe) && (
              <div className="mt-4 flex items-center justify-center gap-4 text-[7px] font-black text-slate-400 tracking-tighter bg-slate-50/50 px-4 py-1 rounded-full border border-slate-100/50">
                {identity.ice && <span>ICE: {identity.ice}</span>}
                {identity.if && <span>IF: {identity.if}</span>}
                {identity.inpe && <span>INPE: {identity.inpe}</span>}
              </div>
            )}

            <p className="mt-4 text-[6px] font-black text-slate-300 tracking-[0.4em] uppercase">Digital Crown Elite Studio v4.2</p>
          </div>

          {/* QR CODE PREVIEW */}
          {qrConfig.enabled && (
            <div className="absolute bottom-[2.8cm] right-8 flex flex-col items-end gap-2 group transition-all">
              <div 
                className="w-14 h-14 rounded-2xl border-2 border-white shadow-2xl flex items-center justify-center p-1.5 relative overflow-hidden transition-all duration-500 group-hover:rotate-6"
                style={{ backgroundColor: qrConfig.color || brandColor }}
              >
                <div className="grid grid-cols-5 gap-1 w-full h-full opacity-30">
                  {[...Array(25)].map((_, i) => (
                    <div 
                      key={i} 
                      className={cn(
                        "bg-white transition-all duration-500",
                        qrConfig.style === 'classic' ? "rounded-none" :
                        qrConfig.style === 'dots' ? "rounded-full" :
                        qrConfig.style === 'rounded' ? "rounded-sm" :
                        "rounded-md"
                      )} 
                    />
                  ))}
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                   <div className="w-5 h-5 bg-white rounded-lg flex items-center justify-center shadow-sm">
                      {logoPreview ? <img src={logoPreview} className="w-full h-full object-contain p-0.5" alt="" /> : <QrCode style={{ color: qrConfig.color || brandColor }} size={12} />}
                   </div>
                </div>
              </div>
              {qrConfig.label && (
                <p className="text-[6px] font-black uppercase tracking-tighter w-20 text-right leading-tight" style={{ color: qrConfig.color || brandColor }}>
                  {qrConfig.label}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

LiveDocumentStudio.displayName = 'LiveDocumentStudio';

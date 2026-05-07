import React from 'react';
import { Sparkles, Image as ImageIcon } from 'lucide-react';
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
  qrConfig: { enabled: boolean; type: string; label: string; color: string | null };
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
  qrConfig
}) => {
  const activeIdentity = BRAND_IDENTITIES.find(i => i.id === selectedIdentity) || BRAND_IDENTITIES[0];
  const brandColor = activeIdentity.primary;
  const secondaryColor = activeIdentity.secondary;
  const accentColor = activeIdentity.accent;
  const fontClass = PREMIUM_FONTS.find(f => f.id === selectedFont)?.class || 'font-sans';

  return (
    <div className="w-full bg-slate-100 rounded-[2.5rem] p-8 border border-slate-200/40 shadow-inner flex justify-center sticky top-28">
      <div className={cn(
        "w-full max-w-[360px] bg-white shadow-2xl rounded-sm overflow-hidden flex flex-col aspect-[1/1.414] border border-slate-100 relative transition-all duration-500",
        fontClass,
        selectedTemplate === 'minimal' && "max-w-[330px]"
      )}>
        {/* FILIGRANE DE FOND */}
        <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] rotate-[-25deg] pointer-events-none">
          {logoPreview ? (
            <img src={logoPreview} className="w-[200px] grayscale" alt="" />
          ) : (
            <Sparkles size={220} style={{ color: secondaryColor }} />
          )}
        </div>

        {headerOption === 'letterhead' && letterheadPreview && (
          <div className="absolute inset-0 z-10 pointer-events-none overflow-hidden" style={{ paddingTop: `${margins.top * 12}px` }}>
            <img src={letterheadPreview} className="w-full object-contain" alt="Header" />
          </div>
        )}

            {headerOption === 'auto' && (
              <div className={cn(
                "p-6 min-h-[140px] transition-all duration-500 relative z-20",
                selectedTemplate === 'classic' && "grid grid-cols-[1.5fr_1fr_1.5fr] items-center text-center px-4",
                selectedTemplate === 'elite' && "flex items-start gap-8",
                selectedTemplate === 'sidebar' && "flex flex-col gap-6",
                selectedTemplate === 'royal' && "flex flex-col items-center text-center",
                selectedTemplate === 'prestige' && "flex flex-col items-center text-center pb-8 border-b-2 border-slate-100",
                selectedTemplate === 'minimal' && "flex items-center justify-between py-6 border-b border-slate-50"
              )}>
                {/* LOGIQUE SIDEBAR */}
                {selectedTemplate === 'sidebar' && (
                  <div className="flex gap-6 w-full">
                    <div className="flex flex-col items-center gap-2 pr-6 border-r border-slate-100">
                      {logoPreview ? (
                        <img src={logoPreview} className="w-12 h-12 object-contain" alt="Logo" />
                      ) : (
                        <div className="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center"><ImageIcon className="text-slate-200" size={20} /></div>
                      )}
                      <div className="h-full w-[1px] bg-gradient-to-b from-slate-100 to-transparent flex-1" />
                    </div>
                    <div className="flex-1 space-y-3">
                      <div>
                        <h4 className="font-black text-[12px] uppercase tracking-tight" style={{ color: brandColor }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                        {identity.nomPraticienAR && <h4 className="font-black text-[13px] font-arabic mt-1" style={{ color: brandColor }}>د. {identity.nomPraticienAR}</h4>}
                      </div>
                      <div className="space-y-1">
                        <p className="text-[8px] font-extrabold text-slate-500 uppercase tracking-widest">{specialtyStrings.fr || 'Chirurgien Dentiste'}</p>
                        {specialtyStrings.ar && <p className="text-[8px] font-bold text-slate-400 font-arabic">{specialtyStrings.ar}</p>}
                      </div>
                    </div>
                  </div>
                )}

                {/* LOGIQUE ROYAL CENTERED */}
                {selectedTemplate === 'royal' && (
                  <div className="flex flex-col items-center w-full space-y-4">
                    {logoPreview ? (
                      <img src={logoPreview} className="w-16 h-16 object-contain" alt="Logo" />
                    ) : (
                      <div className="w-14 h-14 bg-slate-50 rounded-full flex items-center justify-center border-2 border-dashed border-slate-200"><Sparkles className="text-slate-200" size={24} /></div>
                    )}
                    <div className="flex items-center gap-6 w-full">
                       <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent to-slate-200" />
                       <div className="text-center">
                          <h4 className="font-black text-[13px] uppercase tracking-[0.2em]" style={{ color: brandColor }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                          {identity.nomPraticienAR && <h4 className="font-black text-[14px] font-arabic mt-1" style={{ color: brandColor }}>د. {identity.nomPraticienAR}</h4>}
                       </div>
                       <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent to-slate-200" />
                    </div>
                    <p className="text-[8px] font-black text-slate-400 uppercase tracking-[0.3em]">{specialtyStrings.fr || 'EXCELLENCE & SOINS DENTAIRES'}</p>
                  </div>
                )}

                {/* LOGIQUE CLASSIQUE */}
                {selectedTemplate === 'classic' && (
                  <>
                    <div className="text-left border-r border-slate-100 pr-4">
                      <h4 className="font-black text-[10px] uppercase tracking-tight" style={{ color: brandColor }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                      <p className="text-[8px] font-extrabold text-slate-500 uppercase mt-0.5" style={{ color: secondaryColor }}>Chirurgien Dentiste</p>
                      <div className="h-[1px] w-4 bg-slate-200 my-2" style={{ backgroundColor: accentColor }} />
                      <p className="text-[7px] text-slate-400 font-medium leading-tight line-clamp-2">{specialtyStrings.fr || 'Spécialités cliniques'}</p>
                    </div>

                    <div className={cn("flex flex-col items-center px-2")}>
                      {logoPreview ? (
                        <div className="p-2 bg-white rounded-2xl shadow-sm border border-slate-50 mb-2">
                          <img src={logoPreview} className="w-14 h-14 object-contain" alt="Logo" />
                        </div>
                      ) : (
                        <div className="w-14 h-14 bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl flex items-center justify-center mb-2">
                          <ImageIcon className="text-slate-300" size={24} />
                        </div>
                      )}
                      <div className="flex flex-col items-center">
                        <p className="text-[6px] font-black uppercase tracking-[0.3em] text-slate-400">{cabinetType === 'CLINIQUE' ? 'Centre Médical' : 'Cabinet Dentaire'}</p>
                      </div>
                    </div>

                    <div className="text-right border-l border-slate-100 pl-4" dir="rtl">
                      <h4 className="font-black text-[11px] tracking-tight font-arabic" style={{ color: brandColor }}>د. {identity.nomPraticienAR || 'الاسم الكامل'}</h4>
                      <p className="text-[8px] font-extrabold text-slate-500 mt-0.5" style={{ color: secondaryColor }}>طبيب jراخ للأسنان</p>
                      <div className="h-[1px] w-4 bg-slate-200 my-2 mr-0 ml-auto" style={{ backgroundColor: accentColor }} />
                      <p className="text-[7px] text-slate-400 font-arabic leading-tight line-clamp-2">{specialtyStrings.ar || 'التخصصات الطبية'}</p>
                    </div>
                  </>
                )}

                {(selectedTemplate !== 'classic' && selectedTemplate !== 'sidebar' && selectedTemplate !== 'royal') && (
                  <div className={cn(
                    "flex-1",
                    selectedTemplate === 'prestige' && "mt-4 flex flex-col items-center",
                    selectedTemplate === 'elite' && "order-1 text-left"
                  )}>
                    <div className={cn(
                      "flex items-center gap-3 mb-2",
                      selectedTemplate === 'prestige' && "flex-col gap-1"
                    )}>
                       <div className={cn(
                         "w-1 h-12 rounded-full", 
                         selectedTemplate === 'prestige' && "h-1 w-16 mb-3"
                       )} style={{ backgroundColor: brandColor }} />
                       <div className={cn(selectedTemplate === 'prestige' && "text-center")}>
                          <h4 className="font-black uppercase tracking-tight leading-none text-[14px]" style={{ color: brandColor }}>
                            {identity.nomPraticien || 'DR. NOM DE FAMILLE'}
                          </h4>
                          {identity.nomPraticienAR && (
                            <h4 className="font-black text-[15px] mt-1.5 font-arabic leading-none" style={{ color: brandColor }}>
                              د. {identity.nomPraticienAR}
                            </h4>
                          )}
                          <p className="text-[9px] font-bold text-slate-500 uppercase mt-3 tracking-[0.1em]">
                            {specialtyStrings.fr || 'Chirurgien Dentiste'}
                          </p>
                          {specialtyStrings.ar && (
                            <p className="text-[10px] font-bold text-slate-400 font-arabic mt-1">
                              {specialtyStrings.ar}
                            </p>
                          )}
                       </div>
                    </div>
                  </div>
                )}
              </div>
            )}

        <div className="flex-1 p-8 relative flex flex-col z-10">
          <div className="flex-1 flex items-center justify-center">
             <div className="px-6 py-3 border-2 border-dashed border-slate-100 rounded-2xl">
                <p className="text-[8px] font-black uppercase tracking-[0.5em] text-slate-200">Zone de Contenu Clinique</p>
             </div>
          </div>

          {/* PIED DE PAGE ANCRÉ (CORRECTION ELITE) */}
          <div className="absolute bottom-8 left-0 right-0 px-8 flex flex-col items-center text-center">
            {/* LIGNE DE SÉPARATION ELITE */}
            <div className="w-full h-[1px] bg-slate-100 mb-6 flex items-center justify-center">
               <div className="w-12 h-1 rounded-full" style={{ backgroundColor: brandColor }} />
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

            <div className="mt-6 flex items-center justify-center gap-3 w-full opacity-30">
               <div className="h-[0.5px] flex-1 bg-slate-300" />
               <Sparkles size={12} className="text-slate-400" />
               <div className="h-[0.5px] flex-1 bg-slate-300" />
            </div>
            <p className="mt-2 text-[6px] font-black text-slate-300 tracking-[0.4em] uppercase">Digital Crown Elite Studio v4.2</p>
          </div>

          {/* QR CODE PREVIEW (WYSIWYG) */}
          {qrConfig.enabled && (
            <div className="absolute bottom-[2.6cm] right-8 flex flex-col items-end gap-1 group transition-all hover:scale-110">
              <div 
                className="w-12 h-12 rounded-lg border-2 border-white shadow-xl flex items-center justify-center p-1.5 relative overflow-hidden"
                style={{ backgroundColor: qrConfig.color || brandColor }}
              >
                {/* STYLIZED QR GRID */}
                <div className="grid grid-cols-3 gap-1 w-full h-full opacity-40">
                  {[...Array(9)].map((_, i) => (
                    <div key={i} className="bg-white rounded-[1px]" />
                  ))}
                </div>
                {/* ELITE SEAL (LOGO AU CENTRE) */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-4 h-4 bg-white rounded-sm flex items-center justify-center shadow-sm overflow-hidden">
                    {logoPreview ? (
                      <img src={logoPreview} className="w-full h-full object-contain" alt="QR Logo" />
                    ) : (
                      <Sparkles size={10} style={{ color: qrConfig.color || brandColor }} />
                    )}
                  </div>
                </div>
              </div>
              {qrConfig.label && (
                <p className="text-[5px] font-black uppercase tracking-tighter w-16 text-right leading-tight" style={{ color: qrConfig.color || brandColor }}>
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

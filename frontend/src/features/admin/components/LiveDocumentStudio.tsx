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
  contactString
}) => {
  const activeIdentity = BRAND_IDENTITIES.find(i => i.id === selectedIdentity) || BRAND_IDENTITIES[0];
  const brandColor = activeIdentity.primary;
  const secondaryColor = activeIdentity.secondary;
  const accentColor = activeIdentity.accent;
  const fontClass = PREMIUM_FONTS.find(f => f.id === selectedFont)?.class || 'font-sans';

  return (
    <div className="w-full bg-slate-100 rounded-[2.5rem] p-8 border border-slate-200/40 shadow-inner flex justify-center sticky top-28">
      <div className={cn(
        "w-full max-w-[360px] bg-white shadow-2xl rounded-sm overflow-hidden flex flex-col min-h-[500px] border border-slate-100 relative transition-all duration-300",
        fontClass,
        selectedTemplate === 'minimal' && "max-w-[330px]"
      )}>
        {headerOption === 'letterhead' && letterheadPreview && (
          <div className="absolute inset-0 z-10 pointer-events-none overflow-hidden" style={{ paddingTop: `${margins.top * 12}px` }}>
            <img src={letterheadPreview} className="w-full object-contain" alt="Header" />
          </div>
        )}

        {headerOption === 'auto' && (
          <div className={cn(
            "p-6 min-h-[130px] transition-all duration-500 relative",
            selectedTemplate === 'classic' && "grid grid-cols-[1.5fr_1fr_1.5fr] items-center text-center px-4",
            selectedTemplate === 'elite' && "flex items-start gap-8",
            selectedTemplate === 'prestige' && "flex flex-col items-center text-center pb-8 border-b-2 border-slate-100",
            selectedTemplate === 'minimal' && "flex items-center justify-between py-6 border-b border-slate-50"
          )}>
            {/* Colonne FR */}
            {selectedTemplate === 'classic' && (
              <div className="text-left border-r border-slate-100 pr-4">
                <h4 className="font-black text-[10px] uppercase tracking-tight" style={{ color: brandColor }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                <p className="text-[8px] font-extrabold text-slate-500 uppercase mt-0.5" style={{ color: secondaryColor }}>Chirurgien Dentiste</p>
                <p className="text-[7px] text-slate-400 mt-2 font-medium leading-tight line-clamp-2">{specialtyStrings.fr || 'Spécialités cliniques'}</p>
              </div>
            )}

            {/* Logo / Centre */}
            <div className={cn("flex flex-col items-center px-2", selectedTemplate === 'elite' && "order-2")}>
              {logoPreview ? (
                <img src={logoPreview} className="w-16 h-16 object-contain mb-2" alt="Logo" />
              ) : (
                <div className="w-14 h-14 bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl flex items-center justify-center mb-2">
                  <ImageIcon className="text-slate-300" size={24} />
                </div>
              )}
              {selectedTemplate === 'classic' && (
                <div className="flex flex-col items-center">
                  <div className="w-8 h-0.5 rounded-full mb-1" style={{ backgroundColor: accentColor }} />
                  <p className="text-[6px] font-black uppercase tracking-[0.2em] text-slate-400">{cabinetType === 'CLINIQUE' ? 'Centre Médical' : 'Cabinet Dentaire'}</p>
                </div>
              )}
            </div>

            {/* Colonne AR */}
            {selectedTemplate === 'classic' && (
              <div className="text-right border-l border-slate-100 pl-4" dir="rtl">
                <h4 className="font-black text-[11px] tracking-tight" style={{ color: brandColor }}>د. {identity.nomPraticienAR || 'الاسم الكامل'}</h4>
                <p className="text-[8px] font-extrabold text-slate-500 mt-0.5" style={{ color: secondaryColor }}>طبيب جراح للأسنان</p>
                <p className="text-[7px] text-slate-400 mt-2 font-arabic leading-tight line-clamp-2">{specialtyStrings.ar || 'التخصصات الطبية'}</p>
              </div>
            )}

            {(selectedTemplate !== 'classic') && (
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
                     "w-1 h-10 rounded-full", 
                     selectedTemplate === 'prestige' && "h-1 w-12 mb-2"
                   )} style={{ backgroundColor: brandColor }} />
                   <div className={cn(selectedTemplate === 'prestige' && "text-center")}>
                      <h4 className="font-black uppercase tracking-tight leading-none text-[13px]" style={{ color: brandColor }}>
                        {identity.nomPraticien || 'DR. NOM DE FAMILLE'}
                      </h4>
                      {identity.nomPraticienAR && (
                        <h4 className="font-black text-[14px] mt-1 font-arabic leading-none" style={{ color: brandColor }}>
                          د. {identity.nomPraticienAR}
                        </h4>
                      )}
                      <p className="text-[9px] font-bold text-slate-500 uppercase mt-2 tracking-wider">
                        {specialtyStrings.fr || 'Chirurgien Dentiste'}
                      </p>
                      {specialtyStrings.ar && (
                        <p className="text-[9px] font-bold text-slate-400 font-arabic mt-0.5">
                          {specialtyStrings.ar}
                        </p>
                      )}
                   </div>
                </div>
                {selectedTemplate !== 'prestige' && (
                  <p className="text-[7px] text-slate-400 mt-3 font-medium italic pl-4 border-l border-slate-100 opacity-70">
                    Expertise & Soins d'Excellence
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        <div className="flex-1 p-8 relative flex flex-col">
          <div className="absolute inset-0 flex items-center justify-center opacity-[0.04] rotate-[-25deg] pointer-events-none">
            {logoPreview ? (
              <img src={logoPreview} className="w-[180px] grayscale" alt="" />
            ) : (
              <Sparkles size={180} style={{ color: secondaryColor }} />
            )}
          </div>

          {/* 
          <div className="flex justify-between items-start mb-10">
             <div className="font-bold text-[9px] text-slate-700">Patient: <span className="text-slate-900 px-2 py-0.5 bg-slate-50 rounded">El Khallouki Nada, 10 ans</span></div>
             <div className="text-[8px] text-slate-400 font-bold bg-slate-50 px-2 py-1 rounded">Casablanca, le 18/04/2026</div>
          </div>

          <div className="mt-4 mb-12 text-center">
            <h2 className="text-sm font-black tracking-[0.3em] uppercase py-2 px-6 border-y-2 inline-block" style={{ color: brandColor, borderColor: accentColor }}>Ordonnance</h2>
          </div>

          <div className="space-y-8 flex-1 text-[10px]">
             <div className="space-y-6 mt-4">
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-lg flex items-center justify-center text-white font-black text-[10px] shadow-sm" style={{ backgroundColor: brandColor }}>1</div>
                  <div className="flex-1">
                    <p className="font-black uppercase tracking-wide mb-1" style={{ color: brandColor }}>ZAMOX 500 mg (Sachets)</p>
                    <div className="h-[1px] w-full bg-slate-100 mb-2" />
                    <p className="text-[11px] font-bold italic" style={{ color: secondaryColor }}>- 2 fois par jour, après les repas, pendant 6 jours.</p>
                  </div>
                </div>
             </div>
          </div>
          */}
          <div className="flex-1 flex items-center justify-center">
             <p className="text-[9px] font-black uppercase tracking-[0.4em] text-slate-200">[ Corps du document ]</p>
          </div>

          <div className="mt-auto pt-8 flex flex-col items-center text-center">
            <div className="w-24 h-0.5 rounded-full mb-6 opacity-30" style={{ backgroundColor: brandColor }} />
            
            <div className="space-y-1.5 max-w-[280px]">
              <p className="text-[9px] font-black text-slate-800 leading-tight">
                {identity.adresse || 'ADRESSE DU CABINET DENTAIRE'}
              </p>
              <div className="flex items-center justify-center gap-4">
                <p className="text-[8px] font-black uppercase tracking-widest" style={{ color: brandColor }}>
                  {contactString || 'CONTACT : 05 XX XX XX XX'}
                </p>
              </div>
            </div>

            {(identity.ice || identity.if || identity.inpe) && (
              <div className="mt-3 flex items-center justify-center gap-3 text-[6px] font-bold text-slate-400">
                {identity.ice && <span>ICE: {identity.ice}</span>}
                {identity.ice && (identity.if || identity.inpe) && <span>|</span>}
                {identity.if && <span>IF: {identity.if}</span>}
                {identity.if && identity.inpe && <span>|</span>}
                {identity.inpe && <span>INPE: {identity.inpe}</span>}
              </div>
            )}

            <div className="mt-6 flex items-center justify-center gap-3 w-full opacity-20">
               <div className="h-[1px] flex-1 bg-slate-300" />
               <Sparkles size={10} className="text-slate-400" />
               <div className="h-[1px] flex-1 bg-slate-300" />
            </div>
            <p className="mt-2 text-[5px] font-bold text-slate-300 tracking-[0.3em] uppercase">Digital Crown Elite System</p>
          </div>
        </div>
      </div>
    </div>
  );
});

LiveDocumentStudio.displayName = 'LiveDocumentStudio';

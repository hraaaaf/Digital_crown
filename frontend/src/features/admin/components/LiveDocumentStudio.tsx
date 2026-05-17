import React from 'react';
import { Sparkles, Image as ImageIcon, QrCode } from 'lucide-react';
import { cn } from '../../../utils/cn';
import {
  BRAND_IDENTITIES,
  PREMIUM_FONTS
} from '../constants';
import { API_BASE } from '../../../services/api';
import { useSettingsStore } from '../Settings/hooks/useSettingsStore';


// 1cm in pixels for the simulated A4 (480px wide → 210mm → 1cm ≈ 22.86px)
const CM_TO_PX = 22.86;

export interface LiveDocumentStudioProps {
  identity?: { nomCabinet: string; nomPraticien: string; nomPraticienAR: string; adresse: string; ice: string; if: string; inpe: string };
  selectedIdentity?: string;
  selectedTemplate?: string;
  selectedFont?: string;
  headerOption?: string;
  logoPreview?: string | null;
  letterheadPreview?: string | null;
  margins?: { top: number; bottom: number };
  cabinetType?: 'PRIVE' | 'CLINIQUE';
  specialtyStrings?: { fr: string; ar: string };
  contactString?: string;
  qrConfig?: { enabled: boolean; type: string; label: string; color: string | null; style: string; value?: string };
  headerScale?: number;
  customColors?: { primary: string; secondary: string; accent: string };
}

export const LiveDocumentStudio: React.FC<LiveDocumentStudioProps> = (props) => {
  const { profile } = useSettingsStore();
  
  // Directly pull state from props or fallback to profile
  const selectedTemplate = props.selectedTemplate || profile.selected_template || 'classic';
  const selectedFont = props.selectedFont || profile.font_fr || 'inter';
  const headerOption = props.headerOption || (profile.letterhead_path ? 'letterhead' : 'auto');
  const headerScale = props.headerScale ?? profile.header_scale ?? 1.1;
  const logoPreview = props.logoPreview !== undefined ? props.logoPreview : (profile.logo_path || null);
  const letterheadPreview = props.letterheadPreview !== undefined ? props.letterheadPreview : (profile.letterhead_path || null);
  const margins = props.margins || { top: profile.margin_top || 3.6, bottom: profile.margin_bottom || 3.2 };
  
  const identity = props.identity || {
    nomCabinet: profile.nom || '',
    nomPraticien: profile.header_lines_fr?.[0] || 'DR. NOM DE FAMILLE',
    nomPraticienAR: profile.nom_praticien_ar || '',
    adresse: profile.adresse || '',
    telephone: profile.telephone || '',
    inpe: profile.inpe || ''
  };

  const specialtyStrings = props.specialtyStrings || {
    fr: profile.header_lines_fr?.[2] || 'Chirurgien Dentiste',
    ar: profile.header_lines_ar?.[1] || 'طبيب جراح للأسنان'
  };

  const qrConfig = props.qrConfig || {
    enabled: profile.qr_code_enabled || false,
    type: profile.qr_code_type || 'VCARD',
    label: profile.qr_code_label || '',
    value: profile.qr_code_value || '',
    style: profile.qr_code_style || 'dots',
    color: profile.qr_code_color || null,
  };

  const customColors = props.customColors || {
    primary: profile.primary_color || undefined,
    secondary: profile.secondary_color || undefined,
    accent: profile.accent_color || undefined
  };

  const contactString = props.contactString || profile.telephone || '';
  // Consistent A4 aspect ratio and scaling
  const marginTopPx = Math.round(margins.top * CM_TO_PX);
  const marginBottomPx = Math.round(margins.bottom * CM_TO_PX);

  // The header scale impacts the base height and internal spacings
  const headerHeight = 130 * headerScale;

  const activeIdentity = BRAND_IDENTITIES.find(i => i.id === profile.selected_theme) || BRAND_IDENTITIES[0];
  const brandColor = customColors.primary || activeIdentity.primary;
  const secondaryColor = customColors.secondary || activeIdentity.secondary;
  const fontClass = PREMIUM_FONTS.find(f => f.id === selectedFont)?.class || 'font-sans';
  
  // Footer and QR absolute positions track the bottom margin
  const safeBottomMargin = Math.max(marginBottomPx, 40);
  const topMarginOffset = Math.max(marginTopPx, 40);

  const getQrCell = (index: number): boolean => {
    const seedStr = qrConfig.type + (qrConfig.label || '') + (qrConfig.style || '') + (qrConfig.value || '');
    const base = seedStr.split('').reduce((acc, c, i) => (acc + c.charCodeAt(0) * (i + 1)) & 0xffff, 0);
    return ((base ^ (index * 0x9e37)) & 0xff) > 96;
  };

  const getImageUrl = (path: string | null) => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    const cleanPath = path.replace(/^\/+/, '');
    if (cleanPath.startsWith('api/static/') || cleanPath.startsWith('static/uploads/')) {
      return `${API_BASE}/${cleanPath}`;
    }
    return `${API_BASE}/static/uploads/${cleanPath}`;
  };

  const resolvedLogo = getImageUrl(logoPreview);
  const resolvedLetterhead = getImageUrl(letterheadPreview);

  return (
    <div className="w-full bg-[#F8FAFC] rounded-[3.5rem] p-12 border border-slate-200 shadow-xl flex justify-center relative overflow-hidden group">
      {/* Studio Background - Medical/Clean Style */}
      <div className="absolute inset-0 opacity-40 pointer-events-none" style={{ backgroundImage: 'radial-gradient(#CBD5E1 0.5px, transparent 0.5px)', backgroundSize: '24px 24px' }} />
      <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-primary/5 via-transparent to-emerald-500/5 pointer-events-none" />

      <div className={cn(
        "w-full max-w-[480px] bg-white shadow-[0_30px_80px_rgba(0,0,0,0.12)] rounded-sm overflow-hidden flex flex-col aspect-[1/1.414] border border-slate-100 relative transition-all duration-700",
        fontClass,
        selectedTemplate === 'minimal' && "max-w-[440px]"
      )}>
        {/* LETTERHEAD OVERLAY (if active) */}
        {headerOption === 'letterhead' && resolvedLetterhead && (
          <div className="absolute inset-0 z-0 pointer-events-none">
            <img src={resolvedLetterhead} className="w-full h-full object-cover" alt="Letterhead" />
          </div>
        )}

        {/* HEADER BLOCK (if auto) */}
        {headerOption === 'auto' && (
          <div className={cn(
            "relative z-20 flex transition-all duration-500 overflow-hidden shrink-0",
            selectedTemplate === 'classic' && "grid grid-cols-[1.5fr_1fr_1.5fr] items-center text-center px-6 border-b border-slate-50",
            selectedTemplate === 'elite' && "items-start gap-6 px-8 py-6 border-b border-slate-100",
            selectedTemplate === 'sidebar' && "flex-row-reverse justify-between items-start border-l-4 pr-6 py-6",
            selectedTemplate === 'royal' && "flex-col items-center text-center gap-4 py-8",
            selectedTemplate === 'prestige' && "flex-col items-center text-center pb-8 pt-6 border-b-2 bg-slate-50/20",
            selectedTemplate === 'minimal' && "items-center justify-between py-6 px-10 border-none"
          )} style={{ 
            height: `${headerHeight}px`,
            borderLeftColor: selectedTemplate === 'sidebar' ? brandColor : undefined,
            borderBottomColor: selectedTemplate === 'prestige' ? brandColor : undefined
          }}>

            {selectedTemplate === 'sidebar' && (
              <>
                <div className="flex flex-col items-center gap-3">
                  {resolvedLogo ? (
                    <img src={resolvedLogo} className="w-14 h-14 object-contain shadow-sm rounded-xl p-1 bg-white" alt="Logo" />
                  ) : (
                    <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center border border-slate-100"><ImageIcon className="text-slate-200" size={24} /></div>
                  )}
                </div>
                <div className="flex-1 space-y-2 pr-4">
                  <h4 className="font-black leading-none uppercase tracking-tighter" style={{ color: brandColor, fontSize: `${14 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                  {identity.nomPraticienAR && <h4 className="font-black font-arabic" style={{ color: brandColor, fontSize: `${16 * headerScale}px` }}>د. {identity.nomPraticienAR}</h4>}
                  <p className="font-extrabold uppercase tracking-widest opacity-70" style={{ fontSize: `${8 * headerScale}px`, color: secondaryColor }}>{specialtyStrings.fr || 'Chirurgien Dentiste'}</p>
                </div>
              </>
            )}

            {selectedTemplate === 'royal' && (
              <div className="flex flex-col items-center w-full gap-3">
                {resolvedLogo ? (
                  <img src={resolvedLogo} className="w-16 h-16 object-contain drop-shadow-lg" alt="Logo" />
                ) : (
                  <div className="w-14 h-14 bg-white rounded-full flex items-center justify-center border-2 border-double shadow-sm" style={{ borderColor: brandColor }}><Sparkles style={{ color: brandColor }} size={24} /></div>
                )}
                <div className="flex items-center gap-4 w-full">
                   <div className="h-[1px] flex-1" style={{ backgroundImage: `linear-gradient(to right, transparent, ${brandColor}40)` }} />
                   <div className="text-center">
                      <h4 className="font-black uppercase tracking-[0.1em] leading-none" style={{ color: brandColor, fontSize: `${15 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                      {identity.nomPraticienAR && <h4 className="font-black font-arabic mt-1" style={{ color: brandColor, fontSize: `${17 * headerScale}px` }}>د. {identity.nomPraticienAR}</h4>}
                   </div>
                   <div className="h-[1px] flex-1" style={{ backgroundImage: `linear-gradient(to left, transparent, ${brandColor}40)` }} />
                </div>
              </div>
            )}

            {selectedTemplate === 'classic' && (
              <>
                <div className="text-left space-y-1">
                  <h4 className="font-black uppercase tracking-tight leading-none" style={{ color: brandColor, fontSize: `${11 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM'}</h4>
                  <p className="font-extrabold uppercase" style={{ color: secondaryColor, fontSize: `${7 * headerScale}px` }}>Dentiste</p>
                  <p className="font-medium opacity-50 leading-tight" style={{ fontSize: `${6 * headerScale}px`, color: secondaryColor }}>{specialtyStrings.fr || 'Spécialités'}</p>
                </div>

                <div className="flex flex-col items-center">
                  {resolvedLogo ? (
                    <img src={resolvedLogo} className="w-12 h-12 object-contain" alt="Logo" />
                  ) : (
                    <div className="w-10 h-10 bg-white border border-slate-100 rounded-xl flex items-center justify-center"><ImageIcon className="text-slate-100" size={18} /></div>
                  )}
                </div>

                <div className="text-right" dir="rtl">
                  <h4 className="font-black tracking-tight font-arabic leading-none" style={{ color: brandColor, fontSize: `${12 * headerScale}px` }}>د. {identity.nomPraticienAR || 'الاسم'}</h4>
                  <p className="font-extrabold" style={{ color: secondaryColor, fontSize: `${8 * headerScale}px` }}>طبيب أسنان</p>
                  <p className="font-arabic opacity-50 leading-tight" style={{ fontSize: `${7 * headerScale}px`, color: secondaryColor }}>{specialtyStrings.ar || 'التخصصات'}</p>
                </div>
              </>
            )}

            {(selectedTemplate !== 'classic' && selectedTemplate !== 'sidebar' && selectedTemplate !== 'royal') && (
              <div className={cn(
                "flex-1 flex items-center gap-6",
                selectedTemplate === 'prestige' && "flex-col",
                selectedTemplate === 'minimal' && "justify-between w-full"
              )}>
                {resolvedLogo ? (
                  <img src={resolvedLogo} className={cn("object-contain", selectedTemplate === 'minimal' ? "w-10 h-10" : "w-14 h-14")} alt="Logo" />
                ) : (
                  <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center border border-slate-50 shadow-sm"><ImageIcon className="text-slate-200" size={20} /></div>
                )}
                
                <div className={cn(selectedTemplate === 'prestige' && "text-center", "space-y-1")}>
                  <h4 className="font-black uppercase tracking-tight leading-none" style={{ color: brandColor, fontSize: `${14 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                  {identity.nomPraticienAR && <h4 className="font-black font-arabic" style={{ color: brandColor, fontSize: `${16 * headerScale}px` }}>د. {identity.nomPraticienAR}</h4>}
                  <p className="font-bold uppercase tracking-widest opacity-60" style={{ fontSize: `${8 * headerScale}px`, color: secondaryColor }}>{specialtyStrings.fr || 'Chirurgien Dentiste'}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* MAIN BODY AREA (Fills the remaining A4 space) */}
        <div className="flex-1 relative flex flex-col z-10 overflow-hidden">
          
          {/* WATERMARK - Placed inside the content area for better alignment */}
          <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] rotate-[-25deg] pointer-events-none z-0">
            {resolvedLogo ? (
              <img src={resolvedLogo} className="w-[180px] grayscale brightness-110" alt="" />
            ) : (
              <Sparkles size={200} style={{ color: brandColor }} />
            )}
          </div>

          {/* REAL CONTENT CONTAINER */}
          <div 
            className="flex-1 relative flex flex-col z-10 group/doc"
            style={{ 
              paddingTop: headerOption === 'letterhead' ? `${marginTopPx}px` : `${topMarginOffset / 3}px`,
              paddingBottom: `${safeBottomMargin}px`,
              paddingLeft: 40,
              paddingRight: 40
            }}
          >
            {/* Margin Visualizer */}
            <div 
              className="absolute inset-0 pointer-events-none border-2 border-dashed opacity-0 group-hover/doc:opacity-20 transition-opacity z-50"
              style={{ 
                borderColor: brandColor,
                top: headerOption === 'letterhead' ? `${marginTopPx}px` : '0px',
                bottom: `${safeBottomMargin}px`,
                left: '40px',
                right: '40px'
              }}
            />

            {/* Simulated Medical Text */}
            <div className="space-y-8 relative z-10 opacity-70">
              <div className="space-y-2">
                <div className="w-32 h-3 rounded-full" style={{ backgroundColor: brandColor, opacity: 0.2 }} />
                <div className="w-20 h-2 rounded-full" style={{ backgroundColor: brandColor, opacity: 0.1 }} />
              </div>
              <div className="space-y-6 pt-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="flex gap-4">
                    <span className="text-[10px] font-black" style={{ color: brandColor }}>{i}.</span>
                    <div className="flex-1 space-y-2">
                       <div className="w-56 h-2 rounded-full bg-slate-100" />
                       <div className="w-40 h-1.5 rounded-full bg-slate-50" />
                    </div>
                  </div>
                ))}
              </div>
              <div className="pt-12 flex justify-end">
                <div className="w-32 h-16 border-2 border-dashed rounded-2xl flex items-center justify-center opacity-30" style={{ borderColor: brandColor }}>
                  <span className="text-[7px] font-black uppercase tracking-widest">Cachet</span>
                </div>
              </div>
            </div>

            {/* FOOTER & QR - Anchored to the bottom of the CONTENT AREA */}
            <div className="absolute left-0 right-0 px-10 bottom-0 pointer-events-none" style={{ height: `${safeBottomMargin}px` }}>
                
                {/* QR Code Elite - Animated Pattern */}
                {qrConfig.enabled && (
                  <div className="absolute right-10 bottom-20 flex flex-col items-end gap-2 pointer-events-auto">
                    <div 
                      className="w-16 h-16 rounded-2xl border-4 border-white shadow-[0_20px_50px_rgba(0,0,0,0.15)] flex items-center justify-center p-2 relative overflow-hidden transition-all duration-500 hover:scale-110 hover:shadow-[0_25px_60px_rgba(0,0,0,0.2)]" 
                      style={{ backgroundColor: qrConfig.color || brandColor }}
                    >
                       <div className="grid grid-cols-5 gap-[1.5px] w-full h-full opacity-90">
                         {[...Array(25)].map((_, i) => (
                           <div 
                              key={i} 
                              className={cn(
                                "bg-white transition-all duration-700", 
                                getQrCell(i) ? "opacity-100 scale-100" : "opacity-0 scale-50", 
                                qrConfig.style === 'dots' ? "rounded-full" : "rounded-[1.5px]"
                              )} 
                              style={{ transitionDelay: `${i * 15}ms` }}
                           />
                         ))}
                       </div>
                       <div className="absolute inset-0 flex items-center justify-center">
                          <div className="w-6 h-6 bg-white rounded-lg flex items-center justify-center shadow-lg border border-slate-50">
                             {resolvedLogo ? <img src={resolvedLogo} className="w-full h-full object-contain p-0.5" alt="" /> : <QrCode style={{ color: brandColor }} size={12} />}
                          </div>
                       </div>
                    </div>
                    {qrConfig.label && <span className="text-[7px] font-black uppercase text-right w-24 leading-none tracking-widest opacity-60" style={{ color: brandColor }}>{qrConfig.label}</span>}
                  </div>
                )}

                {/* Main Footer Text */}
                <div className="absolute bottom-6 left-10 right-10 flex flex-col items-center text-center gap-2">
                   <div className="w-12 h-1 rounded-full opacity-20" style={{ backgroundColor: brandColor }} />
                   <p className="text-[8px] font-bold uppercase tracking-tight" style={{ color: secondaryColor }}>{identity.adresse || 'ADRESSE DU CABINET'}</p>
                   <p className="text-[9px] font-black uppercase tracking-widest" style={{ color: brandColor }}>{contactString || '05 XX XX XX XX'}</p>
                   <p className="text-[6px] font-black uppercase opacity-20 mt-2">Digital Crown Elite v4.5</p>
                </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

LiveDocumentStudio.displayName = 'LiveDocumentStudio';

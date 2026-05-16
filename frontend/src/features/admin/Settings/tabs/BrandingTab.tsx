import React, { useState } from 'react';
import { 
  Palette as PaletteIcon, 
  QrCode, 
  Upload, 
  FileText,
  MessageCircle,
  Link,
  Instagram,
  MapPin,
  Shield,
  UserCircle,
  Eye,
  File,
  Info,
  Sparkles
} from 'lucide-react';
import { useSettingsStore } from '../hooks/useSettingsStore';
import { SettingsSection, labelClass, inputClass } from '../components/SharedUI';
import { BRAND_IDENTITIES, PREMIUM_FONTS, DESIGN_VARIANTS } from '../../constants';
import { LiveDocumentStudio } from '../../components/LiveDocumentStudio';
import { cn } from '../../../../utils/cn';
import { API_BASE } from '../../../../services/api';

export const BrandingTab: React.FC = () => {
  const { profile, updateProfile, uploadLetterhead } = useSettingsStore();
  const [viewMode, setViewMode] = useState<'app' | 'doc'>('doc');

  const handleLetterheadUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadLetterhead(file);
    }
  };

  const activeFont = PREMIUM_FONTS.find(f => f.id === profile.font_fr) || PREMIUM_FONTS[0];

  const renderPreviewContent = () => {
    if (viewMode === 'app') {
      return (
        <div className="flex flex-col h-full bg-[#F8FAFC]">
          <div className="h-10 bg-white border-b border-slate-100 flex items-center px-4 gap-3">
             <div className="flex gap-1.5">
               <div className="w-2.5 h-2.5 rounded-full bg-slate-200" />
               <div className="w-2.5 h-2.5 rounded-full bg-slate-200" />
               <div className="w-2.5 h-2.5 rounded-full bg-slate-200" />
             </div>
             <div className="flex-1 h-6 bg-slate-50 rounded-lg flex items-center px-3">
               <div className="w-32 h-1.5 bg-slate-100 rounded-full" />
             </div>
          </div>
          <div className="flex-1 p-6 space-y-4">
             <div className="grid grid-cols-3 gap-4">
                {[1,2,3].map(i => (
                  <div key={i} className="h-24 bg-white rounded-2xl border border-slate-100 p-4 space-y-3">
                    <div className="w-8 h-8 rounded-lg bg-primary/10" />
                    <div className="w-12 h-2 bg-slate-100 rounded-full" />
                  </div>
                ))}
             </div>
             <div className="h-40 bg-white rounded-3xl border-2 border-primary/20 p-6 flex flex-col items-center justify-center gap-3">
                <Sparkles className="text-primary animate-pulse" size={24} />
                <div className="w-32 h-2 bg-primary/10 rounded-full" />
             </div>
          </div>
        </div>
      );
    }

    return (
      <div className="scale-[0.82] origin-top transition-transform duration-700">
        <LiveDocumentStudio
          identity={{
            nomCabinet: profile.nom || '',
            nomPraticien: profile.header_lines_fr?.[0] || 'DR. NOM',
            nomPraticienAR: profile.nom_praticien_ar || 'الاسم',
            adresse: profile.adresse || '',
            ice: profile.ice || '',
            if: profile.if || '',
            inpe: profile.inpe || '',
          }}
          selectedIdentity="custom"
          selectedTemplate={(profile.selected_template as any) || 'classic'}
          selectedFont={profile.font_fr || 'inter'}
          headerOption={profile.letterhead_path ? 'letterhead' : 'auto'}
          logoPreview={profile.logo_path ? `${API_BASE}/static/uploads/${profile.logo_path}` : null}
          letterheadPreview={profile.letterhead_path ? `${API_BASE}/static/uploads/${profile.letterhead_path}` : null}
          margins={{ top: profile.margin_top || 3.6, bottom: profile.margin_bottom || 3.2 }}
          cabinetType={profile.selected_template === 'royal' ? 'CLINIQUE' : 'PRIVE'}
          specialtyStrings={{ 
            fr: profile.header_lines_fr?.[2] || 'Spécialités', 
            ar: profile.header_lines_ar?.[2] || 'التخصصات' 
          }}
          contactString={profile.telephone || ''}
          qrConfig={{
            enabled: profile.qr_code_enabled || false,
            type: profile.qr_code_type || 'VCARD',
            label: profile.qr_code_label || '',
            color: profile.qr_code_color || null,
            style: profile.qr_code_style || 'dots'
          }}
          headerScale={profile.header_scale || 1.0}
          customColors={{
            primary: profile.primary_color || '#003380',
            secondary: profile.secondary_color || '#003380',
            accent: profile.accent_color || '#003380'
          }}
        />
      </div>
    );
  };

  return (
    <div className="space-y-12">
      <div className="bg-indigo-900 rounded-[2.5rem] p-8 text-white flex flex-col md:flex-row items-center gap-8 shadow-2xl relative overflow-hidden">
         <div className="flex-1 space-y-4 z-10">
            <div className="flex items-center gap-3">
               <div className="w-10 h-10 bg-white/10 rounded-2xl flex items-center justify-center backdrop-blur-md">
                 <Info size={20} className="text-indigo-200" />
               </div>
               <h3 className="text-xl font-black">Comment fonctionne votre design ?</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
               <div className="space-y-2">
                  <h4 className="text-xs font-black uppercase tracking-widest text-indigo-200">Mode Automatique</h4>
                  <p className="text-xs text-indigo-50/70 leading-relaxed">
                    Digital Crown génère lui-même votre en-tête et pied de page en utilisant vos couleurs et la typographie choisie. <b>Idéal pour imprimer sur papier blanc vierge.</b>
                  </p>
               </div>
               <div className="space-y-2">
                  <h4 className="text-xs font-black uppercase tracking-widest text-indigo-200">Papier Physique (Upload)</h4>
                  <p className="text-xs text-indigo-50/70 leading-relaxed">
                    Si vous téléchargez votre papier à en-tête, le design automatique est <b>désactivé</b>. Le logiciel écrit alors "à l'intérieur" de votre papier en respectant vos marges.
                  </p>
               </div>
            </div>
         </div>
         <div className="w-full md:w-64 h-40 bg-white/5 rounded-3xl border border-white/10 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center gap-3">
            <FileText size={40} className="text-indigo-300" />
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-100">Aperçu Dynamique</span>
         </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-12">
        <div className="xl:col-span-3 space-y-12">
          <SettingsSection title="Design & Polices" icon={<PaletteIcon size={32} />}>
            <div className="space-y-10">
              <div className="space-y-6">
                <label className={labelClass}>Palettes Signature</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {BRAND_IDENTITIES.map(id => (
                    <button
                      key={id.id}
                      onClick={() => { updateProfile({ primary_color: id.primary, secondary_color: id.secondary, accent_color: id.accent }); document.documentElement.style.setProperty('--primary', id.primary); }}
                      className={cn("p-5 rounded-3xl border-2 transition-all text-left flex flex-col gap-4 group relative overflow-hidden", profile.primary_color === id.primary ? "border-primary bg-white shadow-xl scale-[1.02]" : "border-slate-100 bg-slate-50/50 hover:bg-white")}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex flex-col">
                          <h5 className="text-[11px] font-black uppercase tracking-tighter text-slate-900">{id.name}</h5>
                          <span className="text-[9px] text-slate-400 font-bold uppercase">{id.vibe}</span>
                        </div>
                        <div className="flex -space-x-2">
                          <div className="w-6 h-6 rounded-full border-2 border-white shadow-sm" style={{ backgroundColor: id.primary }} />
                          <div className="w-6 h-6 rounded-full border-2 border-white shadow-sm" style={{ backgroundColor: id.secondary }} />
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <label className={labelClass}>Typographie Signature</label>
                  <div className="space-y-2">
                    {PREMIUM_FONTS.map(f => (
                      <button key={f.id} onClick={() => updateProfile({ font_fr: f.id })} className={cn("w-full p-4 rounded-xl border-2 text-left flex items-center justify-between transition-all group", profile.font_fr === f.id ? "border-primary bg-primary/5" : "border-slate-100 bg-white hover:border-slate-200")}>
                        <div className="flex flex-col">
                          <span className={cn("block text-sm font-bold", f.class)}>{f.name}</span>
                          <span className="text-[9px] text-slate-400 font-medium">{f.desc}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="space-y-4">
                  <label className={labelClass}>Mise en Page</label>
                  <div className="grid grid-cols-2 gap-2">
                    {DESIGN_VARIANTS.map((v: any) => (
                      <button key={v.id} onClick={() => updateProfile({ selected_template: v.id })} className={cn("p-4 rounded-xl border-2 text-left flex flex-col gap-3 transition-all", profile.selected_template === v.id ? "border-amber-400 bg-amber-50/50 shadow-sm" : "border-slate-100 bg-white hover:border-slate-200")}>
                        <v.icon size={16} className={cn(profile.selected_template === v.id ? "text-amber-500" : "text-slate-400")} />
                        <span className="text-[10px] font-black uppercase tracking-tight text-slate-900">{v.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </SettingsSection>

          <SettingsSection title="Rendu & Papier" icon={<FileText size={24} />}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
               <div className="bg-slate-50 p-8 rounded-[2.5rem] border border-slate-200 space-y-6">
                  <label className={labelClass}>Utiliser mon papier en-tête physique</label>
                  <div onClick={() => document.getElementById('letterhead-input-branding')?.click()} className="w-full h-48 rounded-[1.5rem] border-2 border-dashed border-slate-300 bg-white flex flex-col items-center justify-center cursor-pointer hover:bg-primary/5 transition-all overflow-hidden shadow-inner">
                     {profile.letterhead_path ? (
                       <img src={profile.letterhead_path.startsWith('http') ? profile.letterhead_path : `${API_BASE}/static/uploads/${profile.letterhead_path}`} className="h-full object-contain p-4" alt="Letterhead" />
                     ) : (
                       <div className="flex flex-col items-center text-slate-300 gap-3">
                         <Upload size={28} />
                         <span className="text-[10px] font-black uppercase tracking-widest">PDF ou Image (A4)</span>
                       </div>
                     )}
                  </div>
                  <input id="letterhead-input-branding" type="file" className="hidden" accept="image/*,application/pdf" onChange={handleLetterheadUpload} />
               </div>
               <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-xl space-y-10">
                  <label className={labelClass}>Ajustement Précis des Marges (CM)</label>
                  <div className="space-y-8">
                    <div className="space-y-3">
                      <div className="flex justify-between items-end"><span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">Marge Supérieure</span><span className="text-lg font-black text-primary">{(profile.margin_top ?? 3.6).toFixed(1)}cm</span></div>
                      <input type="range" min="0" max="10" step="0.2" value={profile.margin_top ?? 3.6} onChange={(e) => updateProfile({ margin_top: parseFloat(e.target.value) })} className="w-full h-2 bg-slate-100 rounded-full cursor-pointer accent-primary" />
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between items-end"><span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">Marge Inférieure</span><span className="text-lg font-black text-emerald-600">{(profile.margin_bottom ?? 3.2).toFixed(1)}cm</span></div>
                      <input type="range" min="0" max="6" step="0.2" value={profile.margin_bottom ?? 3.2} onChange={(e) => updateProfile({ margin_bottom: parseFloat(e.target.value) })} className="w-full h-2 bg-slate-100 rounded-full cursor-pointer accent-emerald-600" />
                    </div>

                    {/* Header Scale Control (Elite v4.2) */}
                    <div className="pt-6 border-t border-slate-100 space-y-4">
                      <div className="flex justify-between items-end">
                        <div className="flex flex-col gap-1">
                          <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">Taille de l'en-tête</span>
                          <p className="text-[9px] text-slate-400 italic">Configurez les textes dans l'onglet <span className="text-primary font-bold">Profil</span></p>
                        </div>
                        <span className="text-lg font-black text-primary">
                          {Math.round((profile.header_scale || 1.0) * 100)}%
                        </span>
                      </div>
                      <input 
                        type="range" 
                        min="0.5" 
                        max="1.8" 
                        step="0.05"
                        value={profile.header_scale || 1.0} 
                        onChange={(e) => updateProfile({ header_scale: parseFloat(e.target.value) })}
                        className="w-full h-2 bg-slate-100 rounded-full cursor-pointer accent-primary" 
                      />
                    </div>
                  </div>
               </div>
            </div>
          </SettingsSection>
        </div>

        <div className="xl:col-span-2">
          <div className="sticky top-8 space-y-6">
            <div className="flex items-center justify-between">
              <label className={labelClass}>Aperçu Elite Interactif</label>
              <div className="flex bg-slate-100 p-1 rounded-xl gap-1">
                 <button onClick={() => setViewMode('doc')} className={cn("px-3 py-1.5 rounded-lg text-[9px] font-black uppercase flex items-center gap-2 transition-all", viewMode === 'doc' ? "bg-white shadow-sm text-slate-900" : "text-slate-400")}>
                   <File size={12} /> Document
                 </button>
                 <button onClick={() => setViewMode('app')} className={cn("px-3 py-1.5 rounded-lg text-[9px] font-black uppercase flex items-center gap-2 transition-all", viewMode === 'app' ? "bg-white shadow-sm text-slate-900" : "text-slate-400")}>
                   <Eye size={12} /> Logiciel
                 </button>
              </div>
            </div>

            <div className="bg-slate-900 rounded-[2.5rem] p-4 shadow-2xl relative overflow-hidden h-[750px] border-[8px] border-slate-800 transition-all duration-500">
               {renderPreviewContent()}
               <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-white/90 backdrop-blur-md px-6 py-2 rounded-full border border-slate-200 shadow-xl flex items-center gap-3">
                 <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                 <span className="text-[10px] font-black uppercase tracking-widest text-slate-800">
                   {viewMode === 'doc' ? `Rendu Ordonnance : ${activeFont.name}` : `Logiciel Elite`}
                 </span>
               </div>
            </div>
            
            <p className="text-center text-[10px] text-slate-400 font-medium px-8 leading-relaxed">
              Toutes les modifications sont enregistrées automatiquement et appliquées à vos futurs documents générés.
            </p>
          </div>
        </div>
      </div>

      <SettingsSection title="Stratégie QR Code" icon={<QrCode size={24} />}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-6 p-8 border border-slate-100 rounded-[2.5rem] bg-white shadow-xl">
            <div className="flex items-center justify-between pb-6 border-b border-slate-50">
               <h4 className="font-black text-slate-900 text-sm uppercase tracking-tighter">Action du QR</h4>
               <button onClick={() => updateProfile({ qr_code_enabled: !profile.qr_code_enabled })} className={cn("w-14 h-7 rounded-full transition-all relative px-1 flex items-center", profile.qr_code_enabled ? "bg-primary" : "bg-slate-300")}>
                <div className={cn("w-5 h-5 bg-white rounded-full shadow-lg transition-all", profile.qr_code_enabled ? "translate-x-7" : "translate-x-0")} />
              </button>
            </div>
            {profile.qr_code_enabled && (
              <>
              <div className="space-y-6 pt-6 border-t border-slate-50">
                <label className={labelClass}>Modèles Visuels QR (Elite v4.5)</label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { id: 'classic', label: 'Classic', desc: 'Carré', icon: <div className="grid grid-cols-2 gap-0.5 w-4 h-4"><div className="bg-current"/><div className="bg-current"/><div className="bg-current"/><div className="bg-current"/></div> },
                    { id: 'dots', label: 'Modern', desc: 'Points', icon: <div className="grid grid-cols-2 gap-0.5 w-4 h-4"><div className="bg-current rounded-full"/><div className="bg-current rounded-full"/><div className="bg-current rounded-full"/><div className="bg-current rounded-full"/></div> },
                    { id: 'rounded', label: 'Elite', desc: 'Arrondi', icon: <div className="grid grid-cols-2 gap-0.5 w-4 h-4"><div className="bg-current rounded-sm"/><div className="bg-current rounded-sm"/><div className="bg-current rounded-sm"/><div className="bg-current rounded-sm"/></div> },
                    { id: 'elite', label: 'Premium', desc: 'Haute Densité', icon: <Sparkles size={16}/> },
                  ].map(style => (
                    <button 
                      key={style.id} 
                      onClick={() => updateProfile({ qr_code_style: style.id })} 
                      className={cn("flex flex-col items-center gap-2 p-3 rounded-2xl border-2 transition-all group", profile.qr_code_style === style.id ? "bg-primary/5 border-primary text-primary" : "bg-white border-slate-50 text-slate-400 hover:border-slate-200")}
                    >
                      <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center group-hover:scale-110 transition-transform">
                        {style.icon}
                      </div>
                      <div className="text-center">
                        <div className="text-[9px] font-black uppercase tracking-tighter">{style.label}</div>
                        <div className="text-[7px] font-bold opacity-50 uppercase">{style.desc}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {[
                  { id: 'VCARD', label: 'Contact', icon: <UserCircle size={14}/> },
                  { id: 'WEBSITE', label: 'Site Web', icon: <Link size={14}/> },
                  { id: 'INSTAGRAM', label: 'Instagram', icon: <Instagram size={14}/> },
                  { id: 'WHATSAPP', label: 'WhatsApp', icon: <MessageCircle size={14}/> },
                  { id: 'LOCATION', label: 'Maps', icon: <MapPin size={14}/> },
                  { id: 'VALIDATION', label: 'Signature', icon: <Shield size={14}/> },
                ].map(t => (
                  <button key={t.id} onClick={() => updateProfile({ qr_code_type: t.id as any })} className={cn("flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all font-bold text-[10px] uppercase", profile.qr_code_type === t.id ? "bg-primary/5 border-primary text-primary" : "bg-white border-slate-50 text-slate-400")}>
                    {t.icon} {t.label}
                  </button>
                ))}
              </div>
                
                {profile.qr_code_type !== 'VALIDATION' && profile.qr_code_type !== 'LOCATION' && (
                  <div className="pt-4 space-y-4 animate-in fade-in slide-in-from-top-2">
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                        {profile.qr_code_type === 'WHATSAPP' ? 'Numéro WhatsApp' : profile.qr_code_type === 'INSTAGRAM' ? 'Nom d\'utilisateur' : 'Valeur / URL'}
                      </label>
                      <input 
                        type="text" 
                        value={profile.qr_code_value || ''} 
                        onChange={(e) => updateProfile({ qr_code_value: e.target.value })}
                        placeholder={profile.qr_code_type === 'WHATSAPP' ? 'Ex: 0612345678' : 'Saisissez la valeur ici...'}
                        className={cn(inputClass, "bg-slate-50 border-slate-100")}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Étiquette (Légende)</label>
                      <input 
                        type="text" 
                        value={profile.qr_code_label || ''} 
                        onChange={(e) => updateProfile({ qr_code_label: e.target.value })}
                        placeholder="Ex: Scannez pour nous écrire"
                        className={cn(inputClass, "bg-slate-50 border-slate-100")}
                      />
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
          <div className="bg-slate-900 rounded-[2.5rem] p-10 flex flex-col items-center justify-center text-center text-white relative overflow-hidden">
             <QrCode size={100} className="text-white/20 mb-6" />
             <h4 className="font-black uppercase tracking-widest text-lg">Digital Crown QR</h4>
             <p className="text-[10px] text-white/40 mt-2">Stratégie : {profile.qr_code_type || 'Défaut'}</p>
          </div>
        </div>
      </SettingsSection>
    </div>
  );
};


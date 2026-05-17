import React, { useState, useEffect } from 'react';
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
  Info,
  Sparkles
} from 'lucide-react';
import { useSettingsStore } from '../hooks/useSettingsStore';
import { SettingsSection, labelClass, inputClass } from '../components/SharedUI';
import { BRAND_IDENTITIES, PREMIUM_FONTS, DESIGN_VARIANTS } from '../../constants';
import { cn } from '../../../../utils/cn';
import { api, API_BASE } from '../../../../services/api';
import { motion } from 'framer-motion';
import { LivePreview } from '../../DocumentStudio/LivePreview';

export const BrandingTab: React.FC = () => {
  const { profile, updateProfile, uploadLetterhead } = useSettingsStore();
  const [showPdfPreview, setShowPdfPreview] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);

  const getQRInputProps = () => {
    switch (profile.qr_code_type) {
      case 'WHATSAPP':
        return {
          label: "Numéro de téléphone WhatsApp",
          placeholder: "Ex: 0612345678 ou 212612345678",
          info: "Les patients pourront scanner le QR code pour vous contacter directement sur WhatsApp."
        };
      case 'INSTAGRAM':
        return {
          label: "Nom d'utilisateur Instagram",
          placeholder: "Ex: @nom_du_cabinet",
          info: "Le QR code ouvrira l'application Instagram directement sur votre profil professionnel."
        };
      case 'WEBSITE':
      default:
        return {
          label: "Lien de votre Site Web ou Doctolib",
          placeholder: "Ex: https://www.moncabinet.com",
          info: "Redirigez les patients vers votre site vitrine ou votre calendrier de prise de rendez-vous."
        };
    }
  };

  const getAutomaticQRInfo = () => {
    switch (profile.qr_code_type) {
      case 'VCARD':
        return "Carte de contact intelligente. Ce QR code intègre automatiquement vos coordonnées professionnelles (Nom, Téléphones, E-mail, Adresse) issues de votre profil cabinet. Idéal pour être enregistré instantanément par vos patients.";
      case 'LOCATION':
        return "Localisation du Cabinet. Génère automatiquement un itinéraire Google Maps basé sur l'adresse renseignée dans votre profil cabinet.";
      case 'VALIDATION':
        return "Authentification Elite. Génère un sceau de sécurité numérique. En scannant ce QR, vos patients et les pharmaciens pourront certifier la validité de l'ordonnance ou du bilan clinique en temps réel.";
      default:
        return "";
    }
  };

  const fetchSamplePdf = async () => {
    setPdfLoading(true);
    try {
      const res = await api.post('/documents/sample-preview', {
        selected_template: profile.selected_template,
        font_fr: profile.font_fr,
        primary_color: profile.primary_color,
        secondary_color: profile.secondary_color,
        accent_color: profile.accent_color,
        margin_top: profile.margin_top,
        margin_bottom: profile.margin_bottom,
        header_scale: profile.header_scale,
        qr_code_enabled: profile.qr_code_enabled,
        qr_code_type: profile.qr_code_type,
        qr_code_style: profile.qr_code_style,
        qr_code_value: profile.qr_code_value,
        qr_code_label: profile.qr_code_label,
      });
      if (res.data.pdf_url) {
        const cleanPath = res.data.pdf_url.startsWith('/') ? res.data.pdf_url.substring(1) : res.data.pdf_url;
        setPdfUrl(`${API_BASE}/api/${cleanPath}?t=${Date.now()}#view=FitH`);
      }
    } catch (err) {
      console.error("Erreur lors de la récupération de l'aperçu PDF:", err);
    } finally {
      setPdfLoading(false);
    }
  };

  useEffect(() => {
    if (!showPdfPreview) return;
    const timer = setTimeout(() => {
      fetchSamplePdf();
    }, 800);
    return () => clearTimeout(timer);
  }, [
    showPdfPreview,
    profile.primary_color,
    profile.secondary_color,
    profile.font_fr,
    profile.selected_template,
    profile.margin_top,
    profile.margin_bottom,
    profile.header_scale,
    profile.qr_code_enabled,
    profile.qr_code_style,
    profile.qr_code_type,
    profile.qr_code_value,
    profile.qr_code_label,
    profile.letterhead_path,
  ]);

  const getImageUrl = (path: string | null | undefined) => {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    const cleanPath = path.replace(/^\/+/, '');
    if (cleanPath.startsWith('api/static/') || cleanPath.startsWith('static/uploads/')) {
      return `${API_BASE}/${cleanPath}`;
    }
    return `${API_BASE}/static/uploads/${cleanPath}`;
  };

  const handleLetterheadUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadLetterhead(file);
    }
  };

  return (
    <div className="w-full transition-all duration-500 ease-in-out">
      <div className="flex flex-col lg:flex-row gap-10 items-start">
        
        {/* LEFT COLUMN: Controls */}
        <div className={cn("space-y-12 transition-all duration-500 w-full animate-in fade-in duration-500", showPdfPreview ? "lg:w-[50%] xl:w-[52%]" : "max-w-[760px]")}>
          <div 
            className="rounded-[2.5rem] p-8 text-white flex flex-col md:flex-row items-center gap-8 shadow-2xl relative overflow-hidden border border-white/10 transition-all duration-700"
            style={{ 
              background: `linear-gradient(135deg, ${profile.primary_color || '#1e1b4b'} 0%, ${profile.secondary_color || '#0f172a'} 100%)` 
            }}
          >
             <div className="absolute inset-0 opacity-[0.03] pointer-events-none select-none" style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '20px 20px' }} />
             <div className="flex-1 space-y-4 z-10">
                <div className="flex items-center gap-3">
                   <div className="w-10 h-10 bg-white/10 rounded-2xl flex items-center justify-center backdrop-blur-md">
                     <Info size={20} className="text-white" />
                   </div>
                   <h3 className="text-xl font-black">Comment fonctionne votre design ?</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
                   <div className="space-y-2">
                      <h4 className="text-xs font-black uppercase tracking-widest text-white/80">Mode Automatique</h4>
                      <p className="text-xs text-white/60 leading-relaxed">
                        Digital Crown génère lui-même votre en-tête et pied de page en utilisant vos couleurs et la typographie choisie. <b>Idéal pour imprimer sur papier blanc vierge.</b>
                      </p>
                   </div>
                   <div className="space-y-2">
                      <h4 className="text-xs font-black uppercase tracking-widest text-white/80">Papier Physique (Upload)</h4>
                      <p className="text-xs text-white/60 leading-relaxed">
                        Si vous téléchargez votre papier à en-tête, le design automatique est <b>désactivé</b>. Le logiciel écrit alors "à l'intérieur" de votre papier en respectant vos marges.
                      </p>
                   </div>
                </div>
             </div>
          </div>

          <div className="space-y-12">
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

                  <div className="flex flex-col gap-8">
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
                <div className="flex flex-col gap-8">
                   <div className="bg-slate-50 p-8 rounded-[2.5rem] border border-slate-200 space-y-6">
                      <label className={labelClass}>Utiliser mon papier en-tête physique</label>
                      <div onClick={() => document.getElementById('letterhead-input-branding')?.click()} className="w-full h-48 rounded-[1.5rem] border-2 border-dashed border-slate-300 bg-white flex flex-col items-center justify-center cursor-pointer hover:bg-primary/5 transition-all overflow-hidden shadow-inner">
                         {profile.letterhead_path ? (
                           <img src={getImageUrl(profile.letterhead_path)} className="h-full object-contain p-4" alt="Letterhead" />
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

            <SettingsSection title="Stratégie QR Code" icon={<QrCode size={24} />}>
                <div className="flex flex-col gap-8">
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
                        <div className="grid grid-cols-2 gap-3">
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

                      <div className="grid grid-cols-2 gap-3">
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
                        
                        {['WHATSAPP', 'INSTAGRAM', 'WEBSITE'].includes(profile.qr_code_type || '') ? (
                          <div className="pt-4 space-y-4 animate-in fade-in slide-in-from-top-2">
                            <div className="space-y-2">
                              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                {getQRInputProps().label}
                              </label>
                              <input 
                                type="text" 
                                value={profile.qr_code_value || ''} 
                                onChange={(e) => updateProfile({ qr_code_value: e.target.value })}
                                placeholder={getQRInputProps().placeholder}
                                className={cn(inputClass, "bg-slate-50 border-slate-100")}
                              />
                              <p className="text-[9px] text-slate-400 italic mt-1">{getQRInputProps().info}</p>
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
                        ) : (
                          <div className="pt-4 p-5 rounded-2xl bg-slate-50 border border-slate-100 flex gap-4 animate-in fade-in slide-in-from-top-2">
                            <div className="w-10 h-10 rounded-xl bg-primary/5 flex items-center justify-center text-primary shrink-0" style={{ color: 'var(--primary)' }}>
                              <Info size={18} />
                            </div>
                            <div className="space-y-1">
                              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">Génération Automatique</span>
                              <p className="text-xs text-slate-500 font-medium leading-relaxed">{getAutomaticQRInfo()}</p>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
            </SettingsSection>
          </div>
        </div>

        {/* RIGHT COLUMN: Dynamic PDF Preview */}
        {showPdfPreview && (
          <div className="w-full lg:w-[50%] xl:w-[48%] lg:sticky lg:top-24 h-[800px] z-10 animate-in slide-in-from-right-8 duration-500">
            <LivePreview
              pdfUrl={pdfUrl}
              loading={pdfLoading}
              onClose={() => setShowPdfPreview(false)}
              onRefresh={fetchSamplePdf}
              title="Aperçu Réel Signature"
              inline={true}
            />
          </div>
        )}

      </div>

      {/* Floating real PDF preview toggler */}
      {!showPdfPreview && (
        <div className="fixed bottom-8 right-8 z-[15000]">
          <motion.button
            whileHover={{ scale: 1.05, y: -4 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              setShowPdfPreview(true);
              fetchSamplePdf();
            }}
            className="flex items-center gap-3 px-8 py-5 bg-emerald-600 text-white rounded-full shadow-[0_24px_50px_rgba(16,185,129,0.35)] hover:bg-emerald-500 hover:shadow-[0_24px_50px_rgba(16,185,129,0.55)] transition-all font-black text-xs uppercase tracking-widest ring-4 ring-white/50 border border-emerald-400/40 backdrop-blur-md animate-in fade-in zoom-in-50 duration-300"
          >
            <Eye size={18} />
            Aperçu PDF Réel
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-300 animate-pulse shadow-[0_0_8px_#10B981]" />
          </motion.button>
        </div>
      )}
    </div>
  );
};


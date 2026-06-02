import React, { useState, useEffect, useRef } from 'react';
import type { Scope } from './types';
import { cn } from '../../../../../utils/cn';
import { ArrowRight, Activity, Users, Calendar, QrCode, Loader2 } from 'lucide-react';
import { LivePreview } from '../../../DocumentStudio/LivePreview';
import { PREMIUM_FONTS } from '../../../constants';
import { api } from '../../../../../services/api';
import toast from 'react-hot-toast';

interface StudioPreviewProps {
  profile: any;
  scope: Scope;
}

export const StudioPreview: React.FC<StudioPreviewProps> = ({ profile, scope }) => {
  const [showRealPdf, setShowRealPdf] = useState(false);
  const [realPdfUrl, setRealPdfUrl] = useState<string | null>(null);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const blobUrlRef = useRef<string | null>(null);

  useEffect(() => {
    const ref = blobUrlRef;
    return () => { if (ref.current) URL.revokeObjectURL(ref.current); };
  }, []);

  const handleShowRealPdf = async (p = profile) => {
    setIsGeneratingPdf(true);
    try {
      const sanitizedPayload = { ...p };
      for (const key in sanitizedPayload) {
        if (sanitizedPayload[key] === "") sanitizedPayload[key] = null;
      }
      const res = await api.post('/documents/sample-preview', sanitizedPayload);
      let pdfPath = res.data.pdf_url;
      if (pdfPath && !pdfPath.startsWith('/')) pdfPath = `/${pdfPath}`;

      // Fetch as blob so the iframe reçoit le PDF sans problème d'auth
      const pdfBlob = await api.get(pdfPath, { responseType: 'blob' });
      if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current);
      const blobUrl = URL.createObjectURL(new Blob([pdfBlob.data], { type: 'application/pdf' }));
      blobUrlRef.current = blobUrl;
      setRealPdfUrl(blobUrl);
      setShowRealPdf(true);
    } catch (e: any) {
      console.error("Erreur API PDF:", e);
      const msg = e.response?.data?.detail || e.message || String(e);
      toast.error("Erreur: " + msg);
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  useEffect(() => {
    if (!showRealPdf) return;
    const timer = setTimeout(() => {
      handleShowRealPdf(profile);
    }, 600); // 600ms debounce
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile, showRealPdf]);

  // Vue APP
  const renderAppPreview = () => (
    <div className="w-full h-full bg-[#FAFAFA] flex overflow-hidden">
      {/* Sidebar 1 */}
      <div className="w-[62px] border-r border-[var(--border-color)] bg-white flex flex-col items-center py-6 gap-6">
        <div className="w-8 h-8 rounded-lg" style={{ backgroundColor: profile.primary_color || 'var(--primary)' }} />
        <div className="w-6 h-6 rounded-md bg-[var(--border-color)]" />
        <div className="w-6 h-6 rounded-md bg-[var(--border-color)]" />
      </div>
      {/* Sidebar 2 */}
      <div className="w-[200px] border-r border-[var(--border-color)] bg-[#F8F9FA] p-5 flex flex-col gap-4">
        <div className="w-24 h-3 rounded bg-[var(--border-color)]" />
        <div className="w-full h-8 rounded-md bg-white border border-[var(--border-color)] flex items-center px-3 gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: profile.accent_color || 'var(--accent)' }} />
          <div className="w-16 h-2 rounded bg-[var(--border-color)]" />
        </div>
        <div className="w-full h-8 rounded-md bg-transparent flex items-center px-3 gap-2 opacity-50">
          <div className="w-3 h-3 rounded-full bg-[var(--border-color)]" />
          <div className="w-20 h-2 rounded bg-[var(--border-color)]" />
        </div>
      </div>
      {/* Main */}
      <div className="flex-1 p-8 flex flex-col gap-8">
        <h2 className="font-medium text-[28px] text-[var(--text-main)]">Tableau de bord</h2>
        
        <div className="grid grid-cols-3 gap-4">
          {[Activity, Users, Calendar].map((Icon, i) => (
            <div key={i} className="bg-white rounded-xl border border-[var(--border-color)] p-5 shadow-sm">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-4" style={{ backgroundColor: profile.primary_color ? profile.primary_color + '26' : 'var(--primary)15', color: profile.primary_color || 'var(--primary)' }}>
                <Icon size={16} />
              </div>
              <div className="w-16 h-6 rounded bg-[var(--border-color)] mb-2" />
              <div className="w-24 h-2 rounded bg-[var(--border-color)] opacity-50" />
            </div>
          ))}
        </div>

        <div className="bg-white rounded-xl border border-[var(--border-color)] p-5 shadow-sm flex flex-col gap-4">
          <div className="flex items-center justify-between pb-4 border-b border-[var(--border-color)]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[var(--border-color)]" />
              <div>
                <div className="w-24 h-3 rounded bg-[var(--border-color)] mb-1" />
                <div className="w-16 h-2 rounded bg-[var(--border-color)] opacity-50" />
              </div>
            </div>
            <div className="px-3 py-1 rounded-full text-[11px] font-bold uppercase" style={{ backgroundColor: profile.secondary_color ? profile.secondary_color + '26' : 'var(--secondary)15', color: profile.secondary_color || 'var(--secondary)' }}>
              En cours
            </div>
          </div>
          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[var(--border-color)]" />
              <div>
                <div className="w-32 h-3 rounded bg-[var(--border-color)] mb-1" />
                <div className="w-20 h-2 rounded bg-[var(--border-color)] opacity-50" />
              </div>
            </div>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold text-white transition-opacity hover:opacity-90" style={{ backgroundColor: profile.primary_color || 'var(--primary)' }}>
              Dossier <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Vue DOC
  const renderDocPreview = () => {
    const fontClass = PREMIUM_FONTS.find(f => f.id === profile.font_fr)?.class || 'font-sans';
    const tpl = profile.selected_template;
    
    return (
    <div className="w-full h-full bg-[#E5E7EB] flex flex-col items-center py-10 overflow-y-auto">
      <div className={cn(
        "w-[420px] min-h-[594px] bg-white shadow-xl flex flex-col relative", 
        fontClass,
        tpl === 'frame' ? "border-4 border-double" : ""
      )} style={{ 
          borderColor: tpl === 'frame' ? (profile.primary_color || 'var(--primary)') : undefined,
          paddingTop: `${profile.margin_top ?? 4.8}cm`, 
          paddingBottom: `${profile.margin_bottom ?? 3.2}cm`, 
          paddingLeft: tpl === 'double-column' ? '3cm' : '1.5cm', 
          paddingRight: '1.5cm' 
      }}>
        
        {tpl === 'double-column' && (
          <div className="absolute left-0 top-0 bottom-0 w-[80px]" style={{ backgroundColor: profile.primary_color || 'var(--primary)', opacity: 0.08 }} />
        )}

        {tpl === 'frame' && (
           <div className="absolute inset-0 flex items-center justify-center opacity-5 pointer-events-none">
             <div className="w-32 h-32 rounded-full border-[10px]" style={{ borderColor: profile.primary_color || 'var(--primary)' }}/>
           </div>
        )}

        {profile.letterhead_path && profile.letterhead_path !== 'PENDING' && (
          <div className="absolute inset-0 border-4 border-dashed border-[var(--border-color)] opacity-20 pointer-events-none" />
        )}

        {/* Header */}
        <div className={cn("w-full pb-4 mb-8 relative z-10", tpl === 'classic' ? "text-center border-b-2" : tpl === 'asymetric' ? "text-left bg-slate-50 p-4 rounded-xl" : "border-b-[2px] flex items-end justify-between")} style={{ borderColor: profile.primary_color || 'var(--primary)' }}>
          <div>
            <div className="font-medium text-[20px] text-[var(--text-main)] mb-1" style={{ transform: `scale(${profile.header_font_scale ?? 1.0})`, transformOrigin: tpl === 'classic' ? 'center bottom' : 'left bottom' }}>
              Docteur {profile.nom_complet || 'Cabinet'}
            </div>
            <div className={cn("text-[11px] text-[var(--text-muted)]", tpl === 'future' ? "bg-primary/10 text-primary px-2 py-0.5 rounded-full inline-block" : "")}>Chirurgien Dentiste</div>
          </div>
          {tpl !== 'classic' && tpl !== 'asymetric' && (
             <div className="w-10 h-10 rounded bg-slate-100 flex items-center justify-center text-slate-300 text-[8px]">LOGO</div>
          )}
        </div>

        {/* Title */}
        <div className={cn("w-full mb-6 relative z-10", tpl === 'asymetric' ? "flex justify-start" : "flex justify-center")}>
          <h1 className="font-medium text-[22px] uppercase tracking-wider" style={{ color: profile.primary_color || 'var(--primary)' }}>
            Ordonnance
          </h1>
        </div>

        {/* Body */}
        <div className="flex-1 flex flex-col gap-4 relative z-10">
          <div className="w-full flex gap-3">
            <div className="w-1.5 h-full rounded-full" style={{ backgroundColor: profile.accent_color || 'var(--accent)' }} />
            <div className="flex-1 flex flex-col gap-2">
              <div className="w-3/4 h-3 bg-[var(--text-main)] rounded opacity-80" />
              <div className="w-1/2 h-2 bg-[var(--text-muted)] rounded opacity-50" />
            </div>
          </div>
          {tpl === 'future' && <div className="w-full h-[1px] bg-slate-100 my-1" />}
          <div className="w-full flex gap-3 mt-4">
            <div className="w-1.5 h-full rounded-full" style={{ backgroundColor: profile.accent_color || 'var(--accent)' }} />
            <div className="flex-1 flex flex-col gap-2">
              <div className="w-2/3 h-3 bg-[var(--text-main)] rounded opacity-80" />
              <div className="w-1/3 h-2 bg-[var(--text-muted)] rounded opacity-50" />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className={cn("w-full mt-auto pt-4 flex items-center justify-between relative z-10", tpl === 'future' ? "border-t-2" : "border-t")} style={{ borderColor: 'var(--border-color)', transform: `scale(${profile.footer_font_scale ?? 1.0})`, transformOrigin: 'bottom center' }}>
           <div className="flex flex-col gap-1">
             <div className="w-16 h-2 bg-[var(--text-muted)] rounded opacity-50" />
             <div className="w-20 h-2 bg-[var(--text-muted)] rounded opacity-50" />
           </div>
           {profile.qr_code_enabled && (
             <div className="flex flex-col items-center gap-1" style={{ transform: `scale(${profile.footer_qr_scale ?? 1.0})` }}>
               <div className={cn("w-12 h-12 flex items-center justify-center text-white", tpl === 'future' ? "rounded-xl" : "rounded-md")} style={{ backgroundColor: profile.primary_color || 'var(--primary)' }}><QrCode size={20}/></div>
               <div className="text-[7px] font-bold uppercase text-[var(--text-main)]">{profile.qr_code_type || 'SCAN'}</div>
             </div>
           )}
           <div className="w-24 h-8 border border-[var(--border-color)] rounded border-dashed flex items-center justify-center text-[9px] text-[var(--text-muted)] ">
             Signature
           </div>
        </div>

      </div>

      <button 
        onClick={() => handleShowRealPdf()}
        disabled={isGeneratingPdf}
        className="mt-6 flex items-center gap-3 px-6 py-3 bg-white border border-slate-200 rounded-2xl text-[11px] font-black uppercase tracking-widest text-slate-600 hover:border-primary hover:text-primary transition-all shadow-sm"
      >
        {isGeneratingPdf ? <Loader2 size={16} className="animate-spin" /> : null}
        Voir le rendu PDF réel
      </button>

    </div>
  )};

  return (
    <div className="sticky top-[18px] bg-white/90 backdrop-blur-3xl border border-slate-200/60 shadow-xl overflow-hidden rounded-[2.5rem] ring-1 ring-black/5 flex flex-col h-[calc(100vh-36px)] min-h-[680px]">
      
      {/* Header */}
      <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-white/40 backdrop-blur-md z-10">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-emerald-500/10 text-emerald-600 rounded-2xl flex items-center justify-center">
            <Activity size={20} />
          </div>
          <div>
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block leading-none mb-1">Aperçu en direct</span>
            <span className="text-base font-black text-slate-800 tracking-tight">
              {scope === 'app' ? 'Tableau de bord' : 'Document A4'}
            </span>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 relative overflow-hidden bg-[var(--bg-medical-pearl)]">
        
        {/* App View */}
        <div className={cn("absolute inset-0 transition-opacity duration-250", scope === 'app' ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none")}>
          {renderAppPreview()}
        </div>

        {/* Doc View */}
        <div className={cn("absolute inset-0 transition-opacity duration-250", scope === 'doc' ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none")}>
          {renderDocPreview()}
        </div>

      </div>

      {showRealPdf && (
        <LivePreview 
          pdfUrl={realPdfUrl} 
          loading={isGeneratingPdf} 
          onRefresh={() => handleShowRealPdf()}
          onClose={() => {
            setShowRealPdf(false);
            setRealPdfUrl(null);
          }} 
          title="Aperçu Réel" 
        />
      )}
    </div>
  );
};

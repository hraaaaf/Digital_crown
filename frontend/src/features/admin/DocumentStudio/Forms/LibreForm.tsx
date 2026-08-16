import React, { useEffect, useRef } from 'react';
import { cn } from '../../../../utils/cn';
import { api } from '../../../../services/api';

import type { ValidationError } from '../useDocumentGenerator';
import { isLibreDirty, setLibreDirty } from '../LibreDirtyState';
import { AlertCircle, Bold, Italic, Underline, Table, Type } from 'lucide-react';

interface LibreFormProps {
  title: string;
  setTitle: (val: string) => void;
  content: string;
  setContent: (val: string) => void;
  customPatient: string;
  setCustomPatient: (val: string) => void;
  customDate: string;
  setCustomDate: (val: string) => void;
  hideHeader: boolean;
  setHideHeader: (val: boolean) => void;
  pageSize: 'A5' | 'A4';
  setPageSize: (val: 'A5' | 'A4') => void;
  alignment: 'left' | 'center' | 'right' | 'justify';
  setAlignment: (val: 'left' | 'center' | 'right' | 'justify') => void;
  validationErrors?: ValidationError[];
}

export const LibreForm: React.FC<LibreFormProps> = ({
  title, setTitle,
  content, setContent,
  customPatient, setCustomPatient,
  customDate, setCustomDate,
  hideHeader, setHideHeader,
  pageSize, setPageSize,
  alignment, setAlignment,
  validationErrors = []
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    // L'ouverture/réouverture d'un Document Libre établit une baseline propre.
    // Les mutations utilisateur appellent ensuite markDirty().
    setLibreDirty(false);

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!isLibreDirty()) return;
      event.preventDefault();
      event.returnValue = '';
    };

    // Un archivage Libre n'est considéré comme sauvegardé qu'après une réponse
    // backend réussie contenant un nouveau PDF. Un échec/409 conserve le dirty state.
    const responseInterceptor = api.interceptors.response.use((response: any) => {
      const url = String(response?.config?.url || '');
      const method = String(response?.config?.method || '').toLowerCase();
      if (method !== 'post' || !url.includes('/documents/generate') || !url.includes('archive=true')) {
        return response;
      }

      let payload = response?.config?.data;
      if (typeof payload === 'string') {
        try {
          payload = JSON.parse(payload);
        } catch {
          payload = null;
        }
      }

      if (payload?.type === 'libre' && response?.data?.pdf_url) {
        setLibreDirty(false);
      }
      return response;
    });

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      api.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  const markDirty = () => setLibreDirty(true);

  const insertTag = (openTag: string, closeTag: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selected = content.substring(start, end);
    
    const newText = content.substring(0, start) + openTag + selected + closeTag + content.substring(end);
    markDirty();
    setContent(newText);
    
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + openTag.length, start + openTag.length + selected.length);
    }, 10);
  };

  const handleTableInsert = () => {
    const tableSnippet = `\n| Colonne 1 | Colonne 2 |\n|-----------|-----------|\n| Ligne 1   | Valeur    |\n`;
    insertTag(tableSnippet, '');
  };

  const inputClass = "w-full px-4 py-3 bg-white/70 border border-slate-100 rounded-xl text-sm outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all duration-300 shadow-sm font-bold text-slate-800";
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-2 ml-1";
  const titleError = validationErrors.find(e => e.field === 'libreTitle');
  const contentError = validationErrors.find(e => e.field === 'libreContent');

  return (
    <div className="space-y-6 animate-in fade-in duration-500 h-full flex flex-col max-w-4xl mx-auto py-8 w-full">
      
      {/* 🌟 Header Glassmorphism */}
      <div className="bg-white/40 backdrop-blur-xl rounded-[2.5rem] border border-white/60 p-8 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] -mr-32 -mt-32 rounded-full pointer-events-none" />
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
          <div className="md:col-span-1">
            <label className={labelClass}>Titre du Document</label>
            <input type="text" className={cn(inputClass, titleError && "border-red-300 shadow-red-50")} value={title} onChange={(e) => { markDirty(); setTitle(e.target.value); }} placeholder="Ex: ORDONNANCE, LETTRE..." />
            {titleError && (
              <div className="mt-2 text-[9px] font-black text-red-500 uppercase tracking-widest flex items-center gap-1">
                <AlertCircle size={12} /> Titre Requis
              </div>
            )}
          </div>
          <div>
            <label className={labelClass}>Destinataire <span className="opacity-50">(Optionnel)</span></label>
            <input type="text" className={inputClass} value={customPatient} onChange={(e) => { markDirty(); setCustomPatient(e.target.value); }} placeholder="Ex: À qui de droit..." />
          </div>
          <div>
            <label className={labelClass}>Date/Lieu <span className="opacity-50">(Optionnel)</span></label>
            <input type="text" className={inputClass} value={customDate} onChange={(e) => { markDirty(); setCustomDate(e.target.value); }} placeholder="Ex: Rabat, le 12/05/2026" />
          </div>
          
          <div className="md:col-span-3 flex flex-wrap items-center justify-between gap-6 mt-4 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
            <div className="flex items-center gap-3">
              <input 
                type="checkbox" 
                id="hideHeader" 
                checked={hideHeader} 
                onChange={(e) => { markDirty(); setHideHeader(e.target.checked); }}
                className="w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary accent-primary"
              />
              <label htmlFor="hideHeader" className="text-[11px] font-black text-slate-500 uppercase tracking-widest cursor-pointer">Masquer l'en-tête patient</label>
            </div>

            <div className="flex gap-8">
              <div className="flex items-center gap-3">
                <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Format</span>
                <div className="flex bg-white p-1 rounded-xl shadow-sm border border-slate-100 gap-1">
                  {['A5', 'A4'].map((size) => (
                    <button 
                      key={size}
                      type="button"
                      onClick={() => { markDirty(); setPageSize(size as 'A5' | 'A4'); }}
                      className={cn(
                        "px-4 py-1.5 rounded-lg text-[10px] font-black transition-all",
                        pageSize === size ? "bg-primary text-white shadow-md shadow-primary/20" : "text-slate-400 hover:text-slate-600 hover:bg-slate-50"
                      )}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Alignement</span>
                <div className="flex bg-white p-1 rounded-xl shadow-sm border border-slate-100 gap-1">
                  {[
                    { id: 'left', label: 'Gauche' },
                    { id: 'center', label: 'Centre' },
                    { id: 'right', label: 'Droite' },
                    { id: 'justify', label: 'Justifié' }
                  ].map((align) => (
                    <button 
                      key={align.id}
                      type="button"
                      onClick={() => { markDirty(); setAlignment(align.id as 'left' | 'center' | 'right' | 'justify'); }}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-[10px] font-black transition-all",
                        alignment === align.id ? "bg-primary text-white shadow-md shadow-primary/20" : "text-slate-400 hover:text-slate-600 hover:bg-slate-50"
                      )}
                    >
                      {align.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ✍️ Zone de Rédaction avec Toolbar */}
      <div className="flex-1 min-h-[400px] flex flex-col bg-white rounded-[2.5rem] border border-slate-200 shadow-sm overflow-hidden relative">
        
        {/* Toolbar */}
        <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-200 flex items-center gap-2 flex-wrap">
          <div className="flex bg-white rounded-xl shadow-sm border border-slate-200 p-1">
             <button type="button" onClick={() => insertTag('<b>', '</b>')} className="p-2 text-slate-500 hover:text-primary hover:bg-primary/5 rounded-lg transition-all" title="Gras">
               <Bold size={16} strokeWidth={2.5} />
             </button>
             <button type="button" onClick={() => insertTag('<i>', '</i>')} className="p-2 text-slate-500 hover:text-primary hover:bg-primary/5 rounded-lg transition-all" title="Italique">
               <Italic size={16} strokeWidth={2.5} />
             </button>
             <button type="button" onClick={() => insertTag('<u>', '</u>')} className="p-2 text-slate-500 hover:text-primary hover:bg-primary/5 rounded-lg transition-all" title="Souligné">
               <Underline size={16} strokeWidth={2.5} />
             </button>
          </div>
          
          <div className="w-px h-6 bg-slate-200 mx-2" />
          
          <div className="flex bg-white rounded-xl shadow-sm border border-slate-200 p-1">
             <button type="button" onClick={() => insertTag('<font size="16">', '</font>')} className="flex items-center gap-2 px-3 py-2 text-slate-500 hover:text-primary hover:bg-primary/5 rounded-lg transition-all" title="Agrandir">
               <Type size={16} /> <span className="text-[10px] font-black uppercase tracking-widest">Grand Titre</span>
             </button>
             <button type="button" onClick={handleTableInsert} className="flex items-center gap-2 px-3 py-2 text-slate-500 hover:text-primary hover:bg-primary/5 rounded-lg transition-all" title="Tableau">
               <Table size={16} /> <span className="text-[10px] font-black uppercase tracking-widest">Tableau</span>
             </button>
          </div>
        </div>

        <textarea
          ref={textareaRef}
          className={cn(
            "w-full flex-1 p-8 text-sm font-medium text-slate-700 outline-none transition-all resize-none leading-relaxed custom-scrollbar",
            contentError ? "bg-red-50/30" : "bg-transparent"
          )}
          value={content}
          onChange={(e) => { markDirty(); setContent(e.target.value); }}
          placeholder="Rédigez votre document ici... Utilisez la barre d'outils pour mettre en forme le texte."
        />
        {contentError && (
          <div className="absolute bottom-6 right-6 px-5 py-3 bg-red-50 border border-red-200 rounded-2xl text-[10px] font-black text-red-600 uppercase tracking-widest flex items-center gap-2 shadow-lg">
            <AlertCircle size={16} /> Le contenu ne peut être vide
          </div>
        )}
      </div>
    </div>
  );
};
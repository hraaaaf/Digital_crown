import React from 'react';
import { cn } from '../../../../utils/cn';

import type { ValidationError } from '../useDocumentGenerator';
import { AlertCircle } from 'lucide-react';

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
  const inputClass = "w-full px-4 py-3 bg-white/70 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-300 shadow-sm font-medium text-slate-800";
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1";

  return (
    <div className="space-y-6 animate-in fade-in duration-500 h-full flex flex-col">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-slate-50/50 rounded-2xl border border-slate-100 mb-2">
        <div className="md:col-span-1">
          <label className={labelClass}>Titre du Document</label>
          <input type="text" className={cn(inputClass, "font-black", validationErrors.find(e => e.field === 'title') && "border-red-300 shadow-red-50")} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Ex: ORDONNANCE, LETTRE..." />
          {validationErrors.find(e => e.field === 'title') && (
            <div className="mt-1 text-[8px] font-black text-red-500 uppercase tracking-widest flex items-center gap-1">
              <AlertCircle size={10} /> Titre Requis
            </div>
          )}
        </div>
        <div>
          <label className={labelClass}>Destinataire (Édition Dynamique)</label>
          <input type="text" className={inputClass} value={customPatient} onChange={(e) => setCustomPatient(e.target.value)} placeholder="Ex: À qui de droit..." />
        </div>
        <div>
          <label className={labelClass}>Date/Lieu (Édition Dynamique)</label>
          <input type="text" className={inputClass} value={customDate} onChange={(e) => setCustomDate(e.target.value)} placeholder="Ex: Rabat, le 12/05/2026" />
        </div>
        
        <div className="md:col-span-3 flex flex-wrap items-center gap-6 mt-1 border-t border-slate-100 pt-4">
          <div className="flex items-center gap-2">
            <input 
              type="checkbox" 
              id="hideHeader" 
              checked={hideHeader} 
              onChange={(e) => setHideHeader(e.target.checked)}
              className="w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary"
            />
            <label htmlFor="hideHeader" className="text-xs font-bold text-slate-500 cursor-pointer">Masquer l'en-tête patient standard</label>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Format :</span>
            <div className="flex bg-slate-200/50 p-1 rounded-lg gap-1">
              {['A5', 'A4'].map((size) => (
                <button 
                  key={size}
                  onClick={() => setPageSize(size as any)}
                  className={cn(
                    "px-3 py-1 rounded-md text-[10px] font-black transition-all",
                    pageSize === size ? "bg-white text-primary shadow-sm" : "text-slate-400 hover:text-slate-600"
                  )}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Alignement :</span>
            <div className="flex bg-slate-200/50 p-1 rounded-lg gap-1">
              {[
                { id: 'left', label: 'Gauche' },
                { id: 'center', label: 'Centre' },
                { id: 'right', label: 'Droite' },
                { id: 'justify', label: 'Justifié' }
              ].map((align) => (
                <button 
                  key={align.id}
                  onClick={() => setAlignment(align.id as any)}
                  className={cn(
                    "px-3 py-1 rounded-md text-[10px] font-black transition-all",
                    alignment === align.id ? "bg-white text-primary shadow-sm" : "text-slate-400 hover:text-slate-600"
                  )}
                >
                  {align.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-[300px] relative">
        <textarea
          className={cn(
            "w-full h-full p-8 bg-white border rounded-[2rem] text-sm font-medium text-slate-700 outline-none focus:ring-4 focus:ring-primary/5 transition-all shadow-inner resize-none leading-relaxed",
            validationErrors.find(e => e.field === 'content') ? "border-red-200" : "border-slate-200"
          )}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Rédigez votre document ici... Le texte sera automatiquement formaté dans le PDF final."
        />
        {validationErrors.find(e => e.field === 'content') && (
          <div className="absolute top-4 right-8 px-4 py-2 bg-red-50 border border-red-200 rounded-xl text-[10px] font-black text-red-600 uppercase tracking-widest flex items-center gap-2 shadow-sm">
            <AlertCircle size={12} /> Contenu Requis
          </div>
        )}
      </div>
    </div>
  );
};

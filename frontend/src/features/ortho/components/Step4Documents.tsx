import React from 'react';
import { Camera, Printer, Clock, FileText, CheckCircle2 } from 'lucide-react';
import type { PhotoUpload } from '../cephaloTypes';

interface Step4DocumentsProps {
  photos: PhotoUpload[];
  patientName: string;
  sexe: 'M' | 'F';
  onUpload: (id: string, file: File) => void;
  onGeneratePDF: () => void;
  isGenerating: boolean;
  P: any;
}

export const Step4Documents: React.FC<Step4DocumentsProps> = ({ 
  photos, onUpload, onGeneratePDF, isGenerating, P 
}) => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* GRILLE DE PHOTOS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {photos.map((photo) => (
          <div 
            key={photo.id}
            className="group relative aspect-square rounded-2xl overflow-hidden border-2 border-dashed transition-all hover:border-solid"
            style={{ 
              background: P.bgCard, 
              borderColor: photo.preview ? P.accentSuccess : P.border,
              borderStyle: photo.preview ? 'solid' : 'dashed'
            }}
          >
            {photo.preview ? (
              <>
                <img src={photo.preview} alt={photo.label} className="w-full h-full object-cover transition-transform group-hover:scale-105" />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <label className="cursor-pointer p-2 bg-white/20 backdrop-blur-md rounded-full text-white hover:bg-white/40">
                    <Camera size={20} />
                    <input type="file" className="hidden" accept="image/*" onChange={(e) => e.target.files?.[0] && onUpload(photo.id, e.target.files[0])} />
                  </label>
                </div>
                <div className="absolute top-2 right-2 p-1 bg-emerald-500 rounded-full text-white shadow-lg">
                  <CheckCircle2 size={12} />
                </div>
              </>
            ) : (
              <label className="flex flex-col items-center justify-center w-full h-full cursor-pointer p-4 text-center gap-3">
                <Camera size={24} style={{ color: P.textDim }} />
                <span className="text-[10px] font-black uppercase tracking-widest leading-tight" style={{ color: P.textMuted }}>{photo.label}</span>
                <input type="file" className="hidden" accept="image/*" onChange={(e) => e.target.files?.[0] && onUpload(photo.id, e.target.files[0])} />
              </label>
            )}
          </div>
        ))}
      </div>

      {/* SECTION GÉNÉRATION DOCUMENTS */}
      <div className="rounded-[2rem] p-8 flex flex-col md:flex-row items-center justify-between gap-8" style={{ background: P.bgPanel, border: `1px solid ${P.border}`, boxShadow: P.shadowLg }}>
        <div className="flex items-center gap-6">
          <div className="p-4 rounded-2xl" style={{ background: `${P.accent}10`, color: P.accent }}>
            <FileText size={32} />
          </div>
          <div>
            <h3 className="text-xl font-black" style={{ color: P.text }}>Rapport Céphalométrique Complet</h3>
            <p className="text-sm font-medium mt-1" style={{ color: P.textMuted }}>Générez un bilan PDF professionnel incluant tracés, mesures et diagnostics IA.</p>
          </div>
        </div>

        <button 
          onClick={onGeneratePDF}
          disabled={isGenerating}
          className="w-full md:w-auto px-10 py-5 rounded-2xl font-black uppercase tracking-widest text-white shadow-xl flex items-center justify-center gap-3 transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
          style={{ background: `linear-gradient(135deg, ${P.accent}, ${P.accent}dd)` }}
        >
          {isGenerating ? <Clock size={20} className="animate-spin" /> : <Printer size={20} />}
          Générer le Bilan PDF
        </button>
      </div>
    </div>
  );
};

import React from 'react';
import { cn } from '../../../../utils/cn';

import type { ValidationError } from '../useDocumentGenerator';
import { AlertCircle } from 'lucide-react';

interface CertificateFormProps {
  certifType: string;
  setCertifType: (type: string) => void;
  certifDays: number;
  setCertifDays: (days: number) => void;
  validationErrors?: ValidationError[];
}

export const CertificateForm: React.FC<CertificateFormProps> = ({
  certifType,
  setCertifType,
  certifDays,
  setCertifDays,
  validationErrors = []
}) => {
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1";

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-2xl mx-auto py-8">
      <div className="bg-primary/5 rounded-[2.5rem] border border-primary/10 p-10 space-y-8">
        <div>
          <label className={labelClass}>Type de certificat</label>
          <div className="grid grid-cols-2 gap-3">
            {['Repos médical', 'Arrêt de travail', 'Certificat d\'aptitude'].map((type) => (
              <button 
                key={type} 
                onClick={() => setCertifType(type)} 
                className={cn(
                  "px-6 py-4 rounded-2xl text-xs font-black uppercase tracking-widest transition-all border", 
                  certifType === type 
                    ? "bg-primary text-white border-primary shadow-lg shadow-primary/20" 
                    : "bg-white text-slate-500 border-slate-100 hover:border-primary/30"
                )}
                style={certifType === type ? { backgroundColor: 'var(--primary)' } : {}}
              >
                {type}
              </button>
            ))}
          </div>
        </div>
        <div className="pt-4">
          <div className="flex justify-between items-center mb-4">
            <label className={labelClass + " mb-0"}>Durée : {certifDays} jours</label>
            <span className="text-xl font-black text-primary" style={{ color: 'var(--primary)' }}>{certifDays} j</span>
          </div>
          <input 
            type="range" 
            min="0" 
            max="30" 
            step="1" 
            value={certifDays} 
            onChange={(e) => setCertifDays(parseInt(e.target.value))} 
            className="w-full h-3 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-primary" 
            style={{ accentColor: 'var(--primary)' }}
          />
          {validationErrors.find(e => e.field === 'certifDays') && (
            <div className="mt-4 px-4 py-2 bg-red-50 border border-red-200 rounded-xl text-[10px] font-black text-red-600 uppercase tracking-widest flex items-center gap-2 animate-in slide-in-from-top-2">
              <AlertCircle size={12} /> Durée Invalide
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

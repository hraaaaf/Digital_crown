import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../../../utils/cn';
import type { ValidationError } from '../useDocumentGenerator';
import { AlertCircle, CheckCircle2, Clock, Edit3 } from 'lucide-react';

interface CertificateFormProps {
  certifType: string;
  setCertifType: (type: string) => void;
  certifDays: number;
  setCertifDays: (days: number) => void;
  certifCustomMotif: string;
  setCertifCustomMotif: (v: string) => void;
  validationErrors?: ValidationError[];
}

export const CertificateForm: React.FC<CertificateFormProps> = ({
  certifType,
  setCertifType,
  certifDays,
  setCertifDays,
  certifCustomMotif,
  setCertifCustomMotif,
  validationErrors = []
}) => {
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-4 ml-1";
  const inputClass = "w-full px-5 py-4 bg-white/70 border border-slate-100 rounded-2xl text-sm outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all duration-300 shadow-sm font-bold text-slate-800";

  const certifTypes = [
    { id: 'Repos Post-Opératoire', label: 'Repos Post-Op', icon: <Clock size={14} /> },
    { id: 'Suite d\'Intervention', label: 'Suite d\'Acte', icon: <CheckCircle2 size={14} /> },
    { id: 'Certificat de Présence', label: 'Présence (Soin)', icon: <CheckCircle2 size={14} /> },
    { id: 'Certificat d\'aptitude', label: 'Aptitude', icon: <CheckCircle2 size={14} /> },
    { id: 'Autre', label: 'Autre motif', icon: <Edit3 size={14} /> },
  ];

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-2xl mx-auto py-12">
      <div className="bg-white/40 backdrop-blur-xl rounded-[3rem] border border-white/60 p-12 shadow-[0_20px_50px_rgba(0,51,128,0.04)] relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] -mr-32 -mt-32 rounded-full" />

        <div className="relative z-10 space-y-12">
          {/* TYPE DE CERTIFICAT */}
          <div>
            <label className={labelClass}>Motif Clinique (Post-Acte)</label>
            <div className="grid grid-cols-2 gap-4">
              {certifTypes.map((type) => (
                <motion.button
                  key={type.id}
                  whileHover={{ y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setCertifType(type.id)}
                  className={cn(
                    "flex items-center justify-center gap-3 px-6 py-5 rounded-[1.5rem] text-[10px] font-black uppercase tracking-widest transition-all border shadow-sm",
                    certifType === type.id
                      ? "bg-primary text-white border-primary shadow-xl shadow-primary/20"
                      : "bg-white text-slate-500 border-slate-100 hover:border-primary/30 hover:bg-slate-50/50"
                  )}
                  style={certifType === type.id ? { backgroundColor: 'var(--primary)' } : {}}
                >
                  <span className={cn(certifType === type.id ? "text-white" : "text-primary/40")}>{type.icon}</span>
                  {type.label}
                </motion.button>
              ))}
            </div>

            {certifType === 'Autre' && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6"
              >
                <label className={labelClass}>Précisez le motif</label>
                <input
                  type="text"
                  className={inputClass}
                  placeholder="Ex : Douleur post-extraction, Traitement parodontal..."
                  value={certifCustomMotif}
                  onChange={(e) => setCertifCustomMotif(e.target.value)}
                  autoFocus
                />
              </motion.div>
            )}
          </div>

          {/* DURÉE */}
          <div className="pt-6 border-t border-slate-100/50">
            <div className="flex justify-between items-end mb-6">
              <div>
                <label className={labelClass + " mb-1"}>Durée du repos</label>
                <p className="text-[9px] font-bold text-slate-400 italic">Limité aux suites d'interventions faciales.</p>
              </div>
              <motion.span
                key={certifDays}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="text-3xl font-black text-primary tracking-tighter"
                style={{ color: 'var(--primary)' }}
              >
                {certifDays} <span className="text-[10px] uppercase tracking-widest ml-1 opacity-40">jours</span>
              </motion.span>
            </div>

            <div className="relative h-12 flex items-center">
              <input
                type="range"
                min="1"
                max="15"
                step="1"
                value={certifDays}
                onChange={(e) => setCertifDays(parseInt(e.target.value))}
                className="w-full h-2.5 bg-slate-100 rounded-full appearance-none cursor-pointer accent-primary"
                style={{ accentColor: 'var(--primary)' }}
              />
            </div>

            {validationErrors.find(e => e.field === 'certifDays') && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 px-6 py-4 bg-rose-50 border border-rose-100 rounded-[1.2rem] text-[10px] font-black text-rose-600 uppercase tracking-widest flex items-center gap-3"
              >
                <AlertCircle size={14} /> {validationErrors.find(e => e.field === 'certifDays')?.message}
              </motion.div>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center gap-2 text-slate-400">
        <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />
        <span className="text-[9px] font-black uppercase tracking-[0.3em]">Certificat Médical SÉCURISÉ</span>
        <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />
      </div>
    </div>
  );
};

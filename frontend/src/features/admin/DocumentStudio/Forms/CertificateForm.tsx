import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../../../utils/cn';
import { CheckCircle2, Clock, Edit3, Sparkles, AlertCircle } from 'lucide-react';
import { api } from '../../../../services/api';

interface CertificateFormProps {
  patientId: string;
  certifType: string;
  setCertifType: (type: string) => void;
  certifDays: number;
  setCertifDays: (days: number) => void;
  certifCustomMotif: string;
  setCertifCustomMotif: (v: string) => void;
}

export const CertificateForm: React.FC<CertificateFormProps> = ({
  patientId,
  certifType,
  setCertifType,
  certifDays,
  setCertifDays,
  certifCustomMotif,
  setCertifCustomMotif,
}) => {
  const [suggestion, setSuggestion] = React.useState<any>(null);

  React.useEffect(() => {
    if (!patientId) return;
    const fetchSuggestion = async () => {
      try {
        const res = await api.get(`/prescriptions/certif-suggest/${patientId}`);
        setSuggestion(res.data);
        // Si confiance haute, on applique directement (Zero Friction)
        if (res.data.confidence === 'high') {
          setCertifType(res.data.type);
          setCertifDays(res.data.days);
        }
      } catch (err) {
        console.error('Certif Suggest Error:', err);
      }
    };
    fetchSuggestion();
  }, [patientId, setCertifType, setCertifDays]);
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-4 ml-1";
  const inputClass = "w-full px-5 py-4 bg-white/70 border border-slate-100 rounded-2xl text-sm outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all duration-300 shadow-sm font-bold text-slate-800";

  const certifTypes = [
    { id: 'Repos Post-Opératoire', label: 'Repos Post-Op', icon: <Clock size={14} /> },
    { id: 'Certificat de Présence', label: 'Présence (Soin)', icon: <CheckCircle2 size={14} /> },
    { id: 'Autre', label: 'Autre motif', icon: <Edit3 size={14} /> },
  ];


  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-4xl w-full mx-auto py-8">
      <div className="bg-white/40 backdrop-blur-xl rounded-[3rem] border border-white/60 p-10 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] -mr-32 -mt-32 rounded-full pointer-events-none" />

        <div className="relative z-10 space-y-10">
          {/* TYPE DE CERTIFICAT */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <label className={labelClass + " mb-0"}>Motif Clinique</label>
              {suggestion && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1 rounded-full text-[8px] font-black uppercase tracking-widest",
                    suggestion.confidence === 'high' ? "bg-emerald-500/10 text-emerald-600 border border-emerald-200" : "bg-primary/5 text-primary border border-primary/10"
                  )}
                >
                  <Sparkles size={10} className="animate-pulse" />
                  {suggestion.reason}
                </motion.div>
              )}
            </div>

            <div className="flex flex-wrap justify-center gap-4">
              {certifTypes.map((type) => (
                <div key={type.id} className="flex flex-col items-center gap-2">
                  <button
                    onClick={() => setCertifType(type.id)}
                    className={cn(
                      "flex items-center justify-center gap-3 px-6 py-4 rounded-[1.5rem] text-[10px] font-black uppercase tracking-widest transition-all border shadow-sm min-w-[180px]",
                      certifType === type.id
                        ? "bg-primary text-white border-primary shadow-xl shadow-primary/20"
                        : "bg-white text-slate-500 border-slate-100 hover:border-primary/30"
                    )}
                    style={certifType === type.id ? { backgroundColor: 'var(--primary)' } : {}}
                  >
                    <span className={cn(certifType === type.id ? "text-white" : "text-primary/40")}>{type.icon}</span>
                    {type.label}
                  </button>
                  <span className="text-[7px] font-black text-slate-300 uppercase tracking-widest text-center px-4">
                    {type.id === 'Repos Post-Opératoire' && "Génère un arrêt de travail / repos"}
                    {type.id === 'Certificat de Présence' && "Génère un justificatif de présence"}
                    {type.id === 'Autre' && "Saisie libre du motif"}
                  </span>
                </div>
              ))}
            </div>

            {certifType === 'Autre' && (
              <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="mt-6">
                <input
                  type="text"
                  className={inputClass}
                  placeholder="Saisissez le motif personnalisé..."
                  value={certifCustomMotif}
                  onChange={(e) => setCertifCustomMotif(e.target.value)}
                  autoFocus
                />
              </motion.div>
            )}
          </div>

          {/* DURÉE */}
          {certifType !== 'Certificat de Présence' && (
            <div className="pt-8 border-t border-slate-100/50">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <label className={labelClass + " mb-1"}>Durée du repos</label>
                  <p className="text-[9px] font-bold text-slate-400 italic">Limité aux suites d'actes bucco-dentaires.</p>
                </div>
                <span className="text-3xl font-black text-primary tracking-tighter" style={{ color: 'var(--primary)' }}>
                  {certifDays} <span className="text-[10px] uppercase tracking-widest ml-1 opacity-40">jours</span>
                </span>
              </div>

              <input
                type="range"
                min="1"
                max="30"
                step="1"
                value={certifDays}
                onChange={(e) => setCertifDays(parseInt(e.target.value))}
                className="w-full h-2.5 bg-slate-100 rounded-full appearance-none cursor-pointer accent-primary"
                style={{ accentColor: 'var(--primary)' }}
              />
            </div>
          )}
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

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../../../utils/cn';
import { CheckCircle2, Clock, Edit3, AlertCircle } from 'lucide-react';
import { api } from '../../../../services/api';
import {
  CERTIFICATE_TYPE_FREE,
  CERTIFICATE_TYPE_PRESENCE,
  CERTIFICATE_TYPE_WORK_STOP,
  certificateRequiresDuration,
  normalizeCertificateSelection,
} from '../CertificatePolicy';
import { setCertificateDirty } from '../CertificateDirtyState';

interface CertificateFormProps {
  patientId: string;
  certifType: string;
  setCertifType: (type: string) => void;
  certifDays: number;
  setCertifDays: (days: number) => void;
  docDate: string;
  certifStartDate: string;
  setCertifStartDate: (date: string) => void;
  certifCustomMotif: string;
  setCertifCustomMotif: (v: string) => void;
}

export const CertificateForm: React.FC<CertificateFormProps> = ({
  patientId,
  certifType,
  setCertifType,
  certifDays,
  setCertifDays,
  docDate,
  certifStartDate,
  setCertifStartDate,
  certifCustomMotif,
  setCertifCustomMotif,
}) => {
  const [suggestion, setSuggestion] = React.useState<any>(null);

  React.useEffect(() => {
    setCertificateDirty(false);
  }, []);

  React.useEffect(() => {
    if (!patientId) return;
    const fetchSuggestion = async () => {
      try {
        const res = await api.get(`/prescriptions/certif-suggest/${patientId}`);
        setSuggestion(res.data);
      } catch (err) {
        console.error('Certif Suggest Error:', err);
      }
    };
    fetchSuggestion();
  }, [patientId]);

  React.useEffect(() => {
    const normalized = normalizeCertificateSelection(certifType, certifCustomMotif);
    if (normalized.type !== certifType) setCertifType(normalized.type);
    if (normalized.content !== certifCustomMotif) setCertifCustomMotif(normalized.content);
  }, [certifType, certifCustomMotif, setCertifType, setCertifCustomMotif]);

  const markDirty = () => setCertificateDirty(true);
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-4 ml-1";
  const inputClass = "w-full px-5 py-4 bg-white/70 border border-slate-100 rounded-2xl text-sm outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all duration-300 shadow-sm font-bold text-slate-800";
  const freeContentMissing = certifType === CERTIFICATE_TYPE_FREE && !certifCustomMotif.trim();
  const durationMissing = certificateRequiresDuration(certifType) && (!Number.isInteger(certifDays) || certifDays < 1);

  const certifTypes = [
    {
      id: CERTIFICATE_TYPE_WORK_STOP,
      label: 'Arrêt de travail',
      icon: <Clock size={14} />,
      description: 'Repos prescrit et daté par le praticien',
    },
    {
      id: CERTIFICATE_TYPE_PRESENCE,
      label: 'Présence au cabinet',
      icon: <CheckCircle2 size={14} />,
      description: 'Atteste une présence constatée par le praticien',
    },
    {
      id: CERTIFICATE_TYPE_FREE,
      label: 'Certificat médical',
      icon: <Edit3 size={14} />,
      description: 'Document libre rédigé par le praticien',
    },
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-4xl w-full mx-auto py-8">
      <div className="bg-white/40 backdrop-blur-xl rounded-[3rem] border border-white/60 p-10 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] -mr-32 -mt-32 rounded-full pointer-events-none" />

        <div className="relative z-10 space-y-10">
          <div>
            <div className="flex items-center justify-between mb-4 gap-4">
              <label className={labelClass + " mb-0"}>Nature du document</label>
              {suggestion && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl text-[9px] font-bold bg-amber-500/10 text-amber-700 border border-amber-200 max-w-sm"
                  role="status"
                  aria-live="polite"
                >
                  <AlertCircle size={12} className="shrink-0" />
                  <span>
                    Signal documentaire : {suggestion.reason || 'contexte détecté'}. Aucun choix n’est appliqué automatiquement ; le praticien décide du type, du contenu et, le cas échéant, de la durée.
                  </span>
                </motion.div>
              )}
            </div>

            <div className="flex flex-wrap justify-center gap-4">
              {certifTypes.map((type) => (
                <div key={type.id} className="flex flex-col items-center gap-2">
                  <button
                    type="button"
                    onClick={() => { markDirty(); setCertifType(type.id); }}
                    className={cn(
                      "flex items-center justify-center gap-3 px-6 py-4 rounded-[1.5rem] text-[10px] font-black uppercase tracking-widest transition-all border shadow-sm min-w-[180px]",
                      certifType === type.id
                        ? "bg-primary text-white border-primary shadow-xl shadow-primary/20"
                        : "bg-white text-slate-500 border-slate-100 hover:border-primary/30"
                    )}
                    style={certifType === type.id ? { backgroundColor: 'var(--primary)' } : {}}
                    aria-pressed={certifType === type.id}
                  >
                    <span className={cn(certifType === type.id ? "text-white" : "text-primary/40")}>{type.icon}</span>
                    {type.label}
                  </button>
                  <span className="text-[7px] font-black text-slate-300 uppercase tracking-widest text-center px-4 max-w-[210px]">
                    {type.description}
                  </span>
                </div>
              ))}
            </div>

            {!certifType && (
              <p className="mt-5 text-center text-[9px] font-bold text-slate-400">
                Aucun type sélectionné. Le praticien choisit explicitement la nature du certificat.
              </p>
            )}

            {certifType === CERTIFICATE_TYPE_FREE && (
              <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="mt-6">
                <label htmlFor="certificate-free-content" className={labelClass}>Contenu du certificat médical</label>
                <textarea
                  id="certificate-free-content"
                  className={cn(
                    inputClass,
                    "min-h-40 resize-y leading-relaxed",
                    freeContentMissing && "border-amber-200 focus:border-amber-400 focus:ring-amber-100",
                  )}
                  placeholder="Rédigez librement le contenu certifié par le praticien..."
                  value={certifCustomMotif}
                  onChange={(e) => { markDirty(); setCertifCustomMotif(e.target.value); }}
                  autoFocus
                  rows={6}
                  required
                  aria-required="true"
                  aria-invalid={freeContentMissing}
                  aria-describedby="certificate-free-content-help"
                />
                <p
                  id="certificate-free-content-help"
                  className={cn(
                    "mt-2 px-1 text-[9px] font-bold",
                    freeContentMissing ? "text-amber-600" : "text-slate-400",
                  )}
                >
                  {freeContentMissing
                    ? 'Contenu requis avant génération. Le logiciel ne complète jamais ce texte à la place du praticien.'
                    : 'Ce texte est repris tel quel dans le corps du certificat. Aucune suggestion clinique n’est injectée automatiquement.'}
                </p>
              </motion.div>
            )}
          </div>

          {certificateRequiresDuration(certifType) && (
            <div className="pt-8 border-t border-slate-100/50 space-y-6">
              <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_220px] sm:items-end">
                <div>
                  <label htmlFor="certificate-rest-days" className={labelClass + " mb-1"}>Durée du repos</label>
                  <p className="text-[9px] font-bold text-slate-400 italic">À saisir et valider par le praticien. Aucune durée n’est préremplie.</p>
                </div>
                <div>
                  <label htmlFor="certificate-rest-start" className={labelClass + " mb-1"}>Début du repos</label>
                  <input
                    id="certificate-rest-start"
                    type="date"
                    value={certifStartDate || docDate}
                    onChange={(e) => { markDirty(); setCertifStartDate(e.target.value); }}
                    className="w-full rounded-xl border border-slate-100 bg-white/70 px-4 py-3 text-sm font-bold text-slate-700 shadow-sm outline-none transition-all focus:border-primary focus:ring-4 focus:ring-primary/5"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between gap-4">
                <input
                  id="certificate-rest-days"
                  type="number"
                  min="1"
                  max="365"
                  step="1"
                  inputMode="numeric"
                  value={certifDays > 0 ? certifDays : ''}
                  placeholder="Saisir la durée"
                  onChange={(e) => {
                    markDirty();
                    const raw = e.target.value;
                    setCertifDays(raw === '' ? 0 : Number.parseInt(raw, 10));
                  }}
                  className={cn(
                    inputClass,
                    "max-w-xs",
                    durationMissing && "border-amber-200 focus:border-amber-400 focus:ring-amber-100",
                  )}
                  aria-label="Durée du repos en jours"
                  aria-required="true"
                  aria-invalid={durationMissing}
                />
                <span className="shrink-0 text-2xl font-black text-primary tracking-tighter" style={{ color: 'var(--primary)' }}>
                  {certifDays > 0
                    ? <>{certifDays} <span className="text-[10px] uppercase tracking-widest ml-1 opacity-40">jours</span></>
                    : <span className="text-sm uppercase tracking-widest opacity-40">Non définie</span>}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-center gap-2 text-slate-400">
        <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />
        <span className="text-[9px] font-black uppercase tracking-[0.3em]">Validation du praticien requise</span>
        <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />
      </div>
    </div>
  );
};
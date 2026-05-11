import React from 'react';
import { Plus, Trash2, Zap, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../../../utils/cn';

export interface DrugItem {
  id: number;
  name: string;
  dosage: string;
  forme: string;
  posologie: string;
  type?: 'MEDICAMENT' | 'EXAMEN';
  quantite?: number;
  non_substituable?: boolean;
}

import type { ValidationError, CoherenceWarning } from '../useDocumentGenerator';
import { AlertCircle, AlertTriangle } from 'lucide-react';

interface PrescriptionFormProps {
  drugs: DrugItem[];
  onAddDrug: () => void;
  onRemoveDrug: (id: number) => void;
  onUpdateDrug: (id: number, field: keyof DrugItem, value: string) => void;
  loadingSmart: boolean;
  smartSuggestion: any;
  onApplySmart: () => void;
  onApplyPreset: (preset: { label: string, color: string, drugs: any[] }) => void;
  validationErrors?: ValidationError[];
  coherenceWarnings?: CoherenceWarning[];
}

const QUICK_PRESCRIPTIONS = [
  { label: 'Post-Op Standard', color: 'rose', drugs: [
    { name: 'PARACETAMOL', dosage: '1g', forme: 'Gélules (Bte de 16)', posologie: '1 gel x 3 / jour pendant 4 jours' },
    { name: 'IBUPROFENE', dosage: '400mg', forme: 'Comprimés (Bte de 20)', posologie: '1 comp x 3 / jour si douleur' }
  ]},
  { label: 'Infection / Abcès', color: 'emerald', drugs: [
    { name: 'AMOXICILLINE', dosage: '1g', forme: 'Gélules (Bte de 12)', posologie: '1 gel Matin et Soir pendant 7 jours' },
    { name: 'METRONIDAZOLE', dosage: '500mg', forme: 'Comprimés (Bte de 20)', posologie: '1 comp x 3 / jour pendant 7 jours' }
  ]},
  { label: 'Parodontie', color: 'blue', drugs: [
    { name: 'BAIN DE BOUCHE', dosage: '0.12%', forme: 'Flacon', posologie: '2 rincages / jour pendant 10 jours' },
    { name: 'GEL BUCCAL', dosage: '-', forme: 'Tube', posologie: 'Application locale soir' }
  ]},
  { label: 'Urgence Douleur', color: 'amber', drugs: [
    { name: 'KETOPROFENE', dosage: '100mg', forme: 'Comprimés', posologie: '1 comp x 2 / jour au milieu des repas' }
  ]}
];

export const PrescriptionForm: React.FC<PrescriptionFormProps> = ({
  drugs,
  onAddDrug,
  onRemoveDrug,
  onUpdateDrug,
  loadingSmart,
  smartSuggestion,
  onApplySmart,
  onApplyPreset,
  validationErrors = [],
  coherenceWarnings = []
}) => {
  const inputClass = "w-full px-4 py-3 bg-white/70 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-300 shadow-sm font-medium text-slate-800";
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1";

  // Check for global drug errors
  const globalDrugError = validationErrors.find(e => e.field === 'drugs');
  // Check for antibiotic interaction
  const antibioticWarning = coherenceWarnings.find(w => w.message.includes('antibiotique'));

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* BARRE DE RACCOURCIS ELITE */}
      <div className="flex flex-wrap gap-3 p-5 bg-slate-50/50 rounded-[2rem] border border-slate-100 shadow-sm relative overflow-hidden group/bar">
        <div className="flex items-center gap-4 px-4 mr-2 border-r border-slate-200">
          <Zap size={16} className="text-primary" />
          <div className="hidden sm:block">
            <span className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400 block mb-1">Raccourcis</span>
            <span className="text-[10px] font-black uppercase tracking-widest text-primary">Protocoles Rapides</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 relative z-10">
          {QUICK_PRESCRIPTIONS.map(preset => (
            <button
              key={preset.label}
              onClick={() => onApplyPreset(preset)}
              className={cn(
                "group px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 border flex items-center gap-2",
                preset.color === 'rose' ? "bg-rose-50 border-rose-100 text-rose-600 hover:bg-rose-600 hover:text-white" :
                preset.color === 'emerald' ? "bg-emerald-50 border-emerald-100 text-emerald-600 hover:bg-emerald-600 hover:text-white" :
                preset.color === 'blue' ? "bg-blue-50 border-blue-100 text-blue-600 hover:bg-blue-600 hover:text-white" :
                "bg-amber-50 border-amber-100 text-amber-600 hover:bg-amber-600 hover:text-white"
              )}
            >
              <div className="w-1.5 h-1.5 rounded-full bg-current opacity-40 group-hover:opacity-100" />
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <AnimatePresence>
        {(loadingSmart || (smartSuggestion && !smartSuggestion.applied)) && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <div className="bg-primary/5 border border-primary/10 rounded-[1.5rem] p-4 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center text-primary">
                  {loadingSmart ? <Loader2 className="animate-spin" size={20} /> : <Zap size={20} />}
                </div>
                <div>
                  <h4 className="text-sm font-black text-primary uppercase tracking-tight">
                    {loadingSmart ? "Analyse du dossier..." : "Suggestion IA"}
                  </h4>
                  <p className="text-xs text-slate-500 font-medium">
                    {loadingSmart ? "Recherche du meilleur protocole..." : <>Protocole détecté : <span className="font-bold text-primary">{smartSuggestion?.protocol_name}</span></>}
                  </p>
                </div>
              </div>
              {smartSuggestion && !smartSuggestion.applied && !loadingSmart && (
                <button onClick={onApplySmart} className="px-5 py-2 bg-primary text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-primary/20 hover:scale-105 transition-all">Appliquer</button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="space-y-4">
        {/* Global Errors */}
        {globalDrugError && (
          <div className="px-4 py-2 bg-red-50 border border-red-200 rounded-xl text-xs text-red-600 font-bold flex items-center gap-2 animate-in slide-in-from-top-2">
            <AlertCircle size={14} /> {globalDrugError.message}
          </div>
        )}
        {antibioticWarning && (
          <div className="px-4 py-2 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-600 font-bold flex items-center gap-2 animate-in slide-in-from-top-2">
            <AlertTriangle size={14} /> {antibioticWarning.message}
          </div>
        )}

        <div className="grid grid-cols-12 gap-4 px-4">
          <div className="col-span-4"><label className={labelClass}>Médicament</label></div>
          <div className="col-span-3"><label className={labelClass}>Dosage</label></div>
          <div className="col-span-4"><label className={labelClass}>Posologie</label></div>
        </div>
        <div className="space-y-4">
          {drugs.map((drug, idx) => {
            const fieldError = validationErrors.find(e => e.field === `drug_${idx}`);
            return (
              <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} key={drug.id} className={cn(
                "bg-white/40 p-5 rounded-[2rem] border transition-all group relative",
                fieldError ? "border-red-200 bg-red-50/20" : "border-white/60 hover:bg-white/80"
              )}>
                <div className="grid grid-cols-12 gap-6 items-start">
                  <div className="col-span-4">
                    <input 
                      type="text" 
                      className={cn(inputClass, "font-black text-primary text-base", fieldError && "border-red-300 focus:ring-red-200")} 
                      style={{ color: 'var(--primary)' }} 
                      placeholder="MÉDICAMENT..." 
                      value={drug.name} 
                      onChange={(e) => onUpdateDrug(drug.id, 'name', e.target.value.toUpperCase())} 
                    />
                  </div>
                  <div className="col-span-3">
                    <input type="text" className={inputClass} placeholder="Dose (ex: 1g, 500mg...)" value={drug.dosage} onChange={(e) => onUpdateDrug(drug.id, 'dosage', e.target.value)} />
                  </div>
                  <div className="col-span-4">
                    <div className="relative">
                      <input type="text" className={cn(inputClass, fieldError && "border-red-300 focus:ring-red-200")} placeholder="Posologie (ex: 1x3/jour...)" value={drug.posologie} onChange={(e) => onUpdateDrug(drug.id, 'posologie', e.target.value)} />
                      {fieldError && (
                        <div className="absolute -bottom-5 left-1 text-[9px] font-black text-red-500 uppercase tracking-widest flex items-center gap-1">
                          <AlertCircle size={10} /> Posologie Requise
                        </div>
                      )}
                    </div>
                  </div>
                <div className="col-span-1 flex justify-center pt-3">
                  <button onClick={() => onRemoveDrug(drug.id)} className="p-2 text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"><Trash2 size={18} /></button>
                </div>
              </div>

              {/* STUDIO DE FORME ELITE v2.0 */}
              <div className="mt-6 p-4 bg-slate-50/50 rounded-2xl border border-slate-100/50 relative overflow-hidden group/form">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                    <Zap size={12} className="text-primary" /> Architecture de la Forme
                  </span>
                  <div className="flex gap-1">
                    {['12', '16', '20', '30'].map(q => {
                      const isSelected = drug.forme.includes(`Bte de ${q}`);
                      return (
                        <button
                          key={q}
                          onClick={() => {
                            const base = drug.forme.split(' (')[0] || 'Comprimés';
                            onUpdateDrug(drug.id, 'forme', `${base} (Bte de ${q})`);
                          }}
                          className={cn(
                            "px-2 py-1 rounded-md text-[9px] font-black transition-all border",
                            isSelected 
                              ? "bg-emerald-600 text-white border-emerald-500 shadow-sm" 
                              : "bg-white text-slate-400 border-slate-200 hover:border-primary/30 hover:text-primary"
                          )}
                        >
                          {q}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  {[
                    { label: 'Sachets', icon: '📦' },
                    { label: 'Comprimés', icon: '💊' },
                    { label: 'Gélules', icon: '💊' },
                    { label: 'Flacon', icon: '🧪' },
                    { label: 'Bain de bouche', icon: '🧴' },
                    { label: 'Gel buccal', icon: '🧪' },
                    { label: 'Spray', icon: '💨' },
                    { label: 'Autre', icon: '📝' }
                  ].map(f => {
                    const isSelected = drug.forme.startsWith(f.label);
                    return (
                      <button
                        key={f.label}
                        onClick={() => {
                          const suffix = drug.forme.includes(' (Bte') ? ` (${drug.forme.split(' (')[1]}` : "";
                          onUpdateDrug(drug.id, 'forme', f.label + suffix);
                        }}
                        className={cn(
                          "group/btn flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] font-bold transition-all border relative",
                          isSelected
                            ? "bg-white text-primary border-primary shadow-md shadow-primary/10 ring-2 ring-primary/5"
                            : "bg-white/50 text-slate-500 border-slate-200 hover:border-primary/40 hover:bg-white"
                        )}
                      >
                        <span className={cn("text-xs transition-transform", isSelected ? "scale-110" : "grayscale")}>{f.icon}</span>
                        {f.label}
                        {isSelected && <motion.div layoutId={`active-forme-${drug.id}`} className="absolute -top-1 -right-1 w-2 h-2 bg-primary rounded-full shadow-[0_0_8px_var(--primary)]" />}
                      </button>
                    );
                  })}
                </div>

                {drug.forme.startsWith('Autre') && (
                  <motion.div 
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 px-2 pb-2"
                  >
                    <input
                      type="text"
                      className={cn(inputClass, "bg-white border-primary/20 text-primary font-bold h-10")}
                      placeholder="Précisez la forme (ex: Radio, Analyse...)"
                      value={drug.forme.includes(':') ? drug.forme.split(':')[1].trim() : ''}
                      onChange={(e) => onUpdateDrug(drug.id, 'forme', `Autre: ${e.target.value}`)}
                    />
                  </motion.div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
        <button onClick={onAddDrug} className="w-full py-4 border-2 border-dashed border-slate-200 text-slate-400 rounded-2xl flex items-center justify-center gap-2 hover:border-primary hover:text-primary hover:bg-primary/5 transition-all font-bold mt-2"><Plus size={18} /> Ajouter une prescription</button>
      </div>
    </div>
  );
};

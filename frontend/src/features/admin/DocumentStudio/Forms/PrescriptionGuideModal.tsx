import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Stethoscope } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import toast from 'react-hot-toast';
import { MOROCCAN_CLINICAL_RULES, getAgeAwareDosing, estimateWeightFromAge, resolveRule } from '../clinical_rules';
import type { DrugItem } from './prescriptionTypes';

interface NationalMed {
  nom: string;
  dci: string;
  dosage: string;
  unite: string;
  forme: string;
}

interface PrescriptionGuideModalProps {
  show: boolean;
  onClose: () => void;
  guideAge: number;
  setGuideAge: (age: number) => void;
  guideWeight: number;
  setGuideWeight: (w: number) => void;
  guideCategory: string;
  setGuideCategory: (cat: string) => void;
  guideSearch: string;
  setGuideSearch: (s: string) => void;
  guideNationalResults: NationalMed[];
  guideSearching: boolean;
  setGuideSearching: (v: boolean) => void;
  onNationalSearch: (q: string) => void;
  assessment: any;
  onAddMolecule: (name: string, dosage?: string, posologie?: string, forme?: string) => void;
}

const CATEGORIES = ['TOUS', 'Antalgiques', 'AINS', 'Antibiotiques', 'Corticoïdes', 'Antiseptiques', 'Antifongiques'];

export const PrescriptionGuideModal: React.FC<PrescriptionGuideModalProps> = ({
  show, onClose, guideAge, setGuideAge, guideWeight, setGuideWeight,
  guideCategory, setGuideCategory, guideSearch, setGuideSearch,
  guideNationalResults, guideSearching, setGuideSearching,
  onNationalSearch, assessment, onAddMolecule,
}) => {
  const patientHist = (assessment?.patient_context?.antecedents || assessment?.antecedents || '').toUpperCase();

  const getPatientCI = (contraindications: string[]) =>
    patientHist.trim()
      ? contraindications.filter(ci => {
          const tokens = ci.split(/\s+/).filter(t => t.length > 3);
          return tokens.length > 0 && tokens.every(t => patientHist.includes(t));
        })
      : [];

  return (
    <AnimatePresence>
      {show && (
        <div className="fixed inset-0 z-[40000] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 bg-slate-900/60 backdrop-blur-md"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="relative bg-white rounded-[2rem] p-6 w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
          >
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 bg-indigo-500/10 text-indigo-600 rounded-2xl flex items-center justify-center">
                <Stethoscope size={24} />
              </div>
              <div>
                <h3 className="text-xl font-black text-slate-800 tracking-tight">Guide de Prescription</h3>
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mt-1">
                  Tous les médicaments · Posologies · Maroc
                </p>
              </div>
              <button
                onClick={onClose}
                className="ml-auto w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-600 bg-slate-100 rounded-full"
              >
                ×
              </button>
            </div>

            {/* Age / Weight */}
            <div className="flex gap-4 mb-4 p-4 bg-slate-50 rounded-2xl border border-slate-100">
              <div className="flex-1">
                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest block mb-2">
                  Âge du patient (ans) <span className="text-indigo-400 normal-case">· ≥15 = dose adulte</span>
                </label>
                <input
                  type="number" min={0} value={guideAge}
                  onChange={e => {
                    const a = Number(e.target.value);
                    setGuideAge(a);
                    if (a > 0 && a < 15) setGuideWeight(estimateWeightFromAge(a));
                  }}
                  className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2 font-bold focus:border-indigo-500 outline-none"
                />
              </div>
              <div className="flex-1">
                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest block mb-2">
                  Poids (kg){guideAge < 15 && <span className="text-indigo-400 normal-case"> · auto depuis l'âge</span>}
                </label>
                <input
                  type="number" min={0} value={guideWeight}
                  onChange={e => setGuideWeight(Number(e.target.value))}
                  className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2 font-bold focus:border-indigo-500 outline-none"
                />
              </div>
            </div>

            {/* Search + categories */}
            <div className="mb-4 space-y-3">
              <input
                type="text" value={guideSearch}
                onChange={e => {
                  const v = e.target.value;
                  setGuideSearch(v);
                  setGuideSearching(v.trim().length >= 2);
                  onNationalSearch(v);
                }}
                placeholder="Rechercher dans tous les médicaments (nom ou molécule)…"
                className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2 text-sm font-semibold focus:border-indigo-500 outline-none"
              />
              {!guideSearch.trim() && (
                <div className="flex flex-wrap gap-2">
                  {CATEGORIES.map(cat => (
                    <button
                      key={cat}
                      onClick={() => setGuideCategory(cat)}
                      className={cn(
                        'px-3 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest transition-all',
                        guideCategory === cat ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-100 text-slate-500 hover:bg-slate-200',
                      )}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              )}
              {guideSearch.trim().length >= 2 && (
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  Dictionnaire national · {guideSearching ? 'recherche…' : `${guideNationalResults.length} résultat(s)`}
                </p>
              )}
            </div>

            {/* Results list */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin">
              {guideSearch.trim().length >= 2 ? (
                guideNationalResults.length === 0 ? (
                  <div className="py-10 text-center text-slate-400 text-sm font-bold">
                    {guideSearching ? 'Recherche…' : 'Aucun médicament trouvé dans le dictionnaire national.'}
                  </div>
                ) : (
                  guideNationalResults.map((med, mi) => {
                    const dosing = getAgeAwareDosing(med.nom, guideAge, guideWeight);
                    const rule = resolveRule(med.nom);
                    const patientCI = rule ? getPatientCI(rule.contraindications) : [];
                    const natDose = `${med.dosage}${med.unite ? ' ' + med.unite : ''}`.trim();
                    return (
                      <div
                        key={`${med.nom}-${mi}`}
                        className={cn(
                          'p-4 border rounded-2xl transition-all flex items-start justify-between group',
                          patientCI.length > 0 ? 'border-red-200 bg-red-50/40' : 'border-slate-100 hover:border-indigo-100 hover:bg-indigo-50/30',
                        )}
                      >
                        <div className="space-y-1 pr-4">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className="font-bold text-slate-800 text-sm">{med.nom}</h4>
                            {med.dci && (
                              <span className="bg-slate-100 text-slate-500 text-[9px] px-2 py-0.5 rounded-full font-black uppercase">
                                {med.dci}
                              </span>
                            )}
                            {rule
                              ? <span className="bg-emerald-100 text-emerald-700 text-[9px] px-2 py-0.5 rounded-full font-black">POSOLOGIE DISPO</span>
                              : <span className="bg-slate-100 text-slate-400 text-[9px] px-2 py-0.5 rounded-full font-black">RÉFÉRENCE</span>}
                            {patientCI.length > 0 && (
                              <span className="bg-red-500 text-white text-[9px] px-2 py-0.5 rounded-full font-black">⚠ CONCERNE CE PATIENT</span>
                            )}
                          </div>
                          <div className="text-xs text-slate-600">
                            {natDose && <span className="font-bold text-slate-800">{natDose}</span>}
                            {med.forme ? ` · ${med.forme}` : ''}
                          </div>
                          {dosing
                            ? <div className="text-xs text-indigo-700"><span className="font-bold">{dosing.dosage}</span> — {dosing.posology}{dosing.pediatric ? ` (≈ ${dosing.weight} kg)` : ''}</div>
                            : <div className="text-[10px] text-slate-400 italic">Posologie pédiatrique à définir (hors référentiel clinique).</div>}
                          {rule?.notes && <div className="text-[10px] text-slate-500 font-semibold italic">{rule.notes}</div>}
                          {rule && (
                            <div className={cn('text-[9px] font-medium uppercase mt-1', patientCI.length > 0 ? 'text-red-600 font-black' : 'text-rose-500')}>
                              Contre-indications: {rule.contraindications.join(' • ')}
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => {
                            if (dosing) onAddMolecule(med.nom, dosing.dosage, dosing.posology, med.forme);
                            else onAddMolecule(med.nom, natDose, '', med.forme);
                            onClose();
                            toast.success(`${med.nom} ajouté.`);
                          }}
                          className="opacity-0 group-hover:opacity-100 w-8 h-8 shrink-0 bg-indigo-500 text-white rounded-xl flex items-center justify-center hover:bg-indigo-600 transition-all shadow-md"
                          title="Ajouter à l'ordonnance"
                        >
                          <Plus size={16} />
                        </button>
                      </div>
                    );
                  })
                )
              ) : (() => {
                const rules = Object.values(MOROCCAN_CLINICAL_RULES).filter(r =>
                  guideCategory === 'TOUS' || r.category === guideCategory,
                );
                if (rules.length === 0) {
                  return <div className="py-10 text-center text-slate-400 text-sm font-bold">Aucune molécule pour ce filtre.</div>;
                }
                return rules.map(rule => {
                  const ped = rule.pediatric_calc(guideWeight);
                  const patientCI = getPatientCI(rule.contraindications);
                  return (
                    <div
                      key={rule.molecule}
                      className={cn(
                        'p-4 border rounded-2xl transition-all flex items-start justify-between group',
                        patientCI.length > 0 ? 'border-red-200 bg-red-50/40' : 'border-slate-100 hover:border-indigo-100 hover:bg-indigo-50/30',
                      )}
                    >
                      <div className="space-y-1 pr-4">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-bold text-slate-800 text-sm">{rule.molecule}</h4>
                          <span className="bg-slate-100 text-slate-500 text-[9px] px-2 py-0.5 rounded-full font-black uppercase">
                            {rule.category}
                          </span>
                          {guideAge < 15 && (
                            <span className="bg-amber-100 text-amber-700 text-[9px] px-2 py-0.5 rounded-full font-black">PÉDIATRIE</span>
                          )}
                          {patientCI.length > 0 && (
                            <span className="bg-red-500 text-white text-[9px] px-2 py-0.5 rounded-full font-black">⚠ CONCERNE CE PATIENT</span>
                          )}
                        </div>
                        {guideAge >= 15 ? (
                          <div className="text-xs text-slate-600">
                            <span className="font-bold text-slate-800">{rule.adult_dose}</span> — {rule.adult_posology}
                          </div>
                        ) : (
                          <div className="text-xs text-indigo-700">
                            <span className="font-bold">{ped.dosage}</span> — {ped.posology}
                          </div>
                        )}
                        {rule.notes && (
                          <div className="text-[10px] text-slate-500 font-semibold mt-1 italic">{rule.notes}</div>
                        )}
                        <div className={cn('text-[9px] font-medium uppercase mt-2', patientCI.length > 0 ? 'text-red-600 font-black' : 'text-rose-500')}>
                          Contre-indications: {rule.contraindications.join(' • ')}
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          const dose = guideAge >= 15 ? rule.adult_dose : ped.dosage;
                          const poso = guideAge >= 15 ? rule.adult_posology : ped.posology;
                          onAddMolecule(rule.molecule, dose, poso);
                          onClose();
                          toast.success(`${rule.molecule} ajouté.`);
                        }}
                        className="opacity-0 group-hover:opacity-100 w-8 h-8 shrink-0 bg-indigo-500 text-white rounded-xl flex items-center justify-center hover:bg-indigo-600 transition-all shadow-md"
                        title="Ajouter à l'ordonnance"
                      >
                        <Plus size={16} />
                      </button>
                    </div>
                  );
                });
              })()}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

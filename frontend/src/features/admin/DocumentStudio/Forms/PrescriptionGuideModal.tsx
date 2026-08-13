import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, Plus, Search, Stethoscope, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { cn } from '../../../../utils/cn';
import { MOROCCAN_CLINICAL_RULES, getAgeAwareDosing, resolveRule } from '../clinical_rules';

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
const FORMES_RAPIDES = ['Comprimés', 'Gélules', 'Sachets', 'Sirop', 'Flacon', 'Pommade', 'Spray', 'Ampoules'];
const emptyCustom = { name: '', dosage: '', posologie: '', forme: 'Comprimés' };

export const PrescriptionGuideModal: React.FC<PrescriptionGuideModalProps> = ({
  show, onClose, guideAge, setGuideAge, guideWeight, setGuideWeight,
  guideCategory, setGuideCategory, guideSearch, setGuideSearch,
  guideNationalResults, guideSearching, setGuideSearching,
  onNationalSearch, assessment, onAddMolecule,
}) => {
  const [custom, setCustom] = useState(emptyCustom);
  const [editingPoso, setEditingPoso] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!show) return;
    const age = assessment?.patient_context?.age ?? assessment?.age;
    const weight = assessment?.patient_context?.weight ?? assessment?.weight ?? assessment?.poids;
    setGuideAge(typeof age === 'number' && Number.isFinite(age) && age > 0 ? age : 0);
    setGuideWeight(typeof weight === 'number' && Number.isFinite(weight) && weight > 0 ? weight : 0);
  }, [show, assessment, setGuideAge, setGuideWeight]);

  const patientHist = (
    assessment?.patient_context?.antecedents || assessment?.antecedents || ''
  ).toUpperCase();
  const isChild = guideAge > 0 && guideAge < 15;
  const hasExplicitWeight = guideWeight > 0 && Number.isFinite(guideWeight);
  const childContextIncomplete = isChild && !hasExplicitWeight;

  const getPatientCI = (contraindications: string[]) =>
    patientHist.trim()
      ? contraindications.filter(ci => {
          const tokens = ci.split(/\s+/).filter(t => t.length > 3);
          return tokens.length > 0 && tokens.every(t => patientHist.includes(t));
        })
      : [];

  const addCustom = () => {
    if (!custom.name.trim()) return;
    onAddMolecule(
      custom.name.trim().toUpperCase(),
      custom.dosage.trim(),
      custom.posologie.trim(),
      custom.forme,
    );
    setCustom(emptyCustom);
    onClose();
  };

  const addFromList = (
    key: string,
    name: string,
    dosage: string,
    defaultPoso: string,
    forme?: string,
  ) => {
    const poso = editingPoso[key] ?? defaultPoso;
    onAddMolecule(name, dosage, poso, forme);
    toast.success(`${name} ajouté.`);
    onClose();
  };

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
            initial={{ opacity: 0, scale: 0.96, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 12 }}
            className="relative bg-white rounded-[2rem] w-full max-w-2xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
          >
            <div className="flex items-center gap-4 p-6 border-b border-slate-100">
              <div className="w-12 h-12 bg-indigo-500/10 text-indigo-600 rounded-2xl flex items-center justify-center">
                <Stethoscope size={24} />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-black text-slate-800">Référentiel Médicaments</h3>
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Données explicites uniquement</p>
              </div>
              <button onClick={onClose} className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                <X size={16} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              <div className="grid grid-cols-2 gap-3 p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest">
                  Âge (ans)
                  <input
                    type="number" min={0} value={guideAge || ''}
                    onChange={e => setGuideAge(Number(e.target.value) || 0)}
                    className="mt-1.5 w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-sm font-bold outline-none"
                  />
                </label>
                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest">
                  Poids réel (kg)
                  <input
                    type="number" min={0} step="0.1" value={guideWeight || ''}
                    onChange={e => setGuideWeight(Number(e.target.value) || 0)}
                    className="mt-1.5 w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-sm font-bold outline-none"
                  />
                </label>
              </div>

              {childContextIncomplete && (
                <div className="flex gap-3 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800">
                  <AlertCircle size={18} className="shrink-0 mt-0.5" />
                  <p className="text-xs font-bold">Poids réel requis. Aucun calcul automatique n'est affiché tant que cette donnée manque.</p>
                </div>
              )}

              <div className="bg-indigo-50/60 border border-indigo-100 rounded-2xl p-4 space-y-3">
                <p className="text-[10px] font-black text-indigo-600 uppercase tracking-widest">Ajout manuel</p>
                <input
                  value={custom.name}
                  onChange={e => setCustom(p => ({ ...p, name: e.target.value }))}
                  placeholder="Nom"
                  className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-bold"
                />
                <div className="grid grid-cols-2 gap-2">
                  <input value={custom.dosage} onChange={e => setCustom(p => ({ ...p, dosage: e.target.value }))} placeholder="Dosage" className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm" />
                  <input value={custom.posologie} onChange={e => setCustom(p => ({ ...p, posologie: e.target.value }))} placeholder="Posologie" className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm" />
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {FORMES_RAPIDES.map(f => (
                    <button key={f} onClick={() => setCustom(p => ({ ...p, forme: f }))} className={cn('px-3 py-1 rounded-lg text-[10px] font-black border', custom.forme === f ? 'bg-indigo-600 text-white' : 'bg-white text-slate-500')}>
                      {f}
                    </button>
                  ))}
                </div>
                <button onClick={addCustom} disabled={!custom.name.trim()} className="w-full py-3 bg-indigo-600 disabled:opacity-40 text-white rounded-xl text-xs font-black uppercase tracking-widest">
                  <Plus size={15} className="inline mr-2" />Ajouter
                </button>
              </div>

              <div className="relative">
                <Search size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  value={guideSearch}
                  onChange={e => {
                    const value = e.target.value;
                    setGuideSearch(value);
                    setGuideSearching(value.trim().length >= 2);
                    onNationalSearch(value);
                  }}
                  placeholder="Rechercher…"
                  className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm"
                />
              </div>

              {!guideSearch.trim() && (
                <div className="flex flex-wrap gap-2">
                  {CATEGORIES.map(cat => (
                    <button key={cat} onClick={() => setGuideCategory(cat)} className={cn('px-3 py-1.5 rounded-full text-[10px] font-black', guideCategory === cat ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500')}>
                      {cat}
                    </button>
                  ))}
                </div>
              )}

              <div className="space-y-2">
                {guideSearch.trim().length >= 2 ? (
                  guideSearching ? <p className="text-sm text-slate-400">Recherche…</p> :
                  guideNationalResults.map((med, index) => {
                    const key = `national-${index}-${med.nom}`;
                    const dosing = childContextIncomplete ? null : getAgeAwareDosing(med.nom, guideAge, guideWeight || undefined);
                    const defaultPoso = dosing?.posology || '';
                    return (
                      <SafeRow
                        key={key}
                        name={med.nom}
                        subtitle={med.dci}
                        dosage={`${med.dosage}${med.unite ? ` ${med.unite}` : ''}`.trim()}
                        posologie={editingPoso[key] ?? defaultPoso}
                        disabled={false}
                        onPosoChange={v => setEditingPoso(p => ({ ...p, [key]: v }))}
                        onAdd={() => addFromList(key, med.nom, `${med.dosage}${med.unite ? ` ${med.unite}` : ''}`.trim(), defaultPoso, med.forme)}
                      />
                    );
                  })
                ) : Object.values(MOROCCAN_CLINICAL_RULES)
                    .filter(rule => guideCategory === 'TOUS' || rule.category === guideCategory)
                    .map(rule => {
                      const key = `rule-${rule.molecule}`;
                      const dosing = childContextIncomplete ? null : getAgeAwareDosing(rule.molecule, guideAge, guideWeight || undefined);
                      const disabled = guideAge <= 0 || childContextIncomplete || !dosing;
                      const patientCI = getPatientCI(resolveRule(rule.molecule)?.contraindications || []);
                      return (
                        <SafeRow
                          key={key}
                          name={rule.molecule}
                          subtitle={patientCI.length ? 'Vigilance dossier' : rule.category}
                          dosage={dosing?.dosage || ''}
                          posologie={editingPoso[key] ?? dosing?.posology ?? ''}
                          disabled={disabled}
                          onPosoChange={v => setEditingPoso(p => ({ ...p, [key]: v }))}
                          onAdd={() => addFromList(key, rule.molecule, dosing?.dosage || '', dosing?.posology || '')}
                        />
                      );
                    })}
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

const SafeRow: React.FC<{
  name: string;
  subtitle?: string;
  dosage: string;
  posologie: string;
  disabled: boolean;
  onPosoChange: (value: string) => void;
  onAdd: () => void;
}> = ({ name, subtitle, dosage, posologie, disabled, onPosoChange, onAdd }) => (
  <div className="p-4 border border-slate-100 rounded-2xl">
    <div className="flex items-center justify-between gap-3 mb-2">
      <div>
        <h4 className="font-black text-slate-800 text-sm">{name}</h4>
        {subtitle && <p className="text-[10px] text-slate-400 font-bold">{subtitle}</p>}
      </div>
      <button disabled={disabled} onClick={onAdd} className="w-9 h-9 rounded-xl bg-indigo-600 disabled:bg-slate-200 text-white flex items-center justify-center">
        <Plus size={16} />
      </button>
    </div>
    {disabled && <p className="text-[10px] text-amber-700 font-bold mb-2">Données requises manquantes. Ajout automatique désactivé.</p>}
    {dosage && <p className="text-xs font-bold text-slate-700 mb-2">{dosage}</p>}
    <input value={posologie} onChange={e => onPosoChange(e.target.value)} placeholder="Posologie" className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs" />
  </div>
);

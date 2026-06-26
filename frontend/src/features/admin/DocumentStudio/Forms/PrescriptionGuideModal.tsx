import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Stethoscope, X, Search, AlertCircle } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import toast from 'react-hot-toast';
import { MOROCCAN_CLINICAL_RULES, getAgeAwareDosing, estimateWeightFromAge, resolveRule } from '../clinical_rules';

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
  // Per-row editable posologie before adding
  const [editingPoso, setEditingPoso] = useState<Record<string, string>>({});

  const patientHist = (assessment?.patient_context?.antecedents || assessment?.antecedents || '').toUpperCase();

  const getPatientCI = (contraindications: string[]) =>
    patientHist.trim()
      ? contraindications.filter(ci => {
          const tokens = ci.split(/\s+/).filter(t => t.length > 3);
          return tokens.length > 0 && tokens.every(t => patientHist.includes(t));
        })
      : [];

  const addCustom = () => {
    if (!custom.name.trim()) { toast.error('Saisissez un nom de médicament.'); return; }
    onAddMolecule(custom.name.trim().toUpperCase(), custom.dosage.trim(), custom.posologie.trim(), custom.forme);
    toast.success(`${custom.name.trim().toUpperCase()} ajouté.`);
    setCustom(emptyCustom);
    onClose();
  };

  const addFromList = (key: string, name: string, dosage: string, defaultPoso: string, forme?: string) => {
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
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="relative bg-white rounded-[2rem] w-full max-w-2xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
          >
            {/* ── Header ── */}
            <div className="flex items-center gap-4 p-6 border-b border-slate-100">
              <div className="w-12 h-12 bg-indigo-500/10 text-indigo-600 rounded-2xl flex items-center justify-center shrink-0">
                <Stethoscope size={24} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-black text-slate-800">Référentiel Médicaments</h3>
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">
                  Recherche · Posologies · Ajout libre
                </p>
              </div>
              <button
                onClick={onClose}
                className="w-9 h-9 flex items-center justify-center text-slate-400 hover:text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-full transition-all"
              >
                <X size={16} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">

              {/* ── SAISIE LIBRE ── */}
              <div className="bg-indigo-50/60 border border-indigo-100 rounded-2xl p-4 space-y-3">
                <p className="text-[10px] font-black text-indigo-600 uppercase tracking-widest">
                  ✏️ Ajouter un médicament libre
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="Nom du médicament *"
                    value={custom.name}
                    onChange={e => setCustom(p => ({ ...p, name: e.target.value }))}
                    className="col-span-2 bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-bold focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition-all placeholder:text-slate-300"
                  />
                  <input
                    type="text"
                    placeholder="Dosage (ex: 500mg, 1g…)"
                    value={custom.dosage}
                    onChange={e => setCustom(p => ({ ...p, dosage: e.target.value }))}
                    className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-semibold focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition-all placeholder:text-slate-300"
                  />
                  <input
                    type="text"
                    placeholder="Posologie (ex: 1cp x 3/j…)"
                    value={custom.posologie}
                    onChange={e => setCustom(p => ({ ...p, posologie: e.target.value }))}
                    className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-semibold focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition-all placeholder:text-slate-300"
                  />
                </div>
                {/* Forme rapide */}
                <div className="flex flex-wrap gap-1.5">
                  {FORMES_RAPIDES.map(f => (
                    <button
                      key={f}
                      onClick={() => setCustom(p => ({ ...p, forme: f }))}
                      className={cn(
                        'px-3 py-1 rounded-lg text-[10px] font-black transition-all border',
                        custom.forme === f
                          ? 'bg-indigo-600 text-white border-indigo-500 shadow-sm'
                          : 'bg-white text-slate-500 border-slate-200 hover:border-indigo-300 hover:text-indigo-600',
                      )}
                    >
                      {f}
                    </button>
                  ))}
                </div>
                <button
                  onClick={addCustom}
                  disabled={!custom.name.trim()}
                  className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl text-[11px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 shadow-md shadow-indigo-200"
                >
                  <Plus size={16} /> Ajouter à l'ordonnance
                </button>
              </div>

              {/* ── Age / Poids ── */}
              <div className="flex gap-3 p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <div className="flex-1">
                  <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest block mb-1.5">
                    Âge (ans) <span className="text-indigo-400 normal-case">· ≥15 = adulte</span>
                  </label>
                  <input
                    type="number" min={0} value={guideAge}
                    onChange={e => {
                      const a = Number(e.target.value);
                      setGuideAge(a);
                      if (a > 0 && a < 15) setGuideWeight(estimateWeightFromAge(a));
                    }}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 font-bold focus:border-indigo-400 outline-none text-sm"
                  />
                </div>
                <div className="flex-1">
                  <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest block mb-1.5">
                    Poids (kg){guideAge < 15 && <span className="text-indigo-400 normal-case"> · estimé</span>}
                  </label>
                  <input
                    type="number" min={0} value={guideWeight}
                    onChange={e => setGuideWeight(Number(e.target.value))}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 font-bold focus:border-indigo-400 outline-none text-sm"
                  />
                </div>
              </div>

              {/* ── Recherche + catégories ── */}
              <div className="space-y-3">
                <div className="relative">
                  <Search size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text" value={guideSearch}
                    onChange={e => {
                      const v = e.target.value;
                      setGuideSearch(v);
                      setGuideSearching(v.trim().length >= 2);
                      onNationalSearch(v);
                    }}
                    placeholder="Rechercher un médicament ou une molécule…"
                    className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm font-semibold focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition-all"
                  />
                </div>
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
                    {guideSearching ? 'Recherche…' : `${guideNationalResults.length} résultat(s) — dictionnaire national`}
                  </p>
                )}
              </div>

              {/* ── Liste résultats ── */}
              <div className="space-y-2">
                {guideSearch.trim().length >= 2 ? (
                  guideNationalResults.length === 0 ? (
                    <div className="py-10 text-center text-slate-400 text-sm font-bold">
                      {guideSearching ? 'Recherche…' : 'Aucun médicament trouvé.'}
                    </div>
                  ) : (
                    guideNationalResults.map((med, mi) => {
                      const dosing = getAgeAwareDosing(med.nom, guideAge, guideWeight);
                      const rule = resolveRule(med.nom);
                      const patientCI = rule ? getPatientCI(rule.contraindications) : [];
                      const natDose = `${med.dosage}${med.unite ? ' ' + med.unite : ''}`.trim();
                      const key = `nat-${med.nom}-${mi}`;
                      const defaultPoso = dosing ? dosing.posology : '';
                      return (
                        <MedRow
                          key={key}
                          rowKey={key}
                          name={med.nom}
                          dci={med.dci}
                          dosage={natDose}
                          posologie={editingPoso[key] ?? defaultPoso}
                          forme={med.forme}
                          badge={rule ? 'POSOLOGIE DISPO' : 'RÉFÉRENCE'}
                          badgeColor={rule ? 'emerald' : 'slate'}
                          notes={rule?.notes}
                          contraindications={rule?.contraindications}
                          patientCI={patientCI}
                          isPediatric={guideAge < 15}
                          onPosoChange={v => setEditingPoso(p => ({ ...p, [key]: v }))}
                          onAdd={() => addFromList(key, med.nom, natDose, defaultPoso, med.forme)}
                        />
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
                    const dose = guideAge >= 15 ? rule.adult_dose : ped.dosage;
                    const defaultPoso = guideAge >= 15 ? rule.adult_posology : ped.posology;
                    const key = `rule-${rule.molecule}`;
                    return (
                      <MedRow
                        key={key}
                        rowKey={key}
                        name={rule.molecule}
                        dosage={dose}
                        posologie={editingPoso[key] ?? defaultPoso}
                        badge={rule.category}
                        badgeColor="slate"
                        notes={rule.notes}
                        contraindications={rule.contraindications}
                        patientCI={patientCI}
                        isPediatric={guideAge < 15}
                        onPosoChange={v => setEditingPoso(p => ({ ...p, [key]: v }))}
                        onAdd={() => addFromList(key, rule.molecule, dose, defaultPoso)}
                      />
                    );
                  });
                })()}
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

/* ── Row réutilisable avec posologie éditable ── */
interface MedRowProps {
  rowKey: string;
  name: string;
  dci?: string;
  dosage: string;
  posologie: string;
  forme?: string;
  badge: string;
  badgeColor: 'emerald' | 'slate' | 'amber';
  notes?: string;
  contraindications?: string[];
  patientCI: string[];
  isPediatric: boolean;
  onPosoChange: (v: string) => void;
  onAdd: () => void;
}

const MedRow: React.FC<MedRowProps> = ({
  name, dci, dosage, posologie, forme, badge, badgeColor, notes,
  contraindications, patientCI, isPediatric, onPosoChange, onAdd,
}) => (
  <div className={cn(
    'p-4 border rounded-2xl transition-all',
    patientCI.length > 0 ? 'border-red-200 bg-red-50/30' : 'border-slate-100 hover:border-indigo-100 hover:bg-indigo-50/20',
  )}>
    {/* Ligne 1 : nom + badges */}
    <div className="flex items-center gap-2 flex-wrap mb-2">
      <h4 className="font-black text-slate-800 text-sm">{name}</h4>
      {dci && <span className="bg-slate-100 text-slate-500 text-[9px] px-2 py-0.5 rounded-full font-black uppercase">{dci}</span>}
      <span className={cn(
        'text-[9px] px-2 py-0.5 rounded-full font-black',
        badgeColor === 'emerald' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500',
      )}>{badge}</span>
      {isPediatric && <span className="bg-amber-100 text-amber-700 text-[9px] px-2 py-0.5 rounded-full font-black">PÉDIATRIE</span>}
      {patientCI.length > 0 && <span className="bg-red-500 text-white text-[9px] px-2 py-0.5 rounded-full font-black flex items-center gap-1"><AlertCircle size={9} /> CE PATIENT</span>}
    </div>

    {/* Ligne 2 : dosage + forme */}
    {(dosage || forme) && (
      <p className="text-xs text-slate-600 mb-2">
        {dosage && <span className="font-bold text-slate-800">{dosage}</span>}
        {forme && <span className="text-slate-400"> · {forme}</span>}
      </p>
    )}

    {/* Ligne 3 : posologie éditable */}
    <div className="flex items-center gap-2">
      <input
        type="text"
        value={posologie}
        onChange={e => onPosoChange(e.target.value)}
        placeholder="Posologie (modifiable avant ajout)…"
        className="flex-1 bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs font-semibold focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition-all placeholder:text-slate-300"
      />
      <button
        onClick={onAdd}
        className="shrink-0 w-9 h-9 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl flex items-center justify-center transition-all shadow-md shadow-indigo-100"
        title="Ajouter à l'ordonnance"
      >
        <Plus size={16} />
      </button>
    </div>

    {/* Notes + CI */}
    {notes && <p className="text-[10px] text-slate-500 italic mt-2">{notes}</p>}
    {contraindications && contraindications.length > 0 && (
      <p className={cn('text-[9px] font-bold uppercase mt-1', patientCI.length > 0 ? 'text-red-600' : 'text-rose-400')}>
        CI : {contraindications.join(' · ')}
      </p>
    )}
  </div>
);

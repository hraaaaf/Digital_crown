import React, { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, ChevronDown, Plus, Search, Stethoscope, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { cn } from '../../../../utils/cn';
import { arbitrateMedication } from '../DentalPharmacologyArbiter';
import { buildPatientPharmacologyContext } from '../PrescriptionPharmacologyPipeline';

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

const GUIDE_MOLECULES = [
  { name: 'PARACETAMOL', category: 'Antalgiques' },
  { name: 'IBUPROFENE', category: 'AINS' },
  { name: 'PHENOXYMETHYLPENICILLINE', category: 'Antibiotiques' },
  { name: 'AMOXICILLINE', category: 'Antibiotiques' },
  { name: 'METRONIDAZOLE', category: 'Antibiotiques' },
  { name: 'CLINDAMYCINE', category: 'Antibiotiques' },
  { name: 'CLARITHROMYCINE', category: 'Antibiotiques' },
  { name: 'MICONAZOLE', category: 'Antifongiques' },
  { name: 'FLUCONAZOLE', category: 'Antifongiques' },
  { name: 'CHLORHEXIDINE', category: 'Antiseptiques' },
  { name: 'BENZYDAMINE', category: 'Antalgiques locaux' },
] as const;

const CATEGORIES = ['TOUS', ...Array.from(new Set(GUIDE_MOLECULES.map(m => m.category)))];
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
  const [showManual, setShowManual] = useState(false);

  useEffect(() => {
    if (!show) return;
    const context = buildPatientPharmacologyContext(assessment);
    setGuideAge(context.ageYears ?? 0);
    setGuideWeight(context.weightKg ?? 0);
  }, [show, assessment, setGuideAge, setGuideWeight]);

  const patientContext = useMemo(() => ({
    ...buildPatientPharmacologyContext(assessment),
    ageYears: guideAge > 0 ? guideAge : null,
    weightKg: guideWeight > 0 ? guideWeight : null,
  }), [assessment, guideAge, guideWeight]);

  const isChild = guideAge > 0 && guideAge < 18;
  const childContextIncomplete = isChild && !(guideWeight > 0 && Number.isFinite(guideWeight));

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
    toast.success(`${name} ajouté pour revue.`);
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
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Recherche locale + arbitrage pharmacologique</p>
              </div>
              <button type="button" onClick={onClose} className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center text-slate-500" aria-label="Fermer le référentiel">
                <X size={16} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              <div className="grid grid-cols-2 gap-3 p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <div>
                  <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Âge dossier</p>
                  <p className="mt-1 text-sm font-black text-slate-800">{guideAge > 0 ? `${guideAge} ans` : 'Non renseigné'}</p>
                </div>
                <div>
                  <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Poids réel dossier</p>
                  <p className="mt-1 text-sm font-black text-slate-800">{guideWeight > 0 ? `${guideWeight} kg` : 'Non renseigné'}</p>
                </div>
              </div>

              {childContextIncomplete && (
                <div className="flex gap-3 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800">
                  <AlertCircle size={18} className="shrink-0 mt-0.5" />
                  <p className="text-xs font-bold">Poids réel absent du dossier. Toute règle pédiatrique qui en dépend reste bloquée.</p>
                </div>
              )}

              <div className="space-y-3">
                <div className="relative">
                  <Search size={17} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    autoFocus
                    value={guideSearch}
                    onChange={e => {
                      const value = e.target.value;
                      setGuideSearch(value);
                      setGuideSearching(value.trim().length >= 2);
                      onNationalSearch(value);
                    }}
                    placeholder="Rechercher un nom commercial ou une DCI…"
                    className="w-full bg-white border border-slate-200 rounded-2xl pl-11 pr-4 py-3.5 text-base font-bold outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-50"
                    aria-label="Rechercher un médicament"
                  />
                </div>

                {!guideSearch.trim() && (
                  <div className="flex flex-wrap gap-2">
                    {CATEGORIES.map(cat => (
                      <button key={cat} type="button" onClick={() => setGuideCategory(cat)} className={cn('px-3 py-1.5 rounded-full text-[10px] font-black', guideCategory === cat ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500')}>
                        {cat}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-2" aria-live="polite">
                {guideSearch.trim().length >= 2 ? (
                  guideSearching ? <p className="text-sm text-slate-400">Recherche…</p> :
                  guideNationalResults.length === 0 ? <p className="text-sm font-semibold text-slate-400">Aucun résultat local.</p> :
                  guideNationalResults.map((med, index) => {
                    const key = `national-${index}-${med.nom}`;
                    const arbitration = arbitrateMedication(med.dci || med.nom, patientContext);
                    const defaultPoso = arbitration.status === 'applicable' ? arbitration.regimen?.posology || '' : '';
                    return (
                      <SafeRow
                        key={key}
                        name={med.nom}
                        subtitle={`${med.dci || 'DCI non résolue'} · référentiel local, statut AMMPS à confirmer`}
                        dosage={arbitration.status === 'applicable' ? arbitration.regimen?.dosage || '' : ''}
                        posologie={editingPoso[key] ?? defaultPoso}
                        status={arbitration.status}
                        messages={arbitration.messages}
                        disabled={false}
                        onPosoChange={v => setEditingPoso(p => ({ ...p, [key]: v }))}
                        onAdd={() => addFromList(key, med.nom, med.dosage ? `${med.dosage}${med.unite ? ` ${med.unite}` : ''}`.trim() : '', defaultPoso, med.forme)}
                      />
                    );
                  })
                ) : GUIDE_MOLECULES
                    .filter(rule => guideCategory === 'TOUS' || rule.category === guideCategory)
                    .map(rule => {
                      const key = `rule-${rule.name}`;
                      const arbitration = arbitrateMedication(rule.name, patientContext);
                      const regimen = arbitration.status === 'applicable' ? arbitration.regimen : null;
                      return (
                        <SafeRow
                          key={key}
                          name={rule.name}
                          subtitle={rule.category}
                          dosage={regimen?.dosage || ''}
                          posologie={editingPoso[key] ?? regimen?.posology ?? ''}
                          status={arbitration.status}
                          messages={arbitration.messages}
                          disabled={arbitration.status !== 'applicable'}
                          onPosoChange={v => setEditingPoso(p => ({ ...p, [key]: v }))}
                          onAdd={() => addFromList(key, rule.name, regimen?.dosage || '', regimen?.posology || '', regimen?.form)}
                        />
                      );
                    })}
              </div>

              <div className="border-t border-slate-100 pt-4">
                <button
                  type="button"
                  onClick={() => setShowManual(v => !v)}
                  className="w-full flex items-center justify-between rounded-xl px-3 py-2 text-xs font-black uppercase tracking-widest text-slate-500 hover:bg-slate-50"
                  aria-expanded={showManual}
                >
                  Ajout manuel praticien
                  <ChevronDown size={15} className={cn('transition-transform', showManual && 'rotate-180')} />
                </button>

                {showManual && (
                  <div className="mt-3 bg-indigo-50/60 border border-indigo-100 rounded-2xl p-4 space-y-3">
                    <input
                      value={custom.name}
                      onChange={e => setCustom(p => ({ ...p, name: e.target.value }))}
                      placeholder="Nom / DCI"
                      className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-bold"
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <input value={custom.dosage} onChange={e => setCustom(p => ({ ...p, dosage: e.target.value }))} placeholder="Dosage explicite" className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm" />
                      <input value={custom.posologie} onChange={e => setCustom(p => ({ ...p, posologie: e.target.value }))} placeholder="Posologie explicite" className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm" />
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {FORMES_RAPIDES.map(f => (
                        <button key={f} type="button" onClick={() => setCustom(p => ({ ...p, forme: f }))} className={cn('px-3 py-1 rounded-lg text-[10px] font-black border', custom.forme === f ? 'bg-indigo-600 text-white' : 'bg-white text-slate-500')}>
                          {f}
                        </button>
                      ))}
                    </div>
                    <button type="button" onClick={addCustom} disabled={!custom.name.trim()} className="w-full py-3 bg-indigo-600 disabled:opacity-40 text-white rounded-xl text-xs font-black uppercase tracking-widest">
                      <Plus size={15} className="inline mr-2" />Ajouter pour revue
                    </button>
                  </div>
                )}
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
  status: string;
  messages: string[];
  disabled: boolean;
  onPosoChange: (value: string) => void;
  onAdd: () => void;
}> = ({ name, subtitle, dosage, posologie, status, messages, disabled, onPosoChange, onAdd }) => (
  <div className="p-4 border border-slate-100 rounded-2xl">
    <div className="flex items-center justify-between gap-3 mb-2">
      <div>
        <h4 className="font-black text-slate-800 text-sm">{name}</h4>
        {subtitle && <p className="text-[10px] text-slate-400 font-bold">{subtitle}</p>}
      </div>
      <button type="button" disabled={disabled} onClick={onAdd} className="w-9 h-9 rounded-xl bg-indigo-600 disabled:bg-slate-200 text-white flex items-center justify-center" aria-label={`Ajouter ${name}`}>
        <Plus size={16} />
      </button>
    </div>
    {status !== 'applicable' && (
      <div className="flex gap-2 text-[10px] text-amber-700 font-bold mb-2">
        <AlertCircle size={12} className="shrink-0" />
        <span>{messages.join(' ') || 'Revue pharmacologique requise.'}</span>
      </div>
    )}
    {dosage && <p className="text-xs font-bold text-slate-700 mb-2">{dosage}</p>}
    <input value={posologie} onChange={e => onPosoChange(e.target.value)} placeholder="Posologie" className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs" />
  </div>
);

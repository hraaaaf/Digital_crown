import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  AlertTriangle,
  ArrowRight,
  Brain,
  ClipboardCheck,
  Plus,
  RefreshCw,
  ShieldCheck,
  X,
} from 'lucide-react';

import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';
import {
  buildQuoteTransferPayload,
  canTransferPractitionerActs,
  getCompanionOrientation,
  normalizePractitionerAct,
  type CompanionTopic,
  type PractitionerAct,
} from './DiagnosticCompanionPolicy';
import {
  isDiagnosticCompanionDirty,
  setDiagnosticCompanionDirty,
} from './DiagnosticCompanionDirtyState';

interface TreatmentPlanStudioProps {
  patientId: number;
  onConvertToQuote?: (acts: Array<{ suggested_act: string; fdi: 'Global'; phase: string }>) => void;
}

const TOPICS: Array<{ id: CompanionTopic; label: string }> = [
  { id: 'PAIN', label: 'Douleur / urgence' },
  { id: 'AESTHETIC', label: 'Demande esthétique' },
  { id: 'FUNCTION', label: 'Prothèse / fonction' },
  { id: 'TRAUMA', label: 'Traumatisme' },
  { id: 'CHECKUP', label: 'Contrôle / prévention' },
  { id: 'PEDIATRIC', label: 'Contexte pédiatrique' },
];

export const TreatmentPlanStudio: React.FC<TreatmentPlanStudioProps> = ({ patientId, onConvertToQuote }) => {
  const [topic, setTopic] = useState<CompanionTopic | null>(null);
  const [practitionerActs, setPractitionerActs] = useState<PractitionerAct[]>([]);
  const [newActText, setNewActText] = useState('');
  const [newActPhase, setNewActPhase] = useState('INITIALE');
  const [practitionerConfirmed, setPractitionerConfirmed] = useState(false);
  const [medicalHistory, setMedicalHistory] = useState<string | null>(null);
  const [patientContextError, setPatientContextError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setMedicalHistory(null);
    setPatientContextError(false);

    if (!patientId) return () => { cancelled = true; };

    api.get(`/patients/${patientId}`)
      .then((response: any) => {
        if (cancelled) return;
        const history = String(response?.data?.antecedents_medicaux || '').trim();
        setMedicalHistory(history || 'Non renseignés dans le dossier.');
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        console.error('P7: patient context unavailable', error);
        setPatientContextError(true);
        setMedicalHistory(null);
      });

    return () => { cancelled = true; };
  }, [patientId]);

  useEffect(() => {
    const dirty = practitionerActs.length > 0 || normalizePractitionerAct(newActText).length > 0;
    setDiagnosticCompanionDirty(dirty);
  }, [practitionerActs, newActText]);

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!isDiagnosticCompanionDirty()) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  const selectTopic = (nextTopic: CompanionTopic) => {
    setTopic(nextTopic);
    setPractitionerConfirmed(false);
  };

  const addPractitionerAct = () => {
    const act = normalizePractitionerAct(newActText);
    if (!act) return;
    setPractitionerActs(prev => [
      ...prev,
      { id: `practitioner-${Date.now()}`, phase: newActPhase, act },
    ]);
    setNewActText('');
    setPractitionerConfirmed(false);
  };

  const removePractitionerAct = (id: string) => {
    setPractitionerActs(prev => prev.filter(item => item.id !== id));
    setPractitionerConfirmed(false);
  };

  const resetCompanion = () => {
    setTopic(null);
    setPractitionerActs([]);
    setNewActText('');
    setNewActPhase('INITIALE');
    setPractitionerConfirmed(false);
    setDiagnosticCompanionDirty(false);
  };

  const transferToQuote = () => {
    if (!onConvertToQuote) return;
    const payload = buildQuoteTransferPayload(practitionerActs, practitionerConfirmed);
    if (payload.length === 0) return;
    setDiagnosticCompanionDirty(false);
    onConvertToQuote(payload);
    setPractitionerConfirmed(false);
  };

  const orientation = topic ? getCompanionOrientation(topic) : null;
  const canTransfer = canTransferPractitionerActs(practitionerActs, practitionerConfirmed);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-5 rounded-[2rem] border border-slate-200 bg-slate-50/60 p-4 shadow-sm backdrop-blur-xl sm:p-6">
      <header className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-primary/20 bg-primary/10 text-primary">
            <Brain size={21} />
          </div>
          <div>
            <h3 className="font-black tracking-tight text-slate-900">Compagnon d’orientation clinique</h3>
            <p className="mt-1 max-w-2xl text-xs font-medium leading-relaxed text-slate-500">
              Aide structurée à la consultation. Cet outil ne pose pas de diagnostic, ne prescrit pas et ne remplace pas le jugement du praticien.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={resetCompanion}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-500 transition hover:bg-slate-50"
        >
          <RefreshCw size={14} /> Recommencer
        </button>
      </header>

      <section className="rounded-2xl border border-amber-200 bg-amber-50/70 p-4" aria-label="Limites du compagnon diagnostique">
        <div className="flex items-start gap-3">
          <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
          <div>
            <h4 className="text-xs font-black uppercase tracking-wider text-amber-800">Frontière clinique</h4>
            <p className="mt-1 text-xs leading-relaxed text-amber-800">
              Aucun diagnostic, médicament, posologie, substitution thérapeutique ou plan de traitement n’est généré automatiquement. Les actes transférables sont uniquement ceux saisis puis confirmés par le praticien.
            </p>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5" aria-labelledby="p7-patient-context">
        <h4 id="p7-patient-context" className="text-xs font-black uppercase tracking-wider text-slate-500">Contexte patient — lecture seule</h4>
        {patientContextError ? (
          <div className="mt-3 flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>Antécédents indisponibles. Aucune conclusion automatisée n’est produite à partir d’un contexte incomplet.</span>
          </div>
        ) : (
          <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">
            {medicalHistory ?? 'Chargement des antécédents…'}
          </p>
        )}
        <p className="mt-2 text-[11px] text-slate-400">Les antécédents sont affichés pour revue humaine uniquement. Aucune adaptation médicamenteuse automatique n’est effectuée.</p>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5" aria-labelledby="p7-motif-title">
        <h4 id="p7-motif-title" className="text-xs font-black uppercase tracking-wider text-slate-500">1. Motif à structurer</h4>
        <div className="mt-4 flex flex-wrap gap-2">
          {TOPICS.map(item => (
            <button
              key={item.id}
              type="button"
              onClick={() => selectTopic(item.id)}
              aria-pressed={topic === item.id}
              className={cn(
                'rounded-xl border px-4 py-2.5 text-sm font-bold transition',
                topic === item.id
                  ? 'border-primary bg-primary text-white shadow-sm'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-primary/30 hover:bg-primary/5 hover:text-primary',
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
      </section>

      {orientation && (
        <motion.section
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-blue-100 bg-blue-50/60 p-5"
          aria-labelledby="p7-orientation-title"
        >
          <div className="flex items-start gap-3">
            <ClipboardCheck className="mt-0.5 h-5 w-5 shrink-0 text-blue-600" />
            <div className="flex-1">
              <span className="text-[10px] font-black uppercase tracking-wider text-blue-500">Orientation de consultation — à confirmer</span>
              <h4 id="p7-orientation-title" className="mt-1 font-black text-slate-900">{orientation.title}</h4>
              <ul className="mt-4 space-y-2 text-sm text-slate-700">
                {orientation.checklist.map(item => (
                  <li key={item} className="flex items-start gap-2">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </motion.section>
      )}

      <section className="rounded-2xl border border-slate-200 bg-white p-5" aria-labelledby="p7-practitioner-acts">
        <div>
          <h4 id="p7-practitioner-acts" className="text-xs font-black uppercase tracking-wider text-slate-500">2. Actes décidés par le praticien</h4>
          <p className="mt-1 text-xs text-slate-400">Aucun acte n’est prérempli par le compagnon. Ajoutez uniquement les actes que vous retenez après examen.</p>
        </div>

        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <select
            value={newActPhase}
            onChange={event => { setNewActPhase(event.target.value); setPractitionerConfirmed(false); }}
            aria-label="Phase de l'acte"
            className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-bold text-slate-600"
          >
            <option value="URGENCE">Urgence</option>
            <option value="INITIALE">Initiale</option>
            <option value="CONSERVATRICE">Conservatrice</option>
            <option value="CHIRURGIE">Chirurgie</option>
            <option value="REHABILITATION">Réhabilitation</option>
          </select>
          <input
            type="text"
            value={newActText}
            onChange={event => { setNewActText(event.target.value); setPractitionerConfirmed(false); }}
            onKeyDown={event => { if (event.key === 'Enter') addPractitionerAct(); }}
            placeholder="Acte retenu par le praticien"
            aria-label="Acte retenu par le praticien"
            className="min-w-0 flex-1 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 outline-none focus:border-primary"
          />
          <button
            type="button"
            onClick={addPractitionerAct}
            disabled={!normalizePractitionerAct(newActText)}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-800 px-4 py-2.5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Plus size={16} /> Ajouter
          </button>
        </div>

        <div className="mt-4 space-y-2">
          {practitionerActs.length === 0 && (
            <div className="rounded-xl border border-dashed border-slate-200 p-4 text-center text-sm text-slate-400">Aucun acte praticien saisi.</div>
          )}
          {practitionerActs.map(item => (
            <div key={item.id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
              <div className="min-w-0">
                <span className="text-[9px] font-black uppercase tracking-wider text-slate-400">{item.phase}</span>
                <p className="truncate text-sm font-bold text-slate-700">{item.act}</p>
              </div>
              <button
                type="button"
                onClick={() => removePractitionerAct(item.id)}
                aria-label={`Supprimer ${item.act}`}
                className="rounded-lg p-2 text-slate-400 transition hover:bg-red-50 hover:text-red-500"
              >
                <X size={15} />
              </button>
            </div>
          ))}
        </div>

        {practitionerActs.length > 0 && (
          <label className="mt-5 flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <input
              type="checkbox"
              checked={practitionerConfirmed}
              onChange={event => setPractitionerConfirmed(event.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-slate-300 accent-primary"
            />
            <span className="text-xs font-semibold leading-relaxed text-slate-600">
              Je confirme que les actes ci-dessus correspondent à ma décision clinique après examen du patient. Le compagnon ne les a ni diagnostiqués ni prescrits automatiquement.
            </span>
          </label>
        )}

        {onConvertToQuote && practitionerActs.length > 0 && (
          <button
            type="button"
            onClick={transferToQuote}
            disabled={!canTransfer}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-xs font-black uppercase tracking-wider text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:translate-y-0"
          >
            Transférer les actes confirmés vers Devis <ArrowRight size={16} />
          </button>
        )}
      </section>
    </div>
  );
};

export default TreatmentPlanStudio;

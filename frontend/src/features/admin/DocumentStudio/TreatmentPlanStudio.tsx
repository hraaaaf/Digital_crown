import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, ArrowRight, Plus, RefreshCw, X, FileText, CheckCircle2, ShieldCheck } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { isP7Dirty, setP7Dirty } from './P7DirtyState';

type DiagnosticState = 'MOTIF' | 'URGENCE_DOULEUR' | 'DOULEUR_SPONTANEE' | 'DOULEUR_PROVOQUEE' | 'PERCUSSION' | 'ABCES' | 'ESTHETIQUE' | 'PROTHESE_FONCTION' | 'TRAUMATISME' | 'CONTROLE' | 'PEDIATRIE' | 'RESULT';

interface ChatMessage {
  role: 'bot' | 'user';
  text: string;
}

interface ProposedAct {
  id: string;
  phase: string;
  act: string;
}

const INITIAL_HISTORY: ChatMessage[] = [
  { role: 'bot', text: 'Bonjour Docteur. Quel est le motif principal de la consultation aujourd\'hui ?' },
];

export function buildTreatmentPlanSafetyWarnings(medicalHistory: string, actLabels: string[]): string[] {
  const atcd = (medicalHistory || '').toLowerCase();
  const hasPenicillinSignal = atcd.includes('pénicilline') || atcd.includes('penicilline') || atcd.includes('clamoxyl') || atcd.includes('amoxicilline');
  const hasAinsSignal = atcd.includes('ains') || atcd.includes('ibuprofène') || atcd.includes('ibuprofene') || atcd.includes('anti-inflammatoire');
  const warnings: string[] = [];

  if (hasPenicillinSignal && actLabels.some(label => label.toLowerCase().includes('antibiothérapie'))) {
    warnings.push('⚠️ Signal lié aux pénicillines détecté dans les ATCD : vérifier les données structurées et le choix thérapeutique. Aucune substitution thérapeutique automatique n’est appliquée.');
  }
  if (hasAinsSignal && actLabels.some(label => label.toLowerCase().includes('anti-inflammatoire'))) {
    warnings.push('⚠️ Signal lié aux AINS détecté dans les ATCD : vérifier les données structurées et le choix thérapeutique. Aucune substitution thérapeutique automatique n’est appliquée.');
  }

  return warnings;
}

export const TreatmentPlanStudio: React.FC<{ patientId: number; onConvertToQuote?: (acts: any[]) => void }> = ({ patientId, onConvertToQuote }) => {
  const [currentState, setCurrentState] = useState<DiagnosticState>('MOTIF');
  const [history, setHistory] = useState<ChatMessage[]>(INITIAL_HISTORY);
  const [finalDiagnosis, setFinalDiagnosis] = useState('');
  const [proposedActs, setProposedActs] = useState<ProposedAct[]>([]);
  const [newActText, setNewActText] = useState('');
  const [newActPhase, setNewActPhase] = useState('CONSERVATRICE');
  const [medicalHistory, setMedicalHistory] = useState('');
  const [allergyWarning, setAllergyWarning] = useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    setP7Dirty(false);
    setCurrentState('MOTIF');
    setHistory(INITIAL_HISTORY);
    setFinalDiagnosis('');
    setProposedActs([]);
    setNewActText('');
    setNewActPhase('CONSERVATRICE');
    setMedicalHistory('');
    setAllergyWarning(null);

    const fetchPatient = async () => {
      try {
        const { api } = await import('../../../services/api');
        const response = await api.get(`/patients/${patientId}`);
        if (!cancelled) {
          setMedicalHistory(response.data.antecedents_medicaux || '');
        }
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to fetch patient history for pharmacovigilance", err);
        }
      }
    };

    if (patientId) void fetchPatient();
    return () => {
      cancelled = true;
    };
  }, [patientId]);

  React.useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!isP7Dirty()) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  const handleAnswer = (answerText: string, nextState: DiagnosticState, diagnosis?: string, acts?: Omit<ProposedAct, 'id'>[]) => {
    setP7Dirty(true);
    setHistory(prev => [...prev, { role: 'user', text: answerText }]);

    if (diagnosis && acts) {
      const warnings = buildTreatmentPlanSafetyWarnings(medicalHistory, acts.map(act => act.act));
      setFinalDiagnosis(diagnosis);
      setProposedActs(acts.map((a, i) => ({ ...a, id: `act-${Date.now()}-${i}` })));
      setAllergyWarning(warnings.length > 0 ? warnings.join(' ') : null);
    }

    setTimeout(() => {
      let nextQuestion = '';
      switch (nextState) {
        case 'URGENCE_DOULEUR':
          nextQuestion = 'Quel est le caractère principal de la douleur ?';
          break;
        case 'DOULEUR_SPONTANEE':
          nextQuestion = 'La douleur vous réveille-t-elle la nuit (caractère pulsatile) ?';
          break;
        case 'DOULEUR_PROVOQUEE':
          nextQuestion = 'La douleur disparaît-elle rapidement après l\'arrêt du stimulus (froid) ?';
          break;
        case 'PERCUSSION':
          nextQuestion = 'La dent est-elle douloureuse à la percussion axiale ?';
          break;
        case 'ABCES':
          nextQuestion = 'Y a-t-il une fluctuation palpable au fond du vestibule ?';
          break;
        case 'ESTHETIQUE':
          nextQuestion = 'Quelle est la principale demande esthétique du patient ?';
          break;
        case 'PROTHESE_FONCTION':
          nextQuestion = 'Quel est le problème fonctionnel ou prothétique rencontré ?';
          break;
        case 'TRAUMATISME':
          nextQuestion = 'Quelle est la nature du traumatisme subi ?';
          break;
        case 'CONTROLE':
          nextQuestion = 'Quel est le type de contrôle souhaité ?';
          break;
        case 'PEDIATRIE':
          nextQuestion = 'Quel est le problème dentaire de l\'enfant ?';
          break;
        case 'RESULT':
          nextQuestion = 'Hypothèse générée à partir des réponses saisies. Voici une proposition de prise en charge à confirmer par le praticien :';
          break;
      }
      if (nextQuestion) {
        setHistory(prev => [...prev, { role: 'bot', text: nextQuestion }]);
      }
      setCurrentState(nextState);
    }, 400);
  };

  const renderOptions = () => {
    switch (currentState) {
      case 'MOTIF':
        return (
          <div className="flex w-full flex-wrap gap-2 sm:justify-end">
            <OptionButton text="Urgence / Douleur aiguë" onClick={() => handleAnswer("Urgence / Douleur aiguë", 'URGENCE_DOULEUR')} />
            <OptionButton text="Motif Esthétique" onClick={() => handleAnswer("Motif Esthétique", 'ESTHETIQUE')} />
            <OptionButton text="Problème Prothétique / Fonctionnel" onClick={() => handleAnswer("Problème Prothétique / Fonctionnel", 'PROTHESE_FONCTION')} />
            <OptionButton text="Traumatisme" onClick={() => handleAnswer("Traumatisme Dentaire", 'TRAUMATISME')} />
            <OptionButton text="Contrôle de routine / Tartre" onClick={() => handleAnswer("Contrôle de routine / Tartre", 'CONTROLE')} />
            <OptionButton text="Soins Pédiatriques (Enfant)" onClick={() => handleAnswer("Soins Pédiatriques", 'PEDIATRIE')} />
          </div>
        );
      case 'URGENCE_DOULEUR':
        return (
          <>
            <OptionButton text="Douleur spontanée aiguë" onClick={() => handleAnswer("Douleur spontanée", 'DOULEUR_SPONTANEE')} />
            <OptionButton text="Douleur provoquée (Froid/Chaud)" onClick={() => handleAnswer("Douleur provoquée", 'DOULEUR_PROVOQUEE')} />
            <OptionButton text="Abcès ou Gonflement" onClick={() => handleAnswer("Abcès/Gonflement", 'ABCES')} />
          </>
        );
      case 'DOULEUR_SPONTANEE':
        return (
          <>
            <OptionButton
              text="Oui, avec irradiation (réveille la nuit)"
              onClick={() => handleAnswer("Oui, avec irradiation", 'RESULT', 'Pulpite Irréversible', [
                { phase: 'URGENCE', act: 'Pulpectomie et parage canalaire' },
                { phase: 'INITIALE', act: 'Prescription antalgique (Palier 2)' }
              ])}
            />
            <OptionButton text="Non, douleur localisée à la mastication" onClick={() => handleAnswer("Non, localisée à la mastication", 'PERCUSSION')} />
          </>
        );
      case 'PERCUSSION':
        return (
          <>
            <OptionButton
              text="Oui, très douloureuse"
              onClick={() => handleAnswer("Oui, très douloureuse", 'RESULT', 'Parodontite Apicale Aiguë', [
                { phase: 'URGENCE', act: 'Ouverture camérale, drainage et mise en sous-occlusion' },
                { phase: 'INITIALE', act: 'Antibiothérapie et antalgiques' }
              ])}
            />
            <OptionButton
              text="Non ou très peu"
              onClick={() => handleAnswer("Non ou très peu", 'RESULT', 'Syndrome du septum', [
                { phase: 'INITIALE', act: 'Nettoyage des espaces interdentaires et contrôle de l\'occlusion' }
              ])}
            />
          </>
        );
      case 'DOULEUR_PROVOQUEE':
        return (
          <>
            <OptionButton
              text="Oui (disparaît en quelques secondes)"
              onClick={() => handleAnswer("Oui (quelques secondes)", 'RESULT', 'Hyperhémie Pulpaire / Pulpite Réversible', [
                { phase: 'CONSERVATRICE', act: 'Coiffage pulpaire indirect et restauration coronaire' }
              ])}
            />
            <OptionButton
              text="Non, elle persiste plusieurs minutes"
              onClick={() => handleAnswer("Non, persiste plusieurs minutes", 'RESULT', 'Pulpite Irréversible', [
                { phase: 'URGENCE', act: 'Pulpectomie immédiate' }
              ])}
            />
          </>
        );
      case 'ABCES':
        return (
          <>
            <OptionButton
              text="Oui, fluctuation évidente"
              onClick={() => handleAnswer("Oui, fluctuation évidente", 'RESULT', 'Abcès Sous-Muqueux', [
                { phase: 'URGENCE', act: 'Incision, drainage et lavage' },
                { phase: 'INITIALE', act: 'Antibiothérapie de couverture et antalgiques' }
              ])}
            />
            <OptionButton
              text="Non, douleur sourde diffuse (pas de fluctuation)"
              onClick={() => handleAnswer("Non, pas de fluctuation", 'RESULT', 'Cellulite (Stade séreux)', [
                { phase: 'INITIALE', act: 'Antibiothérapie et anti-inflammatoires stéroïdiens' },
                { phase: 'URGENCE', act: 'Traitement endodontique de la dent causale' }
              ])}
            />
          </>
        );
      case 'ESTHETIQUE':
        return (
          <>
            <OptionButton text="Coloration / Taches" onClick={() => handleAnswer("Coloration ou Taches", 'RESULT', 'Dyschromie dentaire', [
              { phase: 'INITIALE', act: 'Photographies et prise de teinte initiale' },
              { phase: 'CONSERVATRICE', act: 'Éclaircissement dentaire (Blanchiment interne/externe)' },
              { phase: 'REHABILITATION', act: 'Facettes céramiques si dyschromie sévère' }
            ])} />
            <OptionButton text="Dents mal alignées" onClick={() => handleAnswer("Dents mal alignées", 'RESULT', 'Malocclusion / Encombrement', [
              { phase: 'INITIALE', act: 'Bilan orthodontique (Moulages, Photos, Céphalo)' },
              { phase: 'REHABILITATION', act: 'Traitement par Aligneurs transparents ou Multi-attaches' }
            ])} />
            <OptionButton text="Dents usées ou cassées" onClick={() => handleAnswer("Usure/Casse esthétique", 'RESULT', 'Usure dentaire / Attrition', [
              { phase: 'INITIALE', act: 'Analyse occlusale et dimension verticale' },
              { phase: 'REHABILITATION', act: 'Facettes, Onlays ou Reconstitution au composite' }
            ])} />
          </>
        );
      case 'PROTHESE_FONCTION':
        return (
          <>
            <OptionButton text="Dent(s) manquante(s)" onClick={() => handleAnswer("Dent manquante", 'RESULT', 'Édendement partiel/total', [
              { phase: 'INITIALE', act: 'Examen radiologique 3D (CBCT)' },
              { phase: 'CHIRURGIE', act: 'Pose d\'implant(s) ou chirurgie pré-implantaire' },
              { phase: 'REHABILITATION', act: 'Prothèse sur implant ou Bridge conventionnel' }
            ])} />
            <OptionButton text="Couronne/Bridge cassé ou descellé" onClick={() => handleAnswer("Problème prothétique existant", 'RESULT', 'Descellement prothétique', [
              { phase: 'URGENCE', act: 'Nettoyage et essai de repositionnement' },
              { phase: 'REHABILITATION', act: 'Rescellement ou réalisation d\'une nouvelle empreinte' }
            ])} />
            <OptionButton text="Difficulté à mastiquer / Douleur ATM" onClick={() => handleAnswer("Douleur à la mastication (ATM)", 'RESULT', 'Trouble ATM / Perte de DVO', [
              { phase: 'INITIALE', act: 'Examen palpation ATM et muscles masticateurs' },
              { phase: 'CONSERVATRICE', act: 'Gouttière de reconditionnement occlusal' }
            ])} />
          </>
        );
      case 'TRAUMATISME':
        return (
          <>
            <OptionButton text="Choc avec dent cassée" onClick={() => handleAnswer("Choc / Dent cassée", 'RESULT', 'Fracture corono-radiculaire', [
              { phase: 'URGENCE', act: 'Bilan radiographique (Rétro-alvéolaire)' },
              { phase: 'CONSERVATRICE', act: 'Reconstitution composite ou Traitement Endodontique si pulpe exposée' }
            ])} />
            <OptionButton text="Dent mobile après un choc" onClick={() => handleAnswer("Mobilité dentaire post-traumatique", 'RESULT', 'Subluxation / Luxation', [
              { phase: 'URGENCE', act: 'Contention semi-rigide (composite/fil) pour 2 à 4 semaines' },
              { phase: 'INITIALE', act: 'Surveillance régulières de la vitalité pulpaire' }
            ])} />
            <OptionButton text="Dent complètement expulsée" onClick={() => handleAnswer("Dent expulsée", 'RESULT', 'Avulsion traumatique', [
              { phase: 'URGENCE', act: 'Réimplantation immédiate si < 60 min, sinon conditionnement' },
              { phase: 'CHIRURGIE', act: 'Contention flexible et antibiothérapie prophylactique' },
              { phase: 'CONSERVATRICE', act: 'Traitement endodontique différé (7-10 jours)' }
            ])} />
          </>
        );
      case 'CONTROLE':
        return (
          <>
            <OptionButton text="Visite de contrôle annuelle" onClick={() => handleAnswer("Contrôle annuel", 'RESULT', 'Bilan bucco-dentaire de routine', [
              { phase: 'INITIALE', act: 'Examen clinique complet et radiographies (Bite-wing)' },
              { phase: 'CONSERVATRICE', act: 'Détartrage, polissage et prophylaxie' }
            ])} />
            <OptionButton text="Gencives qui saignent (Tartre)" onClick={() => handleAnswer("Saignement gingival", 'RESULT', 'Gingivite / Parodontite', [
              { phase: 'INITIALE', act: 'Sondage parodontal et bilan radiographique long cône' },
              { phase: 'CONSERVATRICE', act: 'Surfaçage radiculaire (Assainissement parodontal)' },
              { phase: 'INITIALE', act: 'Enseignement à l\'hygiène orale' }
            ])} />
          </>
        );
      case 'PEDIATRIE':
        return (
          <>
            <OptionButton text="Carie profonde avec douleur (Dent de lait)" onClick={() => handleAnswer("Carie profonde avec douleur", 'RESULT', 'Pulpite / Nécrose sur dent temporaire', [
              { phase: 'URGENCE', act: 'Pulpotomie ou Pulpectomie temporaire' },
              { phase: 'REHABILITATION', act: 'Coiffe pédodontique préformée' }
            ])} />
            <OptionButton text="Carie débutante (sans douleur)" onClick={() => handleAnswer("Carie débutante", 'RESULT', 'Carie dentine superficielle (Dent temporaire)', [
              { phase: 'CONSERVATRICE', act: 'Éviction carieuse et restauration Verre Ionomère (CVI)' }
            ])} />
            <OptionButton text="Prévention / Scellement" onClick={() => handleAnswer("Prévention", 'RESULT', 'Prévention carieuse pédiatrique', [
              { phase: 'CONSERVATRICE', act: 'Scellement des sillons (Sealants)' },
              { phase: 'INITIALE', act: 'Application topique de vernis fluoré' }
            ])} />
          </>
        );
      default:
        return null;
    }
  };

  const addCustomAct = () => {
    if (!newActText.trim()) return;
    setP7Dirty(true);
    setProposedActs(prev => [...prev, { id: `custom-${Date.now()}`, phase: newActPhase, act: newActText }]);
    setNewActText('');
  };

  const removeAct = (id: string) => {
    setP7Dirty(true);
    setProposedActs(prev => prev.filter(a => a.id !== id));
  };

  const resetDiagnostic = () => {
    setP7Dirty(false);
    setCurrentState('MOTIF');
    setHistory(INITIAL_HISTORY);
    setFinalDiagnosis('');
    setProposedActs([]);
    setAllergyWarning(null);
  };

  const convertToQuote = () => {
    if (!onConvertToQuote || proposedActs.length === 0) return;
    onConvertToQuote(proposedActs.map(act => ({
      suggested_act: act.act,
      fdi: 'Global',
      phase: act.phase,
    })));
    setP7Dirty(false);
  };

  return (
    <div className="flex h-[70vh] min-h-[520px] max-h-[700px] flex-col overflow-hidden rounded-[1.5rem] border border-slate-200 bg-slate-50/50 backdrop-blur-xl sm:h-[600px] sm:rounded-[2rem]">
      <div className="z-10 flex shrink-0 items-center justify-between border-b border-slate-200 bg-white/80 px-4 py-4 backdrop-blur-md sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-primary/20 bg-primary/10 text-primary shadow-sm">
            <Brain size={20} />
          </div>
          <div className="min-w-0">
            <h3 className="truncate font-black leading-none tracking-tight text-slate-800">Compagnon Diagnostique</h3>
            <p className="mt-1 text-[10px] font-black uppercase tracking-widest text-slate-400">Aide structurée à confirmer</p>
          </div>
        </div>
        <button type="button" onClick={resetDiagnostic} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-transparent text-slate-400 transition-colors hover:border-slate-200 hover:bg-slate-100 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary" aria-label="Recommencer le compagnon diagnostique" title="Recommencer">
          <RefreshCw size={16} />
        </button>
      </div>

      <div className="custom-scrollbar-white flex-1 space-y-4 overflow-y-auto p-4 sm:p-6">
        {history.map((msg, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn("flex w-full", msg.role === 'user' ? "justify-end" : "justify-start")}
          >
            <div className={cn(
              "max-w-[92%] break-words px-4 py-3 text-sm font-medium sm:max-w-[80%]",
              msg.role === 'user'
                ? "rounded-2xl rounded-tr-sm bg-primary text-white shadow-md"
                : "rounded-2xl rounded-tl-sm border border-slate-200 bg-white text-slate-700 shadow-sm"
            )}>
              {msg.text}
            </div>
          </motion.div>
        ))}

        {currentState !== 'RESULT' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex w-full flex-col items-stretch gap-2 sm:items-end">
            {renderOptions()}
          </motion.div>
        )}

        {currentState === 'RESULT' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-200/50"
            aria-live="polite"
          >
            <div className="flex items-start gap-3 border-b border-primary/10 bg-primary/5 px-4 py-4 sm:px-6">
              <CheckCircle2 size={24} className="mt-0.5 shrink-0 text-primary" />
              <div className="min-w-0">
                <span className="mb-0.5 block text-[10px] font-black uppercase tracking-widest text-primary">Hypothèse à confirmer</span>
                <h4 className="break-words text-lg font-black tracking-tight text-slate-800">{finalDiagnosis}</h4>
                <p className="mt-1 text-[11px] font-semibold text-slate-500">Sortie logicielle déterministe, non équivalente à un diagnostic clinique validé.</p>
              </div>
            </div>

            <div className="p-4 sm:p-6">
              {allergyWarning && (
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6 flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3.5" role="alert">
                  <ShieldCheck size={18} className="mt-0.5 shrink-0 text-rose-600" />
                  <div>
                    <h5 className="mb-0.5 text-[10px] font-black uppercase tracking-widest text-rose-600">Vérification ATCD requise</h5>
                    <p className="text-xs font-bold leading-snug text-rose-700">{allergyWarning}</p>
                  </div>
                </motion.div>
              )}

              <h5 className="mb-4 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-400">
                <FileText size={14} /> Proposition de prise en charge à valider
              </h5>

              <div className="mb-6 space-y-2">
                {proposedActs.map((act) => (
                  <div key={act.id} className="group flex items-start justify-between gap-2 rounded-xl border border-slate-100 bg-slate-50/80 p-3 transition-colors hover:bg-slate-50 sm:items-center">
                    <div className="flex min-w-0 flex-1 flex-col items-start gap-2 sm:flex-row sm:items-center sm:gap-3">
                      <span className={cn(
                        "shrink-0 rounded-md px-2 py-1 text-[9px] font-black uppercase tracking-wider",
                        act.phase === 'URGENCE' ? "bg-red-100 text-red-700" :
                        act.phase === 'INITIALE' ? "bg-amber-100 text-amber-700" :
                        act.phase === 'CONSERVATRICE' ? "bg-emerald-100 text-emerald-700" :
                        "bg-blue-100 text-blue-700"
                      )}>
                        {act.phase}
                      </span>
                      <span className="break-words text-sm font-bold text-slate-700">{act.act}</span>
                    </div>
                    <button type="button" onClick={() => removeAct(act.id)} aria-label={`Supprimer ${act.act}`} className="shrink-0 rounded-full border border-slate-200 bg-white p-2 text-slate-400 opacity-100 transition-all hover:border-red-200 hover:text-red-500 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 sm:p-1 sm:opacity-0 sm:group-hover:opacity-100">
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex flex-col gap-2 rounded-xl border border-slate-100 bg-slate-50/50 p-2 sm:flex-row sm:items-center">
                <select
                  value={newActPhase}
                  onChange={(e) => setNewActPhase(e.target.value)}
                  aria-label="Phase de l'acte proposé"
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-600 shadow-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 sm:w-auto"
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
                  onChange={(e) => setNewActText(e.target.value)}
                  aria-label="Acte à ajouter à la proposition"
                  placeholder="Ajouter un acte à valider..."
                  className="w-full flex-1 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700 shadow-sm outline-none transition-all focus:border-primary focus:ring-2 focus:ring-primary/20"
                  onKeyDown={(e) => e.key === 'Enter' && addCustomAct()}
                />
                <button type="button" onClick={addCustomAct} aria-label="Ajouter l'acte à la proposition" className="flex h-10 w-full items-center justify-center rounded-lg bg-primary text-white shadow-md shadow-primary/20 transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary sm:w-10">
                  <Plus size={18} />
                </button>
              </div>

              {onConvertToQuote && proposedActs.length > 0 && (
                <button
                  type="button"
                  onClick={convertToQuote}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-center text-xs font-black uppercase tracking-widest text-white shadow-lg shadow-primary/20 transition-all hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary active:scale-[0.99] sm:px-5"
                >
                  Préparer le devis à partir de cette proposition <ArrowRight size={16} className="shrink-0" />
                </button>
              )}

              <p className="mt-4 text-[11px] font-semibold leading-relaxed text-slate-500">
                Les repères cliniques non sourcés/versionnés sont masqués jusqu’à validation scientifique dédiée. La validation du praticien reste requise avant toute utilisation clinique ou conversion documentaire.
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

const OptionButton: React.FC<{ text: string; onClick: () => void }> = ({ text, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className="group flex w-full items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-2.5 text-left text-sm font-black text-primary shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary sm:w-auto sm:justify-center sm:text-center"
  >
    <span>{text}</span>
    <ArrowRight size={14} className="shrink-0 text-primary/70 transition-all sm:-ml-2 sm:opacity-0 sm:group-hover:ml-0 sm:group-hover:opacity-100 sm:group-focus-visible:ml-0 sm:group-focus-visible:opacity-100" />
  </button>
);

export default TreatmentPlanStudio;
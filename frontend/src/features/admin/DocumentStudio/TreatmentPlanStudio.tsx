import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, ArrowRight, Plus, RefreshCw, X, FileText, CheckCircle2, Lightbulb, ShieldCheck } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { safeStorage } from '../../../hooks/useLocalStorage';
import { useSettingsStore } from '../Settings/hooks/useSettingsStore';

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
    // Patient boundary: no diagnostic, proposed act or warning may survive a patient change.
    let cancelled = false;
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

  const { profile } = useSettingsStore();
  const clinicalTipsEnabled = profile.clinical_tips_enabled ?? safeStorage.get('clinicalTipsEnabled') !== 'false';

  const getClinicalTip = (diagnosis: string) => {
    if (diagnosis.includes('Pulpite Irréversible')) return "Rappel scientifique: Le succès d'une pulpectomie d'urgence dépend d'un parage canalaire minimal d'au moins le tiers cervical pour éliminer le maximum de charge bactérienne aiguë.";
    if (diagnosis.includes('Parodontite Apicale')) return "Évidence Clinique: La mise en sous-occlusion de la dent causale réduit significativement la symptomatologie douloureuse dans les 24h, indépendamment de l'antibiothérapie.";
    if (diagnosis.includes('Syndrome du septum')) return "Conseil: La prescription d'antalgiques est inutile si le point de contact n'est pas restauré et le bourrage alimentaire persistant.";
    if (diagnosis.includes('Hyperhémie Pulpaire')) return "Recommandation: L'utilisation d'une base de silicate de calcium (MTA/Biodentine) améliore de 65% la réparation dentinaire comparé à l'hydroxyde de calcium classique.";
    if (diagnosis.includes('Abcès Sous-Muqueux')) return "Guidance: Un drainage sans incision large et sans lavage à la chlorhexidine 0.2% augmente le risque de diffusion cellulaire de 40%.";
    if (diagnosis.includes('Cellulite')) return "Alerte: La prescription d'AINS est formellement contre-indiquée en première intention sans une couverture antibiotique adaptée (ex: Amoxicilline 2g/j).";
    if (diagnosis.includes('Dyschromie dentaire')) return "Esthétique: Un éclaircissement interne est indiqué avant toute facette si la dent est dépulpée et fortement dyschromiée.";
    if (diagnosis.includes('Malocclusion')) return "Orthodontie: L'évaluation de la classe squelettique et de la DDM est préalable à tout plan de traitement par aligneurs.";
    if (diagnosis.includes('Usure dentaire')) return "Prothèse: La perte de dimension verticale doit être évaluée; une réhabilitation globale par onlays/overlays peut être nécessaire.";
    if (diagnosis.includes('Édendement')) return "Implantologie: Prévoir un CBCT pour évaluer le volume osseux résiduel avant de proposer une solution implantaire.";
    if (diagnosis.includes('Descellement prothétique')) return "Prothèse: Vérifier l'absence de reprise carieuse sous-jacente et l'adaptation marginale avant le rescellement.";
    if (diagnosis.includes('Trouble ATM')) return "ATM: La prescription d'une gouttière de reconditionnement musculaire (gouttière occlusale) est le traitement de première intention.";
    if (diagnosis.includes('Fracture corono-radiculaire')) return "Traumatologie: Une radiographie rétro-alvéolaire est indispensable. Si la fracture s'étend sous la crête osseuse, l'extraction peut être envisagée.";
    if (diagnosis.includes('Subluxation')) return "Traumatologie: Tester la vitalité pulpaire (au froid) immédiatement puis à 2, 4 et 12 semaines post-traumatisme.";
    if (diagnosis.includes('Avulsion traumatique')) return "Urgence: La réimplantation doit idéalement être réalisée dans les 60 minutes. Prescrire antibiotiques (Amoxicilline) et vérifier le statut tétanique.";
    if (diagnosis.includes('Gingivite') || diagnosis.includes('Parodontite')) return "Parodontie: Le sondage parodontal (charting) est indispensable pour objectiver la perte d'attache avant le surfaçage radiculaire.";
    if (diagnosis.includes('Pulpite / Nécrose sur dent temporaire')) return "Pédodontie: L'utilisation du MTA ou de la Biodentine pour les pulpotomies offre un taux de succès clinique supérieur au formocrésol.";
    if (diagnosis.includes('Prévention carieuse pédiatrique')) return "Prévention: Le scellement des puits et fissures est indiqué dès l'éruption complète des premières molaires permanentes (vers 6 ans).";
    return "Optimisation: Vérifiez toujours les antécédents médicaux avant d'initier la phase thérapeutique.";
  };

  const handleAnswer = (answerText: string, nextState: DiagnosticState, diagnosis?: string, acts?: Omit<ProposedAct, 'id'>[]) => {
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
          nextQuestion = 'Diagnostic établi. Voici le plan de traitement scientifique recommandé :';
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
          <div className="flex flex-wrap gap-2 justify-end">
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
            <OptionButton
              text="Non, douleur localisée à la mastication"
              onClick={() => handleAnswer("Non, localisée à la mastication", 'PERCUSSION')}
            />
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
    setProposedActs(prev => [...prev, { id: `custom-${Date.now()}`, phase: newActPhase, act: newActText }]);
    setNewActText('');
  };

  const removeAct = (id: string) => {
    setProposedActs(prev => prev.filter(a => a.id !== id));
  };

  const resetDiagnostic = () => {
    setCurrentState('MOTIF');
    setHistory(INITIAL_HISTORY);
    setFinalDiagnosis('');
    setProposedActs([]);
    setAllergyWarning(null);
  };

  return (
    <div className="flex flex-col h-[600px] bg-slate-50/50 rounded-[2rem] border border-slate-200 overflow-hidden relative backdrop-blur-xl">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md px-6 py-4 border-b border-slate-200 flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary shadow-sm border border-primary/20">
            <Brain size={20} />
          </div>
          <div>
            <h3 className="font-black text-slate-800 leading-none tracking-tight">Compagnon Diagnostique</h3>
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mt-1">State Machine Clinique</p>
          </div>
        </div>
        <button onClick={resetDiagnostic} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 text-slate-400 hover:text-primary transition-colors border border-transparent hover:border-slate-200" title="Recommencer">
          <RefreshCw size={14} />
        </button>
      </div>

      {/* Chat History Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar-white">
        {history.map((msg, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
              "flex w-full",
              msg.role === 'user' ? "justify-end" : "justify-start"
            )}
          >
            <div className={cn(
              "max-w-[80%] px-4 py-3 text-sm font-medium",
              msg.role === 'user'
                ? "bg-primary text-white rounded-2xl rounded-tr-sm shadow-md"
                : "bg-white border border-slate-200 text-slate-700 shadow-sm rounded-2xl rounded-tl-sm"
            )}>
              {msg.text}
            </div>
          </motion.div>
        ))}

        {currentState !== 'RESULT' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-end gap-2 mt-4"
          >
            {renderOptions()}
          </motion.div>
        )}

        {/* Result Area */}
        {currentState === 'RESULT' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-6 bg-white rounded-2xl border border-slate-200 shadow-xl shadow-slate-200/50 overflow-hidden"
          >
            <div className="bg-primary/5 px-6 py-4 border-b border-primary/10 flex items-center gap-3">
              <CheckCircle2 size={24} className="text-primary" />
              <div>
                <span className="text-[10px] font-black text-primary uppercase tracking-widest block mb-0.5">Diagnostic Établi</span>
                <h4 className="text-lg font-black text-slate-800 tracking-tight">{finalDiagnosis}</h4>
              </div>
            </div>

            <div className="p-6">
              {/* Warning-only pharmacovigilance boundary. */}
              {allergyWarning && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-3"
                >
                  <ShieldCheck size={18} className="text-rose-600 shrink-0 mt-0.5" />
                  <div>
                    <h5 className="text-[10px] font-black text-rose-600 uppercase tracking-widest mb-0.5">Vérification ATCD requise</h5>
                    <p className="text-xs font-bold text-rose-700 leading-snug">{allergyWarning}</p>
                  </div>
                </motion.div>
              )}

              <h5 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                <FileText size={14} /> Plan de Traitement Scientifique
              </h5>

              <div className="space-y-2 mb-6">
                {proposedActs.map((act) => (
                  <div key={act.id} className="flex items-center justify-between p-3 bg-slate-50/80 rounded-xl border border-slate-100 group transition-colors hover:bg-slate-50">
                    <div className="flex items-center gap-3">
                      <span className={cn(
                        "text-[9px] font-black uppercase tracking-wider px-2 py-1 rounded-md",
                        act.phase === 'URGENCE' ? "bg-red-100 text-red-700" :
                        act.phase === 'INITIALE' ? "bg-amber-100 text-amber-700" :
                        act.phase === 'CONSERVATRICE' ? "bg-emerald-100 text-emerald-700" :
                        "bg-blue-100 text-blue-700"
                      )}>
                        {act.phase}
                      </span>
                      <span className="text-sm font-bold text-slate-700">{act.act}</span>
                    </div>
                    <button onClick={() => removeAct(act.id)} className="text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all bg-white rounded-full p-1 border border-slate-200 hover:border-red-200">
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>

              {/* Add Custom Act */}
              <div className="flex gap-2 items-center bg-slate-50/50 p-2 rounded-xl border border-slate-100">
                <select
                  value={newActPhase}
                  onChange={(e) => setNewActPhase(e.target.value)}
                  className="bg-white border border-slate-200 text-xs font-bold text-slate-600 rounded-lg px-3 py-2 outline-none focus:border-primary shadow-sm"
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
                  placeholder="Ajouter un acte clinique scientifique..."
                  className="flex-1 bg-white border border-slate-200 text-sm font-bold text-slate-700 rounded-lg px-4 py-2 outline-none focus:border-primary transition-all shadow-sm"
                  onKeyDown={(e) => e.key === 'Enter' && addCustomAct()}
                />
                <button onClick={addCustomAct} className="w-10 h-10 bg-primary text-white rounded-lg flex items-center justify-center hover:bg-primary/90 transition-colors shadow-md shadow-primary/20">
                  <Plus size={18} />
                </button>
              </div>

              {onConvertToQuote && proposedActs.length > 0 && (
                <button
                  type="button"
                  onClick={() => onConvertToQuote(proposedActs.map(act => ({
                    suggested_act: act.act,
                    fdi: 'Global',
                    phase: act.phase,
                  })))}
                  className="mt-4 w-full flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-xs font-black uppercase tracking-widest text-white shadow-lg shadow-primary/20 transition-all hover:-translate-y-0.5 active:scale-[0.99]"
                >
                  Créer le devis <ArrowRight size={16} />
                </button>
              )}

              {clinicalTipsEnabled && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="mt-6 bg-blue-50/50 border border-blue-100 rounded-xl p-4 flex gap-3"
                >
                  <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-500 flex items-center justify-center shrink-0">
                    <Lightbulb size={16} />
                  </div>
                  <div>
                    <h5 className="text-[10px] font-black uppercase tracking-widest text-blue-500 mb-1">Intelligence Clinique Proactive</h5>
                    <p className="text-xs text-blue-800 font-medium leading-relaxed">
                      {getClinicalTip(finalDiagnosis)}
                    </p>
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

const OptionButton: React.FC<{ text: string; onClick: () => void }> = ({ text, onClick }) => (
  <button
    onClick={onClick}
    className="px-5 py-2.5 bg-white border border-slate-200 text-primary text-sm font-black rounded-2xl shadow-sm hover:border-primary/30 hover:bg-primary/5 transition-all flex items-center gap-2 group hover:-translate-y-0.5"
  >
    {text}
    <ArrowRight size={14} className="opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all text-primary/70" />
  </button>
);

export default TreatmentPlanStudio;
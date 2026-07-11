import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import {
  Calendar,
  FileText,
  Radio,
  Banknote,
  Wrench,
  Flag,
  ChevronDown,
  ChevronRight,
  Plus,
  Trash2,
  ExternalLink,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';
import { EliteGhostLoader } from '../../../components/EliteGhostLoader';
import { LegacyActeNotes, type LegacyActe } from './LegacyActeNotes';

// P0-TREATMENT-JOURNEY-1 — fil chronologique du dossier patient. Remplace PatientTracking comme
// rendu par défaut de l'onglet "tracking" (voir docs/TREATMENT_JOURNEY_DESIGN.md, STATE.md).
// N'est jamais la source de vérité : agrège des données déjà présentes en base, la navigation
// renvoie toujours vers l'écran qui possède réellement la donnée.

interface JourneyEvent {
  event_key: string;
  source: string;
  type: string;
  ref_id: number;
  date: string;
  title: string;
  status: string;
  phase_hint: string;
  navigation_target: 'DOCUMENT' | 'RADIOLOGY_TAB' | 'TREATMENT_PLAN_TAB' | 'ACCOUNTING_TAB' | 'LAB_PAGE' | 'INLINE';
  related_event_key: string | null;
}

interface JourneySummary {
  active_plan_steps: number;
  total_plan_steps: number;
  remaining_due: number;
  next_appointment: string | null;
  last_document_date: string | null;
}

interface JourneyResponse {
  patient_id: number;
  window_months: number;
  truncated: boolean;
  total_events_available: number;
  summary: JourneySummary;
  events: JourneyEvent[];
}

interface DocumentInfo {
  id: string;
  name: string;
  url: string;
}

interface PatientJourneyProps {
  patientId: number;
}

const PHASE_ORDER = [
  'diagnostic', 'plan', 'devis', 'paiement', 'prestation', 'consultation',
  'radio', 'ordonnance', 'certificat', 'labo', 'controle', 'cloture', 'document', 'autre',
];

const PHASE_LABELS: Record<string, string> = {
  diagnostic: 'Diagnostic',
  plan: 'Plan de traitement',
  devis: 'Devis',
  paiement: 'Paiements & échéances',
  prestation: 'Prestations',
  consultation: 'Consultations',
  radio: 'Radios & analyses',
  ordonnance: 'Ordonnances',
  certificat: 'Certificats',
  labo: 'Laboratoire',
  controle: 'Contrôles',
  cloture: 'Clôture',
  document: 'Documents',
  autre: 'Autre',
};

const SOURCE_LABELS: Record<string, string> = {
  appointment: 'Consultations',
  treatment_plan_step: 'Plan',
  document_archive: 'Documents',
  panoramic_analysis: 'Panoramique',
  cephalo_analysis: 'Céphalométrie',
  payment: 'Paiements',
  installment: 'Échéances',
  lab_job: 'Labo',
  journey_milestone: 'Jalons',
};

const SOURCE_ICONS: Record<string, React.ElementType> = {
  appointment: Calendar,
  treatment_plan_step: Flag,
  document_archive: FileText,
  panoramic_analysis: Radio,
  cephalo_analysis: Radio,
  payment: Banknote,
  installment: Banknote,
  lab_job: Wrench,
  journey_milestone: Flag,
};

const GREEN_STATUSES = new Set(['PAYE', 'done', 'DONE', 'TERMINÉ', 'TERMINE', 'DELIVERED', 'READY', 'ACTIF', 'CALIBRE']);
const AMBER_STATUSES = new Set(['EN_ATTENTE', 'PARTIEL', 'pending', 'PENDING', 'A_ENCAISSER', 'IN_PROGRESS', 'SENT', 'PRESCRIPTION', 'TRY_IN', 'NON_CALIBRE']);
const RED_STATUSES = new Set(['ANNULÉ', 'ANNULE', 'REFUSÉ', 'REFUSE', 'EXPIRÉ', 'EXPIRE']);

function statusColorClass(status: string): string {
  if (GREEN_STATUSES.has(status)) return 'bg-emerald-100 text-emerald-600';
  if (AMBER_STATUSES.has(status)) return 'bg-amber-100 text-amber-600';
  if (RED_STATUSES.has(status)) return 'bg-red-100 text-red-600';
  return 'bg-slate-100 text-slate-500';
}

const MILESTONE_TYPES = ['DIAGNOSTIC', 'DEVIS_VALIDE', 'CONTROLE', 'CLOTURE'] as const;

export const PatientJourney = ({ patientId }: PatientJourneyProps) => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const [fullHistory, setFullHistory] = useState(false);
  // null = aucune phase encore manipulée manuellement -> le pliage suit le défaut
  // (seule la phase la plus récente est dépliée). Dès qu'une phase est togglée, on
  // fige l'état courant (défaut inclus) dans le Set pour ne plus recalculer le défaut.
  const [expandedPhases, setExpandedPhases] = useState<Set<string> | null>(null);
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);
  const [showMilestoneModal, setShowMilestoneModal] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['patient-journey', patientId, fullHistory],
    queryFn: async () => {
      const res = await api.get(`/patients/${patientId}/journey`, { params: { full_history: fullHistory } });
      return res.data as JourneyResponse;
    },
  });

  const { data: actes = [] } = useQuery({
    queryKey: ['actes', patientId],
    queryFn: async () => {
      const res = await api.get(`/actes/patient/${patientId}`);
      return res.data as LegacyActe[];
    },
  });

  const { data: documents = [] } = useQuery({
    queryKey: ['patient-documents', patientId],
    queryFn: async () => {
      const res = await api.get(`/patients/${patientId}/documents`);
      return res.data as DocumentInfo[];
    },
  });

  const events = data?.events ?? [];
  const filteredEvents = sourceFilter ? events.filter((e) => e.source === sourceFilter) : events;

  // Basé sur les événements filtrés : un filtre actif ne doit jamais faire disparaître
  // le seul groupe restant derrière un pliage par défaut hérité de la vue non filtrée.
  const currentPhase = filteredEvents.length > 0 ? filteredEvents[0].phase_hint : null;

  const grouped = useMemo(() => {
    const map = new Map<string, JourneyEvent[]>();
    for (const ev of filteredEvents) {
      const list = map.get(ev.phase_hint) ?? [];
      list.push(ev);
      map.set(ev.phase_hint, list);
    }
    return PHASE_ORDER
      .filter((phase) => map.has(phase))
      .map((phase) => ({ phase, items: map.get(phase)! }));
  }, [filteredEvents]);

  const presentSources = useMemo(() => Array.from(new Set(events.map((e) => e.source))), [events]);

  const isPhaseExpanded = (phase: string) => {
    if (expandedPhases !== null) return expandedPhases.has(phase);
    return phase === currentPhase;
  };

  const togglePhase = (phase: string) => {
    setExpandedPhases((prev) => {
      const base = prev ?? new Set(currentPhase ? [currentPhase] : []);
      const next = new Set(base);
      if (next.has(phase)) next.delete(phase); else next.add(phase);
      return next;
    });
  };

  const toggleExpanded = (eventKey: string) => {
    setExpandedEvents((prev) => {
      const next = new Set(prev);
      if (next.has(eventKey)) next.delete(eventKey); else next.add(eventKey);
      return next;
    });
  };

  const handleOpenDocument = async (refId: number) => {
    const doc = documents.find((d) => String(d.id) === String(refId));
    if (!doc) {
      toast.error('Document introuvable.');
      return;
    }
    try {
      const clean = doc.url.startsWith('/') ? doc.url.slice(1) : doc.url;
      const res = await api.get(`/${clean}`, { responseType: 'blob' });
      const blobUrl = URL.createObjectURL(res.data);
      window.open(blobUrl, '_blank');
      setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
    } catch (err) {
      toast.error("Impossible d'ouvrir le document.");
    }
  };

  const handleEventClick = (ev: JourneyEvent) => {
    switch (ev.navigation_target) {
      case 'DOCUMENT':
        handleOpenDocument(ev.ref_id);
        break;
      case 'RADIOLOGY_TAB':
        setSearchParams({ tab: 'radiology' });
        break;
      case 'TREATMENT_PLAN_TAB':
        setSearchParams({ tab: 'admin' });
        break;
      case 'ACCOUNTING_TAB':
        setSearchParams({ tab: 'finances' });
        break;
      case 'LAB_PAGE':
        navigate('/labo');
        break;
      case 'INLINE':
      default:
        toggleExpanded(ev.event_key);
        break;
    }
  };

  const createMilestoneMutation = useMutation({
    mutationFn: async (payload: { milestone_type: string; milestone_date: string; note?: string; confirm_duplicate?: boolean }) => {
      const res = await api.post(`/patients/${patientId}/journey/milestones`, payload);
      return res.data;
    },
    onSuccess: async (result, variables) => {
      if (result.possible_duplicate && !result.milestone) {
        const confirmed = window.confirm('Un jalon identique existe déjà pour cette date. Créer quand même ?');
        if (confirmed) {
          await createMilestoneMutation.mutateAsync({ ...variables, confirm_duplicate: true });
        }
        return;
      }
      toast.success('Jalon ajouté.');
      queryClient.invalidateQueries({ queryKey: ['patient-journey', patientId] });
      setShowMilestoneModal(false);
    },
    onError: () => toast.error("Erreur lors de la création du jalon."),
  });

  const deleteMilestoneMutation = useMutation({
    mutationFn: async (milestoneId: number) => {
      await api.delete(`/patients/${patientId}/journey/milestones/${milestoneId}`);
    },
    onSuccess: () => {
      toast.success('Jalon supprimé.');
      queryClient.invalidateQueries({ queryKey: ['patient-journey', patientId] });
    },
    onError: () => toast.error("Vous n'avez pas l'autorisation de supprimer ce jalon."),
  });

  if (isLoading) {
    return <EliteGhostLoader text="Chargement du parcours patient..." size="medium" />;
  }

  if (isError || !data) {
    return (
      <div className="text-center py-16 text-text-muted font-bold">
        Impossible de charger le parcours patient.
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Bandeau résumé */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card-bg p-6 rounded-[2rem] border border-border-main shadow-sm">
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted mb-2">Plan de traitement</p>
          <div className="text-3xl font-black" style={{ color: 'var(--primary)' }}>
            {data.summary.active_plan_steps}/{data.summary.total_plan_steps}
          </div>
          <div className="text-xs text-text-muted font-bold mt-1">étapes en cours</div>
        </div>
        <div className={cn('p-6 rounded-[2rem] border shadow-sm', data.summary.remaining_due > 0 ? 'bg-red-50 border-red-100' : 'bg-card-bg border-border-main')}>
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted mb-2">Reste dû</p>
          <div className={cn('text-3xl font-black', data.summary.remaining_due > 0 ? 'text-red-600' : 'text-emerald-600')}>
            {data.summary.remaining_due.toLocaleString('fr-MA')} MAD
          </div>
        </div>
        <div className="bg-card-bg p-6 rounded-[2rem] border border-border-main shadow-sm">
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted mb-2">Prochain RDV</p>
          <div className="text-lg font-black text-slate-800">
            {data.summary.next_appointment
              ? format(new Date(data.summary.next_appointment), 'd MMM yyyy', { locale: fr })
              : '—'}
          </div>
        </div>
        <div className="bg-card-bg p-6 rounded-[2rem] border border-border-main shadow-sm">
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted mb-2">Dernier document</p>
          <div className="text-lg font-black text-slate-800">
            {data.summary.last_document_date
              ? format(new Date(data.summary.last_document_date), 'd MMM yyyy', { locale: fr })
              : '—'}
          </div>
        </div>
      </div>

      {/* Filtres + actions */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => setSourceFilter(null)}
          className={cn(
            'px-3 py-1.5 rounded-xl text-xs font-bold border transition-colors',
            sourceFilter === null ? 'bg-primary text-white border-primary' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'
          )}
        >
          Tout
        </button>
        {presentSources.map((src) => (
          <button
            key={src}
            onClick={() => setSourceFilter(src)}
            className={cn(
              'px-3 py-1.5 rounded-xl text-xs font-bold border transition-colors',
              sourceFilter === src ? 'bg-primary text-white border-primary' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'
            )}
          >
            {SOURCE_LABELS[src] ?? src}
          </button>
        ))}
        <div className="flex-1" />
        <button
          onClick={() => setShowMilestoneModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-xl font-bold hover:bg-primary/20 transition-all text-sm"
        >
          <Plus size={16} /> Ajouter un jalon
        </button>
        {!fullHistory && (
          <button
            onClick={() => setFullHistory(true)}
            className="px-4 py-2 text-xs font-bold text-slate-500 hover:text-primary transition-colors"
          >
            Voir tout l'historique
          </button>
        )}
      </div>

      {data.truncated && (
        <div className="text-xs font-bold text-amber-600 bg-amber-50 border border-amber-200 rounded-xl px-4 py-2">
          {data.events.length} événements affichés sur {data.total_events_available} — affinez les filtres pour voir le reste.
        </div>
      )}

      {/* Timeline groupée par phase */}
      {grouped.length === 0 ? (
        <div className="text-center py-16 bg-card-bg rounded-[2.5rem] border border-border-main">
          <p className="text-text-muted font-bold">Aucun événement pour l'instant.</p>
          <p className="text-text-muted text-sm mt-1">Le parcours de ce patient apparaîtra ici au fil des actes, documents et paiements.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {grouped.map(({ phase, items }) => {
            const expanded = isPhaseExpanded(phase);
            return (
              <div key={phase} className="bg-card-bg rounded-[2rem] border border-border-main shadow-sm overflow-hidden">
                <button
                  onClick={() => togglePhase(phase)}
                  className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {expanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                    <span className="font-black text-slate-800">{PHASE_LABELS[phase] ?? phase}</span>
                    <span className="text-xs font-bold text-text-muted">{items.length}</span>
                  </div>
                </button>
                {expanded && (
                  <div className="p-6 pt-0 space-y-4">
                    {items.map((ev) => {
                      const Icon = SOURCE_ICONS[ev.source] ?? FileText;
                      const isExpanded = expandedEvents.has(ev.event_key);
                      return (
                        <div key={ev.event_key} className="flex gap-4">
                          <div className="flex flex-col items-center">
                            <div className="w-10 h-10 rounded-full bg-slate-100 border-4 border-white shadow-sm flex items-center justify-center text-primary z-10">
                              <Icon size={16} />
                            </div>
                          </div>
                          <div className="flex-1 bg-white border border-slate-100 rounded-2xl p-4 shadow-sm">
                            <button
                              onClick={() => handleEventClick(ev)}
                              className="w-full flex items-center justify-between text-left group"
                            >
                              <div>
                                <div className="font-bold text-slate-800">{ev.title}</div>
                                <div className="text-xs text-text-muted font-bold">
                                  {format(new Date(ev.date), "d MMM yyyy 'à' HH:mm", { locale: fr })}
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className={cn('px-2 py-0.5 rounded-md text-[10px] uppercase tracking-widest font-bold', statusColorClass(ev.status))}>
                                  {ev.status}
                                </span>
                                {ev.navigation_target !== 'INLINE' && (
                                  <ExternalLink size={14} className="text-slate-300 group-hover:text-primary transition-colors" />
                                )}
                              </div>
                            </button>
                            {ev.related_event_key && (
                              <p className="text-[11px] text-slate-400 font-bold mt-1">
                                Généré depuis une analyse liée
                              </p>
                            )}
                            {ev.source === 'journey_milestone' && isExpanded && (
                              <div className="mt-3 pt-3 border-t border-slate-100 flex justify-end">
                                <button
                                  onClick={() => deleteMilestoneMutation.mutate(ev.ref_id)}
                                  className="flex items-center gap-1 text-xs font-bold text-red-500 hover:text-red-600"
                                >
                                  <Trash2 size={14} /> Supprimer ce jalon
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Actes historiques (legacy — patients avec des Acte réels, ~13% du cabinet) */}
      {actes.length > 0 && (
        <div className="bg-card-bg rounded-[2.5rem] border border-border-main shadow-sm overflow-hidden">
          <button
            onClick={() => togglePhase('__legacy_actes__')}
            className="w-full flex items-center justify-between px-8 py-6 hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              {isPhaseExpanded('__legacy_actes__') ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
              <h2 className="text-lg font-black">Actes historiques ({actes.length})</h2>
            </div>
          </button>
          {isPhaseExpanded('__legacy_actes__') && (
            <div className="p-8 pt-0 space-y-6">
              {actes.map((acte) => (
                <div key={acte.id} className="bg-white border border-slate-100 rounded-3xl p-6 shadow-sm">
                  <h3 className="text-lg font-black text-slate-800 mb-3">{acte.libelle}</h3>
                  <LegacyActeNotes acte={acte} patientId={patientId} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {showMilestoneModal && (
        <MilestoneCreateModal
          onClose={() => setShowMilestoneModal(false)}
          onSubmit={(payload) => createMilestoneMutation.mutate(payload)}
          isSubmitting={createMilestoneMutation.isPending}
        />
      )}
    </div>
  );
};

function MilestoneCreateModal({
  onClose,
  onSubmit,
  isSubmitting,
}: {
  onClose: () => void;
  onSubmit: (payload: { milestone_type: string; milestone_date: string; note?: string }) => void;
  isSubmitting: boolean;
}) {
  const [milestoneType, setMilestoneType] = useState<string>(MILESTONE_TYPES[0]);
  const [milestoneDate, setMilestoneDate] = useState<string>(new Date().toISOString().slice(0, 10));
  const [note, setNote] = useState('');

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-3xl p-6 w-full max-w-md shadow-xl">
        <h3 className="text-lg font-black mb-4">Ajouter un jalon</h3>
        <div className="space-y-4">
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Type</label>
            <select
              value={milestoneType}
              onChange={(e) => setMilestoneType(e.target.value)}
              className="w-full mt-1 border border-slate-200 rounded-xl p-2.5 text-sm"
            >
              {MILESTONE_TYPES.map((t) => (
                <option key={t} value={t}>{t.replace('_', ' ')}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Date</label>
            <input
              type="date"
              value={milestoneDate}
              onChange={(e) => setMilestoneDate(e.target.value)}
              className="w-full mt-1 border border-slate-200 rounded-xl p-2.5 text-sm"
            />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Note (optionnel)</label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full mt-1 border border-slate-200 rounded-xl p-2.5 text-sm min-h-[80px]"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <button onClick={onClose} className="px-4 py-2 text-sm font-bold text-slate-500 hover:bg-slate-100 rounded-lg">
            Annuler
          </button>
          <button
            disabled={isSubmitting}
            onClick={() => onSubmit({ milestone_type: milestoneType, milestone_date: `${milestoneDate}T00:00:00`, note: note || undefined })}
            className="px-4 py-2 text-sm font-bold bg-primary text-white hover:bg-primary/90 rounded-lg disabled:opacity-50"
          >
            Enregistrer
          </button>
        </div>
      </div>
    </div>
  );
}

import { useQuery } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CalendarClock, ChevronRight, FileImage, ScanLine, Waypoints, Clock3, Activity } from 'lucide-react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { fetchOrthoCockpit, type OrthoCockpitEvidence } from './orthoCockpit';

interface Props {
  patientId: number;
}

const phaseLabel = (value: string | null) =>
  value ? value.replaceAll('_', ' ').toLocaleLowerCase('fr-FR').replace(/^./, c => c.toUpperCase()) : 'Non renseignée';

const lifecycleLabel: Record<string, string> = {
  ACTIVE: 'Actif',
  INTERRUPTED: 'Interrompu',
  ABANDONED: 'Abandonné',
  CLOSED: 'Clôturé',
};

const dateLabel = (value: string | null | undefined, withTime = false) => {
  if (!value) return 'Non renseigné';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Non renseigné';
  return format(date, withTime ? "d MMM yyyy · HH:mm" : 'd MMM yyyy', { locale: fr });
};

const evidenceIcon = (kind: string) => {
  if (kind === 'CEPHALO') return <Waypoints size={14} />;
  if (kind === 'PANORAMIC') return <ScanLine size={14} />;
  return <FileImage size={14} />;
};

const EvidenceButton = ({ item, onOpen }: { item: OrthoCockpitEvidence; onOpen: (item: OrthoCockpitEvidence) => void }) => (
  <button
    type="button"
    onClick={() => onOpen(item)}
    className="inline-flex min-h-9 min-w-0 items-center gap-1.5 rounded-xl border border-border-main bg-card-bg px-2.5 py-1.5 text-left text-[10px] font-black text-main transition-colors hover:border-primary/30 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
  >
    <span className="shrink-0 text-primary">{evidenceIcon(item.kind)}</span>
    <span className="truncate">{item.label}</span>
    <span className="shrink-0 text-text-muted">T{item.timepoint_ordinal}</span>
  </button>
);

export const OrthoCockpitPanel = ({ patientId }: Props) => {
  const navigate = useNavigate();
  const [, setSearchParams] = useSearchParams();
  const query = useQuery({
    queryKey: ['ortho-cockpit', patientId],
    queryFn: () => fetchOrthoCockpit(patientId),
  });

  if (query.isLoading) {
    return (
      <section data-ortho-f4-cockpit className="rounded-[1.5rem] border border-border-main bg-card-bg p-4 shadow-sm sm:rounded-[2rem]">
        <div className="flex items-center gap-2 text-sm font-black text-text-muted"><Activity size={16} className="animate-pulse" />Chargement du suivi orthodontique…</div>
      </section>
    );
  }

  if (query.isError || !query.data) {
    return (
      <section data-ortho-f4-cockpit className="rounded-[1.5rem] border border-border-main bg-card-bg p-4 shadow-sm sm:rounded-[2rem]">
        <p className="text-sm font-black text-main">Cockpit orthodontique indisponible</p>
        <p className="mt-1 text-xs font-bold text-text-muted">Les données orthodontiques n’ont pas pu être chargées.</p>
      </section>
    );
  }

  const data = query.data;
  if (!data.case) return null;

  const openEvidence = (item: OrthoCockpitEvidence) => {
    const radioTab = item.kind === 'CEPHALO' ? 'cephalo' : item.kind === 'PANORAMIC' ? 'panoramic' : 'media';
    setSearchParams({ tab: 'radiology', radioTab });
  };

  const evidences = [data.latest_cephalo, data.latest_panoramic, data.latest_clinical_asset].filter(Boolean) as OrthoCockpitEvidence[];
  const latestControl = data.latest_control;
  const plannedControl = latestControl?.next_control_at ?? null;
  const nextStep = latestControl?.next_planned_step ?? null;

  const scrollToCompare = () => {
    document.querySelector('[data-ortho-f3-compare]')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <section
      data-ortho-f4-cockpit
      aria-label="Cockpit orthodontique"
      className="overflow-hidden rounded-[1.5rem] border border-border-main bg-card-bg shadow-sm sm:rounded-[2rem]"
    >
      <div className="border-b border-border-main px-3.5 py-3 sm:px-5 sm:py-4 md:px-6">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-[9px] font-black uppercase tracking-[0.16em] text-text-muted sm:text-[10px]">Suivi orthodontique</p>
            <div className="mt-1 flex flex-wrap items-baseline gap-x-2 gap-y-1">
              <h2 className="text-base font-black tracking-tight text-main sm:text-lg md:text-xl">{phaseLabel(data.case.current_phase_key)}</h2>
              <span className="rounded-full border border-primary/15 bg-primary/5 px-2 py-0.5 text-[9px] font-black uppercase tracking-wide text-primary">
                {lifecycleLabel[data.case.lifecycle_status] ?? data.case.lifecycle_status}
              </span>
            </div>
            <p className="mt-1 text-[11px] font-bold text-text-muted sm:text-xs">
              Début {dateLabel(data.case.started_at)} · {data.case.controls_count} contrôle{data.case.controls_count > 1 ? 's' : ''} structuré{data.case.controls_count > 1 ? 's' : ''}
            </p>
          </div>
          {data.latest_timepoint && (
            <span className="rounded-xl border border-border-main bg-background px-2.5 py-1.5 text-[10px] font-black text-main">
              T{data.latest_timepoint.ordinal} · {dateLabel(data.latest_timepoint.occurred_at)}
            </span>
          )}
        </div>
      </div>

      <div className="grid min-w-0 grid-cols-1 divide-y divide-border-main md:grid-cols-3 md:divide-x md:divide-y-0">
        <div className="min-w-0 px-3.5 py-3 sm:px-5 md:px-5">
          <p className="text-[9px] font-black uppercase tracking-[0.14em] text-text-muted">État actuel</p>
          <div className="mt-2 space-y-1.5 text-xs">
            <div className="flex items-center justify-between gap-3"><span className="font-bold text-text-muted">Phase</span><span className="truncate font-black text-main">{phaseLabel(data.case.current_phase_key)}</span></div>
            <div className="flex items-center justify-between gap-3"><span className="font-bold text-text-muted">Statut</span><span className="font-black text-main">{lifecycleLabel[data.case.lifecycle_status] ?? data.case.lifecycle_status}</span></div>
            <div className="flex items-center justify-between gap-3"><span className="font-bold text-text-muted">Dernier repère</span><span className="font-black text-main">{data.latest_timepoint ? `T${data.latest_timepoint.ordinal}` : 'Non renseigné'}</span></div>
          </div>
        </div>

        <div className="min-w-0 px-3.5 py-3 sm:px-5 md:px-5">
          <p className="text-[9px] font-black uppercase tracking-[0.14em] text-text-muted">Dernier contrôle</p>
          {latestControl ? (
            <div className="mt-2 space-y-1.5">
              <p className="text-sm font-black text-main">{dateLabel(latestControl.occurred_at)}</p>
              <p className="text-[11px] font-bold text-text-muted">{latestControl.notable_event || 'Aucun événement notable renseigné'}</p>
              {nextStep && <p className="line-clamp-2 text-[11px] font-bold text-main">Étape suivante : {nextStep}</p>}
            </div>
          ) : (
            <p className="mt-2 text-xs font-bold text-text-muted">Aucun contrôle structuré enregistré</p>
          )}
        </div>

        <div className="min-w-0 px-3.5 py-3 sm:px-5 md:px-5">
          <p className="text-[9px] font-black uppercase tracking-[0.14em] text-text-muted">Suite & preuves</p>
          <div className="mt-2 space-y-2">
            <div className="space-y-1 text-[11px]">
              <div className="flex items-start gap-2"><Clock3 size={13} className="mt-0.5 shrink-0 text-primary" /><span><strong className="text-main">Contrôle prévu :</strong> <span className="font-bold text-text-muted">{dateLabel(plannedControl)}</span></span></div>
              <div className="flex items-start gap-2"><CalendarClock size={13} className="mt-0.5 shrink-0 text-primary" /><span><strong className="text-main">RDV réel :</strong> <span className="font-bold text-text-muted">{data.next_appointment ? dateLabel(data.next_appointment.datetime_start, true) : 'Aucun rendez-vous futur enregistré'}</span></span></div>
            </div>
            {evidences.length > 0 ? <div className="flex flex-wrap gap-1.5">{evidences.map(item => <EvidenceButton key={`${item.kind}-${item.ref_id}`} item={item} onOpen={openEvidence} />)}</div> : <p className="text-[11px] font-bold text-text-muted">Aucune preuve canonique liée</p>}
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-2 border-t border-border-main px-3.5 py-2.5 sm:flex-row sm:items-center sm:justify-between sm:px-5 md:px-6">
        <div className="min-w-0">
          {data.attention.includes('TREATMENT_INTERRUPTED') && <p className="text-[10px] font-black text-text-muted">Traitement enregistré comme interrompu.</p>}
          {data.attention.includes('LATEST_TIMEPOINT_WITHOUT_EVIDENCE') && <p className="text-[10px] font-black text-text-muted">Dernier timepoint sans preuve liée.</p>}
          {!data.latest_timepoint && <p className="text-[10px] font-black text-text-muted">Aucun timepoint enregistré.</p>}
          {nextStep && <p className="truncate text-[10px] font-black text-text-muted">Prochaine étape planifiée présente.</p>}
        </div>
        <div className="flex gap-1.5">
          {data.next_appointment && <button type="button" onClick={() => navigate('/agenda')} className="inline-flex min-h-10 items-center justify-center rounded-xl border border-border-main px-3 text-[10px] font-black uppercase tracking-wide text-main hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30">Agenda</button>}
          <button type="button" onClick={scrollToCompare} className="inline-flex min-h-10 items-center justify-center gap-1 rounded-xl bg-primary px-3 text-[10px] font-black uppercase tracking-wide text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30">
            Voir comparaison <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </section>
  );
};

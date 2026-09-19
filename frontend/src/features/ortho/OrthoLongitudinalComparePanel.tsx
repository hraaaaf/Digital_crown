import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { ArrowLeftRight, FileImage, Layers3, ScanLine, Waypoints } from 'lucide-react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { cn } from '../../utils/cn';
import { hasAccess } from '../../utils/accessControl';
import { useAuthStore } from '../../stores/useAuthStore';
import { OrthoSuperimpositionViewer } from './OrthoSuperimpositionViewer';
import {
  fetchOrthoCase,
  fetchOrthoLongitudinalCompare,
  fetchOrthoTimepoints,
  type OrthoCompareEvidence,
} from './orthoLongitudinalCompare';

interface Props {
  patientId: number;
}

const evidenceIcon = (kind: string) => {
  if (kind === 'CEPHALO') return <Waypoints size={14} />;
  if (kind === 'PANORAMIC') return <ScanLine size={14} />;
  return <FileImage size={14} />;
};

const signed = (value: number, unit: string) => {
  const rounded = Math.abs(value) < 0.00005 ? 0 : value;
  const prefix = rounded > 0 ? '+' : '';
  return `${prefix}${rounded.toLocaleString('fr-FR', { maximumFractionDigits: 2 })} ${unit}`;
};

const valueLabel = (value: number, unit: string) =>
  `${value.toLocaleString('fr-FR', { maximumFractionDigits: 2 })} ${unit}`;

const EvidenceLane = ({ items, onOpen }: { items: OrthoCompareEvidence[]; onOpen: (item: OrthoCompareEvidence) => void }) => (
  <div className="space-y-1.5 sm:space-y-2">
    {items.length === 0 ? (
      <p className="text-xs font-bold text-text-muted">Aucune preuve liée</p>
    ) : (
      items.map((item) => (
        <button
          type="button"
          key={`${item.kind}:${item.ref_id}`}
          onClick={() => onOpen(item)}
          className="flex w-full items-center justify-between gap-2 rounded-lg border border-border-main bg-white/60 px-2.5 py-1.5 text-left transition-colors hover:bg-white sm:gap-3 sm:rounded-xl sm:px-3 sm:py-2"
          aria-label={`Ouvrir la source ${item.label} #${item.ref_id}`}
        >
          <div className="flex min-w-0 items-center gap-2 text-slate-700">
            <span className="shrink-0 text-primary">{evidenceIcon(item.kind)}</span>
            <span className="truncate text-xs font-black">{item.label}</span>
          </div>
          <span className="shrink-0 font-mono text-[10px] font-bold text-text-muted">#{item.ref_id}</span>
        </button>
      ))
    )}
  </div>
);

export const OrthoLongitudinalComparePanel = ({ patientId }: Props) => {
  const [, setSearchParams] = useSearchParams();
  const [fromOrdinal, setFromOrdinal] = useState<number | null>(null);
  const [toOrdinal, setToOrdinal] = useState<number | null>(null);
  const [superimpositionOpen, setSuperimpositionOpen] = useState(false);
  const user = useAuthStore((state) => state.user);
  const canUseCephalo = hasAccess(user, 'cephalo');

  const caseQuery = useQuery({
    queryKey: ['ortho-case', patientId],
    queryFn: () => fetchOrthoCase(patientId),
  });
  const caseId = caseQuery.data?.id ?? null;

  const timepointsQuery = useQuery({
    queryKey: ['ortho-timepoints', patientId, caseId],
    queryFn: () => fetchOrthoTimepoints(patientId, caseId!),
    enabled: caseId !== null,
  });

  const timepoints = useMemo(
    () => [...(timepointsQuery.data ?? [])].sort((a, b) => a.ordinal - b.ordinal),
    [timepointsQuery.data],
  );

  useEffect(() => {
    if (timepoints.length < 2) return;
    setFromOrdinal((current) => current ?? timepoints[0].ordinal);
    setToOrdinal((current) => current ?? timepoints[timepoints.length - 1].ordinal);
  }, [timepoints]);

  const comparisonQuery = useQuery({
    queryKey: ['ortho-timepoint-compare', patientId, caseId, fromOrdinal, toOrdinal],
    queryFn: () => fetchOrthoLongitudinalCompare(patientId, caseId!, fromOrdinal!, toOrdinal!),
    enabled: caseId !== null && fromOrdinal !== null && toOrdinal !== null && fromOrdinal !== toOrdinal,
  });

  if (caseQuery.isLoading || timepointsQuery.isLoading) return null;
  if (caseQuery.isError || timepointsQuery.isError) {
    return (
      <section className="rounded-[2rem] border border-border-main bg-card-bg p-5 shadow-sm">
        <p className="text-sm font-black text-slate-700">Comparaison orthodontique indisponible</p>
        <p className="mt-1 text-xs font-bold text-text-muted">Impossible de charger les repères orthodontiques.</p>
      </section>
    );
  }
  if (!caseQuery.data || timepoints.length === 0) return null;

  if (timepoints.length === 1) {
    return (
      <section className="rounded-[2rem] border border-border-main bg-card-bg p-5 shadow-sm" aria-label="Comparaison orthodontique">
        <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted">Comparaison orthodontique</p>
        <p className="mt-2 text-sm font-black text-slate-700">Un second timepoint est nécessaire pour comparer.</p>
      </section>
    );
  }

  const comparison = comparisonQuery.data;

  const openEvidence = (item: OrthoCompareEvidence) => {
    const radioTab =
      item.kind === 'CEPHALO'
        ? 'cephalo'
        : item.kind === 'PANORAMIC'
          ? 'panoramic'
          : 'media';
    setSearchParams({ tab: 'radiology', radioTab });
  };

  const swap = () => {
    if (fromOrdinal === null || toOrdinal === null) return;
    setFromOrdinal(toOrdinal);
    setToOrdinal(fromOrdinal);
  };

  return (
    <section
      className="rounded-[1.5rem] border border-border-main bg-card-bg p-3 shadow-sm sm:rounded-[2rem] sm:p-5 md:p-6"
      aria-label="Comparaison orthodontique"
      data-ortho-f3-compare
    >
      <div className="mb-3 flex flex-col gap-1.5 sm:mb-4 sm:gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted">Suivi longitudinal</p>
          <h2 className="mt-0.5 text-base font-black text-slate-800 sm:mt-1 sm:text-lg md:text-xl">Comparaison orthodontique</h2>
          <p className="mt-0.5 text-[11px] font-bold leading-4 text-text-muted sm:mt-1 sm:text-xs sm:leading-normal">Comparer deux repères du traitement sans interprétation automatique.</p>
        </div>
        {comparison && (
          <span className="self-start rounded-full border border-border-main bg-slate-50 px-2.5 py-0.5 text-[9px] font-black text-text-muted sm:px-3 sm:py-1 sm:text-[10px]">
            {comparison.from_timepoint.evidences.length + comparison.to_timepoint.evidences.length} preuves
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 gap-2 sm:gap-3 md:grid-cols-[1fr_auto_1fr] md:items-stretch">
        <TimepointSelector
          label="Repère initial"
          value={fromOrdinal}
          options={timepoints.map((t) => t.ordinal)}
          onChange={setFromOrdinal}
          disabledOrdinal={toOrdinal}
        />
        <button
          type="button"
          onClick={swap}
          className="mx-auto flex h-8 w-8 items-center justify-center rounded-lg border border-border-main bg-slate-50 text-slate-500 transition-colors hover:text-primary sm:h-9 sm:w-9 sm:rounded-xl md:self-center"
          aria-label="Permuter les timepoints"
        >
          <ArrowLeftRight size={15} />
        </button>
        <TimepointSelector
          label="Repère comparé"
          value={toOrdinal}
          options={timepoints.map((t) => t.ordinal)}
          onChange={setToOrdinal}
          disabledOrdinal={fromOrdinal}
        />
      </div>

      {comparisonQuery.isError && (
        <div className="mt-4 rounded-2xl border border-border-main bg-slate-50 p-4 text-xs font-bold text-text-muted">
          Comparaison indisponible. Les timepoints restent inchangés.
        </div>
      )}

      {comparison && (
        <>
          <div className="mt-3 grid grid-cols-1 gap-2 sm:mt-4 sm:gap-3 md:grid-cols-2">
            {[comparison.from_timepoint, comparison.to_timepoint].map((tp) => (
              <div key={tp.id} className="rounded-xl border border-border-main bg-slate-50/60 p-3 sm:rounded-2xl sm:p-4">
                <div className="mb-2 flex items-baseline justify-between gap-2 sm:mb-3 sm:gap-3">
                  <div className="text-base font-black text-slate-800 sm:text-lg">T{tp.ordinal}</div>
                  <div className="text-[11px] font-bold text-text-muted">
                    {format(new Date(tp.occurred_at), 'd MMM yyyy', { locale: fr })}
                  </div>
                </div>
                <EvidenceLane items={tp.evidences} onOpen={openEvidence} />
              </div>
            ))}
          </div>

          <div className="mt-3 rounded-xl border border-border-main bg-white/60 p-2.5 sm:mt-4 sm:rounded-2xl sm:p-4">
            <div className="mb-2 sm:mb-3">
              <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted">Mesures communes</p>
              <p className="mt-1 text-[11px] font-bold text-text-muted">Variation numérique — interprétation clinique par le praticien.</p>
            </div>

            {comparison.measurements.length === 0 ? (
              <p className="text-xs font-bold text-text-muted">
                {comparison.measurement_status === 'AMBIGUOUS_CEPHALO_PAIR'
                  ? 'Plusieurs céphalométries sont liées à un timepoint : aucune sélection automatique.'
                  : 'Aucune mesure céphalométrique commune exploitable.'}
              </p>
            ) : (
              <>
                <div className="hidden overflow-hidden rounded-xl border border-border-main sm:block">
                  <div className="grid grid-cols-4 bg-slate-50 px-3 py-2 text-[10px] font-black uppercase tracking-wide text-text-muted">
                    <span>Mesure</span><span>T{comparison.from_timepoint.ordinal}</span><span>T{comparison.to_timepoint.ordinal}</span><span>Δ numérique</span>
                  </div>
                  {comparison.measurements.map((m) => (
                    <div key={m.key} className="grid grid-cols-4 border-t border-border-main px-3 py-2.5 text-xs">
                      <span className="font-black text-slate-700">{m.label}</span>
                      <span className="font-bold text-slate-600">{valueLabel(m.from_value, m.unit)}</span>
                      <span className="font-bold text-slate-600">{valueLabel(m.to_value, m.unit)}</span>
                      <span className="font-black text-slate-800">{signed(m.delta, m.unit)}</span>
                    </div>
                  ))}
                </div>

                <div className="space-y-1.5 sm:hidden">
                  {comparison.measurements.map((m) => (
                    <div key={m.key} className="rounded-lg border border-border-main bg-slate-50/70 px-2.5 py-2">
                      <div className="text-xs font-black text-slate-700">{m.label}</div>
                      <div className="mt-0.5 text-[10px] font-bold leading-4 text-text-muted">
                        T{comparison.from_timepoint.ordinal} {valueLabel(m.from_value, m.unit)} → T{comparison.to_timepoint.ordinal} {valueLabel(m.to_value, m.unit)}
                      </div>
                      <div className="mt-0.5 text-[11px] font-black text-slate-800">Δ {signed(m.delta, m.unit)}</div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          {(() => {
            const fromCephalo = comparison.from_timepoint.evidences.filter((item) => item.kind === 'CEPHALO');
            const toCephalo = comparison.to_timepoint.evidences.filter((item) => item.kind === 'CEPHALO');
            const chronological = comparison.from_timepoint.ordinal < comparison.to_timepoint.ordinal;
            const canOpenF5 = canUseCephalo && fromCephalo.length === 1 && toCephalo.length === 1 && chronological;
            return (
              <div className="mt-3 flex flex-col gap-2 rounded-xl border border-border-main bg-slate-50/60 p-3 sm:mt-4 sm:flex-row sm:items-center sm:justify-between sm:rounded-2xl sm:p-4">
                <div className="min-w-0">
                  <p className="text-xs font-black text-main">Superposition structurale F5</p>
                  <p className="mt-0.5 text-[11px] font-bold text-text-muted">
                    {canOpenF5
                      ? 'Comparer visuellement les deux céphalogrammes canoniques, sans interprétation automatique.'
                      : !canUseCephalo
                        ? 'Permission céphalométrie requise pour ouvrir F5.'
                        : !chronological
                          ? 'Remettez les timepoints dans l’ordre chronologique pour ouvrir F5.'
                          : 'Une céphalométrie canonique unique est requise à chaque timepoint.'}
                  </p>
                </div>
                <button
                  type="button"
                  disabled={!canOpenF5}
                  onClick={() => setSuperimpositionOpen(true)}
                  className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-xl border border-border-main bg-card-bg px-4 text-[10px] font-black uppercase tracking-wide text-main transition-colors hover:border-primary/30 hover:text-primary disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
                >
                  <Layers3 size={14} /> Superposition scientifique
                </button>
              </div>
            );
          })()}

          {superimpositionOpen && (
            <OrthoSuperimpositionViewer
              patientId={patientId}
              caseId={comparison.ortho_case_id}
              fromTimepoint={comparison.from_timepoint}
              toTimepoint={comparison.to_timepoint}
              onClose={() => setSuperimpositionOpen(false)}
            />
          )}
        </>
      )}
    </section>
  );
};

const TimepointSelector = ({
  label,
  value,
  options,
  onChange,
  disabledOrdinal,
}: {
  label: string;
  value: number | null;
  options: number[];
  onChange: (value: number) => void;
  disabledOrdinal: number | null;
}) => (
  <label className="block rounded-xl border border-border-main bg-slate-50/70 p-2.5 sm:rounded-2xl sm:p-3">
    <span className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted">{label}</span>
    <select
      value={value ?? ''}
      onChange={(event) => onChange(Number(event.target.value))}
      className={cn(
        'mt-1.5 w-full rounded-lg border border-border-main bg-white px-2.5 py-1.5 text-sm font-black text-slate-800 outline-none sm:mt-2 sm:rounded-xl sm:px-3 sm:py-2',
        'focus:border-primary/40 focus:ring-2 focus:ring-primary/10',
      )}
    >
      {options.map((ordinal) => (
        <option key={ordinal} value={ordinal} disabled={ordinal === disabledOrdinal}>
          T{ordinal}
        </option>
      ))}
    </select>
  </label>
);

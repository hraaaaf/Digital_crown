import { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { CircleDollarSign, ShieldCheck, Stethoscope, UserRoundCheck, UsersRound } from 'lucide-react';

import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';

interface PractitionerOption {
  id: number;
  name: string;
  role: string;
}

interface AssignmentResponse {
  patient_id: number;
  practitioner: PractitionerOption | null;
}

interface PractitionerFinanceRow {
  practitioner_id: number;
  practitioner_name: string;
  act_count: number;
  total_billed: number;
  linked_collected: number;
  linked_remaining_due: number;
}

interface FinancialBreakdown {
  by_practitioner?: PractitionerFinanceRow[];
  unattributed_collected?: number;
}

const money = (value: number) => `${value.toLocaleString('fr-MA')} MAD`;

export const PatientPractitionerContextPortal = ({ patientId }: { patientId: number }) => {
  const [searchParams] = useSearchParams();
  const tab = searchParams.get('tab') || 'tracking';
  const isDocuments = tab === 'admin' || tab === 'archives';
  const isFinances = tab === 'finances';
  const [target, setTarget] = useState<HTMLElement | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (isDocuments) {
      setTarget(null);
      return;
    }

    const resolve = () => {
      const node = document.querySelector<HTMLElement>('[data-flow-patient-surface]');
      if (node) setTarget(node);
      return Boolean(node);
    };

    if (resolve()) return;
    const observer = new MutationObserver(() => {
      if (resolve()) observer.disconnect();
    });
    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [isDocuments, patientId]);

  const optionsQuery = useQuery<PractitionerOption[]>({
    queryKey: ['patient-practitioner-options'],
    queryFn: async () => (await api.get('/patients/_clinic/practitioners')).data,
    staleTime: 60_000,
  });

  const assignmentQuery = useQuery<AssignmentResponse>({
    queryKey: ['patient-practitioner', patientId],
    queryFn: async () => (await api.get(`/patients/${patientId}/practitioner`)).data,
  });

  const financeQuery = useQuery<FinancialBreakdown>({
    queryKey: ['patient-financial-snapshot', patientId],
    queryFn: async () => (await api.get(`/patients/${patientId}/financial-snapshot`)).data,
    enabled: isFinances,
  });

  const assignMutation = useMutation({
    mutationFn: async (practitionerId: number | null) => (
      await api.put(`/patients/${patientId}/practitioner`, { practitioner_id: practitionerId })
    ).data as AssignmentResponse,
    onSuccess: (data) => {
      queryClient.setQueryData(['patient-practitioner', patientId], data);
    },
  });

  const selectedId = assignmentQuery.data?.practitioner?.id ?? '';
  const selectedName = assignmentQuery.data?.practitioner?.name ?? 'Non attribué';
  const practitionerCount = optionsQuery.data?.length ?? 0;
  const breakdown = financeQuery.data?.by_practitioner ?? [];
  const unattributed = financeQuery.data?.unattributed_collected ?? 0;

  const options = useMemo(
    () => [...(optionsQuery.data ?? [])].sort((a, b) => a.name.localeCompare(b.name, 'fr')),
    [optionsQuery.data],
  );

  if (!target || isDocuments) return null;

  return createPortal(
    <div className="mb-6 space-y-3" data-p2-practitioner-context>
      <section className="relative min-w-0 overflow-hidden rounded-[2rem] border border-blue-100/80 bg-white/80 p-4 shadow-[0_18px_50px_-34px_rgba(0,51,128,0.45)] backdrop-blur-xl sm:p-5">
        <div className="pointer-events-none absolute -right-12 -top-16 h-40 w-40 rounded-full bg-blue-100/60 blur-3xl" />
        <div className="relative flex min-w-0 flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[#003380] text-white shadow-lg shadow-blue-900/15">
              <UserRoundCheck size={20} />
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">Référent clinique</p>
                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-100 bg-emerald-50 px-2 py-1 text-[9px] font-black uppercase tracking-wide text-emerald-700">
                  <ShieldCheck size={11} /> Dossier local
                </span>
              </div>
              <p className="mt-1 truncate text-sm font-black text-slate-900">{selectedName}</p>
              <p className="mt-0.5 text-[11px] font-semibold text-slate-400">
                Attribution clinique additive. Patients et documents locaux inchangés.
              </p>
            </div>
          </div>

          <div className="min-w-0 lg:w-[340px]">
            <label className="mb-1.5 flex items-center gap-1.5 text-[9px] font-black uppercase tracking-[0.14em] text-slate-400">
              <Stethoscope size={12} /> Praticien référent
            </label>
            <select
              value={selectedId}
              disabled={optionsQuery.isLoading || assignmentQuery.isLoading || assignMutation.isPending}
              onChange={(event) => assignMutation.mutate(event.target.value ? Number(event.target.value) : null)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-black text-slate-800 outline-none transition focus:border-[#003380]/40 focus:ring-4 focus:ring-[#003380]/10 disabled:opacity-60"
              aria-label="Praticien référent"
            >
              <option value="">Non attribué</option>
              {options.map((practitioner) => (
                <option key={practitioner.id} value={practitioner.id}>{practitioner.name}</option>
              ))}
            </select>
            <p className="mt-1.5 flex items-center gap-1 text-[10px] font-semibold text-slate-400">
              <UsersRound size={11} /> {practitionerCount} praticien{practitionerCount > 1 ? 's' : ''} assignable{practitionerCount > 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </section>

      {isFinances && (breakdown.length > 0 || unattributed > 0) && (
        <section className="rounded-[2rem] border border-slate-200/80 bg-white/80 p-4 shadow-sm backdrop-blur-xl sm:p-5" aria-label="Production par praticien">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">Production par praticien</p>
              <h3 className="mt-1 text-base font-black text-slate-900">Facturation traçable</h3>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1.5 text-[10px] font-black text-[#003380]">
              <CircleDollarSign size={13} /> Source : actes + paiements liés
            </span>
          </div>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {breakdown.map((row) => (
              <div key={row.practitioner_id} className="min-w-0 rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
                <p className="truncate text-xs font-black text-slate-800">{row.practitioner_name}</p>
                <p className="mt-0.5 text-[10px] font-bold text-slate-400">{row.act_count} acte{row.act_count > 1 ? 's' : ''}</p>
                <div className="mt-3 grid grid-cols-3 gap-2 text-[10px]">
                  <Metric label="Facturé" value={money(row.total_billed)} />
                  <Metric label="Encaissé" value={money(row.linked_collected)} positive />
                  <Metric label="Reste" value={money(row.linked_remaining_due)} warning={row.linked_remaining_due > 0} />
                </div>
              </div>
            ))}
          </div>

          {unattributed > 0 && (
            <div className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3">
              <p className="text-[10px] font-black uppercase tracking-[0.12em] text-amber-700">Encaissements non attribués</p>
              <p className="mt-1 text-sm font-black text-amber-900">{money(unattributed)}</p>
              <p className="mt-0.5 text-[10px] font-semibold text-amber-700/80">Paiement réel, mais aucun acte ne permet de l'affecter honnêtement à un praticien.</p>
            </div>
          )}
        </section>
      )}
    </div>,
    target,
  );
};

const Metric = ({ label, value, positive = false, warning = false }: { label: string; value: string; positive?: boolean; warning?: boolean }) => (
  <div className="min-w-0">
    <p className="font-black uppercase tracking-wide text-slate-400">{label}</p>
    <p className={cn('mt-1 break-words font-black text-slate-700', positive && 'text-emerald-600', warning && 'text-rose-600')}>{value}</p>
  </div>
);

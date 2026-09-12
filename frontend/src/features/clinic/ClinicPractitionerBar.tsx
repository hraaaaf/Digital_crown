import React, { useEffect, useMemo, useState } from 'react';
import { Check, Stethoscope, UsersRound } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { api } from '../../services/api';
import { useAuthStore } from '../../stores/useAuthStore';
import { cn } from '../../utils/cn';
import {
  type ClinicPractitioner,
  usePractitionerContextStore,
} from './practitionerContext';

const initials = (name: string) => {
  const parts = name
    .replace(/^dr\.?\s*/i, '')
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  return (parts[0]?.[0] || 'P') + (parts[1]?.[0] || '');
};

const resolveFallbackPractitioner = (user: ReturnType<typeof useAuthStore.getState>['user']): ClinicPractitioner[] => {
  if (!user) return [];

  const numericUserId = Number(user.id);
  const numericEmployerId = Number(user.employer_id);
  const isSecretary = user.role === 'SECRETAIRE';
  const practitionerId = isSecretary && Number.isFinite(numericEmployerId)
    ? numericEmployerId
    : numericUserId;

  if (!Number.isFinite(practitionerId)) return [];

  const name = isSecretary
    ? 'Praticien principal'
    : user.nom_complet || user.full_name || user.email || 'Praticien principal';

  return [{ id: practitionerId, name, isFallback: true }];
};

export const ClinicPractitionerBar: React.FC = () => {
  const location = useLocation();
  const user = useAuthStore((state) => state.user);
  const practitioners = usePractitionerContextStore((state) => state.practitioners);
  const selectedPractitionerId = usePractitionerContextStore((state) => state.selectedPractitionerId);
  const setPractitioners = usePractitionerContextStore((state) => state.setPractitioners);
  const selectPractitioner = usePractitionerContextStore((state) => state.selectPractitioner);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const loadPractitioners = async () => {
      setLoading(true);
      const fallback = resolveFallbackPractitioner(user);

      try {
        const start = new Date();
        start.setHours(0, 0, 0, 0);
        const end = new Date(start);
        end.setHours(23, 59, 59, 999);

        const response = await api.get('/appointments/multi-practitioner', {
          params: {
            start_date: start.toISOString(),
            end_date: end.toISOString(),
          },
        });

        const dentists = Array.isArray(response.data?.dentists)
          ? response.data.dentists
          : [];
        const next: ClinicPractitioner[] = dentists
          .map((dentist: any) => ({
            id: Number(dentist.dentist_id),
            name: dentist.dentist_name || `Praticien ${dentist.dentist_id}`,
            appointmentCount: Array.isArray(dentist.appointments) ? dentist.appointments.length : 0,
          }))
          .filter((dentist: ClinicPractitioner) => Number.isFinite(dentist.id));

        if (!cancelled) setPractitioners(next.length > 0 ? next : fallback);
      } catch {
        if (!cancelled) setPractitioners(fallback);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    loadPractitioners();
    return () => { cancelled = true; };
  }, [setPractitioners, user]);

  const selected = useMemo(
    () => practitioners.find((practitioner) => practitioner.id === selectedPractitionerId) ?? practitioners[0] ?? null,
    [practitioners, selectedPractitionerId],
  );

  const agendaCopy = location.pathname.startsWith('/agenda')
    ? 'Les nouveaux rendez-vous seront attribués à ce praticien.'
    : 'Contexte clinique partagé entre le tableau de bord, l’agenda et l’équipe.';

  if (!loading && practitioners.length === 0) return null;

  return (
    <section
      aria-label="Contexte praticien"
      className="relative min-w-0 overflow-hidden rounded-[1.75rem] border border-white/70 bg-white/70 p-3.5 shadow-[0_18px_50px_-30px_rgba(15,45,95,0.42)] backdrop-blur-2xl sm:p-4"
    >
      <div className="pointer-events-none absolute -right-10 -top-16 h-40 w-40 rounded-full bg-primary/10 blur-3xl" />
      <div className="relative flex min-w-0 flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary text-white shadow-lg shadow-primary/20">
            <Stethoscope size={20} />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-[9px] font-black uppercase tracking-[0.22em] text-slate-400">Contexte clinique</p>
              {!loading && practitioners.length > 1 && (
                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-100 bg-emerald-50 px-2 py-1 text-[9px] font-black uppercase tracking-wide text-emerald-700">
                  <UsersRound size={11} /> {practitioners.length} praticiens actifs
                </span>
              )}
            </div>
            <p className="mt-0.5 truncate text-sm font-black text-slate-800">
              {loading ? 'Synchronisation des praticiens…' : selected?.name || 'Praticien principal'}
            </p>
            <p className="mt-0.5 max-w-xl text-[10px] font-semibold leading-relaxed text-slate-400 sm:text-[11px]">{agendaCopy}</p>
          </div>
        </div>

        <div className="min-w-0 xl:max-w-[58%]">
          <div className="flex max-w-full items-center gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {loading && (
              <div className="h-11 w-44 shrink-0 animate-pulse rounded-2xl bg-slate-100" />
            )}
            {!loading && practitioners.map((practitioner) => {
              const active = practitioner.id === selected?.id;
              return (
                <button
                  key={practitioner.id}
                  type="button"
                  onClick={() => selectPractitioner(practitioner)}
                  aria-pressed={active}
                  className={cn(
                    'group flex min-w-[150px] shrink-0 items-center gap-2.5 rounded-2xl border px-3 py-2.5 text-left transition-all',
                    active
                      ? 'border-primary/20 bg-primary text-white shadow-lg shadow-primary/15'
                      : 'border-slate-200/80 bg-white/80 text-slate-700 hover:border-primary/20 hover:bg-primary/5',
                  )}
                >
                  <span className={cn(
                    'flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-[10px] font-black',
                    active ? 'bg-white/15 text-white' : 'bg-slate-100 text-primary',
                  )}>
                    {initials(practitioner.name)}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[11px] font-black">{practitioner.name}</span>
                    <span className={cn(
                      'mt-0.5 block truncate text-[9px] font-bold',
                      active ? 'text-white/70' : 'text-slate-400',
                    )}>
                      {typeof practitioner.appointmentCount === 'number'
                        ? `${practitioner.appointmentCount} RDV aujourd’hui`
                        : 'Disponible'}
                    </span>
                  </span>
                  {active && <Check size={14} className="shrink-0 text-emerald-200" />}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};

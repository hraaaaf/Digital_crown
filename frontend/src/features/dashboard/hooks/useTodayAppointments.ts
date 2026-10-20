import { useCallback, useEffect, useRef, useState } from 'react';
import type { AppUser } from '../../../types';
import { api } from '../../../services/api';
import { hasAccess } from '../../../utils/accessControl';
import { getLocalDayBounds } from '../localDate';
import type { DashboardAppointment, DataState } from '../types';
import { normalizeCabinetAppointments } from '../normalizeCabinetAppointments';

export const useTodayAppointments = ({
  user,
  authLoading,
  onStatsRefresh,
  onCompleted,
}: {
  user: AppUser | null;
  authLoading: boolean;
  onStatsRefresh: () => Promise<void>;
  onCompleted: (patient: { nom: string; prenom: string }) => void;
}) => {
  const [appointments, setAppointments] = useState<DashboardAppointment[] | null>([]);
  const [appointmentsState, setAppointmentsState] = useState<DataState>('idle');
  const [loadedIdentity, setLoadedIdentity] = useState<string | null>(null);

  const canUseAgenda = hasAccess(user, 'agenda');
  const canReadPatients = hasAccess(user, 'patients');
  // Keep this key synchronously in render: a permission/tenant switch must
  // redact historical rows BEFORE any new effect or HTTP response completes.
  const identity = !authLoading && user && canUseAgenda
    ? `${user.id}:${user.employer_id ?? 'owner'}:${user.role}:${Number(canReadPatients)}`
    : null;
  const latestIdentity = useRef(identity);
  latestIdentity.current = identity;
  const requestSequence = useRef(0);

  useEffect(() => () => { requestSequence.current += 1; }, []);

  const refreshAppointments = useCallback(async () => {
    if (!user || !canUseAgenda || !identity) {
      requestSequence.current += 1;
      setAppointments([]);
      setLoadedIdentity(null);
      setAppointmentsState('idle');
      return;
    }

    const startedFor = identity;
    const requestId = ++requestSequence.current;
    setAppointmentsState('loading');
    try {
      const { start, end } = getLocalDayBounds();
      const response = await api.get(`/appointments/?start_date=${start}&end_date=${end}`);
      const normalized = normalizeCabinetAppointments(response.data, canReadPatients);
      if (requestId !== requestSequence.current || latestIdentity.current !== startedFor) return;
      setAppointments(normalized);
      setLoadedIdentity(startedFor);
      setAppointmentsState('ready');
    } catch (error) {
      if (requestId !== requestSequence.current || latestIdentity.current !== startedFor) return;
      console.error('Erreur chargement rendez-vous du jour', error);
      setAppointments(null);
      setLoadedIdentity(startedFor);
      setAppointmentsState('error');
    }
  }, [canReadPatients, canUseAgenda, identity, user]);

  useEffect(() => {
    if (authLoading) return;
    if (!user || !canUseAgenda) {
      setAppointments([]);
      setAppointmentsState('idle');
      return;
    }
    void refreshAppointments();
  }, [authLoading, canUseAgenda, refreshAppointments, user]);

  const updateAppointmentStatus = useCallback(async (
    appointmentId: number,
    newStatus: string,
  ) => {
    if (!canUseAgenda) return;

    try {
      await api.put(`/appointments/${appointmentId}`, { status: newStatus });
      void refreshAppointments();

      if (canReadPatients) {
        void onStatsRefresh();
      }

      if (newStatus === 'TERMINÉ') {
        const appointment = appointments?.find(item => item.id === appointmentId);
        if (appointment?.patient) {
          onCompleted(appointment.patient);
        }
      }
    } catch (error) {
      console.error('Erreur changement de statut du rendez-vous', error);
    }
  }, [appointments, canReadPatients, canUseAgenda, onCompleted, onStatsRefresh, refreshAppointments]);

  // Do not return rows fetched under a different role, account, tenant or
  // permission set, even during the render BEFORE the refetch effect runs.
  const visibleState: DataState = identity === null ? (authLoading ? 'loading' : 'idle')
    : loadedIdentity === identity ? appointmentsState : 'loading';
  const visibleAppointments = identity === null && !authLoading ? []
    : loadedIdentity === identity ? appointments : null;

  return {
    appointments: visibleAppointments,
    appointmentsState: visibleState,
    loadingAppointments: visibleState === 'loading',
    refreshAppointments,
    updateAppointmentStatus,
  };
};

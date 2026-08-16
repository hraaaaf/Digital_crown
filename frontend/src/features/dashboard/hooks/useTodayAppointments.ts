import { useCallback, useEffect, useState } from 'react';
import type { AppUser } from '../../../types';
import { api } from '../../../services/api';
import { hasAccess } from '../../../utils/accessControl';
import type { DashboardAppointment, DataState } from '../types';

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
  const [appointments, setAppointments] = useState<DashboardAppointment[]>([]);
  const [appointmentsState, setAppointmentsState] = useState<DataState>('idle');

  const canUseAgenda = hasAccess(user, 'agenda');
  const canReadPatients = hasAccess(user, 'patients');

  const refreshAppointments = useCallback(async () => {
    if (!user || !canUseAgenda) {
      setAppointments([]);
      setAppointmentsState('idle');
      return;
    }

    setAppointmentsState('loading');
    try {
      const todayStr = new Date().toISOString().split('T')[0];
      const start = `${todayStr}T00:00:00`;
      const end = `${todayStr}T23:59:59`;
      const response = await api.get(`/appointments/?start_date=${start}&end_date=${end}`);
      setAppointments(response.data);
      setAppointmentsState('ready');
    } catch (error) {
      console.error('Erreur chargement rendez-vous du jour', error);
      setAppointments([]);
      setAppointmentsState('error');
    }
  }, [canUseAgenda, user]);

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

    await api.put(`/appointments/${appointmentId}`, { status: newStatus });
    await refreshAppointments();

    if (canReadPatients) {
      await onStatsRefresh();
    }

    if (newStatus === 'TERMINÉ') {
      const appointment = appointments.find(item => item.id === appointmentId);
      if (appointment?.patient) {
        onCompleted(appointment.patient);
      }
    }
  }, [appointments, canReadPatients, canUseAgenda, onCompleted, onStatsRefresh, refreshAppointments]);

  return {
    appointments,
    appointmentsState,
    loadingAppointments: appointmentsState === 'loading',
    refreshAppointments,
    updateAppointmentStatus,
  };
};

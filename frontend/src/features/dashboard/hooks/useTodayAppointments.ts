import { useCallback, useEffect, useState } from 'react';
import type { AppUser } from '../../../types';
import { api } from '../../../services/api';
import { hasAccess } from '../../../utils/accessControl';
import { getLocalDayBounds } from '../localDate';
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
  const [appointments, setAppointments] = useState<DashboardAppointment[] | null>([]);
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
      const { start, end } = getLocalDayBounds();
      const response = await api.get(`/appointments/?start_date=${start}&end_date=${end}`);
      setAppointments(response.data);
      setAppointmentsState('ready');
    } catch (error) {
      console.error('Erreur chargement rendez-vous du jour', error);
      setAppointments(null);
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

  return {
    appointments,
    appointmentsState,
    loadingAppointments: appointmentsState === 'loading',
    refreshAppointments,
    updateAppointmentStatus,
  };
};

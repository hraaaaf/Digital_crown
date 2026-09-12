import React, { useEffect } from 'react';
import { AgendaStudio } from '../features/agenda/AgendaStudio';
import { api } from '../services/api';
import { useAuthStore } from '../stores/useAuthStore';
import { usePractitionerContextStore } from '../features/clinic/practitionerContext';

const resolveActivePractitionerId = (): number | null => {
  const selected = usePractitionerContextStore.getState().selectedPractitionerId;
  if (selected) return selected;

  const user = useAuthStore.getState().user;
  if (!user) return null;

  const fallback = user.role === 'SECRETAIRE'
    ? Number(user.employer_id)
    : Number(user.id);

  return Number.isFinite(fallback) ? fallback : null;
};

export const withPractitionerContext = (data: unknown, practitionerId: number) => {
  if (!data) return { praticien_id: practitionerId };

  if (typeof data === 'string') {
    try {
      const parsed = JSON.parse(data);
      return { ...parsed, praticien_id: parsed.praticien_id ?? practitionerId };
    } catch {
      return data;
    }
  }

  if (typeof data === 'object' && !Array.isArray(data)) {
    const objectData = data as Record<string, unknown>;
    return {
      ...objectData,
      praticien_id: objectData.praticien_id ?? practitionerId,
    };
  }

  return data;
};

export const AgendaPage: React.FC = () => {
  useEffect(() => {
    const practitionerByAppointment = new Map<number, number>();

    const rememberAppointment = (appointment: any) => {
      if (!appointment || appointment.praticien_id == null) return;
      const appointmentId = Number(appointment.id);
      const practitionerId = Number(appointment.praticien_id);
      if (Number.isFinite(appointmentId) && Number.isFinite(practitionerId)) {
        practitionerByAppointment.set(appointmentId, practitionerId);
      }
    };

    const responseInterceptor = api.interceptors.response.use((response) => {
      const url = (response.config.url || '').split('?')[0];

      if (url === '/appointments/' && Array.isArray(response.data)) {
        response.data.forEach(rememberAppointment);
      }

      if (url === '/appointments/multi-practitioner' && Array.isArray(response.data?.dentists)) {
        response.data.dentists.forEach((dentist: any) => {
          if (Array.isArray(dentist.appointments)) dentist.appointments.forEach(rememberAppointment);
        });
        if (Array.isArray(response.data?.legacy_unassigned)) {
          response.data.legacy_unassigned.forEach(rememberAppointment);
        }
      }

      return response;
    });

    const requestInterceptor = api.interceptors.request.use((config) => {
      const activePractitionerId = resolveActivePractitionerId();
      const url = (config.url || '').split('?')[0];
      const method = (config.method || 'get').toLowerCase();

      if (method === 'get' && url === '/appointments/check-conflicts') {
        const excludeId = Number(config.params?.exclude_id);
        const editingPractitionerId = Number.isFinite(excludeId)
          ? practitionerByAppointment.get(excludeId)
          : undefined;
        const practitionerId = editingPractitionerId ?? activePractitionerId;

        if (practitionerId) {
          config.params = {
            ...(config.params || {}),
            praticien_id: config.params?.praticien_id ?? practitionerId,
          };
        }
        return config;
      }

      if (!activePractitionerId) return config;

      if (method === 'post' && url === '/appointments/') {
        config.data = withPractitionerContext(config.data, activePractitionerId);
        return config;
      }

      // Une modification conserve le praticien historique si le payload n'en
      // fournit pas explicitement un. Le contexte global ne doit jamais réaffecter
      // silencieusement un rendez-vous simplement parce qu'on l'édite.
      if (method === 'put' && /^\/appointments\/\d+$/.test(url)) {
        return config;
      }

      if (method === 'post' && url === '/appointments/bulk' && config.data && typeof config.data === 'object') {
        const payload = config.data as { appointments?: Array<Record<string, unknown>> };
        if (Array.isArray(payload.appointments)) {
          config.data = {
            ...payload,
            appointments: payload.appointments.map((appointment) => ({
              ...appointment,
              praticien_id: appointment.praticien_id ?? activePractitionerId,
            })),
          };
        }
      }

      return config;
    });

    return () => {
      api.interceptors.request.eject(requestInterceptor);
      api.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  return (
    <div className="h-full w-full min-w-0 overflow-y-auto overflow-x-hidden custom-scrollbar">
      <AgendaStudio />
    </div>
  );
};

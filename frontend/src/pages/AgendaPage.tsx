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

const withPractitioner = (data: unknown, practitionerId: number) => {
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
    const interceptor = api.interceptors.request.use((config) => {
      const practitionerId = resolveActivePractitionerId();
      if (!practitionerId) return config;

      const url = (config.url || '').split('?')[0];
      const method = (config.method || 'get').toLowerCase();

      if (method === 'get' && url === '/appointments/check-conflicts') {
        config.params = {
          ...(config.params || {}),
          praticien_id: config.params?.praticien_id ?? practitionerId,
        };
        return config;
      }

      if (method === 'post' && url === '/appointments/') {
        config.data = withPractitioner(config.data, practitionerId);
        return config;
      }

      if (method === 'put' && /^\/appointments\/\d+$/.test(url)) {
        config.data = withPractitioner(config.data, practitionerId);
        return config;
      }

      if (method === 'post' && url === '/appointments/bulk' && config.data && typeof config.data === 'object') {
        const payload = config.data as { appointments?: Array<Record<string, unknown>> };
        if (Array.isArray(payload.appointments)) {
          config.data = {
            ...payload,
            appointments: payload.appointments.map((appointment) => ({
              ...appointment,
              praticien_id: appointment.praticien_id ?? practitionerId,
            })),
          };
        }
      }

      return config;
    });

    return () => api.interceptors.request.eject(interceptor);
  }, []);

  return (
    <div className="h-full w-full min-w-0 overflow-y-auto overflow-x-hidden custom-scrollbar">
      <AgendaStudio />
    </div>
  );
};

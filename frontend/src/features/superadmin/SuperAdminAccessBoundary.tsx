import React, { useEffect, useState } from 'react';
import { ShieldAlert } from 'lucide-react';
import { api } from '../../services/api';
import { DigitalCrownLoader } from '../../components/DigitalCrownLoader';
import { SuperAdminDashboard } from './SuperAdminDashboard';

type AccessState = 'checking' | 'allowed' | 'denied';

const isForbidden = (error: unknown): boolean => {
  const candidate = error as { response?: { status?: number } };
  return candidate?.response?.status === 403;
};

export const SuperAdminAccessBoundary: React.FC = () => {
  const [accessState, setAccessState] = useState<AccessState>('checking');

  useEffect(() => {
    let cancelled = false;

    const checkAccess = async () => {
      try {
        await Promise.all([
          api.get('/superadmin/clients'),
          api.get('/superadmin/trial-codes'),
        ]);
        if (!cancelled) setAccessState('allowed');
      } catch (error) {
        if (cancelled) return;
        setAccessState(isForbidden(error) ? 'denied' : 'allowed');
      }
    };

    checkAccess();
    return () => {
      cancelled = true;
    };
  }, []);

  if (accessState === 'checking') {
    return <DigitalCrownLoader text="Vérification Sécurité..." textColor="text-[#003380]" spinnerColor="border-[#003380]" />;
  }

  if (accessState === 'denied') {
    return (
      <main className="min-h-[70vh] bg-slate-50 px-4 py-12 sm:px-6 flex items-center justify-center" data-testid="superadmin-access-denied">
        <section className="w-full max-w-lg rounded-[2rem] border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-10">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
            <ShieldAlert size={28} aria-hidden="true" />
          </div>
          <h1 className="mt-6 text-2xl font-black tracking-tight text-slate-900">Accès Superadmin non autorisé</h1>
          <p className="mt-3 text-sm font-medium leading-6 text-slate-500">
            Votre session ne dispose pas d’une autorisation plateforme.
          </p>
        </section>
      </main>
    );
  }

  return <SuperAdminDashboard />;
};

import React, { useEffect, useState } from 'react';
import { ShieldAlert, WifiOff } from 'lucide-react';
import { api } from '../../services/api';
import { DigitalCrownLoader } from '../../components/DigitalCrownLoader';
import { SuperAdminWorkspace } from './SuperAdminWorkspace';

type AccessState = 'checking' | 'allowed' | 'denied' | 'unavailable';

const statusCode = (error: unknown): number | undefined => {
  const candidate = error as { response?: { status?: number } };
  return candidate?.response?.status;
};

export const SuperAdminAccessBoundary: React.FC = () => {
  const [accessState, setAccessState] = useState<AccessState>('checking');

  useEffect(() => {
    let cancelled = false;

    const checkAccess = async () => {
      try {
        // This endpoint is intentionally available to the immutable owner and to
        // explicitly delegated platform operators. Panel permissions remain granular.
        await api.get('/superadmin/passkey/status');
        if (!cancelled) setAccessState('allowed');
      } catch (error) {
        if (cancelled) return;
        const status = statusCode(error);
        setAccessState(status === 401 || status === 403 ? 'denied' : 'unavailable');
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

  if (accessState === 'unavailable') {
    return (
      <main className="min-h-[70vh] bg-slate-50 px-4 py-12 sm:px-6 flex items-center justify-center" data-testid="superadmin-access-unavailable">
        <section className="w-full max-w-lg rounded-[2rem] border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-10">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
            <WifiOff size={28} aria-hidden="true" />
          </div>
          <h1 className="mt-6 text-2xl font-black tracking-tight text-slate-900">Control-plane indisponible</h1>
          <p className="mt-3 text-sm font-medium leading-6 text-slate-500">
            L’autorité plateforme n’a pas pu être vérifiée. Aucun contrôle n’est affiché tant que la vérification serveur échoue.
          </p>
        </section>
      </main>
    );
  }

  return <SuperAdminWorkspace />;
};

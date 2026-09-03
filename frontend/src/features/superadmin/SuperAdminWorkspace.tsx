import React, { useEffect, useState } from 'react';
import { Settings2, Users } from 'lucide-react';
import { api } from '../../services/api';
import { establishPlatformStepUp, fetchPlatformPasskeyStatus } from './platformPasskey';
import { SuperAdminControlCenter } from './SuperAdminControlCenter';
import { SuperAdminDashboard } from './SuperAdminDashboard';

type WorkspaceTab = 'clients' | 'control';

const requiresPlatformStepUp = (method?: string, url?: string): boolean => {
  const normalizedMethod = String(method || 'get').toLowerCase();
  const normalizedUrl = String(url || '');
  return (
    ['post', 'put', 'patch', 'delete'].includes(normalizedMethod) &&
    normalizedUrl.startsWith('/superadmin/') &&
    !normalizedUrl.startsWith('/superadmin/passkey/')
  );
};

export const SuperAdminWorkspace: React.FC = () => {
  const [tab, setTab] = useState<WorkspaceTab>('control');

  useEffect(() => {
    const interceptorId = api.interceptors.request.use(async (config) => {
      if (!requiresPlatformStepUp(config.method, config.url)) return config;

      const status = await fetchPlatformPasskeyStatus();
      if (!status.step_up_valid) {
        await establishPlatformStepUp(status.enrolled);
      }
      return config;
    });

    return () => {
      api.interceptors.request.eject(interceptorId);
    };
  }, []);

  return (
    <div data-testid="superadmin-workspace">
      <div className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur sm:px-6">
        <nav
          aria-label="Navigation Superadmin"
          className="mx-auto flex max-w-7xl gap-2 rounded-2xl bg-slate-100 p-1.5"
        >
          <button
            type="button"
            onClick={() => setTab('clients')}
            aria-current={tab === 'clients' ? 'page' : undefined}
            className={`inline-flex flex-1 items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-black transition ${
              tab === 'clients' ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <Users size={17} aria-hidden="true" />
            Clients & licences
          </button>
          <button
            type="button"
            onClick={() => setTab('control')}
            aria-current={tab === 'control' ? 'page' : undefined}
            className={`inline-flex flex-1 items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-black transition ${
              tab === 'control' ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <Settings2 size={17} aria-hidden="true" />
            Contrôle plateforme
          </button>
        </nav>
      </div>

      {tab === 'clients' ? (
        <SuperAdminDashboard />
      ) : (
        <main className="min-h-screen bg-slate-50 px-4 py-6 sm:px-6 lg:py-8">
          <div className="mx-auto max-w-7xl">
            <div className="mb-6">
              <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-400">Control plane</p>
              <h1 className="mt-1 text-2xl font-black tracking-tight text-slate-950 sm:text-3xl">Contrôle plateforme</h1>
              <p className="mt-2 max-w-2xl text-sm font-medium leading-6 text-slate-500">
                Devices, canal de diffusion, opérateurs et audit. Les mutations restent soumises au step-up WebAuthn serveur.
              </p>
            </div>
            <SuperAdminControlCenter />
          </div>
        </main>
      )}
    </div>
  );
};

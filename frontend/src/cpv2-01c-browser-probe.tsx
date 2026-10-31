// Synthetic browser probe: imports the REAL production theme hook/storage.
// Never a physical-device or paired-backend FUE; all clinic data is disposable.
import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import { MobileStorage } from './services/zka/MobileStorage';
import {
  bootstrapMobileRuntimeTheme,
  useMobileRuntimeTheme,
  mobileThemeCacheKey,
} from './features/mobile/Dashboard/hooks/useMobileRuntimeTheme';

declare global {
  interface Window {
    __cpv2Lab?: {
      pair: (cabinet: string, token: string) => Promise<void>;
      switchSilently: (cabinet: string, token: string) => Promise<void>;
      refresh: () => void;
      neutralize: () => void;
      saveSnapshot: (marker: string) => Promise<void>;
      readSnapshot: () => Promise<unknown>;
      cacheKey: (cabinet: string) => string;
    };
  }
}

const origin = 'http://127.0.0.1:8005';
const day = '2026-10-31';
const device_id = 'disposable-browser-pwa-1';
const makeCredentials = (cabinet: string, token: string) => ({
  publicId: cabinet,
  masterKey: 'a'.repeat(64),
  access_token: token,
  refresh_token: 'disposable-refresh-' + cabinet,
  device_id,
  api_base_url: origin,
});

function Probe() {
  const [generation, setGeneration] = useState(0);
  useMobileRuntimeTheme(String(generation));
  useEffect(() => {
    window.__cpv2Lab = {
      pair: async (cabinet, token) => {
        await MobileStorage.saveCredentials(makeCredentials(cabinet, token));
        setGeneration(n => n + 1);
      },
      switchSilently: async (cabinet, token) => {
        await MobileStorage.saveCredentials(makeCredentials(cabinet, token));
      },
      refresh: () => setGeneration(n => n + 1),
      neutralize: () => bootstrapMobileRuntimeTheme(),
      saveSnapshot: async marker => MobileStorage.saveLastSnapshot({ marker }, day),
      readSnapshot: async () => (await MobileStorage.getLastSnapshot(day))?.data ?? null,
      cacheKey: cabinet => mobileThemeCacheKey(makeCredentials(cabinet, 'discarded')),
    };
    return () => { delete window.__cpv2Lab; };
  }, []);
  return (
    <main data-cpv2-browser-probe style={{
      margin: '2rem auto', padding: '1rem', maxWidth: '640px',
      fontFamily: 'var(--app-font-family, Inter, system-ui, sans-serif)',
      border: '1px solid var(--primary)',
      borderRadius: '20px',
    }}>
      <h1 style={{ fontSize: '1.25rem', fontWeight: 700 }}>CPV2-01C — Isolation navigateur</h1>
      <p>Probe synthétique React + MobileStorage + useMobileRuntimeTheme</p>
      <p data-test-theme-swatch style={{
        backgroundColor: 'var(--primary, #edf2f7)',
        color: 'var(--text-on-primary, #020617)',
        borderRadius: '12px', padding: '1.5rem',
      }}>Thème actif — preuve de tokens CSS calculés</p>
      <span data-test-no-phi>Aucun dossier patient réel</span>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<Probe />);

import { useCallback, useEffect, useRef, useState } from 'react';
import { mobileApiFetch } from '../../../../services/zka/mobileApi';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { CryptoService } from '../../../../services/zka/CryptoService';
import { DENY_POCKET_READ, parsePocketReadAccess, type PocketReadAccess } from '../pocketReadCapabilities';

export function usePocketReadCapabilities(refreshKey?: string) {
  const [access, setAccess] = useState<PocketReadAccess>(DENY_POCKET_READ);
  const [status, setStatus] = useState<'loading' | 'ready' | 'unavailable'>('loading');
  const generation = useRef(0);
  const activeRequest = useRef<AbortController | null>(null);
  const alive = useRef(false);

  const refresh = useCallback(async () => {
    const requestId = ++generation.current;
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;
    setAccess(DENY_POCKET_READ);
    setStatus('loading');
    const timeout = window.setTimeout(() => controller.abort(), 5000);
    try {
      const credentials = await MobileStorage.getCredentials();
      if (!credentials) throw new Error('Non appairé');
      const response = await mobileApiFetch('/capabilities', {
        cache: 'no-store',
        signal: controller.signal,
      });
      if (!response.ok) throw new Error('Droits indisponibles.');
      const raw: unknown = await response.json();
      const encrypted = raw && typeof raw === 'object' && 'payload' in raw
        ? (raw as { payload: unknown }).payload : undefined;
      if (typeof encrypted !== 'string') throw new Error('Réponse de droits non chiffrée.');
      const payload = await CryptoService.decryptPayload(encrypted, credentials.masterKey);
      const next = parsePocketReadAccess(payload);
      if (controller.signal.aborted) throw new Error('Vérification des droits interrompue.');
      if (alive.current && requestId === generation.current) {
        setAccess(next);
        setStatus('ready');
      }
    } catch {
      if (alive.current && requestId === generation.current) {
        setAccess(DENY_POCKET_READ);
        setStatus('unavailable');
      }
    } finally {
      window.clearTimeout(timeout);
    }
  }, []);

  useEffect(() => {
    alive.current = true;
    void refresh();
    const onVisible = () => { if (document.visibilityState === 'visible') void refresh(); };
    window.addEventListener('focus', refresh);
    window.addEventListener('online', refresh);
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      alive.current = false;
      generation.current += 1;
      activeRequest.current?.abort();
      window.removeEventListener('focus', refresh);
      window.removeEventListener('online', refresh);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [refresh, refreshKey]);

  return { access, status, refresh };
}

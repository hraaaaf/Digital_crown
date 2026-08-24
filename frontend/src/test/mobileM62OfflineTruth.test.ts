import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const read = (p: string) => fs.readFileSync(path.join(root, p), 'utf8');

describe('Mobile M6.2 offline truth', () => {
  it('uses one Workbox service worker and never caches mobile APIs', () => {
    const main = read('src/main.tsx');
    const vite = read('vite.config.ts');
    expect(main).not.toContain("serviceWorker.register('/sw.js')");
    expect(vite).toContain('runtimeCaching: []');
    expect(vite).not.toContain('api-snapshot-cache');
    expect(fs.existsSync(path.join(root, 'public/sw.js'))).toBe(false);
  });

  it('scopes the single app queue to cabinet and device', () => {
    const storage = read('src/services/zka/MobileStorage.ts');
    expect(storage).toContain("zka_action_queue_v2");
    expect(storage).toContain('cabinetPublicId');
    expect(storage).toContain('deviceId');
    expect(storage).toContain('LEGACY_ACTION_QUEUE_ID');
  });

  it('requires HTTP success before removing queued actions or showing mutation success', () => {
    const hook = read('src/features/mobile/Dashboard/hooks/useMobileDashboard.ts');
    expect(hook).toContain("'X-Mobile-Action-Id': action.id");
    expect(hook).toContain('if (!res.ok)');
    expect(hook).toContain('await MobileStorage.removeActionFromQueue(action.id)');
    expect(hook).toContain('isQueueableNetworkError');
    expect(hook).toContain("name === 'AbortError' || name === 'TimeoutError'");
    expect(hook).not.toContain("toast('Déplacement mis en attente (hors ligne)'");
  });

  it('does not mark a lab job SENT from a finally block', () => {
    const hook = read('src/features/mobile/Dashboard/hooks/useMobileDashboard.ts');
    const start = hook.indexOf('const handleWhatsAppSend');
    const end = hook.indexOf('const fetchSignatureDocs', start);
    const block = hook.slice(start, end);
    expect(block).toContain('await patchLabJobStatus');
    expect(block).not.toContain('finally');
  });

  it('routes mobile 401 refresh through the paired-device endpoint', () => {
    const api = read('src/services/api.ts');
    const mobileFetch = read('src/services/zka/mobileFetch.ts');
    expect(api).toContain('MobileStorage.refreshCredentials()');
    expect(api).toContain("!window.location.pathname.startsWith('/mobile')");
    expect(mobileFetch).toContain('first.status !== 401');
    expect(mobileFetch).toContain('MobileStorage.refreshCredentials()');
  });
});

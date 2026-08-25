import { MobileStorage } from './MobileStorage';
import { mobileFetch } from './mobileFetch';

export type MobilePushKind =
  | 'secure-required'
  | 'install-required'
  | 'unsupported'
  | 'prompt'
  | 'denied'
  | 'enabled'
  | 'disabled';

export interface MobilePushState {
  kind: MobilePushKind;
  title: string;
  detail: string;
}

export interface PushCapabilityInput {
  secure: boolean;
  ios: boolean;
  standalone: boolean;
  notificationApi: boolean;
  serviceWorker: boolean;
  pushManager: boolean;
  permission: NotificationPermission | 'unsupported';
}

export function evaluatePushCapability(input: PushCapabilityInput): MobilePushState {
  if (!input.secure) {
    return {
      kind: 'secure-required',
      title: 'HTTPS requis',
      detail: 'Les notifications OS exigent une connexion chiffrée au cabinet.',
    };
  }
  if (input.ios && !input.standalone) {
    return {
      kind: 'install-required',
      title: 'Installer l’app sur l’écran d’accueil',
      detail: 'Sur iPhone/iPad, Web Push fonctionne depuis l’app ajoutée à l’écran d’accueil.',
    };
  }
  if (!input.notificationApi || !input.serviceWorker || !input.pushManager) {
    return {
      kind: 'unsupported',
      title: 'Push OS non disponible',
      detail: 'Ce navigateur ne fournit pas les API Web Push nécessaires.',
    };
  }
  if (input.permission === 'denied') {
    return {
      kind: 'denied',
      title: 'Notifications bloquées',
      detail: 'Réactivez les notifications de Digital Crown dans les réglages du téléphone.',
    };
  }
  if (input.permission === 'granted') {
    return {
      kind: 'disabled',
      title: 'Push OS prêt',
      detail: 'La permission est accordée. Activez la liaison à cet appareil appairé.',
    };
  }
  return {
    kind: 'prompt',
    title: 'Alertes hors écran',
    detail: 'Recevez un signal générique, sans donnée patient sur l’écran verrouillé.',
  };
}

function isIOSDevice(): boolean {
  if (typeof navigator === 'undefined') return false;
  return /iPad|iPhone|iPod/i.test(navigator.userAgent)
    || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
}

function isStandalonePWA(): boolean {
  if (typeof window === 'undefined') return false;
  const navigatorWithStandalone = navigator as Navigator & { standalone?: boolean };
  return navigatorWithStandalone.standalone === true
    || window.matchMedia?.('(display-mode: standalone)').matches === true;
}

function resolveApiBaseUrl(stored: string): string {
  const normalized = stored.endsWith('/') ? stored.slice(0, -1) : stored;
  if (typeof window === 'undefined') return normalized;
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return normalized;
  if (normalized.includes('localhost') || normalized.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return normalized;
}

export function urlBase64ToUint8Array(value: string): Uint8Array {
  const padding = '='.repeat((4 - (value.length % 4)) % 4);
  const normalized = (value + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(normalized);
  return Uint8Array.from(raw, char => char.charCodeAt(0));
}

function sameApplicationServerKey(current: ArrayBuffer | null, expected: Uint8Array): boolean {
  if (!current) return false;
  const actual = new Uint8Array(current);
  return actual.length === expected.length && actual.every((value, index) => value === expected[index]);
}

function capabilitySnapshot(): PushCapabilityInput {
  const notificationApi = typeof Notification !== 'undefined';
  return {
    secure: typeof window !== 'undefined' && window.isSecureContext === true,
    ios: isIOSDevice(),
    standalone: isStandalonePWA(),
    notificationApi,
    serviceWorker: typeof navigator !== 'undefined' && 'serviceWorker' in navigator,
    pushManager: typeof window !== 'undefined' && 'PushManager' in window,
    permission: notificationApi ? Notification.permission : 'unsupported',
  };
}

export async function getMobilePushState(): Promise<MobilePushState> {
  const base = evaluatePushCapability(capabilitySnapshot());
  if (base.kind !== 'disabled') return base;

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    const subscription = await registration?.pushManager.getSubscription();
    if (!subscription) return base;

    const creds = await MobileStorage.getCredentials();
    if (!creds) return base;
    const response = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/push/subscription`, {
      signal: AbortSignal.timeout(4000),
    });
    if (!response.ok) return base;
    const payload = await response.json();
    if (payload.active !== true) return base;
    return {
      kind: 'enabled',
      title: 'Push OS activé',
      detail: 'Cet appareil appairé peut recevoir un signal générique lorsque Digital Crown est fermé.',
    };
  } catch {
    return base;
  }
}

function detectPlatform(): 'ios' | 'android' | 'web' {
  if (isIOSDevice()) return 'ios';
  if (typeof navigator !== 'undefined' && /Android/i.test(navigator.userAgent)) return 'android';
  return 'web';
}

export async function enableMobilePush(): Promise<MobilePushState> {
  const initial = evaluatePushCapability(capabilitySnapshot());
  if (['secure-required', 'install-required', 'unsupported', 'denied'].includes(initial.kind)) return initial;

  // Keep the permission prompt directly attached to the user's click. Safari/iOS
  // rejects permission requests that are detached from explicit user interaction.
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    return permission === 'denied'
      ? evaluatePushCapability({ ...capabilitySnapshot(), permission: 'denied' })
      : evaluatePushCapability({ ...capabilitySnapshot(), permission: 'default' });
  }

  const creds = await MobileStorage.getCredentials();
  if (!creds) throw new Error('Session mobile expirée ou révoquée.');
  const apiBase = resolveApiBaseUrl(creds.api_base_url);

  const configResponse = await mobileFetch(`${apiBase}/api/mobile/push/config`, {
    signal: AbortSignal.timeout(5000),
  });
  if (!configResponse.ok) throw new Error('Configuration Web Push indisponible.');
  const config = await configResponse.json();
  if (typeof config.public_key !== 'string' || !config.public_key) {
    throw new Error('Clé publique Web Push invalide.');
  }

  const registration = await navigator.serviceWorker.ready;
  const expectedKey = urlBase64ToUint8Array(config.public_key);
  let subscription = await registration.pushManager.getSubscription();
  if (subscription && !sameApplicationServerKey(subscription.options.applicationServerKey, expectedKey)) {
    await subscription.unsubscribe();
    subscription = null;
  }
  if (!subscription) {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: expectedKey,
    });
  }

  const serialized = subscription.toJSON();
  if (!serialized.endpoint || !serialized.keys?.p256dh || !serialized.keys?.auth) {
    await subscription.unsubscribe().catch(() => undefined);
    throw new Error('Souscription Web Push incomplète.');
  }

  const registerResponse = await mobileFetch(`${apiBase}/api/mobile/push/subscription`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      endpoint: serialized.endpoint,
      keys: { p256dh: serialized.keys.p256dh, auth: serialized.keys.auth },
      platform: detectPlatform(),
    }),
  });
  if (!registerResponse.ok) {
    const payload = await registerResponse.json().catch(() => ({}));
    await subscription.unsubscribe().catch(() => undefined);
    throw new Error(payload.detail || `Activation Push refusée (${registerResponse.status}).`);
  }

  return {
    kind: 'enabled',
    title: 'Push OS activé',
    detail: 'Cet appareil appairé peut recevoir un signal générique lorsque Digital Crown est fermé.',
  };
}

export async function disableMobilePush(): Promise<MobilePushState> {
  const registration = await navigator.serviceWorker.getRegistration();
  const subscription = await registration?.pushManager.getSubscription();
  if (!subscription) return evaluatePushCapability({ ...capabilitySnapshot(), permission: Notification.permission });

  const creds = await MobileStorage.getCredentials();
  let serverError: Error | null = null;
  if (creds) {
    try {
      const response = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/push/subscription`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint: subscription.endpoint }),
      });
      if (!response.ok) serverError = new Error(`Nettoyage serveur refusé (${response.status}).`);
    } catch (error) {
      serverError = error instanceof Error ? error : new Error('Nettoyage serveur impossible.');
    }
  }

  // Local unsubscribe is the privacy boundary: the stale server endpoint becomes
  // unusable and will also be purged on the next 404/410 Web Push response.
  await subscription.unsubscribe();
  if (serverError) throw serverError;
  return {
    kind: 'disabled',
    title: 'Push OS prêt',
    detail: 'La permission reste accordée, mais cet appareil n’est plus lié aux alertes OS.',
  };
}

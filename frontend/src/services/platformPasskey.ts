type CeremonyOptions = {
  challenge_id: string;
  [key: string]: unknown;
};

type PlatformPasskeyStatus = {
  enrolled: boolean;
  credential_id: string | null;
  rp_id: string;
  expected_origin: string;
  origin_ready: boolean;
  user_verification: 'required';
  step_up_valid: boolean;
};

type StepUpResult = {
  expires_in: number;
};

let enrollmentKnown = false;
let stepUpValidUntil = 0;
const CLIENT_EXPIRY_SAFETY_MS = 30_000;

function arrayBufferToBase64Url(value: ArrayBuffer): string {
  const bytes = new Uint8Array(value);
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function base64UrlToArrayBuffer(value: string): ArrayBuffer {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
  const raw = atob(padded);
  const bytes = new Uint8Array(new ArrayBuffer(raw.length));
  for (let index = 0; index < raw.length; index += 1) bytes[index] = raw.charCodeAt(index);
  return bytes.buffer;
}

function serializeCredential(credential: PublicKeyCredential): Record<string, unknown> {
  const response = credential.response;
  const common = {
    id: credential.id,
    rawId: arrayBufferToBase64Url(credential.rawId),
    type: credential.type,
    authenticatorAttachment: credential.authenticatorAttachment,
    clientExtensionResults: credential.getClientExtensionResults(),
  };

  if (response instanceof AuthenticatorAttestationResponse) {
    return {
      ...common,
      response: {
        attestationObject: arrayBufferToBase64Url(response.attestationObject),
        clientDataJSON: arrayBufferToBase64Url(response.clientDataJSON),
        transports: typeof response.getTransports === 'function' ? response.getTransports() : [],
      },
    };
  }

  const assertion = response as AuthenticatorAssertionResponse;
  return {
    ...common,
    response: {
      authenticatorData: arrayBufferToBase64Url(assertion.authenticatorData),
      clientDataJSON: arrayBufferToBase64Url(assertion.clientDataJSON),
      signature: arrayBufferToBase64Url(assertion.signature),
      userHandle: assertion.userHandle ? arrayBufferToBase64Url(assertion.userHandle) : null,
    },
  };
}

function decodeCreationOptions(payload: CeremonyOptions): PublicKeyCredentialCreationOptions {
  const copy: any = { ...payload };
  delete copy.challenge_id;
  copy.challenge = base64UrlToArrayBuffer(String(copy.challenge));
  copy.user = { ...copy.user, id: base64UrlToArrayBuffer(String(copy.user.id)) };
  copy.excludeCredentials = (copy.excludeCredentials || []).map((item: any) => ({
    ...item,
    id: base64UrlToArrayBuffer(String(item.id)),
  }));
  return copy as PublicKeyCredentialCreationOptions;
}

function decodeAuthenticationOptions(payload: CeremonyOptions): PublicKeyCredentialRequestOptions {
  const copy: any = { ...payload };
  delete copy.challenge_id;
  copy.challenge = base64UrlToArrayBuffer(String(copy.challenge));
  copy.allowCredentials = (copy.allowCredentials || []).map((item: any) => ({
    ...item,
    id: base64UrlToArrayBuffer(String(item.id)),
  }));
  return copy as PublicKeyCredentialRequestOptions;
}

async function platformFetch<T>(apiBase: string, path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers || {});
  const webToken = localStorage.getItem('token') || sessionStorage.getItem('token');
  if (webToken) headers.set('Authorization', `Bearer ${webToken}`);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');

  const response = await fetch(`${apiBase}/api/superadmin/passkey${path}`, {
    ...init,
    headers,
    credentials: 'include',
  });
  const payload = await response.json().catch(() => ({}));
  if (response.ok) return payload as T;

  const detail = payload?.detail;
  const message = typeof detail === 'string'
    ? detail
    : detail?.message || detail?.code || `Erreur ${response.status}`;
  throw new Error(message);
}

function assertWebAuthnReady(expectedOrigin?: string): void {
  if (typeof window === 'undefined' || !window.isSecureContext || !('PublicKeyCredential' in window) || !navigator.credentials) {
    throw new Error('WebAuthn nécessite un navigateur sécurisé compatible.');
  }
  if (expectedOrigin && window.location.origin.toLowerCase() !== expectedOrigin.toLowerCase()) {
    throw new Error(`Ouvrez Digital Crown depuis ${expectedOrigin} pour confirmer une action SuperAdmin.`);
  }
}

function rememberStepUp(expiresIn: number): void {
  stepUpValidUntil = Date.now() + Math.max(0, expiresIn * 1000 - CLIENT_EXPIRY_SAFETY_MS);
}

async function registerPlatformPasskey(apiBase: string): Promise<void> {
  const options = await platformFetch<CeremonyOptions>(apiBase, '/registration/options', { method: 'POST' });
  const credential = await navigator.credentials.create({ publicKey: decodeCreationOptions(options) });
  if (!(credential instanceof PublicKeyCredential)) throw new Error('Enrôlement passkey annulé.');

  const result = await platformFetch<StepUpResult>(apiBase, '/registration/verify', {
    method: 'POST',
    body: JSON.stringify({ challenge_id: options.challenge_id, credential: serializeCredential(credential) }),
  });
  enrollmentKnown = true;
  rememberStepUp(result.expires_in);
}

async function authenticatePlatformPasskey(apiBase: string): Promise<void> {
  const options = await platformFetch<CeremonyOptions>(apiBase, '/authentication/options', { method: 'POST' });
  const credential = await navigator.credentials.get({ publicKey: decodeAuthenticationOptions(options) });
  if (!(credential instanceof PublicKeyCredential)) throw new Error('Vérification passkey annulée.');

  const result = await platformFetch<StepUpResult>(apiBase, '/authentication/verify', {
    method: 'POST',
    body: JSON.stringify({ challenge_id: options.challenge_id, credential: serializeCredential(credential) }),
  });
  rememberStepUp(result.expires_in);
}

async function fetchPlatformStatus(apiBase: string): Promise<PlatformPasskeyStatus> {
  const status = await platformFetch<PlatformPasskeyStatus>(apiBase, '/status');
  assertWebAuthnReady(status.expected_origin);
  enrollmentKnown = status.enrolled;
  return status;
}

/**
 * Complete a WebAuthn user-verification ceremony when the current proof window
 * is absent or close to expiry. The proof itself stays in an HttpOnly cookie;
 * frontend memory stores only the expiry timestamp. Cached client time is never
 * sufficient by itself: the backend confirms that the scoped cookie still exists
 * and verifies before any privileged mutation reuses it.
 */
export async function ensurePlatformStepUp(apiBase: string): Promise<void> {
  assertWebAuthnReady();

  if (Date.now() < stepUpValidUntil) {
    const status = await fetchPlatformStatus(apiBase);
    if (status.step_up_valid) return;
    stepUpValidUntil = 0;
  }

  if (!enrollmentKnown) {
    await fetchPlatformStatus(apiBase);
  }

  if (enrollmentKnown) {
    await authenticatePlatformPasskey(apiBase);
  } else {
    await registerPlatformPasskey(apiBase);
  }
}

export function resetPlatformPasskeyClientState(): void {
  enrollmentKnown = false;
  stepUpValidUntil = 0;
}

import { MobileStorage } from './MobileStorage';

export type MobilePasskeyState = 'disabled' | 'pending' | 'enabled';

export interface MobilePasskeyStatus {
  state: MobilePasskeyState;
  credential_id: string | null;
  rp_id: string;
  expected_origin: string;
  origin_ready: boolean;
  user_verification: 'required';
  server_gate: boolean;
}

interface CeremonyOptions {
  challenge_id: string;
  [key: string]: unknown;
}

interface AuthenticationResult {
  accessToken: string;
  expiresIn: number;
  credentialId: string;
  credentialState: MobilePasskeyState;
  prfOutput: ArrayBuffer | null;
}

function arrayBufferToBase64Url(value: ArrayBuffer): string {
  const bytes = new Uint8Array(value);
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

export function base64UrlToArrayBuffer(value: string): ArrayBuffer {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
  const raw = atob(padded);
  const bytes = new Uint8Array(new ArrayBuffer(raw.length));
  for (let index = 0; index < raw.length; index += 1) bytes[index] = raw.charCodeAt(index);
  return bytes.buffer;
}

function randomBase64Url(bytes = 32): string {
  return arrayBufferToBase64Url(crypto.getRandomValues(new Uint8Array(bytes)).buffer);
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
  // Ask for PRF support during creation so incompatible platform authenticators fail closed.
  copy.extensions = { ...(copy.extensions || {}), prf: {} };
  return copy as PublicKeyCredentialCreationOptions;
}

function decodeAuthenticationOptions(payload: CeremonyOptions, prfSalt?: string): PublicKeyCredentialRequestOptions {
  const copy: any = { ...payload };
  delete copy.challenge_id;
  delete copy.credential_state;
  copy.challenge = base64UrlToArrayBuffer(String(copy.challenge));
  copy.allowCredentials = (copy.allowCredentials || []).map((item: any) => ({
    ...item,
    id: base64UrlToArrayBuffer(String(item.id)),
  }));
  if (prfSalt) {
    copy.extensions = {
      ...(copy.extensions || {}),
      prf: { eval: { first: base64UrlToArrayBuffer(prfSalt) } },
    };
  }
  return copy as PublicKeyCredentialRequestOptions;
}

async function durableFetch(path: string, init: RequestInit = {}, tokenOverride?: string): Promise<Response> {
  const creds = await MobileStorage.getCredentials();
  if (!creds?.access_token) throw new Error('Session mobile expirée ou révoquée.');
  const headers = new Headers(init.headers || {});
  headers.set('Authorization', `Bearer ${tokenOverride || creds.access_token}`);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  return fetch(`${creds.api_base_url}/api/mobile${path}`, { ...init, headers });
}

async function jsonOrError(response: Response): Promise<any> {
  const payload = await response.json().catch(() => ({}));
  if (response.ok) return payload;
  const detail = payload?.detail;
  const message = typeof detail === 'string'
    ? detail
    : detail?.message || detail?.code || `Erreur ${response.status}`;
  const error = new Error(message);
  (error as Error & { status?: number; code?: string }).status = response.status;
  (error as Error & { status?: number; code?: string }).code = detail?.code;
  throw error;
}

export function isStablePasskeyOrigin(expectedOrigin = 'https://digitalcrown.local:8005'): boolean {
  return typeof window !== 'undefined'
    && window.isSecureContext === true
    && window.location.origin.toLowerCase() === expectedOrigin.toLowerCase();
}

export function isWebAuthnAvailable(): boolean {
  return typeof window !== 'undefined'
    && 'PublicKeyCredential' in window
    && typeof navigator !== 'undefined'
    && !!navigator.credentials;
}

export async function hasPlatformUserVerification(): Promise<boolean> {
  if (!isWebAuthnAvailable()) return false;
  try {
    return await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
  } catch {
    return false;
  }
}

export async function getMobilePasskeyStatus(): Promise<MobilePasskeyStatus> {
  return jsonOrError(await durableFetch('/passkey/status'));
}

async function createPendingCredential(): Promise<string> {
  const optionsPayload = await jsonOrError(await durableFetch('/passkey/registration/options', { method: 'POST' })) as CeremonyOptions;
  const credential = await navigator.credentials.create({ publicKey: decodeCreationOptions(optionsPayload) });
  if (!(credential instanceof PublicKeyCredential)) throw new Error('Enrôlement passkey annulé.');
  const extensionResults = credential.getClientExtensionResults() as AuthenticationExtensionsClientOutputs & {
    prf?: { enabled?: boolean };
  };
  if (extensionResults.prf?.enabled !== true) {
    throw new Error('Ce navigateur ne fournit pas le coffre PRF requis par Digital Crown.');
  }
  const verified = await jsonOrError(await durableFetch('/passkey/registration/verify', {
    method: 'POST',
    body: JSON.stringify({ challenge_id: optionsPayload.challenge_id, credential: serializeCredential(credential) }),
  }));
  return String(verified.credential_id);
}

async function authenticateCredential(prfSalt?: string): Promise<AuthenticationResult> {
  const optionsPayload = await jsonOrError(await durableFetch('/passkey/authentication/options', { method: 'POST' })) as CeremonyOptions;
  const credential = await navigator.credentials.get({
    publicKey: decodeAuthenticationOptions(optionsPayload, prfSalt),
  });
  if (!(credential instanceof PublicKeyCredential)) throw new Error('Vérification biométrique annulée.');
  let prfOutput: ArrayBuffer | null = null;
  if (prfSalt) {
    const extensionResults = credential.getClientExtensionResults() as AuthenticationExtensionsClientOutputs & {
      prf?: { results?: { first?: ArrayBuffer } };
    };
    prfOutput = extensionResults.prf?.results?.first ?? null;
    if (!prfOutput || prfOutput.byteLength !== 32) {
      throw new Error('Le coffre PRF biométrique est indisponible sur cet appareil.');
    }
  }
  const verified = await jsonOrError(await durableFetch('/passkey/authentication/verify', {
    method: 'POST',
    body: JSON.stringify({ challenge_id: optionsPayload.challenge_id, credential: serializeCredential(credential) }),
  }));
  return {
    accessToken: String(verified.access_token),
    expiresIn: Number(verified.expires_in),
    credentialId: String(verified.credential_id),
    credentialState: verified.credential_state as MobilePasskeyState,
    prfOutput,
  };
}


async function authenticateLocalVault(credentialId: string, prfSalt: string): Promise<ArrayBuffer> {
  const publicKey: any = {
    challenge: crypto.getRandomValues(new Uint8Array(32)),
    rpId: 'digitalcrown.local',
    allowCredentials: [{ type: 'public-key', id: base64UrlToArrayBuffer(credentialId) }],
    userVerification: 'required',
    timeout: 60000,
    extensions: { prf: { eval: { first: base64UrlToArrayBuffer(prfSalt) } } },
  };
  const credential = await navigator.credentials.get({ publicKey });
  if (!(credential instanceof PublicKeyCredential)) throw new Error('Vérification biométrique annulée.');
  const extensionResults = credential.getClientExtensionResults() as AuthenticationExtensionsClientOutputs & {
    prf?: { results?: { first?: ArrayBuffer } };
  };
  const output = extensionResults.prf?.results?.first;
  if (!output || output.byteLength !== 32) throw new Error('Le coffre PRF biométrique est indisponible.');
  return output;
}

export async function activateMobilePasskey(): Promise<MobilePasskeyStatus> {
  const status = await getMobilePasskeyStatus();
  if (!isStablePasskeyOrigin(status.expected_origin)) {
    throw new Error(`Ouvrez Digital Crown depuis ${status.expected_origin} pour activer la biométrie.`);
  }
  if (!isWebAuthnAvailable() || !(await hasPlatformUserVerification())) {
    throw new Error('Aucun authentificateur biométrique de plateforme compatible n’est disponible.');
  }
  if (status.state === 'enabled') throw new Error('Le verrou biométrique est déjà activé.');

  let credentialId = status.credential_id;
  if (status.state === 'disabled') credentialId = await createPendingCredential();
  if (!credentialId) throw new Error('Passkey pending introuvable.');

  const prfSalt = randomBase64Url(32);
  const authentication = await authenticateCredential(prfSalt);
  if (!authentication.prfOutput || authentication.credentialId !== credentialId) {
    throw new Error('Passkey incompatible avec le coffre local.');
  }

  await MobileStorage.sealBiometricVault({
    credentialId,
    prfSalt,
    prfOutput: authentication.prfOutput,
  });
  const enabled = await jsonOrError(await durableFetch('/passkey/enable', {
    method: 'POST',
    body: JSON.stringify({ credential_id: credentialId }),
  }, authentication.accessToken));
  MobileStorage.setBiometricAccessToken(authentication.accessToken);
  return { ...status, state: enabled.state, credential_id: credentialId, server_gate: true, origin_ready: true };
}

export async function unlockMobilePasskey(): Promise<MobilePasskeyStatus> {
  const vault = await MobileStorage.getBiometricVaultEnvelope();
  if (!vault) throw new Error('Coffre biométrique local introuvable.');
  const expectedOrigin = 'https://digitalcrown.local:8005';
  if (!isStablePasskeyOrigin(expectedOrigin)) {
    throw new Error(`Ouvrez Digital Crown depuis ${expectedOrigin} pour déverrouiller.`);
  }

  try {
    const status = await getMobilePasskeyStatus();
    // Recovery path: the server may already have deleted the credential while a
    // previous local restore was interrupted. The authenticator still owns the
    // passkey, so one local UV can decrypt and retire the orphaned vault safely.
    if (status.state === 'disabled') {
      const prfOutput = await authenticateLocalVault(vault.credential_id, vault.prf_salt);
      await MobileStorage.unlockBiometricVault(prfOutput);
      await MobileStorage.disableBiometricVault();
      MobileStorage.clearBiometricAccessToken();
      return status;
    }
    const authentication = await authenticateCredential(vault.prf_salt);
    if (!authentication.prfOutput || authentication.credentialId !== vault.credential_id) {
      throw new Error('Passkey incompatible avec ce coffre local.');
    }
    await MobileStorage.unlockBiometricVault(authentication.prfOutput);
    MobileStorage.setBiometricAccessToken(authentication.accessToken);

    if (status.state === 'pending') {
      await jsonOrError(await durableFetch('/passkey/enable', {
        method: 'POST',
        body: JSON.stringify({ credential_id: vault.credential_id }),
      }, authentication.accessToken));
      return { ...status, state: 'enabled', server_gate: true };
    }
    return status;
  } catch (error) {
    // Offline fallback: only decrypt the local vault. No server UV token is minted,
    // therefore no protected API route is unlocked and no mutation can escape locally.
    if ((typeof navigator !== 'undefined' && navigator.onLine === false) || error instanceof TypeError) {
      const prfOutput = await authenticateLocalVault(vault.credential_id, vault.prf_salt);
      await MobileStorage.unlockBiometricVault(prfOutput);
      MobileStorage.clearBiometricAccessToken();
      return {
        state: 'enabled', credential_id: vault.credential_id, rp_id: 'digitalcrown.local',
        expected_origin: expectedOrigin, origin_ready: true, user_verification: 'required', server_gate: true,
      };
    }
    throw error;
  }
}

export async function resetPendingMobilePasskey(): Promise<void> {
  await jsonOrError(await durableFetch('/passkey/pending', { method: 'DELETE' }));
}

export async function disableMobilePasskey(): Promise<void> {
  const vault = await MobileStorage.getBiometricVaultEnvelope();
  if (!vault) throw new Error('Coffre biométrique local introuvable.');
  if (!(await MobileStorage.isBiometricVaultUnlocked())) {
    await unlockMobilePasskey();
  }
  let token = MobileStorage.getBiometricAccessToken();
  if (!token) {
    const authentication = await authenticateCredential(vault.prf_salt);
    if (!authentication.prfOutput) throw new Error('Vérification biométrique requise.');
    await MobileStorage.unlockBiometricVault(authentication.prfOutput);
    MobileStorage.setBiometricAccessToken(authentication.accessToken);
    token = authentication.accessToken;
  }
  await jsonOrError(await durableFetch('/passkey', { method: 'DELETE' }, token));
  await MobileStorage.disableBiometricVault();
}

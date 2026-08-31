import { api } from '../../services/api';

const decodeBase64Url = (value: string): ArrayBuffer => {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4);
  const binary = window.atob(padded);
  const buffer = new ArrayBuffer(binary.length);
  const bytes = new Uint8Array(buffer);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return buffer;
};

const encodeBase64Url = (value: ArrayBuffer): string => {
  const bytes = new Uint8Array(value);
  let binary = '';
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return window.btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
};

const registrationOptions = (raw: Record<string, any>): PublicKeyCredentialCreationOptions => ({
  ...raw,
  challenge: decodeBase64Url(raw.challenge),
  user: {
    ...raw.user,
    id: decodeBase64Url(raw.user.id),
  },
  excludeCredentials: (raw.excludeCredentials || []).map((credential: any) => ({
    ...credential,
    id: decodeBase64Url(credential.id),
  })),
});

const authenticationOptions = (raw: Record<string, any>): PublicKeyCredentialRequestOptions => ({
  ...raw,
  challenge: decodeBase64Url(raw.challenge),
  allowCredentials: (raw.allowCredentials || []).map((credential: any) => ({
    ...credential,
    id: decodeBase64Url(credential.id),
  })),
});

const serializeCredential = (credential: PublicKeyCredential): Record<string, any> => {
  const response = credential.response;
  const serializedResponse: Record<string, any> = {
    clientDataJSON: encodeBase64Url(response.clientDataJSON),
  };

  if (response instanceof AuthenticatorAttestationResponse) {
    serializedResponse.attestationObject = encodeBase64Url(response.attestationObject);
    if (typeof response.getTransports === 'function') {
      serializedResponse.transports = response.getTransports();
    }
  } else if (response instanceof AuthenticatorAssertionResponse) {
    serializedResponse.authenticatorData = encodeBase64Url(response.authenticatorData);
    serializedResponse.signature = encodeBase64Url(response.signature);
    serializedResponse.userHandle = response.userHandle ? encodeBase64Url(response.userHandle) : null;
  }

  return {
    id: credential.id,
    rawId: encodeBase64Url(credential.rawId),
    type: credential.type,
    authenticatorAttachment: credential.authenticatorAttachment,
    clientExtensionResults: credential.getClientExtensionResults(),
    response: serializedResponse,
  };
};

export type PlatformPasskeyStatus = {
  enrolled: boolean;
  origin_ready: boolean;
  step_up_valid: boolean;
  rp_id: string;
  expected_origin: string;
};

export const fetchPlatformPasskeyStatus = async (): Promise<PlatformPasskeyStatus> => {
  const response = await api.get('/superadmin/passkey/status');
  return response.data as PlatformPasskeyStatus;
};

export const establishPlatformStepUp = async (enrolled: boolean): Promise<void> => {
  if (!window.PublicKeyCredential || !navigator.credentials) {
    throw new Error('WebAuthn indisponible sur ce navigateur.');
  }

  const purpose = enrolled ? 'authentication' : 'registration';
  const optionsResponse = await api.post(`/superadmin/passkey/${purpose}/options`);
  const { challenge_id: challengeId, ...rawOptions } = optionsResponse.data as Record<string, any>;

  const credential = enrolled
    ? await navigator.credentials.get({ publicKey: authenticationOptions(rawOptions) })
    : await navigator.credentials.create({ publicKey: registrationOptions(rawOptions) });

  if (!(credential instanceof PublicKeyCredential)) {
    throw new Error('Vérification WebAuthn interrompue.');
  }

  await api.post(`/superadmin/passkey/${purpose}/verify`, {
    challenge_id: challengeId,
    credential: serializeCredential(credential),
  });
};

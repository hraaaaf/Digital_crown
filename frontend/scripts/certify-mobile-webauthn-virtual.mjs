import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const origin = 'https://digitalcrown.local:5173';
const artifactDir = resolve(process.cwd(), '../artifacts/mobile-sim-cert/webauthn');
await mkdir(artifactDir, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  args: ['--host-resolver-rules=MAP digitalcrown.local 127.0.0.1,EXCLUDE localhost'],
});
const context = await browser.newContext({
  ignoreHTTPSErrors: true,
  viewport: { width: 390, height: 844 },
  isMobile: true,
  hasTouch: true,
});
const page = await context.newPage();
const cdp = await context.newCDPSession(page);

try {
  await cdp.send('WebAuthn.enable');
  const { authenticatorId } = await cdp.send('WebAuthn.addVirtualAuthenticator', {
    options: {
      protocol: 'ctap2',
      transport: 'internal',
      hasResidentKey: true,
      hasUserVerification: true,
      isUserVerified: true,
      automaticPresenceSimulation: true,
    },
  });

  await page.goto(`${origin}/mobile/onboarding`, {
    waitUntil: 'domcontentloaded',
    timeout: 30_000,
  });

  const result = await page.evaluate(async () => {
    if (!window.isSecureContext) throw new Error('Expected secure context');
    if (!('credentials' in navigator)) throw new Error('Credential Management API unavailable');

    const challengeCreate = crypto.getRandomValues(new Uint8Array(32));
    const userId = crypto.getRandomValues(new Uint8Array(16));
    const created = await navigator.credentials.create({
      publicKey: {
        challenge: challengeCreate,
        rp: { id: 'digitalcrown.local', name: 'Digital Crown SIM-CERT' },
        user: {
          id: userId,
          name: 'sim-cert@digitalcrown.local',
          displayName: 'Digital Crown SIM-CERT',
        },
        pubKeyCredParams: [{ type: 'public-key', alg: -7 }],
        authenticatorSelection: {
          authenticatorAttachment: 'platform',
          residentKey: 'required',
          userVerification: 'required',
        },
        timeout: 10_000,
        attestation: 'none',
      },
    });

    if (!(created instanceof PublicKeyCredential)) {
      throw new Error('Credential creation did not return PublicKeyCredential');
    }

    const challengeGet = crypto.getRandomValues(new Uint8Array(32));
    const assertion = await navigator.credentials.get({
      publicKey: {
        challenge: challengeGet,
        rpId: 'digitalcrown.local',
        allowCredentials: [{ type: 'public-key', id: created.rawId }],
        userVerification: 'required',
        timeout: 10_000,
      },
    });

    if (!(assertion instanceof PublicKeyCredential)) {
      throw new Error('Credential assertion did not return PublicKeyCredential');
    }

    return {
      origin: window.location.origin,
      secureContext: window.isSecureContext,
      userAgent: navigator.userAgent,
      credentialId: created.id,
      assertionCredentialId: assertion.id,
      credentialType: created.type,
      assertionType: assertion.type,
    };
  });

  if (result.origin !== origin) {
    throw new Error(`Origin mismatch: ${result.origin}`);
  }
  if (result.credentialId !== result.assertionCredentialId) {
    throw new Error('WebAuthn assertion credential does not match created credential');
  }

  await page.screenshot({
    path: resolve(artifactDir, 'exact-origin-mobile.png'),
    fullPage: true,
  });
  await writeFile(
    resolve(artifactDir, 'result.json'),
    JSON.stringify(
      {
        head: process.env.GITHUB_SHA ?? null,
        scope: 'VIRTUAL_PLATFORM_AUTHENTICATOR_NOT_PHYSICAL_BIOMETRIC',
        ...result,
      },
      null,
      2,
    ),
    'utf8',
  );
  console.log(JSON.stringify(result));
} finally {
  await browser.close();
}

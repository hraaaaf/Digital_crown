import { chromium, webkit } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import {
  CompactEncrypt,
  CompactSign,
  compactDecrypt,
  compactVerify,
  exportJWK,
  generateKeyPair,
  importJWK,
} from 'jose';

const baseUrl = process.env.PC07_AFTER_URL || 'http://127.0.0.1:5183';
const outputRoot = process.env.PC07_EVIDENCE_DIR || '../artifacts/pc07-emergency-photo-after';
const viewports = [{ width: 360, height: 800 }, { width: 390, height: 844 }];
const browsers = { chromium, webkit };
const states = ['idle', 'preview', 'pending', 'success'];
const evidence = [];
const token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzA3LWFmdGVyIiwiZXhwIjoyMDAwMDAwMDAwfQ.audit';
const accessId = '77777777-7777-4777-8777-777777777777';
const encoder = new TextEncoder();
const decoder = new TextDecoder();
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFElEQVR4nGP8z8DAwMDAxMDAAAANHQEDasKb6QAAAABJRU5ErkJggg==', 'base64');

async function keys() {
  const signing = await generateKeyPair('ES256');
  const encryption = await generateKeyPair('ECDH-ES+A256KW', { crv: 'P-256' });
  const signingKid = crypto.randomUUID();
  const encryptionKid = crypto.randomUUID();
  const signingPublic = { ...(await exportJWK(signing.publicKey)), kid: signingKid, use: 'sig' };
  const encryptionPublic = { ...(await exportJWK(encryption.publicKey)), kid: encryptionKid, use: 'enc' };
  return { signing, encryption, signingKid, encryptionKid, signingPublic, encryptionPublic };
}

async function makeAck(blob, harness, patientKeys) {
  const decrypted = await compactDecrypt(blob, harness.encryption.privateKey, {
    keyManagementAlgorithms: ['ECDH-ES+A256KW'],
    contentEncryptionAlgorithms: ['A256GCM'],
  });
  const signedRequest = decoder.decode(decrypted.plaintext);
  const patientSigning = await importJWK(patientKeys.signing_public_jwk, 'ES256');
  const verified = await compactVerify(signedRequest, patientSigning, { algorithms: ['ES256'] });
  const request = JSON.parse(decoder.decode(verified.payload));
  const op = request.operation;
  let result = { state: 'uploading' };
  if (op === 'emergency_photo.begin') {
    result = { state: 'uploading', received_chunks: 0, chunk_count: request.payload.chunk_count };
  } else if (op === 'emergency_photo.chunk') {
    result = { state: 'uploading', received_chunks: Number(request.payload.chunk_index) + 1, chunk_count: 1 };
  } else if (op === 'emergency_photo.finalize') {
    result = { state: 'received', asset_id: 77, received_at: new Date().toISOString() };
  }

  const now = new Date();
  const ack = {
    protocol_version: 'dc-pc-remote-v1',
    message_id: crypto.randomUUID(),
    access_id: request.access_id,
    sent_at: now.toISOString(),
    expires_at: new Date(now.getTime() + 10 * 60 * 1000).toISOString(),
    idempotency_key: request.idempotency_key,
    operation: 'command.result',
    payload: {
      request_message_id: request.message_id,
      request_operation: op,
      status: 'ACCEPTED',
      result,
    },
  };
  const compactJws = await new CompactSign(encoder.encode(JSON.stringify(ack)))
    .setProtectedHeader({ alg: 'ES256', kid: harness.signingKid, typ: 'application/dc-pc+jws' })
    .sign(harness.signing.privateKey);
  const patientEncryption = await importJWK(patientKeys.encryption_public_jwk, 'ECDH-ES+A256KW');
  return new CompactEncrypt(encoder.encode(compactJws))
    .setProtectedHeader({
      alg: 'ECDH-ES+A256KW',
      enc: 'A256GCM',
      kid: patientKeys.encryption_kid,
      typ: 'application/dc-pc+jwe',
      cty: 'application/dc-pc+jws',
    })
    .encrypt(patientEncryption);
}

async function installHarness(page, mode) {
  const harness = await keys();
  let patientKeys = null;

  await page.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());

    if (url.hostname === 'relay.test') {
      if (request.method() === 'POST') {
        return route.fulfill({ status: 201, contentType: 'application/json', body: '{}' });
      }
      if (request.method() === 'GET') {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [] }) });
      }
      return route.fulfill({ status: 204, body: '' });
    }

    if (!url.pathname.startsWith('/api/patient-companion/')) return route.continue();

    if (url.pathname === '/api/patient-companion/pair' && request.method() === 'POST') {
      const body = request.postDataJSON();
      patientKeys = body.remote_keys;
      const relay = mode === 'pending'
        ? {
            protocol_version: 'dc-relay-v1',
            relay_url: 'https://relay.test',
            cabinet_inbox: {
              mailbox_id: '11111111-1111-4111-8111-111111111111',
              write_capability: 'a'.repeat(43),
            },
            patient_inbox: {
              mailbox_id: '22222222-2222-4222-8222-222222222222',
              read_capability: 'b'.repeat(43),
            },
          }
        : undefined;
      return route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: token,
          context: { access_id: accessId, relationship_type: 'SELF', patient: { display_name: 'Aya Urgence' } },
          paired_at: '2026-09-21T09:00:00Z',
          remote_transport: {
            status: 'enrolled',
            protocol_version: 'dc-pc-remote-v1',
            keyset_id: '33333333-3333-4333-8333-333333333333',
            patient_signing_kid: patientKeys.signing_kid,
            patient_encryption_kid: patientKeys.encryption_kid,
            cabinet: {
              signing: { kid: harness.signingKid, public_jwk: harness.signingPublic },
              encryption: { kid: harness.encryptionKid, public_jwk: harness.encryptionPublic },
            },
            ...(relay ? { relay } : {}),
          },
        }),
      });
    }

    if (url.pathname.endsWith('/emergency-photo/remote-command') && request.method() === 'POST') {
      const body = request.postDataJSON();
      const ack = await makeAck(body.blob, harness, patientKeys);
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ blob: ack }) });
    }

    if (url.pathname.endsWith('/agenda') || url.pathname.endsWith('/shares') || url.pathname.endsWith('/questionnaires') || url.pathname.endsWith('/consents')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [] }) });
    }
    if (url.pathname.endsWith('/notifications')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], preferences: { appointments: true, documents: true, questionnaires: true, consents: true } }),
      });
    }
    return route.fulfill({ status: 404, contentType: 'application/json', body: '{}' });
  });
}

async function pair(page) {
  await page.goto(`${baseUrl}/companion`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Appairer ce téléphone', { exact: true }).waitFor();
  await page.getByLabel('Code manuel').fill('ABCD-EFGH-JKLM');
  await page.getByText('Appairer avec le code', { exact: true }).click();
  await page.getByText('Aya Urgence', { exact: true }).waitFor();
  await page.locator('[data-pc07-emergency-photo]').waitFor();
}

async function choosePhoto(page) {
  const input = page.locator('[data-pc07-emergency-photo] input[type=file]');
  await input.setInputFiles({ name: 'urgence.png', mimeType: 'image/png', buffer: png });
  await page.getByText('Envoyer au cabinet', { exact: true }).waitFor();
}

for (const [browserName, browserType] of Object.entries(browsers)) {
  const browser = await browserType.launch({ headless: true });
  try {
    for (const viewport of viewports) {
      for (const state of states) {
        const context = await browser.newContext({ viewport });
        if (state === 'pending') {
          await context.addInitScript(() => {
            const nativeSetTimeout = window.setTimeout.bind(window);
            window.setTimeout = ((handler, timeout = 0, ...args) =>
              nativeSetTimeout(handler, timeout === 1000 ? 25 : timeout, ...args)) as typeof window.setTimeout;
          });
        }
        const page = await context.newPage();
        await installHarness(page, state === 'pending' ? 'pending' : 'direct');
        await pair(page);

        if (state !== 'idle') await choosePhoto(page);
        if (state === 'pending' || state === 'success') {
          await page.getByText('Envoyer au cabinet', { exact: true }).click();
        }
        if (state === 'pending') {
          await page.getByText(/aucune réception cabinet n’est encore confirmée/i).waitFor({ timeout: 15000 });
        }
        if (state === 'success') {
          await page.getByText('Photo reçue par le cabinet.', { exact: true }).waitFor({ timeout: 15000 });
        }

        const root = page.locator('[data-pc07-emergency-photo]');
        const controls = await root.locator('button').evaluateAll(nodes =>
          nodes.map(node => ({ height: node.getBoundingClientRect().height, width: node.getBoundingClientRect().width }))
        );
        if (controls.some(control => control.height < 44)) throw new Error('PC07 actionable control below 44px');
        const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
        if (horizontalOverflow) throw new Error('PC07 AFTER horizontal overflow');

        const screenshot = `${browserName}-${state}-${viewport.width}x${viewport.height}.png`;
        await fs.mkdir(path.join(outputRoot, 'after'), { recursive: true });
        await page.screenshot({ path: path.join(outputRoot, 'after', screenshot), fullPage: true });
        evidence.push({ browser: browserName, phase: 'after', state, viewport, screenshot, horizontalOverflow, controls });
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
}
await fs.writeFile(path.join(outputRoot, 'evidence.json'), JSON.stringify(evidence, null, 2));

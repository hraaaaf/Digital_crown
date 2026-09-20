import fs from 'node:fs';
import { webcrypto } from 'node:crypto';
import {
  CompactEncrypt,
  CompactSign,
  compactDecrypt,
  compactVerify,
  importJWK,
} from 'jose';

if (!globalThis.crypto) globalThis.crypto = webcrypto;

const [, , pythonPath, jsPath] = process.argv;
if (!pythonPath || !jsPath) throw new Error('usage: node certify-pc-remote-interop.mjs <python-json> <js-json>');

const keys = JSON.parse(fs.readFileSync('../backend/tests/fixtures/patient_companion_remote_test_keys.json', 'utf8'));
const fromPython = JSON.parse(fs.readFileSync(pythonPath, 'utf8'));

const JWS_ALG = 'ES256';
const JWE_ALG = 'ECDH-ES+A256KW';
const JWE_ENC = 'A256GCM';
const JWS_TYP = 'application/dc-pc+jws';
const JWE_TYP = 'application/dc-pc+jwe';

const publicOnly = ({ d: _d, ...value }) => value;
const exactKeys = (obj, expected) => {
  const a = Object.keys(obj).sort();
  const b = [...expected].sort();
  return a.length === b.length && a.every((item, index) => item === b[index]);
};

const patientEncPrivate = await importJWK(keys.patient_encryption, JWE_ALG);
const decrypted = await compactDecrypt(fromPython.token, patientEncPrivate, {
  keyManagementAlgorithms: [JWE_ALG],
  contentEncryptionAlgorithms: [JWE_ENC],
});
if (!exactKeys(decrypted.protectedHeader, ['alg', 'enc', 'kid', 'typ', 'cty', 'epk'])) {
  throw new Error('Python JWE protected-header shape mismatch');
}
if (
  decrypted.protectedHeader.alg !== JWE_ALG
  || decrypted.protectedHeader.enc !== JWE_ENC
  || decrypted.protectedHeader.kid !== keys.patient_encryption.kid
  || decrypted.protectedHeader.typ !== JWE_TYP
  || decrypted.protectedHeader.cty !== JWS_TYP
) {
  throw new Error('Python JWE protected-header value mismatch');
}
const epk = decrypted.protectedHeader.epk;
if (!epk || !exactKeys(epk, ['kty', 'crv', 'x', 'y']) || epk.kty !== 'EC' || epk.crv !== 'P-256') {
  throw new Error('Python JWE epk mismatch');
}

const cabinetSigningPublic = await importJWK(publicOnly(keys.cabinet_signing), JWS_ALG);
const signed = new TextDecoder().decode(decrypted.plaintext);
const verified = await compactVerify(signed, cabinetSigningPublic, { algorithms: [JWS_ALG] });
if (!exactKeys(verified.protectedHeader, ['alg', 'kid', 'typ'])) {
  throw new Error('Python JWS protected-header shape mismatch');
}
if (
  verified.protectedHeader.alg !== JWS_ALG
  || verified.protectedHeader.kid !== keys.cabinet_signing.kid
  || verified.protectedHeader.typ !== JWS_TYP
) {
  throw new Error('Python JWS protected-header value mismatch');
}
const decodedPythonPayload = JSON.parse(new TextDecoder().decode(verified.payload));
const canonicalJson = (value) => JSON.stringify(
  Object.fromEntries(Object.entries(value).sort(([a], [b]) => a.localeCompare(b))),
);
if (canonicalJson(decodedPythonPayload) !== canonicalJson(fromPython.payload)) {
  throw new Error('Python -> JS JOSE payload mismatch');
}

const browserSigning = await crypto.subtle.generateKey(
  { name: 'ECDSA', namedCurve: 'P-256' },
  false,
  ['sign', 'verify'],
);
const browserEncryption = await crypto.subtle.generateKey(
  { name: 'ECDH', namedCurve: 'P-256' },
  false,
  ['deriveBits', 'deriveKey'],
);
if (browserSigning.privateKey.extractable || browserEncryption.privateKey.extractable) {
  throw new Error('browser private keys unexpectedly exportable');
}
if (!browserSigning.publicKey.extractable || !browserEncryption.publicKey.extractable) {
  throw new Error('browser public keys unexpectedly non-exportable');
}

const patientSigningPrivate = await importJWK(keys.patient_signing, JWS_ALG);
const cabinetEncryptionPublic = await importJWK(publicOnly(keys.cabinet_encryption), JWE_ALG);
const jsPayload = {
  protocol_version: 'dc-pc-remote-v1',
  direction: 'patient-to-cabinet',
  proof: 'js-jose-to-python-jwcrypto',
};
const jsJws = await new CompactSign(new TextEncoder().encode(JSON.stringify(jsPayload)))
  .setProtectedHeader({
    alg: JWS_ALG,
    kid: keys.patient_signing.kid,
    typ: JWS_TYP,
  })
  .sign(patientSigningPrivate);
const jsJwe = await new CompactEncrypt(new TextEncoder().encode(jsJws))
  .setProtectedHeader({
    alg: JWE_ALG,
    enc: JWE_ENC,
    kid: keys.cabinet_encryption.kid,
    typ: JWE_TYP,
    cty: JWS_TYP,
  })
  .encrypt(cabinetEncryptionPublic);

fs.writeFileSync(jsPath, JSON.stringify({ token: jsJwe, payload: jsPayload }));

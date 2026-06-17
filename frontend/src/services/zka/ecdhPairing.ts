/**
 * ECDH ZKA Pairing (S5) — échange de clé sécurisé pour l'appairage mobile.
 *
 * La masterKey ne transite JAMAIS en clair. Le client génère une paire ECDH
 * (P-256), envoie sa clé publique au backend, qui chiffre la masterKey en
 * AES-256-GCM via un secret partagé dérivé en HKDF-SHA256. Doit rester aligné
 * avec backend/routers/mobile.py::claim_pairing_token (info = "zka_mobile_bridge",
 * salt HKDF = 32 octets nuls, nonce GCM = 12 octets préfixés au ciphertext).
 */

function bufToHex(buf: ArrayBuffer): string {
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

function hexToBytes(hex: string): Uint8Array {
  const clean = hex.trim();
  const out = new Uint8Array(clean.length / 2);
  for (let i = 0; i < out.length; i++) {
    out[i] = parseInt(clean.substr(i * 2, 2), 16);
  }
  return out;
}

export interface ClientKeyPair {
  privateKey: CryptoKey;
  publicKeyHex: string;
}

/** Génère une paire ECDH P-256 ; retourne la clé publique en hex (point non compressé). */
export async function generateClientKeyPair(): Promise<ClientKeyPair> {
  const keyPair = await crypto.subtle.generateKey(
    { name: 'ECDH', namedCurve: 'P-256' },
    false, // privée non extractible
    ['deriveBits'],
  );
  const raw = await crypto.subtle.exportKey('raw', keyPair.publicKey); // 0x04 || X || Y (65 octets)
  return { privateKey: keyPair.privateKey, publicKeyHex: bufToHex(raw) };
}

/**
 * Dérive la masterKey à partir de la clé publique serveur et du blob chiffré.
 * Retourne la masterKey (chaîne hex 64 caractères).
 */
export async function deriveMasterKey(
  privateKey: CryptoKey,
  serverPublicKeyHex: string,
  encryptedMasterKeyHex: string,
): Promise<string> {
  const serverPubKey = await crypto.subtle.importKey(
    'raw',
    hexToBytes(serverPublicKeyHex),
    { name: 'ECDH', namedCurve: 'P-256' },
    false,
    [],
  );

  const sharedBits = await crypto.subtle.deriveBits(
    { name: 'ECDH', public: serverPubKey },
    privateKey,
    256, // 32 octets (coordonnée X) — identique au exchange() Python
  );

  const hkdfKey = await crypto.subtle.importKey('raw', sharedBits, 'HKDF', false, ['deriveKey']);

  const aesKey = await crypto.subtle.deriveKey(
    {
      name: 'HKDF',
      hash: 'SHA-256',
      salt: new Uint8Array(32), // salt=None côté Python ⇒ 32 octets nuls (RFC5869)
      info: new TextEncoder().encode('zka_mobile_bridge'),
    },
    hkdfKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['decrypt'],
  );

  const blob = hexToBytes(encryptedMasterKeyHex);
  const nonce = blob.slice(0, 12);
  const ciphertext = blob.slice(12);

  const plain = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: nonce }, aesKey, ciphertext);
  return new TextDecoder().decode(plain);
}

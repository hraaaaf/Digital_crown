/**
 * Service cryptographique Zero-Knowledge (ZKA) pour le frontend Mobile.
 * Utilise AES-256-GCM via la Web Crypto API native.
 */

export const CryptoService = {
  /**
   * Importe la clé maître (hexadécimale de 64 chars) en CryptoKey.
   */
  async importKey(hexKey: string): Promise<CryptoKey> {
    if (hexKey.length !== 64) throw new Error('Clé maître invalide. Doit faire 64 caractères hex.');
    
    // Convert hex string to ArrayBuffer
    const keyBytes = new Uint8Array(hexKey.match(/.{1,2}/g)!.map(byte => parseInt(byte, 16)));
    
    return await window.crypto.subtle.importKey(
      'raw',
      keyBytes,
      { name: 'AES-GCM' },
      false,
      ['encrypt', 'decrypt']
    );
  },

  /**
   * Déchiffre un payload chiffré par le backend.
   * payload est un base64 de : IV (12) + Ciphertext + Tag (16)
   */
  async decryptPayload(base64Payload: string, hexKey: string): Promise<any> {
    const key = await this.importKey(hexKey);
    
    const binaryStr = atob(base64Payload);
    const combinedBytes = new Uint8Array(binaryStr.length);
    for (let i = 0; i < binaryStr.length; i++) {
      combinedBytes[i] = binaryStr.charCodeAt(i);
    }
    
    // La Web Crypto API s'attend à ce que le tag soit inclus à la fin du ciphertext
    const iv = combinedBytes.slice(0, 12);
    const dataWithTag = combinedBytes.slice(12);
    
    const decryptedBuffer = await window.crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: iv,
      },
      key,
      dataWithTag
    );
    
    const dec = new TextDecoder('utf-8');
    const jsonStr = dec.decode(decryptedBuffer);
    return JSON.parse(jsonStr);
  },

  /**
   * Chiffre un payload JSON pour l'envoyer au backend.
   * Retourne la structure : base64(IV + Ciphertext + Tag)
   */
  async encryptPayload(data: any, hexKey: string): Promise<string> {
    const key = await this.importKey(hexKey);
    
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const enc = new TextEncoder();
    const plaintext = enc.encode(JSON.stringify(data));
    
    const encryptedBuffer = await window.crypto.subtle.encrypt(
      {
        name: 'AES-GCM',
        iv: iv,
      },
      key,
      plaintext
    );
    
    // Le buffer contient Ciphertext + Tag
    const encryptedBytes = new Uint8Array(encryptedBuffer);
    
    // Combiner IV + Ciphertext + Tag
    const combinedBytes = new Uint8Array(iv.length + encryptedBytes.length);
    combinedBytes.set(iv, 0);
    combinedBytes.set(encryptedBytes, iv.length);
    
    let binaryStr = '';
    for (let i = 0; i < combinedBytes.length; i++) {
      binaryStr += String.fromCharCode(combinedBytes[i]);
    }
    
    return btoa(binaryStr);
  }
};

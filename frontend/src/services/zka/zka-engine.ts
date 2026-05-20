/**
 * ZKA-ENGINE (Digital Crown Elite Edition)
 * Moteur de déchiffrement Zero-Knowledge utilisant la Web Crypto API.
 */

export class ZKAEngine {
  /**
   * Convertit une clé hexadécimale (Master Key) en CryptoKey exploitable.
   */
  private static async importMasterKey(hexKey: string): Promise<CryptoKey> {
    const keyBuffer = new Uint8Array(
      hexKey.match(/.{1,2}/g)!.map(byte => parseInt(byte, 16))
    );

    return window.crypto.subtle.importKey(
      "raw",
      keyBuffer,
      { name: "AES-GCM", length: 256 },
      false,
      ["decrypt"]
    );
  }

  /**
   * Déchiffre un payload Base64 provenant de Supabase.
   * @param base64Blob Le blob contenant [IV(12b)][Ciphertext][Tag(16b)]
   * @param hexKey La clé maître (hex) scannée via QR Code.
   */
  public static async decryptPayload(base64Blob: string, hexKey: string): Promise<any> {
    try {
      // 1. Conversion Base64 -> Uint8Array
      const binaryString = window.atob(base64Blob);
      const buffer = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        buffer[i] = binaryString.charCodeAt(i);
      }

      // 2. Slicing chirurgical
      // IV = 12 premiers octets
      // Data = le reste (Ciphertext + Tag)
      const iv = buffer.slice(0, 12);
      const data = buffer.slice(12);

      // 3. Préparation de la clé
      const cryptoKey = await this.importMasterKey(hexKey);

      // 4. Déchiffrement
      const decryptedBuffer = await window.crypto.subtle.decrypt(
        {
          name: "AES-GCM",
          iv: iv,
          tagLength: 128, // Standard AES-GCM (16 octets)
        },
        cryptoKey,
        data
      );

      // 5. Décodage texte -> JSON
      const decoder = new TextDecoder();
      const jsonString = decoder.decode(decryptedBuffer);
      
      return JSON.parse(jsonString);
    } catch (error) {
      console.error("❌ Échec critique du déchiffrement ZKA:", error);
      throw new Error("Impossible de déchiffrer les données. Clé invalide ou payload corrompu.");
    }
  }
}

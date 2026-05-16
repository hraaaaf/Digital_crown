import localforage from 'localforage';

/**
 * MOBILE-STORAGE (Digital Crown Elite)
 * Gestionnaire de stockage sécurisé utilisant IndexedDB.
 */

localforage.config({
  driver: localforage.INDEXEDDB,
  name: 'digital-crown-zka',
  version: 1.0,
  storeName: 'secure_keys',
});

const STORE_CREDENTIALS_ID = 'zka_credentials';
const STORE_SNAPSHOT_ID = 'zka_last_snapshot';

export interface ZKACredentials {
  publicId: string;
  masterKey: string;
}

export const MobileStorage = {
  /**
   * Sauvegarde le duo ID Cabinet + Clé Maître.
   */
  async saveCredentials(creds: ZKACredentials): Promise<void> {
    if (!/^[0-9a-fA-F]{16}$/.test(creds.publicId)) throw new Error("ID Cabinet invalide.");
    if (!/^[0-9a-fA-F]{64}$/.test(creds.masterKey)) throw new Error("Clé Maître invalide.");
    await localforage.setItem(STORE_CREDENTIALS_ID, creds);
  },

  /**
   * Cache le dernier snapshot déchiffré (SWR).
   */
  async saveLastSnapshot(data: any): Promise<void> {
    await localforage.setItem(STORE_SNAPSHOT_ID, data);
  },

  /**
   * Récupère le snapshot en cache.
   */
  async getLastSnapshot(): Promise<any | null> {
    return await localforage.getItem(STORE_SNAPSHOT_ID);
  },

  /**
   * Récupère les identifiants complets.
   */
  async getCredentials(): Promise<ZKACredentials | null> {
    return await localforage.getItem<ZKACredentials>(STORE_CREDENTIALS_ID);
  },

  /**
   * Effacement complet (Révocation / Logout).
   */
  async clearAll(): Promise<void> {
    await localforage.removeItem(STORE_CREDENTIALS_ID);
    await localforage.removeItem(STORE_SNAPSHOT_ID);
  },

  /**
   * Vérifie si l'appairage est actif.
   */
  async isPaired(): Promise<boolean> {
    const creds = await this.getCredentials();
    return !!(creds?.publicId && creds?.masterKey);
  }
};

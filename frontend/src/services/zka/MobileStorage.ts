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
  /** JWT mobile 24h pour /api/mobile/snapshot */
  access_token: string;
  /** URL du backend LAN (ex: http://192.168.1.50:8000) */
  api_base_url: string;
}

export const MobileStorage = {
  async saveCredentials(creds: ZKACredentials): Promise<void> {
    if (!/^[0-9a-fA-F]{16}$/.test(creds.publicId)) throw new Error('ID Cabinet invalide.');
    if (!/^[0-9a-fA-F]{64}$/.test(creds.masterKey)) throw new Error('Clé Maître invalide.');
    if (!creds.access_token) throw new Error('Token mobile manquant.');
    await localforage.setItem(STORE_CREDENTIALS_ID, creds);
  },

  async saveLastSnapshot(data: any): Promise<void> {
    await localforage.setItem(STORE_SNAPSHOT_ID, { data, saved_at: Date.now() });
  },

  async getLastSnapshot(): Promise<any | null> {
    const entry = await localforage.getItem<{ data: any; saved_at: number }>(STORE_SNAPSHOT_ID);
    return entry?.data ?? null;
  },

  async getCredentials(): Promise<ZKACredentials | null> {
    return localforage.getItem<ZKACredentials>(STORE_CREDENTIALS_ID);
  },

  async clearAll(): Promise<void> {
    await localforage.removeItem(STORE_CREDENTIALS_ID);
    await localforage.removeItem(STORE_SNAPSHOT_ID);
  },

  async isPaired(): Promise<boolean> {
    const creds = await this.getCredentials();
    return !!(creds?.publicId && creds?.masterKey && creds?.access_token);
  },
};

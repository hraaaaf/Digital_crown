import { api } from '../../services/api';
import type { R5PreferenceRecord } from './R5PreferencesPolicy';

export type R5PersistedState = Readonly<{
  revision: number;
  record: R5PreferenceRecord | null;
  canRollback: boolean;
}>;

/** No browser storage, no Firebase; workstation HttpOnly cookie + user JWT only. */
export const r5PreferencesService = {
  async load(): Promise<R5PersistedState> {
    const {data}=await api.get<R5PersistedState>('/workstation/r5-preferences');
    return data;
  },
  async save(record: R5PreferenceRecord,expectedRevision: number): Promise<R5PersistedState> {
    const {data}=await api.put<R5PersistedState>('/workstation/r5-preferences',{
      record,expectedRevision,
    });
    return data;
  },
  async rollback(expectedRevision: number): Promise<R5PersistedState> {
    const {data}=await api.post<R5PersistedState>('/workstation/r5-preferences/rollback',{expectedRevision});
    return data;
  },
};

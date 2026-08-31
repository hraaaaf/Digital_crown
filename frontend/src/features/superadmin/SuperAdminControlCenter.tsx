import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  BadgeCheck,
  KeyRound,
  Laptop,
  RefreshCw,
  ShieldCheck,
  UserCog,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  establishPlatformStepUp,
  fetchPlatformPasskeyStatus,
  type PlatformPasskeyStatus,
} from './platformPasskey';

type Client = {
  id: number;
  email: string;
  nom_complet?: string | null;
};

type Device = {
  device_id: string;
  user_id: number;
  created_at?: string | null;
  last_seen_at?: string | null;
  revoked_at?: string | null;
  active: boolean;
};

type DevicePayload = {
  client_id: number;
  license: {
    active: boolean;
    license_type?: string | null;
    max_devices?: number | null;
    active_devices: number;
    release_channel?: 'stable' | 'beta' | null;
  };
  devices: Device[];
};

type Operator = {
  id: number;
  email: string;
  nom_complet?: string | null;
  is_active: boolean;
  is_suspended: boolean;
  is_owner: boolean;
  permissions: Record<string, boolean>;
};

type AuditRow = {
  id: number;
  timestamp: string;
  user_id?: number | null;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  severity?: string | null;
  details?: string | null;
};

type PanelState = 'loading' | 'ready' | 'forbidden' | 'error';

const PLATFORM_PERMISSIONS = [
  'license.read',
  'license.create_trial',
  'license.create_paid',
  'license.extend',
  'license.suspend',
  'license.revoke',
  'license.manage_devices',
  'license.change_release_channel',
  'admin.read',
  'admin.create',
  'admin.update_permissions',
  'admin.disable',
  'audit.read',
] as const;

const isForbidden = (error: unknown): boolean => {
  const candidate = error as { response?: { status?: number } };
  return candidate?.response?.status === 403;
};

const errorMessage = (error: unknown): string => {
  const candidate = error as {
    response?: { data?: { detail?: string | { message?: string } } };
    message?: string;
  };
  const detail = candidate.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object' && typeof detail.message === 'string') return detail.message;
  return candidate.message || 'Action plateforme impossible.';
};

const Card: React.FC<React.PropsWithChildren<{ title: string; icon: React.ReactNode; testId?: string }>> = ({
  title,
  icon,
  testId,
  children,
}) => (
  <section
    className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
    data-testid={testId}
  >
    <div className="mb-5 flex items-center gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
        {icon}
      </div>
      <h2 className="text-lg font-black tracking-tight text-slate-900">{title}</h2>
    </div>
    {children}
  </section>
);

const PermissionDenied: React.FC = () => (
  <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm font-semibold text-amber-900">
    Permission plateforme insuffisante pour ce panneau.
  </div>
);

const PanelError: React.FC<{ message: string }> = ({ message }) => (
  <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-4 text-sm font-semibold text-rose-900">
    {message}
  </div>
);

const PermissionChecklist: React.FC<{
  value: Record<string, boolean>;
  onChange: (next: Record<string, boolean>) => void;
  disabled?: boolean;
}> = ({ value, onChange, disabled }) => (
  <div className="grid gap-2 sm:grid-cols-2">
    {PLATFORM_PERMISSIONS.map((permission) => (
      <label
        key={permission}
        className="flex min-h-10 items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700"
      >
        <input
          type="checkbox"
          checked={value[permission] === true}
          disabled={disabled}
          onChange={(event) => onChange({ ...value, [permission]: event.target.checked })}
          className="h-4 w-4 rounded border-slate-300"
        />
        <span className="break-all">{permission}</span>
      </label>
    ))}
  </div>
);

export const SuperAdminControlCenter: React.FC = () => {
  const [passkey, setPasskey] = useState<PlatformPasskeyStatus | null>(null);
  const [passkeyState, setPasskeyState] = useState<PanelState>('loading');
  const [passkeyError, setPasskeyError] = useState('');
  const [stepUpBusy, setStepUpBusy] = useState(false);

  const [clients, setClients] = useState<Client[]>([]);
  const [clientState, setClientState] = useState<PanelState>('loading');
  const [clientError, setClientError] = useState('');
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null);
  const [devicePayload, setDevicePayload] = useState<DevicePayload | null>(null);
  const [deviceState, setDeviceState] = useState<PanelState>('loading');
  const [deviceError, setDeviceError] = useState('');
  const [deviceBusy, setDeviceBusy] = useState<string | null>(null);
  const [releaseBusy, setReleaseBusy] = useState(false);

  const [operators, setOperators] = useState<Operator[]>([]);
  const [operatorState, setOperatorState] = useState<PanelState>('loading');
  const [operatorError, setOperatorError] = useState('');
  const [operatorBusy, setOperatorBusy] = useState<number | 'create' | null>(null);
  const [operatorDrafts, setOperatorDrafts] = useState<Record<number, Record<string, boolean>>>({});
  const [candidateUserId, setCandidateUserId] = useState('');
  const [candidatePermissions, setCandidatePermissions] = useState<Record<string, boolean>>({});

  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [auditState, setAuditState] = useState<PanelState>('loading');
  const [auditError, setAuditError] = useState('');

  const loadPasskey = useCallback(async () => {
    setPasskeyState('loading');
    try {
      const status = await fetchPlatformPasskeyStatus();
      setPasskey(status);
      setPasskeyState('ready');
      setPasskeyError('');
    } catch (error) {
      setPasskeyState(isForbidden(error) ? 'forbidden' : 'error');
      setPasskeyError(errorMessage(error));
    }
  }, []);

  const loadClients = useCallback(async () => {
    setClientState('loading');
    try {
      const response = await api.get('/superadmin/clients');
      const rows = (response.data || []) as Client[];
      setClients(rows);
      setSelectedClientId((current) => current ?? rows[0]?.id ?? null);
      setClientState('ready');
      setClientError('');
    } catch (error) {
      setClientState(isForbidden(error) ? 'forbidden' : 'error');
      setClientError(errorMessage(error));
    }
  }, []);

  const loadDevices = useCallback(async (clientId: number) => {
    setDeviceState('loading');
    try {
      const response = await api.get(`/superadmin/platform-admins/clients/${clientId}/devices`);
      setDevicePayload(response.data as DevicePayload);
      setDeviceState('ready');
      setDeviceError('');
    } catch (error) {
      setDevicePayload(null);
      setDeviceState(isForbidden(error) ? 'forbidden' : 'error');
      setDeviceError(errorMessage(error));
    }
  }, []);

  const loadOperators = useCallback(async () => {
    setOperatorState('loading');
    try {
      const response = await api.get('/superadmin/platform-admins');
      const rows = (response.data || []) as Operator[];
      setOperators(rows);
      setOperatorDrafts(
        Object.fromEntries(rows.map((operator) => [operator.id, { ...operator.permissions }])),
      );
      setOperatorState('ready');
      setOperatorError('');
    } catch (error) {
      setOperatorState(isForbidden(error) ? 'forbidden' : 'error');
      setOperatorError(errorMessage(error));
    }
  }, []);

  const loadAudit = useCallback(async () => {
    setAuditState('loading');
    try {
      const response = await api.get('/superadmin/audit', { params: { limit: 20, offset: 0 } });
      setAudit((response.data || []) as AuditRow[]);
      setAuditState('ready');
      setAuditError('');
    } catch (error) {
      setAuditState(isForbidden(error) ? 'forbidden' : 'error');
      setAuditError(errorMessage(error));
    }
  }, []);

  useEffect(() => {
    void loadPasskey();
    void loadClients();
    void loadOperators();
    void loadAudit();
  }, [loadAudit, loadClients, loadOperators, loadPasskey]);

  useEffect(() => {
    if (selectedClientId !== null) void loadDevices(selectedClientId);
  }, [loadDevices, selectedClientId]);

  const ensureStepUp = useCallback(async () => {
    const status = await fetchPlatformPasskeyStatus();
    if (!status.step_up_valid) {
      await establishPlatformStepUp(status.enrolled);
    }
    await loadPasskey();
  }, [loadPasskey]);

  const handleStepUp = async () => {
    setStepUpBusy(true);
    setPasskeyError('');
    try {
      const status = passkey || (await fetchPlatformPasskeyStatus());
      await establishPlatformStepUp(status.enrolled);
      await loadPasskey();
    } catch (error) {
      setPasskeyError(errorMessage(error));
    } finally {
      setStepUpBusy(false);
    }
  };

  const revokeDevice = async (deviceId: string) => {
    if (selectedClientId === null) return;
    setDeviceBusy(deviceId);
    setDeviceError('');
    try {
      await ensureStepUp();
      await api.post(`/superadmin/platform-admins/clients/${selectedClientId}/devices/${encodeURIComponent(deviceId)}/revoke`);
      await loadDevices(selectedClientId);
      await loadAudit();
    } catch (error) {
      setDeviceError(errorMessage(error));
    } finally {
      setDeviceBusy(null);
    }
  };

  const changeReleaseChannel = async (channel: 'stable' | 'beta') => {
    if (selectedClientId === null) return;
    setReleaseBusy(true);
    setDeviceError('');
    try {
      await ensureStepUp();
      await api.patch(`/superadmin/clients/${selectedClientId}/release-channel`, null, {
        params: { channel },
      });
      await loadDevices(selectedClientId);
      await loadAudit();
    } catch (error) {
      setDeviceError(errorMessage(error));
    } finally {
      setReleaseBusy(false);
    }
  };

  const createOperator = async () => {
    const userId = Number(candidateUserId);
    if (!Number.isInteger(userId) || userId <= 0) {
      setOperatorError('ID utilisateur plateforme invalide.');
      return;
    }
    setOperatorBusy('create');
    setOperatorError('');
    try {
      await ensureStepUp();
      await api.post(`/superadmin/platform-admins/${userId}`, { permissions: candidatePermissions });
      setCandidateUserId('');
      setCandidatePermissions({});
      await loadOperators();
      await loadAudit();
    } catch (error) {
      setOperatorError(errorMessage(error));
    } finally {
      setOperatorBusy(null);
    }
  };

  const saveOperatorPermissions = async (operator: Operator) => {
    setOperatorBusy(operator.id);
    setOperatorError('');
    try {
      await ensureStepUp();
      await api.patch(`/superadmin/platform-admins/${operator.id}/permissions`, {
        permissions: operatorDrafts[operator.id] || {},
      });
      await loadOperators();
      await loadAudit();
    } catch (error) {
      setOperatorError(errorMessage(error));
    } finally {
      setOperatorBusy(null);
    }
  };

  const toggleOperator = async (operator: Operator) => {
    setOperatorBusy(operator.id);
    setOperatorError('');
    try {
      await ensureStepUp();
      await api.patch(`/superadmin/platform-admins/${operator.id}/enabled`, {
        enabled: !operator.is_active,
      });
      await loadOperators();
      await loadAudit();
    } catch (error) {
      setOperatorError(errorMessage(error));
    } finally {
      setOperatorBusy(null);
    }
  };

  const selectedClient = useMemo(
    () => clients.find((client) => client.id === selectedClientId) || null,
    [clients, selectedClientId],
  );

  return (
    <div className="space-y-5" data-testid="superadmin-control-center">
      <Card title="Vérification plateforme" icon={<KeyRound size={20} />} testId="superadmin-passkey-panel">
        {passkeyState === 'forbidden' ? <PermissionDenied /> : null}
        {passkeyState === 'error' ? <PanelError message={passkeyError} /> : null}
        {passkeyState === 'ready' && passkey ? (
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
                <BadgeCheck size={18} className={passkey.step_up_valid ? 'text-emerald-600' : 'text-slate-400'} />
                {passkey.step_up_valid ? 'Step-up actif' : passkey.enrolled ? 'Passkey enregistrée' : 'Passkey à enregistrer'}
              </div>
              <p className="mt-1 text-xs font-medium text-slate-500">
                Les mutations exigent une vérification WebAuthn récente, liée à votre propre session.
              </p>
            </div>
            <button
              type="button"
              onClick={handleStepUp}
              disabled={stepUpBusy || !passkey.origin_ready}
              className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {stepUpBusy ? 'Vérification…' : passkey.step_up_valid ? 'Renouveler le step-up' : passkey.enrolled ? 'Vérifier la passkey' : 'Enregistrer la passkey'}
            </button>
          </div>
        ) : null}
        {passkeyError && passkeyState === 'ready' ? <div className="mt-3"><PanelError message={passkeyError} /></div> : null}
      </Card>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card title="Devices & canal de diffusion" icon={<Laptop size={20} />} testId="superadmin-devices-panel">
          {clientState === 'forbidden' ? <PermissionDenied /> : null}
          {clientState === 'error' ? <PanelError message={clientError} /> : null}
          {clientState === 'ready' ? (
            <div className="space-y-4">
              <label className="block text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
                Client
                <select
                  value={selectedClientId ?? ''}
                  onChange={(event) => setSelectedClientId(Number(event.target.value))}
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-800"
                >
                  {clients.length === 0 ? <option value="">Aucun client</option> : null}
                  {clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.nom_complet || client.email} · #{client.id}
                    </option>
                  ))}
                </select>
              </label>

              {deviceState === 'forbidden' ? <PermissionDenied /> : null}
              {deviceState === 'error' ? <PanelError message={deviceError} /> : null}
              {deviceState === 'ready' && devicePayload ? (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-2xl bg-slate-50 p-4">
                      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Devices actifs</p>
                      <p className="mt-1 text-2xl font-black text-slate-900">
                        {devicePayload.license.active_devices}/{devicePayload.license.max_devices ?? '—'}
                      </p>
                    </div>
                    <div className="rounded-2xl bg-slate-50 p-4">
                      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Canal</p>
                      <p className="mt-1 text-lg font-black capitalize text-slate-900">
                        {devicePayload.license.release_channel || '—'}
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-2" data-testid="superadmin-release-channel">
                    {(['stable', 'beta'] as const).map((channel) => (
                      <button
                        type="button"
                        key={channel}
                        disabled={releaseBusy || devicePayload.license.release_channel === channel}
                        onClick={() => changeReleaseChannel(channel)}
                        className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm font-bold capitalize text-slate-700 disabled:bg-slate-100 disabled:text-slate-400"
                      >
                        {channel}
                      </button>
                    ))}
                  </div>

                  <div className="space-y-2">
                    {devicePayload.devices.length === 0 ? (
                      <p className="rounded-xl bg-slate-50 px-3 py-3 text-sm font-medium text-slate-500">Aucun device appairé.</p>
                    ) : devicePayload.devices.map((device) => (
                      <div key={device.device_id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 px-3 py-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-bold text-slate-900">{device.device_id}</p>
                          <p className="text-xs font-medium text-slate-500">{device.active ? 'Actif' : 'Révoqué'} · user #{device.user_id}</p>
                        </div>
                        {device.active ? (
                          <button
                            type="button"
                            disabled={deviceBusy === device.device_id}
                            onClick={() => revokeDevice(device.device_id)}
                            className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-bold text-rose-700 disabled:opacity-50"
                          >
                            Révoquer
                          </button>
                        ) : null}
                      </div>
                    ))}
                  </div>
                  {deviceError ? <PanelError message={deviceError} /> : null}
                  {selectedClient ? <p className="text-xs font-medium text-slate-400">Client sélectionné : {selectedClient.email}</p> : null}
                </>
              ) : null}
            </div>
          ) : null}
        </Card>

        <Card title="Journal d’audit" icon={<Activity size={20} />} testId="superadmin-audit-panel">
          {auditState === 'forbidden' ? <PermissionDenied /> : null}
          {auditState === 'error' ? <PanelError message={auditError} /> : null}
          {auditState === 'ready' ? (
            <div className="space-y-2">
              <div className="flex justify-end">
                <button type="button" onClick={() => void loadAudit()} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-600">
                  <RefreshCw size={14} /> Actualiser
                </button>
              </div>
              {audit.length === 0 ? (
                <p className="rounded-xl bg-slate-50 px-3 py-3 text-sm font-medium text-slate-500">Aucun événement Superadmin.</p>
              ) : audit.map((row) => (
                <div key={row.id} className="rounded-xl border border-slate-200 px-3 py-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-xs font-black text-slate-900">{row.action}</p>
                    <span className="text-[11px] font-semibold text-slate-400">{row.timestamp ? new Date(row.timestamp).toLocaleString('fr-FR') : '—'}</span>
                  </div>
                  <p className="mt-1 break-words text-xs font-medium text-slate-500">
                    {row.resource_type || 'Ressource'} {row.resource_id ? `#${row.resource_id}` : ''}{row.details ? ` · ${row.details}` : ''}
                  </p>
                </div>
              ))}
            </div>
          ) : null}
        </Card>
      </div>

      <Card title="Opérateurs plateforme" icon={<UserCog size={20} />} testId="superadmin-operators-panel">
        {operatorState === 'forbidden' ? <PermissionDenied /> : null}
        {operatorState === 'error' ? <PanelError message={operatorError} /> : null}
        {operatorState === 'ready' ? (
          <div className="space-y-5">
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4">
              <div className="flex items-center gap-2 text-sm font-black text-slate-900">
                <ShieldCheck size={18} /> Ajouter un opérateur existant
              </div>
              <p className="mt-1 text-xs font-medium text-slate-500">
                Le backend n’expose pas encore de recherche de candidats : saisir l’ID d’un compte plateforme existant.
              </p>
              <input
                value={candidateUserId}
                onChange={(event) => setCandidateUserId(event.target.value)}
                inputMode="numeric"
                placeholder="ID utilisateur plateforme"
                className="mt-3 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-800 sm:max-w-xs"
              />
              <div className="mt-3">
                <PermissionChecklist value={candidatePermissions} onChange={setCandidatePermissions} />
              </div>
              <button
                type="button"
                onClick={createOperator}
                disabled={operatorBusy === 'create'}
                className="mt-3 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50"
              >
                Ajouter l’opérateur
              </button>
            </div>

            {operators.map((operator) => (
              <div key={operator.id} className="rounded-2xl border border-slate-200 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-black text-slate-900">{operator.nom_complet || operator.email}</p>
                      {operator.is_owner ? <span className="rounded-full bg-slate-900 px-2 py-0.5 text-[10px] font-black uppercase tracking-wide text-white">Owner</span> : null}
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-black uppercase tracking-wide ${operator.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                        {operator.is_active ? 'Actif' : 'Désactivé'}
                      </span>
                    </div>
                    <p className="mt-1 text-xs font-medium text-slate-500">{operator.email} · #{operator.id}</p>
                  </div>
                  {!operator.is_owner ? (
                    <button
                      type="button"
                      disabled={operatorBusy === operator.id}
                      onClick={() => toggleOperator(operator)}
                      className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700 disabled:opacity-50"
                    >
                      {operator.is_active ? 'Désactiver' : 'Réactiver'}
                    </button>
                  ) : null}
                </div>
                <div className="mt-4">
                  <PermissionChecklist
                    value={operatorDrafts[operator.id] || {}}
                    onChange={(next) => setOperatorDrafts((current) => ({ ...current, [operator.id]: next }))}
                    disabled={operator.is_owner}
                  />
                </div>
                {!operator.is_owner ? (
                  <button
                    type="button"
                    disabled={operatorBusy === operator.id}
                    onClick={() => saveOperatorPermissions(operator)}
                    className="mt-3 rounded-xl border border-slate-900 px-4 py-2 text-xs font-black text-slate-900 disabled:opacity-50"
                  >
                    Enregistrer les permissions
                  </button>
                ) : null}
              </div>
            ))}
            {operatorError ? <PanelError message={operatorError} /> : null}
          </div>
        ) : null}
      </Card>
    </div>
  );
};

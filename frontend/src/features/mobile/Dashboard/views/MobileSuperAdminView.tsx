import { useState, useEffect, useCallback, useMemo } from 'react';
import { ArrowLeft, Shield, RefreshCw, Search, CheckCircle2, XCircle, Ban, AlertTriangle, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';
import { Skeleton } from '../components/Skeleton';
import toast from 'react-hot-toast';

interface ClientStats {
  total_patients: number;
  total_ia_panoramique: number;
  total_ia_cephalo: number;
}

interface Client {
  id: number;
  nom_complet: string;
  email: string;
  cabinet_name: string;
  is_licensed: boolean;
  license_expires_at: string | null;
  is_archived: boolean;
  is_suspended: boolean;
  subscription_plan: string | null;
  stats: ClientStats;
}

const PLAN_OPTIONS = ['GOLD', 'PREMIUM', 'ELITE'] as const;

function resolveApiBaseUrl(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return stored;
}

function getExpirationStatus(dateString: string | null) {
  if (!dateString) return { expired: true, daysLeft: 0 };
  const diffDays = Math.ceil((new Date(dateString).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  return { expired: diffDays <= 0, daysLeft: diffDays };
}

export function MobileSuperAdminView() {
  const navigate = useNavigate();
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [busyId, setBusyId] = useState<number | null>(null);

  // Les endpoints SuperAdmin partagés réutilisent le JWT mobile user/device-bound.
  // mobileFetch renouvelle ce JWT via /api/mobile/refresh-token, jamais via /auth/refresh.
  const authedFetch = useCallback(async (path: string, init?: RequestInit) => {
    const creds = await MobileStorage.getCredentials();
    if (!creds) throw new Error('Non appairé');
    const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}${path}`, {
      ...init,
      headers: {
        Authorization: `Bearer ${creds.access_token}`,
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ?? `Erreur ${res.status}`);
    }
    return res.status === 204 ? null : res.json();
  }, []);

  const fetchClients = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await authedFetch('/api/superadmin/clients');
      setClients(data ?? []);
    } catch (e: any) {
      setError(e.message ?? 'Erreur réseau');
    } finally {
      setLoading(false);
    }
  }, [authedFetch]);

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

  const runAction = async (id: number, action: () => Promise<any>, successMsg: string) => {
    setBusyId(id);
    try {
      await action();
      toast.success(successMsg);
      await fetchClients();
    } catch (e: any) {
      toast.error(e.message ?? 'Erreur');
    } finally {
      setBusyId(null);
    }
  };

  const handleSetPlan = (id: number, plan: string) =>
    runAction(id, () => authedFetch(`/api/superadmin/clients/${id}/plan?plan=${plan}`, { method: 'PATCH' }), `Pack ${plan} attribué.`);

  const handleToggleSuspend = (id: number, currentlySuspended: boolean) =>
    runAction(id, () => authedFetch(`/api/superadmin/clients/${id}/suspend`, { method: 'PATCH' }), currentlySuspended ? 'Client réactivé.' : 'Client suspendu.');

  const handleGrantLicense = (id: number, action: string, label: string) =>
    runAction(id, () => authedFetch(`/api/superadmin/clients/${id}/grant-license?action=${action}`, { method: 'POST' }), `Licence prolongée (${label}).`);

  const filteredClients = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return clients;
    return clients.filter(c => c.nom_complet?.toLowerCase().includes(q) || c.email.toLowerCase().includes(q) || c.cabinet_name?.toLowerCase().includes(q));
  }, [clients, search]);

  return (
    <div className="min-h-[100dvh] bg-background text-text-main flex flex-col font-outfit select-none" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
      {/* Header */}
      <div className="px-6 pt-14 pb-6 relative z-10">
        <div className="flex items-center gap-3 mb-8">
          <button
            onClick={() => navigate('/mobile/dashboard')}
            className="w-10 h-10 bg-card border border-glass-border rounded-[14px] shadow-elite flex items-center justify-center active:scale-90 transition-transform"
          >
            <ArrowLeft size={16} className="text-primary" />
          </button>
          <button
            onClick={fetchClients}
            disabled={loading}
            className="w-10 h-10 bg-card border border-glass-border rounded-[14px] shadow-elite flex items-center justify-center active:scale-90 transition-transform disabled:opacity-40 ml-auto"
          >
            <RefreshCw size={14} className={`text-text-muted ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-amber-400/20 rounded-[14px] flex items-center justify-center">
            <Shield size={18} className="text-amber-500" />
          </div>
          <div>
            <h1 className="text-3xl font-black tracking-tight text-primary font-outfit leading-none">SuperAdmin</h1>
            <p className="text-[10px] font-black text-text-muted uppercase tracking-widest mt-0.5">{clients.length} client{clients.length !== 1 ? 's' : ''}</p>
          </div>
        </div>

        <div className="relative">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder="Rechercher un client..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-card border border-glass-border rounded-[16px] pl-11 pr-4 py-3 text-sm font-bold outline-none focus:border-primary transition-colors"
          />
        </div>
      </div>

      {/* Content */}
      <main className="flex-1 px-6 pb-10 space-y-4">
        {error && (
          <div className="p-4 bg-rose-500/5 border border-rose-200 rounded-[16px]">
            <p className="text-xs font-black text-rose-600">{error}</p>
          </div>
        )}

        {loading && !clients.length ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <Skeleton key={i} className="h-40 w-full rounded-[20px]" />
            ))}
          </div>
        ) : filteredClients.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Shield size={32} className="text-text-muted/30" />
            <p className="text-sm font-black text-text-muted">Aucun client trouvé</p>
          </div>
        ) : (
          filteredClients.map(client => {
            const exp = getExpirationStatus(client.license_expires_at);
            const active = client.is_licensed && !exp.expired && !client.is_suspended && !client.is_archived;
            const busy = busyId === client.id;

            let badge = { style: 'bg-slate-100 text-slate-500', text: 'Inconnu', Icon: AlertTriangle };
            if (client.is_archived) badge = { style: 'bg-slate-100 text-slate-500', text: 'Archivé', Icon: AlertTriangle };
            else if (client.is_suspended) badge = { style: 'bg-orange-100 text-orange-700', text: 'Suspendu', Icon: Ban };
            else if (exp.expired) badge = { style: 'bg-rose-100 text-rose-700', text: 'Expiré', Icon: XCircle };
            else if (exp.daysLeft <= 7) badge = { style: 'bg-rose-100 text-rose-700', text: `Expire (${exp.daysLeft}j)`, Icon: XCircle };
            else if (exp.daysLeft <= 30) badge = { style: 'bg-amber-100 text-amber-700', text: `Expire (${exp.daysLeft}j)`, Icon: AlertTriangle };
            else badge = { style: 'bg-emerald-100 text-emerald-700', text: 'Actif', Icon: CheckCircle2 };

            return (
              <div key={client.id} className={`bg-card border border-glass-border rounded-[20px] p-5 shadow-elite ${client.is_archived ? 'opacity-60' : ''}`}>
                <div className="flex items-start justify-between gap-3 mb-4">
                  <div className="min-w-0">
                    <p className="text-sm font-black text-text-main truncate">{client.nom_complet || 'Sans nom'}</p>
                    <p className="text-[11px] font-bold text-text-muted truncate">{client.cabinet_name || 'Cabinet N/A'}</p>
                    <p className="text-[10px] text-text-muted/70 truncate">{client.email}</p>
                  </div>
                  <div className={`shrink-0 px-2.5 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest flex items-center gap-1 ${badge.style}`}>
                    <badge.Icon size={11} />
                    {badge.text}
                  </div>
                </div>

                <div className="flex items-center gap-2 mb-3">
                  <span className="text-[9px] font-black uppercase tracking-widest text-text-muted shrink-0">Pack</span>
                  <select
                    value={client.subscription_plan || 'GOLD'}
                    onChange={(e) => handleSetPlan(client.id, e.target.value)}
                    disabled={client.is_archived || busy}
                    className="flex-1 bg-background border border-glass-border rounded-lg px-2 py-1.5 text-[11px] font-black text-text-main outline-none focus:border-primary disabled:opacity-50"
                  >
                    {PLAN_OPTIONS.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-4 gap-1.5 mb-3">
                  {[['1m', '+1M'], ['3m', '+3M'], ['6m', '+6M'], ['1y', '+1AN']].map(([action, label]) => (
                    <button
                      key={action}
                      onClick={() => handleGrantLicense(client.id, action, label)}
                      disabled={client.is_archived || busy}
                      className="py-2 bg-primary/10 text-primary rounded-lg text-[10px] font-black transition-all disabled:opacity-50 active:scale-95 flex items-center justify-center gap-0.5"
                    >
                      {action === '1y' && <Zap size={10} />}
                      {label}
                    </button>
                  ))}
                </div>

                <button
                  onClick={() => handleToggleSuspend(client.id, client.is_suspended)}
                  disabled={busy}
                  className={`w-full py-2.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all disabled:opacity-50 flex items-center justify-center gap-1.5 ${client.is_suspended ? 'bg-orange-100 text-orange-700' : 'bg-slate-100 text-slate-600'}`}
                >
                  <Ban size={12} />
                  {client.is_suspended ? 'Réactiver' : 'Suspendre'}
                </button>
              </div>
            );
          })
        )}
      </main>
    </div>
  );
}

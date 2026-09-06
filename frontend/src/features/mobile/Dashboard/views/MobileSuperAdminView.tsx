import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from 'react';
import {
  AlertTriangle,
  Archive,
  ArrowLeft,
  Ban,
  Boxes,
  CheckCircle2,
  ChevronRight,
  ClipboardCopy,
  Clock3,
  FileClock,
  FilePlus2,
  Fingerprint,
  History,
  Mail,
  PackageCheck,
  Plus,
  ReceiptText,
  RefreshCw,
  Search,
  Send,
  Shield,
  ShoppingCart,
  Store,
  Truck,
  UserCheck,
  Users,
  X,
  XCircle,
  Zap,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  useMobileSuperAdmin,
  type GlobalProduct,
  type GlobalSupplier,
  type MobileSuperAdminPreviewData,
  type OperationalOrder,
  type ProductCreateInput,
  type SuperAdminClient,
  type SuperAdminSection,
  type SupplierCreateInput,
  type TrialCodeCreateInput,
} from '../../superadmin/useMobileSuperAdmin';

const SECTIONS: Array<{ key: SuperAdminSection; label: string }> = [
  { key: 'overview', label: 'Vue globale' },
  { key: 'clients', label: 'Clients' },
  { key: 'trials', label: 'Essais' },
  { key: 'marketplace', label: 'Marketplace' },
  { key: 'operations', label: 'Opérations' },
];

const PLAN_OPTIONS = ['GOLD', 'PREMIUM', 'ELITE'] as const;

type ConfirmState = {
  title: string;
  body: string;
  confirmLabel: string;
  danger?: boolean;
  action: () => Promise<unknown>;
} | null;

interface Props {
  previewData?: MobileSuperAdminPreviewData;
}

function formatMoney(value: unknown): string {
  const amount = typeof value === 'number' ? value : Number(value ?? 0);
  return new Intl.NumberFormat('fr-MA', { maximumFractionDigits: 2 }).format(Number.isFinite(amount) ? amount : 0) + ' MAD';
}

function formatDate(value: unknown): string {
  if (!value || typeof value !== 'string') return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
}

function expiration(client: SuperAdminClient) {
  if (!client.license_expires_at) return { days: 0, label: 'Sans licence', tone: 'rose' };
  const days = Math.ceil((new Date(client.license_expires_at).getTime() - Date.now()) / 86_400_000);
  if (client.is_archived) return { days, label: 'Archivé', tone: 'slate' };
  if (client.is_suspended) return { days, label: 'Suspendu', tone: 'orange' };
  if (!client.is_licensed || days <= 0) return { days, label: 'Expiré', tone: 'rose' };
  if (days <= 30) return { days, label: `${days} j`, tone: 'amber' };
  return { days, label: 'Actif', tone: 'emerald' };
}

function toneClass(tone: string) {
  if (tone === 'emerald') return 'bg-emerald-100 text-emerald-700';
  if (tone === 'amber') return 'bg-amber-100 text-amber-800';
  if (tone === 'orange') return 'bg-orange-100 text-orange-700';
  if (tone === 'rose') return 'bg-rose-100 text-rose-700';
  return 'bg-slate-100 text-slate-600';
}

function Metric({ label, value, icon }: { label: string; value: ReactNode; icon?: ReactNode }) {
  return (
    <div className="rounded-[18px] border border-glass-border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[9px] font-black uppercase tracking-[0.14em] text-text-muted">{label}</p>
        {icon && <span className="text-primary">{icon}</span>}
      </div>
      <div className="mt-2 text-xl font-black tracking-tight text-text-main">{value}</div>
    </div>
  );
}

function SectionTitle({ eyebrow, title, action }: { eyebrow: string; title: string; action?: ReactNode }) {
  return (
    <div className="flex items-end justify-between gap-3">
      <div>
        <p className="text-[9px] font-black uppercase tracking-[0.18em] text-primary">{eyebrow}</p>
        <h2 className="mt-1 text-xl font-black tracking-tight text-text-main">{title}</h2>
      </div>
      {action}
    </div>
  );
}

function Sheet({ title, subtitle, onClose, children }: { title: string; subtitle?: string; onClose: () => void; children: ReactNode }) {
  return (
    <div className="fixed inset-0 z-[80] bg-slate-950/40 backdrop-blur-sm" role="dialog" aria-modal="true" aria-label={title}>
      <div className="absolute inset-x-0 bottom-0 top-5 flex flex-col rounded-t-[30px] bg-background shadow-2xl sm:left-1/2 sm:max-w-xl sm:-translate-x-1/2">
        <div className="flex items-center gap-3 border-b border-glass-border px-5 py-4">
          <div className="min-w-0 flex-1">
            <h2 className="truncate text-lg font-black text-text-main">{title}</h2>
            {subtitle && <p className="truncate text-[10px] font-bold text-text-muted">{subtitle}</p>}
          </div>
          <button type="button" onClick={onClose} className="flex h-11 w-11 items-center justify-center rounded-[14px] border border-glass-border bg-card" aria-label="Fermer">
            <X size={18} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 pb-10 pt-5">{children}</div>
      </div>
    </div>
  );
}

function ConfirmDialog({ state, busy, onCancel, onConfirm }: { state: NonNullable<ConfirmState>; busy: boolean; onCancel: () => void; onConfirm: () => void }) {
  return (
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-slate-950/50 p-4 sm:items-center" role="alertdialog" aria-modal="true" aria-label={state.title}>
      <div className="w-full max-w-md rounded-[26px] border border-glass-border bg-card p-6 shadow-2xl">
        <div className={`flex h-12 w-12 items-center justify-center rounded-[16px] ${state.danger ? 'bg-rose-100 text-rose-700' : 'bg-primary/10 text-primary'}`}>
          {state.danger ? <AlertTriangle size={22} /> : <Shield size={22} />}
        </div>
        <h3 className="mt-4 text-lg font-black text-text-main">{state.title}</h3>
        <p className="mt-2 text-sm font-semibold leading-relaxed text-text-muted">{state.body}</p>
        <div className="mt-6 grid grid-cols-2 gap-3">
          <button type="button" onClick={onCancel} disabled={busy} className="min-h-12 rounded-[16px] border border-glass-border bg-background text-sm font-black text-text-main disabled:opacity-50">Annuler</button>
          <button type="button" onClick={onConfirm} disabled={busy} className={`min-h-12 rounded-[16px] text-sm font-black text-white disabled:opacity-50 ${state.danger ? 'bg-rose-600' : 'bg-primary'}`}>
            {busy ? 'Traitement…' : state.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export function MobileSuperAdminView({ previewData }: Props) {
  const navigate = useNavigate();
  const superadmin = useMobileSuperAdmin(previewData);
  const [section, setSection] = useState<SuperAdminSection>('overview');
  const [search, setSearch] = useState('');
  const [clientFilter, setClientFilter] = useState<'ALL' | 'ACTIVE' | 'RENEW' | 'SUSPENDED' | 'ARCHIVED'>('ALL');
  const [selectedClient, setSelectedClient] = useState<SuperAdminClient | null>(null);
  const [selectedSupplier, setSelectedSupplier] = useState<GlobalSupplier | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<GlobalProduct | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<OperationalOrder | null>(null);
  const [marketTab, setMarketTab] = useState<'suppliers' | 'products' | 'incidents' | 'audit'>('suppliers');
  const [confirm, setConfirm] = useState<ConfirmState>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [trialFormOpen, setTrialFormOpen] = useState(false);
  const [supplierCreateOpen, setSupplierCreateOpen] = useState(false);
  const [productCreateOpen, setProductCreateOpen] = useState(false);

  useEffect(() => {
    if (section === 'overview' || section === 'marketplace') void superadmin.loadMarketplace(false);
    if (section === 'operations') void superadmin.loadOperations();
  }, [section]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!selectedClient) return;
    const fresh = superadmin.clients.find(item => item.id === selectedClient.id);
    if (fresh) setSelectedClient(fresh);
  }, [superadmin.clients]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!selectedOrder) return;
    const fresh = superadmin.operationalOrders.find(item => item.id === selectedOrder.id);
    if (fresh) setSelectedOrder(fresh);
  }, [superadmin.operationalOrders]); // eslint-disable-line react-hooks/exhaustive-deps

  const filteredClients = useMemo(() => {
    const q = search.trim().toLowerCase();
    return superadmin.clients.filter(client => {
      if (q && ![client.nom_complet, client.email, client.cabinet_name].some(value => String(value || '').toLowerCase().includes(q))) return false;
      const exp = expiration(client);
      if (clientFilter === 'ACTIVE') return exp.tone === 'emerald';
      if (clientFilter === 'RENEW') return exp.tone === 'amber' || exp.tone === 'rose';
      if (clientFilter === 'SUSPENDED') return client.is_suspended;
      if (clientFilter === 'ARCHIVED') return client.is_archived;
      return true;
    });
  }, [clientFilter, search, superadmin.clients]);

  const criticalClients = superadmin.clients.filter(client => {
    const exp = expiration(client);
    return exp.tone === 'amber' || exp.tone === 'rose' || client.is_suspended;
  }).length;

  const requestConfirm = (state: NonNullable<ConfirmState>) => setConfirm(state);
  const executeConfirm = async () => {
    if (!confirm) return;
    setConfirmBusy(true);
    try { await confirm.action(); } finally { setConfirmBusy(false); setConfirm(null); }
  };

  const refresh = () => {
    if (section === 'marketplace' || section === 'overview') void Promise.all([superadmin.loadCore(), superadmin.loadMarketplace(false)]);
    else if (section === 'operations') void superadmin.loadOperations();
    else void superadmin.loadCore();
  };

  return (
    <div data-mobile-superadmin data-superadmin-section={section} className="min-h-[100dvh] bg-background text-text-main font-outfit" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
      <header className="sticky top-0 z-30 border-b border-glass-border bg-background/95 px-5 pb-3 pt-[max(14px,env(safe-area-inset-top))] backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <button type="button" onClick={() => navigate('/mobile/dashboard')} className="flex h-11 w-11 items-center justify-center rounded-[15px] border border-glass-border bg-card shadow-sm" aria-label="Retour au dashboard">
            <ArrowLeft size={17} className="text-primary" />
          </button>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <Shield size={16} className="text-amber-500" />
              <h1 className="text-xl font-black tracking-tight text-primary">SuperAdmin</h1>
            </div>
            <p className="text-[9px] font-black uppercase tracking-[0.16em] text-text-muted">Console Digital Crown</p>
          </div>
          <button type="button" onClick={refresh} className="flex h-11 w-11 items-center justify-center rounded-[15px] border border-glass-border bg-card shadow-sm" aria-label="Actualiser">
            <RefreshCw size={16} className={superadmin.loadingCore || superadmin.loadingMarketplace || superadmin.loadingOperations ? 'animate-spin text-primary' : 'text-text-muted'} />
          </button>
        </div>
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none]">
          {SECTIONS.map(item => (
            <button key={item.key} type="button" onClick={() => setSection(item.key)} className={`min-h-10 shrink-0 rounded-full px-4 text-[10px] font-black uppercase tracking-[0.08em] transition ${section === item.key ? 'bg-primary text-white shadow-sm' : 'border border-glass-border bg-card text-text-muted'}`}>
              {item.label}
            </button>
          ))}
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-5 px-5 pb-12 pt-5">
        {previewData && <div className="rounded-[16px] border border-primary/15 bg-primary/5 px-4 py-3"><p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">MODE DÉMO — SUPERADMIN</p><p className="mt-1 text-[10px] font-bold text-text-muted">Données fictives • aucune requête réelle</p></div>}
        {superadmin.error && <div role="alert" className="rounded-[16px] border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-bold text-rose-700">{superadmin.error}</div>}
        {superadmin.lastMessage && <div role="status" className="rounded-[16px] border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs font-bold text-emerald-700">{superadmin.lastMessage}</div>}

        {section === 'overview' && (
          <OverviewSection
            totalClients={superadmin.clients.length}
            criticalClients={criticalClients}
            suspended={superadmin.clients.filter(item => item.is_suspended).length}
            archived={superadmin.clients.filter(item => item.is_archived).length}
            overview={superadmin.overview}
            incidentsCount={superadmin.incidents.length}
            marketplaceLocked={superadmin.marketplaceLocked}
            loading={superadmin.loadingMarketplace}
            onUnlock={() => void superadmin.marketplaceActions.unlock()}
            onClients={() => setSection('clients')}
            onMarketplace={() => setSection('marketplace')}
            onOperations={() => setSection('operations')}
          />
        )}

        {section === 'clients' && (
          <ClientsSection
            clients={filteredClients}
            search={search}
            setSearch={setSearch}
            filter={clientFilter}
            setFilter={setClientFilter}
            onOpen={setSelectedClient}
          />
        )}

        {section === 'trials' && (
          <TrialsSection
            codes={superadmin.trialCodes}
            onNew={() => setTrialFormOpen(true)}
            onCopy={async url => {
              try { await navigator.clipboard.writeText(url); superadmin.setLastMessage('Lien d’activation copié.'); }
              catch { superadmin.setError('Impossible de copier le lien.'); }
            }}
            onRevoke={code => requestConfirm({ title: 'Révoquer ce code ?', body: `${code.code} ne pourra plus être utilisé pour activer un essai.`, confirmLabel: 'Révoquer', danger: true, action: () => superadmin.coreActions.revokeTrial(code.id) })}
          />
        )}

        {section === 'marketplace' && (
          <MarketplaceSection
            locked={superadmin.marketplaceLocked}
            loading={superadmin.loadingMarketplace}
            tab={marketTab}
            setTab={setMarketTab}
            suppliers={superadmin.suppliers}
            products={superadmin.products}
            incidents={superadmin.incidents}
            audit={superadmin.audit}
            onUnlock={() => void superadmin.marketplaceActions.unlock()}
            onSupplier={setSelectedSupplier}
            onProduct={setSelectedProduct}
            onNewSupplier={() => setSupplierCreateOpen(true)}
            onNewProduct={() => setProductCreateOpen(true)}
            onSync={(supplier, force) => requestConfirm({ title: force ? 'Forcer la synchronisation ?' : 'Synchroniser le fournisseur ?', body: `${supplier.name} sera synchronisé via le moteur canonique serveur.${force ? ' Le backoff normal sera contourné.' : ''}`, confirmLabel: force ? 'Forcer' : 'Synchroniser', danger: force, action: () => superadmin.marketplaceActions.syncSupplier(supplier.id, force) })}
          />
        )}

        {section === 'operations' && (
          <OperationsSection
            orders={superadmin.operationalOrders}
            globalOrders={superadmin.globalOrders}
            finance={superadmin.financeSummary}
            globalLocked={superadmin.marketplaceLocked}
            loading={superadmin.loadingOperations}
            onUnlockGlobal={() => void superadmin.marketplaceActions.unlock()}
            onOpen={setSelectedOrder}
          />
        )}
      </main>

      {selectedClient && (
        <ClientDetailSheet
          client={selectedClient}
          onClose={() => setSelectedClient(null)}
          actions={superadmin.coreActions}
          onMessage={superadmin.setLastMessage}
          onError={superadmin.setError}
          confirm={requestConfirm}
        />
      )}

      {trialFormOpen && <TrialCreateSheet onClose={() => setTrialFormOpen(false)} onSubmit={superadmin.coreActions.createTrial} />}

      {selectedSupplier && (
        <SupplierDetailSheet
          supplier={selectedSupplier}
          onClose={() => setSelectedSupplier(null)}
          getGovernance={superadmin.marketplaceActions.getGovernance}
          onUpdate={payload => superadmin.marketplaceActions.updateSupplier(selectedSupplier.id, payload)}
          onGovernance={payload => superadmin.marketplaceActions.updateGovernance(selectedSupplier.id, payload)}
          confirm={requestConfirm}
        />
      )}

      {supplierCreateOpen && <SupplierCreateSheet onClose={() => setSupplierCreateOpen(false)} onSubmit={superadmin.marketplaceActions.createSupplier} />}

      {selectedProduct && (
        <ProductSheet
          product={selectedProduct}
          suppliers={superadmin.suppliers}
          onClose={() => setSelectedProduct(null)}
          onSubmit={payload => superadmin.marketplaceActions.updateProduct(selectedProduct.id, payload)}
        />
      )}

      {productCreateOpen && <ProductCreateSheet suppliers={superadmin.suppliers} onClose={() => setProductCreateOpen(false)} onSubmit={superadmin.marketplaceActions.createProduct} />}

      {selectedOrder && (
        <OperationSheet
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
          loadDetail={superadmin.operationActions.loadDetail}
          updateOrder={superadmin.operationActions.updateOrder}
          dispatch={superadmin.operationActions.dispatch}
          acknowledgeProcurement={superadmin.operationActions.acknowledgeProcurement}
          recordInvoice={superadmin.operationActions.recordInvoice}
          receive={superadmin.operationActions.receive}
          confirm={requestConfirm}
        />
      )}

      {confirm && <ConfirmDialog state={confirm} busy={confirmBusy} onCancel={() => setConfirm(null)} onConfirm={() => void executeConfirm()} />}
    </div>
  );
}

function OverviewSection(props: {
  totalClients: number; criticalClients: number; suspended: number; archived: number;
  overview: ReturnType<typeof useMobileSuperAdmin>['overview']; incidentsCount: number;
  marketplaceLocked: boolean; loading: boolean; onUnlock: () => void;
  onClients: () => void; onMarketplace: () => void; onOperations: () => void;
}) {
  return (
    <div className="space-y-5" data-superadmin-overview>
      <SectionTitle eyebrow="Pilotage" title="Vue globale" />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric label="Clients" value={props.totalClients} icon={<Users size={15} />} />
        <Metric label="À surveiller" value={props.criticalClients} icon={<AlertTriangle size={15} />} />
        <Metric label="Suspendus" value={props.suspended} icon={<Ban size={15} />} />
        <Metric label="Archivés" value={props.archived} icon={<Archive size={15} />} />
      </div>
      <button type="button" onClick={props.onClients} className="flex min-h-14 w-full items-center justify-between rounded-[18px] border border-glass-border bg-card px-4 text-left shadow-sm">
        <span><span className="block text-sm font-black">Clients & licences</span><span className="text-[10px] font-bold text-text-muted">Licences, notes, historique, relances</span></span><ChevronRight size={18} className="text-primary" />
      </button>

      <section className="rounded-[22px] border border-glass-border bg-card p-4 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <div><p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Marketplace global</p><h3 className="mt-1 text-base font-black">Control-plane</h3></div>
          <Store size={20} className="text-primary" />
        </div>
        {props.marketplaceLocked ? (
          <div className="mt-4 rounded-[18px] border border-amber-200 bg-amber-50 p-4">
            <div className="flex items-start gap-3"><Fingerprint size={20} className="mt-0.5 text-amber-700" /><div><p className="text-sm font-black text-amber-900">Vérification biométrique requise</p><p className="mt-1 text-xs font-semibold leading-relaxed text-amber-800">Le JWT mobile ordinaire reste refusé. Une session WebAuthn UV courte ouvre le control-plane.</p></div></div>
            <button type="button" disabled={props.loading} onClick={props.onUnlock} className="mt-4 min-h-12 w-full rounded-[15px] bg-amber-600 text-xs font-black text-white disabled:opacity-50">{props.loading ? 'Vérification…' : 'Vérifier et ouvrir'}</button>
          </div>
        ) : props.overview ? (
          <>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="Commandes" value={props.overview.ordersCount} />
              <Metric label="Fournisseurs" value={`${props.overview.activeSuppliersCount}/${props.overview.suppliersCount}`} />
              <Metric label="Incidents sync" value={props.incidentsCount} />
              <Metric label="Revenu reconnu" value={formatMoney(props.overview.recognizedRevenueAmount)} />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <button type="button" onClick={props.onMarketplace} className="min-h-12 rounded-[15px] border border-glass-border bg-background text-xs font-black text-primary">Gouvernance</button>
              <button type="button" onClick={props.onOperations} className="min-h-12 rounded-[15px] bg-primary text-xs font-black text-white">Opérations</button>
            </div>
          </>
        ) : <p className="mt-4 text-xs font-bold text-text-muted">Aucune donnée Marketplace chargée.</p>}
      </section>
    </div>
  );
}

function ClientsSection(props: {
  clients: SuperAdminClient[]; search: string; setSearch: (value: string) => void;
  filter: 'ALL' | 'ACTIVE' | 'RENEW' | 'SUSPENDED' | 'ARCHIVED'; setFilter: (value: 'ALL' | 'ACTIVE' | 'RENEW' | 'SUSPENDED' | 'ARCHIVED') => void;
  onOpen: (client: SuperAdminClient) => void;
}) {
  const filters = [['ALL', 'Tous'], ['ACTIVE', 'Actifs'], ['RENEW', 'Renouveler'], ['SUSPENDED', 'Suspendus'], ['ARCHIVED', 'Archivés']] as const;
  return (
    <div className="space-y-4" data-superadmin-clients>
      <SectionTitle eyebrow="Parc" title="Clients & licences" />
      <div className="relative"><Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" /><input value={props.search} onChange={event => props.setSearch(event.target.value)} placeholder="Nom, cabinet ou email" className="min-h-12 w-full rounded-[16px] border border-glass-border bg-card pl-11 pr-4 text-sm font-bold outline-none focus:border-primary" /></div>
      <div className="flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none]">{filters.map(([key, label]) => <button key={key} type="button" onClick={() => props.setFilter(key)} className={`min-h-9 shrink-0 rounded-full px-3 text-[9px] font-black uppercase tracking-wider ${props.filter === key ? 'bg-primary text-white' : 'border border-glass-border bg-card text-text-muted'}`}>{label}</button>)}</div>
      <div className="space-y-3">
        {props.clients.map(client => {
          const exp = expiration(client);
          return <button key={client.id} type="button" onClick={() => props.onOpen(client)} className="flex min-h-[88px] w-full items-center gap-3 rounded-[20px] border border-glass-border bg-card p-4 text-left shadow-sm">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[14px] bg-primary/10 text-primary"><Users size={18} /></div>
            <div className="min-w-0 flex-1"><p className="truncate text-sm font-black">{client.cabinet_name || 'Cabinet sans nom'}</p><p className="truncate text-[11px] font-bold text-text-muted">{client.nom_complet || 'Sans nom'} · {client.subscription_plan || '—'}</p><p className="mt-1 truncate text-[9px] font-semibold text-text-muted">{client.email}</p></div>
            <div className="flex shrink-0 flex-col items-end gap-2"><span className={`rounded-full px-2.5 py-1 text-[8px] font-black uppercase tracking-wider ${toneClass(exp.tone)}`}>{exp.label}</span><ChevronRight size={15} className="text-text-muted" /></div>
          </button>;
        })}
        {!props.clients.length && <div className="py-16 text-center text-sm font-bold text-text-muted">Aucun client trouvé.</div>}
      </div>
    </div>
  );
}

function ClientDetailSheet(props: {
  client: SuperAdminClient; onClose: () => void;
  actions: ReturnType<typeof useMobileSuperAdmin>['coreActions']; onMessage: (message: string | null) => void; onError: (message: string | null) => void;
  confirm: (state: NonNullable<ConfirmState>) => void;
}) {
  const [notes, setNotes] = useState(props.client.internal_notes ?? '');
  const [historyRows, setHistoryRows] = useState<Array<Record<string, unknown>> | null>(null);
  const exp = expiration(props.client);
  const confirm = props.confirm;
  const clientName = props.client.cabinet_name || props.client.nom_complet || props.client.email;

  return <Sheet title={clientName} subtitle={props.client.email} onClose={props.onClose}>
    <div className="space-y-5" data-superadmin-client-detail>
      <div className="grid grid-cols-2 gap-3"><Metric label="Statut" value={<span className={`inline-flex rounded-full px-2 py-1 text-xs ${toneClass(exp.tone)}`}>{exp.label}</span>} /><Metric label="Expiration" value={formatDate(props.client.license_expires_at)} /></div>
      <section className="rounded-[20px] border border-glass-border bg-card p-4">
        <p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Licence & abonnement</p>
        {!props.client.is_active && <button type="button" onClick={() => confirm({ title: 'Valider ce client ?', body: `${clientName} sera activé avec un essai de 30 jours selon le contrat serveur.`, confirmLabel: 'Valider', action: () => props.actions.validateClient(props.client.id) })} className="mt-4 min-h-12 w-full rounded-[15px] bg-emerald-600 text-xs font-black text-white"><UserCheck size={15} className="mr-2 inline" />Valider + essai 30 j</button>}
        <label className="mt-4 block text-[10px] font-black text-text-muted">Pack</label>
        <select value={props.client.subscription_plan || 'GOLD'} onChange={event => { const plan = event.target.value; confirm({ title: `Passer en ${plan} ?`, body: `Le pack de ${clientName} sera modifié côté serveur.`, confirmLabel: 'Changer le pack', action: () => props.actions.setPlan(props.client.id, plan) }); }} className="mt-2 min-h-12 w-full rounded-[15px] border border-glass-border bg-background px-3 text-sm font-black">
          {PLAN_OPTIONS.map(plan => <option key={plan}>{plan}</option>)}
        </select>
        <div className="mt-4 grid grid-cols-4 gap-2">{[['1m', '+1M'], ['3m', '+3M'], ['6m', '+6M'], ['1y', '+1AN']].map(([action, label]) => <button key={action} type="button" onClick={() => confirm({ title: `Prolonger ${label} ?`, body: `La licence de ${clientName} sera prolongée par le serveur.`, confirmLabel: label, action: () => props.actions.grantLicense(props.client.id, action) })} className="min-h-11 rounded-[13px] bg-primary/10 text-[10px] font-black text-primary">{label}</button>)}</div>
      </section>

      <section className="rounded-[20px] border border-glass-border bg-card p-4">
        <p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">CRM interne</p>
        <textarea value={notes} onChange={event => setNotes(event.target.value)} rows={4} placeholder="Notes internes" className="mt-3 w-full rounded-[15px] border border-glass-border bg-background p-3 text-sm font-semibold outline-none focus:border-primary" />
        <button type="button" onClick={() => void props.actions.saveNotes(props.client.id, notes)} className="mt-3 min-h-11 w-full rounded-[14px] bg-primary text-xs font-black text-white">Enregistrer les notes</button>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <button type="button" onClick={() => void props.actions.getHistory(props.client.id).then(setHistoryRows).catch(error => props.onError(error instanceof Error ? error.message : 'Historique indisponible.'))} className="min-h-11 rounded-[14px] border border-glass-border bg-background text-[10px] font-black"><History size={14} className="mr-1 inline" />Historique</button>
          <button type="button" onClick={() => confirm({ title: 'Envoyer une relance ?', body: 'Le backend utilisera le canal canonique disponible, actuellement WhatsApp si un téléphone est renseigné.', confirmLabel: 'Envoyer', action: () => props.actions.sendRenewal(props.client.id, 'Votre licence Digital Crown expire bientôt.') })} className="min-h-11 rounded-[14px] border border-glass-border bg-background text-[10px] font-black"><Mail size={14} className="mr-1 inline" />Relance</button>
        </div>
        {historyRows && <div className="mt-4 space-y-2 rounded-[14px] bg-background p-3">{historyRows.length ? historyRows.slice(0, 10).map((row, index) => <div key={String(row.id ?? index)} className="flex items-center justify-between gap-3 border-b border-glass-border py-2 last:border-0"><span className="text-[10px] font-black">{String(row.action ?? 'Action')}</span><span className="text-[9px] font-bold text-text-muted">{formatDate(row.timestamp ?? row.created_at)}</span></div>) : <p className="text-[10px] font-bold text-text-muted">Aucun historique.</p>}</div>}
      </section>

      <section className="rounded-[20px] border border-rose-200 bg-rose-50 p-4">
        <p className="text-[9px] font-black uppercase tracking-[0.16em] text-rose-700">Zone sensible</p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <button type="button" onClick={() => confirm({ title: props.client.is_suspended ? 'Réactiver ce client ?' : 'Suspendre ce client ?', body: `${clientName} : le statut d’accès sera modifié immédiatement côté serveur.`, confirmLabel: props.client.is_suspended ? 'Réactiver' : 'Suspendre', danger: !props.client.is_suspended, action: () => props.actions.toggleSuspend(props.client.id) })} className="min-h-12 rounded-[14px] border border-rose-200 bg-white text-[10px] font-black text-rose-700"><Ban size={14} className="mr-1 inline" />{props.client.is_suspended ? 'Réactiver' : 'Suspendre'}</button>
          <button type="button" onClick={() => confirm({ title: props.client.is_archived ? 'Désarchiver ce client ?' : 'Archiver ce client ?', body: `${clientName} : l’état d’archivage sera basculé et journalisé.`, confirmLabel: props.client.is_archived ? 'Désarchiver' : 'Archiver', danger: !props.client.is_archived, action: () => props.actions.toggleArchive(props.client.id) })} className="min-h-12 rounded-[14px] border border-rose-200 bg-white text-[10px] font-black text-rose-700"><Archive size={14} className="mr-1 inline" />{props.client.is_archived ? 'Désarchiver' : 'Archiver'}</button>
        </div>
        <button type="button" onClick={() => confirm({ title: 'Révoquer la licence ?', body: `La licence de ${clientName} expirera immédiatement. Cette action est auditée.`, confirmLabel: 'Révoquer la licence', danger: true, action: () => props.actions.grantLicense(props.client.id, 'revoke') })} className="mt-2 min-h-12 w-full rounded-[14px] bg-rose-600 text-[10px] font-black uppercase tracking-wider text-white"><XCircle size={14} className="mr-1 inline" />Révoquer licence</button>
      </section>
    </div>
  </Sheet>;
}

function TrialsSection(props: { codes: ReturnType<typeof useMobileSuperAdmin>['trialCodes']; onNew: () => void; onCopy: (url: string) => void; onRevoke: (code: ReturnType<typeof useMobileSuperAdmin>['trialCodes'][number]) => void }) {
  return <div className="space-y-4" data-superadmin-trials>
    <SectionTitle eyebrow="Onboarding commercial" title="Codes d’essai" action={<button type="button" onClick={props.onNew} className="flex min-h-10 items-center gap-2 rounded-[14px] bg-primary px-3 text-[10px] font-black text-white"><Plus size={14} />Nouveau</button>} />
    {props.codes.map(code => {
      const state = code.consumed_at ? 'Consommé' : code.revoked_at ? 'Révoqué' : new Date(code.expires_at).getTime() < Date.now() ? 'Expiré' : 'Actif';
      return <div key={code.id} className="rounded-[20px] border border-glass-border bg-card p-4 shadow-sm">
        <div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="truncate font-mono text-xs font-black">{code.code}</p><p className="mt-1 truncate text-[10px] font-bold text-text-muted">{code.cabinet_name || code.nom_complet || code.email}</p></div><span className={`rounded-full px-2.5 py-1 text-[8px] font-black uppercase ${state === 'Actif' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>{state}</span></div>
        <div className="mt-3 flex items-center justify-between text-[9px] font-bold text-text-muted"><span>{code.trial_days} jours d’essai</span><span>expire {formatDate(code.expires_at)}</span></div>
        <div className="mt-3 grid grid-cols-2 gap-2"><button type="button" onClick={() => props.onCopy(code.activation_url)} className="min-h-11 rounded-[14px] border border-glass-border bg-background text-[10px] font-black"><ClipboardCopy size={14} className="mr-1 inline" />Copier</button><button type="button" disabled={state !== 'Actif'} onClick={() => props.onRevoke(code)} className="min-h-11 rounded-[14px] border border-rose-200 bg-rose-50 text-[10px] font-black text-rose-700 disabled:opacity-40">Révoquer</button></div>
      </div>;
    })}
  </div>;
}

function TrialCreateSheet(props: { onClose: () => void; onSubmit: (payload: TrialCodeCreateInput) => Promise<boolean> }) {
  const [form, setForm] = useState<TrialCodeCreateInput>({ email: '', nom_complet: '', cabinet_name: '', trial_days: 30, expires_in_days: 14, notes: '' });
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); try { if (await props.onSubmit(form)) props.onClose(); } finally { setBusy(false); } };
  return <Sheet title="Nouveau code d’essai" subtitle="Activation cabinet" onClose={props.onClose}><form onSubmit={submit} className="space-y-3"><Field label="Email" required value={form.email} onChange={value => setForm({ ...form, email: value })} /><Field label="Nom complet" value={form.nom_complet || ''} onChange={value => setForm({ ...form, nom_complet: value })} /><Field label="Cabinet" value={form.cabinet_name || ''} onChange={value => setForm({ ...form, cabinet_name: value })} /><div className="grid grid-cols-2 gap-3"><NumberField label="Jours d’essai" value={form.trial_days} min={1} max={90} onChange={value => setForm({ ...form, trial_days: value })} /><NumberField label="Validité code" value={form.expires_in_days} min={1} max={60} onChange={value => setForm({ ...form, expires_in_days: value })} /></div><TextArea label="Notes internes" value={form.notes || ''} onChange={value => setForm({ ...form, notes: value })} /><button disabled={busy} className="min-h-13 w-full rounded-[16px] bg-primary text-xs font-black text-white disabled:opacity-50">{busy ? 'Création…' : 'Créer le code'}</button></form></Sheet>;
}

function MarketplaceSection(props: {
  locked: boolean; loading: boolean; tab: 'suppliers' | 'products' | 'incidents' | 'audit'; setTab: (tab: 'suppliers' | 'products' | 'incidents' | 'audit') => void;
  suppliers: GlobalSupplier[]; products: GlobalProduct[]; incidents: ReturnType<typeof useMobileSuperAdmin>['incidents']; audit: ReturnType<typeof useMobileSuperAdmin>['audit'];
  onUnlock: () => void; onSupplier: (supplier: GlobalSupplier) => void; onProduct: (product: GlobalProduct) => void; onNewSupplier: () => void; onNewProduct: () => void; onSync: (supplier: GlobalSupplier, force: boolean) => void;
}) {
  if (props.locked) return <div className="space-y-4" data-superadmin-marketplace><SectionTitle eyebrow="Control-plane" title="Marketplace Admin" /><div className="rounded-[22px] border border-amber-200 bg-amber-50 p-5"><Fingerprint size={28} className="text-amber-700" /><h3 className="mt-4 text-lg font-black text-amber-950">Step-up WebAuthn requis</h3><p className="mt-2 text-sm font-semibold leading-relaxed text-amber-800">Le control-plane global refuse le JWT mobile durable. Déverrouille une session UV de 5 minutes pour continuer.</p><button type="button" onClick={props.onUnlock} disabled={props.loading} className="mt-5 min-h-13 w-full rounded-[16px] bg-amber-600 text-xs font-black text-white disabled:opacity-50">{props.loading ? 'Vérification…' : 'Vérifier biométrie'}</button></div></div>;
  const tabs = [['suppliers', 'Fournisseurs'], ['products', 'Catalogue'], ['incidents', 'Incidents'], ['audit', 'Audit']] as const;
  return <div className="space-y-4" data-superadmin-marketplace>
    <SectionTitle eyebrow="Control-plane" title="Marketplace Admin" action={props.tab === 'suppliers' ? <button onClick={props.onNewSupplier} className="flex min-h-10 items-center gap-1 rounded-[13px] bg-primary px-3 text-[9px] font-black text-white"><Plus size={13} />Fournisseur</button> : props.tab === 'products' ? <button onClick={props.onNewProduct} className="flex min-h-10 items-center gap-1 rounded-[13px] bg-primary px-3 text-[9px] font-black text-white"><Plus size={13} />Produit</button> : null} />
    <div className="grid grid-cols-4 gap-2">{tabs.map(([key, label]) => <button key={key} type="button" onClick={() => props.setTab(key)} className={`min-h-10 rounded-[12px] px-1 text-[8px] font-black uppercase tracking-wide ${props.tab === key ? 'bg-primary text-white' : 'border border-glass-border bg-card text-text-muted'}`}>{label}</button>)}</div>
    {props.tab === 'suppliers' && <div className="space-y-3">{props.suppliers.map(supplier => <div key={supplier.id} className="rounded-[19px] border border-glass-border bg-card p-4 shadow-sm"><button type="button" onClick={() => props.onSupplier(supplier)} className="flex w-full items-center gap-3 text-left"><div className="flex h-10 w-10 items-center justify-center rounded-[13px] bg-primary/10 text-primary"><Store size={17} /></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-black">{supplier.name}</p><p className="truncate text-[9px] font-bold text-text-muted">Cabinet #{supplier.employerId} · {supplier.syncMode || 'manual'}</p></div><span className={`rounded-full px-2 py-1 text-[8px] font-black ${supplier.isActive ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>{supplier.isActive ? 'ACTIF' : 'INACTIF'}</span><ChevronRight size={14} /></button><div className="mt-3 grid grid-cols-2 gap-2"><button type="button" onClick={() => props.onSync(supplier, false)} className="min-h-10 rounded-[12px] border border-glass-border bg-background text-[9px] font-black">Synchroniser</button><button type="button" onClick={() => props.onSync(supplier, true)} className="min-h-10 rounded-[12px] border border-amber-200 bg-amber-50 text-[9px] font-black text-amber-800">Force sync</button></div></div>)}</div>}
    {props.tab === 'products' && <div className="space-y-3">{props.products.map(product => <button key={String(product.id)} type="button" onClick={() => props.onProduct(product)} className="flex min-h-[82px] w-full items-center gap-3 rounded-[19px] border border-glass-border bg-card p-4 text-left shadow-sm"><div className="flex h-10 w-10 items-center justify-center rounded-[13px] bg-primary/10 text-primary"><Boxes size={17} /></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-black">{product.name}</p><p className="truncate text-[9px] font-bold text-text-muted">{product.sku} · Cabinet #{product.employerId}</p><p className="mt-1 text-[10px] font-black text-primary">{formatMoney(product.price)}</p></div><ChevronRight size={15} /></button>)}</div>}
    {props.tab === 'incidents' && <div className="space-y-3">{props.incidents.length ? props.incidents.map((incident, index) => <div key={`${incident.supplierId}-${index}`} className="rounded-[18px] border border-rose-200 bg-rose-50 p-4"><div className="flex items-center gap-2"><AlertTriangle size={16} className="text-rose-700" /><p className="text-sm font-black text-rose-900">{incident.supplierName || `Fournisseur #${incident.supplierId}`}</p></div><p className="mt-2 text-[10px] font-bold text-rose-800">{String(incident.freshness.status)} · {incident.consecutiveFailures} échec(s)</p><p className="mt-1 text-[10px] font-semibold text-rose-700">{incident.lastErrorDetail || incident.lastErrorCode || 'Incident de fraîcheur'}</p></div>) : <Empty label="Aucun incident sync global." />}</div>}
    {props.tab === 'audit' && <div className="space-y-2">{props.audit.length ? props.audit.map(event => <div key={event.id} className="rounded-[16px] border border-glass-border bg-card p-3"><div className="flex items-center justify-between gap-3"><span className="text-[10px] font-black">{event.action}</span><span className="text-[8px] font-bold text-text-muted">{formatDate(event.createdAt)}</span></div><p className="mt-1 text-[9px] font-semibold text-text-muted">{event.entityType} #{event.entityId} · Cabinet #{event.employerId}</p></div>) : <Empty label="Journal Marketplace vide." />}</div>}
  </div>;
}

function SupplierDetailSheet(props: { supplier: GlobalSupplier; onClose: () => void; getGovernance: (id: number) => Promise<Record<string, unknown>>; onUpdate: (payload: Record<string, unknown>) => Promise<boolean>; onGovernance: (payload: Record<string, unknown>) => Promise<boolean>; confirm: (state: NonNullable<ConfirmState>) => void }) {
  const [name, setName] = useState(props.supplier.name);
  const [apiBaseUrl, setApiBaseUrl] = useState(props.supplier.apiBaseUrl || '');
  const [syncMode, setSyncMode] = useState(props.supplier.syncMode || 'manual');
  const [governance, setGovernance] = useState<Record<string, unknown> | null>(null);
  const [agreementStatus, setAgreementStatus] = useState('NONE');
  const [agreementReference, setAgreementReference] = useState('');
  const [notes, setNotes] = useState('');
  useEffect(() => { void props.getGovernance(props.supplier.id).then(value => { setGovernance(value); const agreement = value.agreement as Record<string, unknown> | undefined; setAgreementStatus(String(agreement?.storedStatus ?? agreement?.status ?? 'NONE')); setAgreementReference(String(agreement?.reference ?? '')); setNotes(String(agreement?.notes ?? '')); }); }, [props.supplier.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const active = Boolean(governance?.isActive ?? props.supplier.isActive);
  return <Sheet title={props.supplier.name} subtitle={`Cabinet #${props.supplier.employerId}`} onClose={props.onClose}><div className="space-y-5">
    <section className="rounded-[20px] border border-glass-border bg-card p-4"><p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Fournisseur global</p><div className="mt-3 space-y-3"><Field label="Nom" value={name} onChange={setName} /><Field label="URL API" value={apiBaseUrl} onChange={setApiBaseUrl} /><SelectField label="Mode sync" value={syncMode} options={['manual', 'api']} onChange={setSyncMode} /><button type="button" onClick={() => void props.onUpdate({ name, apiBaseUrl, syncMode })} className="min-h-12 w-full rounded-[15px] bg-primary text-xs font-black text-white">Enregistrer fournisseur</button></div></section>
    <section className="rounded-[20px] border border-amber-200 bg-amber-50 p-4"><p className="text-[9px] font-black uppercase tracking-[0.16em] text-amber-800">Gouvernance & accord</p><div className="mt-3 space-y-3"><SelectField label="Statut accord" value={agreementStatus} options={['NONE', 'DRAFT', 'ACTIVE', 'SUSPENDED', 'TERMINATED']} onChange={setAgreementStatus} /><Field label="Référence accord" value={agreementReference} onChange={setAgreementReference} /><TextArea label="Notes accord" value={notes} onChange={setNotes} /><button type="button" onClick={() => props.confirm({ title: 'Mettre à jour la gouvernance ?', body: `Accord ${agreementStatus} pour ${props.supplier.name}. Le backend exigera confirm=true et journalisera la mutation.`, confirmLabel: 'Mettre à jour', danger: agreementStatus === 'SUSPENDED' || agreementStatus === 'TERMINATED', action: () => props.onGovernance({ agreementStatus, agreementReference, notes }) })} className="min-h-12 w-full rounded-[15px] bg-amber-600 text-xs font-black text-white">Mettre à jour l’accord</button><button type="button" onClick={() => props.confirm({ title: active ? 'Désactiver ce fournisseur ?' : 'Réactiver ce fournisseur ?', body: `${props.supplier.name} sera ${active ? 'retiré du catalogue actif' : 'réactivé'} globalement pour son cabinet.`, confirmLabel: active ? 'Désactiver' : 'Réactiver', danger: active, action: () => props.onGovernance({ isActive: !active }) })} className={`min-h-12 w-full rounded-[15px] text-xs font-black ${active ? 'bg-rose-600 text-white' : 'bg-emerald-600 text-white'}`}>{active ? 'Désactiver fournisseur' : 'Réactiver fournisseur'}</button></div></section>
  </div></Sheet>;
}

function SupplierCreateSheet(props: { onClose: () => void; onSubmit: (payload: SupplierCreateInput) => Promise<boolean> }) {
  const [form, setForm] = useState<SupplierCreateInput>({ employerId: 0, supplierKey: '', name: '', badge: '', description: '', promise: '', apiBaseUrl: '', syncMode: 'manual', isActive: true });
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); try { if (await props.onSubmit(form)) props.onClose(); } finally { setBusy(false); } };
  return <Sheet title="Nouveau fournisseur" subtitle="Création globale SuperAdmin" onClose={props.onClose}><form onSubmit={submit} className="space-y-3"><NumberField label="ID cabinet cible" value={form.employerId} min={1} onChange={value => setForm({ ...form, employerId: value })} /><Field label="Clé fournisseur" required value={form.supplierKey} onChange={value => setForm({ ...form, supplierKey: value })} /><Field label="Nom" required value={form.name} onChange={value => setForm({ ...form, name: value })} /><Field label="Badge" value={form.badge || ''} onChange={value => setForm({ ...form, badge: value })} /><TextArea label="Description" value={form.description || ''} onChange={value => setForm({ ...form, description: value })} /><Field label="URL API" value={form.apiBaseUrl || ''} onChange={value => setForm({ ...form, apiBaseUrl: value })} /><SelectField label="Mode sync" value={form.syncMode || 'manual'} options={['manual', 'api']} onChange={value => setForm({ ...form, syncMode: value })} /><button disabled={busy} className="min-h-13 w-full rounded-[16px] bg-primary text-xs font-black text-white">{busy ? 'Création…' : 'Créer avec confirmation globale'}</button></form></Sheet>;
}

function ProductSheet(props: { product: GlobalProduct; suppliers: GlobalSupplier[]; onClose: () => void; onSubmit: (payload: Record<string, unknown>) => Promise<boolean> }) {
  const [form, setForm] = useState({ supplierId: Number(props.product.supplierId), name: props.product.name, sku: props.product.sku, dentalCategory: props.product.dentalCategory || props.product.category || '', dentalSpecialty: props.product.dentalSpecialty || props.product.specialty || '', unit: props.product.unit, price: Number(props.product.price), availability: props.product.availability, shortDescription: props.product.shortDescription || props.product.description || '', longDescription: props.product.longDescription || '', isFeatured: Boolean(props.product.isFeatured), sortOrder: Number(props.product.sortOrder || 0) });
  return <Sheet title={props.product.name} subtitle={`${props.product.sku} · Cabinet #${props.product.employerId}`} onClose={props.onClose}><ProductFields form={form} setForm={setForm} suppliers={props.suppliers.filter(item => item.employerId === props.product.employerId)} /><button type="button" onClick={() => void props.onSubmit(form)} className="mt-4 min-h-13 w-full rounded-[16px] bg-primary text-xs font-black text-white">Enregistrer produit</button></Sheet>;
}

function ProductCreateSheet(props: { suppliers: GlobalSupplier[]; onClose: () => void; onSubmit: (payload: ProductCreateInput) => Promise<boolean> }) {
  const [form, setForm] = useState<ProductCreateInput>({ employerId: props.suppliers[0]?.employerId ?? 0, supplierId: props.suppliers[0]?.id ?? 0, externalProductId: '', name: '', sku: '', dentalCategory: '', dentalSpecialty: '', unit: '', price: 0, availability: 'AVAILABLE', shortDescription: '', longDescription: '', benefits: [], isFeatured: false, sortOrder: 0 });
  const [busy, setBusy] = useState(false);
  const compatible = props.suppliers.filter(item => item.employerId === form.employerId);
  const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); try { if (await props.onSubmit(form)) props.onClose(); } finally { setBusy(false); } };
  return <Sheet title="Nouveau produit" subtitle="Catalogue global SuperAdmin" onClose={props.onClose}><form onSubmit={submit}><NumberField label="ID cabinet cible" value={form.employerId} min={1} onChange={value => setForm({ ...form, employerId: value, supplierId: props.suppliers.find(item => item.employerId === value)?.id ?? 0 })} /><ProductFields form={form} setForm={setForm} suppliers={compatible} /><button disabled={busy} className="mt-4 min-h-13 w-full rounded-[16px] bg-primary text-xs font-black text-white">{busy ? 'Création…' : 'Créer avec confirmation globale'}</button></form></Sheet>;
}

function ProductFields<T extends { supplierId: number; name: string; sku: string; dentalCategory: string; dentalSpecialty: string; unit: string; price: number; availability: string; shortDescription?: string; longDescription?: string; isFeatured?: boolean; sortOrder?: number }>(props: { form: T; setForm: (value: T) => void; suppliers: GlobalSupplier[] }) {
  const f = props.form;
  return <div className="mt-3 space-y-3"><label className="block"><span className="text-[9px] font-black uppercase tracking-wider text-text-muted">Fournisseur</span><select value={f.supplierId} onChange={event => props.setForm({ ...f, supplierId: Number(event.target.value) })} className="mt-1 min-h-12 w-full rounded-[14px] border border-glass-border bg-card px-3 text-sm font-bold">{props.suppliers.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><Field label="Nom" required value={f.name} onChange={value => props.setForm({ ...f, name: value })} /><Field label="SKU" required value={f.sku} onChange={value => props.setForm({ ...f, sku: value })} /><div className="grid grid-cols-2 gap-3"><Field label="Catégorie" required value={f.dentalCategory} onChange={value => props.setForm({ ...f, dentalCategory: value })} /><Field label="Spécialité" required value={f.dentalSpecialty} onChange={value => props.setForm({ ...f, dentalSpecialty: value })} /></div><div className="grid grid-cols-2 gap-3"><Field label="Unité" required value={f.unit} onChange={value => props.setForm({ ...f, unit: value })} /><NumberField label="Prix MAD" value={f.price} min={0} step="0.01" onChange={value => props.setForm({ ...f, price: value })} /></div><SelectField label="Disponibilité" value={f.availability} options={['AVAILABLE', 'ON_REQUEST', 'DISCONTINUED']} onChange={value => props.setForm({ ...f, availability: value })} /><TextArea label="Description courte" value={f.shortDescription || ''} onChange={value => props.setForm({ ...f, shortDescription: value })} /><TextArea label="Description longue" value={f.longDescription || ''} onChange={value => props.setForm({ ...f, longDescription: value })} /></div>;
}

function OperationsSection(props: { orders: OperationalOrder[]; globalOrders: ReturnType<typeof useMobileSuperAdmin>['globalOrders']; finance: ReturnType<typeof useMobileSuperAdmin>['financeSummary']; globalLocked: boolean; loading: boolean; onUnlockGlobal: () => void; onOpen: (order: OperationalOrder) => void }) {
  return <div className="space-y-5" data-superadmin-operations>
    <SectionTitle eyebrow="Flux fournisseur" title="Opérations" />
    {props.finance && <div className="grid grid-cols-2 gap-3"><Metric label="À facturer" value={props.finance.waitingInvoiceCount} icon={<ReceiptText size={14} />} /><Metric label="Écarts" value={props.finance.mismatchCount} icon={<AlertTriangle size={14} />} /><Metric label="Payable attendu" value={formatMoney(props.finance.expectedSupplierPayable)} /><Metric label="Facturé" value={formatMoney(props.finance.invoicedAmount)} /></div>}
    <section className="space-y-3"><p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Tenant courant · actions réelles</p>{props.loading && !props.orders.length ? <Empty label="Chargement des commandes…" /> : props.orders.length ? props.orders.map(order => <button key={order.id} type="button" onClick={() => props.onOpen(order)} className="flex min-h-[84px] w-full items-center gap-3 rounded-[19px] border border-glass-border bg-card p-4 text-left shadow-sm"><div className="flex h-10 w-10 items-center justify-center rounded-[13px] bg-primary/10 text-primary"><ShoppingCart size={17} /></div><div className="min-w-0 flex-1"><p className="truncate text-xs font-black">{order.orderNumber}</p><p className="truncate text-[9px] font-bold text-text-muted">{order.partnerName} · {order.status}</p><p className="mt-1 text-[10px] font-black text-primary">{formatMoney(order.currentTotal)}</p></div><ChevronRight size={15} /></button>) : <Empty label="Aucune commande opérationnelle pour le tenant courant." />}</section>
    <section className="rounded-[20px] border border-glass-border bg-card p-4"><div className="flex items-center justify-between"><div><p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Vue globale P10</p><h3 className="mt-1 text-sm font-black">Commandes multi-cabinets</h3></div><Shield size={18} className="text-primary" /></div>{props.globalLocked ? <button type="button" onClick={props.onUnlockGlobal} className="mt-4 min-h-11 w-full rounded-[14px] bg-amber-600 text-[10px] font-black text-white"><Fingerprint size={14} className="mr-1 inline" />Déverrouiller WebAuthn</button> : <div className="mt-3 space-y-2">{props.globalOrders.slice(0, 8).map(order => <div key={order.id} className="flex items-center justify-between gap-3 rounded-[13px] bg-background p-3"><div className="min-w-0"><p className="truncate text-[10px] font-black">{order.orderNumber}</p><p className="truncate text-[8px] font-bold text-text-muted">Cabinet #{order.employerId} · {order.supplierName}</p></div><div className="text-right"><p className="text-[9px] font-black">{order.status}</p><p className="text-[8px] font-bold text-primary">{formatMoney(order.currentTotal)}</p></div></div>)}</div>}</section>
  </div>;
}

function OperationSheet(props: {
  order: OperationalOrder; onClose: () => void; loadDetail: (id: number) => Promise<ReturnType<typeof useMobileSuperAdmin> extends { operationActions: infer A } ? A extends { loadDetail: (...args: never[]) => Promise<infer D> } ? D : never : never>;
  updateOrder: ReturnType<typeof useMobileSuperAdmin>['operationActions']['updateOrder']; dispatch: ReturnType<typeof useMobileSuperAdmin>['operationActions']['dispatch']; acknowledgeProcurement: ReturnType<typeof useMobileSuperAdmin>['operationActions']['acknowledgeProcurement']; recordInvoice: ReturnType<typeof useMobileSuperAdmin>['operationActions']['recordInvoice']; receive: ReturnType<typeof useMobileSuperAdmin>['operationActions']['receive']; confirm: (state: NonNullable<ConfirmState>) => void;
}) {
  const [detail, setDetail] = useState<{ dispatch: Record<string, unknown> | null; procurement: Record<string, unknown> | null; receipts: Array<Record<string, unknown>>; reconciliation: Record<string, unknown> | null } | null>(null);
  const [supplierReference, setSupplierReference] = useState('');
  const [expectedDeliveryAt, setExpectedDeliveryAt] = useState('');
  const [procurementNote, setProcurementNote] = useState('');
  const [backorders, setBackorders] = useState<Record<string, number>>({});
  const [invoiceReference, setInvoiceReference] = useState('');
  const [invoiceAmount, setInvoiceAmount] = useState(Number(props.order.currentTotal || 0));
  const [receiptQty, setReceiptQty] = useState<Record<string, number>>({});
  const [receiptLot, setReceiptLot] = useState<Record<string, string>>({});
  const [receiptExpiry, setReceiptExpiry] = useState<Record<string, string>>({});
  useEffect(() => { void props.loadDetail(props.order.id).then(setDetail); }, [props.order.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const reload = () => void props.loadDetail(props.order.id).then(setDetail);
  const transitions = props.order.allowedTransitions.filter(value => value !== 'SENT_TO_PARTNER');
  return <Sheet title={props.order.orderNumber} subtitle={`${props.order.partnerName} · ${props.order.status}`} onClose={props.onClose}><div className="space-y-5" data-superadmin-operation-detail>
    <div className="grid grid-cols-2 gap-3"><Metric label="Total" value={formatMoney(props.order.currentTotal)} /><Metric label="Revenu reconnu" value={formatMoney(props.order.recognizedRevenueAmount)} /></div>
    <section className="rounded-[20px] border border-glass-border bg-card p-4"><p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Cycle commande</p>{props.order.status === 'DRAFT' && <button type="button" onClick={() => props.confirm({ title: 'Envoyer réellement au fournisseur ?', body: `Commande ${props.order.orderNumber} → ${props.order.partnerName}. Le backend effectuera l’appel HTTPS avec preuve de transport et idempotence.`, confirmLabel: 'Envoyer', danger: true, action: async () => { const ok = await props.dispatch(props.order.id); if (ok) reload(); return ok; } })} className="mt-3 min-h-12 w-full rounded-[15px] bg-primary text-xs font-black text-white"><Send size={15} className="mr-1 inline" />Dispatch fournisseur</button>}{transitions.length > 0 && <div className="mt-3 grid grid-cols-2 gap-2">{transitions.map(state => <button key={state} type="button" onClick={() => props.confirm({ title: `Passer en ${state} ?`, body: 'La transition sera validée par le moteur canonique serveur. Aucun succès local ne sera simulé.', confirmLabel: state, danger: state === 'CANCELLED', action: () => props.updateOrder(props.order.id, { status: state }) })} className={`min-h-11 rounded-[13px] text-[9px] font-black ${state === 'CANCELLED' ? 'bg-rose-100 text-rose-700' : 'border border-glass-border bg-background text-text-main'}`}>{state}</button>)}</div>}{detail?.dispatch && <div className="mt-4 rounded-[14px] bg-background p-3 text-[9px] font-semibold text-text-muted"><p className="font-black text-text-main">Preuve dispatch</p><p className="mt-1">Outcome: {String(detail.dispatch.outcome ?? '—')}</p><p>HTTP: {String(detail.dispatch.responseStatus ?? '—')} · Réf: {String(detail.dispatch.supplierReference ?? '—')}</p></div>}</section>

    <section className="rounded-[20px] border border-glass-border bg-card p-4"><div className="flex items-center gap-2"><Truck size={16} className="text-primary" /><p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Procurement</p></div><Field label="Référence fournisseur" value={supplierReference} onChange={setSupplierReference} /><Field label="Livraison attendue" type="datetime-local" value={expectedDeliveryAt} onChange={setExpectedDeliveryAt} /><TextArea label="Note" value={procurementNote} onChange={setProcurementNote} />{props.order.lines.map(line => <NumberField key={line.productId} label={`Backorder ${line.sku} · max ${line.quantity}`} value={backorders[line.productId] || 0} min={0} max={line.quantity} onChange={value => setBackorders({ ...backorders, [line.productId]: value })} />)}<button type="button" disabled={!supplierReference.trim()} onClick={() => props.confirm({ title: 'Enregistrer l’accusé fournisseur ?', body: 'Le serveur vérifiera CONFIRMED, reliquats et backorders avant toute écriture.', confirmLabel: 'Enregistrer', action: async () => { const ok = await props.acknowledgeProcurement(props.order.id, { supplierReference, expectedDeliveryAt: expectedDeliveryAt || null, backorderedLines: Object.entries(backorders).filter(([, qty]) => qty > 0).map(([productId, quantityBackordered]) => ({ productId, quantityBackordered })), note: procurementNote || undefined }); if (ok) reload(); return ok; } })} className="mt-3 min-h-12 w-full rounded-[15px] bg-primary text-xs font-black text-white disabled:opacity-40">Accuser réception fournisseur</button></section>

    <section className="rounded-[20px] border border-glass-border bg-card p-4"><div className="flex items-center gap-2"><ReceiptText size={16} className="text-primary" /><p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Facture & rapprochement</p></div>{detail?.reconciliation && <div className="mt-3 grid grid-cols-2 gap-2"><Metric label="Statut" value={String(detail.reconciliation.reconciliationStatus ?? '—')} /><Metric label="Variance" value={formatMoney(detail.reconciliation.invoiceVariance)} /></div>}<Field label="Référence facture" value={invoiceReference} onChange={setInvoiceReference} /><NumberField label="Montant total MAD" value={invoiceAmount} min={0} step="0.01" onChange={setInvoiceAmount} /><button type="button" disabled={!invoiceReference.trim()} onClick={() => props.confirm({ title: 'Enregistrer cette facture fournisseur ?', body: `${invoiceReference} · ${formatMoney(invoiceAmount)}. Une clé d’idempotence sera générée côté mobile et validée par le serveur.`, confirmLabel: 'Enregistrer facture', action: async () => { const ok = await props.recordInvoice(props.order.id, { invoiceReference, amountTotal: invoiceAmount }); if (ok) reload(); return ok; } })} className="mt-3 min-h-12 w-full rounded-[15px] bg-primary text-xs font-black text-white disabled:opacity-40">Enregistrer facture</button></section>

    <section className="rounded-[20px] border border-glass-border bg-card p-4"><div className="flex items-center gap-2"><PackageCheck size={16} className="text-primary" /><p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Réception</p></div>{props.order.lines.map(line => <div key={line.productId} className="mt-3 rounded-[14px] bg-background p-3"><p className="text-[10px] font-black">{line.name}</p><p className="text-[8px] font-bold text-text-muted">{line.sku} · commandé {line.quantity}</p><div className="mt-2 grid grid-cols-2 gap-2"><NumberField label="Qté reçue" value={receiptQty[line.productId] || 0} min={0} max={line.quantity} onChange={value => setReceiptQty({ ...receiptQty, [line.productId]: value })} /><Field label="Lot" value={receiptLot[line.productId] || ''} onChange={value => setReceiptLot({ ...receiptLot, [line.productId]: value })} /></div><Field label="Expiration" type="date" value={receiptExpiry[line.productId] || ''} onChange={value => setReceiptExpiry({ ...receiptExpiry, [line.productId]: value })} /></div>)}<button type="button" onClick={() => props.confirm({ title: 'Enregistrer cette réception ?', body: 'Le serveur recalculera commandé / déjà reçu / restant et refusera toute sur-réception.', confirmLabel: 'Enregistrer réception', action: async () => { const lines = props.order.lines.filter(line => (receiptQty[line.productId] || 0) > 0).map(line => ({ productId: line.productId, quantityReceived: receiptQty[line.productId], lotNumber: receiptLot[line.productId] || null, expiresAt: receiptExpiry[line.productId] || null })); const ok = await props.receive(props.order.id, { lines }); if (ok) reload(); return ok; } })} className="mt-3 min-h-12 w-full rounded-[15px] bg-primary text-xs font-black text-white">Enregistrer réception</button>{detail?.receipts?.length ? <p className="mt-3 text-[9px] font-bold text-text-muted">{detail.receipts.length} réception(s) déjà enregistrée(s).</p> : null}</section>
  </div></Sheet>;
}

function Field(props: { label: string; value: string; onChange: (value: string) => void; required?: boolean; type?: string }) {
  return <label className="mt-3 block"><span className="text-[9px] font-black uppercase tracking-wider text-text-muted">{props.label}</span><input required={props.required} type={props.type || 'text'} value={props.value} onChange={event => props.onChange(event.target.value)} className="mt-1 min-h-12 w-full rounded-[14px] border border-glass-border bg-background px-3 text-sm font-semibold outline-none focus:border-primary" /></label>;
}
function NumberField(props: { label: string; value: number; onChange: (value: number) => void; min?: number; max?: number; step?: string }) {
  return <label className="mt-3 block"><span className="text-[9px] font-black uppercase tracking-wider text-text-muted">{props.label}</span><input type="number" value={Number.isFinite(props.value) ? props.value : 0} min={props.min} max={props.max} step={props.step || '1'} onChange={event => props.onChange(Number(event.target.value) || 0)} className="mt-1 min-h-12 w-full rounded-[14px] border border-glass-border bg-background px-3 text-sm font-semibold outline-none focus:border-primary" /></label>;
}
function SelectField(props: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return <label className="mt-3 block"><span className="text-[9px] font-black uppercase tracking-wider text-text-muted">{props.label}</span><select value={props.value} onChange={event => props.onChange(event.target.value)} className="mt-1 min-h-12 w-full rounded-[14px] border border-glass-border bg-background px-3 text-sm font-semibold outline-none focus:border-primary">{props.options.map(option => <option key={option} value={option}>{option}</option>)}</select></label>;
}
function TextArea(props: { label: string; value: string; onChange: (value: string) => void }) {
  return <label className="mt-3 block"><span className="text-[9px] font-black uppercase tracking-wider text-text-muted">{props.label}</span><textarea rows={3} value={props.value} onChange={event => props.onChange(event.target.value)} className="mt-1 w-full rounded-[14px] border border-glass-border bg-background p-3 text-sm font-semibold outline-none focus:border-primary" /></label>;
}
function Empty({ label }: { label: string }) { return <div className="rounded-[18px] border border-dashed border-glass-border bg-card px-4 py-10 text-center text-xs font-bold text-text-muted">{label}</div>; }

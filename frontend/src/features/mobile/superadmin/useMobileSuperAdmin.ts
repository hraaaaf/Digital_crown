import { useCallback, useEffect, useMemo, useState } from 'react';
import { MobileStorage } from '../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../services/zka/mobileFetch';
import { unlockMobilePasskey } from '../../../services/zka/mobilePasskey';

export type SuperAdminSection = 'overview' | 'clients' | 'trials' | 'marketplace' | 'operations';

export interface SuperAdminClient {
  id: number;
  nom_complet: string;
  email: string;
  telephone?: string | null;
  telephone_mobile?: string | null;
  telephone_fixe?: string | null;
  cabinet_name: string;
  is_active?: boolean;
  is_licensed: boolean;
  license_expires_at: string | null;
  created_at?: string | null;
  is_archived: boolean;
  is_suspended: boolean;
  internal_notes?: string | null;
  last_login_at?: string | null;
  subscription_plan: string | null;
  stats: { total_patients: number; total_ia_panoramique: number; total_ia_cephalo: number };
}

export interface TrialCode {
  id: number;
  code: string;
  email: string;
  nom_complet: string | null;
  cabinet_name: string | null;
  trial_days: number;
  notes?: string | null;
  expires_at: string;
  consumed_at: string | null;
  revoked_at: string | null;
  created_at?: string | null;
  activation_url: string;
}

export interface MarketplaceOverview {
  cabinetsCount: number;
  suppliersCount: number;
  activeSuppliersCount: number;
  productsCount: number;
  ordersCount: number;
  ordersByStatus: Record<string, number>;
  recognizedRevenueAmount: number;
  invoicedSupplierAmount: number;
  syncDegradedCount: number;
  syncStaleCount: number;
  activeAgreementsCount: number;
}

export interface GlobalOrder {
  employerId: number;
  ownerEmail: string | null;
  ownerName: string | null;
  id: number;
  orderNumber: string;
  supplierName: string;
  status: string;
  currentTotal: number;
  recognizedRevenueAmount: number;
  partnerReference: string | null;
}

export interface GlobalSupplier {
  employerId: number;
  id: number;
  supplierKey: string;
  name: string;
  badge?: string | null;
  description?: string | null;
  promise?: string | null;
  apiBaseUrl?: string | null;
  syncMode?: string | null;
  isActive: boolean;
  productCount?: number;
}

export interface GlobalProduct {
  employerId: number;
  id: number | string;
  supplierId: number | string;
  supplierName?: string;
  externalProductId?: string | null;
  name: string;
  sku: string;
  dentalCategory?: string;
  category?: string;
  dentalSpecialty?: string;
  specialty?: string;
  unit: string;
  price: number;
  availability: string;
  shortDescription?: string | null;
  description?: string | null;
  longDescription?: string | null;
  benefits?: string[];
  isFeatured?: boolean;
  sortOrder?: number;
}

export interface SyncIncident {
  employerId: number;
  ownerEmail: string | null;
  ownerName: string | null;
  supplierId: number;
  supplierName: string | null;
  freshness: { status: string; [key: string]: unknown };
  lastErrorCode: string | null;
  lastErrorDetail: string | null;
  consecutiveFailures: number;
  nextRetryAt: string | null;
}

export interface GovernanceAuditEvent {
  id: number;
  adminUserId: number;
  employerId: number;
  entityType: string;
  entityId: string;
  action: string;
  payload: unknown;
  createdAt: string | null;
}

export interface OperationalOrder {
  id: number;
  orderNumber: string;
  partnerId: string;
  partnerName: string;
  status: string;
  allowedTransitions: string[];
  currentTotal: number;
  estimatedTotal: number;
  recognizedRevenueAmount: number;
  partnerReference: string | null;
  statusNote?: string | null;
  lines: Array<{ productId: string; name: string; sku: string; quantity: number; unitPrice: number; lineTotal: number }>;
  [key: string]: unknown;
}

export interface MarketplaceFinanceSummary {
  ordersCount: number;
  matchedCount: number;
  mismatchCount: number;
  waitingInvoiceCount: number;
  waitingReceiptCount: number;
  cancelledCount: number;
  currentOrderAmount: number;
  recognizedRevenueAmount: number;
  expectedSupplierPayable: number;
  invoicedAmount: number;
  invoiceVariance: number;
  orders: Array<Record<string, unknown>>;
}

export interface OperationDetail {
  dispatch: Record<string, unknown> | null;
  procurement: Record<string, unknown> | null;
  receipts: Array<Record<string, unknown>>;
  receiptProgress: Record<string, unknown> | null;
  reconciliation: Record<string, unknown> | null;
}

export interface MobileSuperAdminPreviewData {
  clients: SuperAdminClient[];
  trialCodes: TrialCode[];
  overview: MarketplaceOverview;
  globalOrders: GlobalOrder[];
  suppliers: GlobalSupplier[];
  products: GlobalProduct[];
  incidents: SyncIncident[];
  audit: GovernanceAuditEvent[];
  operationalOrders: OperationalOrder[];
  financeSummary: MarketplaceFinanceSummary;
  operationDetails?: Record<number, Omit<OperationDetail, 'receiptProgress'> & { receiptProgress?: Record<string, unknown> | null }>;
}

export interface TrialCodeCreateInput {
  email: string;
  nom_complet?: string;
  cabinet_name?: string;
  trial_days: number;
  expires_in_days: number;
  notes?: string;
}

export interface SupplierCreateInput {
  employerId: number;
  supplierKey: string;
  name: string;
  badge?: string;
  description?: string;
  promise?: string;
  apiBaseUrl?: string;
  syncMode?: string;
  isActive: boolean;
}

export interface ProductCreateInput {
  employerId: number;
  supplierId: number;
  externalProductId?: string | null;
  name: string;
  sku: string;
  dentalCategory: string;
  dentalSpecialty: string;
  unit: string;
  price: number;
  availability: string;
  shortDescription?: string;
  longDescription?: string;
  benefits?: string[];
  isFeatured?: boolean;
  sortOrder?: number;
}

interface ApiError extends Error {
  status?: number;
  code?: string;
}

interface DispatchEnvelope {
  dispatch: Record<string, unknown> | null;
}

interface ProcurementEnvelope {
  procurement: Record<string, unknown> | null;
}

interface ReceiptsEnvelope {
  receipts: Array<Record<string, unknown>>;
  progress: Record<string, unknown>;
}

function resolveApiBaseUrl(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) return `${window.location.protocol}//${hostname}:8005`;
  return stored;
}

function errorMessage(payload: unknown, status: number): string {
  if (typeof payload === 'object' && payload !== null && 'detail' in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === 'string') return detail;
    if (detail && typeof detail === 'object') {
      const message = (detail as { message?: unknown }).message;
      const code = (detail as { code?: unknown }).code;
      if (typeof message === 'string') return message;
      if (typeof code === 'string') return code;
    }
  }
  return `Erreur ${status}`;
}

function errorCode(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object' || !('detail' in payload)) return undefined;
  const detail = (payload as { detail?: unknown }).detail;
  if (!detail || typeof detail !== 'object') return undefined;
  const code = (detail as { code?: unknown }).code;
  return typeof code === 'string' ? code : undefined;
}

export function useMobileSuperAdmin(previewData?: MobileSuperAdminPreviewData) {
  const [clients, setClients] = useState<SuperAdminClient[]>(() => previewData?.clients ?? []);
  const [trialCodes, setTrialCodes] = useState<TrialCode[]>(() => previewData?.trialCodes ?? []);
  const [overview, setOverview] = useState<MarketplaceOverview | null>(() => previewData?.overview ?? null);
  const [globalOrders, setGlobalOrders] = useState<GlobalOrder[]>(() => previewData?.globalOrders ?? []);
  const [suppliers, setSuppliers] = useState<GlobalSupplier[]>(() => previewData?.suppliers ?? []);
  const [products, setProducts] = useState<GlobalProduct[]>(() => previewData?.products ?? []);
  const [incidents, setIncidents] = useState<SyncIncident[]>(() => previewData?.incidents ?? []);
  const [audit, setAudit] = useState<GovernanceAuditEvent[]>(() => previewData?.audit ?? []);
  const [operationalOrders, setOperationalOrders] = useState<OperationalOrder[]>(() => previewData?.operationalOrders ?? []);
  const [financeSummary, setFinanceSummary] = useState<MarketplaceFinanceSummary | null>(() => previewData?.financeSummary ?? null);
  const [loadingCore, setLoadingCore] = useState(!previewData);
  const [loadingMarketplace, setLoadingMarketplace] = useState(false);
  const [loadingOperations, setLoadingOperations] = useState(false);
  const [marketplaceLocked, setMarketplaceLocked] = useState(!previewData);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  const request = useCallback(async <T,>(path: string, init: RequestInit = {}): Promise<T> => {
    if (previewData) throw new Error('Preview request forbidden');
    const creds = await MobileStorage.getCredentials();
    if (!creds) throw new Error('Session mobile non appairée.');
    const response = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init.headers ?? {}),
      },
      signal: init.signal ?? AbortSignal.timeout(10_000),
    });
    const payload = response.status === 204 ? null : await response.json().catch(() => ({}));
    if (!response.ok) {
      const typed = new Error(errorMessage(payload, response.status)) as ApiError;
      typed.status = response.status;
      typed.code = errorCode(payload);
      throw typed;
    }
    return payload as T;
  }, [previewData]);

  const loadCore = useCallback(async () => {
    if (previewData) return;
    setLoadingCore(true);
    setError(null);
    try {
      const [nextClients, nextTrials] = await Promise.all([
        request<SuperAdminClient[]>('/api/superadmin/clients'),
        request<TrialCode[]>('/api/superadmin/trial-codes'),
      ]);
      setClients(nextClients);
      setTrialCodes(nextTrials);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Chargement SuperAdmin impossible.');
    } finally {
      setLoadingCore(false);
    }
  }, [previewData, request]);

  const loadMarketplace = useCallback(async (stepUp = false) => {
    if (previewData) {
      setMarketplaceLocked(false);
      return true;
    }
    setLoadingMarketplace(true);
    setError(null);
    try {
      if (stepUp && !MobileStorage.getBiometricAccessToken()) await unlockMobilePasskey();
      const [nextOverview, nextOrders, nextSuppliers, nextProducts, nextIncidents, nextAudit] = await Promise.all([
        request<MarketplaceOverview>('/api/superadmin/marketplace/overview'),
        request<GlobalOrder[]>('/api/superadmin/marketplace/orders?limit=200'),
        request<GlobalSupplier[]>('/api/superadmin/marketplace/suppliers?limit=500'),
        request<GlobalProduct[]>('/api/superadmin/marketplace/products?limit=1000'),
        request<SyncIncident[]>('/api/superadmin/marketplace/sync-incidents'),
        request<GovernanceAuditEvent[]>('/api/superadmin/marketplace/audit?limit=100'),
      ]);
      setOverview(nextOverview);
      setGlobalOrders(nextOrders);
      setSuppliers(nextSuppliers);
      setProducts(nextProducts);
      setIncidents(nextIncidents);
      setAudit(nextAudit);
      setMarketplaceLocked(false);
      return true;
    } catch (cause) {
      const typed = cause as ApiError;
      if (typed.status === 403 && typed.code === 'MARKETPLACE_SUPERADMIN_BIOMETRIC_REQUIRED') {
        setMarketplaceLocked(true);
        MobileStorage.clearBiometricAccessToken();
      } else {
        setError(typed.message || 'Control-plane Marketplace indisponible.');
      }
      return false;
    } finally {
      setLoadingMarketplace(false);
    }
  }, [previewData, request]);

  const loadOperations = useCallback(async () => {
    if (previewData) return;
    setLoadingOperations(true);
    setError(null);
    try {
      const [nextOrders, nextFinance] = await Promise.all([
        request<OperationalOrder[]>('/api/partner-orders'),
        request<MarketplaceFinanceSummary>('/api/partner-orders/finance/summary'),
      ]);
      setOperationalOrders(nextOrders);
      setFinanceSummary(nextFinance);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Opérations Marketplace indisponibles.');
    } finally {
      setLoadingOperations(false);
    }
  }, [previewData, request]);

  useEffect(() => { void loadCore(); }, [loadCore]);

  const previewSuccess = useCallback((message: string) => {
    setLastMessage(`${message} — démo locale, aucune donnée réelle envoyée.`);
    return true;
  }, []);

  const refreshFor = useCallback(async (refresh: 'core' | 'marketplace' | 'operations' | 'none') => {
    if (refresh === 'core') await loadCore();
    if (refresh === 'marketplace') await loadMarketplace(false);
    if (refresh === 'operations') await loadOperations();
  }, [loadCore, loadMarketplace, loadOperations]);

  const run = useCallback(async (
    operation: () => Promise<unknown>,
    success: string,
    refresh: 'core' | 'marketplace' | 'operations' | 'none' = 'none',
  ) => {
    if (previewData) return previewSuccess(success);
    setError(null);
    try {
      await operation();
      setLastMessage(success);
      await refreshFor(refresh);
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Action SuperAdmin refusée.');
      return false;
    }
  }, [previewData, previewSuccess, refreshFor]);

  const ensureFreshUv = useCallback(async () => {
    if (previewData) return true;
    if (MobileStorage.getBiometricAccessToken()) return true;
    try {
      await unlockMobilePasskey();
      return Boolean(MobileStorage.getBiometricAccessToken());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Vérification biométrique requise.');
      return false;
    }
  }, [previewData]);

  const runP10 = useCallback(async (
    operation: () => Promise<unknown>,
    success: string,
    refresh: 'marketplace' | 'none' = 'marketplace',
  ) => {
    if (previewData) return previewSuccess(success);
    if (!(await ensureFreshUv())) return false;
    setError(null);
    try {
      await operation();
      setLastMessage(success);
      if (refresh === 'marketplace') await loadMarketplace(false);
      return true;
    } catch (cause) {
      const typed = cause as ApiError;
      if (typed.status === 403 && typed.code === 'MARKETPLACE_SUPERADMIN_BIOMETRIC_REQUIRED') {
        MobileStorage.clearBiometricAccessToken();
        setMarketplaceLocked(true);
        setError('La vérification biométrique SuperAdmin a expiré. Déverrouillez de nouveau le control-plane.');
      } else {
        setError(typed.message || 'Action Marketplace SuperAdmin refusée.');
      }
      return false;
    }
  }, [ensureFreshUv, loadMarketplace, previewData, previewSuccess]);

  const coreActions = useMemo(() => ({
    validateClient: (id: number) => run(
      () => request(`/api/superadmin/clients/${id}/validate`, { method: 'POST' }),
      'Client validé avec essai 30 jours.',
      'core',
    ),
    setPlan: (id: number, plan: string) => run(
      () => request(`/api/superadmin/clients/${id}/plan?plan=${encodeURIComponent(plan)}`, { method: 'PATCH' }),
      `Pack ${plan} attribué.`,
      'core',
    ),
    grantLicense: (id: number, action: string) => run(
      () => request(`/api/superadmin/clients/${id}/grant-license?action=${encodeURIComponent(action)}`, { method: 'POST' }),
      action === 'revoke' ? 'Licence révoquée.' : 'Licence prolongée.',
      'core',
    ),
    toggleArchive: (id: number) => run(
      () => request(`/api/superadmin/clients/${id}/archive`, { method: 'PATCH' }),
      'Statut d’archivage mis à jour.',
      'core',
    ),
    toggleSuspend: (id: number) => run(
      () => request(`/api/superadmin/clients/${id}/suspend`, { method: 'PATCH' }),
      'Statut de suspension mis à jour.',
      'core',
    ),
    saveNotes: (id: number, internal_notes: string) => run(
      () => request(`/api/superadmin/clients/${id}/notes`, { method: 'PATCH', body: JSON.stringify({ internal_notes }) }),
      'Notes internes enregistrées.',
      'core',
    ),
    getHistory: async (id: number) => previewData
      ? [{ id: 1, action: 'grant', duration: 30, timestamp: new Date().toISOString() }]
      : request<Array<Record<string, unknown>>>(`/api/superadmin/clients/${id}/license-history`),
    sendRenewal: (id: number, message: string) => run(
      () => request(`/api/superadmin/clients/${id}/send-renewal-email`, { method: 'POST', body: JSON.stringify({ message }) }),
      'Relance renouvellement déclenchée.',
      'none',
    ),
    createTrial: async (payload: TrialCodeCreateInput) => {
      if (previewData) {
        const fake: TrialCode = {
          id: Date.now(),
          code: 'DC-DEMO-NEW-CODE',
          email: payload.email,
          nom_complet: payload.nom_complet ?? null,
          cabinet_name: payload.cabinet_name ?? null,
          trial_days: payload.trial_days,
          notes: payload.notes ?? null,
          expires_at: new Date(Date.now() + payload.expires_in_days * 86_400_000).toISOString(),
          consumed_at: null,
          revoked_at: null,
          activation_url: 'https://digitalcrown.local/activate?code=DC-DEMO-NEW-CODE',
        };
        setTrialCodes(items => [fake, ...items]);
        return previewSuccess('Code d’essai créé');
      }
      setError(null);
      try {
        const next = await request<TrialCode>('/api/superadmin/trial-codes', { method: 'POST', body: JSON.stringify(payload) });
        setTrialCodes(items => [next, ...items]);
        setLastMessage('Code d’essai créé.');
        return true;
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : 'Création du code impossible.');
        return false;
      }
    },
    revokeTrial: (id: number) => run(
      () => request(`/api/superadmin/trial-codes/${id}/revoke`, { method: 'POST' }),
      'Code d’essai révoqué.',
      'core',
    ),
  }), [previewData, previewSuccess, request, run]);

  const marketplaceActions = useMemo(() => ({
    unlock: () => loadMarketplace(true),
    getGovernance: async (supplierId: number) => previewData
      ? {
          supplierId,
          supplierName: suppliers.find(item => item.id === supplierId)?.name ?? 'Fournisseur démo',
          isActive: true,
          syncMode: 'api',
          agreement: {
            status: 'ACTIVE',
            storedStatus: 'ACTIVE',
            reference: 'AGR-DEMO',
            effectiveAt: null,
            expiresAt: null,
            notes: 'Accord fictif',
          },
        }
      : request<Record<string, unknown>>(`/api/superadmin/marketplace/suppliers/${supplierId}/governance`),
    updateGovernance: (supplierId: number, payload: Record<string, unknown>) => runP10(
      () => request(`/api/superadmin/marketplace/suppliers/${supplierId}/governance`, {
        method: 'PATCH',
        body: JSON.stringify({ ...payload, confirm: true }),
      }),
      'Gouvernance fournisseur mise à jour.',
    ),
    createSupplier: (payload: SupplierCreateInput) => runP10(
      () => request('/api/superadmin/marketplace/suppliers', {
        method: 'POST',
        body: JSON.stringify({ ...payload, confirm: true }),
      }),
      'Fournisseur créé.',
    ),
    updateSupplier: (id: number, payload: Record<string, unknown>) => runP10(
      () => request(`/api/superadmin/marketplace/suppliers/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ ...payload, confirm: true }),
      }),
      'Fournisseur mis à jour.',
    ),
    createProduct: (payload: ProductCreateInput) => runP10(
      () => request('/api/superadmin/marketplace/products', {
        method: 'POST',
        body: JSON.stringify({ ...payload, confirm: true }),
      }),
      'Produit créé.',
    ),
    updateProduct: (id: number | string, payload: Record<string, unknown>) => runP10(
      () => request(`/api/superadmin/marketplace/products/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ ...payload, confirm: true }),
      }),
      'Produit mis à jour.',
    ),
    getSyncStatus: async (supplierId: number) => previewData
      ? { freshness: { status: 'FRESH' }, lastErrorCode: null }
      : request<Record<string, unknown>>(`/api/partner-catalog/suppliers/${supplierId}/sync-status`),
    syncSupplier: (supplierId: number, force = false) => run(
      () => request(`/api/partner-catalog/suppliers/${supplierId}/sync${force ? '?force=true' : ''}`, { method: 'POST' }),
      force ? 'Synchronisation forcée terminée.' : 'Synchronisation terminée.',
      'marketplace',
    ),
  }), [loadMarketplace, previewData, request, run, runP10, suppliers]);

  const operationActions = useMemo(() => ({
    loadDetail: async (id: number): Promise<OperationDetail> => {
      if (previewData) {
        const stored = previewData.operationDetails?.[id];
        return {
          dispatch: stored?.dispatch ?? null,
          procurement: stored?.procurement ?? null,
          receipts: stored?.receipts ?? [],
          receiptProgress: stored?.receiptProgress ?? null,
          reconciliation: stored?.reconciliation ?? null,
        };
      }
      const safe = async <T,>(path: string, fallback: T): Promise<T> => {
        try { return await request<T>(path); } catch { return fallback; }
      };
      const [dispatchResult, procurementResult, receiptsResult, reconciliation] = await Promise.all([
        safe<DispatchEnvelope>(`/api/partner-orders/${id}/dispatch`, { dispatch: null }),
        safe<ProcurementEnvelope>(`/api/partner-orders/${id}/procurement`, { procurement: null }),
        safe<ReceiptsEnvelope>(`/api/partner-orders/${id}/receipts`, { receipts: [], progress: {} }),
        safe<Record<string, unknown>>(`/api/partner-orders/finance/orders/${id}/reconciliation`, {}),
      ]);
      return {
        dispatch: dispatchResult.dispatch ?? null,
        procurement: procurementResult.procurement ?? null,
        receipts: Array.isArray(receiptsResult.receipts) ? receiptsResult.receipts : [],
        receiptProgress: receiptsResult.progress && typeof receiptsResult.progress === 'object' ? receiptsResult.progress : null,
        reconciliation: Object.keys(reconciliation).length ? reconciliation : null,
      };
    },
    updateOrder: (id: number, payload: { status: string; currentTotal?: number; partnerReference?: string; note?: string }) => run(
      () => request(`/api/partner-orders/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
      'Commande partenaire mise à jour.',
      'operations',
    ),
    dispatch: (id: number) => run(
      () => request(`/api/partner-orders/${id}/dispatch`, { method: 'POST' }),
      'Commande envoyée au fournisseur avec preuve de transport.',
      'operations',
    ),
    acknowledgeProcurement: (
      id: number,
      payload: {
        supplierReference: string;
        expectedDeliveryAt?: string | null;
        backorderedLines: Array<{ productId: string; quantityBackordered: number }>;
        note?: string;
      },
    ) => run(
      () => request(`/api/partner-orders/${id}/procurement`, { method: 'PUT', body: JSON.stringify(payload) }),
      'Accusé fournisseur enregistré.',
      'operations',
    ),
    recordInvoice: (
      id: number,
      payload: { invoiceReference: string; amountTotal: number; issuedAt?: string | null; note?: string },
    ) => {
      const invoiceKey = typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `mobile-${Date.now()}`;
      return run(
        () => request(`/api/partner-orders/finance/orders/${id}/invoices`, {
          method: 'POST',
          body: JSON.stringify({ ...payload, invoiceKey, currency: 'MAD' }),
        }),
        'Facture fournisseur enregistrée.',
        'operations',
      );
    },
    receive: (
      id: number,
      payload: {
        lines: Array<{ productId: string; quantityReceived: number; lotNumber?: string | null; expiresAt?: string | null }>;
        note?: string;
      },
    ) => {
      const idempotencyKey = typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `mobile-${Date.now()}`;
      return run(
        () => request(`/api/partner-orders/${id}/receipt`, {
          method: 'POST',
          body: JSON.stringify({ ...payload, idempotencyKey }),
        }),
        'Réception fournisseur enregistrée.',
        'operations',
      );
    },
  }), [previewData, request, run]);

  return {
    clients,
    trialCodes,
    overview,
    globalOrders,
    suppliers,
    products,
    incidents,
    audit,
    operationalOrders,
    financeSummary,
    loadingCore,
    loadingMarketplace,
    loadingOperations,
    marketplaceLocked,
    error,
    setError,
    lastMessage,
    setLastMessage,
    loadCore,
    loadMarketplace,
    loadOperations,
    coreActions,
    marketplaceActions,
    operationActions,
    previewMode: Boolean(previewData),
  };
}

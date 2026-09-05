import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Camera, CircleDollarSign, Loader2, ScanLine, Search, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';
import { CryptoService } from '../../../../services/zka/CryptoService';
import type { MobileQuickPatientAction } from './MobileQuickActionHub';

type SearchResult = {
  id: number;
  name: string;
  phone?: string | null;
  numero_dossier?: string | null;
};

type PaymentMethod = 'ESPECES' | 'CARTE' | 'VIREMENT' | 'CHEQUE';

function resolveApiBaseUrl(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return stored.replace(/\/$/, '');
}

async function decryptMobileResponse<T>(response: Response, masterKey: string): Promise<T> {
  const raw = await response.json();
  return raw.payload ? CryptoService.decryptPayload(raw.payload, masterKey) : raw;
}

export function MobileQuickPatientFlow({
  action,
  onClose,
  onPaymentRecorded,
}: {
  action: MobileQuickPatientAction;
  onClose: () => void;
  onPaymentRecorded: () => void;
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<SearchResult | null>(null);
  const [amount, setAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('ESPECES');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const title = useMemo(() => {
    if (action === 'photo') return 'Photo clinique';
    if (action === 'scan') return 'Scanner document';
    return 'Encaisser rapidement';
  }, [action]);

  useEffect(() => {
    if (selectedPatient) return;
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setSearching(true);
      setError('');
      try {
        const creds = await MobileStorage.getCredentials();
        if (!creds) throw new Error('Session mobile indisponible.');
        const baseUrl = resolveApiBaseUrl(creds.api_base_url);
        const response = await mobileFetch(
          `${baseUrl}/api/mobile/patient-cockpit/search?q=${encodeURIComponent(query.trim())}`,
          {
            headers: { Authorization: `Bearer ${creds.access_token}` },
            signal: AbortSignal.timeout(5000),
          },
        );
        if (!response.ok) throw new Error(`Recherche patient indisponible (${response.status}).`);
        const payload = await decryptMobileResponse<{ patients: SearchResult[] }>(response, creds.masterKey);
        if (!cancelled) setResults(payload.patients || []);
      } catch (failure) {
        if (!cancelled) {
          setResults([]);
          setError(failure instanceof Error ? failure.message : 'Recherche patient indisponible.');
        }
      } finally {
        if (!cancelled) setSearching(false);
      }
    }, 220);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query, selectedPatient]);

  const openClinicalContext = async (patient: SearchResult) => {
    setSubmitting(true);
    setError('');
    try {
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Session mobile indisponible.');
      const baseUrl = resolveApiBaseUrl(creds.api_base_url);
      const response = await mobileFetch(`${baseUrl}/api/mobile/patient-cockpit/${patient.id}/context`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${creds.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ resource_type: 'patient', resource_id: null }),
        signal: AbortSignal.timeout(5000),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !payload?.context?.key || payload?.context?.type !== 'patient') {
        throw new Error(payload?.detail || `Contexte indisponible (${response.status}).`);
      }
      await MobileStorage.saveBridgeContext(payload.context);
      try { sessionStorage.setItem('dc-mobile-quick-intent', action); } catch { /* best effort only */ }
      window.location.assign('/mobile/context');
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Impossible d’ouvrir le contexte clinique.');
      setSubmitting(false);
    }
  };

  const preparePayment = async (patient: SearchResult) => {
    setSubmitting(true);
    setError('');
    try {
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Session mobile indisponible.');
      const baseUrl = resolveApiBaseUrl(creds.api_base_url);
      const response = await mobileFetch(`${baseUrl}/api/mobile/patient-cockpit/${patient.id}`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
        signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) {
        if (response.status === 403) throw new Error('Accès financier non autorisé pour cet utilisateur.');
        throw new Error(`Situation financière indisponible (${response.status}).`);
      }
      const cockpit = await decryptMobileResponse<{ finance?: { remaining_due?: number | null } | null }>(response, creds.masterKey);
      const remainingDue = Number(cockpit.finance?.remaining_due ?? 0);
      if (remainingDue > 0) setAmount(String(Math.round(remainingDue * 100) / 100));
      setSelectedPatient(patient);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Encaissement indisponible.');
    } finally {
      setSubmitting(false);
    }
  };

  const selectPatient = (patient: SearchResult) => {
    if (action === 'payment') {
      void preparePayment(patient);
      return;
    }
    void openClinicalContext(patient);
  };

  const recordPayment = async () => {
    if (!selectedPatient) return;
    const numericAmount = Number(amount.replace(',', '.'));
    if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
      setError('Saisissez un montant supérieur à 0.');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Session mobile indisponible.');
      const baseUrl = resolveApiBaseUrl(creds.api_base_url);
      const response = await mobileFetch(`${baseUrl}/api/accounting/payments`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${creds.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patient_id: selectedPatient.id,
          amount: numericAmount,
          payment_method: paymentMethod,
        }),
        signal: AbortSignal.timeout(6000),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof payload?.detail === 'string' ? payload.detail : `Encaissement refusé (${response.status}).`;
        throw new Error(detail);
      }
      toast.success('Encaissement enregistré');
      onPaymentRecorded();
      onClose();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Encaissement impossible.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-end bg-slate-950/30 backdrop-blur-sm sm:items-center sm:justify-center sm:p-4" data-mobile-quick-patient-flow>
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="mobile-quick-patient-title"
        className="w-full max-h-[88dvh] overflow-y-auto rounded-t-[28px] border border-glass-border bg-card p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] shadow-elite sm:max-w-md sm:rounded-[28px]"
        style={{
          backgroundColor: 'var(--glass-bg)',
          fontFamily: 'var(--app-font-family, "Inter", system-ui, sans-serif)',
        }}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-[14px] bg-primary/10 text-primary">
              {action === 'photo' ? <Camera size={19} /> : action === 'scan' ? <ScanLine size={19} /> : <CircleDollarSign size={19} />}
            </span>
            <div>
              <p className="text-[9px] font-black uppercase tracking-[0.16em] text-text-muted">Action rapide</p>
              <h2 id="mobile-quick-patient-title" className="mt-0.5 text-lg font-black text-text-main">{title}</h2>
            </div>
          </div>
          <button type="button" onClick={onClose} aria-label="Fermer" className="flex h-11 w-11 items-center justify-center rounded-[15px] border border-glass-border bg-background text-text-muted">
            <X size={18} />
          </button>
        </div>

        {selectedPatient && action === 'payment' ? (
          <div className="space-y-4">
            <button type="button" onClick={() => { setSelectedPatient(null); setAmount(''); setError(''); }} className="inline-flex min-h-11 items-center gap-2 text-xs font-black text-primary">
              <ArrowLeft size={16} /> Changer de patient
            </button>
            <div className="rounded-[18px] border border-glass-border bg-background p-4">
              <p className="text-[9px] font-black uppercase tracking-[0.14em] text-text-muted">Patient</p>
              <p className="mt-1 text-sm font-black text-text-main">{selectedPatient.name}</p>
            </div>
            <div>
              <label className="text-[10px] font-black uppercase tracking-[0.14em] text-text-muted">Montant (MAD)</label>
              <input
                inputMode="decimal"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                placeholder="0,00"
                className="mt-1 min-h-14 w-full rounded-[18px] border border-glass-border bg-background px-4 text-lg font-black text-text-main outline-none focus:border-primary/40"
              />
            </div>
            <div>
              <label className="text-[10px] font-black uppercase tracking-[0.14em] text-text-muted">Mode de paiement</label>
              <select
                value={paymentMethod}
                onChange={(event) => setPaymentMethod(event.target.value as PaymentMethod)}
                className="mt-1 min-h-14 w-full rounded-[18px] border border-glass-border bg-background px-4 text-sm font-black text-text-main outline-none focus:border-primary/40"
              >
                <option value="ESPECES">Espèces</option>
                <option value="CARTE">Carte</option>
                <option value="VIREMENT">Virement</option>
                <option value="CHEQUE">Chèque</option>
              </select>
            </div>
            {error && <p className="text-xs font-bold text-rose-600">{error}</p>}
            <button type="button" disabled={submitting} onClick={() => void recordPayment()} className="flex min-h-[54px] w-full items-center justify-center gap-2 rounded-[18px] bg-primary px-4 text-sm font-black text-white shadow-sm disabled:opacity-50">
              {submitting && <Loader2 size={17} className="animate-spin" />} Confirmer l’encaissement
            </button>
          </div>
        ) : (
          <>
            <label className="relative block">
              <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-primary" />
              <input
                autoFocus
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Nom, téléphone ou n° dossier"
                className="min-h-14 w-full rounded-[20px] border border-glass-border bg-background pl-12 pr-12 text-sm font-bold text-text-main outline-none focus:border-primary/40"
              />
              {searching && <Loader2 size={17} className="absolute right-4 top-1/2 -translate-y-1/2 animate-spin text-primary" />}
            </label>

            {error && <p className="mt-3 text-xs font-bold text-rose-600">{error}</p>}

            <div className="mt-4 space-y-2">
              {!searching && !error && results.length === 0 && (
                <div className="rounded-[18px] border border-glass-border bg-background p-4 text-center text-xs font-bold text-text-muted">Aucun patient trouvé.</div>
              )}
              {results.map((patient) => (
                <button
                  key={patient.id}
                  type="button"
                  disabled={submitting}
                  onClick={() => selectPatient(patient)}
                  className="flex min-h-[58px] w-full items-center justify-between gap-3 rounded-[18px] border border-glass-border bg-background p-3 text-left active:scale-[0.99] disabled:opacity-50"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-black text-text-main">{patient.name}</span>
                    <span className="mt-0.5 block truncate text-[10px] font-bold text-text-muted">
                      {patient.numero_dossier ? `#${patient.numero_dossier}` : patient.phone || 'Dossier patient'}
                    </span>
                  </span>
                  {submitting ? <Loader2 size={16} className="shrink-0 animate-spin text-primary" /> : <span className="text-xs font-black text-primary">Choisir</span>}
                </button>
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}

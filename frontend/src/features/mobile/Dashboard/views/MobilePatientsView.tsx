import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Camera,
  ChevronRight,
  CircleDollarSign,
  FileText,
  Image as ImageIcon,
  Loader2,
  MessageCircle,
  Phone,
  ScanLine,
  Search,
  ShieldCheck,
  UserRound,
} from 'lucide-react';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';
import { CryptoService } from '../../../../services/zka/CryptoService';
import { buildTelHref, buildWhatsAppHref } from '../../Context/mobilePatientContact';

export interface PatientSearchResult {
  id: number;
  name: string;
  phone?: string | null;
  numero_dossier?: string | null;
  has_medical_alert: boolean;
}

export interface PatientCockpit {
  patient: {
    id: number;
    name: string;
    prenom?: string | null;
    nom?: string | null;
    numero_dossier?: string | null;
    date_naissance?: string | null;
    phone?: string | null;
    assurance?: string | null;
    has_medical_alert: boolean;
    medical_alert_summary?: string | null;
  };
  next_appointment?: {
    id: number;
    datetime_start: string;
    duration_minutes: number;
    motif: string;
    status: string;
  } | null;
  finance?: {
    has_billing_data: boolean;
    remaining_due: number | null;
    total_collected: number;
    overdue_count: number;
  } | null;
}

export interface PatientCockpitResources {
  documents: Array<{
    id: number;
    label: string;
    document_type?: string | null;
    created_at?: string | null;
  }>;
  panoramics: Array<{
    id: number;
    label: string;
    created_at?: string | null;
  }>;
}

export interface MobilePatientsPreviewData {
  results: PatientSearchResult[];
  cockpit: PatientCockpit;
  resources?: PatientCockpitResources;
  initialSelectedId?: number | null;
}

function resolveApiBaseUrl(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return stored.replace(/\/$/, '');
}

function ageFromBirth(value?: string | null): number | null {
  if (!value) return null;
  const birth = new Date(value);
  if (Number.isNaN(birth.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const beforeBirthday = now.getMonth() < birth.getMonth()
    || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate());
  if (beforeBirthday) age -= 1;
  return age >= 0 && age < 130 ? age : null;
}

function formatMoney(value: number): string {
  return new Intl.NumberFormat('fr-MA', {
    style: 'currency',
    currency: 'MAD',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatAppointment(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date à confirmer';
  return date.toLocaleString('fr-FR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

async function decryptMobileResponse<T>(response: Response, masterKey: string): Promise<T> {
  const raw = await response.json();
  return raw.payload ? CryptoService.decryptPayload(raw.payload, masterKey) : raw;
}

export function MobilePatientsView({
  onClose,
  previewData,
}: {
  onClose: () => void;
  previewData?: MobilePatientsPreviewData;
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<PatientSearchResult[]>(previewData?.results ?? []);
  const [selectedId, setSelectedId] = useState<number | null>(previewData?.initialSelectedId ?? null);
  const [cockpit, setCockpit] = useState<PatientCockpit | null>(
    previewData?.initialSelectedId ? previewData.cockpit : null,
  );
  const [resources, setResources] = useState<PatientCockpitResources>(
    previewData?.resources ?? { documents: [], panoramics: [] },
  );
  const [searching, setSearching] = useState(false);
  const [loadingPatient, setLoadingPatient] = useState(false);
  const [loadingResources, setLoadingResources] = useState(false);
  const [openingContext, setOpeningContext] = useState<string | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (selectedId !== null) return;
    if (previewData) {
      const normalized = query.trim().toLocaleLowerCase('fr');
      setResults(
        normalized
          ? previewData.results.filter((patient) => [patient.name, patient.phone, patient.numero_dossier]
              .filter(Boolean)
              .some((value) => String(value).toLocaleLowerCase('fr').includes(normalized)))
          : previewData.results,
      );
      setSearching(false);
      setError('');
      return;
    }

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
        if (!response.ok) throw new Error(`Recherche indisponible (${response.status}).`);
        const payload = await decryptMobileResponse<{ patients: PatientSearchResult[] }>(response, creds.masterKey);
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
  }, [query, selectedId, previewData]);

  useEffect(() => {
    if (selectedId === null) {
      setCockpit(null);
      setResources({ documents: [], panoramics: [] });
      setOpeningContext(null);
      return;
    }
    if (previewData) {
      setCockpit(previewData.cockpit);
      setResources(previewData.resources ?? { documents: [], panoramics: [] });
      setLoadingPatient(false);
      setLoadingResources(false);
      setOpeningContext(null);
      setError('');
      return;
    }

    // Fail closed between patient selections. A failed load must never leave the
    // previous patient's identity or resources visible under the new selection.
    setCockpit(null);
    setResources({ documents: [], panoramics: [] });
    setOpeningContext(null);
    setError('');

    let cancelled = false;
    const load = async () => {
      setLoadingPatient(true);
      setLoadingResources(true);
      try {
        const creds = await MobileStorage.getCredentials();
        if (!creds) throw new Error('Session mobile indisponible.');
        const baseUrl = resolveApiBaseUrl(creds.api_base_url);
        const [cockpitResponse, resourcesResponse] = await Promise.all([
          mobileFetch(`${baseUrl}/api/mobile/patient-cockpit/${selectedId}`, {
            headers: { Authorization: `Bearer ${creds.access_token}` },
            signal: AbortSignal.timeout(5000),
          }),
          mobileFetch(`${baseUrl}/api/mobile/patient-cockpit/${selectedId}/resources`, {
            headers: { Authorization: `Bearer ${creds.access_token}` },
            signal: AbortSignal.timeout(5000),
          }),
        ]);
        if (!cockpitResponse.ok) throw new Error(`Dossier indisponible (${cockpitResponse.status}).`);
        if (!resourcesResponse.ok) throw new Error(`Ressources indisponibles (${resourcesResponse.status}).`);
        const [cockpitPayload, resourcesPayload] = await Promise.all([
          decryptMobileResponse<PatientCockpit>(cockpitResponse, creds.masterKey),
          decryptMobileResponse<PatientCockpitResources>(resourcesResponse, creds.masterKey),
        ]);
        if (!cancelled) {
          setCockpit(cockpitPayload);
          setResources(resourcesPayload);
        }
      } catch (failure) {
        if (!cancelled) setError(failure instanceof Error ? failure.message : 'Dossier patient indisponible.');
      } finally {
        if (!cancelled) {
          setLoadingPatient(false);
          setLoadingResources(false);
        }
      }
    };

    void load();
    return () => { cancelled = true; };
  }, [selectedId, previewData]);

  const openSecureContext = async (resourceType: 'patient' | 'document' | 'panoramic', resourceId?: number) => {
    if (!selectedId || previewData) return;
    const actionKey = `${resourceType}:${resourceId ?? selectedId}`;
    setOpeningContext(actionKey);
    setError('');
    try {
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Session mobile indisponible.');
      const baseUrl = resolveApiBaseUrl(creds.api_base_url);
      const response = await mobileFetch(`${baseUrl}/api/mobile/patient-cockpit/${selectedId}/context`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${creds.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ resource_type: resourceType, resource_id: resourceId ?? null }),
        signal: AbortSignal.timeout(5000),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !payload?.context?.key || !payload?.context?.type) {
        throw new Error(payload?.detail || `Contexte indisponible (${response.status}).`);
      }
      await MobileStorage.saveBridgeContext(payload.context);
      window.location.assign('/mobile/context');
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Impossible d’ouvrir le contexte clinique.');
      setOpeningContext(null);
    }
  };

  const patient = cockpit?.patient;
  const age = useMemo(() => ageFromBirth(patient?.date_naissance), [patient?.date_naissance]);
  const callHref = buildTelHref(patient?.phone);
  const whatsappHref = buildWhatsAppHref(patient?.phone);
  const latestDocument = resources.documents[0];
  const latestPanoramic = resources.panoramics[0];

  if (selectedId !== null) {
    return (
      <section data-mobile-patient-cockpit className="pb-10 space-y-4">
        <button
          type="button"
          onClick={() => setSelectedId(null)}
          className="inline-flex min-h-11 items-center gap-2 text-sm font-black text-primary active:scale-95 transition-transform"
        >
          <ArrowLeft size={17} /> Tous les patients
        </button>

        {loadingPatient && (
          <div className="min-h-56 rounded-[24px] border border-glass-border bg-card shadow-elite flex items-center justify-center" style={{ backgroundColor: 'var(--glass-bg)' }}>
            <Loader2 className="animate-spin text-primary" size={26} />
          </div>
        )}

        {!loadingPatient && error && (
          <div className="rounded-[22px] border border-rose-200 bg-rose-500/5 p-4 text-sm font-bold text-rose-700">
            {error}
          </div>
        )}

        {!loadingPatient && patient && (
          <>
            <div className="rounded-[26px] border border-glass-border bg-card p-5 shadow-elite" style={{ backgroundColor: 'var(--glass-bg)' }}>
              <div className="flex items-start gap-4">
                <div className="h-14 w-14 shrink-0 rounded-[18px] bg-primary/10 text-primary flex items-center justify-center">
                  <UserRound size={25} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] font-black uppercase tracking-[0.18em] text-text-muted">Dossier patient</p>
                  <h2 className="mt-1 text-2xl font-black tracking-tight text-text-main leading-tight">{patient.name}</h2>
                  <div className="mt-2 flex flex-wrap gap-2 text-[11px] font-bold text-text-muted">
                    {age !== null && <span>{age} ans</span>}
                    {patient.numero_dossier && <span>• #{patient.numero_dossier}</span>}
                    {patient.assurance && <span>• {patient.assurance}</span>}
                  </div>
                </div>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-2">
                <a
                  href={callHref || undefined}
                  aria-disabled={!callHref}
                  className={`min-h-12 rounded-[16px] border flex items-center justify-center gap-2 text-xs font-black transition-all ${callHref ? 'border-primary/20 bg-primary/10 text-primary active:scale-95' : 'border-border-main bg-background text-text-muted opacity-45 pointer-events-none'}`}
                >
                  <Phone size={16} /> Appeler
                </a>
                <a
                  href={whatsappHref || undefined}
                  target={whatsappHref ? '_blank' : undefined}
                  rel="noreferrer"
                  aria-disabled={!whatsappHref}
                  className={`min-h-12 rounded-[16px] border flex items-center justify-center gap-2 text-xs font-black transition-all ${whatsappHref ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-700 active:scale-95' : 'border-border-main bg-background text-text-muted opacity-45 pointer-events-none'}`}
                >
                  <MessageCircle size={16} /> WhatsApp
                </a>
              </div>
            </div>

            {patient.has_medical_alert ? (
              <div className="rounded-[24px] border border-rose-500/25 bg-rose-500/8 p-4 shadow-sm">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 h-9 w-9 shrink-0 rounded-[12px] bg-rose-500/10 text-rose-600 flex items-center justify-center">
                    <AlertTriangle size={18} />
                  </div>
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.16em] text-rose-600">Alerte médicale</p>
                    <p className="mt-1 text-sm font-bold leading-relaxed text-text-main">
                      {patient.medical_alert_summary || 'Antécédents médicaux renseignés dans le dossier.'}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-[22px] border border-emerald-500/20 bg-emerald-500/5 p-4 flex items-center gap-3">
                <ShieldCheck size={18} className="text-emerald-600" />
                <p className="text-xs font-bold text-text-main">Aucune alerte médicale renseignée.</p>
              </div>
            )}

            <div className="rounded-[24px] border border-glass-border bg-card p-4 shadow-elite" style={{ backgroundColor: 'var(--glass-bg)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Camera size={17} className="text-primary" />
                <h3 className="text-sm font-black text-text-main">Actions cliniques rapides</h3>
                {loadingResources && <Loader2 size={14} className="ml-auto animate-spin text-primary" />}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => void openSecureContext('patient')}
                  disabled={Boolean(openingContext)}
                  className="min-h-12 rounded-[16px] border border-primary/20 bg-primary/10 text-primary flex items-center justify-center gap-2 text-xs font-black disabled:opacity-50"
                >
                  <Camera size={16} /> Photo clinique
                </button>
                <button
                  type="button"
                  onClick={() => void openSecureContext('patient')}
                  disabled={Boolean(openingContext)}
                  className="min-h-12 rounded-[16px] border border-primary/20 bg-primary/10 text-primary flex items-center justify-center gap-2 text-xs font-black disabled:opacity-50"
                >
                  <ScanLine size={16} /> Scanner
                </button>
                <button
                  type="button"
                  onClick={() => latestDocument && void openSecureContext('document', latestDocument.id)}
                  disabled={!latestDocument || Boolean(openingContext)}
                  className="min-h-12 rounded-[16px] border border-glass-border bg-background text-text-main flex items-center justify-center gap-2 text-xs font-black disabled:opacity-40"
                  title={latestDocument?.label}
                >
                  <FileText size={16} /> Dernier document
                </button>
                <button
                  type="button"
                  onClick={() => latestPanoramic && void openSecureContext('panoramic', latestPanoramic.id)}
                  disabled={!latestPanoramic || Boolean(openingContext)}
                  className="min-h-12 rounded-[16px] border border-glass-border bg-background text-text-main flex items-center justify-center gap-2 text-xs font-black disabled:opacity-40"
                  title={latestPanoramic?.label}
                >
                  <ImageIcon size={16} /> Dernière pano
                </button>
              </div>
              <p className="mt-3 text-[10px] font-bold leading-relaxed text-text-muted">
                Ouverture via contexte serveur opaque lié à cet appareil. Aucun identifiant patient n’est placé dans l’URL.
              </p>
            </div>

            <div className="rounded-[24px] border border-glass-border bg-card p-4 shadow-elite" style={{ backgroundColor: 'var(--glass-bg)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Calendar size={17} className="text-primary" />
                <h3 className="text-sm font-black text-text-main">Prochain rendez-vous</h3>
              </div>
              {cockpit.next_appointment ? (
                <div>
                  <p className="text-base font-black text-text-main">{formatAppointment(cockpit.next_appointment.datetime_start)}</p>
                  <p className="mt-1 text-xs font-bold text-text-muted">{cockpit.next_appointment.motif} · {cockpit.next_appointment.duration_minutes} min</p>
                </div>
              ) : (
                <p className="text-xs font-bold text-text-muted">Aucun rendez-vous futur planifié.</p>
              )}
            </div>

            {cockpit.finance && (
              <div className="rounded-[24px] border border-glass-border bg-card p-4 shadow-elite" style={{ backgroundColor: 'var(--glass-bg)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <CircleDollarSign size={17} className="text-primary" />
                  <h3 className="text-sm font-black text-text-main">Situation financière</h3>
                </div>
                {cockpit.finance.has_billing_data && cockpit.finance.remaining_due !== null ? (
                  <div className="flex items-end justify-between gap-4">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-[0.14em] text-text-muted">Reste à régler</p>
                      <p className="mt-1 text-2xl font-black text-primary">{formatMoney(cockpit.finance.remaining_due)}</p>
                    </div>
                    {cockpit.finance.overdue_count > 0 && (
                      <span className="rounded-full bg-rose-500/10 px-3 py-1.5 text-[10px] font-black text-rose-600">
                        {cockpit.finance.overdue_count} impayé{cockpit.finance.overdue_count > 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                ) : (
                  <p className="text-xs font-bold text-text-muted">Solde non calculable : aucune base de facturation enregistrée.</p>
                )}
              </div>
            )}
          </>
        )}
      </section>
    );
  }

  return (
    <section data-mobile-patient-search className="pb-10">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-text-muted">Cockpit opérationnel</p>
          <h2 className="mt-1 text-2xl font-black tracking-tight text-text-main">Trouver un patient</h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="h-11 px-4 rounded-[15px] border border-glass-border bg-card text-xs font-black text-primary shadow-sm active:scale-95 transition-transform"
          style={{ backgroundColor: 'var(--glass-bg)' }}
        >
          Agenda
        </button>
      </div>

      <label className="relative block">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-primary" />
        <input
          autoFocus
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Nom, téléphone ou n° dossier"
          className="w-full min-h-14 rounded-[20px] border border-glass-border bg-card pl-12 pr-12 text-sm font-bold text-text-main outline-none shadow-elite placeholder:text-text-muted focus:border-primary/40"
          style={{ backgroundColor: 'var(--glass-bg)' }}
        />
        {searching && <Loader2 size={17} className="absolute right-4 top-1/2 -translate-y-1/2 animate-spin text-primary" />}
      </label>

      {error && <p className="mt-3 text-xs font-bold text-rose-600">{error}</p>}

      <div className="mt-4 space-y-2">
        {!searching && !error && results.length === 0 && (
          <div className="rounded-[22px] border border-glass-border bg-card p-5 text-center text-xs font-bold text-text-muted" style={{ backgroundColor: 'var(--glass-bg)' }}>
            Aucun patient trouvé.
          </div>
        )}

        {results.map((result) => (
          <button
            key={result.id}
            type="button"
            onClick={() => setSelectedId(result.id)}
            className="w-full rounded-[20px] border border-glass-border bg-card p-4 text-left shadow-sm active:scale-[0.99] transition-transform"
            style={{ backgroundColor: 'var(--glass-bg)' }}
          >
            <div className="flex items-center gap-3">
              <div className="h-11 w-11 shrink-0 rounded-[14px] bg-primary/10 text-primary flex items-center justify-center">
                <UserRound size={19} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="truncate text-sm font-black text-text-main">{result.name}</p>
                  {result.has_medical_alert && <AlertTriangle size={14} className="shrink-0 text-rose-600" aria-label="Alerte médicale" />}
                </div>
                <p className="mt-0.5 truncate text-[11px] font-bold text-text-muted">
                  {result.phone || 'Téléphone non renseigné'}{result.numero_dossier ? ` · #${result.numero_dossier}` : ''}
                </p>
              </div>
              <ChevronRight size={18} className="shrink-0 text-primary" />
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}

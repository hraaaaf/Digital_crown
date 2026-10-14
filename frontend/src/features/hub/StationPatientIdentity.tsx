import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Nfc, QrCode, RefreshCw, ShieldCheck } from 'lucide-react';
import {
  stationPatientSessionService,
  type StationPatientSessionCreated,
} from '../../services/stationPatientSession';
import { StationAppointmentArrival, type StationFlowLanguage } from './StationAppointmentArrival';
import { StationPrintStatusPanel } from './StationPrintStatusPanel';

const COPY = {
  fr: {
    tooMany: 'Trop de tentatives. Générez une nouvelle session ou demandez de l’aide.',
    disabled: 'Identification de secours désactivée par le cabinet.',
    notConfirmed: 'Identification non confirmée. Vérifiez les informations ou demandez de l’aide.',
    unavailable: 'Identification indisponible. Prévenez l’équipe d’accueil.',
    disconnected: 'Connexion à la session interrompue.',
    preparing: 'Préparation de la session sécurisée…',
    private: 'Session privée · usage unique',
    qrAlt: 'QR d’identification Patient Companion',
    scan: 'Scannez avec votre téléphone',
    expires: (time: string) => `Le QR expire à ${time} et ne peut servir qu’une fois.`,
    nfc: 'NFC utilise le même lien sécurisé, sans donnée patient.',
    noPhone: 'Je n’ai pas mon téléphone',
    fallback: 'Identification de secours',
    phone: 'Téléphone', firstName: 'Prénom', lastName: 'Nom', birthDate: 'Date de naissance',
    checking: 'Vérification…', confirm: 'Confirmer mon identité',
    privacy: 'Les informations servent uniquement à cette vérification et ne sont pas affichées dans la file d’attente.',
    expired: 'Session expirée', newQr: 'Nouveau QR', retry: 'Réessayer',
    documentsVerified: 'Identité confirmée',
    documentsConstruction: 'Le retrait des documents est en cours de construction sur cette station.',
    documentsStaff: 'Aucun document autorisé à retirer. Adressez-vous à l’accueil.',
    documentsFallback: 'Pour retirer ce document, adressez-vous au personnel du cabinet. Le retrait sur téléphone nécessite Patient Companion appairé.',
    documentsReady: 'Document disponible sur votre téléphone dans Patient Companion. Aucun PDF ne sera conservé sur cette borne.',
  },
  en: {
    tooMany: 'Too many attempts. Generate a new session or ask for help.',
    disabled: 'Backup identification is disabled by the clinic.',
    notConfirmed: 'Identity not confirmed. Check the information or ask for help.',
    unavailable: 'Identification unavailable. Please notify the reception team.',
    disconnected: 'The secure session connection was interrupted.',
    preparing: 'Preparing the secure session…',
    private: 'Private session · single use',
    qrAlt: 'Patient Companion identification QR code',
    scan: 'Scan with your phone',
    expires: (time: string) => `The QR code expires at ${time} and can only be used once.`,
    nfc: 'NFC uses the same secure link, without patient data.',
    noPhone: 'I do not have my phone',
    fallback: 'Backup identification',
    phone: 'Phone', firstName: 'First name', lastName: 'Last name', birthDate: 'Date of birth',
    checking: 'Checking…', confirm: 'Confirm my identity',
    privacy: 'This information is used only for this verification and is not displayed in the waiting queue.',
    expired: 'Session expired', newQr: 'New QR code', retry: 'Try again',
    documentsVerified: 'Identity confirmed',
    documentsConstruction: 'Document collection is under construction at this station.',
    documentsStaff: 'No document is available for collection. Please contact reception.',
    documentsFallback: 'Please contact reception to collect this document. Phone delivery requires a paired Patient Companion.',
    documentsReady: 'Document available on your phone in Patient Companion. This station does not save PDF files.',
  },
  ar: {
    tooMany: 'محاولات كثيرة جداً. أنشئوا جلسة جديدة أو اطلبوا المساعدة.',
    disabled: 'التعرّف الاحتياطي معطل من طرف العيادة.',
    notConfirmed: 'لم يتم تأكيد الهوية. تحققوا من المعلومات أو اطلبوا المساعدة.',
    unavailable: 'خدمة التعرّف غير متاحة. يرجى إبلاغ فريق الاستقبال.',
    disconnected: 'انقطع الاتصال بالجلسة الآمنة.',
    preparing: 'جارٍ إعداد الجلسة الآمنة…',
    private: 'جلسة خاصة · للاستعمال مرة واحدة',
    qrAlt: 'رمز QR للتعرّف عبر Patient Companion',
    scan: 'امسحوا الرمز بهاتفكم',
    expires: (time: string) => `تنتهي صلاحية رمز QR عند ${time} ولا يمكن استعماله إلا مرة واحدة.`,
    nfc: 'يستخدم NFC الرابط الآمن نفسه من دون بيانات المريض.',
    noPhone: 'ليس لدي هاتفي',
    fallback: 'التعرّف الاحتياطي',
    phone: 'الهاتف', firstName: 'الاسم الشخصي', lastName: 'الاسم العائلي', birthDate: 'تاريخ الميلاد',
    checking: 'جارٍ التحقق…', confirm: 'تأكيد هويتي',
    privacy: 'تُستخدم هذه المعلومات لهذا التحقق فقط ولا تظهر في قائمة الانتظار.',
    expired: 'انتهت صلاحية الجلسة', newQr: 'رمز QR جديد', retry: 'إعادة المحاولة',
    documentsVerified: 'تم تأكيد الهوية',
    documentsConstruction: 'خدمة استلام الوثائق قيد الإنشاء في هذه المحطة.',
    documentsStaff: 'لا توجد وثيقة مرخصة للاستلام. يرجى مراجعة الاستقبال.',
    documentsFallback: 'يرجى مراجعة فريق العيادة لاستلام الوثيقة. يتطلب التسليم عبر الهاتف ربط Patient Companion.',
    documentsReady: 'وثيقة متاحة على هاتفكم في Patient Companion. لن تحتفظ هذه المحطة بأي ملف PDF.',
  },
} as const;

const purgeSessionBestEffort = async (sessionId: string) => {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await stationPatientSessionService.purge(sessionId);
      return true;
    } catch {
      // Retry a bounded number of times; the short server TTL remains the final safety net.
    }
  }
  return false;
};

const apiErrorDetail = (error: unknown, language: StationFlowLanguage): string => {
  const copy = COPY[language];
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { status?: number; data?: { detail?: string } } }).response;
    if (response?.status === 429) return copy.tooMany;
    if (response?.data?.detail === 'STATION_FALLBACK_DISABLED') return copy.disabled;
  }
  return copy.notConfirmed;
};

export const StationPatientIdentity = ({
  onBack,
  backLabel,
  language = 'fr',
  purpose = 'appointment',
}: {
  onBack: () => void;
  backLabel: string;
  language?: StationFlowLanguage;
  purpose?: 'appointment' | 'documents';
}) => {
  const copy = COPY[language];
  const [session, setSession] = useState<StationPatientSessionCreated | null>(null);
  const [status, setStatus] = useState<'loading' | 'pending' | 'identified' | 'expired' | 'error'>('loading');
  const [displayName, setDisplayName] = useState('');
  const [companionPaired, setCompanionPaired] = useState(false);
  const [availableDocuments, setAvailableDocuments] = useState<Array<{ documentId: number }>>([]);
  const [documentsBusy, setDocumentsBusy] = useState(false);
  const [documentsError, setDocumentsError] = useState('');
  const [error, setError] = useState('');
  const [fallbackOpen, setFallbackOpen] = useState(false);
  const [fallbackBusy, setFallbackBusy] = useState(false);
  const [birthDate, setBirthDate] = useState('');
  const [phone, setPhone] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const purgeStartedRef = useRef<Set<string>>(new Set());
  const mountedRef = useRef(false);
  const generationRef = useRef(0);
  const sessionRef = useRef<string | null>(null);

  const requestPurge = useCallback((sessionId: string) => {
    if (purgeStartedRef.current.has(sessionId)) return;
    purgeStartedRef.current.add(sessionId);
    void purgeSessionBestEffort(sessionId);
  }, []);

  const createSession = async (generation: number) => {
    try {
      const created = await stationPatientSessionService.create();
      if (!mountedRef.current || generation !== generationRef.current) {
        requestPurge(created.sessionId);
        return;
      }
      sessionRef.current = created.sessionId;
      setSession(created);
      setStatus('pending');
    } catch {
      if (!mountedRef.current || generation !== generationRef.current) return;
      setSession(null);
      setStatus('error');
      setError(COPY[language].unavailable);
    }
  };

  const start = () => {
    const generation = ++generationRef.current;
    if (sessionRef.current) requestPurge(sessionRef.current);
    sessionRef.current = null;
    setSession(null);
    setStatus('loading');
    setError('');
    setDisplayName('');
    setCompanionPaired(false);
    setAvailableDocuments([]);
    setDocumentsError('');
    setFallbackOpen(false);
    setBirthDate('');
    setPhone('');
    setFirstName('');
    setLastName('');
    void createSession(generation);
  };

  useEffect(() => {
    mountedRef.current = true;
    const generation = ++generationRef.current;
    void createSession(generation);
    return () => {
      mountedRef.current = false;
      ++generationRef.current;
      if (sessionRef.current) requestPurge(sessionRef.current);
    };
  }, []);

  useEffect(() => {
    // Once documents have been identified, continue observing server revocation:
    // a phone-side purge must clear the shared Station without waiting for TTL.
    if (!session || (status !== 'pending' && !(purpose === 'documents' && status === 'identified'))) return undefined;
    let cancelled = false;
    const poll = async () => {
      try {
        const next = await stationPatientSessionService.status(session.sessionId);
        if (cancelled) return;
        // An already-expired server response must never resurrect patient data
        // on a shared kiosk, even when a stale status reply says "identified".
        if (purpose === 'documents' && (
          !Number.isFinite(new Date(session.expiresAt).getTime())
          || Date.now() >= new Date(session.expiresAt).getTime()
        )) {
          setDisplayName('');
          setCompanionPaired(false);
          setAvailableDocuments([]);
          setDocumentsError('');
          setStatus('expired');
          requestPurge(session.sessionId);
          return;
        }
        if (next.status === 'identified') {
          setDisplayName(next.displayName);
          setCompanionPaired(next.companionPaired === true);
          setStatus('identified');
          return;
        }
        if (next.status === 'expired') {
          setDisplayName('');
          setCompanionPaired(false);
          setAvailableDocuments([]);
          setDocumentsError('');
          setStatus('expired');
        }
      } catch {
        if (!cancelled) {
          setStatus('error');
          setError(copy.disconnected);
        }
      }
    };
    const timer = window.setInterval(() => void poll(), 1500);
    void poll();
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [session, status, purpose]);

  useEffect(() => {
    if (status !== 'identified' || purpose !== 'documents' || !session) return undefined;
    let cancelled = false;
    setDocumentsBusy(true);
    setDocumentsError('');
    void stationPatientSessionService.availableDocuments(session.sessionId)
      .then((result) => { if (!cancelled) setAvailableDocuments(result.documents); })
      .catch(() => { if (!cancelled) setDocumentsError(copy.unavailable); })
      .finally(() => { if (!cancelled) setDocumentsBusy(false); });
    return () => { cancelled = true; };
  }, [status, purpose, session]);

  // Do not leave a patient's identity or document choices visible on an unattended kiosk.
  // The backend enforces expiry; the Station also clears the screen at that deadline.
  useEffect(() => {
    if (purpose !== 'documents' || status !== 'identified' || !session) return undefined;
    const closeExpired = () => {
      setDisplayName('');
      setCompanionPaired(false);
      setAvailableDocuments([]);
      setDocumentsError('');
      setStatus('expired');
      requestPurge(session.sessionId);
    };
    const remaining = new Date(session.expiresAt).getTime() - Date.now();
    if (!Number.isFinite(remaining) || remaining <= 0) {
      closeExpired();
      return undefined;
    }
    const timeout = window.setTimeout(closeExpired, remaining);
    return () => window.clearTimeout(timeout);
  }, [purpose, status, session, requestPurge]);

  const expiresLabel = useMemo(() => {
    if (!session) return '';
    return new Date(session.expiresAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }, [session]);

  const submitFallback = async () => {
    if (!session || session.fallbackMode === 'disabled' || !birthDate) {
      setError(copy.notConfirmed);
      return;
    }
    setFallbackBusy(true);
    setError('');
    try {
      const result = await stationPatientSessionService.fallback(
        session.sessionId,
        session.fallbackMode === 'phone_dob'
          ? { birthDate, phone }
          : { birthDate, firstName, lastName },
      );
      setDisplayName(result.displayName);
      setCompanionPaired(false);
      setStatus('identified');
      setFallbackOpen(false);
    } catch (fallbackError) {
      setError(apiErrorDetail(fallbackError, language));
    } finally {
      setFallbackBusy(false);
    }
  };

  const leave = async () => {
    ++generationRef.current;
    const sessionId = sessionRef.current || session?.sessionId;
    if (sessionId) requestPurge(sessionId);
    onBack();
  };

  if (status === 'identified' && session && purpose === 'documents') {
    return (
      <section data-station-documents-identity-confirmed className="mx-auto mt-9 w-full max-w-xl rounded-elite-lg border border-border-main bg-card-bg p-6 text-center shadow-elite sm:p-8">
        <ShieldCheck className="mx-auto text-success" size={38} aria-hidden="true" />
        <h2 className="mt-4 text-2xl font-black">{copy.documentsVerified}</h2>
        <p className="mt-2 text-base font-bold text-text-muted">{displayName}</p>
        {documentsBusy && <p className="mt-5 text-sm font-semibold" role="status">{copy.checking}</p>}
        {!documentsBusy && availableDocuments.length === 0 && !documentsError && (
          <p className="mt-5 text-sm font-semibold leading-relaxed text-text-muted">{copy.documentsStaff}</p>
        )}
        {!documentsBusy && availableDocuments.length > 0 && !documentsError && !companionPaired && (
          <p data-station-phone-fallback className="mt-5 text-sm font-semibold leading-relaxed text-text-muted">
            {copy.documentsFallback}
          </p>
        )}
        {!documentsBusy && availableDocuments.length > 0 && !documentsError && companionPaired && (
          <p data-station-phone-delivery className="mt-5 text-sm font-semibold leading-relaxed text-text-muted">
            {copy.documentsReady}
          </p>
        )}
        {/* 04.8-D only renders on identified document sessions. No print action,
            destinations, API call, PDF, or hidden client opt-in exists yet. */}
        <div data-station-print-status-slot className="mt-5 w-full min-w-0">
          <StationPrintStatusPanel language={language} status="disabled" />
        </div>
        {documentsError && <p role="alert" className="mt-4 text-sm font-bold text-danger">{documentsError}</p>}
        <button type="button" onClick={() => void leave()} className="mt-6 min-h-12 w-full rounded-elite-sm bg-primary px-5 text-sm font-black text-on-primary">
          {backLabel}
        </button>
      </section>
    );
  }

  if (status === 'identified' && session) {
    return (
      <StationAppointmentArrival
        sessionId={session.sessionId}
        displayName={displayName}
        onLeave={leave}
        backLabel={backLabel}
        language={language}
      />
    );
  }

  return (
    <section data-station-patient-session className="mx-auto mt-9 w-full max-w-xl rounded-elite-lg border border-border-main bg-card-bg p-6 text-center shadow-elite sm:p-8">
      {status === 'loading' && <p className="font-black">{copy.preparing}</p>}

      {status === 'pending' && session && (
        <>
          <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary/5 px-3 py-2 text-xs font-black text-primary">
            <ShieldCheck size={15} aria-hidden="true" /> {copy.private}
          </div>
          <img src={session.qrDataUrl} alt={copy.qrAlt} className="mx-auto mt-5 aspect-square h-auto w-full max-w-56 rounded-2xl border border-border-main bg-white p-3 object-contain" />
          <p className="mt-4 text-sm font-bold">{copy.scan}</p>
          <p className="mt-1 text-xs font-semibold text-text-muted">{copy.expires(expiresLabel)}</p>
          <div className="mt-4 flex items-center justify-center gap-2 rounded-2xl border border-border-main bg-main-bg px-4 py-3 text-xs font-bold text-text-muted">
            <Nfc size={18} aria-hidden="true" /> {copy.nfc}
          </div>

          {session.fallbackMode !== 'disabled' && (
            <button
              type="button"
              data-station-fallback-toggle
              onClick={() => {
                setFallbackOpen((value) => !value);
                setError('');
              }}
              className="mt-4 min-h-12 w-full rounded-elite-sm border border-border-main px-4 text-sm font-black"
            >
              {copy.noPhone}
            </button>
          )}

          {fallbackOpen && session.fallbackMode !== 'disabled' && (
            <div data-station-fallback-form className="mt-4 rounded-2xl border border-border-main bg-main-bg p-4 text-start">
              <p className="text-xs font-black uppercase tracking-wider text-primary">{copy.fallback}</p>
              {session.fallbackMode === 'phone_dob' ? (
                <label className="mt-3 block text-xs font-black text-text-muted">
                  {copy.phone}
                  <input
                    aria-label={copy.phone}
                    inputMode="tel"
                    value={phone}
                    onChange={(event) => setPhone(event.target.value.slice(0, 32))}
                    className="mt-2 min-h-12 w-full rounded-xl border border-border-main bg-card-bg px-3 text-base font-bold text-main"
                  />
                </label>
              ) : (
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <label className="text-xs font-black text-text-muted">
                    {copy.firstName}
                    <input
                      aria-label={copy.firstName}
                      value={firstName}
                      onChange={(event) => setFirstName(event.target.value.slice(0, 100))}
                      className="mt-2 min-h-12 w-full rounded-xl border border-border-main bg-card-bg px-3 text-base font-bold text-main"
                    />
                  </label>
                  <label className="text-xs font-black text-text-muted">
                    {copy.lastName}
                    <input
                      aria-label={copy.lastName}
                      value={lastName}
                      onChange={(event) => setLastName(event.target.value.slice(0, 100))}
                      className="mt-2 min-h-12 w-full rounded-xl border border-border-main bg-card-bg px-3 text-base font-bold text-main"
                    />
                  </label>
                </div>
              )}
              <label className="mt-3 block text-xs font-black text-text-muted">
                {copy.birthDate}
                <input
                  aria-label={copy.birthDate}
                  type="date"
                  value={birthDate}
                  onChange={(event) => setBirthDate(event.target.value)}
                  className="mt-2 min-h-12 w-full rounded-xl border border-border-main bg-card-bg px-3 text-base font-bold text-main"
                />
              </label>
              <button
                type="button"
                disabled={fallbackBusy}
                onClick={() => void submitFallback()}
                className="mt-4 min-h-12 w-full rounded-xl bg-primary px-4 text-sm font-black text-on-primary disabled:opacity-50"
              >
                {fallbackBusy ? copy.checking : copy.confirm}
              </button>
              <p className="mt-3 text-[11px] font-semibold text-text-muted">{copy.privacy}</p>
            </div>
          )}
        </>
      )}

      {status === 'expired' && (
        <>
          <QrCode className="mx-auto text-text-muted" size={38} aria-hidden="true" />
          <p className="mt-4 font-black">{copy.expired}</p>
          <button type="button" onClick={() => void start()} className="mt-5 inline-flex min-h-12 items-center gap-2 rounded-elite-sm bg-primary px-5 text-sm font-black text-on-primary">
            <RefreshCw size={16} aria-hidden="true" /> {copy.newQr}
          </button>
        </>
      )}

      {error && status !== 'error' && <p role="alert" className="mt-4 font-black text-danger">{error}</p>}

      {status === 'error' && (
        <>
          <p role="alert" className="font-black text-danger">{error}</p>
          <button type="button" onClick={() => void start()} className="mt-5 inline-flex min-h-12 items-center gap-2 rounded-elite-sm border border-border-main px-5 text-sm font-black">
            <RefreshCw size={16} aria-hidden="true" /> {copy.retry}
          </button>
        </>
      )}

      <button type="button" onClick={() => void leave()} className="mt-5 min-h-12 w-full rounded-elite-sm border border-border-main px-5 text-sm font-black">
        {backLabel}
      </button>
    </section>
  );
};

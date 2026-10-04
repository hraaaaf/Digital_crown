import { useEffect, useMemo, useState } from 'react';
import { Nfc, QrCode, RefreshCw, ShieldCheck } from 'lucide-react';
import {
  stationPatientSessionService,
  type StationPatientSessionCreated,
} from '../../services/stationPatientSession';
import { StationAppointmentArrival, type StationFlowLanguage } from './StationAppointmentArrival';

const COPY = {
  fr: {
    tooMany: 'Trop de tentatives. Générez une nouvelle session ou demandez de l’aide.',
    disabled: '{copy.fallback} désactivée par le cabinet.',
    notConfirmed: 'Identification non confirmée. Vérifiez les informations ou demandez de l’aide.',
    unavailable: 'Identification indisponible. Prévenez l’équipe d’accueil.',
    disconnected: 'Connexion à la session interrompue.',
    preparing: '{copy.preparing}',
    private: '{copy.private}',
    qrAlt: 'QR d’identification Patient Companion',
    scan: '{copy.scan}',
    expires: (time: string) => `Le QR expire à ${time} et ne peut servir qu’une fois.`,
    nfc: '{copy.nfc}',
    noPhone: '{copy.noPhone}',
    fallback: '{copy.fallback}',
    phone: 'Téléphone', firstName: 'Prénom', lastName: 'Nom', birthDate: 'Date de naissance',
    checking: 'Vérification…', confirm: 'Confirmer mon identité',
    privacy: '{copy.privacy}',
    expired: '{copy.expired}', newQr: '{copy.newQr}', retry: '{copy.retry}',
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
  },
} as const;

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
}: {
  onBack: () => void;
  backLabel: string;
  language?: StationFlowLanguage;
}) => {
  const copy = COPY[language];
  const [session, setSession] = useState<StationPatientSessionCreated | null>(null);
  const [status, setStatus] = useState<'loading' | 'pending' | 'identified' | 'expired' | 'error'>('loading');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [fallbackOpen, setFallbackOpen] = useState(false);
  const [fallbackBusy, setFallbackBusy] = useState(false);
  const [birthDate, setBirthDate] = useState('');
  const [phone, setPhone] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  const start = async () => {
    setStatus('loading');
    setError('');
    setDisplayName('');
    setFallbackOpen(false);
    setBirthDate('');
    setPhone('');
    setFirstName('');
    setLastName('');
    try {
      const created = await stationPatientSessionService.create();
      setSession(created);
      setStatus('pending');
    } catch {
      setSession(null);
      setStatus('error');
      setError(copy.unavailable);
    }
  };

  useEffect(() => {
    void start();
  }, []);

  useEffect(() => {
    if (!session || status !== 'pending') return undefined;
    let cancelled = false;
    const poll = async () => {
      try {
        const next = await stationPatientSessionService.status(session.sessionId);
        if (cancelled) return;
        if (next.status === 'identified') {
          setDisplayName(next.displayName);
          setStatus('identified');
          return;
        }
        if (next.status === 'expired') setStatus('expired');
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
  }, [session, status]);

  useEffect(() => () => {
    if (session) void stationPatientSessionService.purge(session.sessionId).catch(() => undefined);
  }, [session]);

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
      setStatus('identified');
      setFallbackOpen(false);
    } catch (fallbackError) {
      setError(apiErrorDetail(fallbackError, language));
    } finally {
      setFallbackBusy(false);
    }
  };

  const leave = async () => {
    if (session) await stationPatientSessionService.purge(session.sessionId).catch(() => undefined);
    onBack();
  };

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
                className="mt-4 min-h-12 w-full rounded-xl bg-primary px-4 text-sm font-black text-card-bg disabled:opacity-50"
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
          <button type="button" onClick={() => void start()} className="mt-5 inline-flex min-h-12 items-center gap-2 rounded-elite-sm bg-primary px-5 text-sm font-black text-card-bg">
            <RefreshCw size={16} aria-hidden="true" /> {copy.newQr}
          </button>
        </>
      )}

      {error && status !== 'error' && <p role="alert" className="mt-4 font-black text-rose-700">{error}</p>}

      {status === 'error' && (
        <>
          <p role="alert" className="font-black text-rose-700">{error}</p>
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

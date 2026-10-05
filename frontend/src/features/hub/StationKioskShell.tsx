import { useEffect, useMemo, useState } from 'react';
import { CalendarCheck2, ChevronLeft, FileDown, HandHelping, Languages, ShieldCheck, TabletSmartphone } from 'lucide-react';
import { StationPatientIdentity } from './StationPatientIdentity';

type StationLanguage = 'fr' | 'ar' | 'en';
type StationScreen = 'home' | 'appointment' | 'documents' | 'help';

type Copy = {
  localeName: string;
  eyebrow: string;
  title: string;
  subtitle: string;
  secure: string;
  appointment: string;
  appointmentHint: string;
  documents: string;
  documentsHint: string;
  help: string;
  helpHint: string;
  building: string;
  back: string;
  privacy: string;
};

const COPY: Record<StationLanguage, Copy> = {
  fr: {
    localeName: 'Français',
    eyebrow: 'Digital Crown · Station d’accueil',
    title: 'Bienvenue au cabinet',
    subtitle: 'Comment pouvons-nous vous aider aujourd’hui ?',
    secure: 'Station sécurisée',
    appointment: 'J’ai rendez-vous',
    appointmentHint: 'Identification et arrivée au cabinet',
    documents: 'Retirer un document',
    documentsHint: 'Accès aux documents autorisés',
    help: 'Besoin d’aide',
    helpHint: 'Prévenir l’équipe d’accueil',
    building: 'Cette étape est en cours de construction.',
    back: 'Retour à l’accueil',
    privacy: 'Aucune donnée clinique n’est affichée sur cette station.',
  },
  ar: {
    localeName: 'العربية',
    eyebrow: 'Digital Crown · محطة الاستقبال',
    title: 'مرحباً بكم في العيادة',
    subtitle: 'كيف يمكننا مساعدتكم اليوم؟',
    secure: 'محطة استقبال آمنة',
    appointment: 'لدي موعد',
    appointmentHint: 'التعرّف وتأكيد الوصول إلى العيادة',
    documents: 'استلام وثيقة',
    documentsHint: 'الوصول إلى الوثائق المصرح بها',
    help: 'أحتاج إلى مساعدة',
    helpHint: 'إبلاغ فريق الاستقبال',
    building: 'هذه الخطوة قيد الإنشاء.',
    back: 'العودة إلى الاستقبال',
    privacy: 'لا يتم عرض أي بيانات سريرية على هذه المحطة.',
  },
  en: {
    localeName: 'English',
    eyebrow: 'Digital Crown · Welcome station',
    title: 'Welcome to the clinic',
    subtitle: 'How can we help you today?',
    secure: 'Secure welcome station',
    appointment: 'I have an appointment',
    appointmentHint: 'Identify yourself and confirm your arrival',
    documents: 'Collect a document',
    documentsHint: 'Access authorized documents',
    help: 'I need help',
    helpHint: 'Notify the reception team',
    building: 'This step is under construction.',
    back: 'Back to welcome',
    privacy: 'No clinical data is displayed on this station.',
  },
};

const ACTIONS: Array<{
  id: Exclude<StationScreen, 'home'>;
  icon: typeof CalendarCheck2;
  title: keyof Pick<Copy, 'appointment' | 'documents' | 'help'>;
  hint: keyof Pick<Copy, 'appointmentHint' | 'documentsHint' | 'helpHint'>;
}> = [
  { id: 'appointment', icon: CalendarCheck2, title: 'appointment', hint: 'appointmentHint' },
  { id: 'documents', icon: FileDown, title: 'documents', hint: 'documentsHint' },
  { id: 'help', icon: HandHelping, title: 'help', hint: 'helpHint' },
];

const clampIdleTimeout = (value: number) => Math.min(120_000, Math.max(30_000, value));

export const StationKioskShell = ({
  onAdminTap,
  idleTimeoutMs = 60_000,
}: {
  onAdminTap: () => void;
  idleTimeoutMs?: number;
}) => {
  const [language, setLanguage] = useState<StationLanguage>('fr');
  const [screen, setScreen] = useState<StationScreen>('home');
  const [activityTick, setActivityTick] = useState(0);
  const copy = COPY[language];
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  const timeoutMs = useMemo(() => clampIdleTimeout(idleTimeoutMs), [idleTimeoutMs]);

  useEffect(() => {
    if (screen === 'home') return;
    const timer = window.setTimeout(() => {
      setScreen('home');
    }, timeoutMs);
    return () => window.clearTimeout(timer);
  }, [activityTick, screen, timeoutMs]);

  const noteActivity = () => {
    if (screen !== 'home') setActivityTick((value) => value + 1);
  };

  return (
    <main
      data-workstation-experience="station"
      data-station-screen={screen}
      data-station-language={language}
      lang={language}
      dir={dir}
      onPointerDown={noteActivity}
      onKeyDown={noteActivity}
      className="relative min-h-screen overflow-x-hidden bg-main-bg text-main"
    >
      <div aria-hidden="true" className="pointer-events-none absolute -left-32 -top-36 h-80 w-80 rounded-full bg-primary/5 blur-3xl" />
      <div aria-hidden="true" className="pointer-events-none absolute -right-40 bottom-0 h-96 w-96 rounded-full bg-primary/5 blur-3xl" />

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-4 sm:px-6 sm:py-6 lg:px-10 lg:py-8">
        <header className="flex items-center justify-between gap-3">
          <button
            type="button"
            aria-label="Digital Crown"
            onClick={onAdminTap}
            className="flex min-h-12 min-w-12 items-center justify-center rounded-elite-sm border border-border-main bg-card-bg text-primary shadow-elite focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <TabletSmartphone size={24} aria-hidden="true" />
          </button>

          <div role="group" aria-label="Langue / Language / اللغة" className="flex items-center gap-1.5 rounded-elite-sm border border-border-main bg-card-bg p-1 shadow-elite">
            <Languages size={17} className="mx-1 text-text-muted" aria-hidden="true" />
            {(['fr', 'ar', 'en'] as StationLanguage[]).map((locale) => (
              <button
                key={locale}
                type="button"
                aria-label={COPY[locale].localeName}
                aria-pressed={language === locale}
                onClick={() => {
                  setLanguage(locale);
                  setScreen('home');
                }}
                className={`min-h-11 min-w-11 rounded-xl px-2.5 text-xs font-black uppercase transition-elite motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                  language === locale ? 'bg-primary text-on-primary' : 'text-text-muted hover:bg-primary/5 hover:text-main'
                }`}
              >
                {locale === 'ar' ? 'ع' : locale.toUpperCase()}
              </button>
            ))}
          </div>
        </header>

        <section className="mx-auto flex w-full max-w-5xl flex-1 flex-col justify-center py-8 sm:py-10 lg:py-12">
          <div className="text-center">
            <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary/5 px-4 py-2 text-xs font-black uppercase tracking-widest text-primary">
              <ShieldCheck size={15} aria-hidden="true" />
              {copy.secure}
            </div>
            <p className="mt-5 text-xs font-black uppercase tracking-widest text-primary">{copy.eyebrow}</p>
            <h1 className="mx-auto mt-3 max-w-3xl font-outfit text-3xl font-black tracking-tight sm:text-4xl lg:text-5xl">
              {screen === 'home' ? copy.title : copy[ACTIONS.find((action) => action.id === screen)?.title ?? 'appointment']}
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-base font-semibold leading-relaxed text-text-muted sm:text-lg">
              {screen === 'home' ? copy.subtitle : screen === 'appointment' ? copy.appointmentHint : copy.building}
            </p>
          </div>

          {screen === 'home' ? (
            <div className="mt-8 grid gap-3 sm:mt-10 sm:grid-cols-3 sm:gap-4">
              {ACTIONS.map(({ id, icon: Icon, title, hint }) => (
                <button
                  key={id}
                  type="button"
                  data-station-action={id}
                  onClick={() => setScreen(id)}
                  className="group min-h-40 rounded-elite-lg border border-border-main bg-card-bg p-5 text-start shadow-elite transition-elite motion-reduce:transition-none hover:-translate-y-0.5 motion-reduce:hover:translate-y-0 hover:border-primary/30 hover:shadow-elite-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary sm:min-h-48 sm:p-6"
                >
                  <span className="flex h-12 w-12 items-center justify-center rounded-elite-sm bg-primary/10 text-primary">
                    <Icon size={24} aria-hidden="true" />
                  </span>
                  <span className="mt-5 block font-outfit text-lg font-black tracking-tight sm:text-xl">{copy[title]}</span>
                  <span className="mt-2 block text-sm font-semibold leading-relaxed text-text-muted">{copy[hint]}</span>
                </button>
              ))}
            </div>
          ) : screen === 'appointment' ? (
            <StationPatientIdentity onBack={() => setScreen('home')} backLabel={copy.back} language={language} />
          ) : (
            <div className="mx-auto mt-9 w-full max-w-xl rounded-elite-lg border border-border-main bg-card-bg p-6 text-center shadow-elite sm:p-8">
              <button
                type="button"
                onClick={() => setScreen('home')}
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-elite-sm bg-primary px-5 text-sm font-black text-on-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              >
                <ChevronLeft size={18} className={dir === 'rtl' ? 'rotate-180' : ''} aria-hidden="true" />
                {copy.back}
              </button>
            </div>
          )}
        </section>

        <footer className="pb-1 text-center text-xs font-bold leading-relaxed text-text-muted">
          {copy.privacy}
        </footer>
      </div>
    </main>
  );
};

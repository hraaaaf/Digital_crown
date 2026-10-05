import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { BellRing, ShieldCheck, Volume2, VolumeX } from 'lucide-react';
import {
  stationWallDisplayService,
  type WallDisplaySnapshot,
} from '../../services/stationWallDisplay';

const POLL_MS = 2_000;
const WALL_MAX_VISIBLE_ENTRIES = 8;

const createWallAudioContext = (): AudioContext | null => {
  const AudioContextCtor = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  return AudioContextCtor ? new AudioContextCtor() : null;
};

const playBoundedChime = (context: AudioContext) => {
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.type = 'sine';
  oscillator.frequency.setValueAtTime(523.25, context.currentTime);
  oscillator.frequency.setValueAtTime(659.25, context.currentTime + 0.22);
  gain.gain.setValueAtTime(0.0001, context.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.18, context.currentTime + 0.03);
  gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.55);
  oscillator.connect(gain);
  gain.connect(context.destination);
  oscillator.start();
  oscillator.stop(context.currentTime + 0.56);
};

export const StationWallDisplay = () => {
  const [snapshot, setSnapshot] = useState<WallDisplaySnapshot | null>(null);
  const [failed, setFailed] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [clockTick, setClockTick] = useState(0);
  const lastChimedCallKey = useRef<string | null>(null);
  const refreshSequence = useRef(0);
  const audioContextRef = useRef<AudioContext | null>(null);

  const refresh = useCallback(async () => {
    const sequence = ++refreshSequence.current;
    try {
      const next = await stationWallDisplayService.snapshot();
      if (sequence !== refreshSequence.current) return;
      setSnapshot(next);
      setFailed(false);
    } catch {
      if (sequence !== refreshSequence.current) return;
      setFailed(true);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => { void refresh(); }, POLL_MS);
    return () => window.clearInterval(interval);
  }, [refresh]);

  useEffect(() => {
    if (!snapshot?.currentCall) return;
    const interval = window.setInterval(() => setClockTick(value => value + 1), 250);
    return () => window.clearInterval(interval);
  }, [snapshot?.currentCall]);

  const activeCall = useMemo(() => {
    void clockTick;
    if (!snapshot?.currentCall) return null;
    return new Date(snapshot.currentCall.expiresAt).getTime() > Date.now()
      ? snapshot.currentCall
      : null;
  }, [clockTick, snapshot]);

  useEffect(() => {
    if (!soundEnabled || !activeCall) return;
    const context = audioContextRef.current;
    if (!context || context.state !== 'running') return;
    const callKey = `${activeCall.ticketNumber}:${activeCall.expiresAt}`;
    if (lastChimedCallKey.current === callKey) return;
    lastChimedCallKey.current = callKey;
    try {
      playBoundedChime(context);
    } catch {
      // Visual calling remains authoritative when browser audio is unavailable.
    }
  }, [activeCall, soundEnabled]);

  useEffect(() => () => {
    const context = audioContextRef.current;
    audioContextRef.current = null;
    if (context && context.state !== 'closed') void context.close();
  }, []);

  const toggleSound = useCallback(async () => {
    if (soundEnabled) {
      setSoundEnabled(false);
      return;
    }
    try {
      const context = audioContextRef.current ?? createWallAudioContext();
      if (!context) return;
      audioContextRef.current = context;
      if (context.state === 'suspended') await context.resume();
      setSoundEnabled(context.state === 'running');
    } catch {
      setSoundEnabled(false);
    }
  }, [soundEnabled]);

  const isLoading = snapshot === null && !failed;
  const visibleEntries = (snapshot?.entries ?? []).slice(0, WALL_MAX_VISIBLE_ENTRIES);
  const displayState = failed ? 'unavailable' : isLoading ? 'loading' : activeCall ? 'calling' : 'waiting';

  return (
    <main
      data-workstation-experience="station-wall"
      data-wall-state={displayState}
      className="min-h-screen bg-main-bg text-main"
    >
      <div className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col px-5 py-5 sm:px-8 sm:py-7 lg:px-12 lg:py-10">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border-main pb-5">
          <div>
            <div className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.2em] text-primary">
              <ShieldCheck size={16} aria-hidden="true" />
              Digital Crown
            </div>
            <h1 className="mt-2 font-outfit text-2xl font-black tracking-tight sm:text-3xl">
              Salle d’attente
            </h1>
          </div>

          <button
            type="button"
            aria-pressed={soundEnabled}
            onClick={() => { void toggleSound(); }}
            className="inline-flex min-h-12 items-center gap-2 rounded-elite-sm border border-border-main bg-card-bg px-4 text-sm font-black shadow-elite focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            {soundEnabled ? <Volume2 size={18} aria-hidden="true" /> : <VolumeX size={18} aria-hidden="true" />}
            {soundEnabled ? 'Son activé' : 'Activer le son'}
          </button>
        </header>

        <section className="flex flex-1 flex-col justify-center py-7 sm:py-10">
          {isLoading ? (
            <div role="status" className="mx-auto w-full max-w-2xl rounded-elite-lg border border-border-main bg-card-bg p-8 text-center shadow-elite">
              <p className="font-outfit text-2xl font-black">Synchronisation de l’affichage…</p>
              <p className="mt-3 text-sm font-semibold text-text-muted">Aucun état d’attente n’est supposé avant la première lecture.</p>
            </div>
          ) : failed ? (
            <div role="status" className="mx-auto w-full max-w-2xl rounded-elite-lg border border-border-main bg-card-bg p-8 text-center shadow-elite">
              <p className="font-outfit text-2xl font-black">Affichage momentanément indisponible</p>
              <p className="mt-3 text-sm font-semibold text-text-muted">Merci de vous adresser à l’accueil.</p>
            </div>
          ) : activeCall ? (
            <div
              aria-live="assertive"
              className="mx-auto w-full max-w-5xl rounded-[2rem] border border-primary/20 bg-card-bg p-6 text-center shadow-elite sm:p-10 lg:p-14"
            >
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary sm:h-20 sm:w-20">
                <BellRing size={34} aria-hidden="true" />
              </div>
              <p className="mt-6 text-sm font-black uppercase tracking-[0.24em] text-primary">Patient appelé</p>
              <div className="mt-4 font-outfit text-6xl font-black tracking-tight sm:text-8xl lg:text-9xl">
                N° {activeCall.ticketNumber}
              </div>
              {activeCall.identityLabel && (
                <div className="mt-4 text-2xl font-black text-text-muted sm:text-4xl">{activeCall.identityLabel}</div>
              )}
              <p className="mx-auto mt-7 max-w-2xl text-lg font-semibold text-text-muted sm:text-2xl">
                Merci de vous présenter à l’accueil.
              </p>
            </div>
          ) : (
            <div className="mx-auto w-full max-w-6xl">
              <div className="text-center">
                <p className="text-sm font-black uppercase tracking-[0.2em] text-primary">En attente</p>
                <h2 className="mt-3 font-outfit text-3xl font-black tracking-tight sm:text-5xl">Merci de patienter</h2>
                <p className="mt-3 text-sm font-semibold text-text-muted sm:text-base">
                  L’équipe vous appellera sur cet écran.
                </p>
              </div>

              <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4">
                {visibleEntries.map(entry => (
                  <div
                    key={`${entry.ticketNumber}-${entry.identityLabel ?? 'number-only'}`}
                    className="rounded-elite-lg border border-border-main bg-card-bg p-4 text-center shadow-elite sm:p-6"
                  >
                    <p className="text-xs font-black uppercase tracking-widest text-text-muted">N° de file</p>
                    <p className="mt-2 font-outfit text-3xl font-black sm:text-4xl">{entry.ticketNumber}</p>
                    {entry.identityLabel && (
                      <p className="mt-2 text-base font-black text-primary sm:text-lg">{entry.identityLabel}</p>
                    )}
                  </div>
                ))}
              </div>

              {(snapshot?.waitingCount ?? 0) > visibleEntries.length && (
                <p className="mt-5 text-center text-xs font-semibold text-text-muted">
                  Certaines arrivées sont prises en charge directement par l’accueil.
                </p>
              )}
            </div>
          )}
        </section>

        <footer className="border-t border-border-main pt-4 text-center text-xs font-bold text-text-muted">
          {snapshot?.identityMode === 'full_name'
            ? 'Affichage public configuré avec nom complet · aucune donnée clinique'
            : snapshot?.identityMode === 'number_only'
              ? 'Affichage public par numéro uniquement · aucune donnée clinique'
              : 'Affichage public pseudonymisé · aucune donnée clinique'}
        </footer>
      </div>
    </main>
  );
};

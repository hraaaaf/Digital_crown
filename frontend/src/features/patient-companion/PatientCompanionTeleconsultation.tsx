import { useCallback, useEffect, useRef, useState } from 'react';
import { Camera, Loader2, PhoneOff, RefreshCcw, Video } from 'lucide-react';

import type { PatientPairing } from './PatientCompanionStorage';
import {
  PatientCompanionTeleconsultTransport,
  type TeleconsultSession,
  type TeleconsultSignal,
} from './PatientCompanionTeleconsultTransport';

type Props = {
  pairing: PatientPairing;
  enabled: boolean;
};

const terminalStates = new Set(['ENDED', 'REJECTED', 'EXPIRED', 'FAILED']);

const waitForIceGathering = (peer: RTCPeerConnection, timeoutMs = 5000) => new Promise<void>(resolve => {
  if (peer.iceGatheringState === 'complete') {
    resolve();
    return;
  }
  let settled = false;
  const finish = () => {
    if (settled) return;
    settled = true;
    peer.removeEventListener('icegatheringstatechange', onChange);
    resolve();
  };
  const onChange = () => {
    if (peer.iceGatheringState === 'complete') finish();
  };
  peer.addEventListener('icegatheringstatechange', onChange);
  window.setTimeout(finish, timeoutMs);
});

function sessionLabel(state: TeleconsultSession['state']): string {
  if (state === 'CREATED') return 'Préparation par le cabinet';
  if (state === 'CONNECTED') return 'En consultation';
  if (state === 'NEGOTIATING') return 'Connexion en cours';
  if (state === 'WAITING_PATIENT' || state === 'WAITING_STAFF') return 'Prête à rejoindre';
  if (state === 'ENDED') return 'Terminée';
  if (state === 'EXPIRED') return 'Expirée';
  if (state === 'REJECTED') return 'Refusée';
  return 'Connexion impossible';
}

export function PatientCompanionTeleconsultation({ pairing, enabled }: Props) {
  const [sessions, setSessions] = useState<TeleconsultSession[]>([]);
  const [active, setActive] = useState<TeleconsultSession | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [mediaStarted, setMediaStarted] = useState(false);
  const peerRef = useRef<RTCPeerConnection | null>(null);
  const sessionRef = useRef<TeleconsultSession | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const remoteStreamRef = useRef<MediaStream | null>(null);
  const localVideoRef = useRef<HTMLVideoElement | null>(null);
  const remoteVideoRef = useRef<HTMLVideoElement | null>(null);
  const cursorRef = useRef<string | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const connectedReportedRef = useRef(false);
  const failedReportedRef = useRef(false);
  const refreshBusyRef = useRef(false);
  const syncBusyRef = useRef(false);

  const setCurrent = (session: TeleconsultSession | null) => {
    sessionRef.current = session;
    setActive(session);
  };

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const cleanupPeer = useCallback(() => {
    stopPolling();
    peerRef.current?.close();
    peerRef.current = null;
    for (const track of localStreamRef.current?.getTracks() || []) track.stop();
    localStreamRef.current = null;
    remoteStreamRef.current = null;
    if (localVideoRef.current) localVideoRef.current.srcObject = null;
    if (remoteVideoRef.current) remoteVideoRef.current.srcObject = null;
    cursorRef.current = null;
    connectedReportedRef.current = false;
    failedReportedRef.current = false;
    setMediaStarted(false);
  }, [stopPolling]);

  useEffect(() => cleanupPeer, [cleanupPeer]);

  useEffect(() => {
    if (mediaStarted && localVideoRef.current && localStreamRef.current) localVideoRef.current.srcObject = localStreamRef.current;
    if (mediaStarted && remoteVideoRef.current) remoteVideoRef.current.srcObject = remoteStreamRef.current;
  }, [mediaStarted]);

  const refresh = useCallback(async () => {
    if (!enabled || !pairing.remoteTransport || refreshBusyRef.current) return;
    refreshBusyRef.current = true;
    try {
      const items = await PatientCompanionTeleconsultTransport.list(pairing);
      setSessions(items);
      if (active) {
        const next = items.find(item => item.session_id === active.session_id);
        if (next) setCurrent(next);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Téléconsultation indisponible.');
    } finally {
      refreshBusyRef.current = false;
    }
  }, [active, enabled, pairing]);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const processSignal = useCallback(async (signal: TeleconsultSignal, peer: RTCPeerConnection) => {
    if (signal.signal_type === 'answer') {
      await peer.setRemoteDescription(signal.payload as unknown as RTCSessionDescriptionInit);
      return;
    }
    if (signal.signal_type === 'ice') {
      const candidate = signal.payload as unknown as RTCIceCandidateInit;
      if (candidate?.candidate) await peer.addIceCandidate(candidate);
    }
  }, []);

  const syncActive = useCallback(async () => {
    const current = sessionRef.current;
    if (!current || !peerRef.current || syncBusyRef.current) return;
    syncBusyRef.current = true;
    try {
      const result = await PatientCompanionTeleconsultTransport.sync(
        pairing,
        current.session_id,
        cursorRef.current,
      );
      setCurrent(result.session);
      for (const signal of result.signals) {
        await processSignal(signal, peerRef.current);
        cursorRef.current = signal.signal_id;
      }
      if (terminalStates.has(result.session.state)) cleanupPeer();
    } catch (error) {
      cleanupPeer();
      setMessage(error instanceof Error ? error.message : 'Synchronisation de la consultation impossible.');
    } finally {
      syncBusyRef.current = false;
    }
  }, [cleanupPeer, pairing, processSignal]);

  const join = async (session: TeleconsultSession) => {
    if (!enabled || !pairing.remoteTransport || busy) return;
    if (!navigator.mediaDevices?.getUserMedia || typeof RTCPeerConnection === 'undefined' || typeof MediaStream === 'undefined') {
      setMessage('La caméra ou le microphone ne sont pas disponibles sur cet appareil.');
      return;
    }
    setBusy(true);
    setMessage('');
    cleanupPeer();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      localStreamRef.current = stream;
      if (localVideoRef.current) localVideoRef.current.srcObject = stream;

      const joined = await PatientCompanionTeleconsultTransport.join(pairing, session.session_id);
      setCurrent(joined);
      const iceServers = await PatientCompanionTeleconsultTransport.iceConfig(pairing, session.session_id);

      const peer = new RTCPeerConnection({ iceServers });
      peerRef.current = peer;
      const remoteStream = new MediaStream();
      remoteStreamRef.current = remoteStream;
      for (const track of stream.getTracks()) peer.addTrack(track, stream);

      peer.ontrack = event => {
        for (const track of event.streams[0]?.getTracks() || [event.track]) {
          remoteStream.addTrack(track);
        }
        if (remoteVideoRef.current) remoteVideoRef.current.srcObject = remoteStream;
      };

      peer.onconnectionstatechange = () => {
        if (peer.connectionState === 'connected' && !connectedReportedRef.current) {
          connectedReportedRef.current = true;
          void PatientCompanionTeleconsultTransport.connected(pairing, session.session_id)
.then(setCurrent)
            .catch(() => setMessage('Connexion établie, confirmation du cabinet en attente.'));
        } else if (peer.connectionState === 'failed' && !failedReportedRef.current) {
          failedReportedRef.current = true;
          const current = sessionRef.current;
          if (!current) {
            cleanupPeer();
            setMessage('Connexion impossible sur ce réseau.');
            return;
          }
          void PatientCompanionTeleconsultTransport.failed(pairing, current.session_id, 'PEER_CONNECTION_FAILED')
            .then(failed => {
              setCurrent(failed);
              cleanupPeer();
              setMessage('Connexion impossible sur ce réseau.');
            })
            .catch(() => {
              cleanupPeer();
              setMessage('Connexion impossible sur ce réseau.');
            });
        }
      };

      const offer = await peer.createOffer();
      await peer.setLocalDescription(offer);
      await waitForIceGathering(peer);
      const localDescription = peer.localDescription;
      if (!localDescription) throw new Error('Préparation de la connexion impossible.');
      await PatientCompanionTeleconsultTransport.signal(
        pairing,
        session.session_id,
        'offer',
        { type: localDescription.type, sdp: localDescription.sdp || '' },
      );

      setMediaStarted(true);
      pollTimerRef.current = window.setInterval(() => void syncActive(), 1500);
      setMessage('Connexion au cabinet en cours…');
    } catch (error) {
      cleanupPeer();
      const name = error instanceof DOMException ? error.name : '';
      setMessage(
        name === 'NotAllowedError'
          ? 'Autorisez la caméra et le microphone pour rejoindre la consultation.'
          : error instanceof Error ? error.message : 'Impossible de rejoindre la consultation.',
      );
    } finally {
      setBusy(false);
    }
  };

  const reject = async (session: TeleconsultSession) => {
    if (busy) return;
    setBusy(true);
    setMessage('');
    try {
      const rejected = await PatientCompanionTeleconsultTransport.reject(pairing, session.session_id);
      setCurrent(rejected);
      setMessage('Téléconsultation refusée.');
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Refus non confirmé.');
    } finally {
      setBusy(false);
    }
  };

  const end = async () => {
    const session = sessionRef.current;
    cleanupPeer();
    if (!session) return;
    try {
      const ended = await PatientCompanionTeleconsultTransport.end(pairing, session.session_id);
      setCurrent(ended);
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Fin de consultation non confirmée.');
    }
  };

  const available = sessions.filter(item => !terminalStates.has(item.state));
  const shown = active || available[0] || null;

  return (
    <section data-pc09-patient className="mt-4 rounded-[1.5rem] border border-border-main bg-card-bg p-4" aria-label="Téléconsultation">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-primary"><Video size={17} /><p className="text-[10px] font-black uppercase tracking-[0.14em]">Téléconsultation</p></div>
          <h3 className="mt-1 text-lg font-black">Consultation vidéo</h3>
          <p className="mt-1 text-[11px] font-bold leading-relaxed text-text-muted">En rejoignant, vous acceptez cette téléconsultation. La caméra et le microphone s’activent uniquement après votre action. Aucun enregistrement.</p>
        </div>
        <button type="button" onClick={() => void refresh()} disabled={!enabled || busy} aria-label="Actualiser" className="grid min-h-11 min-w-11 place-items-center rounded-full border border-border-main bg-background text-primary disabled:opacity-40">
          {busy ? <Loader2 className="animate-spin" size={18} /> : <RefreshCcw size={18} />}
        </button>
      </div>

      {!pairing.remoteTransport && (
        <p className="mt-3 rounded-xl bg-amber-50 px-3 py-2.5 text-[11px] font-black text-amber-800">Cette fonction sera disponible après activation complète de votre accès.</p>
      )}

      {!shown && (
        <div className="mt-3 rounded-2xl border border-border-main bg-background px-4 py-5 text-center">
          <Camera size={22} className="mx-auto text-primary" />
          <p className="mt-2 text-sm font-black">Aucune téléconsultation en attente</p>
          <p className="mt-1 text-[11px] font-bold text-text-muted">Une consultation apparaîtra ici lorsqu’elle sera ouverte par votre cabinet.</p>
        </div>
      )}

      {shown && (
        <div className="mt-3">
          <div className="rounded-2xl border border-border-main bg-background p-3">
            <div className="flex items-center justify-between gap-3">
              <div><p className="text-sm font-black">{sessionLabel(shown.state)}</p><p className="mt-1 text-[10px] font-bold text-text-muted">Créée le {new Date(shown.created_at).toLocaleString()}</p></div>
              {!mediaStarted && !terminalStates.has(shown.state) && (
                <div className="flex flex-col gap-2 sm:flex-row">
                  <button type="button" onClick={() => void join(shown)} disabled={busy || !enabled} className="min-h-[48px] rounded-xl bg-primary px-4 text-xs font-black text-white disabled:opacity-50">Accepter et rejoindre</button>
                  <button type="button" onClick={() => void reject(shown)} disabled={busy || !enabled} className="min-h-[44px] rounded-xl border border-border-main bg-card-bg px-4 text-xs font-black text-text-muted disabled:opacity-50">Refuser</button>
                </div>
              )}
            </div>
          </div>

          {mediaStarted && (
            <>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <div className="overflow-hidden rounded-2xl border border-border-main bg-black">
                  <video ref={remoteVideoRef} autoPlay playsInline className="aspect-video w-full object-cover" aria-label="Vidéo du cabinet" />
                  <p className="bg-black/80 px-3 py-2 text-[10px] font-black text-white">Cabinet</p>
                </div>
                <div className="overflow-hidden rounded-2xl border border-border-main bg-black">
                  <video ref={localVideoRef} autoPlay muted playsInline className="aspect-video w-full object-cover" aria-label="Votre caméra" />
                  <p className="bg-black/80 px-3 py-2 text-[10px] font-black text-white">Vous</p>
                </div>
              </div>
              <button type="button" onClick={() => void end()} className="mt-3 inline-flex min-h-[48px] w-full items-center justify-center gap-2 rounded-xl bg-rose-700 px-4 text-xs font-black text-white"><PhoneOff size={16} /> Terminer</button>
            </>
          )}
        </div>
      )}

      {message && <p role="status" className="mt-3 rounded-xl bg-primary/5 px-3 py-2.5 text-[11px] font-black text-primary">{message}</p>}
    </section>
  );
}

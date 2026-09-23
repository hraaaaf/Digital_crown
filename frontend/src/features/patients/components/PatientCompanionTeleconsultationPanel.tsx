import { useCallback, useEffect, useRef, useState } from 'react';
import { Loader2, PhoneOff, RefreshCcw, Video } from 'lucide-react';

import { api } from '../../../services/api';

type Access = { access_id: string; relationship_type: string; created_at: string };
type Session = {
  session_id: string;
  access_id?: string | null;
  state: 'WAITING_PATIENT' | 'WAITING_STAFF' | 'NEGOTIATING' | 'CONNECTED' | 'ENDED' | 'REJECTED' | 'EXPIRED' | 'FAILED';
  created_at: string;
  expires_at: string;
  connected_at?: string | null;
};
type Signal = {
  signal_id: string;
  signal_type: 'offer' | 'answer' | 'ice';
  payload: Record<string, unknown>;
  sender_kind: 'PATIENT' | 'STAFF';
};

const terminal = new Set(['ENDED', 'REJECTED', 'EXPIRED', 'FAILED']);

export function PatientCompanionTeleconsultationPanel({ patientId }: { patientId: number }) {
  const [accesses, setAccesses] = useState<Access[]>([]);
  const [selectedAccess, setSelectedAccess] = useState('');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [active, setActive] = useState<Session | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [mediaStarted, setMediaStarted] = useState(false);
  const peerRef = useRef<RTCPeerConnection | null>(null);
  const sessionRef = useRef<Session | null>(null);
  const accessRef = useRef('');
  const localStreamRef = useRef<MediaStream | null>(null);
  const remoteStreamRef = useRef<MediaStream>(new MediaStream());
  const localVideoRef = useRef<HTMLVideoElement | null>(null);
  const remoteVideoRef = useRef<HTMLVideoElement | null>(null);
  const cursorRef = useRef<string | null>(null);
  const pollRef = useRef<number | null>(null);
  const connectedReportedRef = useRef(false);

  const setCurrent = (session: Session | null) => {
    sessionRef.current = session;
    setActive(session);
  };

  const stopPeer = useCallback(() => {
    if (pollRef.current !== null) window.clearInterval(pollRef.current);
    pollRef.current = null;
    peerRef.current?.close();
    peerRef.current = null;
    for (const track of localStreamRef.current?.getTracks() || []) track.stop();
    localStreamRef.current = null;
    remoteStreamRef.current = new MediaStream();
    if (localVideoRef.current) localVideoRef.current.srcObject = null;
    if (remoteVideoRef.current) remoteVideoRef.current.srcObject = null;
    cursorRef.current = null;
    connectedReportedRef.current = false;
    setMediaStarted(false);
  }, []);

  useEffect(() => stopPeer, [stopPeer]);

  useEffect(() => {
    if (mediaStarted && localVideoRef.current && localStreamRef.current) localVideoRef.current.srcObject = localStreamRef.current;
    if (mediaStarted && remoteVideoRef.current) remoteVideoRef.current.srcObject = remoteStreamRef.current;
  }, [mediaStarted]);

  const load = useCallback(async () => {
    const response = await api.get('/patient-companion/admin/patients/' + patientId + '/teleconsultations');
    const nextAccesses = Array.isArray(response.data?.accesses) ? response.data.accesses : [];
    const nextSessions = Array.isArray(response.data?.items) ? response.data.items : [];
    setAccesses(nextAccesses);
    setSessions(nextSessions);
    setSelectedAccess(value => value || nextAccesses[0]?.access_id || '');
    if (sessionRef.current) {
      const next = nextSessions.find((item: Session) => item.session_id === sessionRef.current?.session_id);
      if (next) setCurrent(next);
    }
  }, [patientId]);

  useEffect(() => { void load().catch(() => setMessage('Impossible de charger les téléconsultations.')); }, [load]);

  const sendSignal = useCallback(async (type: Signal['signal_type'], payload: Record<string, unknown>) => {
    const session = sessionRef.current;
    const accessId = accessRef.current;
    if (!session || !accessId) return;
    await api.post('/patient-companion/admin/patients/' + patientId + '/teleconsultations/' + session.session_id + '/signals', {
      access_id: accessId,
      client_signal_id: crypto.randomUUID(),
      signal_type: type,
      payload,
    });
  }, [patientId]);

  const poll = useCallback(async () => {
    const session = sessionRef.current;
    const accessId = accessRef.current;
    const peer = peerRef.current;
    if (!session || !accessId || !peer) return;
    const response = await api.get('/patient-companion/admin/patients/' + patientId + '/teleconsultations/' + session.session_id + '/signals', {
      params: { access_id: accessId, after_signal_id: cursorRef.current || undefined },
    });
    const nextSession = response.data?.session as Session;
    if (nextSession) {
      setCurrent(nextSession);
      if (terminal.has(nextSession.state)) stopPeer();
    }
    const signals: Signal[] = Array.isArray(response.data?.signals) ? response.data.signals : [];
    for (const signal of signals) {
      if (signal.signal_type === 'offer') {
        await peer.setRemoteDescription(signal.payload as RTCSessionDescriptionInit);
        const answer = await peer.createAnswer();
        await peer.setLocalDescription(answer);
        await sendSignal('answer', { type: answer.type, sdp: answer.sdp || '' });
      } else if (signal.signal_type === 'ice') {
        const candidate = signal.payload as unknown as RTCIceCandidateInit;
        if (candidate?.candidate) await peer.addIceCandidate(candidate);
      }
      cursorRef.current = signal.signal_id;
    }
  }, [patientId, sendSignal, stopPeer]);

  const startMedia = async (session: Session, accessId: string) => {
    if (!navigator.mediaDevices?.getUserMedia || typeof RTCPeerConnection === 'undefined') {
      throw new Error('Caméra ou microphone indisponible sur cet appareil.');
    }
    stopPeer();
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    localStreamRef.current = stream;
    if (localVideoRef.current) localVideoRef.current.srcObject = stream;

    const peer = new RTCPeerConnection({ iceServers: [] });
    peerRef.current = peer;
    accessRef.current = accessId;
    setCurrent(session);
    for (const track of stream.getTracks()) peer.addTrack(track, stream);

    peer.ontrack = event => {
      for (const track of event.streams[0]?.getTracks() || [event.track]) remoteStreamRef.current.addTrack(track);
      if (remoteVideoRef.current) remoteVideoRef.current.srcObject = remoteStreamRef.current;
    };
    peer.onicecandidate = event => {
      if (event.candidate) void sendSignal('ice', event.candidate.toJSON() as unknown as Record<string, unknown>);
    };
    peer.onconnectionstatechange = () => {
      if (peer.connectionState === 'connected' && !connectedReportedRef.current) {
        connectedReportedRef.current = true;
        const current = sessionRef.current;
        if (!current) return;
        void api.post('/patient-companion/admin/patients/' + patientId + '/teleconsultations/' + current.session_id + '/connected', {
          access_id: accessRef.current,
        }).then(response => setCurrent(response.data.session)).catch(() => setMessage('Confirmation de connexion en attente.'));
      } else if (peer.connectionState === 'failed') {
        setMessage('Connexion impossible sur ce réseau.');
      }
    };

    await api.post('/patient-companion/admin/patients/' + patientId + '/teleconsultations/' + session.session_id + '/join', { access_id: accessId });
    setMediaStarted(true);
    pollRef.current = window.setInterval(() => void poll().catch(() => setMessage('Connexion au patient interrompue.')), 1000);
  };

  const create = async () => {
    if (!selectedAccess || busy) return;
    setBusy(true);
    setMessage('');
    try {
      const response = await api.post('/patient-companion/admin/patients/' + patientId + '/teleconsultations', {
        access_id: selectedAccess,
        ttl_minutes: 60,
      });
      const session = { ...(response.data.session as Session), access_id: selectedAccess };
      setSessions(items => [session, ...items]);
      await startMedia(session, selectedAccess);
      setMessage('En attente du patient…');
    } catch (error: any) {
      const name = error instanceof DOMException ? error.name : '';
      setMessage(name === 'NotAllowedError'
        ? 'Autorisez la caméra et le microphone pour démarrer.'
        : error?.response?.data?.detail || error?.message || 'Impossible de démarrer la consultation.');
    } finally {
      setBusy(false);
    }
  };

  const resume = async (session: Session) => {
    const accessId = session.access_id || selectedAccess || accesses[0]?.access_id;
    if (!accessId) return;
    setBusy(true);
    setMessage('');
    try {
      await startMedia(session, accessId);
      setMessage('En attente du patient…');
    } catch (error: any) {
      setMessage(error?.message || 'Impossible d’ouvrir la consultation.');
    } finally {
      setBusy(false);
    }
  };

  const end = async () => {
    const session = sessionRef.current;
    const accessId = accessRef.current;
    stopPeer();
    if (!session || !accessId) return;
    try {
      const response = await api.post('/patient-companion/admin/patients/' + patientId + '/teleconsultations/' + session.session_id + '/end', { access_id: accessId });
      setCurrent(response.data.session);
      await load();
    } catch {
      setMessage('Fin de consultation non confirmée.');
    }
  };

  const currentAvailable = sessions.find(item => !terminal.has(item.state) && (!selectedAccess || item.access_id === selectedAccess));

  return (
    <section data-pc09-staff className="rounded-2xl sm:rounded-[1.75rem] border border-border-main bg-card-bg p-4 sm:p-5 md:p-6 shadow-elite">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-primary"><Video size={18} /></div>
          <h3 className="mt-1 text-lg font-black text-main">Téléconsultation</h3>
          <p className="mt-1 text-xs font-medium text-text-muted">Consultation vidéo avec le patient.</p>
        </div>
        <button type="button" onClick={() => void load()} aria-label="Actualiser" className="grid min-h-11 min-w-11 place-items-center rounded-xl border border-border-main bg-background text-primary">
          <RefreshCcw size={17} />
        </button>
      </div>

      {accesses.length > 1 && !mediaStarted && (
        <label className="mt-4 block">
          <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Accès</span>
          <select value={selectedAccess} onChange={event => setSelectedAccess(event.target.value)} className="mt-1.5 min-h-11 w-full rounded-xl border border-border-main bg-background px-3 text-sm font-bold">
            {accesses.map(item => <option key={item.access_id} value={item.access_id}>{item.relationship_type === 'SELF' ? 'Patient' : item.relationship_type}</option>)}
          </select>
        </label>
      )}

      {!accesses.length && <p className="mt-4 rounded-xl bg-amber-50 px-3 py-2.5 text-xs font-bold text-amber-800">Aucun accès Patient Companion actif.</p>}

      {!mediaStarted && accesses.length > 0 && (
        <button type="button" onClick={() => currentAvailable ? void resume(currentAvailable) : void create()} disabled={busy} className="mt-4 min-h-[48px] w-full rounded-xl bg-primary px-4 text-xs font-black text-white disabled:opacity-50">
          {busy ? <Loader2 className="mx-auto animate-spin" size={18} /> : currentAvailable ? 'Ouvrir la consultation' : 'Démarrer une téléconsultation'}
        </button>
      )}

      {mediaStarted && (
        <>
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            <div className="overflow-hidden rounded-2xl border border-border-main bg-black"><video ref={remoteVideoRef} autoPlay playsInline className="aspect-video w-full object-cover" /><p className="bg-black/80 px-3 py-2 text-[10px] font-black text-white">Patient</p></div>
            <div className="overflow-hidden rounded-2xl border border-border-main bg-black"><video ref={localVideoRef} autoPlay muted playsInline className="aspect-video w-full object-cover" /><p className="bg-black/80 px-3 py-2 text-[10px] font-black text-white">Cabinet</p></div>
          </div>
          <div className="mt-3 flex items-center justify-between gap-3 rounded-xl border border-border-main bg-background px-3 py-2.5">
            <p className="text-xs font-black">{active?.state === 'CONNECTED' ? 'En consultation' : 'Connexion en cours'}</p>
            <button type="button" onClick={() => void end()} className="inline-flex min-h-[44px] items-center gap-2 rounded-xl bg-rose-700 px-3 text-xs font-black text-white"><PhoneOff size={15} /> Terminer</button>
          </div>
        </>
      )}

      {message && <p role="status" className="mt-3 rounded-xl bg-primary/5 px-3 py-2.5 text-xs font-bold text-primary">{message}</p>}
    </section>
  );
}

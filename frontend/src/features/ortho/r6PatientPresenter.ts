import type { OrthoLongitudinalCompare } from './orthoLongitudinalCompare';
import { trustedR6Comparison, type R6Trajectory, type R6SourceRef } from './r6ThreeTimepoints';
import { API_BASE } from '../../services/api';

/**
 * LOT07 R6 / 07.1.D — patient-facing projection, never a new clinical source.
 * No notes, author, token, patient name, free text, media blob or automated claim.
 */
export type R6PresenterSnapshot = Readonly<{
  patientId: number;
  caseId: number;
  userId: string;
  pair: readonly [number, number];
  points: readonly Readonly<{
    ordinal: number;
    occurred_at: string;
    sources: readonly R6SourceRef[];
  }>[];
}>;

/**
 * Backend /auth/me may supply a numeric database ID while AppUser extends
 * Supabase's string ID type. Accept only actual nonempty strings or positive
 * safe integers, then compare a single canonical string in all lifecycle gates.
 */
export function normalizeR6PresenterUserId(value: unknown): string | null {
  if (typeof value === 'string') return value.trim() || null;
  if (typeof value === 'number' && Number.isSafeInteger(value) && value > 0) {
    return String(value);
  }
  return null;
}

export function projectR6Presenter(
  trajectory: R6Trajectory | null,
  comparison: OrthoLongitudinalCompare | null | undefined,
  userId: string | null | undefined,
  fromOrdinal: number | null,
  toOrdinal: number | null,
): R6PresenterSnapshot | null {
  if (!trajectory || !normalizeR6PresenterUserId(userId) ||
      ![0, 1].includes(fromOrdinal ?? -1) || ![1, 2].includes(toOrdinal ?? -1) ||
      fromOrdinal! >= toOrdinal! ||
      !trustedR6Comparison(comparison, trajectory.patientId, trajectory.caseId, fromOrdinal, toOrdinal)) {
    return null;
  }
  const first=trajectory.points[fromOrdinal!];
  const last=trajectory.points[toOrdinal!];
  if (!first || !last ||
      first.id !== comparison!.from_timepoint.id ||
      last.id !== comparison!.to_timepoint.id ||
      Date.parse(first.occurred_at) !== Date.parse(comparison!.from_timepoint.occurred_at) ||
      Date.parse(last.occurred_at) !== Date.parse(comparison!.to_timepoint.occurred_at)) {
    return null;
  }
  return {
    patientId: trajectory.patientId, caseId: trajectory.caseId,
    userId: userId!,
    pair: [fromOrdinal!, toOrdinal!],
    points: trajectory.points.map(p=>({
      ordinal:p.ordinal, occurred_at:p.occurred_at,
      sources:p.sources.map(s=>({kind:s.kind,refId:s.refId})),
    })),
  };
}

const STALE_WINDOW_MS = 28_000;

/**
 * LOT07 B10: an empty backend-served document gets a real HTTP CSP sandbox
 * WITHOUT allow-same-origin. Its origin is opaque ('null'), so it cannot read
 * Cabinet localStorage/cookies, and it has no API client or clinical URL.
 *
 * Only a bounded, text-only projection travels over a MessageChannel after a
 * HELLO/READY handshake. No token, patient ID, clinical note or media blob.
 */
export class R6PresenterWindow {
  private readonly child: Window;
  private readonly channel: string;
  private readonly pagehide: () => void;
  private readonly onHello: (event: MessageEvent) => void;
  private port: MessagePort | null = null;
  private ready=false;
  private seq=0;
  private latest: Pick<R6PresenterSnapshot,'pair'|'points'> | null=null;
  private expiry: number | undefined;
  private heartbeatTimer: number | undefined;

  private constructor(child: Window, channel: string) {
    this.child=child;
    this.channel=channel;
    this.pagehide=()=>this.close();
    this.onHello=(event)=>{
      if(event.source!==this.child || event.origin!=='null' ||
         event.data?.type!=='DC_PRESENTER_HELLO' || event.data.channel!==this.channel ||
         this.port || this.child.closed)return;
      const bridge=new MessageChannel();
      this.port=bridge.port1;
      this.port.onmessage=(message)=>{
        if(message.data?.channel!==this.channel)return;
        if(message.data.type==='DC_PRESENTER_READY'){
          this.ready=true;
          this.sendLatest();
          this.startHeartbeat();
        }
      };
      this.port.start();
      // The target has a deliberately opaque origin; '*' is mandatory for
      // MessagePort transfer. No clinical content is included in this message.
      this.child.postMessage({type:'DC_PRESENTER_INIT',channel:this.channel},'*',[bridge.port2]);
    };
    window.addEventListener('message',this.onHello);
    window.addEventListener('pagehide',this.pagehide);
    this.refreshExpiry();
  }

  static open(snapshot: R6PresenterSnapshot): R6PresenterWindow | null {
    const bytes=new Uint8Array(16);
    crypto.getRandomValues(bytes);
    const hex=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
    const channel=[hex.slice(0,8),hex.slice(8,12),hex.slice(12,16),hex.slice(16,20),hex.slice(20)].join('-');
    const url=new URL(API_BASE+'/api/ortho/presenter-window');
    url.searchParams.set('origin',window.location.origin);
    url.searchParams.set('channel',channel);
    const child=window.open(url.href,'_blank','popup,width=1120,height=720');
    if(!child)return null;
    const presenter=new R6PresenterWindow(child,channel);
    if(!presenter.update(snapshot)){
      presenter.close();
      return null;
    }
    return presenter;
  }

  isOpen(): boolean {
    try {return !this.child.closed;}catch{return false;}
  }

  private startHeartbeat(): void {
    if(this.heartbeatTimer!==undefined)window.clearInterval(this.heartbeatTimer);
    const ping=()=>{
      if(!this.isOpen()){this.close();return;}
      try{this.port?.postMessage({type:'DC_PRESENTER_HEARTBEAT',channel:this.channel});}
      catch{this.close();}
    };
    ping();
    this.heartbeatTimer=window.setInterval(ping,2000);
  }

  private sendLatest(): void {
    if(!this.port || !this.ready || !this.latest || !this.isOpen())return;
    this.port.postMessage({
      type:'DC_PRESENTER_UPDATE',channel:this.channel,seq:++this.seq,
      snapshot:this.latest,
    });
  }

  update(snapshot: R6PresenterSnapshot): boolean {
    if(!this.isOpen()){this.close();return false;}
    this.latest={
      pair:[...snapshot.pair] as [number,number],
      points:snapshot.points.map(p=>({
        ordinal:p.ordinal,occurred_at:p.occurred_at,
        sources:p.sources.map(s=>({kind:s.kind,refId:s.refId})),
      })),
    };
    this.sendLatest();
    this.refreshExpiry();
    return true;
  }

  private refreshExpiry(): void {
    if(this.expiry!==undefined)window.clearTimeout(this.expiry);
    this.expiry=window.setTimeout(()=>this.close(),STALE_WINDOW_MS);
  }

  close(): void {
    window.removeEventListener('pagehide',this.pagehide);
    window.removeEventListener('message',this.onHello);
    if(this.expiry!==undefined)window.clearTimeout(this.expiry);
    if(this.heartbeatTimer!==undefined)window.clearInterval(this.heartbeatTimer);
    this.heartbeatTimer=undefined;
    try{this.port?.postMessage({type:'DC_PRESENTER_CLOSE',channel:this.channel});}catch{}
    this.port?.close();
    this.port=null;
    this.latest=null;
    try{this.child.close();}catch{/* may already be closed */}
  }
}

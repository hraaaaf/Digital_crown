import type { OrthoLongitudinalCompare } from './orthoLongitudinalCompare';
import { trustedR6Comparison, type R6Trajectory, type R6SourceRef } from './r6ThreeTimepoints';

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

const validUserId = (value: unknown): value is string => typeof value === 'string' && value.trim().length > 0;

export function projectR6Presenter(
  trajectory: R6Trajectory | null,
  comparison: OrthoLongitudinalCompare | null | undefined,
  userId: string | null | undefined,
  fromOrdinal: number | null,
  toOrdinal: number | null,
): R6PresenterSnapshot | null {
  if (!trajectory || !validUserId(userId) ||
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
 * Inert about:blank child. Parent owns lifecycle and refreshes its expiry.
 * No app bundle, auth storage, URL patient IDs, API clients or form controls.
 * If parent crashes, the popup removes its contents and closes on expiry.
 */
export class R6PresenterWindow {
  private readonly child: Window;
  private expiry: number | undefined;
  private readonly pagehide: () => void;

  private constructor(child: Window) {
    this.child=child;
    this.pagehide=()=>this.close();
    window.addEventListener('pagehide',this.pagehide);
  }

  static open(snapshot: R6PresenterSnapshot): R6PresenterWindow | null {
    const child=window.open('about:blank','_blank','popup,width=1120,height=720');
    if (!child) return null;
    try {
      child.opener=null;
      const presenter=new R6PresenterWindow(child);
      presenter.update(snapshot);
      return presenter;
    } catch {
      child.close();
      return null;
    }
  }

  isOpen(): boolean {
    try { return !this.child.closed && this.child.location.href==='about:blank'; }
    catch { return false; }
  }

  update(snapshot: R6PresenterSnapshot): boolean {
    if (!this.isOpen()) { this.close(); return false; }
    try {
      const doc=this.child.document;
      doc.title='Digital Crown · Présentation du suivi';
      const style=doc.createElement('style');
      style.textContent=`html{font-family:system-ui,Arial,sans-serif;background:#0d1b2a;color:#f5f8fc}
body{margin:0;padding:clamp(20px,5vw,70px)}header{border-bottom:1px solid #526175;padding-bottom:26px}
h1{font-size:clamp(24px,3vw,42px);margin:8px 0}
small,p{color:#cfdae9}small{letter-spacing:.13em;text-transform:uppercase}
main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:32px}
article{border:1px solid #566983;border-radius:18px;background:#1b3045;padding:22px;min-height:158px}
h2{font-size:30px;margin:0 0 12px}li{margin:8px 0;word-wrap:break-word}
footer{padding-top:32px;font-size:15px;color:#c5d2e2}
@media(max-width:650px){main{grid-template-columns:1fr}}`;
      const make=(tag: string,value: string,attr?:string)=>{
        const element=doc.createElement(tag);
        element.textContent=value;
        if(attr)element.setAttribute('data-testid',attr);
        return element;
      };
      const header=doc.createElement('header');
      header.append(
        make('small','Digital Crown · Présentation en lecture seule'),
        make('h1','Suivi orthodontique · T0 → T1 → T2'),
        make('p',`Comparaison sélectionnée : T${snapshot.pair[0]} → T${snapshot.pair[1]}`,'r6d-pair'),
      );
      const main=doc.createElement('main');
      main.setAttribute('data-testid','r6d-readonly-presenter');
      for (const point of snapshot.points) {
        const card=doc.createElement('article');
        card.setAttribute('data-r6d-ordinal',String(point.ordinal));
        const iso=new Date(point.occurred_at);
        card.append(
          make('h2','T'+point.ordinal),
          make('p',iso.toLocaleDateString('fr-FR',{year:'numeric',month:'long',day:'numeric'})),
        );
        const sources=doc.createElement('ul');
        for (const source of point.sources) {
          const label=source.kind==='CEPHALO'?'Céphalo':source.kind==='PANORAMIC'?'Panoramique':'Média';
          sources.appendChild(make('li',label+' · source #'+source.refId));
        }
        card.appendChild(sources);
        main.appendChild(card);
      }
      const footer=make('footer','Sources canoniques vérifiées. Lecture seule. Aucune interprétation clinique automatique.');
      const policy=doc.createElement('meta');
      policy.httpEquiv='Content-Security-Policy';
      policy.content="default-src 'none'; style-src 'unsafe-inline'; connect-src 'none'; form-action 'none'; base-uri 'none'";
      doc.head.replaceChildren(policy,style);
      doc.body.replaceChildren(header,main,footer);
      this.refreshExpiry();
      return true;
    } catch {
      this.close();
      return false;
    }
  }

  private refreshExpiry(): void {
    if (this.expiry!==undefined) this.child.clearTimeout(this.expiry);
    this.expiry=this.child.setTimeout(()=>{
      try { this.child.document.body.replaceChildren(); } catch { /* navigated */ }
      this.child.close();
    },STALE_WINDOW_MS);
  }

  close(): void {
    window.removeEventListener('pagehide',this.pagehide);
    try {
      if (this.expiry!==undefined) this.child.clearTimeout(this.expiry);
      this.child.document.body.replaceChildren();
      this.child.close();
    } catch {
      try { this.child.close(); } catch { /* already gone */ }
    }
  }
}

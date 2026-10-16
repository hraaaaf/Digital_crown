import type { Landmark } from '../cephaloShared';

/**
 * Presentation-only label placement. Never mutate landmark geometry or feed
 * these coordinates back to persistence, measurements, or pointer handlers.
 */
export interface CephaloLabelPlacement {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export const cephaloLabelFontSize = (imageWidth: number, imageHeight: number): number =>
  Math.max(42, Math.min(64, Math.max(imageWidth / 35, imageHeight / 35)));

export function layoutCephaloLandmarkLabels(
  landmarks: Pick<Landmark, 'id' | 'x' | 'y'>[],
  requestedIds: ReadonlySet<string>,
  priorityId: string | null,
  imageWidth: number,
  imageHeight: number,
  fontOverride?: number,
): Map<string, CephaloLabelPlacement> {
  const result = new Map<string, CephaloLabelPlacement>();
  if (!(imageWidth > 0 && imageHeight > 0)) return result;
  const font = fontOverride && Number.isFinite(fontOverride) && fontOverride > 0
    ? fontOverride : cephaloLabelFontSize(imageWidth, imageHeight);
  const candidates = landmarks
    .filter(pt => requestedIds.has(pt.id) && Number.isFinite(pt.x) && Number.isFinite(pt.y))
    .sort((a, b) => Number(b.id === priorityId) - Number(a.id === priorityId)
      || a.id.localeCompare(b.id));
  const occupied: CephaloLabelPlacement[] = [];
  const margin = font * 0.3;
  for (const pt of candidates) {
    const width = Math.max(font * 1.3, (pt.id.length * 0.68 + 0.6) * font);
    const height = font * 1.35;
    if (width + margin * 2 > imageWidth || height + margin * 2 > imageHeight) continue;
    const shift = font * 1.1;
    const origins = [
      { x: pt.x + shift, y: pt.y - shift },
      { x: pt.x - shift - width, y: pt.y - shift },
      { x: pt.x + shift, y: pt.y + shift + height * 0.15 },
      { x: pt.x - shift - width, y: pt.y + shift + height * 0.15 },
      { x: pt.x + shift * 1.8, y: pt.y - height * 0.1 },
      { x: pt.x - shift * 1.8 - width, y: pt.y - height * 0.1 },
    ];
    if (fontOverride) {
      origins.push(
        { x: pt.x + shift * 2.6, y: pt.y - height },
        { x: pt.x - shift * 2.6 - width, y: pt.y - height },
        { x: pt.x + shift * 2.6, y: pt.y + height },
        { x: pt.x - shift * 2.6 - width, y: pt.y + height },
        { x: pt.x + shift * 3.5, y: pt.y - height * 0.25 },
        { x: pt.x - shift * 3.5 - width, y: pt.y - height * 0.25 },
      );
    }
    for (const origin of origins) {
      const x = Math.max(margin, Math.min(imageWidth - margin - width, origin.x));
      const y = Math.max(margin + height, Math.min(imageHeight - margin, origin.y));
      const box = { id: pt.id, x, y, width, height };
      // SVG text anchor is the baseline. Include a margin between labels.
      const collides = occupied.some(existing =>
        x < existing.x + existing.width + margin
        && x + width + margin > existing.x
        && y - height < existing.y + margin
        && y + margin > existing.y - existing.height);
      if (collides) continue;
      occupied.push(box);
      result.set(pt.id, box);
      break;
    }
  }
  return result;
}


/**
 * R21.2 desktop editorial layout: every anatomical name gets a stable text
 * position on one of two visual rails. This only creates presentation data.
 * The source landmarks, calibrated measurements and editing remain untouched.
 */
export interface CephaloPerimeterLabel {
  id: string;
  x: number;
  y: number;
  side: 'left' | 'right';
  sourceX: number;
  sourceY: number;
  leaderEndX: number;
  leaderEndY: number;
}

export function layoutCephaloPerimeterLabels(
  landmarks: Pick<Landmark, 'id' | 'x' | 'y'>[],
  viewport: string,
  unitsPerPixel: number,
): Map<string, CephaloPerimeterLabel> {
  const result = new Map<string, CephaloPerimeterLabel>();
  const parts = viewport.trim().split(/\s+/).map(Number);
  if (parts.length !== 4 || parts.some(value => !Number.isFinite(value))) return result;
  const [vx, vy, vw, vh] = parts;
  if (vw <= 0 || vh <= 0 || !Number.isFinite(unitsPerPixel) || unitsPerPixel <= 0) return result;
  const scale = Math.max(0.1, Math.min(unitsPerPixel, 30));
  const pad = 13 * scale;
  const points = landmarks.filter(pt => Number.isFinite(pt.x) && Number.isFinite(pt.y))
    .slice().sort((a, b) => a.x - b.x || a.y - b.y || a.id.localeCompare(b.id));
  const left = points.slice(0, Math.ceil(points.length / 2));
  const right = points.slice(Math.ceil(points.length / 2));
  const clamp = (value: number, low: number, high: number) => Math.max(low, Math.min(high, value));
  const place = (side: 'left' | 'right', column: typeof points) => {
    const rows = column.slice().sort((a, b) => a.y - b.y || a.id.localeCompare(b.id));
    // Floating image controls occupy the top and bottom corners on tall
    // radiographs. Reserve these lanes where vertical room permits, while
    // preserving 22.5px minimum row pitch for the desktop 38-name layout.
    const stageHeightCss = vh / scale;
    const verticalPadCss = Math.min(74, Math.max(13,
      (stageHeightCss - rows.length * 22.5) / 2));
    const verticalPad = verticalPadCss * scale;
    const step = (vh - verticalPad * 2) / Math.max(1, rows.length);
    const x = side === 'left' ? vx + pad : vx + vw - pad;
    rows.forEach((pt, index) => {
      const y = vy + verticalPad + (index + 0.5) * step + 5.5 * scale;
      // Full clinical name, never a relabeled or truncated anatomical ID.
      const approxWidth = pt.id.length * 9.7 * scale;
      const leaderEndX = side === 'left'
        ? Math.min(x + approxWidth + 7 * scale, vx + vw * 0.47)
        : Math.max(x - approxWidth - 7 * scale, vx + vw * 0.53);
      result.set(pt.id, {
        id: pt.id, x, y, side,
        sourceX: clamp(pt.x, vx + pad, vx + vw - pad),
        sourceY: clamp(pt.y, vy + pad, vy + vh - pad),
        leaderEndX,
        leaderEndY: y - 5 * scale,
      });
    });
  };
  place('left', left);
  place('right', right);
  return result;
}


/** BEFORE 2.0: labels stay near anatomical points, never alter them. */
export interface CephaloAnatomicalLabel {
  id: string; x: number; y: number; width: number;
  sourceX: number; sourceY: number; leaderEndX: number; leaderEndY: number;
  leaderNeeded: boolean; distancePx: number;
}
export function layoutCephaloAnatomicalLabels(
  landmarks: Pick<Landmark,'id'|'x'|'y'>[], viewport: string, unitsPerPixel: number,
  originalImageWidth?: number,
  labelForId: (id: string) => string = id => id,
): Map<string, CephaloAnatomicalLabel> {
  const result=new Map<string,CephaloAnatomicalLabel>();
  const v=viewport.trim().split(/\s+/).map(Number);
  if(v.length!==4||v.some(n=>!Number.isFinite(n))||!Number.isFinite(unitsPerPixel)
    ||unitsPerPixel<=0||v[2]<=0||v[3]<=0)return result;
  const [vx,vy,vw,vh]=v;
  const scale=Math.max(.1,Math.min(30,unitsPerPixel));
  const W=vw/scale,H=vh/scale;
  if(W<250||H<290)return result;
  const edge=15,h=21,gap=3;
  type Box={l:number;t:number;r:number;b:number};
  // At 150–200% zoom the toolbar gains four pan buttons, almost doubling
  // its footprint. The labels and radiograph controls share a screen space,
  // so keep that part of the canvas free of text at both zoom states.
  // This is display-only geometry, not anatomical repositioning.
  const zoomed=originalImageWidth !== undefined && Number.isFinite(originalImageWidth)
    && originalImageWidth>0 && vw<originalImageWidth-.5;
  const zoomDockWidth=Math.min(W-12,zoomed?Math.min(440,W*.82):220);
  const zoomDockHeight=zoomed?108:76;
  const forbidden:Box[]=[
    {l:W*.16,t:36,r:W*.87,b:92},
    {l:W-112,t:0,r:W,b:88},
    {l:0,t:H-zoomDockHeight,r:zoomDockWidth,b:H},
    {l:W-115,t:H-53,r:W,b:H},
  ];
  const intersect=(a:Box,b:Box,p=gap)=>
    a.l<b.r+p && a.r+p>b.l && a.t<b.b+p && a.b+p>b.t;
  const placed:Box[]=[];
  const clamp=(x:number,a:number,b:number)=>Math.max(a,Math.min(b,x));
  const points=landmarks.filter(p=>p.id&&Number.isFinite(p.x)&&Number.isFinite(p.y));
  const density=(p:typeof points[number])=>points.filter(q=>q!==p
    &&Math.hypot(q.x-p.x,q.y-p.y)<105*scale).length;
  const ordered=points.slice().sort((a,b)=>density(b)-density(a)
    ||b.id.length-a.id.length||a.y-b.y||a.x-b.x||a.id.localeCompare(b.id));
  for(const pt of ordered){
    const w=labelForId(pt.id).length*9.95+5;
    if(w>W-2*edge)continue;
    const ax=clamp((pt.x-vx)/scale,edge,W-edge);
    const ay=clamp((pt.y-vy)/scale,edge,H-edge);
    const seeds=[[18,-8],[-w-18,-8],[18,14],[-w-18,14],
      [-w/2,-27],[-w/2,29]];
    const options:{l:number;t:number;cost:number}[]=[];
    for(const radius of [0,22,40,65,95,130,170,220,290,360,460])
      for(const [dx,dy] of seeds)
        for(const [sx,sy] of radius===0 ? [[0,0]]
          : [[1,0],[-1,0],[0,1],[0,-1],[.7,.7],[-.7,.7],[.7,-.7],[-.7,-.7]]){
          const l=clamp(ax+dx+sx*radius,edge,W-edge-w);
          const t=clamp(ay+dy+sy*radius-h,edge,H-edge-h);
          options.push({l,t,cost:Math.hypot(l+w/2-ax,t+h/2-ay)});
        }
    // Global fallback must never silently drop a required clinical name.
    for(let t=edge;t<=H-edge-h;t+=h+4)
      for(let l=edge;l<=W-edge-w;l+=14)
        options.push({l,t,cost:Math.hypot(l+w/2-ax,t+h/2-ay)+12});
    options.sort((a,b)=>a.cost-b.cost||a.t-b.t||a.l-b.l);
    const chosen=options.find(c=>{
      const box={l:c.l,t:c.t,r:c.l+w,b:c.t+h};
      return !placed.some(b=>intersect(box,b))
        &&!forbidden.some(b=>intersect(box,b,1));
    });
    if(!chosen)continue; // The live browser gate fails if 38/38 not visible.
    placed.push({l:chosen.l,t:chosen.t,r:chosen.l+w,b:chosen.t+h});
    const ex=clamp(ax,chosen.l,chosen.l+w);
    const ey=clamp(ay,chosen.t,chosen.t+h);
    const d=Math.hypot(ex-ax,ey-ay);
    result.set(pt.id,{
      id:pt.id,x:vx+chosen.l*scale,y:vy+(chosen.t+h-4)*scale,width:w*scale,
      sourceX:pt.x,sourceY:pt.y,
      leaderEndX:vx+ex*scale,leaderEndY:vy+ey*scale,
      leaderNeeded:d>23 && pt.x>=vx&&pt.x<=vx+vw&&pt.y>=vy&&pt.y<=vy+vh,
      distancePx:d,
    });
  }
  return result;
}

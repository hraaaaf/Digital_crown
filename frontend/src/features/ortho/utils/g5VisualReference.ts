import sourceReference from '../fixtures/g5VisualReference.json';
import {api} from '../../../services/api';

/** QA visual guide, NOT clinical contour data and never an approval source. */
export const G5_VISUAL_REFERENCE = sourceReference;
export const G5_PAIRED_FILM_URL = '/api/static/uploads/radios/t2-cephalo-seeded.png';

type Study = {
  image_original_path?: string | null;
  angles_data?: {
    odf_lab_image_landmark_alignment?: string;
    odf_lab_display_png_sha256?: string;
  } | null;
};

/** Matching metadata is necessary, but never sufficient to reveal the guide. */
export function isG5ReferenceStudy(study: Study): boolean {
  return study.image_original_path === G5_PAIRED_FILM_URL.slice(1) &&
    study.angles_data?.odf_lab_image_landmark_alignment ===
      'VERIFIED_AARIZ_EXPERT_PAIR' &&
    study.angles_data?.odf_lab_display_png_sha256 ===
      G5_VISUAL_REFERENCE.source.display_sha256 &&
    G5_VISUAL_REFERENCE.clinical_approval === false &&
    G5_VISUAL_REFERENCE.curves.length === 6;
}

/** Exact bytes of the displayed film must match the reviewed pixel coordinate space. */
export async function verifyG5ReferenceFilm(
  study: Study,
  readAuthenticatedFilm: () => Promise<ArrayBuffer> = async () => {
    // This source may require the cabinet JWT. Never read it using an
    // anonymous raw fetch: the same authorization boundary applies to G5.
    const response = await api.get<ArrayBuffer>(
      '/static/uploads/radios/t2-cephalo-seeded.png',
      {responseType:'arraybuffer',headers:{'Cache-Control':'no-cache'}},
    );
    return response.data;
  },
): Promise<boolean> {
  if (!isG5ReferenceStudy(study) || !globalThis.crypto?.subtle) return false;
  try {
    const bytes=await readAuthenticatedFilm();
    if (!(bytes instanceof ArrayBuffer)) return false;
    const png=new Uint8Array(bytes);
    const signature=[137,80,78,71,13,10,26,10];
    if(png.length<100000||!signature.every((value,i)=>png[i]===value)) return false;
    const digest=await crypto.subtle.digest('SHA-256',bytes);
    const actual=Array.from(new Uint8Array(digest))
      .map(byte=>byte.toString(16).padStart(2,'0')).join('');
    return actual===G5_VISUAL_REFERENCE.source.display_sha256;
  }catch{
    return false;
  }
}

type Point = readonly [number, number];
const round = (n: number) => Number(n.toFixed(2));
const sign = (v: number) => v > 0 ? 1 : v < 0 ? -1 : 0;

/** Piecewise cubic Hermite with PCHIP derivatives, matching the QA board renderer. */
export function g5ReferenceSvgPath(points: readonly (readonly number[])[]): string {
  if (points.length < 2 || points.some(p => p.length !== 2 ||
    !Number.isFinite(p[0]) || !Number.isFinite(p[1]))) return '';
  const knots = points as readonly Point[];
  const lengths: number[] = [];
  for (let i = 1; i < knots.length; i++) {
    const length = Math.hypot(knots[i][0] - knots[i-1][0],
      knots[i][1] - knots[i-1][1]);
    if (length < 0.5) return '';
    lengths.push(length);
  }
  const derivatives = ([0,1] as const).map(axis => {
    const slopes = lengths.map((h,i) =>
      (knots[i+1][axis] - knots[i][axis]) / h);
    if (slopes.length === 1) return [slopes[0],slopes[0]];
    const edge = (h0:number,h1:number,m0:number,m1:number) => {
      let d=((2*h0+h1)*m0-h0*m1)/(h0+h1);
      if(sign(d)!==sign(m0)) d=0;
      else if(sign(m0)!==sign(m1) && Math.abs(d)>3*Math.abs(m0)) d=3*m0;
      return d;
    };
    const ds=[edge(lengths[0],lengths[1],slopes[0],slopes[1])];
    for(let i=1;i<knots.length-1;i++) {
      const prev=slopes[i-1],next=slopes[i];
      if(!prev||!next||sign(prev)!==sign(next)) ds.push(0);
      else {
        const w1=2*lengths[i]+lengths[i-1];
        const w2=lengths[i]+2*lengths[i-1];
        ds.push((w1+w2)/(w1/prev+w2/next));
      }
    }
    ds.push(edge(lengths.at(-1)!,lengths.at(-2)!,
      slopes.at(-1)!,slopes.at(-2)!));
    return ds;
  });
  let path=`M ${round(knots[0][0])} ${round(knots[0][1])}`;
  for(let i=0;i<lengths.length;i++) {
    const h=lengths[i];
    const c1:Point=[knots[i][0]+h*derivatives[0][i]/3,
      knots[i][1]+h*derivatives[1][i]/3];
    const c2:Point=[knots[i+1][0]-h*derivatives[0][i+1]/3,
      knots[i+1][1]-h*derivatives[1][i+1]/3];
    path+=` C ${round(c1[0])} ${round(c1[1])} ${round(c2[0])} ${round(c2[1])} ${round(knots[i+1][0])} ${round(knots[i+1][1])}`;
  }
  return path;
}

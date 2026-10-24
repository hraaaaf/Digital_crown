import type { CSSProperties } from 'react';
import type { Geometry } from './studioLayouts';

/** Pure 07.1.B geometries. Module authority and min widths are checked elsewhere. */
export function geometryGridStyle(geometry: Geometry, ratio = 50): CSSProperties {
  const value = Number.isFinite(ratio) ? Math.max(37,Math.min(63,ratio)) : 50;
  const common: CSSProperties = {display:'grid',gap:'0.75rem',width:'100%',minWidth:0};
  switch (geometry) {
    case 'single': return {...common,gridTemplateColumns:'minmax(0,1fr)'};
    case 'two-columns': return {...common,gridTemplateColumns:'minmax(0,' + value + 'fr) minmax(0,' + (100-value) + 'fr)'};
    case 'two-rows': return {...common,gridTemplateColumns:'minmax(0,1fr)',gridTemplateRows:'repeat(2,minmax(0,1fr))'};
    case 'three-columns': return {...common,gridTemplateColumns:'repeat(3,minmax(0,1fr))'};
    case 'hero-two': return {...common,gridTemplateColumns:'minmax(0,' + value + 'fr) minmax(0,' + (100-value) + 'fr)',gridTemplateRows:'repeat(2,minmax(0,1fr))'};
    case 'grid-2x2': return {...common,gridTemplateColumns:'repeat(2,minmax(0,1fr))',gridTemplateRows:'repeat(2,minmax(0,1fr))'};
    case 'focus-rail': return {...common,gridTemplateColumns:'minmax(0,3fr) minmax(0,1fr)',gridTemplateRows:'repeat(2,minmax(0,1fr))'};
  }
}

export function geometrySlotStyle(geometry: Geometry, index: number): CSSProperties {
  if ((geometry === 'hero-two' || geometry === 'focus-rail') && index === 0) {
    return {gridRow:'1 / span 2',minWidth:0,minHeight:0};
  }
  return {minWidth:0,minHeight:0};
}

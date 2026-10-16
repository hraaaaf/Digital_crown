import { describe, expect, it } from 'vitest';
import { cephaloLabelFontSize, layoutCephaloLandmarkLabels, layoutCephaloPerimeterLabels, layoutCephaloAnatomicalLabels } from './cephaloLabelLayout';

const points = [
  { id: 'N', x: 800, y: 450 }, { id: 'A', x: 806, y: 454 },
  { id: 'B', x: 810, y: 458 }, { id: 'Po', x: 300, y: 600 },
  { id: 'Or', x: 420, y: 590 }, { id: 'Me', x: 810, y: 790 },
];

describe('DC-CEPH-03B.3e label layout (visual only)', () => {
  it('removes ambient labels but preserves editable landmarks unchanged', () => {
    const before = JSON.stringify(points);
    const labels = layoutCephaloLandmarkLabels(points, new Set(), null, 1280, 900);
    expect(labels.size).toBe(0);
    expect(JSON.stringify(points)).toBe(before);
  });
  it('prioritizes focused landmark and prevents pairwise text box collisions', () => {
    const requested = new Set(points.map(p => p.id));
    const labels = layoutCephaloLandmarkLabels(points, requested, 'N', 1280, 900);
    expect(labels.has('N')).toBe(true);
    const boxes = [...labels.values()];
    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i], b = boxes[j];
        const overlaps = a.x < b.x + b.width && a.x + a.width > b.x
          && a.y - a.height < b.y && a.y > b.y - b.height;
        expect(overlaps, a.id + ' and ' + b.id + ' collide').toBe(false);
      }
    }
    const shuffled = [...points].reverse();
    expect([...layoutCephaloLandmarkLabels(shuffled, requested, 'N', 1280, 900)])
      .toEqual([...labels]);
  });
  it('keeps label bounds within the raster while leaving edge points untouched', () => {
    const edge = [{ id: 'S', x: 0, y: 0 }, { id: 'N', x: 1000, y: 1255 }];
    const before = JSON.stringify(edge);
    const labels = layoutCephaloLandmarkLabels(edge, new Set(['S', 'N']), 'S', 1000, 1255);
    expect(labels.size).toBe(2);
    for (const label of labels.values()) {
      expect(label.x).toBeGreaterThanOrEqual(0);
      expect(label.y - label.height).toBeGreaterThanOrEqual(0);
      expect(label.x + label.width).toBeLessThanOrEqual(1000);
      expect(label.y).toBeLessThanOrEqual(1255);
    }
    expect(JSON.stringify(edge)).toBe(before);
  });
  it('fails closed on invalid raster dimensions and never displays non-finite labels', () => {
    expect(layoutCephaloLandmarkLabels(points, new Set(['N']), 'N', 0, 900).size).toBe(0);
    expect(layoutCephaloLandmarkLabels([{ id: 'N', x: NaN, y: 3 }],
      new Set(['N']), 'N', 1000, 1000).size).toBe(0);
    expect(cephaloLabelFontSize(2272, 1818)).toBeGreaterThan(18);
  });
});

// Pure presentation coordinates: full clinical IDs remain the persistence contract.
describe('R21.2 compact labels do not change editable anatomical coordinates', () => {
  it('uses a zoom-dependent screen font while keeping boxes separated', () => {
    const source = JSON.stringify(points);
    for (const units of [1.5, 2.5, 4]) {
      const rendered = layoutCephaloLandmarkLabels(points, new Set(points.map(p => p.id)), 'N', 1280, 900, 16 * units);
      expect(rendered.has('N')).toBe(true);
      expect(rendered.size).toBeGreaterThanOrEqual(4);
      const boxes = [...rendered.values()];
      for (let i = 0; i < boxes.length; i++) {
        for (let j = i + 1; j < boxes.length; j++) {
          const a = boxes[i], b = boxes[j];
          expect(a.x >= b.x+b.width || b.x >= a.x+a.width || a.y-a.height >= b.y || b.y-b.height >= a.y).toBe(true);
        }
      }
    }
    expect(JSON.stringify(points)).toBe(source);
  });
});

describe('R21.2 no-container perimeter labeling', () => {
  const pts = Array.from({ length: 38 }, (_, i) => ({
    id: 'Anatomic_' + String(i).padStart(2, '0'), x: 150 + i * 37, y: 200 + (i * 101) % 1000,
  }));
  it('places all 38 unchanged names in two deterministic balanced rails', () => {
    const prior = JSON.stringify(pts);
    for (const [viewBox, scale] of [['0 0 2272 1818', 2.7], ['0 0 1000 1255', 2],
      ['300 250 1000 900', 1.7]] as const) {
      const actual = layoutCephaloPerimeterLabels(pts, viewBox, scale);
      expect(actual.size).toBe(38);
      expect([...actual.values()].filter(v => v.side === 'left')).toHaveLength(19);
      expect([...actual.values()].filter(v => v.side === 'right')).toHaveLength(19);
      for (const item of actual.values()) {
        expect(item.id).toMatch(/^Anatomic_[0-9]{2}$/);
        expect([item.x, item.y, item.sourceX, item.sourceY, item.leaderEndX,
          item.leaderEndY].every(Number.isFinite)).toBe(true);
      }
      expect([...layoutCephaloPerimeterLabels([...pts].reverse(), viewBox, scale)])
        .toEqual([...actual]);
    }
    expect(JSON.stringify(pts)).toBe(prior);
  });
  it('reserves floating control lanes at short and tall desktop radiograph heights', () => {
    const before = JSON.stringify(pts);
    for (const screenHeight of [510, 574, 690]) {
      const unitsPerPixel = 3;
      const positions = [...layoutCephaloPerimeterLabels(
        pts, `0 0 2272 ${screenHeight * unitsPerPixel}`, unitsPerPixel,
      ).values()];
      expect(positions).toHaveLength(38);
      for (const side of ['left', 'right'] as const) {
        const rail = positions.filter(p => p.side === side).sort((a, b) => a.y - b.y);
        expect(rail).toHaveLength(19);
        const reserved = screenHeight >= 574 ? 69 : 39;
        expect(rail[0].y / unitsPerPixel).toBeGreaterThan(reserved);
        expect(screenHeight - rail[18].y / unitsPerPixel).toBeGreaterThan(reserved - 8);
        for (let i = 1; i < rail.length; i++) {
          expect((rail[i].y - rail[i-1].y) / unitsPerPixel).toBeGreaterThanOrEqual(22.49);
        }
      }
    }
    expect(JSON.stringify(pts)).toBe(before);
  });
  it('refuses invalid geometry and scale without writing coordinates', () => {
    expect(layoutCephaloPerimeterLabels(pts, 'bad', 2).size).toBe(0);
    expect(layoutCephaloPerimeterLabels(pts, '0 0 0 100', 2).size).toBe(0);
    expect(layoutCephaloPerimeterLabels(pts, '0 0 200 200', NaN).size).toBe(0);
  });
});

describe('BEFORE 2.0 anatomical non-container labels',()=>{
  const dense=Array.from({length:38},(_,i)=>({
    id:'P'+String(i).padStart(2,'0'),x:530+(i%8)*8,y:550+Math.floor(i/8)*10,
  }));
  it('fits all 38 full names without overlapping on dense anatomy and remains deterministic',()=>{
    const old=JSON.stringify(dense);
    for(const [vb,scale] of [['0 0 2272 1818',3],['300 100 1500 1200',3]] as const){
      const labels=layoutCephaloAnatomicalLabels(dense,vb,scale);
      expect(labels.size).toBe(38);
      const boxes=[...labels.values()].map(p=>({id:p.id,
        l:p.x/scale,r:(p.x+p.width)/scale,t:p.y/scale-17,b:p.y/scale+4}));
      for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){
        const a=boxes[i],b=boxes[j];
        expect(a.r+1<=b.l||b.r+1<=a.l||a.b+1<=b.t||b.b+1<=a.t,
          a.id+' / '+b.id).toBe(true);
      }
      expect([...layoutCephaloAnatomicalLabels([...dense].reverse(),vb,scale)])
        .toEqual([...labels]);
    }
    expect(JSON.stringify(dense)).toBe(old);
  });
  it('keeps isolated names next to their actual anatomical point',()=>{
    const pts=[{id:'N',x:1100,y:280},{id:'A',x:1900,y:1050},
      {id:'B',x:1600,y:1400}];
    const placed=layoutCephaloAnatomicalLabels(pts,'0 0 2272 1818',3);
    expect(placed.size).toBe(3);
    for(const p of pts){
      const label=placed.get(p.id)!;
      expect(label.distancePx).toBeLessThan(45);
      expect(Number.isFinite(label.leaderEndX)).toBe(true);
    }
  });
  it('refuses invalid geometry and scale instead of inventing positions',()=>{
    expect(layoutCephaloAnatomicalLabels(dense,'bad',2).size).toBe(0);
    expect(layoutCephaloAnatomicalLabels(dense,'0 0 2272 1818',NaN).size).toBe(0);
    expect(layoutCephaloAnatomicalLabels(dense,'0 0 100 100',1).size).toBe(0);
  });
});

describe('R22 zoom dock never obscures anatomical labels',()=>{
  const landmarks=[
    {id:'Go',x:840,y:1150},{id:'Me',x:1120,y:1050},
    {id:'N',x:1050,y:360},{id:'Po',x:450,y:510},
  ];
  it('reserves expanded bottom-left pan controls at 150% without moving landmarks',()=>{
    const before=JSON.stringify(landmarks);
    const layout=layoutCephaloAnatomicalLabels(landmarks,'0 0 1500 1200',3,2272);
    expect(layout.size).toBe(landmarks.length);
    const W=500,H=400, dockWidth=Math.min(440,W*.82);
    for(const p of layout.values()){
      const l=p.x/3,t=p.y/3-17,r=(p.x+p.width)/3,b=p.y/3+4;
      expect(r<=0||l>=dockWidth||b<=H-108||t>=H,
        p.id+' hidden under pan controls').toBe(true);
    }
    expect(JSON.stringify(landmarks)).toBe(before);
  });
  it('keeps only the compact zoom dock reserved at 100%',()=>{
    const layout=layoutCephaloAnatomicalLabels(landmarks,'0 0 2272 1818',3,2272);
    expect(layout.size).toBe(landmarks.length);
  });
});

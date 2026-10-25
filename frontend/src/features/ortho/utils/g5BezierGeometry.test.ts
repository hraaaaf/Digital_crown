import {describe, expect, it} from 'vitest';
import {g5CubicAt, g5SampleBezierContour, type G5CubicSegment} from './g5BezierGeometry';

const source = {imageWidth: 1935, imageHeight: 2400} as const;
const horizontal: G5CubicSegment = {
  start:[100,200],control1:[150,200],control2:[200,200],end:[250,200],
};
const facial: G5CubicSegment = {
  start:[1550,850],control1:[1690,980],control2:[1650,1100],end:[1610,1250],
};

describe('G5 source-pixel cubic geometry — LAB only', () => {
  it('interpolates an actual cubic curve without inventing anatomy', () => {
    expect(g5CubicAt(horizontal,0)).toEqual([100,200]);
    expect(g5CubicAt(horizontal,1)).toEqual([250,200]);
    expect(g5CubicAt(horizontal,0.5)).toEqual([175,200]);
    const m=g5CubicAt(facial,0.5);
    expect(m[0]).toBeGreaterThan(1550);
    expect(m[1]).toBeGreaterThan(850);
    expect(m[1]).toBeLessThan(1250);
  });

  it('samples in original image pixels regardless of browser zoom', () => {
    const out=g5SampleBezierContour([horizontal],source);
    expect(out[0]).toEqual([100,200]);
    expect(out.at(-1)).toEqual([250,200]);
    expect(out.length).toBeGreaterThan(10);
    expect(out.length).toBeLessThanOrEqual(600);
    expect(out.every(p=>p[1]===200 && p[0]>=100 && p[0]<=250)).toBe(true);
    for(let i=1;i<out.length;i++){
      expect(Math.hypot(out[i][0]-out[i-1][0],out[i][1]-out[i-1][1])).toBeGreaterThanOrEqual(0.5);
    }
  });

  it('keeps joined segments one continuous contour, without duplicate junction', () => {
    const second:G5CubicSegment={start:[250,200],control1:[275,205],control2:[310,230],end:[350,280]};
    const out=g5SampleBezierContour([horizontal,second],source);
    expect(out[0]).toEqual([100,200]);
    expect(out.at(-1)).toEqual([350,280]);
    expect(out.filter(p=>p[0]===250&&p[1]===200)).toHaveLength(1);
  });

  it('rejects out-of-image controls, nonfinite source points and discontinuous geometry', () => {
    const outside:G5CubicSegment={...horizontal,control1:[-2,200]};
    const nonfinite:G5CubicSegment={...horizontal,control1:[Number.NaN,200]};
    const separated:G5CubicSegment={...horizontal,start:[280,200],end:[420,200]};
    expect(()=>g5SampleBezierContour([outside],source)).toThrow('G5_BEZIER_OUTSIDE_SOURCE_IMAGE');
    expect(()=>g5SampleBezierContour([nonfinite],source)).toThrow('G5_BEZIER_OUTSIDE_SOURCE_IMAGE');
    expect(()=>g5SampleBezierContour([horizontal,separated],source)).toThrow('G5_BEZIER_DISCONTINUOUS_CONTOUR');
  });

  it('refuses degenerate contours, insufficient budget and invalid bounds', () => {
    const degenerate:G5CubicSegment={...horizontal,end:[100.1,200.1]};
    expect(()=>g5SampleBezierContour([degenerate],source)).toThrow('G5_BEZIER_DEGENERATE_SEGMENT');
    expect(()=>g5SampleBezierContour([horizontal],{...source,maxPoints:5}))
      .toThrow('G5_BEZIER_TOO_MANY_SAMPLES');
    expect(()=>g5SampleBezierContour([horizontal],{...source,imageHeight:0}))
      .toThrow('G5_BEZIER_INVALID_SAMPLING_CONTRACT');
    expect(()=>g5CubicAt(horizontal,Number.NaN)).toThrow('G5_BEZIER_INVALID_PARAMETER');
  });

  it('remains a geometry helper, not an automatic approval mechanism', () => {
    const out=g5SampleBezierContour([facial],source);
    expect(out.length).toBeGreaterThan(3);
    expect(out.at(-1)).toEqual([1610,1250]);
  });
});

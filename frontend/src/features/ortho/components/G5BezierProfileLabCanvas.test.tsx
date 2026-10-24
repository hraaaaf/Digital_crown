import React from 'react';
import {describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen} from '@testing-library/react';
import {G5BezierProfileLabCanvas} from './G5BezierProfileLabCanvas';

const width=1935;
const height=2400;
const viewport={left:0,top:0,width,height};

describe('G5 cutaneous Bezier canvas — research LAB guard',()=>{
  it('manually adds anchors and emits the sampled source-pixel contour',()=>{
    const emit=vi.fn();
    render(<G5BezierProfileLabCanvas
      imageUrl="/g5-qa-fixture.png" imageWidth={width} imageHeight={height}
      viewport={viewport} otherContours={[]} disabled={false}
      borderColor="#999" textColor="#444" onSampledChange={emit}/>);
    const svg=screen.getByTestId('odf-g5-bezier-surface');
    vi.spyOn(svg,'getBoundingClientRect').mockReturnValue({
      left:0,top:0,width:530,height:657.3643410852713,right:530,
      bottom:657.3643410852713,x:0,y:0,toJSON:()=>({}),
    });
    fireEvent.pointerDown(svg,{clientX:300,clientY:300});
    expect(screen.getByTestId('g5-bezier-anchor-0')).toBeTruthy();
    // The first single point is never a complete anatomy contour.
    expect(emit).toHaveBeenLastCalledWith([]);
    fireEvent.pointerDown(svg,{clientX:310,clientY:380});
    expect(screen.getByTestId('g5-bezier-anchor-1')).toBeTruthy();
    const samples=emit.mock.calls.at(-1)?.[0];
    expect(Array.isArray(samples)).toBe(true);
    expect(samples.length).toBeGreaterThan(16);
    expect(samples.length).toBeLessThanOrEqual(600);
    expect(samples[0][0]).toBeGreaterThan(0);
    expect(samples[0][1]).toBeGreaterThan(0);
    expect(samples.every((p:readonly number[])=>p[0]>=0&&p[0]<width
      &&p[1]>=0&&p[1]<height)).toBe(true);
    fireEvent.click(screen.getByTestId('g5-bezier-undo'));
    expect(emit).toHaveBeenLastCalledWith([]);
    fireEvent.click(screen.getByTestId('g5-bezier-redo'));
    expect(emit.mock.calls.at(-1)?.[0]).toEqual(samples);
  });

  it('does not create a contour when the LAB control is disabled',()=>{
    const emit=vi.fn();
    render(<G5BezierProfileLabCanvas
      imageUrl="/g5-qa-fixture.png" imageWidth={width} imageHeight={height}
      viewport={viewport} otherContours={[]} disabled={true}
      borderColor="#999" textColor="#444" onSampledChange={emit}/>);
    const svg=screen.getByTestId('odf-g5-bezier-surface');
    fireEvent.pointerDown(svg,{clientX:300,clientY:300});
    expect(emit).not.toHaveBeenCalled();
  });
});

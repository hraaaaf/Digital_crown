import React, {useRef, useState} from 'react';
import {
  g5SampleBezierContour,
  type G5CubicSegment,
  type G5PixelPoint,
} from '../utils/g5BezierGeometry';

/**
 * LAB ONLY — pure browser/manual Bézier profile input, never anatomy inference.
 * On each edit, emits only the exact V1 source-pixel polyline to be displayed,
 * stored and printed. V1 does not persist the editable handles: closing the
 * Bézier session leaves the sampled, non-approved polyline in the G5 draft.
 */
export type G5BezierNode = {anchor:G5PixelPoint;incoming:G5PixelPoint;outgoing:G5PixelPoint};
type Node = G5BezierNode;
type Handle = 'anchor'|'incoming'|'outgoing';
type Drag = {index:number;handle:Handle;last:G5PixelPoint};
type Props = {
  imageUrl:string;
  imageWidth:number;
  imageHeight:number;
  viewport:{left:number;top:number;width:number;height:number};
  otherContours:readonly {id:string;points:readonly G5PixelPoint[];color:string}[];
  disabled:boolean;
  onSampledChange:(points:G5PixelPoint[])=>void;
  initialNodes?:readonly G5BezierNode[]|null;
  onNodesChange?:(nodes:G5BezierNode[])=>void;
  borderColor:string;
  textColor:string;
};
const initialNode=(p:G5PixelPoint):Node=>({
  anchor:p,incoming:p,outgoing:p,
});
const inside=(v:number,max:number)=>Math.max(0,Math.min(max-0.1,Math.round(v*10)/10));
const add=(p:G5PixelPoint,d:G5PixelPoint):G5PixelPoint=>[p[0]+d[0],p[1]+d[1]];
const sub=(a:G5PixelPoint,b:G5PixelPoint):G5PixelPoint=>[a[0]-b[0],a[1]-b[1]];

export const G5BezierProfileLabCanvas:React.FC<Props>=({
  imageUrl,imageWidth,imageHeight,viewport,otherContours,disabled,
  onSampledChange,initialNodes,onNodesChange,borderColor,textColor,
})=>{
  const svg=useRef<SVGSVGElement|null>(null);
  const dragging=useRef<Drag|null>(null);
  const history=useRef<Node[][]>([]);
  const redoHistory=useRef<Node[][]>([]);
  const [nodes,setNodes]=useState<Node[]>(()=>initialNodes?.map(n=>({
    anchor:[...n.anchor] as G5PixelPoint,
    incoming:[...n.incoming] as G5PixelPoint,
    outgoing:[...n.outgoing] as G5PixelPoint,
  }))||[]);
  const [error,setError]=useState('');
  const inImage=(e:React.PointerEvent<SVGSVGElement>):G5PixelPoint|null=>{
    const bounds=svg.current?.getBoundingClientRect();
    if(!bounds||!bounds.width||!bounds.height)return null;
    const x=viewport.left+(e.clientX-bounds.left)*viewport.width/bounds.width;
    const y=viewport.top+(e.clientY-bounds.top)*viewport.height/bounds.height;
    return [inside(x,imageWidth),inside(y,imageHeight)];
  };
  const takeSnapshot=()=>{
    history.current.push(nodes.map(n=>({...n})));
    if(history.current.length>50)history.current.shift();
    redoHistory.current=[];
  };
  const segments=(arr:readonly Node[]):G5CubicSegment[]=>arr.slice(0,-1).map((n,i)=>({
    start:n.anchor,control1:n.outgoing,control2:arr[i+1].incoming,
    end:arr[i+1].anchor,
  }));
  const commit=(next:Node[])=>{
    try{
      const samples=next.length>1?g5SampleBezierContour(
        segments(next),{imageWidth,imageHeight,maxStepPixels:5},
      ):[];
      setNodes(next);
      onNodesChange?.(next.map(n=>({
        anchor:[...n.anchor] as G5PixelPoint,
        incoming:[...n.incoming] as G5PixelPoint,
        outgoing:[...n.outgoing] as G5PixelPoint,
      })));
      onSampledChange(samples.map(p=>[p[0],p[1]]));
      setError('');
    }catch(e){
      // Reject invalid updates, never silently truncate a clinically visible path.
      setError(e instanceof Error?e.message:'G5_BEZIER_GEOMETRY_REJECTED');
    }
  };
  const undo=()=>{
    const previous=history.current.pop();
    if(!previous)return;
    redoHistory.current.push(nodes);
    commit(previous);
  };
  const redo=()=>{
    const next=redoHistory.current.pop();
    if(!next)return;
    history.current.push(nodes);
    commit(next);
  };
  // Render the exact same deterministic V1 pixel samples that the API stores
  // and that the two PDF views draw; cubic-only SVG would misrepresent output.
  let renderedPoints:G5PixelPoint[]=[];
  if(nodes.length>1){
    try{
      renderedPoints=g5SampleBezierContour(segments(nodes),{
        imageWidth,imageHeight,maxStepPixels:5,
      });
    }catch{
      // Keep the last valid stored contour until the editor accepts an update.
    }
  }
  const renderedPolyline=renderedPoints.map(p=>p.join(',')).join(' ');
  const updateDrag=(p:G5PixelPoint)=>{
    const d=dragging.current;
    if(!d||!nodes[d.index])return;
    const original=nodes[d.index];
    let next:Node;
    if(d.handle==='anchor'){
      const delta=sub(p,d.last);
      next={
        anchor:p,
        incoming:[inside(original.incoming[0]+delta[0],imageWidth),
          inside(original.incoming[1]+delta[1],imageHeight)],
        outgoing:[inside(original.outgoing[0]+delta[0],imageWidth),
          inside(original.outgoing[1]+delta[1],imageHeight)],
      };
    }else{
      next={...original,[d.handle]:p};
    }
    dragging.current={...d,last:p};
    commit(nodes.map((n,i)=>i===d.index?next:n));
  };
  return <div data-testid="odf-g5-bezier-lab" className="space-y-2">
    <div className="flex flex-wrap items-center gap-2">
      <strong className="text-xs" style={{color:textColor}}>Profil cutané · poignées Bézier</strong>
      <button type="button" data-testid="g5-bezier-undo" onClick={undo}
        disabled={disabled||!history.current.length}
        className="rounded border px-2 py-1 text-xs" style={{borderColor,color:textColor}}>
        ↶ Annuler
      </button>
      <button type="button" data-testid="g5-bezier-redo" onClick={redo}
        disabled={disabled||!redoHistory.current.length}
        className="rounded border px-2 py-1 text-xs" style={{borderColor,color:textColor}}>
        ↷ Rétablir
      </button>
      <span className="text-xs" style={{color:textColor}}>
        {nodes.length} ancres · {Math.max(0,nodes.length-1)} segments
      </span>
    </div>
    <svg ref={svg} role="img" data-testid="odf-g5-bezier-surface"
      aria-label="Éditeur Bézier de profil cutané sur téléradiographie source"
      viewBox={`${viewport.left} ${viewport.top} ${viewport.width} ${viewport.height}`}
      className="mx-auto block w-full max-w-[530px] touch-none rounded-lg border"
      style={{aspectRatio:`${imageWidth} / ${imageHeight}`,borderColor,
        background:'#18202b',cursor:'crosshair'}}
      onPointerDown={e=>{
        if(disabled||dragging.current)return;
        const p=inImage(e);if(!p)return;
        takeSnapshot();
        if(!nodes.length){commit([initialNode(p)]);return;}
        const last=nodes[nodes.length-1].anchor;
        if(Math.hypot(p[0]-last[0],p[1]-last[1])<5)return;
        const third:G5PixelPoint=[(p[0]-last[0])/3,(p[1]-last[1])/3];
        const prev=nodes[nodes.length-1];
        commit([...nodes.slice(0,-1),{...prev,outgoing:add(last,third)},
          {...initialNode(p),incoming:sub(p,third)}]);
      }}
      onPointerMove={e=>{
        if(disabled||!dragging.current)return;
        const p=inImage(e);if(p)updateDrag(p);
      }}
      onPointerUp={e=>{
        dragging.current=null;
        if(e.currentTarget.hasPointerCapture(e.pointerId))
          e.currentTarget.releasePointerCapture(e.pointerId);
      }}
      onPointerCancel={()=>{dragging.current=null;}}>
      <image href={imageUrl} x="0" y="0" width={imageWidth} height={imageHeight}/>
      {otherContours.map(curve=><polyline key={curve.id}
        points={curve.points.map(p=>p.join(',')).join(' ')}
        fill="none" stroke={curve.color} strokeWidth="5"
        strokeLinecap="round" strokeLinejoin="round" pointerEvents="none"/>)}
      {renderedPolyline&&<>
        <polyline points={renderedPolyline} fill="none" stroke="#19222e"
          strokeWidth="10" strokeLinejoin="round" strokeLinecap="round"
          pointerEvents="none"/>
        <polyline points={renderedPolyline} fill="none" stroke="#ffac85"
          strokeWidth="5" strokeLinejoin="round" strokeLinecap="round"
          pointerEvents="none"/>
      </>}
      {nodes.map((node,index)=><g key={index}>
        {(['incoming','outgoing'] as const).map(key=>{
          if((index===0&&key==='incoming')||
              (index===nodes.length-1&&key==='outgoing'))return null;
          const control=node[key];
          return <g key={key}>
            <line x1={node.anchor[0]} y1={node.anchor[1]}
              x2={control[0]} y2={control[1]}
              stroke="#85c3ff" strokeWidth="2" strokeDasharray="7 5"
              pointerEvents="none"/>
            <circle data-testid={`g5-bezier-handle-${index}-${key}`}
              cx={control[0]} cy={control[1]} r="10"
              stroke="#85c3ff" strokeWidth="2" fill="#13273c"
              onPointerDown={e=>{
                if(disabled)return;
                e.stopPropagation();takeSnapshot();
                const p=inImage(e);
                if(!p)return;
                dragging.current={index,handle:key,last:p};
                svg.current?.setPointerCapture(e.pointerId);
              }}/>
          </g>;
        })}
        <circle data-testid={`g5-bezier-anchor-${index}`}
          cx={node.anchor[0]} cy={node.anchor[1]} r="12"
          stroke="#fff" strokeWidth="2" fill="#ffad84"
          onPointerDown={e=>{
            if(disabled)return;
            e.stopPropagation();takeSnapshot();
            const p=inImage(e);if(!p)return;
            dragging.current={index,handle:'anchor',last:p};
            svg.current?.setPointerCapture(e.pointerId);
          }}/>
      </g>)}
    </svg>
    <p className="text-xs" style={{color:error?'#c84f43':textColor}}>
      {error||'Cliquez sur l’image pour ajouter des ancres ; glissez les points ou tangentes pour corriger. Les points échantillonnés, pas les poignées, sont sauvegardés par V1. Mode LAB non clinique.'}
    </p>
  </div>;
};

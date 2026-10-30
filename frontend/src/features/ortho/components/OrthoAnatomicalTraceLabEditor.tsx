import React, {useEffect, useRef, useState} from 'react';
import {cephaloRepository} from '../cephaloRepository';
import {G5BezierProfileLabCanvas, type G5BezierNode} from './G5BezierProfileLabCanvas';
import {G5VisualReferenceOverlay} from './G5VisualReferenceOverlay';
import {verifyG5ReferenceFilm} from '../utils/g5VisualReference';
import {useOrthoStore} from '../stores/useOrthoStore';

/** Only mounted with VITE_ODF_G5_LAB=1; API separately refuses all non-LAB calls.
 * Draw what the dentist actually sees; never derive a silhouette from landmarks.
 */
type CurveId='cranial_base'|'maxilla'|'mandible'|'upper_incisor'|
  'lower_incisor'|'soft_tissue_profile';
type Point=[number,number];
type Curve={id:CurveId;points:Point[]};
const STRUCTURES:{id:CurveId;label:string;min:number;color:string}[]=[
  {id:'cranial_base',label:'Base du crâne',min:10,color:'#28466A'},
  {id:'maxilla',label:'Maxillaire',min:10,color:'#345C83'},
  {id:'mandible',label:'Mandibule',min:16,color:'#24496E'},
  {id:'upper_incisor',label:'Incisive supérieure',min:7,color:'#246D72'},
  {id:'lower_incisor',label:'Incisive inférieure',min:7,color:'#246D72'},
  {id:'soft_tissue_profile',label:'Profil cutané',min:16,color:'#B26B55'},
];
const W=1935,H=2400;
const fresh=():Curve[]=>STRUCTURES.map(item=>({id:item.id,points:[]}));
const pairedImage='/api/static/uploads/radios/t2-cephalo-seeded.png';

export const OrthoAnatomicalTraceLabEditor:React.FC<{P:any}>=({P})=>{
  const patientId=useOrthoStore(s=>s.patientId);
  const analysisId=useOrthoStore(s=>s.analysisId);
  const svgRef=useRef<SVGSVGElement|null>(null);
  const drawing=useRef(false);
  const panStart=useRef<{clientX:number;clientY:number;center:Point}|null>(null);
  const requestId=useRef(0);
  const [curves,setCurves]=useState<Curve[]>(fresh);
  const [zoom,setZoom]=useState<1|2|4|8>(1);
  const [panMode,setPanMode]=useState(false);
  const [bezierMode,setBezierMode]=useState(false);
  const [bezierNodes,setBezierNodes]=useState<G5BezierNode[]|null>(null);
  const [referenceMatched,setReferenceMatched]=useState(false);
  const [showReference,setShowReference]=useState(false);
  const [viewportCenter,setViewportCenter]=useState<Point>([W/2,H/2]);
  const [selected,setSelected]=useState<CurveId>('cranial_base');
  const [revision,setRevision]=useState<number|null>(null);
  const [draftVersion,setDraftVersion]=useState(0);
  const [serverApproved,setServerApproved]=useState(false);
  const [dirty,setDirty]=useState(false);
  const [busy,setBusy]=useState(false);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const [notice,setNotice]=useState('');
  // Zoom/pan changes viewport only; original source image pixel space persists.
  const viewW=W/zoom,viewH=H/zoom;
  const viewLeft=Math.max(0,Math.min(W-viewW,viewportCenter[0]-viewW/2));
  const viewTop=Math.max(0,Math.min(H-viewH,viewportCenter[1]-viewH/2));

  useEffect(()=>{
    const id=++requestId.current;
    drawing.current=false;panStart.current=null;
    setZoom(1);setPanMode(false);setBezierMode(false);setBezierNodes(null);
    setViewportCenter([W/2,H/2]);
    setCurves(fresh());setRevision(null);setDraftVersion(0);
    setDirty(false);setServerApproved(false);setError('');setNotice('');
    setReferenceMatched(false);setShowReference(false);
    if(!patientId||!analysisId)return;
    setLoading(true);
    (async()=>{
      try{
        const study=await cephaloRepository.getAnalysis(analysisId);
        const r=study.angles_data?.scientific_read_path?.revision;
        if(study.id!==analysisId||!Number.isSafeInteger(r)||r<1)throw Error('Révision scientifique absente');
        const server=await cephaloRepository.readAnatomicalTrace(patientId,analysisId,r);
        if(id!==requestId.current)return;
        setRevision(r);setDraftVersion(server.draft_version);
        if(server.stale)throw Error('Courbes périmées : réouvrir cette étude');
        setCurves(STRUCTURES.map(s=>{
          const c=server.contours.find((v:{id:string})=>v.id===s.id);
          return {id:s.id,points:Array.isArray(c?.points)?
            c.points.map((p:number[])=>[p[0],p[1]] as Point):[]};
        }));
        setBezierNodes(Array.isArray(server.bezier_profile_nodes)
          ?server.bezier_profile_nodes.map(n=>({
            anchor:[n.anchor[0],n.anchor[1]] as Point,
            incoming:[n.incoming[0],n.incoming[1]] as Point,
            outgoing:[n.outgoing[0],n.outgoing[1]] as Point,
          })):null);
        setServerApproved(server.approved);
        // The guide remains hidden unless both study provenance AND the
        // displayed film's actual bytes match the fixed Aariz review target.
        const matched=await verifyG5ReferenceFilm(study);
        if(id===requestId.current)setReferenceMatched(matched);
      }catch(e){
        if(id===requestId.current)setError(e instanceof Error?e.message:'Tracé non disponible');
      }finally{if(id===requestId.current)setLoading(false);}
    })();
    return ()=>{requestId.current++;};
  },[patientId,analysisId]);

  const loc=(e:React.PointerEvent<SVGSVGElement>):Point|null=>{
    const svg=svgRef.current;if(!svg)return null;
    const rect=svg.getBoundingClientRect();
    if(!rect.width||!rect.height)return null;
    const x=viewLeft+(e.clientX-rect.left)*viewW/rect.width;
    const y=viewTop+(e.clientY-rect.top)*viewH/rect.height;
    if(x<0||y<0||x>=W||y>=H)return null;
    return [Math.round(x*10)/10,Math.round(y*10)/10];
  };
  const add=(p:Point)=>{
    if(selected==='soft_tissue_profile')setBezierNodes(null);
    setCurves(prev=>prev.map(c=>{
      if(c.id!==selected)return c;
      const last=c.points[c.points.length-1];
      if(last&&Math.hypot(last[0]-p[0],last[1]-p[1])<5)return c;
      if(c.points.length>=600)return c;
      return {...c,points:[...c.points,p]};
    }));
    setDirty(true);setServerApproved(false);setNotice('');
  };
  const undo=()=>{if(selected==='soft_tissue_profile')setBezierNodes(null);
    setCurves(prev=>prev.map(c=>c.id===selected?
      {...c,points:c.points.slice(0,-1)}:c));setDirty(true);setServerApproved(false);};
  const clear=()=>{if(selected==='soft_tissue_profile'){
      setBezierMode(false);setBezierNodes(null);
    }
    setCurves(prev=>prev.map(c=>c.id===selected?
      {...c,points:[]}:c));setDirty(true);setServerApproved(false);};
  const complete=STRUCTURES.every(spec=>(curves.find(c=>c.id===spec.id)?.points.length||0)>=spec.min);

  const save=async()=>{
    if(!patientId||!analysisId||!revision||!complete||busy||loading)return;
    setBusy(true);setError('');
    try{
      const saved=await cephaloRepository.saveAnatomicalTraceDraft(
        patientId,analysisId,{
          expected_revision:revision,expected_draft_version:draftVersion,
          contours:curves,
          bezier_profile_nodes:bezierNodes,
        });
      setDraftVersion(saved.draft_version);setServerApproved(false);
      setDirty(false);setNotice('Brouillon manuel enregistré ; validation encore nécessaire.');
    }catch(e){setError(e instanceof Error?e.message:'Échec d’enregistrement');}
    finally{setBusy(false);}
  };
  const approve=async()=>{
    if(!patientId||!analysisId||!revision||!draftVersion||dirty||busy)return;
    setBusy(true);setError('');
    try{
      const signed=await cephaloRepository.approveAnatomicalTrace(
        patientId,analysisId,{
          expected_revision:revision,expected_draft_version:draftVersion,
        });
      if(!signed.approved)throw Error('Approbation du tracé refusée par le serveur');
      setServerApproved(true);setNotice('Six contours approuvés par le dentiste pour cette révision.');
    }catch(e){setError(e instanceof Error?e.message:'Validation impossible');}
    finally{setBusy(false);}
  };

  if(import.meta.env.VITE_ODF_G5_LAB!=='1')return null;
  return <section data-testid="odf-g5-manual-tracing"
    className="space-y-3 rounded-xl border p-4" style={{background:P.bgCard,borderColor:P.border}}>
    <div className="flex flex-wrap items-start justify-between gap-2">
      <div>
        <h3 className="font-bold text-sm" style={{color:P.text}}>
          G5 LAB — tracé anatomique manuel
        </h3>
        <p className="text-xs" style={{color:P.textMuted}}>
          Dessinez à la main six contours sur cette radiographie réelle.
          Aucun contour n’est proposé automatiquement.
        </p>
      </div>
      <span className="text-xs font-semibold" style={{color:serverApproved?'#23765F':P.textMuted}}>
        {serverApproved?'Approuvé (LAB)':dirty?'Modifié, non approuvé':'Brouillon'}
      </span>
    </div>
    <div className="flex flex-wrap items-center gap-2">
      <button type="button" data-testid="g5-reference-toggle"
        disabled={!referenceMatched||loading||busy}
        aria-pressed={showReference}
        onClick={()=>setShowReference(v=>!v)}
        className="rounded-lg border px-3 py-2 text-xs font-semibold"
        style={{borderColor:P.border,color:P.text}}>
        {showReference?'Masquer la référence QA':'Afficher la référence QA (lecture seule)'}
      </button>
      <span data-testid="g5-reference-source-status" className="text-xs"
        style={{color:P.textMuted}}>
        {referenceMatched
          ?'Source Aariz vérifiée · 2 contours pleins, 4 incertains en pointillés · NON CLINIQUE'
          :'Référence indisponible : image et étude source non confirmées'}
      </span>
    </div>
    {showReference&&referenceMatched&&<p data-testid="g5-reference-warning"
      className="text-xs font-semibold" style={{color:'#a55e37'}}>
      Référence visuelle uniquement : jamais copiée dans le brouillon ou le PDF
      clinique. Tracez et corrigez vous-même chaque structure avant approbation.
    </p>}
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {STRUCTURES.map(spec=>{
        const n=curves.find(c=>c.id===spec.id)?.points.length||0;
        return <button type="button" key={spec.id} disabled={busy||loading||!revision}
          aria-pressed={selected===spec.id}
          onClick={()=>{setSelected(spec.id);setBezierMode(false);}}
          className="rounded-lg border px-2 py-2 text-left text-xs"
          style={{color:P.text,borderColor:selected===spec.id?spec.color:P.border,
            background:selected===spec.id?P.bgInput:P.bgCard}}>
          <span style={{color:spec.color}}>●</span> {spec.label}
          <span className="block opacity-70">{n}/{spec.min} points minimum</span>
        </button>;
      })}
    </div>
    <div className="flex flex-wrap items-center gap-2" role="group"
      aria-label="Zoom et déplacement du tracé">
      <span className="text-xs" style={{color:P.textMuted}}>Zoom</span>
      {([1,2,4,8] as const).map(level=>
        <button key={level} type="button" data-testid={`g5-zoom-${level}`}
          disabled={!revision||loading||busy} aria-pressed={zoom===level}
          className="rounded-lg border px-3 py-2 text-xs"
          style={{borderColor:zoom===level?P.accent:P.border,color:P.text}}
          onClick={()=>{
            setZoom(level);
            if(level===1){setPanMode(false);setViewportCenter([W/2,H/2]);}
          }}>×{level}</button>)}
      <button type="button" data-testid="g5-pan-toggle"
        disabled={zoom===1||!revision||loading||busy} aria-pressed={panMode}
        className="rounded-lg border px-3 py-2 text-xs"
        style={{borderColor:panMode?P.accent:P.border,color:P.text}}
        onClick={()=>setPanMode(v=>!v)}>Déplacer l'image</button>
      <span className="text-xs" style={{color:P.textMuted}}>
        {panMode?'Glissez pour déplacer, sans dessiner':'Coordonnées de l’image source'}
      </span>
    </div>
    {selected==='soft_tissue_profile'&&<div className="flex flex-wrap items-center gap-2">
      <button type="button" data-testid="g5-bezier-mode-toggle"
        disabled={busy||loading||!revision||(!bezierMode&&
          (curves.find(c=>c.id==='soft_tissue_profile')?.points.length||0)>0
          &&!bezierNodes)}
        aria-pressed={bezierMode}
        onClick={()=>{setBezierMode(v=>!v);setPanMode(false);}}
        className="rounded-lg border px-3 py-2 text-xs font-semibold"
        style={{borderColor:bezierMode?'#ffac85':P.border,color:P.text}}>
        {bezierMode?'Quitter l’édition Bézier':'Tracer le profil en Bézier'}
      </button>
      <span className="text-xs" style={{color:P.textMuted}}>
        {bezierMode
          ?'Mode LAB : poignées temporaires, même polyligne source-pixel que le PDF V1.'
          :'Démarrer uniquement sur un profil vide ; effacer explicitement avant de recommencer.'}
      </span>
    </div>}
    {bezierMode&&selected==='soft_tissue_profile'
      ?<G5BezierProfileLabCanvas
        key={`g5-bezier-${patientId}-${analysisId}-${revision}-${draftVersion}`}
        imageUrl={pairedImage} imageWidth={W} imageHeight={H}
        viewport={{left:viewLeft,top:viewTop,width:viewW,height:viewH}}
        otherContours={curves.filter(c=>c.id!=='soft_tissue_profile').map(c=>({
          id:c.id,points:c.points,
          color:STRUCTURES.find(s=>s.id===c.id)?.color||'#111111',
        }))}
        disabled={busy||loading||!revision||panMode}
        borderColor={P.border} textColor={P.textMuted}
        showVisualReference={showReference&&referenceMatched}
        initialNodes={bezierNodes}
        onNodesChange={setBezierNodes}
        onSampledChange={points=>{
          setCurves(prev=>prev.map(c=>c.id==='soft_tissue_profile'
            ?{...c,points:points.map(p=>[p[0],p[1]] as Point)}:c));
          setDirty(true);setServerApproved(false);setNotice('');
        }}
      />
      :<svg ref={svgRef} data-testid="odf-g5-drawing-surface"
      viewBox={`${viewLeft} ${viewTop} ${viewW} ${viewH}`} role="img"
      aria-label="Dessiner le contour sélectionné directement sur la téléradiographie"
      className="mx-auto block w-full max-w-[530px] touch-none rounded-lg border"
      style={{aspectRatio:`${W} / ${H}`,borderColor:P.border,
        background:'#18202b',cursor:panMode?'grab':'crosshair'}}
      onPointerDown={e=>{
        if(busy||loading||!revision)return;
        if(panMode){
          if(zoom===1)return;
          panStart.current={clientX:e.clientX,clientY:e.clientY,
            center:[viewLeft+viewW/2,viewTop+viewH/2]};
          e.currentTarget.setPointerCapture(e.pointerId);return;
        }
        const p=loc(e);if(!p)return;
        drawing.current=true;
        e.currentTarget.setPointerCapture(e.pointerId);add(p);
      }}
      onPointerMove={e=>{
        if(panStart.current){
          const rect=e.currentTarget.getBoundingClientRect();
          if(!rect.width||!rect.height)return;
          const start=panStart.current;
          setViewportCenter([
            Math.max(viewW/2,Math.min(W-viewW/2,
              start.center[0]-(e.clientX-start.clientX)*viewW/rect.width)),
            Math.max(viewH/2,Math.min(H-viewH/2,
              start.center[1]-(e.clientY-start.clientY)*viewH/rect.height)),
          ]);
          return;
        }
        if(!drawing.current||busy)return;
        const p=loc(e);if(p)add(p);
      }}
      onPointerUp={e=>{drawing.current=false;panStart.current=null;
        if(e.currentTarget.hasPointerCapture(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId);}}
      onPointerCancel={()=>{drawing.current=false;panStart.current=null;}}>
      <image href={pairedImage} x="0" y="0" width={W} height={H}/>
      {showReference&&referenceMatched&&<G5VisualReferenceOverlay/>}
      {curves.map(curve=>{
        const color=STRUCTURES.find(s=>s.id===curve.id)?.color||'#111111';
        const points=curve.points.map(p=>p.join(',')).join(' ');
        return <polyline key={curve.id} points={points}
          fill="none" stroke={color} strokeWidth={curve.id===selected?8:5}
          strokeLinecap="round" strokeLinejoin="round"/>;
      })}
    </svg>}
    <div className="flex flex-wrap gap-2">
      <button type="button" disabled={busy||loading||!revision||bezierMode}
        onClick={undo} className="rounded-lg border px-3 py-2 text-xs"
        style={{borderColor:P.border,color:P.text}}>Annuler dernier point</button>
      <button type="button" disabled={busy||loading||!revision}
        onClick={clear} className="rounded-lg border px-3 py-2 text-xs"
        style={{borderColor:P.border,color:P.text}}>Effacer ce contour</button>
      <button type="button" disabled={!complete||busy||loading||!dirty||!revision}
        onClick={save} className="rounded-lg px-3 py-2 text-xs font-semibold"
        style={{background:P.accent,color:'#fff'}}>Enregistrer les six contours</button>
      <button type="button" disabled={!complete||busy||loading||dirty||!draftVersion||serverApproved}
        onClick={approve} className="rounded-lg border px-3 py-2 text-xs font-semibold"
        style={{borderColor:P.accent,color:P.text}}>Approuver explicitement le tracé</button>
    </div>
    <p className="text-xs" style={{color:P.textMuted}}>
      Pour valider, chaque courbe doit suivre une structure anatomique visible.
      La saisie ne remplace pas la validation clinique du diagnostic.
    </p>
    {(error||notice)&&<p role="status" className="text-xs"
      style={{color:error?'#ad493b':P.text}}>{error||notice}</p>}
  </section>;
};

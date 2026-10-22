import { useEffect, useRef, useState, type PointerEvent } from 'react';
import {
  PERMANENT_FDI, RESEARCH_SCHEMA, RESEARCH_SPECIALTIES,
  createResearchState, parseResearchInput, addResearchTooth,
  confirmResearchTooth, discardResearchTooth, duplicateFdi,
  editResearchTooth, undoResearchConfirmation, addResearchAct,
  attachResearchAct, researchExport,
  type FdiBox, type FdiResearchState, type ResearchAct,
} from './fdiResearchState';

/**
 * Development-only research workbench embedded in the actual PanoramicStudio.
 * STRICTLY NOT connected to the patient image, clinical endpoints, or records.
 * No weights are downloaded/bundled; genuine inference requires an authorized
 * offline research ONNX export via the J10E bridge.
 */
export function FDIResearchPanel() {
  const [state, setState] = useState<FdiResearchState | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageDims, setImageDims] = useState<{ width: number; height: number } | null>(null);
  const [sample, setSample] = useState(false);
  const [manualFdi, setManualFdi] = useState('38');
  const [addMode, setAddMode] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [actLabel, setActLabel] = useState('');
  const [specialty, setSpecialty] = useState<string>(RESEARCH_SPECIALTIES[0]);
  const [actDictionary, setActDictionary] = useState<ResearchAct[]>([]);
  const [actId, setActId] = useState('');
  const [selectedBox, setSelectedBox] = useState<FdiBox | null>(null);
  const imageUrlRef = useRef<string | null>(null);
  const dragRef = useRef<{ id: string; x: number; y: number; box: FdiBox } | null>(null);

  useEffect(() => () => { if (imageUrlRef.current) URL.revokeObjectURL(imageUrlRef.current); }, []);
  const tooth = state?.teeth.find((t) => t.id === selected) ?? null;
  const errors = state ? duplicateFdi(state) : [];
  const confirmed = state?.teeth.filter((t) => t.confirmed).length ?? 0;
  const safeApply = (callback: () => FdiResearchState) => {
    try {
      const changed = callback();
      setState(changed);
      setFeedback('Modification locale enregistrée en mémoire (hors dossier patient).');
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : 'Modification invalide.');
    }
  };
  const resetSelection = (next: FdiResearchState) => {
    setState(next); setSelected(null); setSelectedBox(null);
    setFeedback('Propositions reçues : aucune dent n’est confirmée.');
  };
  const openSynthetic = () => {
    if (imageUrlRef.current) URL.revokeObjectURL(imageUrlRef.current);
    imageUrlRef.current = null;
    setImageUrl(null); setSample(true);
    setImageDims({ width: 1200, height: 600 });
    resetSelection(createResearchState({
      schema: RESEARCH_SCHEMA, image_width: 1200, image_height: 600,
      proposals: [
        { fdi: '36', bbox: [0.21, 0.35, 0.31, 0.72], confidence: 0.91 },
        { fdi: '37', bbox: [0.35, 0.31, 0.45, 0.71], confidence: 0.78 },
        { fdi: '46', bbox: [0.64, 0.35, 0.74, 0.71], confidence: 0.88 },
      ],
    }));
  };
  const onImageFile = async (file?: File) => {
    if (!file) return;
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 20_000_000) {
      setFeedback('Image de recherche invalide (PNG/JPEG/WebP, 20 Mo maximum).'); return;
    }
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      if (img.naturalWidth <= 0 || img.naturalHeight <= 0 || img.naturalWidth > 10000 || img.naturalHeight > 10000) {
        URL.revokeObjectURL(url);
        setFeedback('Dimensions d’image invalides.'); return;
      }
      if (imageUrlRef.current) URL.revokeObjectURL(imageUrlRef.current);
      imageUrlRef.current = url; setImageUrl(url); setSample(false);
      setImageDims({ width: img.naturalWidth, height: img.naturalHeight });
      // Image identity changed. Prior confirmation/FDI/acts MUST NOT migrate,
      // even between two different research images with identical dimensions.
      resetSelection(createResearchState({
        schema: RESEARCH_SCHEMA, image_width: img.naturalWidth, image_height: img.naturalHeight, proposals: [],
      }));
      setFeedback('Fichier de recherche chargé dans le navigateur, sans transfert.');
    };
    img.onerror = () => { URL.revokeObjectURL(url); setFeedback('Image illisible.'); };
    img.src = url;
  };
  const onProposalsFile = async (file?: File) => {
    if (!file) return;
    if (file.size > 1_000_000) { setFeedback('JSON trop volumineux.'); return; }
    try {
      const parsed = parseResearchInput(JSON.parse(await file.text()));
      if (imageDims && (imageDims.width !== parsed.image_width || imageDims.height !== parsed.image_height)) {
        throw new Error('Dimensions JSON et image différentes.');
      }
      resetSelection(createResearchState(parsed));
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : 'JSON invalide.');
    }
  };
  const point = (event: PointerEvent<SVGSVGElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    return [
      Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width)),
      Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height)),
    ] as const;
  };
  const pointerDown = (event: PointerEvent<SVGSVGElement>) => {
    if (!state) return;
    const [x, y] = point(event);
    if (addMode) {
      const w = .085, h = .14, x1 = Math.max(0, Math.min(1-w, x-w/2));
      const y1 = Math.max(0, Math.min(1-h, y-h/2));
      safeApply(() => addResearchTooth(state, manualFdi, [x1, y1, x1+w, y1+h]));
      setSelected(`t${state.nextId}`); setAddMode(false);
      return;
    }
    const el = event.target as Element;
    const g = el.closest('[data-fdi-id]') as SVGElement | null;
    const id = g?.getAttribute('data-fdi-id');
    if (!id) return;
    const selectedTooth = state.teeth.find((t) => t.id === id);
    if (!selectedTooth) return;
    setSelected(id); setSelectedBox([...selectedTooth.bbox] as FdiBox);
    dragRef.current = { id, x, y, box: [...selectedTooth.bbox] as FdiBox };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const pointerUp = (event: PointerEvent<SVGSVGElement>) => {
    const drag = dragRef.current;
    dragRef.current = null;
    if (!drag || !state) return;
    const [x, y] = point(event), dx = x-drag.x, dy=y-drag.y;
    // A tap/click selects. Only deliberate pointer motion edits anatomy and
    // invalidates an existing clinician confirmation/its linked manual acts.
    if (Math.hypot(dx, dy) < 0.005) {
      try { event.currentTarget.releasePointerCapture(event.pointerId); } catch { /* released */ }
      return;
    }
    const width = drag.box[2]-drag.box[0], height=drag.box[3]-drag.box[1];
    const x1 = Math.max(0, Math.min(1-width, drag.box[0]+dx));
    const y1 = Math.max(0, Math.min(1-height, drag.box[1]+dy));
    const nextBox: FdiBox = [x1, y1, x1+width, y1+height];
    safeApply(() => editResearchTooth(state, drag.id, { bbox: nextBox }));
    setSelectedBox(nextBox);
    try { event.currentTarget.releasePointerCapture(event.pointerId); } catch { /* released */ }
  };
  const downloadResearchReport = () => {
    if (!state) return;
    try {
      const result = researchExport(state, actDictionary);
      const u = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }));
      const a = document.createElement('a');
      a.href = u; a.download = 'fdi-relecture-recherche.json'; a.click();
      window.setTimeout(() => URL.revokeObjectURL(u), 1000);
      setFeedback('Export local uniquement. Aucune écriture au dossier patient.');
    } catch (err) { setFeedback(err instanceof Error ? err.message : 'Export impossible.'); }
  };
  return (
    <section aria-label="Atelier FDI de recherche" data-testid="fdi-research-workspace"
      className="rounded-2xl border border-amber-400/70 bg-slate-950 p-4 text-slate-100 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-[11px] font-black tracking-widest text-amber-300">LABORATOIRE FDI · MODE DÉVELOPPEMENT UNIQUEMENT</p>
          <h3 className="text-lg font-bold">Correction des dents — recherche locale</h3>
          <p className="text-xs text-slate-300">Ni image patient liée, ni API clinique, ni diagnostic, ni sauvegarde dans le dossier.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="rounded-lg bg-cyan-700 px-3 py-2 text-xs" type="button" onClick={openSynthetic}>Exemple synthétique</button>
          <label className="cursor-pointer rounded-lg border border-slate-500 px-3 py-2 text-xs">
            Image locale de recherche
            <input aria-label="Image locale de recherche" className="sr-only" type="file" accept="image/png,image/jpeg,image/webp"
              onChange={(e) => { void onImageFile(e.target.files?.[0]); }} />
          </label>
          <label className="cursor-pointer rounded-lg border border-slate-500 px-3 py-2 text-xs">
            Propositions FDI (.json)
            <input aria-label="Propositions FDI (.json)" className="sr-only" type="file" accept="application/json,.json"
              onChange={(e) => { void onProposalsFile(e.target.files?.[0]); }} />
          </label>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="rounded-full border border-slate-500 px-3 py-1">{state?.teeth.length ?? 0} propositions</span>
        <span className="rounded-full border border-emerald-500 px-3 py-1">{confirmed} confirmées</span>
        <span className="rounded-full border border-amber-500 px-3 py-1">{errors.length ? 'Doublons à vérifier : ' + errors.join(', ') : 'FDI en doublon : aucun'}</span>
      </div>
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1.8fr)_minmax(260px,1fr)]">
        <div className="min-w-0 space-y-3">
          <div className="relative aspect-[2/1] overflow-hidden rounded-xl border border-slate-600 bg-slate-900"
            data-testid="fdi-image-stage">
            {sample && <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1200 600" aria-label="Panoramique artificielle uniquement">
              <defs><linearGradient id="fdiJ10FResearchGradient"><stop stopColor="#172633" /><stop offset=".5" stopColor="#6f8291"/><stop offset="1" stopColor="#172633"/></linearGradient></defs>
              <rect width="1200" height="600" fill="url(#fdiJ10FResearchGradient)"/>
              {[180,300,420,540,660,780,900].map((x) => <ellipse key={x} cx={x} cy="300" rx="43" ry="99" fill="#b2c4cf" fillOpacity=".58"/>)}
            </svg>}
            {imageUrl && <img src={imageUrl} alt="Image de recherche locale, sans lien au patient" className="absolute inset-0 h-full w-full object-fill" />}
            {!imageUrl && !sample && <p className="absolute inset-0 grid place-items-center text-sm text-slate-300">Choisir l’exemple synthétique ou une image de recherche autorisée.</p>}
            {state && <svg data-testid="fdi-overlay" role="img" aria-label="Boîtes dentaires FDI modifiables"
              viewBox="0 0 1000 1000" preserveAspectRatio="none"
              className="absolute inset-0 h-full w-full touch-none" onPointerDown={pointerDown} onPointerUp={pointerUp}
              onPointerCancel={() => { dragRef.current = null; }}>
              {state.teeth.map((t) => {
                const [x1,y1,x2,y2] = t.bbox.map((v) => v*1000);
                return <g key={t.id} data-fdi-id={t.id}>
                  <rect x={x1} y={y1} width={x2-x1} height={y2-y1}
                    fill="rgba(45,212,191,.07)" stroke={t.id === selected ? '#fde68a' : t.confirmed ? '#4ade80' : '#2dd4bf'}
                    strokeWidth={t.id===selected?4:2} vectorEffect="non-scaling-stroke" />
                  <text x={x1+4} y={Math.max(26,y1-4)} fill="#fff" fontSize="24" fontWeight="bold" pointerEvents="none">{t.fdi}</text>
                </g>;
              })}
            </svg>}
          </div>
          <div className="flex flex-wrap items-end gap-2">
            <label className="text-xs">Ajouter dent FDI <select aria-label="Numéro FDI à ajouter" className="ml-2 rounded-lg bg-slate-800 p-2"
              value={manualFdi} onChange={(e) => setManualFdi(e.target.value)}>
              {PERMANENT_FDI.map((fdi) => <option key={fdi} value={fdi}>{fdi}</option>)}
            </select></label>
            <button className={'rounded-lg px-3 py-2 text-xs ' + (addMode ? 'bg-amber-700' : 'bg-slate-700')}
              type="button" onClick={() => setAddMode(!addMode)}>Ajouter sur l’image</button>
          </div>
          <div className="flex max-h-40 flex-wrap gap-2 overflow-y-auto">
            {state?.teeth.map((t) => <button key={t.id} type="button"
              className={'rounded-lg border px-3 py-2 text-xs ' + (t.id===selected ? 'border-amber-300 bg-slate-700' : 'border-slate-700')}
              onClick={() => { setSelected(t.id); setSelectedBox([...t.bbox] as FdiBox); }}>
              {t.fdi} · {t.confirmed ? '✓ confirmée' : 'à vérifier'}
            </button>)}
          </div>
        </div>
        <div className="min-w-0 space-y-3 text-xs">
          {tooth ? <>
            <p className="font-bold text-sm">Dent sélectionnée · {tooth.fdi}</p>
            <label className="block">Corriger FDI <select aria-label="Corriger numéro FDI"
              className="mt-1 w-full rounded-lg bg-slate-800 p-2" value={tooth.fdi}
              onChange={(e) => safeApply(() => editResearchTooth(state!, tooth.id, { fdi: e.target.value }))}>
              {PERMANENT_FDI.map((fdi) => <option key={fdi} value={fdi}>{fdi}</option>)}</select>
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(['X min', 'Y min', 'X max', 'Y max'] as const).map((key, idx) => <label key={key}>{key} (%)
                <input aria-label={'Rectangle '+key} type="number" min="0" max="100" step=".1"
                  className="mt-1 w-full rounded-lg bg-slate-800 p-2"
                  value={selectedBox ? Number((selectedBox[idx]*100).toFixed(1)) : ''}
                  onChange={(e) => setSelectedBox((current) => {
                    if (!current) return null;
                    const next = [...current] as FdiBox; next[idx] = Number(e.target.value)/100; return next;
                  })}/>
              </label>)}
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" className="rounded-lg bg-slate-700 p-2" onClick={() => {
                if (selectedBox) safeApply(() => editResearchTooth(state!, tooth.id, { bbox: selectedBox }));
              }}>Corriger rectangle</button>
              <button type="button" className="rounded-lg bg-emerald-700 p-2" onClick={() => safeApply(() => confirmResearchTooth(state!, tooth.id))}>Confirmer FDI</button>
              <button type="button" className="rounded-lg bg-slate-700 p-2" onClick={() => safeApply(() => undoResearchConfirmation(state!, tooth.id))}>Annuler</button>
              <button type="button" className="rounded-lg bg-red-900 p-2" onClick={() => {
                safeApply(() => discardResearchTooth(state!, tooth.id)); setSelected(null); setSelectedBox(null);
              }}>Supprimer proposition</button>
            </div>
          </> : <p className="rounded-lg border border-slate-700 p-3">Sélectionner une dent pour corriger et confirmer sa numérotation.</p>}
          <div className="space-y-2 border-t border-slate-600 pt-3">
            <p className="font-bold text-sm">Actes du praticien — en mémoire uniquement</p>
            <label className="block">Spécialité <select aria-label="Spécialité de l’acte" value={specialty}
              className="mt-1 w-full rounded-lg bg-slate-800 p-2" onChange={(e) => setSpecialty(e.target.value)}>
              {RESEARCH_SPECIALTIES.map((name) => <option key={name}>{name}</option>)}</select></label>
            <label className="block">Libellé manuel <input aria-label="Libellé de l’acte manuel"
              className="mt-1 w-full rounded-lg bg-slate-800 p-2" value={actLabel} onChange={(e)=>setActLabel(e.target.value)}/></label>
            <button type="button" className="rounded-lg bg-slate-700 p-2" onClick={() => {
              try {
                const next = addResearchAct(actDictionary, specialty, actLabel);
                setActDictionary(next); setActId(next[next.length-1].id); setActLabel('');
                setFeedback('Acte ajouté en mémoire temporaire (non enregistré en patient).');
              } catch (err) { setFeedback(err instanceof Error ? err.message : 'Acte invalide.'); }
            }}>Ajouter un acte</button>
            <label className="block">Acte existant <select aria-label="Choisir acte manuel"
              className="mt-1 w-full rounded-lg bg-slate-800 p-2" value={actId}
              onChange={(e)=>setActId(e.target.value)}>
              <option value="">Choisir...</option>
              {actDictionary.map((a) => <option key={a.id} value={a.id}>{a.specialty} · {a.label}</option>)}
            </select></label>
            <button type="button" className="rounded-lg bg-cyan-700 p-2"
              onClick={() => { if (state && selected) safeApply(() => attachResearchAct(state, selected, actId, actDictionary)); else setFeedback('Choisir une dent confirmée.'); }}>
              Associer manuellement à la dent confirmée</button>
            <p>Actes de cette dent : {tooth?.actIds.map((id)=>actDictionary.find((a)=>a.id===id)?.label).filter(Boolean).join(', ') || 'aucun'}</p>
          </div>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-600 pt-3">
        <p className="max-w-2xl text-xs text-amber-200">Recherche hors soins uniquement : 32 dents permanentes, aucune sauvegarde patient. Modèle non autorisé en production commerciale.</p>
        <button className="rounded-lg bg-slate-700 px-4 py-2 text-xs font-bold" type="button"
          onClick={downloadResearchReport}>Exporter la relecture locale</button>
      </div>
      <p role="status" aria-live="polite" className="text-xs text-cyan-200">{feedback}</p>
    </section>
  );
}

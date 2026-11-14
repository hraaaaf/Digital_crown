/** Descriptive A4 V1: exact preview -> explicit clinician approval -> archive.
 * No electronic signature, no clinical diagnosis/treatment activation.
 * This component never relies on the generic archive:true PDF route. */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Archive, CheckCircle2, Eye, Loader2, ShieldCheck, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../../../services/api';
import type { PDFPageProxy } from 'pdfjs-dist';
import { cephaloArchiveErrorMessage } from '../cephaloArchiveGate';
import { prepareBoundCephaloDocumentSource } from '../cephaloDocumentSource';
import { useOrthoStore } from '../stores/useOrthoStore';

type PreparedA4 = {
  analysis_id: number;
  expected_revision: number;
  practitioner_name: string;
  cabinet_stamp_name: string;
  pdf_sha256: string;
  pdf_base64: string;
  approval_token: string;
  document_kind: 'CEPH_A4_DESCRIPTIVE_APPROVAL_V1';
  clinical_diagnosis_validated: false;
};


/**
 * Verify the exact PDF SHA-256, then paint ALL pages with PDF.js before the
 * clinician can acknowledge, print or archive. Local-only, fail-closed.
 */
const MAX_A4_PREVIEW_BYTES = 16 * 1024 * 1024;
const MAX_A4_PREVIEW_PAGES = 20;

const VerifiedA4PdfCanvas: React.FC<{
  pdfBase64: string;
  expectedSha256: string;
  onVerified: (verified: boolean) => void;
}> = ({ pdfBase64, expectedSha256, onVerified }) => {
  const hostRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [pages, setPages] = useState(0);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let cancelled = false;
    let loadingTask: { destroy: () => Promise<void> } | null = null;
    let renderTask: ReturnType<PDFPageProxy['render']> | null = null;
    host.replaceChildren();
    setStatus('loading');
    setPages(0);
    onVerified(false);

    const loadAndRender = async () => {
      try {
        if (!/^[a-f0-9]{64}$/.test(expectedSha256))
          throw Error('A4_EXPECTED_SHA_INVALID');
        const raw = atob(pdfBase64);
        if (raw.length < 4 || raw.length > MAX_A4_PREVIEW_BYTES ||
            raw.slice(0, 4) !== '%PDF')
          throw Error('A4_PDF_BYTES_INVALID');
        const bytes = new Uint8Array(raw.length);
        for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
        const hash = await crypto.subtle.digest('SHA-256', bytes);
        const actualSha = Array.from(new Uint8Array(hash), value =>
          value.toString(16).padStart(2, '0')).join('');
        if (actualSha !== expectedSha256) throw Error('A4_PREVIEW_SHA_MISMATCH');
        if (cancelled) return;

        // Keep PDF.js out of module initialization: jsdom/SSR has no DOMMatrix.
        // Never bypass renderer in the real browser or weaken the fail-closed gate.
        const [{ getDocument, GlobalWorkerOptions }, worker] = await Promise.all([
          import('pdfjs-dist'),
          import('pdfjs-dist/build/pdf.worker.min.mjs?url'),
        ]);
        if (cancelled) return;
        GlobalWorkerOptions.workerSrc = worker.default;
        const task = getDocument({ data: bytes, isEvalSupported: false });
        loadingTask = task;
        const pdf = await task.promise;
        if (cancelled) return;
        if (pdf.numPages < 1 || pdf.numPages > MAX_A4_PREVIEW_PAGES)
          throw Error('A4_PAGE_COUNT_UNSUPPORTED');

        for (let number = 1; number <= pdf.numPages; number++) {
          if (cancelled) return;
          const pdfPage = await pdf.getPage(number);
          if (cancelled) return;
          const normal = pdfPage.getViewport({ scale: 1 });
          const scale = Math.min(1.35, Math.max(1, (host.clientWidth - 32) / normal.width));
          const viewport = pdfPage.getViewport({ scale });
          const pixelRatio = Math.min(Math.max(window.devicePixelRatio || 1, 1), 2);
          const canvas = document.createElement('canvas');
          canvas.width = Math.ceil(viewport.width * pixelRatio);
          canvas.height = Math.ceil(viewport.height * pixelRatio);
          canvas.style.width = Math.ceil(viewport.width) + 'px';
          canvas.style.height = Math.ceil(viewport.height) + 'px';
          canvas.className = 'mx-auto mb-4 block max-w-none bg-white shadow-lg';
          canvas.setAttribute('aria-label', 'Page ' + number + ' du bilan A4');
          canvas.setAttribute('data-ceph-a4-page-rendered', 'false');
          const canvasContext = canvas.getContext('2d', { alpha: false });
          if (!canvasContext) throw Error('A4_CANVAS_UNAVAILABLE');
          host.appendChild(canvas);
          renderTask = pdfPage.render({
            canvas, canvasContext, viewport,
            transform: pixelRatio === 1
              ? undefined : [pixelRatio, 0, 0, pixelRatio, 0, 0],
          });
          await renderTask.promise;
          if (cancelled) return;
          renderTask = null;
          if (canvas.width < 1 || canvas.height < 1)
            throw Error('A4_CANVAS_EMPTY');
          canvas.setAttribute('data-ceph-a4-page-rendered', 'true');
        }
        if (cancelled) return;
        setPages(pdf.numPages);
        setStatus('ready');
        onVerified(true);
      } catch {
        if (cancelled) return;
        host.replaceChildren();
        setStatus('error');
        onVerified(false);
      }
    };
    void loadAndRender();
    return () => {
      cancelled = true;
      try { renderTask?.cancel(); } catch { /* already completed */ }
      void loadingTask?.destroy().catch(() => {});
      host.replaceChildren();
    };
  }, [pdfBase64, expectedSha256, onVerified]);

  return (
    <section data-ceph-a4-pdf-preview={status}
      aria-label="Aperçu PDF exact vérifié avant approbation"
      className="mt-3 overflow-hidden rounded-lg border border-slate-300">
      {status === 'loading' && (
        <p role="status" className="p-3 text-xs font-semibold text-slate-700">
          Vérification SHA-256 et rendu de toutes les pages du bilan A4…
        </p>
      )}
      {status === 'error' && (
        <p role="alert" className="p-3 text-xs font-bold text-red-700">
          Aperçu PDF non vérifiable ou non affichable : approbation et archivage bloqués.
        </p>
      )}
      {status === 'ready' && (
        <p role="status" className="p-3 text-xs font-semibold text-emerald-800">
          PDF exact vérifié (SHA-256) — {pages} page(s) affichée(s).
          Consultez toutes les pages avant de confirmer.
        </p>
      )}
      <div ref={hostRef} className="h-[55vh] overflow-auto bg-slate-200 p-3" />
    </section>
  );
};

function scienceLocalSnapshot(): string {
  const s = useOrthoStore.getState();
  return JSON.stringify({landmarks: s.local.landmarks, mmPerPixel: s.mmPerPixel});
}

export const CephaloA4ApprovalV1: React.FC<{
  P: any; disabled?: boolean;
}> = ({ P, disabled = false }) => {
  const { patientId, analysisId } = useOrthoStore();
  const [prepared, setPrepared] = useState<PreparedA4 | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<string | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const [previewVerified, setPreviewVerified] = useState(false);
  const [previewGeneration, setPreviewGeneration] = useState(0);
  const onPreviewVerified = useCallback((verified: boolean) => {
    setPreviewVerified(verified);
  }, []);
  const [busy, setBusy] = useState<'prepare' | 'archive' | null>(null);
  const inFlight = useRef(false);
  const objectUrl = useRef<string | null>(null);
  const identityRef = useRef({ patientId, analysisId });
  identityRef.current = { patientId, analysisId };

  function clearPreview() {
    if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
    objectUrl.current = null;
    setPrepared(null);
    setPreviewUrl(null);
    setSnapshot(null);
    setAcknowledged(false);
    setPreviewVerified(false);
    setPreviewGeneration(previous => previous + 1);
  }

  useEffect(() => {
    return () => {
      if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
      objectUrl.current = null;
    };
  }, []);

  useEffect(() => {
    // A pending preview of patient A must never remain approvable on study B.
    clearPreview();
  }, [patientId, analysisId]);

  async function prepare() {
    if (!patientId || !analysisId || disabled || inFlight.current) return;
    if (useOrthoStore.getState().isPrinting || useOrthoStore.getState().isPreviewLoading) {
      toast.error('Une opération PDF est déjà en cours.'); return;
    }
    inFlight.current = true;
    setBusy('prepare');
    const active = () =>
      identityRef.current.patientId === patientId &&
      identityRef.current.analysisId === analysisId;
    try {
      const selected = await prepareBoundCephaloDocumentSource(
        patientId, analysisId, active,
        () => useOrthoStore.getState().silentSave(analysisId, true),
        () => {
          const live = useOrthoStore.getState();
          return { landmarks: live.local.landmarks, mmPerPixel: live.mmPerPixel };
        },
      );
      if (!active()) throw Error("L'étude sélectionnée a changé");
      const scientificLocal = scienceLocalSnapshot();
      const response = await api.post<PreparedA4>(
        `/patients/${patientId}/cephalo-a4/prepare`,
        selected,
      );
      const result = response.data;
      if (!active() || scientificLocal !== scienceLocalSnapshot()) {
        throw Error("Les repères ont changé pendant la préparation du bilan");
      }
      if (
        result.analysis_id !== analysisId ||
        result.expected_revision !== selected.expected_revision ||
        result.document_kind !== 'CEPH_A4_DESCRIPTIVE_APPROVAL_V1' ||
        result.clinical_diagnosis_validated !== false ||
        !result.pdf_base64 || !result.approval_token || !result.pdf_sha256
      ) throw Error("Bilan descriptif ou révision non vérifiable");
      const raw = atob(result.pdf_base64);
      const bytes = new Uint8Array(raw.length);
      for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
      const nextUrl = URL.createObjectURL(new Blob([bytes], {type:'application/pdf'}));
      if (!active()) {
        URL.revokeObjectURL(nextUrl);
        throw Error("L'étude sélectionnée a changé");
      }
      clearPreview();
      objectUrl.current = nextUrl;
      setPreviewUrl(nextUrl);
      setPrepared(result);
      setSnapshot(scientificLocal);
    } catch (error) {
      if (active()) toast.error(await cephaloArchiveErrorMessage(error));
    } finally {
      inFlight.current = false;
      setBusy(null);
    }
  }

  function printPrepared() {
    if (!prepared || !previewUrl || !previewVerified || !acknowledged || busy || disabled) return;
    // An explicit click opens a local PDF viewer; NEVER calls /archive.
    const popup = window.open('', '_blank');
    if (!popup) {
      toast.error("Autorisez l'ouverture de la fenêtre d'impression."); return;
    }
    const raw = atob(prepared.pdf_base64);
    const bytes = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
    const printUrl = URL.createObjectURL(new Blob([bytes], { type:'application/pdf' }));
    const doc = popup.document;
    doc.title = "Bilan A4 descriptif — impression";
    doc.body.replaceChildren();
    doc.body.style.cssText = "margin:0;font-family:Arial,sans-serif;background:#f8fafc";
    const toolbar = doc.createElement('div');
    toolbar.style.cssText = "display:flex;align-items:center;gap:12px;padding:12px;background:white";
    const button = doc.createElement('button');
    button.type = 'button';
    button.textContent = 'Imprimer le PDF';
    const description = doc.createElement('span');
    description.textContent = "Bilan descriptif vérifié par le praticien — impression sans archivage";
    const frame = doc.createElement('iframe');
    frame.src = printUrl;
    frame.title = 'PDF céphalométrique descriptif à imprimer';
    frame.style.cssText = 'display:block;width:100%;height:calc(100vh - 52px);border:0';
    button.addEventListener('click', () => {
      frame.contentWindow?.focus();
      frame.contentWindow?.print();
    });
    toolbar.append(button, description);
    doc.body.append(toolbar, frame);
    popup.addEventListener('beforeunload', () => URL.revokeObjectURL(printUrl), { once:true });
    popup.focus();
  }

  async function archive() {
    if (!patientId || !analysisId || !prepared || !previewVerified || !acknowledged ||
        !snapshot || inFlight.current || disabled) return;
    if (prepared.analysis_id !== analysisId || snapshot !== scienceLocalSnapshot()) {
      clearPreview();
      toast.error("Les repères ou la calibration ont changé : prévisualisez à nouveau.");
      return;
    }
    inFlight.current = true;
    setBusy('archive');
    const active = () =>
      identityRef.current.patientId === patientId &&
      identityRef.current.analysisId === analysisId;
    try {
      const response = await api.post<Blob>(
        `/patients/${patientId}/cephalo-a4/archive`,
        {
          analysis_id: analysisId,
          expected_revision: prepared.expected_revision,
          approval_token: prepared.approval_token,
          pdf_base64: prepared.pdf_base64,
          approved: true,
        },
        { responseType: 'blob' },
      );
      if (
        String(response.headers?.['x-cephalo-analysis-id'] ?? '') !== String(analysisId) ||
        String(response.headers?.['x-cephalo-revision'] ?? '') !== String(prepared.expected_revision)
      ) throw Error("Accusé d'archivage incohérent, vérifiez le dossier avant toute nouvelle action");
      if (active()) {
        clearPreview();
        toast.success("Bilan descriptif A4 validé et archivé dans le dossier patient.");
      }
    } catch (error) {
      if (active()) toast.error(await cephaloArchiveErrorMessage(error));
    } finally {
      inFlight.current = false;
      setBusy(null);
    }
  }

  return (
    <div className="mt-4 rounded-xl border p-4" style={{ borderColor: P.border, background: P.bgCard }}>
      <div className="flex items-center gap-2">
        <ShieldCheck size={17} style={{ color: P.accent }} />
        <p className="text-xs font-black" style={{ color: P.text }}>Validation praticien — bilan descriptif A4</p>
      </div>
      <p className="mt-2 text-xs" style={{ color: P.textMuted }}>
        Après vérification des mesures, vous pouvez approuver et archiver le PDF exact affiché.
        Ce bilan descriptif ne comprend ni diagnostic ni plan de traitement.
      </p>
      <button type="button" onClick={() => void prepare()} disabled={!analysisId || !patientId || disabled || !!busy}
        className="mt-3 inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-bold disabled:opacity-40"
        style={{ borderColor: P.border, color: P.text }}>
        {busy === 'prepare' ? <Loader2 size={16} className="animate-spin" /> : <Eye size={16} />}
        Préparer l'aperçu A4 à valider
      </button>
      {prepared && previewUrl && (
        <div role="dialog" aria-modal="true" aria-label="Vérification finale du bilan A4" className="mt-4 border rounded-xl p-3" style={{ borderColor: P.border }}>
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-sm font-black" style={{ color: P.text }}>Aperçu exact du bilan à archiver</p>
              <p className="text-xs" style={{ color: P.textMuted }}>
                Étude {prepared.analysis_id} · Révision {prepared.expected_revision} · {prepared.practitioner_name}
              </p>
              <p className="text-xs" style={{ color: P.textMuted }}>
                Cachet du cabinet : {prepared.cabinet_stamp_name || 'non configuré'}
              </p>
            </div>
            <button type="button" aria-label="Fermer l'aperçu A4" onClick={clearPreview} disabled={!!busy}>
              <X size={18}/>
            </button>
          </div>
          <VerifiedA4PdfCanvas
            key={previewGeneration}
            pdfBase64={prepared.pdf_base64}
            expectedSha256={prepared.pdf_sha256}
            onVerified={onPreviewVerified}
          />
          <p className="mt-2 font-mono text-[10px] break-all" style={{ color: P.textMuted }}>SHA-256 : {prepared.pdf_sha256}</p>
          <label className="mt-3 flex items-start gap-2 text-xs font-semibold" style={{ color: P.text }}>
            <input type="checkbox" checked={acknowledged}
              onChange={e => {
                // HTML disabled is a UX guard; the handler must also fail closed.
                if (previewVerified && !busy && !disabled) setAcknowledged(e.target.checked);
              }}
              disabled={!previewVerified || !!busy || disabled} />
            J'ai personnellement vérifié les repères, la calibration, les mesures et ce PDF descriptif exact.
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={printPrepared}
              disabled={!previewVerified || !acknowledged || !!busy || disabled} className="mt-3 inline-flex items-center gap-2 rounded-xl border px-4 py-3 text-xs font-black disabled:opacity-40"
              style={{ borderColor: P.border, color: P.text }}>
              Imprimer ce bilan A4
            </button>
            <button type="button" onClick={() => void archive()}
              disabled={!previewVerified || !acknowledged || !!busy || disabled} className="mt-3 inline-flex items-center gap-2 rounded-xl px-4 py-3 text-xs font-black text-white disabled:opacity-40"
              style={{ background: P.accent }}>
              {busy === 'archive' ? <Loader2 size={16} className="animate-spin" /> : <Archive size={16} />}
              Valider et archiver ce bilan A4
            </button>
          </div>
          <p className="mt-2 flex items-center gap-1 text-[10px]" style={{ color: P.textMuted }}>
            <CheckCircle2 size={12}/> Aucun archivage par l'action Imprimer. Validation enregistrée avec votre identité et la révision de l'étude.
          </p>
        </div>
      )}
    </div>
  );
};

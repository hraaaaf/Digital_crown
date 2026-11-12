/** Descriptive A4 V1: exact preview -> explicit clinician approval -> archive.
 * No electronic signature, no clinical diagnosis/treatment activation.
 * This component never relies on the generic archive:true PDF route. */
import React, { useEffect, useRef, useState } from 'react';
import { Archive, CheckCircle2, Eye, Loader2, ShieldCheck, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../../../services/api';
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
    if (!prepared || !previewUrl || !acknowledged || busy) return;
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
    if (!patientId || !analysisId || !prepared || !acknowledged || !snapshot || inFlight.current) return;
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
          <iframe title="Bilan descriptif A4 soumis à validation" src={previewUrl} className="mt-3 h-[55vh] w-full rounded-lg border" />
          <p className="mt-2 font-mono text-[10px] break-all" style={{ color: P.textMuted }}>SHA-256 : {prepared.pdf_sha256}</p>
          <label className="mt-3 flex items-start gap-2 text-xs font-semibold" style={{ color: P.text }}>
            <input type="checkbox" checked={acknowledged} onChange={e => setAcknowledged(e.target.checked)} disabled={!!busy} />
            J'ai personnellement vérifié les repères, la calibration, les mesures et ce PDF descriptif exact.
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={printPrepared}
              disabled={!acknowledged || !!busy || disabled} className="mt-3 inline-flex items-center gap-2 rounded-xl border px-4 py-3 text-xs font-black disabled:opacity-40"
              style={{ borderColor: P.border, color: P.text }}>
              Imprimer ce bilan A4
            </button>
            <button type="button" onClick={() => void archive()}
              disabled={!acknowledged || !!busy || disabled} className="mt-3 inline-flex items-center gap-2 rounded-xl px-4 py-3 text-xs font-black text-white disabled:opacity-40"
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

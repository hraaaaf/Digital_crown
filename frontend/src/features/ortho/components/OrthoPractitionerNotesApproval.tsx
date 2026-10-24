import React, { useCallback, useEffect, useRef, useState } from 'react';
import { cephaloRepository } from '../cephaloRepository';
import { useOrthoStore } from '../stores/useOrthoStore';

type NoteState = Awaited<ReturnType<typeof cephaloRepository.readPractitionerNotes>>;

/**
 * Explicit clinician action — not a scientific R14 validation.
 * Never silently approves imported ai_diagnostic or historical clinical_data.
 */
export const OrthoPractitionerNotesApproval: React.FC<{ P: any }> = ({ P }) => {
  const patientId = useOrthoStore(s => s.patientId);
  const analysisId = useOrthoStore(s => s.analysisId);
  const diag = useOrthoStore(s => s.diag);
  const ddm = useOrthoStore(s => s.ddm);
  const [record, setRecord] = useState<NoteState | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [molarRight, setMolarRight] = useState('');
  const [molarLeft, setMolarLeft] = useState('');
  const [canineRight, setCanineRight] = useState('');
  const [canineLeft, setCanineLeft] = useState('');
  const noteSignature = () => JSON.stringify({
    patientId, analysisId, molarRight, molarLeft, canineRight, canineLeft,
    source: sourceSignature(),
  });
  const approvedFingerprint = useRef<string | null>(null);
  const sequence = useRef(0);
  const sourceSignature = () => {
    const s = useOrthoStore.getState();
    return JSON.stringify({
      patientId: s.patientId, analysisId: s.analysisId,
      landmarks: s.local.landmarks, diag: s.diag,
      ddm: s.ddm, etape2Data: s.etape2Data, etape3Data: s.etape3Data,
      mmPerPixel: s.mmPerPixel,
    });
  };
  const stillSelected = (p: number, a: number) => {
    const s = useOrthoStore.getState();
    return s.patientId === p && s.analysisId === a;
  };

  const fetchCurrentRevision = useCallback(async (p: number, a: number) => {
    const response = await cephaloRepository.getAnalysis(a);
    if (!stillSelected(p,a) || response.id !== a) throw Error('Étude changée, recommencez.');
    const revision = response.angles_data?.scientific_read_path?.revision;
    if (!Number.isSafeInteger(revision) || revision <= 0) {
      throw Error('La révision scientifique est indisponible.');
    }
    return revision as number;
  }, []);

  useEffect(() => {
    const generation = ++sequence.current;
    setRecord(null);
    setLoading(true);
    setMessage('');
    approvedFingerprint.current = null;
    setMolarRight(''); setMolarLeft(''); setCanineRight(''); setCanineLeft('');
    if (!patientId || !analysisId) {
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const revision = await fetchCurrentRevision(patientId, analysisId);
        const loaded = await cephaloRepository.readPractitionerNotes(patientId, analysisId, revision);
        if (generation !== sequence.current || !stillSelected(patientId,analysisId)) return;
        setRecord(loaded);
        setMolarRight(String(loaded.notes?.moulages?.classe_molaire_droite || ''));
        setMolarLeft(String(loaded.notes?.moulages?.classe_molaire_gauche || ''));
        setCanineRight(String(loaded.notes?.moulages?.classe_canine_droite || ''));
        setCanineLeft(String(loaded.notes?.moulages?.classe_canine_gauche || ''));
        setLoading(false);
        // An approval loaded from another screen is intentionally NOT enough
        // to treat the current unsaved workspace as unchanged.
      } catch {
        if (generation === sequence.current) {
          setMessage('Validation des notes indisponible pour cette étude.');
          setLoading(false);
        }
      }
    })();
    return () => { sequence.current++; };
  }, [patientId, analysisId, fetchCurrentRevision]);

  const saveDraft = async () => {
    if (!patientId || !analysisId || busy || loading || !record) return;
    // Snapshot the visible clinician observations synchronously, before
    // silentSave may rehydrate/re-mount the cephalometric editor.
    const selectedAngles = { molarRight, molarLeft, canineRight, canineLeft };
    setBusy(true); setMessage('');
    approvedFingerprint.current = null;
    try {
      const store = useOrthoStore.getState();
      // Persist the exact study BEFORE binding notes to its next revision.
      await store.silentSave(analysisId, true);
      if (!stillSelected(patientId,analysisId)) throw Error('Étude changée.');
      const revision = await fetchCurrentRevision(patientId,analysisId);
      const previous = await cephaloRepository.readPractitionerNotes(patientId, analysisId, revision);
      const latest = useOrthoStore.getState();
      const casts: Record<string, string | number> = {};
      if (selectedAngles.molarRight) casts.classe_molaire_droite = selectedAngles.molarRight;
      if (selectedAngles.molarLeft) casts.classe_molaire_gauche = selectedAngles.molarLeft;
      if (selectedAngles.canineRight) casts.classe_canine_droite = selectedAngles.canineRight;
      if (selectedAngles.canineLeft) casts.classe_canine_gauche = selectedAngles.canineLeft;
      if (latest.diag.analyse_moulages.trim()) casts.commentaire = latest.diag.analyse_moulages.trim();
      if (latest.ddm.maxillaire !== '' && Number.isFinite(Number(latest.ddm.maxillaire))) {
        casts.ddm_maxillaire = Number(latest.ddm.maxillaire);
      }
      if (latest.ddm.mandibulaire !== '' && Number.isFinite(Number(latest.ddm.mandibulaire))) {
        casts.ddm_mandibulaire = Number(latest.ddm.mandibulaire);
      }
      const saved = await cephaloRepository.savePractitionerDraft(patientId, analysisId, {
        expected_revision: revision,
        expected_draft_version: previous.draft_version,
        moulages: casts,
        resume_diagnostique: latest.diag.synthese_diagnostique || '',
        plan_traitement: latest.diag.strategie_therapeutique || '',
      });
      if (!stillSelected(patientId,analysisId)) throw Error('Étude changée.');
      setRecord(saved);
      setMessage('Brouillon enregistré. Approbation explicite du dentiste requise.');
    } catch (error: any) {
      setMessage(error?.response?.data?.detail || error?.message || 'Enregistrement impossible.');
    } finally { setBusy(false); }
  };

  const approve = async () => {
    if (!patientId || !analysisId || busy || !record || record.stale || record.approved) return;
    setBusy(true); setMessage('');
    try {
      const revision = await fetchCurrentRevision(patientId, analysisId);
      if (revision !== record.analysis_revision) throw Error('Étude modifiée : recommencez.');
      const approved = await cephaloRepository.approvePractitionerDraft(patientId, analysisId, {
        expected_revision: revision, expected_draft_version: record.draft_version,
      });
      if (!stillSelected(patientId, analysisId)) throw Error('Étude changée.');
      setRecord(approved);
      approvedFingerprint.current = noteSignature();
      setMessage('Notes approuvées par le dentiste connecté (validation R14 distincte).');
    } catch (error: any) {
      setMessage(error?.response?.data?.detail || error?.message || 'Approbation refusée.');
    } finally { setBusy(false); }
  };

  const exportApproved = async () => {
    if (!patientId || !analysisId || !record?.approved || busy) return;
    setBusy(true); setMessage('');
    try {
      if (approvedFingerprint.current !== noteSignature()) {
        throw Error('L’espace de travail a changé ou a été rechargé. Réenregistrez et approuvez avant l’export.');
      }
      const revision = await fetchCurrentRevision(patientId, analysisId);
      if (revision !== record.analysis_revision) throw Error('L’étude a changé.');
      // Deliberately do not autosave a fresh scientific revision after sign-off.
      // PDF generator reads the approved note ONLY from the server DB.
      const pdf = await cephaloRepository.generatePDF(patientId, {
        analysis_id: analysisId, expected_revision: revision, archive: false,
      });
      if (!stillSelected(patientId,analysisId)) throw Error('Étude changée.');
      const url = URL.createObjectURL(pdf);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Bilan_ODF_notes_approuvees_${analysisId}.pdf`;
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 60000);
      setMessage('PDF généré à partir de la version approuvée (pas de validation scientifique R14).');
    } catch (error: any) {
      setMessage(error?.response?.data?.detail || error?.message || 'Export impossible.');
    } finally { setBusy(false); }
  };

  if (!patientId || !analysisId) return null;
  const changed = approvedFingerprint.current !== noteSignature();
  return (
    <section aria-busy={loading} className="rounded-xl border p-4 space-y-3" style={{ borderColor: P.border, background: P.bgCard }}>
      <h3 className="text-sm font-bold" style={{ color: P.text }}>Validation des notes du bilan orthodontique</h3>
      <p className="text-xs" style={{ color: P.textMuted }}>
        Examen des moulages, résumé diagnostique et plan de traitement. La validation
        est réservée au dentiste connecté et ne remplace pas l’évaluation scientifique R14.
      </p>
      {loading ? (
        <p role="status" className="text-xs" style={{ color: P.textMuted }}>
          Chargement de la version du dossier et des notes du praticien…
        </p>
      ) : record ? (
        <span data-testid="odf-note-source-ready" className="sr-only">Notes liées à l’étude chargées</span>
      ) : null}
      <p className="text-xs" style={{ color: P.textMuted }}>
        {record?.approved ? 'Notes approuvées' : record?.stale ? 'Anciennes notes invalidées par une modification de l’étude' : 'Notes non approuvées'}
        {record ? ` · Version ${record.draft_version}` : ''}
      </p>
      <fieldset className="grid grid-cols-2 gap-2">
        <legend className="mb-2 text-xs font-semibold" style={{ color: P.text }}>
          Classe d’Angle — examen clinique des moulages uniquement
        </legend>
        {([
          ['Molaire droite', molarRight, setMolarRight, 'molaire-droite'],
          ['Molaire gauche', molarLeft, setMolarLeft, 'molaire-gauche'],
          ['Canine droite', canineRight, setCanineRight, 'canine-droite'],
          ['Canine gauche', canineLeft, setCanineLeft, 'canine-gauche'],
        ] as const).map(([label, value, update, id]) => (
          <label key={id} className="text-xs" style={{ color: P.textMuted }}>
            {label}
            <select data-testid={`odf-angle-${id}`} value={value}
              disabled={busy || loading || !record}
              onChange={event => update(event.target.value)}
              className="mt-1 w-full rounded-lg border px-2 py-2 text-xs"
              style={{ borderColor: P.border, background: P.bgCard, color: P.text }}>
              <option value="">Non renseignée</option>
              <option value="Classe I">Classe I</option>
              <option value="Classe II">Classe II</option>
              <option value="Classe III">Classe III</option>
            </select>
          </label>
        ))}
        <p className="col-span-2 text-xs" style={{ color: P.textMuted }}>
          Ces classes sont renseignées par le dentiste après examen occlusal.
          Elles ne sont pas déduites de la téléradiographie de profil.
        </p>
      </fieldset>
      <div className="flex flex-wrap gap-2">
        <button type="button" disabled={busy || loading || !record} onClick={saveDraft}
          className="rounded-lg border px-3 py-2 text-xs font-semibold"
          style={{ borderColor: P.border, color: P.text }}>
          1. Enregistrer le brouillon
        </button>
        <button type="button" disabled={busy || !record || record.approved || record.stale || record.draft_version < 1}
          onClick={approve} className="rounded-lg border px-3 py-2 text-xs font-semibold"
          style={{ borderColor: P.border, color: P.text }}>
          2. Approuver mes notes
        </button>
        <button type="button" disabled={busy || !record?.approved || changed}
          onClick={exportApproved} className="rounded-lg border px-3 py-2 text-xs font-semibold"
          style={{ borderColor: P.border, color: P.text }}>
          3. Exporter le PDF approuvé
        </button>
      </div>
      {record?.approved && changed && (
        <p className="text-xs" style={{ color: P.accentWarning }}>
          Après modification ou rechargement du dossier, enregistrez puis approuvez les notes à nouveau avant l’export.
        </p>
      )}
      {message && <p role="status" className="text-xs" style={{ color: P.text }}>{message}</p>}
    </section>
  );
};

"""V1 A4 workflow guardrails: preview, print, and archive remain distinct.

Synthetic contract tests only; no real patient, OS printer, or archive write.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_step_four_shows_preview_print_and_explicit_hold_for_archive():
    ui = _source("frontend/src/features/ortho/components/Step4Documents.tsx")
    assert "Prévisualiser</button>" in ui
    assert "Imprimer</button>" in ui
    assert "Archivage suspendu</button>" in ui
    assert "onClick={handlePrintBilan}" in ui
    assert "await onPrintPDF()" in ui
    assert 'data-testid="unsigned-cephalo-archive-hold"' in ui


def test_store_print_is_pdf_draft_never_archive_and_checks_selection():
    store = _source("frontend/src/features/ortho/stores/useOrthoStore.ts")
    print_action = store.split("  handlePrint: async (", 1)[1]
    assert "archive: false" in print_action
    assert "archive: true" not in print_action
    assert "generatePDF(s.patientId" in print_action
    assert "prepareBoundCephaloDocumentSource" in print_action
    assert "bound.analysis_id !== s.analysisId" in print_action
    assert "if (!stillSelected()) throw" in print_action
    assert "window.open('', '_blank')" in print_action
    assert "printWindow.close()" in print_action
    assert "frame.contentWindow?.print()" in print_action
    assert "URL.revokeObjectURL(pdfUrl)" in print_action


def test_preview_remains_draft_and_archive_requires_separate_server_gate():
    store = _source("frontend/src/features/ortho/stores/useOrthoStore.ts")
    preview = store.split("  handlePreview: async () => {", 1)[1].split("  handlePrint: async", 1)[0]
    assert "archive: false" in preview
    server = _source("backend/routers/patients.py")
    assert "Archivage officiel refusé" in server
    assert "BROUILLON NON SIGNÉ" in server
    assert "already_archived_pdf" in server  # prior archived rows remain safeguarded


def test_no_v1_diagnosis_or_treatment_promotion_from_print():
    source = _source("backend/services/cephalo_r15_clinical_studio.py")
    assert '"clinical_validation_available": False' in source
    print_action = _source("frontend/src/features/ortho/stores/useOrthoStore.ts").split("  handlePrint: async (", 1)[1]
    assert "snapshotCephaloPdfClinicalInputs(s)" in print_action
    assert "sign_document" not in print_action

"""Static guardrails on secondary/legacy archive entrypoints.

These tests complement (not replace) authenticated HTTP and browser E2E tests.
No patient fixtures are required; they prevent obsolete official-archive
expectations from silently returning to the source tree.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_legacy_hook_never_promotes_unsigned_print_to_official_archive():
    source = (ROOT / "frontend/src/features/ortho/hooks/useCephaloPersistence.ts").read_text(encoding="utf-8")
    assert "archive: !preview" not in source
    assert "archive: true" not in source
    assert "archive: false" in source
    assert "Brouillon PDF non signé" in source


def test_authenticated_browser_scripts_assert_both_unsigned_http_denial_and_ui_hold():
    for filename in (
        "certify-ceph-p2ter-authenticated-cabinet.mjs",
        "fue-ceph-p2ter-first-value.mjs",
    ):
        source = (ROOT / "frontend/scripts" / filename).read_text(encoding="utf-8")
        assert "Archivage suspendu" in source
        assert "BROUILLON NON SIGNÉ" in source
        assert "archive:true" in source
        assert "archive:false" in source or "archive!==false" in source
        assert "OFFICIAL_ARCHIVE_REPLAY" not in source
        assert "Archiver le bilan" not in source


def test_authenticated_real_cabinet_workflow_never_requires_new_unsigned_archives():
    source = (ROOT / ".github/workflows/ceph-p2ter-master-bridge-real-cabinet.yml").read_text(encoding="utf-8")
    assert "len(rows)==0" in source
    assert "UNSIGNED_OFFICIAL_ARCHIVE_HOLD" in source
    assert "OFFICIAL_ARCHIVE_REPLAY" not in source
    assert "len(rows)==2" not in source
    assert "P2TER_UNSIGNED_A4_NO_OFFICIAL_ARCHIVE_AND_DRAFT_PROOF_PASS" in source

"""Pre-audit upstream PDF generator collision guard; synthetic and nonclinical.

Guarantee same-second/same-name source generators cannot overwrite another
generated PDF before ArchiveService is invoked. No application of restoration.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.services.generators.pdf_output_safety import reserve_generated_pdf_path
from backend.services.generators.accounting_gen import AccountingGenerator
from backend.services.generators.ordonnance_gen import OrdonnanceGenerator
from backend.services.generators.certificat_gen import CertificatGenerator
from backend.services.generators.libre_gen import LibreGenerator

PDF_A = b"%PDF-1.4\nfirst-fictional-patient\n%%EOF\n"
PDF_B = b"%PDF-1.4\nsecond-fictional-patient\n%%EOF\n"


@pytest.mark.parametrize("generator_name", ["ordonnance", "certificat", "accounting_note", "accounting_devis", "libre"])
def test_upstream_generators_reserve_distinct_pdf_paths_for_same_patient_and_second(
    tmp_path, generator_name,
):
    """Even unchanged patient/name/timestamp, a generated file is never reused."""
    person = SimpleNamespace(nom="SYNTHESE", prenom="FICTION", date_naissance=None)
    if generator_name == "ordonnance":
        generator = object.__new__(OrdonnanceGenerator)
        generator.output_dir = str(tmp_path)
        get_path = lambda: generator._get_save_path(person, SimpleNamespace())
    elif generator_name == "certificat":
        generator = object.__new__(CertificatGenerator)
        generator.output_dir = str(tmp_path)
        get_path = lambda: generator._get_save_path(person, SimpleNamespace())
    elif generator_name.startswith("accounting"):
        generator = object.__new__(AccountingGenerator)
        generator.base_output_dir = str(tmp_path)
        prefix = "NOTE" if generator_name == "accounting_note" else "DEVIS"
        get_path = lambda: generator._get_save_path(person, prefix, SimpleNamespace())
    else:
        generator = object.__new__(LibreGenerator)
        generator.output_dir = str(tmp_path)
        get_path = lambda: generator._get_save_path(person, "Texte fictif")

    first = Path(get_path())
    assert first.exists() and first.stat().st_size == 0
    first.write_bytes(PDF_A)
    second = Path(get_path())
    assert second != first
    assert second.parent == first.parent
    assert second.exists() and second.stat().st_size == 0
    second.write_bytes(PDF_B)
    assert first.read_bytes() == PDF_A and second.read_bytes() == PDF_B


def test_concurrent_generations_reserve_unique_paths_exclusively(tmp_path):
    def make_file(index):
        path = Path(reserve_generated_pdf_path(tmp_path, "CERTIFICAT_FICTION_20261107_120000.pdf"))
        content = ("fake-pdf-" + str(index)).encode()
        path.write_bytes(content)
        return path, content

    with ThreadPoolExecutor(max_workers=8) as pool:
        created = list(pool.map(make_file, range(48)))
    assert len({path.name.casefold() for path, _ in created}) == len(created)
    assert all(path.read_bytes() == content for path, content in created)


def test_exclusive_paths_sanitize_unsafe_names_without_touching_old_content(tmp_path):
    victim = tmp_path / "CERTIFICAT_patient_20261107_120000.pdf"
    victim.write_bytes(PDF_A)
    new_path = Path(reserve_generated_pdf_path(
        tmp_path,
        'CERTIFICAT_../CON\\ALICE:BAD?*_20261107_120000.pdf',
    ))
    assert new_path.parent == tmp_path
    assert new_path.name not in {victim.name, ".."}
    assert not any(ch in new_path.name for ch in '/\\<>:"|?*')
    assert victim.read_bytes() == PDF_A
    assert new_path.exists() and new_path.stat().st_size == 0


def test_relative_output_path_keeps_legacy_static_documents_convention(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = reserve_generated_pdf_path(
        "static/documents/2026/11",
        "CERTIFICAT_SYNTHETIQUE_20261107_120000.pdf",
    )
    path = Path(result)
    assert not path.is_absolute()
    assert path.parts[:2] == ("static", "documents")
    assert path.is_file() and path.stat().st_size == 0
    assert path.resolve().is_relative_to(tmp_path.resolve())


def test_reportlab_can_render_to_exclusively_reserved_filename(tmp_path):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate

    path = reserve_generated_pdf_path(tmp_path, "ORDONNANCE_TEST_20261107_120000.pdf")
    assert Path(path).exists()
    doc = SimpleDocTemplate(path)
    doc.build([Paragraph("Contenu fictif", getSampleStyleSheet()["Normal"])])
    assert Path(path).read_bytes().startswith(b"%PDF-")
    first = Path(path).read_bytes()

    second = reserve_generated_pdf_path(tmp_path, "ORDONNANCE_TEST_20261107_120000.pdf")
    SimpleDocTemplate(second).build([Paragraph("Second document fictif", getSampleStyleSheet()["Normal"])])
    assert Path(path).read_bytes() == first
    assert Path(second).read_bytes().startswith(b"%PDF-")
    assert path != second

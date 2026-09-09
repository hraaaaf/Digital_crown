from datetime import date
from pathlib import Path
from types import SimpleNamespace

from backend.schemas.documents import DevisData
from backend.services.generators.accounting_gen import AccountingGenerator
from backend.services.generators.certificat_gen import CertificatGenerator


def _assert_real_pdf(path: str) -> None:
    pdf_path = Path(path)
    assert pdf_path.is_file()
    payload = pdf_path.read_bytes()
    assert payload.startswith(b"%PDF-")
    assert len(payload) > 1_000
    assert b"%%EOF" in payload[-1_024:]


def _patient():
    return SimpleNamespace(
        nom="CERTIFICATION",
        prenom="Document Studio",
        date_naissance=date(1990, 1, 1),
        sexe="M",
    )


def test_certificate_generator_writes_real_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "backend.services.generators.certificat_gen.resolve_certificate_signer_name",
        lambda _user: "Dentiste Certification",
    )
    data = SimpleNamespace(
        reason="Certificat de Présence",
        days=0,
        content=None,
        observations="",
        doc_date=date(2026, 9, 9),
        start_date=None,
    )

    output = CertificatGenerator(output_dir=str(tmp_path)).generate(_patient(), data)

    _assert_real_pdf(output)


def test_devis_generator_writes_real_pdf_from_consistent_teeth_data(tmp_path):
    data = DevisData(
        items=[
            {
                "acte": "Composite 2 faces",
                "dent": "16",
                "dents": [16],
                "prix_unitaire": 700,
            }
        ],
        teeth_data=[
            {
                "tooth_number": 16,
                "treatments": [
                    {
                        "code": "COMP2",
                        "name": "Composite 2 faces",
                        "price": 700,
                    }
                ],
                "surfaces": ["M", "O"],
                "notes": "Certification PDF",
            }
        ],
        doc_date=date(2026, 9, 9),
    )

    output = AccountingGenerator(base_output_dir=str(tmp_path)).generate_devis(
        _patient(),
        data,
        document_number="CERT-001",
    )

    _assert_real_pdf(output)

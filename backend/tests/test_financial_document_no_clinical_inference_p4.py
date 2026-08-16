import asyncio
from types import SimpleNamespace

from backend.routers import documents
from backend.schemas.documents import DocumentRequest


class _Query:
    def __init__(self, value):
        self.value = value

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.value


class _DB:
    def __init__(self, patient):
        self.patient = patient

    def query(self, *args, **kwargs):
        return _Query(self.patient)


async def _return_fake_pdf(*args, **kwargs):
    return "/tmp/note_honoraires.pdf"


async def _no_warnings(*args, **kwargs):
    return []


def test_financial_note_never_infers_radiography_from_act_keywords(monkeypatch):
    patient = SimpleNamespace(id=1)
    current_user = SimpleNamespace(id=7, get_employer_id=lambda: 7)
    db = _DB(patient)
    req = DocumentRequest(
        type="note",
        patient_id=1,
        payment_status="EN_ATTENTE",
        data={
            "payments": [
                {"acte": "Couronne céramique sur implant", "montant": 3500},
            ]
        },
    )

    monkeypatch.setattr(documents, "require_document_permission", lambda *args, **kwargs: None)
    monkeypatch.setattr(documents, "assert_patient_access", lambda *args, **kwargs: None)
    monkeypatch.setattr(documents.asyncio, "to_thread", _return_fake_pdf)
    monkeypatch.setattr(documents, "should_archive_financial_document", lambda *args, **kwargs: False)
    monkeypatch.setattr(documents, "should_learn_financial_document", lambda *args, **kwargs: False)
    monkeypatch.setattr(documents, "should_offer_financial_rdv_suggestion", lambda *args, **kwargs: False)
    monkeypatch.setattr(documents.coherence_service, "analyze_coherence", _no_warnings)
    monkeypatch.setattr(documents.audit_service, "log", lambda *args, **kwargs: None)

    result = asyncio.run(
        documents.generate_document(
            req,
            archive=False,
            preview=False,
            db=db,
            current_user=current_user,
        )
    )

    assert result["rdv_suggestion"] is None
    assert result["suggest_radio"] is False

"""P6 consumer reconciliation: organization, actor and archive truth."""
import os
from datetime import datetime
from types import SimpleNamespace

import pytest

from backend import models
from backend.schemas import installments as installment_schemas
from backend.security import get_password_hash
from backend.services.document_factory import DocumentFactory
from backend.services.generators.accounting_gen import AccountingGenerator
from backend.services.generators.installment_gen import _cabinet_contact_lines, generate_installment_plan
from backend.services.generators.tenant_aware_accounting_gen import TenantAwareAccountingGenerator


def _user(db, email: str, *, employer_id=None, name="Dr Test"):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role=models.UserRole.DENTISTE,
        nom_complet=name,
        employer_id=employer_id,
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _cabinet(db, owner, *, name="Cabinet Employeur"):
    config = models.CabinetConfig(
        owner_id=owner.id,
        nom_cabinet=name,
        nom_praticien=owner.nom_complet or "",
        footer_address="2 avenue Footer",
        footer_phones="",
        contacts_json={
            "fixe": {"enabled": True, "value": "0537111111"},
            "whatsapp": {"enabled": True, "value": "0666111111"},
        },
        is_initialized=True,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def _patient(db, owner, *, nom="Patient", prenom="Test"):
    patient = models.Patient(
        nom=nom,
        prenom=prenom,
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _plan(db, patient, *, title="Traitement P6", total=1000.0):
    plan = models.InstallmentPlan(
        patient_id=patient.id,
        title=title,
        total_amount=total,
    )
    db.add(plan)
    db.flush()
    db.add(models.Installment(
        plan_id=plan.id,
        label="Versement 1",
        amount=total,
        due_date=datetime(2026, 9, 1),
        status="EN_ATTENTE",
    ))
    db.commit()
    db.refresh(plan)
    return plan


@pytest.mark.parametrize("method_name, number_kw", [
    ("generate_note", "facture_number"),
    ("generate_devis", "document_number"),
])
def test_accounting_adapter_uses_employer_for_config_and_preserves_actor(
    db, monkeypatch, method_name, number_kw
):
    owner = _user(db, f"p6-owner-{method_name}@test.ma", name="Dr Owner")
    actor = _user(db, f"p6-actor-{method_name}@test.ma", employer_id=owner.id, name="Dr Secondary")
    config = _cabinet(db, owner)
    captured = {}

    def fake_parent_generate(self, patient, data, db=None, user_id=None, **kwargs):
        captured["lookup_user_id"] = user_id
        captured["number"] = kwargs.get(number_kw)
        resolved_config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user_id).first()
        resolved_user = db.query(models.User).filter(models.User.id == user_id).first()
        return self._build_pdf("fake.pdf", [], "", config=resolved_config, user=resolved_user)

    def fake_parent_build(self, filepath, elements, cloture_text, config=None, user=None, **kwargs):
        captured["config"] = config
        captured["actor"] = user
        return filepath

    monkeypatch.setattr(AccountingGenerator, method_name, fake_parent_generate)
    monkeypatch.setattr(AccountingGenerator, "_build_pdf", fake_parent_build)

    generator = TenantAwareAccountingGenerator()
    method = getattr(generator, method_name)
    result = method(
        SimpleNamespace(),
        SimpleNamespace(),
        db=db,
        user_id=actor.id,
        **{number_kw: "P6-1"},
    )

    assert result == "fake.pdf"
    assert captured["lookup_user_id"] == owner.id
    assert captured["number"] == "P6-1"
    assert captured["config"].id == config.id
    assert captured["actor"].id == actor.id
    assert generator._actor_context.get() is None


def test_installment_preview_uses_employer_config_and_real_actor(db, monkeypatch, tmp_path):
    from backend.routers import installments as installments_router
    from backend.services.generators import installment_receipt_gen

    owner = _user(db, "p6-owner-preview@test.ma", name="Dr Owner")
    actor = _user(db, "p6-actor-preview@test.ma", employer_id=owner.id, name="Dr Secondary")
    config = _cabinet(db, owner)
    patient = _patient(db, owner)
    captured = {}

    def fake_receipt(**kwargs):
        captured.update(kwargs)
        path = tmp_path / "preview.pdf"
        path.write_bytes(b"preview")
        return str(path)

    monkeypatch.setattr(installment_receipt_gen, "generate_installment_receipt", fake_receipt)

    req = installment_schemas.InstallmentPreviewRequest(
        patient_id=patient.id,
        title="Plan preview",
        total_amount=500.0,
        items=[{"label": "Acompte", "amount": 500.0, "due_date": "2026-09-01", "paid": False}],
    )
    response = installments_router.generate_installment_preview(req, db=db, current_user=actor)

    assert response["pdf_url"].endswith("preview.pdf")
    assert captured["config"].id == config.id
    assert captured["config"].owner_id == owner.id
    assert captured["user"].id == actor.id


def test_final_installment_uses_real_archive_contract(db, monkeypatch, tmp_path):
    import backend.services.archive_service as archive_service_module
    import backend.services.document_factory as factory_module

    owner = _user(db, "p6-owner-final@test.ma", name="Dr Owner")
    actor = _user(db, "p6-actor-final@test.ma", employer_id=owner.id, name="Dr Secondary")
    config = _cabinet(db, owner)
    patient = _patient(db, owner)
    plan = _plan(db, patient)
    captured = {}

    def fake_generate(plan_arg, patient_arg, config_arg, output_dir):
        captured["config"] = config_arg
        path = tmp_path / "installment-final.pdf"
        path.write_bytes(b"%PDF-1.4\nP6 final\n")
        return str(path)

    monkeypatch.setattr(factory_module, "generate_installment_plan", fake_generate)
    monkeypatch.setattr(archive_service_module, "ARCHIVE_BASE_DIR", tmp_path / "archives")

    factory = DocumentFactory.__new__(DocumentFactory)
    factory.output_dir = str(tmp_path)
    result = factory.create_installment_plan(db=db, plan_id=plan.id, user_id=actor.id, archive=True)
    archive = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == result["archive_id"]).first()

    assert captured["config"].id == config.id
    assert captured["config"].owner_id == owner.id
    assert archive is not None
    assert archive.patient_id == patient.id
    assert archive.uploaded_by_id == actor.id
    assert archive.document_type is models.DocumentType.AUTRE
    assert archive.tags == ["ECHEANCIER"]
    assert archive.clinical_data == {"kind": "ECHEANCIER", "plan_id": plan.id}
    assert archive.is_accounted is False
    assert archive.file_path.startswith("static/archives/")
    assert result["url"].endswith("/static/documents/installment-final.pdf")
    assert not hasattr(models, "Clinic")


def test_final_installment_preview_does_not_archive(db, monkeypatch, tmp_path):
    import backend.services.document_factory as factory_module

    owner = _user(db, "p6-owner-noarchive@test.ma")
    actor = _user(db, "p6-actor-noarchive@test.ma", employer_id=owner.id)
    _cabinet(db, owner)
    patient = _patient(db, owner)
    plan = _plan(db, patient)

    path = tmp_path / "preview-only.pdf"
    path.write_bytes(b"preview")
    monkeypatch.setattr(factory_module, "generate_installment_plan", lambda *args, **kwargs: str(path))

    factory = DocumentFactory.__new__(DocumentFactory)
    factory.output_dir = str(tmp_path)
    before = db.query(models.DocumentArchive).count()
    result = factory.create_installment_plan(db=db, plan_id=plan.id, user_id=actor.id, archive=False)

    assert result["archive_id"] is None
    assert db.query(models.DocumentArchive).count() == before


def test_final_installment_rejects_cross_tenant_patient(db, monkeypatch, tmp_path):
    import backend.services.document_factory as factory_module

    owner_a = _user(db, "p6-owner-a@test.ma")
    actor_a = _user(db, "p6-actor-a@test.ma", employer_id=owner_a.id)
    _cabinet(db, owner_a, name="Cabinet A")
    owner_b = _user(db, "p6-owner-b@test.ma")
    patient_b = _patient(db, owner_b, nom="Other")
    plan_b = _plan(db, patient_b)

    called = {"generator": False}

    def should_not_generate(*args, **kwargs):
        called["generator"] = True
        raise AssertionError("cross-tenant generation must be blocked before rendering")

    monkeypatch.setattr(factory_module, "generate_installment_plan", should_not_generate)
    factory = DocumentFactory.__new__(DocumentFactory)
    factory.output_dir = str(tmp_path)

    with pytest.raises(ValueError, match="Accès refusé"):
        factory.create_installment_plan(db=db, plan_id=plan_b.id, user_id=actor_a.id, archive=True)

    assert called["generator"] is False


def test_installment_renderer_uses_only_real_cabinet_config_fields(db, tmp_path):
    owner = _user(db, "p6-owner-render@test.ma")
    config = _cabinet(db, owner, name="Centre Dentaire P6")
    patient = _patient(db, owner, nom="Render")
    plan = _plan(db, patient, total=750.0)

    lines = _cabinet_contact_lines(config)
    assert lines == ["2 avenue Footer", "Tél: 0537111111 / WhatsApp: 0666111111"]

    filepath = generate_installment_plan(plan, patient, config, str(tmp_path))
    assert os.path.exists(filepath)
    assert os.path.getsize(filepath) > 0

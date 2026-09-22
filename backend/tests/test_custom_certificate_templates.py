from fastapi import HTTPException

from backend import models, schemas
from backend.routers import templates


def _user(db, email: str, employer_id: int | None = None):
    user = models.User(
        email=email,
        hashed_password="x",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
        nom_complet=email,
        employer_id=employer_id,
        permissions={"patients": True},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _certificate_template(name: str, body: str):
    return schemas.DocumentTemplateCreate(
        type=schemas.DocumentType.CERTIFICAT,
        style_key=schemas.StyleKey.SANINOVA,
        name=name,
        description="Modèle de certificat médical du cabinet",
        body_html=body,
        is_system=False,
        is_default=False,
    )


def test_custom_certificate_template_is_shared_inside_cabinet_and_isolated_between_tenants(db):
    owner_a = _user(db, "template-a@cabinet.test")
    teammate_a = _user(db, "template-a-team@cabinet.test", employer_id=owner_a.id)
    owner_b = _user(db, "template-b@cabinet.test")

    created = templates.create_template(
        _certificate_template(
            "Aptitude traitement",
            "Je certifie avoir examiné ce patient ce jour.",
        ),
        db=db,
        current_user=owner_a,
    )

    assert created.type == models.DocumentType.CERTIFICAT
    assert created.user_id == owner_a.id
    assert created.is_system is False

    owner_rows = templates.list_system_templates(
        type="CERTIFICAT",
        is_system=False,
        db=db,
        current_user=owner_a,
    )
    teammate_rows = templates.list_system_templates(
        type="CERTIFICAT",
        is_system=False,
        db=db,
        current_user=teammate_a,
    )
    other_rows = templates.list_system_templates(
        type="CERTIFICAT",
        is_system=False,
        db=db,
        current_user=owner_b,
    )

    assert [row["id"] for row in owner_rows] == [created.id]
    assert [row["id"] for row in teammate_rows] == [created.id]
    assert other_rows == []


def test_other_cabinet_cannot_read_custom_certificate_template_body(db):
    owner_a = _user(db, "template-read-a@cabinet.test")
    owner_b = _user(db, "template-read-b@cabinet.test")

    created = templates.create_template(
        _certificate_template(
            "Suivi médical",
            "Je certifie que le patient a été examiné dans le cadre de son suivi.",
        ),
        db=db,
        current_user=owner_a,
    )

    own = templates.get_template(created.id, db=db, current_user=owner_a)
    assert own.body_html.startswith("Je certifie")

    try:
        templates.get_template(created.id, db=db, current_user=owner_b)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("cross-tenant certificate template read must fail closed")


def test_custom_document_libre_template_uses_same_tenant_boundary(db):
    owner_a = _user(db, "template-libre-a@cabinet.test")
    owner_b = _user(db, "template-libre-b@cabinet.test")

    created = templates.create_template(
        schemas.DocumentTemplateCreate(
            type=schemas.DocumentType.DOCUMENT_LIBRE,
            style_key=schemas.StyleKey.SANINOVA,
            name="Lettre confrère",
            description="Modèle de document libre du cabinet",
            body_html="Cher confrère, je vous adresse ce patient pour avis spécialisé.",
            is_system=False,
            is_default=False,
        ),
        db=db,
        current_user=owner_a,
    )

    own_rows = templates.list_system_templates(
        type="DOCUMENT_LIBRE",
        is_system=False,
        db=db,
        current_user=owner_a,
    )
    other_rows = templates.list_system_templates(
        type="DOCUMENT_LIBRE",
        is_system=False,
        db=db,
        current_user=owner_b,
    )

    assert [row["id"] for row in own_rows] == [created.id]
    assert other_rows == []

    try:
        templates.get_template(created.id, db=db, current_user=owner_b)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("cross-tenant document libre template read must fail closed")

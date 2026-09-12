from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, text

from backend import models
from backend.models_document_provenance_p3 import (
    _apply_author_before_insert,
    _apply_author_before_update,
    _migrate_existing_document_archives,
    install_document_provenance_p3,
)
from backend.services.document_provenance_context import (
    effective_document_practitioner_id,
    get_document_author_practitioner_id,
    reset_document_author_practitioner_id,
    set_document_author_practitioner_id,
)
from backend.services.document_factory import DocumentFactory
from backend.services.practitioner_policy import (
    is_assignable_practitioner,
    resolve_document_author,
)


class _User(SimpleNamespace):
    def get_employer_id(self) -> int:
        return self.employer_id if self.employer_id is not None else self.id


class _Query:
    def __init__(self, result):
        self.result = result

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.result


class _DB:
    def __init__(self, result):
        self.result = result

    def query(self, *_args, **_kwargs):
        return _Query(self.result)


def _user(
    user_id: int,
    *,
    role=models.UserRole.DENTISTE,
    employer_id=None,
    active=True,
    approval=models.ApprovalStatus.APPROVED.value,
):
    return _User(
        id=user_id,
        role=role,
        employer_id=employer_id,
        is_active=active,
        approval_status=approval,
        email=f"u{user_id}@cabinet.test",
        nom_complet=f"Dr {user_id}",
    )


def test_assignable_practitioner_policy_is_same_cabinet_active_approved_only():
    owner = _user(1, role=models.UserRole.ADMIN)
    dentist = _user(2, employer_id=1)
    secretary = _user(3, role=models.UserRole.SECRETAIRE, employer_id=1)
    outsider = _user(4, employer_id=99)
    inactive = _user(5, employer_id=1, active=False)
    pending = _user(6, employer_id=1, approval="PENDING")

    assert is_assignable_practitioner(owner, 1) is True
    assert is_assignable_practitioner(dentist, 1) is True
    assert is_assignable_practitioner(secretary, 1) is False
    assert is_assignable_practitioner(outsider, 1) is False
    assert is_assignable_practitioner(inactive, 1) is False
    assert is_assignable_practitioner(pending, 1) is False


def test_document_author_defaults_to_authenticated_practitioner_only():
    dentist = _user(2, employer_id=1)
    assert resolve_document_author(_DB(None), dentist, None) is dentist

    secretary = _user(3, role=models.UserRole.SECRETAIRE, employer_id=1)
    with pytest.raises(HTTPException) as exc_info:
        resolve_document_author(_DB(None), secretary, None)
    assert exc_info.value.status_code == 422


def test_explicit_document_author_is_validated_fail_closed():
    secretary = _user(3, role=models.UserRole.SECRETAIRE, employer_id=1)
    dentist = _user(2, employer_id=1)
    assert resolve_document_author(_DB(dentist), secretary, dentist.id) is dentist

    outsider = _user(4, employer_id=99)
    with pytest.raises(HTTPException) as exc_info:
        resolve_document_author(_DB(outsider), secretary, outsider.id)
    assert exc_info.value.status_code == 403


def test_document_author_context_is_request_scoped_and_resettable():
    assert get_document_author_practitioner_id() is None
    assert effective_document_practitioner_id(11) == 11

    outer = set_document_author_practitioner_id(22)
    try:
        assert get_document_author_practitioner_id() == 22
        assert effective_document_practitioner_id(11) == 22
        inner = set_document_author_practitioner_id(33)
        try:
            assert effective_document_practitioner_id(11) == 33
        finally:
            reset_document_author_practitioner_id(inner)
        assert effective_document_practitioner_id(11) == 22
    finally:
        reset_document_author_practitioner_id(outer)

    assert get_document_author_practitioner_id() is None
    assert effective_document_practitioner_id(11) == 11


def test_provenance_columns_are_nullable_user_foreign_keys():
    install_document_provenance_p3()
    table = models.DocumentArchive.__table__

    for name in ("author_practitioner_id", "signed_by_practitioner_id", "signed_at"):
        assert name in table.c
        assert table.c[name].nullable is True

    for name in ("author_practitioner_id", "signed_by_practitioner_id"):
        foreign_keys = list(table.c[name].foreign_keys)
        assert len(foreign_keys) == 1
        assert foreign_keys[0].target_fullname == "users.id"
        assert foreign_keys[0].ondelete == "SET NULL"


def test_historical_schema_migration_preserves_row_and_does_not_backfill():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(text(
            "CREATE TABLE document_archives ("
            "id INTEGER PRIMARY KEY, file_hash TEXT NOT NULL)"
        ))
        connection.execute(text(
            "INSERT INTO document_archives (id, file_hash) VALUES (7, 'legacy-hash')"
        ))

        _migrate_existing_document_archives(None, connection)
        # Idempotence matters because cabinet startup can call create_all repeatedly.
        _migrate_existing_document_archives(None, connection)

        column_names = {
            column["name"] for column in inspect(connection).get_columns("document_archives")
        }
        assert {
            "author_practitioner_id",
            "signed_by_practitioner_id",
            "signed_at",
        }.issubset(column_names)

        row = connection.execute(text(
            "SELECT id, file_hash, author_practitioner_id, "
            "signed_by_practitioner_id, signed_at "
            "FROM document_archives WHERE id = 7"
        )).mappings().one()
        assert row["id"] == 7
        assert row["file_hash"] == "legacy-hash"
        assert row["author_practitioner_id"] is None
        assert row["signed_by_practitioner_id"] is None
        assert row["signed_at"] is None


def test_insert_hook_records_author_without_forging_signature():
    document = models.DocumentArchive()
    token = set_document_author_practitioner_id(42)
    try:
        _apply_author_before_insert(None, None, document)
    finally:
        reset_document_author_practitioner_id(token)

    assert document.author_practitioner_id == 42
    assert document.signed_by_practitioner_id is None
    assert document.signed_at is None


def test_regenerated_file_reassigns_author_and_invalidates_old_signature():
    document = models.DocumentArchive()
    document.file_hash = "old"
    document.author_practitioner_id = 10
    document.signed_by_practitioner_id = 10
    document.signed_at = datetime(2026, 9, 12, 12, 0, 0)
    document.file_hash = "new"

    token = set_document_author_practitioner_id(42)
    try:
        _apply_author_before_update(None, None, document)
    finally:
        reset_document_author_practitioner_id(token)

    assert document.author_practitioner_id == 42
    assert document.signed_by_practitioner_id is None
    assert document.signed_at is None


def test_document_factory_renders_visible_identity_from_validated_author():
    captured = {}

    def _generate(_patient, _data, *, db, user_id, custom_config):
        captured["user_id"] = user_id
        return "generated.pdf"

    factory = DocumentFactory.__new__(DocumentFactory)
    factory.ord_gen = SimpleNamespace(generate=_generate)

    token = set_document_author_practitioner_id(42)
    try:
        result = factory.create_ordonnance(
            SimpleNamespace(),
            SimpleNamespace(),
            db=None,
            user_id=11,
            custom_config=None,
        )
    finally:
        reset_document_author_practitioner_id(token)

    assert result == "generated.pdf"
    assert captured["user_id"] == 42

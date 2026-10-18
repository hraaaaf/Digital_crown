"""LOT05.7-G dormant security contract, NOT an enabled restore workflow.

This module is importable for future integration design, but no runtime entry
point imports or calls it. Clinical apply always denies regardless of flags.
The scanner checks an existing SQLAlchemy connection and a caller-provided
principal. It does not authenticate that principal: a trusted request boundary
must still be implemented and certified. No patient values are returned.
Only fake_lab_publish_no_replace can write, exclusively inside a temporary
fake fixture root. No clinical backup/restore rights are conferred.
"""
from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.core.schema_runtime import CURRENT_ALEMBIC_HEAD


class RestoreContractDenied(PermissionError):
    """Sanitized reason only; never patient identifiers or SQL rows."""


def require_clinical_apply(*_args, **_kwargs):
    """Unconditional blocker; no env/owner/boolean can enable actual apply."""
    raise RestoreContractDenied("LOT05_7_G_CLINICAL_APPLY_DISABLED")


# Exact known fields at neo000000031. NOT a guarantee for all other tables.
_JOIN_CHECKS = (
    ("PATIENT_OWNER", """
     SELECT COUNT(*) FROM patients p
     LEFT JOIN users u ON u.id=p.employer_id
     WHERE u.id IS NULL OR u.employer_id IS NOT NULL
     """),
    ("APPOINTMENT_PATIENT", """
     SELECT COUNT(*) FROM appointments a
     LEFT JOIN patients p ON p.id=a.patient_id
     WHERE a.patient_id IS NOT NULL AND
       (p.id IS NULL OR a.employer_id<>p.employer_id)
     """),
    ("APPOINTMENT_RESOURCE", """
     SELECT COUNT(*) FROM appointments a
     LEFT JOIN agenda_resources r ON r.id=a.resource_id
     WHERE a.resource_id IS NOT NULL AND
       (r.id IS NULL OR a.employer_id<>r.employer_id)
     """),
    ("ACTE_PRACTITIONER", """
     SELECT COUNT(*) FROM actes a
     LEFT JOIN patients p ON p.id=a.patient_id
     LEFT JOIN users u ON u.id=a.praticien_id
     WHERE p.id IS NULL OR u.id IS NULL OR
       p.employer_id<>COALESCE(u.employer_id,u.id)
     """),
    ("PAYMENT_ACTE_PATIENT", """
     SELECT COUNT(*) FROM payments m
     LEFT JOIN actes a ON a.id=m.acte_id
     WHERE m.acte_id IS NOT NULL AND
       (a.id IS NULL OR m.patient_id<>a.patient_id)
     """),
    ("DOCUMENT_UPLOADER", """
     SELECT COUNT(*) FROM document_archives d
     LEFT JOIN patients p ON p.id=d.patient_id
     LEFT JOIN users u ON u.id=d.uploaded_by_id
     WHERE p.id IS NULL OR (d.uploaded_by_id IS NOT NULL AND
       (u.id IS NULL OR p.employer_id<>COALESCE(u.employer_id,u.id)))
     """),
)


def _role_value(role):
    return getattr(role, "value", role)


def verify_owner_observation(connection, principal) -> int:
    """Read-only DB corroboration, never proof of request authentication.

    Principal is untrusted until an actual request-auth dependency attests it.
    No clinical apply caller exists in 05.7-G.
    """
    if principal is None:
        raise RestoreContractDenied("TRUSTED_PRINCIPAL_REQUIRED")
    owner = getattr(principal, "id", None)
    if type(owner) is not int or owner <= 0:
        raise RestoreContractDenied("PRINCIPAL_ID_INVALID")
    role = _role_value(getattr(principal, "role", None))
    if (getattr(principal, "is_active", None) is not True or
        getattr(principal, "employer_id", "MISSING") is not None or
        role not in ("DENTISTE", "ADMIN") or
        getattr(principal, "approval_status", None) != "approved"):
        raise RestoreContractDenied("OWNER_NOT_ELIGIBLE")
    try:
        row = connection.execute(text("""
SELECT id,role,is_active,employer_id,approval_status
FROM users WHERE id=:id
"""), {"id": owner}).one_or_none()
    except SQLAlchemyError as exc:
        raise RestoreContractDenied("OWNER_DB_LOOKUP_FAILED") from exc
    if (row is None or row.employer_id is not None or
        row.role != role or row.role not in ("ADMIN", "DENTISTE") or
        row.is_active not in (True, 1) or row.approval_status != "approved"):
        raise RestoreContractDenied("OWNER_RECORD_MISMATCH")
    return owner


def evaluate_tenant_snapshot_read_only(connection, principal, *, expected_owners):
    """Read schema and six tenant joins; NEVER grants patient import rights.

    The caller supplies explicit owners for a fabricated multi-cabinet fixture.
    Equality with the fixture is NOT a clinical owner authorization.
    """
    if connection.dialect.name not in ("sqlite", "postgresql"):
        raise RestoreContractDenied("UNSUPPORTED_DIALECT")
    if (not isinstance(expected_owners, tuple) or not expected_owners
            or any(type(x) is not int or x <= 0 for x in expected_owners)
            or len(set(expected_owners)) != len(expected_owners)):
        raise RestoreContractDenied("EXPLICIT_OWNER_SCOPE_REQUIRED")
    try:
        version = connection.execute(text(
            "SELECT version_num FROM alembic_version"
        )).scalars().all()
        if version != [CURRENT_ALEMBIC_HEAD]:
            raise RestoreContractDenied("ALEMBIC_HEAD_MISMATCH")
        owner = verify_owner_observation(connection, principal)
        if owner not in expected_owners:
            raise RestoreContractDenied("PRINCIPAL_OUT_OF_SCOPE")
        scopes = set(connection.execute(text(
            "SELECT DISTINCT employer_id FROM patients"
        )).scalars().all())
        if scopes != set(expected_owners):
            raise RestoreContractDenied("UNEXPECTED_TENANT_SCOPE")
        errors = []
        for code, query in _JOIN_CHECKS:
            if connection.execute(text(query)).scalar_one() != 0:
                errors.append(code)
        if errors:
            raise RestoreContractDenied("TENANT_RELATION_DENIED:" + ",".join(errors))
        if connection.dialect.name == "sqlite":
            if connection.exec_driver_sql("PRAGMA foreign_key_check").fetchone():
                raise RestoreContractDenied("FOREIGN_KEY_CHECK_FAILED")
        return {
            "schema_head": CURRENT_ALEMBIC_HEAD,
            "checked_join_families": len(_JOIN_CHECKS),
            "clinical_import_permitted": False,
            "clinical_restore_permitted": False,
        }
    except RestoreContractDenied:
        raise
    except (SQLAlchemyError, OSError, TypeError, ValueError) as exc:
        raise RestoreContractDenied("TENANT_SNAPSHOT_UNVERIFIABLE") from exc


def _check_fake_paths(root: Path, staged: Path, target: Path):
    if os.environ.get("LOT05G_SYNTHETIC_ONLY") != "1":
        raise RestoreContractDenied("FAKE_LAB_DISABLED")
    if (type(root) is not Path or type(staged) is not Path
            or type(target) is not Path):
        raise RestoreContractDenied("LAB_PATH_TYPE_INVALID")
    if (not root.is_absolute() or
        not re.fullmatch(r"lot05e_fake_sqlcipher_[a-zA-Z0-9_-]+", root.name)
            or root.is_symlink() or not root.is_dir()):
        raise RestoreContractDenied("NOT_AN_EPHEMERAL_FAKE_ROOT")
    if (staged.parent != target.parent or staged.parent.parent != root
            or not staged.parent.name.startswith("test_")
            or target.name != "restored_fake.db"
            or not staged.name.startswith(".lot05g_stage_")
            or staged.suffix != ".db"
            or staged.parent.is_symlink() or not staged.parent.is_dir()
            or staged.is_symlink() or not staged.is_file()
            or target.is_symlink() or target.exists()):
        raise RestoreContractDenied("FOREIGN_OR_OCCUPIED_FAKE_TARGET")
    if (root.resolve(strict=True) != root or
            staged.parent.resolve(strict=True) != staged.parent):
        raise RestoreContractDenied("FAKE_PARENT_REDIRECTED")
    if not stat.S_ISREG(staged.stat().st_mode):
        raise RestoreContractDenied("STAGE_NOT_REGULAR")


def fake_lab_publish_no_replace(root: Path, staged: Path, target: Path, *,
                                expected_sha256: str, race_hook=None) -> Path:
    """Synthetic same-filesystem publication, exclusive or DENY.

    Not a real Windows NTFS hostile-path defense; no ACL/reparse guarantee,
    directory durability guarantee, or multi-file/media atomicity.
    """
    _check_fake_paths(root, staged, target)
    if (type(expected_sha256) is not str or
            re.fullmatch(r"[a-f0-9]{64}", expected_sha256) is None):
        raise RestoreContractDenied("EXPECTED_DIGEST_REQUIRED")
    hasher = hashlib.sha256()
    with staged.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
        if hasher.hexdigest() != expected_sha256:
            raise RestoreContractDenied("STAGED_DIGEST_MISMATCH")
    if race_hook is not None:
        race_hook(target)  # adversarial TEST injection, no runtime hook
    if (not staged.parent.is_dir() or staged.parent.is_symlink()
            or staged.parent.resolve(strict=True) != staged.parent):
        raise RestoreContractDenied("FAKE_PARENT_REDIRECTED")
    try:
        os.link(staged, target, follow_symlinks=False)
    except FileExistsError as exc:
        raise RestoreContractDenied("ATOMIC_TARGET_ALREADY_EXISTS") from exc
    except (OSError, NotImplementedError) as exc:
        raise RestoreContractDenied("ATOMIC_LINK_UNAVAILABLE") from exc
    return target

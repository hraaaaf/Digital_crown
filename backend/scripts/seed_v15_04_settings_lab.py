"""Test-only seed for LOT04 Settings browser real-auth gate (never production)."""
import os
from pathlib import Path

if os.environ.get("ENVIRONMENT") != "test" or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "1":
    raise RuntimeError("SETTINGS_SEED_REQUIRES_ISOLATED_TEST_RUNTIME")
if os.environ.get("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db":
    raise RuntimeError("SETTINGS_SEED_REQUIRES_DISPOSABLE_T2_DB")
if not Path("t2-runtime-cert.db").is_file() or not os.environ.get("T2_PASSWORD"):
    raise RuntimeError("SETTINGS_SEED_CANNOT_CREATE_DB_OR_CREDENTIALS")

from backend import database, models
from backend.security import get_password_hash
from backend.services.station_print_held_claims_lab import claims, claim_events
from backend.services.station_print_attestation_recovery_v15 import uncertain_reviews

with database.SessionLocal() as db:
    root = db.query(models.User).filter(models.User.email == "t2-browser@cabinet.ma").one()
    delegated = db.query(models.User).filter(models.User.email == "t2-delegated-admin@cabinet.ma").one_or_none()
    if delegated is None:
        db.add(models.User(
            email="t2-delegated-admin@cabinet.ma",
            hashed_password=get_password_hash(os.environ["T2_PASSWORD"]),
            role=models.UserRole.ADMIN,
            nom_complet="Delegated T2 Synthetic Administrator",
            employer_id=root.id,
            is_active=True,
            is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
            permissions={"settings": True, "admin": True},
        ))
        db.commit()
    elif delegated.employer_id != root.id:
        raise RuntimeError("SETTINGS_SEED_WRONG_TENANT")
    # The owner-only read endpoint joins staged neo29/neo30 objects which are
    # NOT part of Base.metadata.create_all in the disposable T2 boot helper.
    for table in (claims, claim_events, uncertain_reviews):
        table.create(bind=db.get_bind(), checkfirst=True)
print("SETTINGS_T2_DISPOSABLE_OWNER_DELEGATED_AND_STAGED_TABLES_READY")

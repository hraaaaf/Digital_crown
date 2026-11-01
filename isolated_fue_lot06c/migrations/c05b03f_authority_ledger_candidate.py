"""Unchained C05B03F Alembic candidate: SQLCipher synthetic only, NEVER runtime."""
import os
from alembic import op
import sqlalchemy as sa

revision = "c05b03f_candidate"
down_revision = None
branch_labels = None
depends_on = None
NAMES = [f"c05b03f_{x}" for x in ("devices", "approvals", "receipts", "audit", "outbox")]

def _guard():
    con = op.get_bind()
    if (os.getenv("ENVIRONMENT") != "test"
        or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
        or os.getenv("DC06C05B03F_TEST_ONLY") != "1"
        or con.dialect.name != "sqlite"):
        raise RuntimeError("C05B03F_UNCHAINED_LAB_ONLY")
    if not con.exec_driver_sql("PRAGMA cipher_version").scalar_one_or_none():
        raise RuntimeError("C05B03F_NATIVE_SQLCIPHER_REQUIRED")
    if con.exec_driver_sql("PRAGMA foreign_keys").scalar_one() != 1:
        raise RuntimeError("C05B03F_FOREIGN_KEYS_REQUIRED")
    return con

def upgrade():
    _guard()
    op.create_table(NAMES[0],
        sa.Column("tenant", sa.Integer, primary_key=True),
        sa.Column("device", sa.String(64), primary_key=True),
        sa.Column("station", sa.String(36), nullable=False),
        sa.Column("token_sha", sa.String(64), nullable=False),
        sa.Column("generation", sa.Integer, nullable=False),
        sa.Column("active", sa.Integer, nullable=False),
        sa.CheckConstraint("generation > 0 AND active IN (0,1)"),
        sa.ForeignKeyConstraint(["tenant"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["station"], ["workstation_modes.id"], ondelete="RESTRICT"),
    )
    op.create_table(NAMES[1],
        sa.Column("tenant", sa.Integer, primary_key=True),
        sa.Column("device", sa.String(64), primary_key=True),
        sa.Column("capture", sa.String(128), primary_key=True),
        sa.Column("patient", sa.Integer, nullable=False),
        sa.Column("staff", sa.Integer, nullable=False),
        sa.Column("station", sa.String(36), nullable=False),
        sa.Column("station_revision", sa.Integer, nullable=False),
        sa.Column("generation", sa.Integer, nullable=False),
        sa.Column("asset_id", sa.Integer, nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("byte_size", sa.Integer, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("approved", sa.Integer, nullable=False),
        sa.UniqueConstraint("tenant", "asset_id"),
        sa.ForeignKeyConstraint(["tenant","device"], [NAMES[0]+".tenant",NAMES[0]+".device"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient"], ["patients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["staff"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["station"], ["workstation_modes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["asset_id"], ["clinical_assets.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("version > 0 AND byte_size > 0 AND generation > 0 AND station_revision >= 0"),
        sa.CheckConstraint("approved IN (0,1) AND length(digest)=64"),
    )
    op.create_table(NAMES[2],
        sa.Column("tenant", sa.Integer, primary_key=True),
        sa.Column("device", sa.String(64), primary_key=True),
        sa.Column("capture", sa.String(128), primary_key=True),
        sa.Column("receipt_id", sa.String(64), nullable=False, unique=True),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("asset_id", sa.Integer, nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.UniqueConstraint("tenant","asset_id"),
        sa.ForeignKeyConstraint(["tenant","device","capture"],
             [NAMES[1]+".tenant",NAMES[1]+".device",NAMES[1]+".capture"],ondelete="RESTRICT"),
        sa.CheckConstraint("version > 0 AND length(digest)=64"),
    )
    for name in NAMES[3:]:
        op.create_table(name,
            sa.Column("receipt_id", sa.String(64), primary_key=True),
            sa.Column("event", sa.String(32), nullable=False),
            sa.ForeignKeyConstraint(["receipt_id"],[NAMES[2]+".receipt_id"],ondelete="RESTRICT"),
        )
    op.execute("""
      CREATE TRIGGER c05b03f_approval_scoped BEFORE INSERT ON c05b03f_approvals
      BEGIN SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM clinical_assets a
        JOIN patients p ON p.id=NEW.patient
        JOIN users u ON u.id=NEW.staff
        JOIN workstation_modes w ON w.id=NEW.station
        JOIN c05b03f_devices d ON d.tenant=NEW.tenant AND d.device=NEW.device
        WHERE a.id=NEW.asset_id AND a.employer_id=NEW.tenant
          AND a.patient_id=NEW.patient AND a.created_by=NEW.staff
          AND p.employer_id=NEW.tenant AND p.deleted_at IS NULL
          AND w.employer_id=NEW.tenant AND w.revoked_at IS NULL
          AND w.mode_revision=NEW.station_revision
          AND d.station=NEW.station AND d.generation=NEW.generation AND d.active=1
          AND u.is_active=1 AND u.is_archived=0 AND u.is_suspended=0
          AND u.approval_status='approved'
          AND (u.id=NEW.tenant OR u.employer_id=NEW.tenant)
          AND a.sha256=NEW.digest AND a.byte_size=NEW.byte_size
          AND a.storage_key IS NOT NULL
      ) THEN RAISE(ABORT,'C05B03F_SCOPE_MISMATCH') END; END
    """)
    op.execute("""
      CREATE TRIGGER c05b03f_receipt_approved BEFORE INSERT ON c05b03f_receipts
      BEGIN SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM c05b03f_approvals a
        WHERE a.tenant=NEW.tenant AND a.device=NEW.device
          AND a.capture=NEW.capture AND a.approved=1
          AND a.version=NEW.version AND a.asset_id=NEW.asset_id AND a.digest=NEW.digest
      ) THEN RAISE(ABORT,'C05B03F_APPROVAL_REQUIRED') END; END
    """)
    for name in NAMES[2:]:
        for operation in ("UPDATE","DELETE"):
            op.execute(
                f'CREATE TRIGGER "{name}_{operation.lower()}_lock" '
                f'BEFORE {operation} ON "{name}" '
                "BEGIN SELECT RAISE(ABORT,'C05B03F_IMMUTABLE_LEDGER'); END"
            )
    for operation in ("UPDATE","DELETE"):
        op.execute(
            f'CREATE TRIGGER "c05b03f_approval_{operation.lower()}_freeze" '
            f'BEFORE {operation} ON c05b03f_approvals '
            "WHEN EXISTS(SELECT 1 FROM c05b03f_receipts r WHERE "
            "r.tenant=OLD.tenant AND r.device=OLD.device AND r.capture=OLD.capture) "
            "BEGIN SELECT RAISE(ABORT,'C05B03F_APPROVAL_FROZEN'); END"
        )

def downgrade():
    con = _guard()
    for name in NAMES:
        if con.exec_driver_sql(f'SELECT COUNT(*) FROM "{name}"').scalar_one():
            raise RuntimeError("C05B03F_DOWNGRADE_REQUIRES_EMPTY_LEDGER")
    for name in reversed(NAMES):
        op.drop_table(name)

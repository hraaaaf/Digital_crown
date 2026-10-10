"""Explicit operator setup for a fresh isolated cabinet; never called on normal startup."""
from __future__ import annotations
import json
import os
from pathlib import Path
from sqlalchemy.engine import make_url

def provision_new_cabinet(owner_email: str, password: str, *, resume: bool = False) -> None:
    # Validate before importing the database (which resolves/creates runtime paths).
    if os.getenv("ENVIRONMENT") != "cabinet":
        raise RuntimeError("New cabinet setup requires ENVIRONMENT=cabinet")
    if not owner_email or "@" not in owner_email or len(password) < 12:
        raise ValueError("An owner email and password of at least 12 characters are required")
    names = ("DIGITALCROWN_USER_DATA_DIR", "DIGITALCROWN_CONFIG_DIR",
             "DIGITALCROWN_RUNTIME_DIR", "DIGITALCROWN_LOG_DIR", "DIGITALCROWN_ENV_FILE", "MEDIA_ROOT")
    paths = {}
    for name in names:
        value = os.getenv(name, "").strip()
        if not value or not Path(value).is_absolute():
            raise RuntimeError("Every new cabinet path must be explicit and absolute")
        paths[name] = Path(value).resolve()
    data = paths["DIGITALCROWN_USER_DATA_DIR"]
    root = data.parent
    if data.name != "data" or any(not p.is_relative_to(root) for p in paths.values()):
        raise RuntimeError("New cabinet paths must share one dedicated instance root")
    # Refuse the default/historical namespace even if every override points there.
    from backend.core.platform import PlatformAdapter
    defaults = PlatformAdapter(environ={})
    if root == defaults.user_data_dir().resolve() or data == defaults.user_data_dir().resolve():
        raise RuntimeError("Historical/default data directory is forbidden")
    instance = os.getenv("DIGITALCROWN_INSTANCE_ID", "").strip()
    if not instance:
        raise RuntimeError("Explicit instance identity required")
    for key in ("SQLCIPHER_KEY_HEX", "MOBILE_PAIRING_KEY_HEX", "SECRET_KEY"):
        if not os.getenv(key):
            raise RuntimeError("Dedicated storage, mobile and authentication secrets required")
    from backend.core.key_material import sqlcipher_passphrase, mobile_pairing_key_hex
    sqlcipher_passphrase()
    mobile_pairing_key_hex()
    url = make_url(os.getenv("DATABASE_URL", ""))
    db_path = Path(url.database or "")
    if url.get_backend_name() != "sqlite" or not db_path.is_absolute() or db_path.resolve() != data / "clinical_vault.db":
        raise RuntimeError("Database must resolve to the new instance clinical_vault.db")
    # Serialize explicit setup/recovery before touching the schema or owner.
    from backend.core.platform import get_platform_adapter
    setup_lock = get_platform_adapter().try_acquire_process_lock(paths["DIGITALCROWN_RUNTIME_DIR"] / "new-cabinet-setup.lock")
    if setup_lock is None:
        raise RuntimeError("Another new-cabinet setup is running")
    with setup_lock:
        marker = paths["DIGITALCROWN_CONFIG_DIR"] / "new-cabinet-setup.json"
        if resume:
            if not marker.is_file() or json.loads(marker.read_text()) != {"instance_id": instance, "state": "pending"}:
                raise RuntimeError("Resume requires the matching incomplete new-cabinet setup marker")
        else:
            if db_path.exists() or marker.exists():
                raise RuntimeError("Existing database/setup refused; use explicit recovery or resume")
            marker.parent.mkdir(parents=True, exist_ok=True)
            with marker.open("x", encoding="utf-8") as stream:
                json.dump({"instance_id": instance, "state": "pending"}, stream)
        from backend import database, models
        from sqlalchemy import inspect, text
        if resume:
            # Recover an interrupted marker write only for the exact initial owner,
            # authenticated by its password and with no clinical/application data.
            with database.engine.connect() as connection:
                counts = {table: connection.execute(text('SELECT COUNT(*) FROM "' + table.replace('"','""') + '"')).scalar()
                          for table in inspect(connection).get_table_names() if table != "alembic_version"}
            if any(count for table, count in counts.items() if table not in {"users", "cabinet_configs"}):
                raise RuntimeError("Resume refused: database contains application data")
            if counts.get("users"):
                from backend.security import verify_password
                with database.SessionLocal() as session:
                    owner = session.query(models.User).one_or_none() if counts["users"] == 1 else None
                    cabinet = session.query(models.CabinetConfig).one_or_none() if counts.get("cabinet_configs") == 1 else None
                    if (owner is None or cabinet is None or owner.email != owner_email.strip().lower()
                            or owner.role != models.UserRole.DENTISTE or owner.employer_id is not None
                            or cabinet.owner_id != owner.id or not verify_password(password, owner.hashed_password)):
                        raise RuntimeError("Resume refused: initial owner identity is not verified")
                get_platform_adapter().atomic_write_text(marker, json.dumps({"instance_id": instance, "state": "complete"}))
                database.engine.dispose()
                return
            if counts.get("cabinet_configs"):
                raise RuntimeError("Resume refused: inconsistent initial configuration")
        from alembic import command
        from alembic.config import Config
        from backend.core.paths import AppPaths
        bundle = AppPaths.get_base_dir()
        config = Config(str(bundle / "alembic.ini"))
        config.set_main_option("script_location", str(bundle / "alembic"))
        command.upgrade(config, "head")
        from backend.security import get_password_hash
        with database.SessionLocal() as session:
            if session.query(models.User).count():
                raise RuntimeError("Existing owner refused")
            owner = models.User(email=owner_email.strip().lower(), hashed_password=get_password_hash(password),
                                role=models.UserRole.DENTISTE, is_active=True, is_licensed=False)
            session.add(owner)
            session.flush()
            session.add(models.CabinetConfig(owner_id=owner.id, is_initialized=False))
            session.commit()
        # Mark only after the owner transaction succeeded. No license bypass or workstation cookie.
        get_platform_adapter().atomic_write_text(marker, json.dumps({"instance_id": instance, "state": "complete"}))
        database.engine.dispose()

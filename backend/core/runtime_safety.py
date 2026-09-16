"""Fail-closed startup policy for schema/data-mutating boot paths.

The development checkout must never be able to reuse the cabinet database merely
because a caller selected ``ENVIRONMENT=development``.  Cabinet/production startup
is reserved for an independently certified immutable release; isolated development
and rehearsal startup require an explicit process-local attestation.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

from backend.core.platform import get_platform_adapter


DEV_ENVIRONMENTS = frozenset({"development", "local", "test"})
CABINET_ENVIRONMENTS = frozenset({"cabinet", "production"})

DEV_BOOTSTRAP = "isolated_dev_bootstrap"
MIGRATION_ONLY = "migration_only"
REHEARSAL_MIGRATION_ONLY = "rehearsal_migration_only"


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def canonical_database_target(database_url: str) -> str:
    """Return a password-free, stable target identity for an isolation attestation."""
    raw = str(database_url or "").strip()
    parsed = urlsplit(raw)
    if not parsed.scheme:
        return raw.lower()

    try:
        scheme = parsed.scheme.lower()
        base_scheme = scheme.split("+", 1)[0]
        if base_scheme in {"postgres", "postgresql"}:
            # SQLAlchemy driver aliases and PostgreSQL's loopback spellings must
            # identify the same server/database for the anti-accident guard.
            scheme = "postgresql"
            hostname = (parsed.hostname or "").lower()
            if hostname in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
                hostname = "loopback"
            elif ":" in hostname and not hostname.startswith("["):
                hostname = f"[{hostname}]"
            port_number = parsed.port if parsed.port is not None else 5432
            port = f":{port_number}"
            username = unquote(parsed.username or "")
            netloc = f"{username}@" if username else ""
            netloc += hostname + port
            # Query parameters are connection options, not database identity.
            path = unquote(parsed.path)
            return urlunsplit((scheme, netloc, path, "", ""))

        if base_scheme == "sqlite":
            # ``sqlite`` and ``sqlite+pysqlcipher`` can point to the same file;
            # never include the SQLCipher password in the attested identity.
            scheme = "sqlite"
            path = unquote(parsed.path)
            return urlunsplit((scheme, "", path, "", ""))

        hostname = (parsed.hostname or "").lower()
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        host = hostname
        port = f":{parsed.port}" if parsed.port is not None else ""
    except ValueError:
        return raw.lower()

    username = unquote(parsed.username or "")
    netloc = f"{username}@" if username else ""
    netloc += host + port
    return urlunsplit((parsed.scheme.lower(), netloc, unquote(parsed.path), "", ""))


def database_target_fingerprint(database_url: str) -> str:
    return hashlib.sha256(canonical_database_target(database_url).encode("utf-8")).hexdigest()


def _database_url_from_env_file(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        return ""
    return ""


def _known_cabinet_database_urls() -> list[str]:
    package_root = Path(__file__).resolve().parents[2]
    candidates = [package_root / "backend" / ".env.local", get_platform_adapter().cabinet_env_path()]
    return [url for path in candidates if (url := _database_url_from_env_file(path))]


def is_known_cabinet_database(database_url: str) -> bool:
    target = canonical_database_target(database_url)
    return any(canonical_database_target(url) == target for url in _known_cabinet_database_urls())


def is_explicitly_isolated(database_url: str) -> bool:
    """Require an explicit attestation and reject the known cabinet target.

    SQLite in-memory is structurally isolated.  Every persistent/remote target must
    additionally provide a fingerprint of the exact password-free target identity.
    """
    if not _truthy(os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME")):
        return False
    if is_known_cabinet_database(database_url):
        return False

    normalized = str(database_url or "").strip().lower()
    if normalized.startswith("sqlite:") and ":memory:" in normalized:
        return True

    expected = os.environ.get("DIGITALCROWN_ISOLATION_DB_FINGERPRINT", "").strip().lower()
    return bool(expected) and expected == database_target_fingerprint(database_url)


def is_certified_release() -> bool:
    """Verify the immutable release identity before cabinet/production boot."""
    root = Path(
        getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2])
    ).resolve()
    try:
        from backend.release_certification import (
            verify_installable_release_directory,
            verify_installable_release_identity,
        )

        if getattr(sys, "frozen", False):
            verify_installable_release_identity(root)
        else:
            verify_installable_release_directory(root)
        return True
    except Exception:
        return False


def assert_runtime_startup_allowed(cfg) -> str:
    """Return the only permitted boot policy or fail before any DB side effect."""
    environment = str(getattr(cfg, "ENVIRONMENT", os.environ.get("ENVIRONMENT", ""))).strip().lower()
    database_url = str(getattr(cfg, "DATABASE_URL", os.environ.get("DATABASE_URL", ""))).strip()

    if environment in CABINET_ENVIRONMENTS:
        if "--reload" in {arg.lower() for arg in sys.argv}:
            raise RuntimeError("SECURITE : --reload est interdit pour un runtime cabinet/production.")
        if not is_certified_release():
            raise RuntimeError(
                "SECURITE : cabinet/production exige un runtime INSTALLABLE_CERTIFIED; "
                "le dépôt de développement est refusé."
            )
        return MIGRATION_ONLY

    if "rehearsal" in environment:
        if not is_explicitly_isolated(database_url):
            raise RuntimeError(
                "SECURITE : rehearsal refusé sans attestation explicite de DB isolée."
            )
        return REHEARSAL_MIGRATION_ONLY

    if environment in DEV_ENVIRONMENTS:
        if not is_explicitly_isolated(database_url):
            raise RuntimeError(
                "SECURITE : runtime dev/test refusé sans attestation explicite de DB isolée."
            )
        return DEV_BOOTSTRAP

    raise RuntimeError(f"SECURITE : ENVIRONMENT non supporté/refusé: {environment or '<empty>'}")

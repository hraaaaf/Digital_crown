from __future__ import annotations

import base64
import hashlib
import json
import os
import platform as std_platform
import re
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from backend.core.paths import AppPaths
from backend.core.platform import get_platform_adapter
from backend.services.backup_service import BackupService

MANIFEST_SCHEMA = 1
UPDATE_PUBLIC_KEY_ENV = "DIGITALCROWN_UPDATE_PUBLIC_KEY_B64"
UPDATE_ROOT_NAME = "updates"
TRUST_STATE_NAME = "trusted_state.json"
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
MAX_MANIFEST_BYTES = 256 * 1024
MAX_ARTIFACT_BYTES = 8 * 1024**3


class UpdateSecurityError(RuntimeError):
    pass


class UpdatePreparationError(RuntimeError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_utc(value: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise UpdateSecurityError("UPDATE_MANIFEST_TIME_REQUIRED")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise UpdateSecurityError("UPDATE_MANIFEST_TIME_INVALID") from exc
    if parsed.tzinfo is None:
        raise UpdateSecurityError("UPDATE_MANIFEST_TIME_TZ_REQUIRED")
    return parsed.astimezone(timezone.utc)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_file_verified(source: Path, target: Path, expected_sha256: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".partial")
    try:
        with source.open("rb") as src, partial.open("wb") as dst:
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                dst.write(chunk)
            dst.flush()
            os.fsync(dst.fileno())
        if _sha256_file(partial) != expected_sha256:
            raise UpdatePreparationError("UPDATE_STAGED_COPY_CHECKSUM_INVALID")
        os.replace(partial, target)
    finally:
        partial.unlink(missing_ok=True)


def _normalize_arch(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"amd64", "x86_64", "x64"}:
        return "amd64"
    if normalized in {"arm64", "aarch64"}:
        return "arm64"
    return normalized or "unknown"


def _version_tuple(value: str) -> tuple[int, int, int]:
    text = str(value or "").strip()
    if not VERSION_PATTERN.fullmatch(text):
        raise UpdateSecurityError("UPDATE_VERSION_FORMAT_UNSUPPORTED")
    parts = tuple(int(part) for part in text.split("."))
    if len(parts) != 3:
        raise UpdateSecurityError("UPDATE_VERSION_FORMAT_UNSUPPORTED")
    return parts  # type: ignore[return-value]


class UpdateEngine:
    @staticmethod
    def root() -> Path:
        return get_platform_adapter().ensure_private_directory(
            AppPaths.get_user_data_dir() / UPDATE_ROOT_NAME
        )

    @classmethod
    def trust_state_path(cls) -> Path:
        return cls.root() / TRUST_STATE_NAME

    @classmethod
    def _read_trust_state(cls) -> dict[str, Any]:
        path = cls.trust_state_path()
        if not path.exists():
            return {
                "schema": 1,
                "highest_sequence": 0,
                "highest_manifest_sha256": None,
                "last_trusted_time": None,
                "installed_sequence": 0,
                "installed_version": None,
            }
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise UpdateSecurityError("UPDATE_TRUST_STATE_INVALID") from exc
        if not isinstance(payload, dict) or int(payload.get("schema", 0)) != 1:
            raise UpdateSecurityError("UPDATE_TRUST_STATE_SCHEMA_UNSUPPORTED")
        return payload

    @classmethod
    def _write_trust_state(cls, payload: dict[str, Any]) -> None:
        sanitized = {
            "schema": 1,
            "highest_sequence": int(payload.get("highest_sequence", 0)),
            "highest_manifest_sha256": payload.get("highest_manifest_sha256"),
            "last_trusted_time": payload.get("last_trusted_time"),
            "installed_sequence": int(payload.get("installed_sequence", 0)),
            "installed_version": payload.get("installed_version"),
        }
        get_platform_adapter().atomic_write_text(
            cls.trust_state_path(),
            json.dumps(sanitized, indent=2, sort_keys=True),
        )

    @staticmethod
    def _public_key(raw_b64: str | None = None) -> tuple[Ed25519PublicKey, str]:
        encoded = str(raw_b64 or os.getenv(UPDATE_PUBLIC_KEY_ENV, "")).strip()
        if not encoded:
            raise UpdateSecurityError("UPDATE_PUBLIC_KEY_REQUIRED")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except Exception as exc:
            raise UpdateSecurityError("UPDATE_PUBLIC_KEY_INVALID") from exc
        if len(raw) != 32:
            raise UpdateSecurityError("UPDATE_PUBLIC_KEY_INVALID")
        key_id = hashlib.sha256(raw).hexdigest()
        try:
            return Ed25519PublicKey.from_public_bytes(raw), key_id
        except ValueError as exc:
            raise UpdateSecurityError("UPDATE_PUBLIC_KEY_INVALID") from exc

    @classmethod
    def verify_manifest(
        cls,
        manifest_bytes: bytes,
        *,
        public_key_b64: str | None = None,
        now: datetime | None = None,
        platform_kind: str | None = None,
        architecture: str | None = None,
        current_version: str | None = None,
    ) -> dict[str, Any]:
        if not manifest_bytes or len(manifest_bytes) > MAX_MANIFEST_BYTES:
            raise UpdateSecurityError("UPDATE_MANIFEST_SIZE_INVALID")
        try:
            envelope = json.loads(manifest_bytes.decode("utf-8"))
        except Exception as exc:
            raise UpdateSecurityError("UPDATE_MANIFEST_JSON_INVALID") from exc
        if not isinstance(envelope, dict) or set(envelope) != {"signed", "signature"}:
            raise UpdateSecurityError("UPDATE_MANIFEST_ENVELOPE_INVALID")
        signed = envelope.get("signed")
        signature = envelope.get("signature")
        if not isinstance(signed, dict) or not isinstance(signature, dict):
            raise UpdateSecurityError("UPDATE_MANIFEST_ENVELOPE_INVALID")
        if int(signed.get("schema", 0)) != MANIFEST_SCHEMA:
            raise UpdateSecurityError("UPDATE_MANIFEST_SCHEMA_UNSUPPORTED")

        public_key, expected_key_id = cls._public_key(public_key_b64)
        if str(signature.get("keyid") or "") != expected_key_id:
            raise UpdateSecurityError("UPDATE_MANIFEST_KEYID_MISMATCH")
        if str(signature.get("algorithm") or "") != "ed25519":
            raise UpdateSecurityError("UPDATE_MANIFEST_ALGORITHM_UNSUPPORTED")
        try:
            signature_bytes = base64.b64decode(
                str(signature.get("sig") or ""),
                validate=True,
            )
        except Exception as exc:
            raise UpdateSecurityError("UPDATE_MANIFEST_SIGNATURE_INVALID") from exc
        signed_bytes = _canonical_json(signed)
        try:
            public_key.verify(signature_bytes, signed_bytes)
        except (InvalidSignature, ValueError) as exc:
            raise UpdateSecurityError("UPDATE_MANIFEST_SIGNATURE_INVALID") from exc

        sequence = signed.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= 0:
            raise UpdateSecurityError("UPDATE_SEQUENCE_INVALID")
        target_version = str(signed.get("version") or "").strip()
        _version_tuple(target_version)

        issued_at = _parse_utc(str(signed.get("issued_at") or ""))
        expires_at = _parse_utc(str(signed.get("expires_at") or ""))
        if expires_at <= issued_at:
            raise UpdateSecurityError("UPDATE_MANIFEST_EXPIRY_INVALID")

        current_now = (now or _utc_now()).astimezone(timezone.utc)
        state = cls._read_trust_state()
        last_trusted_raw = state.get("last_trusted_time")
        last_trusted = _parse_utc(last_trusted_raw) if last_trusted_raw else current_now
        trusted_now = max(current_now, last_trusted)

        if (issued_at - current_now).total_seconds() > 86400:
            raise UpdateSecurityError("UPDATE_MANIFEST_ISSUED_IN_FUTURE")
        if trusted_now >= expires_at:
            raise UpdateSecurityError("UPDATE_MANIFEST_EXPIRED")

        signed_sha256 = hashlib.sha256(signed_bytes).hexdigest()
        highest_sequence = int(state.get("highest_sequence") or 0)
        highest_manifest_sha256 = state.get("highest_manifest_sha256")
        if sequence < highest_sequence:
            raise UpdateSecurityError("UPDATE_ROLLBACK_BLOCKED")
        if (
            sequence == highest_sequence
            and highest_sequence > 0
            and signed_sha256 != highest_manifest_sha256
        ):
            raise UpdateSecurityError("UPDATE_REPLAY_CONFLICT")

        if current_version is None:
            version_path = Path(__file__).resolve().parents[2] / "VERSION"
            current_version = (
                version_path.read_text(encoding="utf-8").strip()
                if version_path.exists()
                else "0.0.0"
            )
        if _version_tuple(target_version) <= _version_tuple(current_version):
            raise UpdateSecurityError("UPDATE_VERSION_NOT_NEWER")

        platform_value = str(platform_kind or get_platform_adapter().kind).strip().lower()
        arch_value = _normalize_arch(architecture or std_platform.machine())
        targets = signed.get("targets")
        if not isinstance(targets, list) or not targets:
            raise UpdateSecurityError("UPDATE_TARGETS_REQUIRED")
        matching = [
            item
            for item in targets
            if isinstance(item, dict)
            and str(item.get("os") or "").strip().lower() == platform_value
            and _normalize_arch(str(item.get("arch") or "")) == arch_value
        ]
        if len(matching) != 1:
            raise UpdateSecurityError("UPDATE_TARGET_NOT_UNIQUE")

        target = matching[0]
        raw_filename = str(target.get("filename") or "")
        filename = Path(raw_filename).name
        if not filename or filename != raw_filename:
            raise UpdateSecurityError("UPDATE_TARGET_FILENAME_INVALID")
        size_bytes = target.get("size_bytes")
        if (
            not isinstance(size_bytes, int)
            or isinstance(size_bytes, bool)
            or not (0 < size_bytes <= MAX_ARTIFACT_BYTES)
        ):
            raise UpdateSecurityError("UPDATE_TARGET_SIZE_INVALID")
        sha256 = str(target.get("sha256") or "").strip().lower()
        if not SHA256_PATTERN.fullmatch(sha256):
            raise UpdateSecurityError("UPDATE_TARGET_SHA256_INVALID")
        url = str(target.get("url") or "").strip()
        if not url.startswith("https://"):
            raise UpdateSecurityError("UPDATE_TARGET_URL_HTTPS_REQUIRED")

        if sequence > highest_sequence:
            state["highest_sequence"] = sequence
            state["highest_manifest_sha256"] = signed_sha256
        state["last_trusted_time"] = trusted_now.isoformat().replace("+00:00", "Z")
        cls._write_trust_state(state)

        return {
            "schema": MANIFEST_SCHEMA,
            "sequence": sequence,
            "version": target_version,
            "issued_at": issued_at.isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "manifest_sha256": signed_sha256,
            "target": {
                "os": platform_value,
                "arch": arch_value,
                "filename": filename,
                "size_bytes": size_bytes,
                "sha256": sha256,
                "url": url,
            },
        }

    @classmethod
    def _job_dir(cls, job_id: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{32}", str(job_id)):
            raise UpdatePreparationError("UPDATE_JOB_ID_INVALID")
        return get_platform_adapter().ensure_private_directory(
            cls.root() / "jobs" / job_id
        )

    @classmethod
    def _write_job(cls, job: dict[str, Any]) -> None:
        get_platform_adapter().atomic_write_text(
            cls._job_dir(str(job["job_id"])) / "job.json",
            json.dumps(job, indent=2, sort_keys=True),
        )

    @classmethod
    def get_job(cls, job_id: str) -> dict[str, Any]:
        path = cls._job_dir(job_id) / "job.json"
        if not path.exists():
            raise FileNotFoundError("Update job not found")
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    def download_target(
        cls,
        verified_manifest: dict[str, Any],
        job_id: str,
    ) -> Path:
        target = verified_manifest["target"]
        job_dir = cls._job_dir(job_id)
        final_path = job_dir / target["filename"]
        partial_path = final_path.with_name(final_path.name + ".partial")
        request = urllib.request.Request(
            target["url"],
            headers={"User-Agent": "DigitalCrown-Updater/1"},
            method="GET",
        )
        total = 0
        digest = hashlib.sha256()
        try:
            with urllib.request.urlopen(request, timeout=60) as response, partial_path.open("wb") as handle:
                final_url = str(response.geturl())
                if not final_url.startswith("https://"):
                    raise UpdateSecurityError("UPDATE_REDIRECT_DOWNGRADE_BLOCKED")
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > int(target["size_bytes"]):
                        raise UpdateSecurityError("UPDATE_ARTIFACT_SIZE_MISMATCH")
                    digest.update(chunk)
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            if total != int(target["size_bytes"]):
                raise UpdateSecurityError("UPDATE_ARTIFACT_SIZE_MISMATCH")
            if digest.hexdigest() != target["sha256"]:
                raise UpdateSecurityError("UPDATE_ARTIFACT_SHA256_MISMATCH")
            os.replace(partial_path, final_path)
            return final_path
        finally:
            partial_path.unlink(missing_ok=True)

    @classmethod
    def verify_local_artifact(
        cls,
        verified_manifest: dict[str, Any],
        artifact_path: Path,
    ) -> Path:
        target = verified_manifest["target"]
        path = Path(artifact_path)
        if not path.is_file():
            raise UpdatePreparationError("UPDATE_ARTIFACT_MISSING")
        if path.stat().st_size != int(target["size_bytes"]):
            raise UpdateSecurityError("UPDATE_ARTIFACT_SIZE_MISMATCH")
        if _sha256_file(path) != target["sha256"]:
            raise UpdateSecurityError("UPDATE_ARTIFACT_SHA256_MISMATCH")
        return path

    @classmethod
    def prepare_update(
        cls,
        verified_manifest: dict[str, Any],
        *,
        artifact_path: Path,
    ) -> dict[str, Any]:
        artifact = cls.verify_local_artifact(verified_manifest, artifact_path)

        rescue = BackupService.backup_active_database()
        if rescue.get("status") != "SUCCESS" or not rescue.get("backup_filename"):
            raise UpdatePreparationError("UPDATE_RESCUE_BACKUP_FAILED")
        rescue_path = (
            AppPaths.get_user_data_dir()
            / "backups"
            / str(rescue["backup_filename"])
        )
        if not rescue_path.is_file() or rescue_path.stat().st_size <= 0:
            raise UpdatePreparationError("UPDATE_RESCUE_BACKUP_MISSING")
        rescue_sha = str(rescue.get("checksum") or "").lower()
        if (
            not SHA256_PATTERN.fullmatch(rescue_sha)
            or _sha256_file(rescue_path) != rescue_sha
        ):
            raise UpdatePreparationError("UPDATE_RESCUE_BACKUP_CHECKSUM_INVALID")

        job_id = uuid.uuid4().hex
        job_dir = cls._job_dir(job_id)

        target_name = str(verified_manifest["target"]["filename"])
        staged_artifact = job_dir / target_name
        if artifact.resolve() != staged_artifact.resolve():
            _copy_file_verified(
                artifact,
                staged_artifact,
                str(verified_manifest["target"]["sha256"]),
            )
        cls.verify_local_artifact(verified_manifest, staged_artifact)

        rescue_dir = get_platform_adapter().ensure_private_directory(
            job_dir / "rescue"
        )
        staged_rescue = rescue_dir / rescue_path.name
        _copy_file_verified(rescue_path, staged_rescue, rescue_sha)
        if _sha256_file(staged_rescue) != rescue_sha:
            raise UpdatePreparationError("UPDATE_RESCUE_STAGING_CHECKSUM_INVALID")

        now = _utc_now().isoformat().replace("+00:00", "Z")
        job = {
            "schema": 1,
            "job_id": job_id,
            "status": "prepared",
            "created_at": now,
            "updated_at": now,
            "sequence": int(verified_manifest["sequence"]),
            "version": str(verified_manifest["version"]),
            "manifest_sha256": str(verified_manifest["manifest_sha256"]),
            "platform": str(verified_manifest["target"]["os"]),
            "architecture": str(verified_manifest["target"]["arch"]),
            "artifact_filename": staged_artifact.name,
            "artifact_sha256": str(verified_manifest["target"]["sha256"]),
            "artifact_size_bytes": int(verified_manifest["target"]["size_bytes"]),
            "rescue_staged": True,
            "rescue_backup_filename": f"rescue/{staged_rescue.name}",
            "rescue_backup_sha256": rescue_sha,
            "apply_certified": False,
            "apply_blocker": "P6/P7_PACKAGED_INSTALLER_CERTIFICATION_REQUIRED",
        }
        cls._write_job(job)
        return job

    @classmethod
    def mark_installed_healthy(cls, job_id: str) -> dict[str, Any]:
        job = cls.get_job(job_id)
        if job.get("status") != "health_pending":
            raise UpdatePreparationError("UPDATE_JOB_STATE_INVALID")
        state = cls._read_trust_state()
        sequence = int(job["sequence"])
        if sequence < int(state.get("installed_sequence") or 0):
            raise UpdateSecurityError("UPDATE_INSTALLED_ROLLBACK_BLOCKED")
        state["installed_sequence"] = sequence
        state["installed_version"] = str(job["version"])
        cls._write_trust_state(state)
        job["status"] = "healthy"
        job["updated_at"] = _utc_now().isoformat().replace("+00:00", "Z")
        cls._write_job(job)
        return job

    @classmethod
    def require_certified_apply(cls, job_id: str) -> None:
        job = cls.get_job(job_id)
        if not bool(job.get("apply_certified")):
            raise UpdatePreparationError("UPDATE_PLATFORM_APPLY_NOT_CERTIFIED")

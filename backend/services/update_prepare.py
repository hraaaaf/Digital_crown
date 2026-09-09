from __future__ import annotations

import json
import shutil
import uuid
from typing import Any

from backend.services.update_engine import UpdateEngine


class UpdatePrepareService:
    """Prepare a real update job from a production-pinned signed manifest.

    The manifest is always verified by ``UpdateEngine.verify_manifest`` without
    public-key injection. The target is downloaded over the URL authenticated by
    that manifest, re-hashed by the engine, and then staged with a rescue backup.
    """

    @staticmethod
    def _manifest_bytes(envelope: dict[str, Any]) -> bytes:
        return json.dumps(
            envelope,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    @classmethod
    def prepare_from_manifest(cls, envelope: dict[str, Any]) -> dict[str, Any]:
        manifest_bytes = cls._manifest_bytes(envelope)

        # Deliberately omit public_key_b64. Physical/runtime preparation must use
        # only the immutable production trust roots embedded in UpdateEngine.
        verified = UpdateEngine.verify_manifest(manifest_bytes)

        download_id = uuid.uuid4().hex
        transient_dir = UpdateEngine.root() / "jobs" / download_id
        try:
            artifact = UpdateEngine.download_target(verified, download_id)
            job = UpdateEngine.prepare_update(verified, artifact_path=artifact)
        finally:
            # download_target uses the job directory only as a verified temporary
            # staging area. prepare_update copies the artifact into its own job.
            shutil.rmtree(transient_dir, ignore_errors=True)

        return {
            "job_id": str(job["job_id"]),
            "status": str(job["status"]),
            "sequence": int(job["sequence"]),
            "version": str(job["version"]),
            "manifest_sha256": str(job["manifest_sha256"]),
            "platform": str(job["platform"]),
            "architecture": str(job["architecture"]),
            "artifact_filename": str(job["artifact_filename"]),
            "apply_certified": bool(job["apply_certified"]),
            "apply_blocker": job.get("apply_blocker"),
        }

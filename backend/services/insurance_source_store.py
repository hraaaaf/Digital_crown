"""Immutable local storage for validated insurance/NGAP source PDFs.

The cabinet product is local-first. Official servers are therefore not a runtime
dependency: once exact bytes are obtained, they are validated first, then persisted
under their SHA-256 with a deterministic JSON manifest. Nothing here promotes an
unverified source by itself.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from backend.services.insurance_template_registry import (
    InsuranceTemplateDefinition,
    LockedInsuranceTemplate,
    lock_template_pdf,
)
from backend.services.ngap_reference import NgapRelease, lock_ngap_primary_pdf

_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class StoredInsuranceSource:
    namespace: str
    version: str
    sha256: str
    pdf_path: str
    manifest_path: str


def _safe_component(value: str, field: str) -> str:
    normalized = str(value or "").strip()
    if not normalized or not _SAFE_COMPONENT.fullmatch(normalized):
        raise ValueError(f"Invalid {field} for immutable insurance source store")
    return normalized


def _store_locked_bytes(
    *,
    root: Path,
    namespace: str,
    version: str,
    expected_sha256: str,
    pdf_bytes: bytes,
    manifest: dict[str, Any],
) -> StoredInsuranceSource:
    namespace = _safe_component(namespace, "namespace")
    version = _safe_component(version, "version")
    expected_sha256 = str(expected_sha256 or "").strip().lower()
    actual_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    if len(expected_sha256) != 64 or actual_sha256 != expected_sha256:
        raise ValueError("Insurance source SHA-256 mismatch")
    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("Insurance source store accepts PDF bytes only")

    target_dir = Path(root) / namespace / version / actual_sha256
    target_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = target_dir / "source.pdf"
    manifest_path = target_dir / "manifest.json"

    canonical_manifest = {
        **manifest,
        "namespace": namespace,
        "version": version,
        "sha256": actual_sha256,
    }
    manifest_bytes = (
        json.dumps(canonical_manifest, ensure_ascii=False, sort_keys=True, indent=2)
        + "\n"
    ).encode("utf-8")

    if pdf_path.exists() and pdf_path.read_bytes() != pdf_bytes:
        raise ValueError("Immutable insurance source PDF collision")
    if manifest_path.exists() and manifest_path.read_bytes() != manifest_bytes:
        raise ValueError("Immutable insurance source manifest collision")

    if not pdf_path.exists():
        tmp_pdf = pdf_path.with_suffix(".pdf.tmp")
        tmp_pdf.write_bytes(pdf_bytes)
        os.replace(tmp_pdf, pdf_path)
    if not manifest_path.exists():
        tmp_manifest = manifest_path.with_suffix(".json.tmp")
        tmp_manifest.write_bytes(manifest_bytes)
        os.replace(tmp_manifest, manifest_path)

    return StoredInsuranceSource(
        namespace=namespace,
        version=version,
        sha256=actual_sha256,
        pdf_path=str(pdf_path),
        manifest_path=str(manifest_path),
    )


def lock_and_store_ngap_primary(
    *,
    root: Path,
    release: NgapRelease,
    pdf_bytes: bytes,
    source_url: str | None = None,
) -> tuple[NgapRelease, StoredInsuranceSource]:
    """Validate legal NGAP identity, hash-lock, then store immutable exact bytes."""
    locked = lock_ngap_primary_pdf(
        release=release,
        pdf_bytes=pdf_bytes,
        source_url=source_url,
    )
    if not locked.source_hash:
        raise ValueError("Locked NGAP release has no SHA-256")
    stored = _store_locked_bytes(
        root=root,
        namespace="ngap",
        version=locked.version,
        expected_sha256=locked.source_hash,
        pdf_bytes=pdf_bytes,
        manifest={
            "kind": "NGAP_PRIMARY",
            "authority": locked.authority,
            "source_url": locked.source_url,
            "publication_reference": locked.publication_reference,
            "status": locked.status.value,
        },
    )
    return locked, stored


def lock_and_store_insurance_template(
    *,
    root: Path,
    definition: InsuranceTemplateDefinition,
    pdf_bytes: bytes,
    source_url: str,
) -> tuple[LockedInsuranceTemplate, StoredInsuranceSource]:
    """Validate insurer template identity constraints, then store immutable bytes."""
    locked = lock_template_pdf(
        definition=definition,
        pdf_bytes=pdf_bytes,
        source_url=source_url,
    )
    stored = _store_locked_bytes(
        root=root,
        namespace=f"template-{definition.organization.value.lower()}",
        version=definition.version,
        expected_sha256=locked.sha256,
        pdf_bytes=pdf_bytes,
        manifest={
            "kind": "INSURANCE_TEMPLATE",
            "organization": definition.organization.value,
            "label": definition.label,
            "trust": definition.trust.value,
            "source_url": locked.source_url,
            "page_count": locked.page_count,
        },
    )
    return locked, stored

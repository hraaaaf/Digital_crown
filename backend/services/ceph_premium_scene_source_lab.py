"""CEPH-PREMIUM J2.1-M4: fail-closed read-only scene/original-media attestation.

The consumer must pass a DB session and scoped actor identities. The existing
DC-DOS-05 verifier reads authenticated, encrypted asset bytes and original SHA.
This is a laboratory adapter, not an HTTP endpoint, ORM migration, clinical
approval or assertion that ONNX actually used these specific bytes.
"""
from __future__ import annotations

import hashlib
from io import BytesIO

from backend.schemas.cephalo_premium_scene_contract import CephaloPremiumSceneDraft


class SceneSourceRejected(ValueError):
    pass


def verify_original_pixels(scene: CephaloPremiumSceneDraft, *,
                           verified_media: dict, original_bytes: bytes) -> dict:
    """Validate a verified DC-DOS-05 result AND the matching image bytes."""
    if not isinstance(scene, CephaloPremiumSceneDraft):
        raise SceneSourceRejected("Unvalidated scene contract")
    if not isinstance(verified_media, dict):
        raise SceneSourceRejected("Missing trusted media binding")
    i = scene.identity
    if (verified_media.get("clinical_release") is not False
        or verified_media.get("binding_state") != "EXPLICIT_VERIFIED_ORIGINALS"
        or verified_media.get("study_id") != i.study_id
        or verified_media.get("patient_id") != i.patient_id
        or verified_media.get("revision") != i.scientific_revision):
        raise SceneSourceRejected("Study identity or revision does not match verified original")
    items = verified_media.get("items")
    if not isinstance(items, list):
        raise SceneSourceRejected("Verified media has no item list")
    matches = [x for x in items if isinstance(x, dict)
               and x.get("role") == "RADIO_SOURCE"]
    if len(matches) != 1 or any(
        match.get("asset_id") != i.original_asset_id
        or match.get("sha256") != i.original_sha256
        or match.get("revision") != i.scientific_revision
        for match in matches
    ):
        raise SceneSourceRejected("No unique matching verified radiograph original")
    if type(original_bytes) is not bytes:
        raise SceneSourceRejected("Original media bytes not available")
    if hashlib.sha256(original_bytes).hexdigest() != i.original_sha256:
        raise SceneSourceRejected("Radiograph byte-level SHA mismatch")
    try:
        from PIL import Image, UnidentifiedImageError
        with Image.open(BytesIO(original_bytes)) as img:
            if img.format not in {"JPEG", "PNG"}:
                raise SceneSourceRejected("Radiograph source type not supported")
            dimensions = img.size
            if dimensions[0] * dimensions[1] > 100_000_000:
                raise SceneSourceRejected("Source exceeds nonclinical image pixel budget")
            img.verify()  # Must run before getexif/load; PNG closes its file.
        with Image.open(BytesIO(original_bytes)) as img:
            # Original pixel dimensions BEFORE EXIF display orientation.
            exif_orientation = int(img.getexif().get(274, 1))
    except (OSError, ValueError, TypeError, UnidentifiedImageError) as exc:
        raise SceneSourceRejected("Invalid radiograph source bytes") from exc
    if dimensions != (i.original_width, i.original_height):
        raise SceneSourceRejected("Scene dimensions do not match verified original")
    if exif_orientation not in range(1, 9):
        raise SceneSourceRejected("Invalid EXIF orientation")
    return {
        "attestation": "LAB_VERIFIED_ORIGINAL_BYTES_NOT_CLINICAL_SOURCE_OF_INFERENCE",
        "employer_id": i.employer_id,
        "patient_id": i.patient_id,
        "study_id": i.study_id,
        "asset_id": i.original_asset_id,
        "image_sha256": i.original_sha256,
        "source_width": dimensions[0],
        "source_height": dimensions[1],
        "exif_orientation": exif_orientation,
        "study_revision": i.scientific_revision,
        "clinical_release": False,
        "image_used_by_srpose38_inference_verified": False,
    }


def verify_via_dc_dos05(db, *, scene: CephaloPremiumSceneDraft,
                        actor_employer_id: int, actor_patient_id: int,
                        actor_study_id: int) -> dict:
    """Use the existing tenant-scoped read verifier; no bypass/fallback."""
    i = scene.identity
    if (type(actor_employer_id) is not int
        or type(actor_patient_id) is not int
        or type(actor_study_id) is not int
        or (actor_employer_id, actor_patient_id, actor_study_id)
        != (i.employer_id, i.patient_id, i.study_id)):
        raise SceneSourceRejected("Actor does not match the tenant/patient/study")
    from backend.services.cephalo_study_media_binding import (
        read_verified_study_media,
    )
    from backend.services.clinical_asset_storage import read_clinical_asset_bytes

    trusted = read_verified_study_media(
        db, employer_id=i.employer_id, patient_id=i.patient_id, study_id=i.study_id
    )
    original_bytes = read_clinical_asset_bytes(
        db, employer_id=i.employer_id, patient_id=i.patient_id,
        asset_id=i.original_asset_id,
    )
    return verify_original_pixels(
        scene, verified_media=trusted, original_bytes=original_bytes,
    )

"""DC-DOS-06 FUE-only, byte-causal image -> landmarks -> geometry -> PDF.

NOT a clinical pipeline, ONNX execution, diagnostic model, automatic treatment,
or a source proof for any pre-existing cephalometric scientific evidence.
The detector is an intentionally NONCLINICAL synthetic test marker decoder.
The source is re-read from authenticated encrypted Media Core each invocation.
"""
from __future__ import annotations

import hashlib
import json
from math import isfinite
from io import BytesIO

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy.orm import Session

from backend.services.cephalo_safe_engine import cephalo_safe_engine
from backend.services.cephalo_study_media_binding import (
    StudyMediaBindingError,
    read_verified_study_media,
)
from backend.services.clinical_asset_storage import (
    ClinicalAssetStorageError, read_clinical_asset_bytes,
)
from backend.services.srpose38_contract import SOTA_LANDMARKS_MAPPING

SCHEMA_VERSION = "DC_DOS06_SYNTHETIC_PIXEL_CHAIN_V1"
DETECTOR_ID = "NONCLINICAL_RGB_MARKER_38_V1"
MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_SOURCE_PIXELS = 1_000_000


def _canonical_sha(value: object) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def synthetic_marker_color(index: int) -> tuple[int, int, int]:
    """Fixed test palette, not an image analysis model."""
    if type(index) is not int or not (0 <= index < 38):
        raise ValueError("Nonclinical marker index must be 0..37")
    return 31 + index * 5, 211 - index * 4, 30 + index * 3


def _read_synthetic_landmarks(source: bytes) -> list[dict]:
    if not isinstance(source, bytes) or not source or len(source) > MAX_SOURCE_BYTES:
        raise StudyMediaBindingError("Missing/oversize synthetic source")
    try:
        with Image.open(BytesIO(source)) as opened:
            if opened.format != "PNG" or opened.width * opened.height > MAX_SOURCE_PIXELS:
                raise StudyMediaBindingError("Only bounded synthetic PNG markers supported")
            if opened.width < 200 or opened.height < 200:
                raise StudyMediaBindingError("Synthetic image dimensions invalid")
            # The exact decoded source bytes feed the detector; never a filename,
            # view state, thumbnails or a caller-supplied landmark list.
            image = opened.convert("RGB")
            width = image.width
            locations = {synthetic_marker_color(i): [] for i in range(38)}
            for offset, color in enumerate(image.getdata()):
                if color in locations:
                    locations[color].append((offset % width, offset // width))
    except (OSError, ValueError, SyntaxError) as exc:
        raise StudyMediaBindingError("Source image pixels unavailable") from exc
    landmarks = []
    for index, landmark_id in SOTA_LANDMARKS_MAPPING.items():
        markers = locations[synthetic_marker_color(index)]
        if len(markers) != 9:
            raise StudyMediaBindingError("Synthetic image has missing/extra marker pixels")
        xs = [xy[0] for xy in markers]
        ys = [xy[1] for xy in markers]
        x = sum(xs) / 9
        y = sum(ys) / 9
        if (
            x != int(x) or y != int(y)
            or min(xs) != x - 1 or max(xs) != x + 1
            or min(ys) != y - 1 or max(ys) != y + 1
        ):
            raise StudyMediaBindingError("Synthetic marker geometry is incoherent")
        landmarks.append({"id": landmark_id, "x": float(x), "y": float(y)})
    if len(landmarks) != 38:
        raise StudyMediaBindingError("38 synthetic landmarks required")
    return landmarks


def _unsigned_receipt(manifest: dict, *, points: list[dict], measurement: dict) -> bytes:
    """Nonclinical A4 PDF: exactly the same digests as the in-memory calculation."""
    buffer = BytesIO()
    c = Canvas(buffer, pagesize=A4, invariant=1, pageCompression=0)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(48, 793, "DC-DOS-06 - SYNTHETIC REHEARSAL ONLY")
    c.setFont("Helvetica", 10)
    rows = [
        "NOT A CLINICAL CEPHALOMETRIC REPORT - NOT SIGNED",
        f"STUDY_ID: {manifest['study_id']}",
        f"PATIENT_ID: {manifest['patient_id']}",
        f"REVISION: {manifest['revision']}",
        f"SOURCE_ASSET_ID: {manifest['source_asset_id']}",
        f"SOURCE_SHA256: {manifest['source_sha256']}",
        f"LANDMARK_SHA256: {manifest['landmarks_sha256']}",
        f"MEASUREMENT_SHA256: {manifest['measurements_sha256']}",
        f"PROVENANCE_SHA256: {manifest['provenance_sha256']}",
        f"PIXEL_DETECTOR: {DETECTOR_ID}",
        f"LANDMARK_COUNT: {len(points)}",
        "CALIBRATION_AUTHORITY: NONE",
        "INFERENCE_AUTHORITY: SYNTHETIC_ONLY_NOT_ONNX",
        "CLINICAL_RELEASE: FALSE",
        "OFFICIAL_ARCHIVE: NONE",
    ]
    for index, row in enumerate(rows):
        c.drawString(48, 760 - index * 24, row)
    # Display actual raw geometry values from the SAME calculated payload,
    # explicitly nonclinical: SHA-only placeholders are insufficient proof.
    groups = measurement.get("metrics", {})
    samples = (
        ("analyse_osseuse", "SNA"), ("analyse_osseuse", "SNB"),
        ("analyse_osseuse", "ANB"), ("analyse_osseuse", "Angle_de_Tweed"),
        ("analyse_dentaire", "IMPA"),
    )
    printed = 0
    for group, key in samples:
        raw = groups.get(group, {}).get(key, {})
        number = raw.get("valeur") if isinstance(raw, dict) else None
        if type(number) not in {int, float} or not isfinite(number):
            continue
        c.drawString(48, 348 - printed * 20, f"RAW SYNTHETIC {key}: {number:.3f}")
        printed += 1
    if printed < 3:
        raise StudyMediaBindingError("Synthetic calculation has too few numeric measurements")
    # Render the actual geometric engine's result digest; never substitute
    # client-side pseudo-values for the calculation output.
    assert manifest["measurements_sha256"] == _canonical_sha(measurement)
    c.showPage()
    c.save()
    return buffer.getvalue()


def rehearse_source_measure_pdf(
    db: Session, *, employer_id: int, patient_id: int, study_id: int,
    expected_revision: int,
) -> tuple[bytes, dict]:
    """Causal proof for synthetic pixels only, not pre-existing clinical metrics."""
    scoped = read_verified_study_media(
        db, employer_id=employer_id, patient_id=patient_id, study_id=study_id
    )
    if type(expected_revision) is not int or scoped["revision"] != expected_revision:
        raise StudyMediaBindingError("Exact scientific revision required")
    sources = [entry for entry in scoped["items"] if entry["role"] == "RADIO_SOURCE"]
    if len(sources) != 1:
        raise StudyMediaBindingError("Exactly one verified original RADIO_SOURCE required")
    source_record = sources[0]
    try:
        source = read_clinical_asset_bytes(
            db, employer_id=employer_id, patient_id=patient_id,
            asset_id=source_record["asset_id"],
        )
    except (ClinicalAssetStorageError, OSError) as exc:
        raise StudyMediaBindingError("Bound encrypted source not readable") from exc
    if hashlib.sha256(source).hexdigest() != source_record["sha256"]:
        raise StudyMediaBindingError("Source digest mismatch")
    points = _read_synthetic_landmarks(source)
    try:
        geometry = cephalo_safe_engine.calculate_metrics(
            {p["id"]: (p["x"], p["y"]) for p in points},
            custom_mm_ratio=None,
        )
        calculation = geometry.model_dump(mode="json")
        measurements_sha = _canonical_sha(calculation)
    except (ValueError, TypeError, OverflowError) as exc:
        raise StudyMediaBindingError("Synthetic geometry calculation invalid") from exc
    witness = {
        "schema_version": SCHEMA_VERSION,
        "detector_id": DETECTOR_ID,
        "study_id": scoped["study_id"],
        "patient_id": scoped["patient_id"],
        "revision": scoped["revision"],
        "source_asset_id": source_record["asset_id"],
        "source_sha256": source_record["sha256"],
        "landmarks_sha256": _canonical_sha(points),
        "measurements_sha256": measurements_sha,
        "calibration_authority": None,
        "clinical_release": False,
        "existing_cephalo_analysis_metrics_from_source_proven": False,
        "official_pdf": False,
    }
    manifest = {**witness, "provenance_sha256": _canonical_sha(witness)}
    rendered = _unsigned_receipt(manifest, points=points, measurement=calculation)
    manifest["pdf_sha256"] = hashlib.sha256(rendered).hexdigest()
    manifest["pdf_byte_size"] = len(rendered)
    return rendered, manifest

"""Generic PDF overlay engine for validated insurance submissions.

No insurer coordinates live here. A separately reviewed layout profile is bound to the
exact template SHA-256. Signature, stamp/cachet and insurer-decision fields are denied.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import re

import fitz

from backend.schemas.insurance_submission import InsuranceSubmissionDraft
from backend.services.insurance_render_gate import assert_insurance_render_ready


class OverlayKind(str, Enum):
    TEXT = "TEXT"
    MARK = "MARK"


@dataclass(frozen=True)
class InsuranceOverlayPlacement:
    field_key: str
    page_index: int
    x: float
    y: float
    font_size: float = 9.0
    kind: OverlayKind = OverlayKind.TEXT
    max_chars: int | None = None


@dataclass(frozen=True)
class InsuranceOverlayProfile:
    organization: str
    template_version: str
    template_hash: str
    profile_version: str
    placements: tuple[InsuranceOverlayPlacement, ...]
    max_lines: int | None = None


def insurance_overlay_profile_payload(profile: InsuranceOverlayProfile) -> dict:
    payload = {
        "organization": profile.organization,
        "template_version": profile.template_version,
        "template_hash": profile.template_hash,
        "profile_version": profile.profile_version,
        "placements": [
            {
                **asdict(placement),
                "kind": placement.kind.value,
            }
            for placement in profile.placements
        ],
    }
    # Preserve hashes of historical profiles that predate the optional capacity gate.
    if profile.max_lines is not None:
        payload["max_lines"] = profile.max_lines
    return payload


def insurance_overlay_profile_sha256(profile: InsuranceOverlayProfile) -> str:
    canonical = json.dumps(
        insurance_overlay_profile_payload(profile),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


_FORBIDDEN_FIELD_TOKENS = (
    "signature",
    "cachet",
    "stamp",
    "insurer_decision",
    "accord_assureur",
)
_LINE_FIELD = re.compile(r"^lines\[(\d+)\]\.(label|service_date|amount_mad|ngap_code|ngap_coefficient|teeth)$")
_CHOICE_FIELD = re.compile(
    r"^choice\.(request_nature|care_type|beneficiary_sex|relationship_to_insured)\.([A-Za-z0-9_]+)$"
)
_ADMIN_FIELDS = {
    "request_nature",
    "insured_full_name",
    "insured_affiliation_number",
    "insured_registration_number",
    "insured_national_id",
    "insured_address",
    "insured_quality",
    "beneficiary_full_name",
    "beneficiary_birth_date",
    "beneficiary_national_id",
    "beneficiary_sex",
    "relationship_to_insured",
    "practitioner_full_name",
    "practitioner_inpe",
    "care_type",
    "prior_approval_number",
    "accident_date",
    "accident_circumstances",
    "attachments_count",
}


def _text(value) -> str:
    if value is None:
        return ""
    raw = getattr(value, "value", value)
    if isinstance(raw, list):
        return ", ".join(str(getattr(item, "value", item)) for item in raw)
    if hasattr(raw, "isoformat"):
        return raw.isoformat()
    return str(raw)


def _field_value(draft: InsuranceSubmissionDraft, key: str) -> str:
    lowered = key.lower()
    if any(token in lowered for token in _FORBIDDEN_FIELD_TOKENS):
        raise ValueError("Overlay profile requests a forbidden signature/stamp/decision field")

    if key.startswith("administrative."):
        field_name = key.split(".", 1)[1]
        if field_name not in _ADMIN_FIELDS:
            raise ValueError(f"Unsupported administrative overlay field: {field_name}")
        return _text(getattr(draft.administrative, field_name))

    match = _LINE_FIELD.fullmatch(key)
    if match:
        index = int(match.group(1))
        # A profile describes the form's capacity, not the number of acts in a draft.
        # Unused form rows stay blank; max_lines still fails closed when a draft
        # contains more care lines than the exact form can represent.
        if index >= len(draft.lines):
            return ""
        return _text(getattr(draft.lines[index], match.group(2)))

    choice = _CHOICE_FIELD.fullmatch(key)
    if choice:
        field_name, expected = choice.groups()
        actual = getattr(draft.administrative, field_name)
        actual_value = str(getattr(actual, "value", actual) or "")
        return "X" if actual_value == expected else ""

    if key == "computed.total_amount_mad":
        return _text(sum(line.amount_mad for line in draft.lines))
    if key == "computed.attachments_count":
        return _text(draft.administrative.attachments_count)

    raise ValueError(f"Unsupported insurance overlay field: {key}")


def render_insurance_pdf_overlay(
    *,
    draft: InsuranceSubmissionDraft,
    template_bytes: bytes,
    profile: InsuranceOverlayProfile,
) -> bytes:
    """Overlay traceable text/marks on exact locked template bytes."""
    template_hash = assert_insurance_render_ready(
        draft=draft,
        template_bytes=template_bytes,
    )
    if profile.organization != draft.organization.value:
        raise ValueError("Overlay profile organization mismatch")
    if profile.template_version != draft.template.template_version:
        raise ValueError("Overlay profile template version mismatch")
    if profile.template_hash != template_hash:
        raise ValueError("Overlay profile template SHA-256 mismatch")
    if not profile.profile_version.strip():
        raise ValueError("Overlay profile version is required")
    if profile.max_lines is not None:
        if profile.max_lines <= 0:
            raise ValueError("Overlay profile max_lines is invalid")
        if len(draft.lines) > profile.max_lines:
            raise ValueError("Overlay profile cannot represent all care lines")

    try:
        document = fitz.open(stream=template_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError("Locked template PDF is unreadable") from exc

    try:
        for placement in profile.placements:
            if placement.page_index < 0 or placement.page_index >= document.page_count:
                raise ValueError("Overlay profile page index is out of range")
            if placement.font_size <= 0 or placement.font_size > 30:
                raise ValueError("Overlay profile font size is invalid")
            value = _field_value(draft, placement.field_key)
            if placement.max_chars is not None:
                if placement.max_chars <= 0:
                    raise ValueError("Overlay profile max_chars is invalid")
                value = value[: placement.max_chars]
            if not value:
                continue
            page = document[placement.page_index]
            page.insert_text(
                (float(placement.x), float(placement.y)),
                value,
                fontsize=float(placement.font_size),
            )
        return document.tobytes(garbage=4, deflate=True)
    finally:
        document.close()

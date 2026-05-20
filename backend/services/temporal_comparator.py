import logging
from typing import Any
from backend import models

logger = logging.getLogger(__name__)


def _build_finding_map(detections_data: dict) -> dict[str, list[dict]]:
    """
    Build a dict keyed by (tooth_fdi, class_name) → list of detection dicts.
    Handles both new FullAnalysis schema and legacy formats.
    """
    result: dict[str, list[dict]] = {}
    detections = (detections_data or {}).get("detections", [])
    for d in detections:
        label = d.get("class_name") or d.get("label", "")
        tooth = str(d.get("tooth_fdi", "unknown"))
        key = f"{tooth}|{label}"
        result.setdefault(key, []).append(d)
    return result


def _confidence(detection: dict) -> float:
    return float(detection.get("confidence", detection.get("score", 0.0)))


def _describe(key: str, detections: list[dict]) -> str:
    tooth, label = key.split("|", 1)
    conf = max(_confidence(d) for d in detections)
    tooth_str = f"dent {tooth}" if tooth != "unknown" else "localisation inconnue"
    return f"{label} ({tooth_str}, conf. {conf:.0%})"


def compare_panoramic_analyses(
    older: "models.PanoramicAnalysis",
    newer: "models.PanoramicAnalysis",
) -> dict[str, Any]:
    """
    Diff two consecutive panoramic analyses for the same patient.
    Returns categorised findings and a short clinical narrative.
    """
    older_map = _build_finding_map(older.detections_data)
    newer_map = _build_finding_map(newer.detections_data)

    older_keys = set(older_map.keys())
    newer_keys = set(newer_map.keys())

    new_findings = [_describe(k, newer_map[k]) for k in (newer_keys - older_keys)]
    resolved_findings = [_describe(k, older_map[k]) for k in (older_keys - newer_keys)]
    stable_findings = [_describe(k, newer_map[k]) for k in (older_keys & newer_keys)]

    # Detect worsened: same key, confidence increased by ≥ 10 pp
    worsened_findings = []
    for key in older_keys & newer_keys:
        old_conf = max(_confidence(d) for d in older_map[key])
        new_conf = max(_confidence(d) for d in newer_map[key])
        if new_conf - old_conf >= 0.10:
            tooth, label = key.split("|", 1)
            tooth_str = f"dent {tooth}" if tooth != "unknown" else "localisation inconnue"
            worsened_findings.append(
                f"{label} aggravée ({tooth_str}: {old_conf:.0%} → {new_conf:.0%})"
            )

    # Clinical narrative
    parts = []
    if new_findings:
        parts.append(f"{len(new_findings)} nouvelle(s) anomalie(s) détectée(s) : {', '.join(new_findings[:3])}.")
    if resolved_findings:
        parts.append(f"{len(resolved_findings)} anomalie(s) résolue(s) depuis le dernier bilan.")
    if worsened_findings:
        parts.append(f"Aggravation détectée : {', '.join(worsened_findings[:2])}.")
    if not parts:
        parts.append("Situation radiologique stable entre les deux bilans.")

    return {
        "new_findings": new_findings,
        "resolved_findings": resolved_findings,
        "worsened_findings": worsened_findings,
        "stable_findings": stable_findings,
        "summary_text": " ".join(parts),
        "older_date": older.created_at.strftime("%Y-%m-%d"),
        "newer_date": newer.created_at.strftime("%Y-%m-%d"),
        "older_count": len(older_keys),
        "newer_count": len(newer_keys),
    }

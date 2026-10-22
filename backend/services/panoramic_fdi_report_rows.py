"""Explicit clinician-annotated FDI rows for an existing panoramic PDF; NO AI labels.

This is a read-only presentation helper. Never conclude healthy/missing from absent
teeth, never upgrade automated detections into manually confirmed observations.
"""
from __future__ import annotations

from backend.services.panoramic_report_engine import ANOMALY_LABELS

ADULT_FDI = frozenset(str(10*q+n) for q in (1,2,3,4) for n in range(1,9))


def confirmed_manual_fdi_rows(detections_data: object) -> list[dict]:
    """Return ONLY documented tooth annotations selected by the practitioner.

    The field manual_anomalies is stored by /generate-panoramic-report in existing
    patient analyses. It is not equivalent to AI numbering being clinician confirmed.
    Unlisted teeth remain NOT ASSESSED and are deliberately not fabricated.
    """
    if not isinstance(detections_data, dict):
        return []
    source = detections_data.get("manual_anomalies")
    if not isinstance(source, dict) or len(source) > 100:
        return []
    rows = []
    for fdi in sorted(source, key=lambda x: str(x)):
        if not isinstance(fdi, (str, int)) or str(fdi) not in ADULT_FDI:
            continue
        labels = source[fdi]
        if not isinstance(labels, list) or len(labels) > 30:
            continue
        observed, seen = [], set()
        for label_id in labels:
            if not isinstance(label_id, str) or label_id in seen or label_id not in ANOMALY_LABELS:
                continue
            seen.add(label_id)
            observed.append(ANOMALY_LABELS[label_id])
        if observed:
            rows.append({"fdi": str(fdi), "observations": observed,
                         "provenance": "practitioner_manual_annotation"})
    return sorted(rows, key=lambda row: (int(row["fdi"][0]), int(row["fdi"][1])))

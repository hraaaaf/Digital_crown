"""P8 validate 13F/32F same-trace manifest STRUCTURE, not source bytes."""
import json
import re

_PROFILE = {
    "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET": 32,
    "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET": 13,
}
_KINDS = {"ANALYSIS_VALUES", "ANALYSIS_PROPERTIES", "MARKER_POSITIONS"}

def verify_bundle(raw):
    if type(raw) is not bytes or len(raw) > 5_000_000:
        raise ValueError("missing or oversized bundle")
    try:
        m = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("unreadable manifest") from exc
    if not isinstance(m, dict):
        raise ValueError("not a manifest")
    if (m.get("schema_version") != "ORTHO_LOT08_FACAD_RICKETTS_DIRECT_PARITY_EVIDENCE_V1"
        or m.get("scientific_authority") is not False
        or m.get("compatibility_only") is not True
        or m.get("status") != "DIRECT_EVIDENCE_PARTIAL"
        or m.get("parity_rows") != []):
        raise ValueError("unexpected scientific authority or parity claim")
    profiles = m.get("profiles")
    records = m.get("evidence_records")
    if (not isinstance(profiles, list) or len(profiles) != 2 or
        not isinstance(records, list) or len(records) != 6):
        raise ValueError("expected 13F and 32F evidence triplets")
    if {p.get("target_id"): p.get("expected_facad_factor_count")
        for p in profiles if isinstance(p, dict)} != _PROFILE:
        raise ValueError("unexpected analysis profiles")
    seen, cases, ids = set(), set(), set()
    for rec in records:
        if not isinstance(rec, dict):
            raise ValueError("malformed evidence")
        profile, kind = rec.get("profile_target_id"), rec.get("artifact_kind")
        if profile not in _PROFILE or kind not in _KINDS:
            raise ValueError("invalid profile or export kind")
        identity = (profile, kind)
        if identity in seen:
            raise ValueError("duplicate evidence kind")
        seen.add(identity)
        name = rec.get("evidence_id")
        if not isinstance(name, str) or not name or name in ids:
            raise ValueError("duplicate or missing evidence identifier")
        ids.add(name)
        hash_value = rec.get("sha256")
        if not isinstance(hash_value, str) or re.fullmatch("[0-9a-f]{64}", hash_value) is None:
            raise ValueError("bad evidence hash")
        if rec.get("facad_version") != "3.14.1.1111":
            raise ValueError("wrong FACAD evidence version")
        case = rec.get("same_trace_case_id")
        if not isinstance(case, str) or not case:
            raise ValueError("no same-trace case identity")
        cases.add(case)
    if seen != {(p, k) for p in _PROFILE for k in _KINDS} or len(cases) != 1:
        raise ValueError("evidence triplets are not same-trace")
    return True

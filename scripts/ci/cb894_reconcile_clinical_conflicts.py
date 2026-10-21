"""Fail-closed, one-time PR #894 to master clinical conflict resolver.

Runs only on a disposable GitHub runner after a real uncommitted Git merge.
Never chooses upstream raw patient responses over master redaction.
"""
from pathlib import Path
import re
import sys

PINNED_SOURCE = "9cf19e68026fa92d31fb704f5b81b9cd667e5254"
PATTERN = re.compile(
    r"^<<<<<<< HEAD\n(?P<ours>.*?)^=======\n(?P<theirs>.*?)^>>>>>>> (?P<sha>[0-9a-f]{40})\n",
    re.MULTILINE | re.DOTALL,
)
PATHS = {"backend/routers/appointments.py": 2, "backend/routers/frontdesk.py": 1}


def resolve_appointments(s):
    matches = list(PATTERN.finditer(s))
    if len(matches) != 2:
        raise RuntimeError("REFUSED: appointment conflict count changed")
    for m in matches:
        if m["sha"] != PINNED_SOURCE:
            raise RuntimeError("REFUSED: unexpected upstream SHA")
        if m["ours"] != "    )\n    return _agenda_visible_appointment(db_appt, current_user)\n":
            raise RuntimeError("REFUSED: master privacy return changed")
        if ("    ))\n    db.commit()" not in m["theirs"]
            or m["theirs"].count("    return db_appt\n") != 1):
            raise RuntimeError("REFUSED: atomic audit/commit source changed")
    if 'action="CREATE"' not in s or 'action="UPDATE"' not in s:
        raise RuntimeError("REFUSED: audit actions missing")
    s = PATTERN.sub(
        lambda m: m["theirs"].replace(
            "    return db_appt\n",
            "    return _agenda_visible_appointment(db_appt, current_user)\n",
        ), s)
    if any(marker in s for marker in ("<<<<<<<", "=======", ">>>>>>>")):
        raise RuntimeError("REFUSED: unresolved conflict remains")
    return s


def resolve_frontdesk(s):
    matches = list(PATTERN.finditer(s))
    if len(matches) != 1 or matches[0]["sha"] != PINNED_SOURCE:
        raise RuntimeError("REFUSED: Frontdesk conflict count/source changed")
    m = matches[0]
    if ("audit_service.log(" not in m["ours"]
        or "return _visible_frontdesk_fields({" not in m["ours"]
        or m["theirs"] != "    return {\n"):
        raise RuntimeError("REFUSED: Frontdesk source differs from reviewed hunk")
    if not s[:m.start()].rstrip().endswith("db.refresh(appointment)"):
        raise RuntimeError("REFUSED: atomic Frontdesk audit and commit missing")
    if "}, current_user)" not in s[m.end():m.end()+650]:
        raise RuntimeError("REFUSED: master scoped return closure missing")
    # The new _frontdesk_audit was already committed with the appointment;
    # another post-commit audit_service.log would duplicate it, non-atomically.
    s = s[:m.start()] + "    return _visible_frontdesk_fields({\n" + s[m.end():]
    if any(marker in s for marker in ("<<<<<<<", "=======", ">>>>>>>")):
        raise RuntimeError("REFUSED: unresolved Frontdesk conflict remains")
    return s


def patch_pocket_contract():
    p = Path("backend/tests/test_mobile_frontdesk.py")
    s = p.read_text(encoding="utf-8")
    old = (
        '    confirmed = client.post(\n'
        '        f"/api/mobile/frontdesk/requests/{own.id}/confirm", headers=headers\n'
        '    )\n'
        '    assert confirmed.status_code == 200, confirmed.text\n'
    )
    if s.count(old) != 1:
        raise RuntimeError("REFUSED: historical Pocket confirmation test changed")
    new = (
        '    # No clinician assigned: a secretary must not silently confirm a slot.\n'
        '    refused = client.post(\n'
        '        f"/api/mobile/frontdesk/requests/{own.id}/confirm", headers=headers\n'
        '    )\n'
        '    assert refused.status_code == 422, refused.text\n'
        '    assert "praticien_id" in refused.text\n'
        '    db.rollback()\n'
        '    db.refresh(own)\n'
        '    assert own.status == schemas.AppointmentStatus.EN_ATTENTE_DEMANDE\n'
        '    assert own.confirmed_by_id is None\n'
        '    # Explicitly allocate a practitioner from the same authorized cabinet.\n'
        '    own.praticien_id = dentiste.id\n'
        '    db.commit()\n'
        '    confirmed = client.post(\n'
        '        f"/api/mobile/frontdesk/requests/{own.id}/confirm", headers=headers\n'
        '    )\n'
        '    assert confirmed.status_code == 200, confirmed.text\n'
    )
    p.write_text(s.replace(old, new), encoding="utf-8")


def main():
    paths = [p.strip() for p in Path("cb894-merge-diagnostic/conflicts.txt")
             .read_text(encoding="utf-8").splitlines() if p.strip()]
    if set(paths) != set(PATHS) or len(paths) != 2:
        raise RuntimeError("REFUSED: unexpected unmerged index " + repr(paths))
    for p in paths:
        file = Path(p)
        data = file.read_text(encoding="utf-8")
        resolved = (resolve_appointments(data) if p.endswith("appointments.py")
                    else resolve_frontdesk(data))
        file.write_text(resolved, encoding="utf-8")
    patch_pocket_contract()
    print("CB894_CLINICAL_3_HUNKS_AND_POCKET_422_CONTRACT_RESOLVED")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print("CB894_RESOLVER_REFUSED: " + str(err), file=sys.stderr)
        raise

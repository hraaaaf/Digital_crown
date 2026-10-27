#!/usr/bin/env python3
"""Check the migrated heavy Actions policy (fast, no product/runtime tests)."""
from pathlib import Path
import sys
import yaml

FILES = ["cabinet-code-cert-candidate.yml","ceph-p2ter-master-bridge-preflight.yml","ceph-p2ter-master-bridge-real-cabinet.yml","ceph-p2ter-master-bridge-frontend.yml","patient-companion-d2-visual-cert.yml","patient-p1-architecture-after.yml","patient-indicators-cert.yml","ortho-f3-after.yml","ortho-f4-after.yml","ux-continuity-patientdetails-cert.yml","lot07-r3-1-after-screenshots.yml","lot07-r2-ux-polish-9plus.yml","lot07-r2-ronly-dec02-e2e.yml","clinic-p2-patient-billing-visual-cert.yml","media-c5-visual-cert.yml"]

def check():
    errors = []
    for name in FILES:
        path = Path(".github/workflows") / name
        source = path.read_text(encoding="utf-8")
        try:
            obj = yaml.load(source, Loader=yaml.BaseLoader)
        except yaml.YAMLError as exc:
            errors.append(f"{name}: YAML invalid: {exc}")
            continue
        triggers = obj.get("on", {}) if isinstance(obj, dict) else {}
        push = triggers.get("push", {}) if isinstance(triggers, dict) else {}
        if not isinstance(triggers, dict) or set(triggers.keys()) != {"push"}:
            errors.append(f"{name}: heavy workflow must be push-only")
        if not isinstance(push, dict) or push.get("branches") != ["master"]:
            errors.append(f"{name}: must use push only on master")
        paths = push.get("paths", []) if isinstance(push, dict) else []
        if not paths or any(p.startswith(".github/workflows/") for p in paths):
            errors.append(f"{name}: missing paths or self-trigger")
        if name != "cabinet-code-cert-candidate.yml" and any(p in ("frontend/**", "backend/**", "**") for p in paths):
            errors.append(f"{name}: overbroad paths")
        conc = obj.get("concurrency", {}) if isinstance(obj, dict) else {}
        group = str(conc.get("group", "")) if isinstance(conc, dict) else ""
        cancel = str(conc.get("cancel-in-progress", "")).lower() if isinstance(conc, dict) else ""
        if "github.workflow" not in group or "github.ref" not in group or cancel != "true":
            errors.append(f"{name}: concurrency must group by workflow/ref and cancel")
        if "github.event.pull_request." in source:
            errors.append(f"{name}: PR context invalid on master push")
        if not isinstance(obj.get("jobs"), dict) or not obj["jobs"]:
            errors.append(f"{name}: no jobs")
        print("CHECK", name)
    human = (Path(".github/workflows") / "ui-human-visual-approval.yml").read_text()
    scope = (Path(".github/workflows") / "ci-scope-gate.yml").read_text()
    if "pull_request_target:" not in human:
        errors.append("trusted human gate was removed")
    if "pull_request:" not in scope:
        errors.append("lightweight PR scope gate was removed")
    if errors:
        print("\n".join("FAIL "+e for e in errors), file=sys.stderr)
        return 1
    print(f"PASS: {len(FILES)} post-merge contracts, human and scope gates kept")
    return 0

if __name__ == "__main__":
    raise SystemExit(check())

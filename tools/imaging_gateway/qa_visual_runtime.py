"""Reproducible LOT06 pre-merge OPERATIONAL surface — synthetic only.

Load the actual FastAPI route registry at both repository SHAs in separate
isolated interpreter processes. Screenshots visualize this inspected runtime
registry, NOT a product screen or a clinical workflow. No PHI or live service.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
import json
import os
from pathlib import Path
import subprocess
import sys

PREFLIGHT = "/api/imaging-acquisitions/preflight"
EXISTING_IMPORT = "/api/patients/{patient_id}/assets/import"
VIEWPORTS = ((390, 844), (768, 1024), (1280, 900))
COLLECT = r"""
import json
from backend.main import app

routes = sorted([
    {"path": route.path, "methods": sorted(route.methods or [])}
    for route in app.routes if getattr(route, "path", None)
    and getattr(route, "methods", None)
], key=lambda item: (item["path"], item["methods"]))
print("LOT06_ROUTE_JSON=" + json.dumps(routes, sort_keys=True))
"""


def collect(root: Path) -> list[dict]:
    env = os.environ.copy()
    env.update({
        "ENVIRONMENT": "test",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "DC_V15_06_PREFLIGHT_LAB": "0",
        "DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "synthetic-lot06-visual-qa-not-production-secret",
        "TELEMETRY_ENABLED": "false",
        "CLOUD_AI_ENABLED": "false",
        "DEBUG": "false",
        "PYTHONPATH": str(root.resolve()),
    })
    completed = subprocess.run(
        [sys.executable, "-c", COLLECT], cwd=root, env=env,
        capture_output=True, text=True, timeout=180, check=False,
    )
    if completed.returncode:
        # No full traceback from sensitive runtime environments in the artifact.
        raise RuntimeError("FASTAPI_ROUTE_IMPORT_FAILED: " + str(completed.returncode))
    marker = "LOT06_ROUTE_JSON="
    payloads = [line[len(marker):] for line in completed.stdout.splitlines()
                if line.startswith(marker)]
    if len(payloads) != 1:
        raise AssertionError("FASTAPI_ROUTE_SNAPSHOT_MISSING_OR_AMBIGUOUS")
    items = json.loads(payloads[0])
    if not isinstance(items, list) or not items:
        raise AssertionError("FASTAPI_ROUTE_SNAPSHOT_EMPTY")
    return items


def signature(row: dict) -> tuple[str, tuple[str, ...]]:
    return str(row["path"]), tuple(row["methods"])


def route_delta(before: list[tuple[str, tuple[str, ...]]],
                after: list[tuple[str, tuple[str, ...]]]
                ) -> tuple[list[tuple[str, tuple[str, ...]]], list[tuple[str, tuple[str, ...]]]]:
    """Multiset diff: duplicate registered routes cannot masquerade as no delta."""
    old_counts, new_counts = Counter(before), Counter(after)
    return (
        sorted((new_counts - old_counts).elements()),
        sorted((old_counts - new_counts).elements()),
    )


def render(phase: str, sha: str, before_count: int, after_count: int,
           evidence: dict) -> str:
    if phase not in ("BEFORE", "AFTER"):
        raise ValueError("INVALID_PHASE")
    present = phase == "AFTER"
    now = after_count if present else before_count
    label = "ENREGISTRÉE UNE FOIS" if present else "ABSENTE"
    status = "POST /api/imaging-acquisitions/preflight" if present else "Aucune route LOT06-B"
    safe_sha = html.escape(sha)
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Digital Crown · LOT06 — État opérationnel {phase}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f6f7f9;color:#18212d;font:16px system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1060px;margin:auto;padding:clamp(16px,4vw,42px)}}
.eyebrow{{font-weight:750;font-size:12px;letter-spacing:.13em;color:#526377}}
h1{{font-size:clamp(23px,4vw,36px);line-height:1.16;margin:10px 0}}
p{{line-height:1.55}}.muted{{color:#4c5b6b}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,290px),1fr));gap:14px;margin:22px 0}}
.card{{background:#fff;border:1px solid #dce2e9;border-radius:14px;padding:20px;min-width:0}}
small{{display:block;color:#536273;font-size:13px;font-weight:650;margin-bottom:9px}}
code{{overflow-wrap:anywhere;word-break:break-word;font:13px ui-monospace,SFMono-Regular,monospace}}
.value{{font-size:clamp(19px,3vw,26px);font-weight:760;margin-bottom:6px}}
.good{{color:#14624b}}.neutral{{color:#41556b}}
footer{{margin-top:20px;padding-top:14px;border-top:1px solid #dce2e9;color:#455467;font-size:13px;line-height:1.5}}
</style></head><body><main>
<div class="eyebrow">DIGITAL CROWN · LOT06 · OBSERVATION DU RUNTIME FASTAPI</div>
<h1>Routage opérationnel — {phase}</h1>
<p class="muted">Données extraites du <strong>vrai registre de routes chargé en Python</strong>
depuis le commit indiqué. Il ne s'agit ni d'une interface produit ni d'une preuve d'autorisation clinique.</p>
<div class="grid">
<section class="card"><small>État du routage préflight</small>
<div class="value {'good' if present else 'neutral'}">{label}</div>
<code>{status}</code></section>
<section class="card"><small>Nombre de routes préflight POST</small>
<div class="value">{now}</div>
<p class="muted">Attendu: 0 BEFORE / 1 AFTER</p></section>
<section class="card"><small>Route média historique</small>
<div class="value good">PRÉSERVÉE</div>
<code>{html.escape(EXISTING_IMPORT)}</code></section>
<section class="card"><small>SHA Git exact</small><code>{safe_sha}</code></section>
</div>
<div class="card">
<small>But vérifié · Contrat observable</small>
<p>Avant : aucune route de préflight. Après : exactement une route
<code>POST /api/imaging-acquisitions/preflight</code>.
Le routage existant d'import média reste identique.</p>
<p class="muted">Les refus, le contrôle du tenant et l'absence de création
d'actifs cliniques sont vérifiés séparément par le workflow 06-B (pytest).</p>
</div>
<footer>Provenance : app FastAPI importée en processus isolé, données fictives, 
ENVIRONMENT=test, préflight désactivé. Captures 390×844, 768×1024 et 1280×900
aux mêmes états pour revue humaine. LOT10 matériel entièrement hors scope.</footer>
</main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-root", type=Path, required=True)
    parser.add_argument("--after-root", type=Path, required=True)
    parser.add_argument("--before-sha", required=True)
    parser.add_argument("--after-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    def head(root: Path) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True,
        ).strip()

    if head(args.before_root) != args.before_sha or head(args.after_root) != args.after_sha:
        raise AssertionError("SHA_REF_MISMATCH")

    before = collect(args.before_root)
    after = collect(args.after_root)
    old = [signature(x) for x in before]
    new = [signature(x) for x in after]
    bpre = sum(x == (PREFLIGHT, ("POST",)) for x in old)
    apre = sum(x == (PREFLIGHT, ("POST",)) for x in new)
    bimp = sum(x[0] == EXISTING_IMPORT and "POST" in x[1] for x in old)
    aimp = sum(x[0] == EXISTING_IMPORT and "POST" in x[1] for x in new)
    extra, missing = route_delta(old, new)
    if (bpre, apre, bimp, aimp) != (0, 1, 1, 1):
        raise AssertionError("PREFLIGHT_OR_LEGACY_ROUTE_INVARIANT_FAILURE")
    if extra != [(PREFLIGHT, ("POST",))] or missing:
        raise AssertionError("UNEXPECTED_RUNTIME_ROUTE_DIFF")

    summary = {
        "kind": "LOT06_SYNTHETIC_OPERATIONAL_FASTAPI_REGISTRY",
        "before_sha": args.before_sha, "after_sha": args.after_sha,
        "before_route_count": len(before), "after_route_count": len(after),
        "before_preflight": bpre, "after_preflight": apre,
        "existing_media_import_before": bimp, "existing_media_import_after": aimp,
        "new_routes": [{"path": p, "methods": list(m)} for p, m in extra],
        "removed_routes": [],
        "scope": "software only; operational evidence, not a product UI screenshot",
        "viewports": [{"width": w, "height": h} for w, h in VIEWPORTS],
        "screenshots": [],
    }

    for phase, sha in (("BEFORE", args.before_sha), ("AFTER", args.after_sha)):
        filename = f"{phase.lower()}.html"
        (args.out / filename).write_text(
            render(phase, sha, bpre, apre, summary), encoding="utf-8"
        )

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("PLAYWRIGHT_REQUIRED_FOR_REAL_BROWSER_CAPTURE") from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for width, height in VIEWPORTS:
                context = browser.new_context(viewport={"width": width, "height": height},
                                              locale="fr-FR")
                page = context.new_page()
                for phase in ("before", "after"):
                    page.goto((args.out / (phase + ".html")).resolve().as_uri(),
                              wait_until="load")
                    size = page.evaluate("""() => ({
                       scrollWidth: document.documentElement.scrollWidth,
                       clientWidth: document.documentElement.clientWidth
                    })""")
                    if size["scrollWidth"] > size["clientWidth"]:
                        raise AssertionError("HORIZONTAL_OVERFLOW_" + phase + "_" + str(width))
                    file = f"{phase}-{width}x{height}.png"
                    page.screenshot(path=str(args.out / file), full_page=True,
                                    animations="disabled")
                    digest = hashlib.sha256((args.out / file).read_bytes()).hexdigest()
                    summary["screenshots"].append({
                        "phase": phase, "viewport": f"{width}x{height}",
                        "file": file, "sha256": digest,
                        "overflow": False,
                    })
                context.close()
        finally:
            browser.close()

    if len(summary["screenshots"]) != 6:
        raise AssertionError("EXPECTED_SIX_SCREENSHOTS")
    (args.out / "report.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("LOT06_OPERATIONAL_BEFORE_AFTER_PASS: 6 screenshots; "
          "actual FastAPI routes; no UI/clinical/physical certification")


if __name__ == "__main__":
    main()

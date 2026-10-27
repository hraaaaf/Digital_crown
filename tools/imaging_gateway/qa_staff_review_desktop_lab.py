"""LOT06-B visual proof of the *offline fictitious desktop UI only*.

Never handles clinical data, a device, staff authentication or real receipts.
The React preview is a separate Vite DEV entry outside App.tsx.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.url.startswith("http://127.0.0.1:"):
        raise RuntimeError("LOCAL_VITE_DEV_ONLY")
    if not args.url.endswith("/staff-review-lab.html"):
        raise RuntimeError("EXPECTED_STAFF_LAB_HTML")
    args.out.mkdir(parents=True, exist_ok=True)

    evidence: list[dict] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for width, height in ((1280, 900), (1440, 900)):
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                page.goto(args.url, wait_until="networkidle")
                page.get_by_role("heading", name="Associer une capture au bon patient").wait_for()
                if not page.get_by_text("LAB FICTIF · AUCUN REÇU CLINIQUE").is_visible():
                    raise AssertionError("LAB_WARNING_MISSING")
                if page.locator("#lab-patient").input_value() != "":
                    raise AssertionError("PATIENT_MUST_NOT_BE_PRESELECTED")
                if page.get_by_role("button", name="Vérifier le lien patient").is_enabled():
                    raise AssertionError("NO_PATIENT_REVIEW_BYPASS")
                if page.get_by_role("button", name="Confirmer ce patient").count():
                    raise AssertionError("NO_PREMATURE_CONFIRMATION")

                def capture(phase: str) -> None:
                    geometry = page.evaluate("""() => ({
                        scroll: document.documentElement.scrollWidth,
                        client: document.documentElement.clientWidth
                    })""")
                    if geometry["scroll"] > geometry["client"]:
                        raise AssertionError("HORIZONTAL_OVERFLOW_" + phase)
                    path = args.out / f"{phase}-{width}x{height}.png"
                    page.screenshot(path=str(path), full_page=True, animations="disabled")
                    evidence.append({
                        "phase": phase, "viewport": f"{width}x{height}",
                        "file": path.name,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    })

                capture("waiting")
                page.locator("#lab-patient").select_option("101")
                page.locator("#lab-appointment").select_option("301")
                page.get_by_role("button", name="Vérifier le lien patient").click()
                page.get_by_text("Vérifier avant confirmation").wait_for()
                if page.get_by_role("button", name="Confirmer ce patient").count() != 1:
                    raise AssertionError("EXPLICIT_CONFIRMATION_MISSING")
                capture("reviewed")
                page.get_by_role("button", name="Confirmer ce patient").click()
                page.get_by_text(
                    "Association approuvée dans le LAB.", exact=False
                ).wait_for()
                if page.get_by_role("button", name="Confirmer ce patient").count():
                    raise AssertionError("DUPLICATE_CONFIRMATION_ALLOWED")
                capture("approved-lab-only")

                page.reload(wait_until="networkidle")
                page.locator("#lab-patient").select_option("102")
                if page.get_by_role("button", name="Vérifier le lien patient").is_enabled():
                    raise AssertionError("PATIENT_ONLY_REASON_BYPASS")
                page.locator("#lab-reason").fill("Consultation fictive non programmée")
                if not page.get_by_role("button", name="Vérifier le lien patient").is_enabled():
                    raise AssertionError("JUSTIFIED_PATIENT_ONLY_BLOCKED")
                context.close()
        finally:
            browser.close()

    if len(evidence) != 6:
        raise AssertionError("EXPECTED_SIX_DESKTOP_SHOTS")
    (args.out / "report.json").write_text(json.dumps({
        "kind": "LOT06B_SYNTHETIC_DEV_DESKTOP_OPERATOR_UI",
        "screenshots": evidence,
        "clinical_confirmation": False,
        "server_receipt": False,
        "server_connected": False,
        "source": "DEV_ONLY_LOCAL_VITE_MOCKED_REVIEW_FLOW",
        "physical_device_test": False,
        "human_signoff": False,
    }, indent=2) + "\n", encoding="utf-8")
    print("LOT06B_DESKTOP_VISUAL_PASS: real browser clicks, six screenshots, synthetic only")


if __name__ == "__main__":
    main()

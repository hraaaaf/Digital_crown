#!/usr/bin/env python3
"""Human-review screenshots from the real Digital Crown A4 PDF renderer.

Test-only fixtures. NEVER use patient files, network imagery, generated diagnoses
or a user-entered QR validation URL. Review screenshots remain NOT APPROVED.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
import os
import subprocess
import sys
from pathlib import Path

# GitHub Actions invokes this script by path, not as a package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fitz
from PIL import Image, ImageDraw, ImageFont

from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator
from backend.tests.test_cephalo_v1_l3_a4_document import _projection, _test_vm

OUTPUT = Path(os.environ.get("CEPHALO_PDF_VISUAL_OUTPUT", "artifacts/cephalo-pdf-l3-human-review"))
OUTPUT.mkdir(parents=True, exist_ok=True)


def synthetic_plate(label: str, *, radiograph: bool = False) -> bytes:
    width, height = (1200, 1600) if radiograph else (800, 600)
    img = Image.new("RGB", (width, height), "#edf2f6" if radiograph else "#e8eff4")
    draw = ImageDraw.Draw(img)
    draw.rectangle((28, 28, width - 29, height - 29), outline="#20456b", width=8)
    if radiograph:
        # Abstract nonanatomical polygons rather than a pretend true tracing.
        draw.ellipse((width // 4, height // 8, 3 * width // 4, height // 2),
                     fill="#dae2ea", outline="#8ba1b4", width=7)
        draw.polygon([(460, 600), (670, 700), (570, 1090), (430, 960)],
                     fill="#c5d3e0", outline="#6485a1")
    else:
        draw.ellipse((width // 4, height // 5, 3 * width // 4, 4 * height // 5),
                     outline="#9cb3c9", width=12)
    draw.text((55, 65), "ILLUSTRATION SYNTHETIQUE", fill="#294767")
    draw.text((55, 115), label, fill="#294767")
    draw.text((55, height - 110), "AUCUN PATIENT - AUCUN DIAGNOSTIC", fill="#b03d3d")
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=86)
    return buffer.getvalue()


def visual_fixture(name: str, *, with_images: bool):
    vm = _test_vm()
    vm.patient_nom = "DEMONSTRATION"
    vm.patient_prenom = "Synthetique"
    vm.cabinet_config.update({
        "logo_path": "visual-demo-logo.png",
        "nom_cabinet": "CABINET DEMO DIGITAL CROWN",
        "header_lines_fr": ["Cabinet DEMO", "Chirurgie dentaire et orthodontie"],
        "footer_address": "Adresse de demonstration — non reelle",
        "footer_phones": "+00 000 000 000",
        "qr_code_enabled": True,
        "qr_code_type": "WEBSITE",
        "qr_code_value": "example.org",
        "qr_code_label": "Exemple non clinique",
        "selected_template": "swiss" if with_images else "modern",
        "primary_color": "#12406B" if with_images else "#45566C",
        "secondary_color": "#637084" if with_images else "#657587",
    })
    projection = _projection()
    projection["measurements"] = [
        {
            "measurement_id": "SIM_" + identifier,
            "value": value,
            "unit": unit,
            "availability_status": "AVAILABLE" if value is not None else "NOT_COMPUTABLE",
            "method_id": "SOURCE_SYNTHETIQUE",
            "method_version": "fixture-v1",
            "scientific_source": "SYNTHETIC_NON_CLINICAL",
        }
        for identifier, value, unit in (
            ("SNA", 81.5, "deg"), ("SNB", 78.4, "deg"),
            ("ANB", 3.1, "deg"), ("IMPA", 94.2, "deg"),
            ("U1_NA_MM", None, "mm"), ("L1_NB_MM", None, "mm"),
            ("FMA", 25.0, "deg"), ("WITS", None, "mm"),
        )
    ]
    projection["clinical_validation_reason"] = "PREUVE R14 ABSENTE — DEMONSTRATION"
    projection["blocking_gates"] = ["r14_authoritative_snapshot_not_persisted"]
    photographs = []
    if with_images:
        for slot, group in (
            ("Face repos", "Extra-buccales"), ("Profil", "Extra-buccales"),
            ("Sourire", "Extra-buccales"), ("Intra frontal", "Intra-buccales"),
            ("Intra droit", "Intra-buccales"), ("Intra gauche", "Intra-buccales"),
            ("Occlusal maxillaire", "Intra-buccales"),
            ("Occlusal mandibulaire", "Intra-buccales"),
        ):
            photographs.append({"group": group, "label": slot, "jpeg": synthetic_plate(slot)})
    return vm, projection, {
        "radio_jpeg": synthetic_plate("TELERADIO - DEMO", radiograph=True) if with_images else None,
        "photos": photographs,
        "media_unavailable": [],
    }


def capture(name: str, *, with_images: bool) -> dict:
    vm, projection, media = visual_fixture(name, with_images=with_images)
    output = OUTPUT / f"{name}.pdf"
    generator = BilanOrthoPDFGenerator(str(OUTPUT))
    generated = generator.generate(vm, filename=output.name, projection=projection, media=media)
    assert Path(generated).resolve() == output.resolve()
    data = output.read_bytes()
    assert data.startswith(b"%PDF")
    captures = []
    with fitz.open(output) as doc:
        assert doc.page_count == (2 if with_images else 1), "Orphan or overflow A4 page"
        if with_images:
            intra_labels = (
                "Intra frontal", "Intra droit", "Intra gauche",
                "Occlusal maxillaire", "Occlusal mandibulaire",
            )
            intra_pages = [
                page.number for page in doc
                if all(label in page.get_text() for label in intra_labels)
            ]
            assert len(intra_pages) == 1, "Intraoral photo group split across pages"
        for i, page in enumerate(doc):
            assert 590 <= page.rect.width <= 600 and 840 <= page.rect.height <= 850, "Not A4"
            shot = OUTPUT / f"{name}-page-{i + 1:02d}.png"
            page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False).save(shot)
            captures.append(shot.name)
        text = "\n".join(page.get_text() for page in doc)
        assert "TRAÇABILITÉ SCIENTIFIQUE" not in text
        assert "EVIDENCE_GRAPH_V1" not in text
        assert "SYNTHETIC_NON_CLINICAL" not in text
        for label in ("SOURCE_SYNTHETIQUE", "fixture-v1", "BLOCKED", "NOT_COMPUTABLE", "EVALUABLE"):
            assert label not in text, f"Unexpected internal PDF label: {label}"
        for required in ("BILAN ORTHODONTIQUE", "ANALYSE", "MOULAGES", "DIAGNOSTIQUE", "PLAN DE TRAITEMENT", "DOCUMENT CLINIQUE INCOMPLET", "NON VALIDÉ"):
            assert required in text.upper(), f"Missing {required}"
    return {
        "scenario": name,
        "source": "actual BilanOrthoPDFGenerator, no mock",
        "clinical_data": "SYNTHETIC_NON_CLINICAL",
        "human_approved": False,
        "pdf": output.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "captures": captures,
        "page_count": len(captures),
    }


def main():
    # Prove that the normal document header resolves a configurable local logo
    # from the isolated media root rather than a hardcoded template image.
    media_root = (OUTPUT / "synthetic-media-root").resolve()
    media_root.mkdir(parents=True, exist_ok=True)
    os.environ["MEDIA_ROOT"] = str(media_root)
    demo_logo = Image.new("RGB", (240, 240), "#ffffff")
    pen = ImageDraw.Draw(demo_logo)
    pen.ellipse((12, 12, 228, 228), fill="#12406B")
    pen.text((72, 100), "DC", fill="#ffffff")
    demo_logo.save(media_root / "visual-demo-logo.png")
    items = [
        capture("a4-swiss-with-synthetic-photos", with_images=True),
        capture("a4-modern-no-images", with_images=False),
    ]
    # A separate montage is convenient for quick human triage. The originals
    # above must be reviewed at full resolution before any visual approval.
    thumbs = []
    for item in items:
        for name in item["captures"]:
            with Image.open(OUTPUT / name) as page:
                thumb = page.copy()
                thumb.thumbnail((560, 780))
                thumbs.append((name, thumb))
    columns, gap, label_height = 2, 20, 35
    rows = (len(thumbs) + columns - 1) // columns
    montage = Image.new("RGB", (2 * 560 + 3 * gap, rows * (780 + label_height + gap) + gap), "#e8edf2")
    pen = ImageDraw.Draw(montage)
    for j, (name, thumb) in enumerate(thumbs):
        x, y = gap + (j % columns) * (560 + gap), gap + (j // columns) * (780 + label_height + gap)
        montage.paste(thumb, (x, y + label_height))
        pen.text((x + 4, y), name[:65], fill="#1e293b")
    montage.save(OUTPUT / "contact-sheet.png")
    exact_checkout_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    expected_sha = os.environ.get("EXPECTED_SHA")
    if expected_sha and exact_checkout_sha != expected_sha:
        raise RuntimeError("Wrong checkout SHA for screenshots")
    manifest = {
        "commit": exact_checkout_sha,
        "source_branch": os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or "UNKNOWN",
        "review_status": "VISUAL_HUMAN_APPROVAL_REQUIRED",
        "scope": "A4 PDF actual renderer; UI modal/browser preview NOT captured",
        "photos": "synthetic plates only; not clinical photographs",
        "tracing": "no authoritative traced image; not shown as real",
        "mould_scans": "no verified rendered model image",
        "documents": items,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "capture_count": sum(len(t["captures"]) for t in items), "manifest": manifest}, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render the real AccountingGenerator at three dedicated vertical body offsets."""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import fitz
from PIL import Image, ImageDraw, ImageOps

from backend.services.generators.accounting_gen import AccountingGenerator
from scripts.audit_document_models import ACTS, HEADER_AR, HEADER_FR, FakeDB, _config, _make_logo, _normalize

ROOT = Path("document-content-position-audit")
PDF_DIR = ROOT / "pdf"
PNG_DIR = ROOT / "png"
PDF_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR.mkdir(parents=True, exist_ok=True)

POSITIONS = [
    ("higher", -0.8, "Plus haut (-8 mm demandé)"),
    ("neutral", 0.0, "Neutre (0)"),
    ("lower", 1.5, "Plus bas (+15 mm)"),
]


def _title_y(doc: fitz.Document) -> float:
    for page in doc:
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                text = _normalize("".join(span.get("text", "") for span in line.get("spans", [])))
                if "NOTE D'HONORAIRES" in text:
                    return round(float(line["bbox"][1]), 2)
    raise AssertionError("title bbox not found")


def _sheet(items: list[tuple[str, Path]], output: Path) -> None:
    width, height, label_h, gap = 500, 707, 55, 20
    sheet = Image.new("RGB", (3 * width + 4 * gap, height + label_h + 2 * gap), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (label, path) in enumerate(items):
        image = ImageOps.contain(Image.open(path).convert("RGB"), (width, height))
        x = gap + index * (width + gap)
        draw.text((x + 6, gap + 16), label, fill="black")
        panel = Image.new("RGB", (width, height), "white")
        panel.paste(image, ((width - image.width) // 2, (height - image.height) // 2))
        sheet.paste(panel, (x, gap + label_h))
    sheet.save(output)


def main() -> None:
    logo = _make_logo()
    patient = SimpleNamespace(nom="ALAMI", prenom="Sara", date_naissance=dt.date(1990, 4, 12))
    payments = [
        SimpleNamespace(acte=act, dents=dents, dent=(dents[0] if dents else "-"), mode_reglement=mode, montant=amount)
        for act, dents, mode, amount in ACTS
    ]
    data = SimpleNamespace(
        id="AUDIT-POSITION-10",
        doc_date=dt.date(2026, 9, 2),
        payments=payments,
        installments=[],
        is_global_note=False,
    )
    user = SimpleNamespace(id=1, nom="Benmoussa", prenom="Achraf", email="audit@digitalcrown.local")

    rendered = []
    metrics = {}
    for key, offset_y, label in POSITIONS:
        config = _config("swiss", logo)
        config.margin_top = 3.6
        config.content_offset_y = offset_y
        config.header_lines_fr = HEADER_FR
        config.header_lines_ar = HEADER_AR
        generator = AccountingGenerator(str(PDF_DIR / key / "generated"))
        generated = Path(
            generator.generate_note(
                patient,
                data,
                facture_number="F-2026-0010",
                db=FakeDB(config, user),
                user_id=1,
            )
        )
        target = PDF_DIR / f"swiss-{key}.pdf"
        shutil.copy2(generated, target)
        doc = fitz.open(target)
        assert doc.page_count >= 1
        title_y = _title_y(doc)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
        png = PNG_DIR / f"swiss-{key}.png"
        pix.save(png)
        doc.close()
        metrics[key] = {"content_offset_y_cm": offset_y, "title_y_points": title_y}
        rendered.append((f"{label} | titre y={title_y} pt", png))

    # PyMuPDF bbox y uses a top-left origin: larger y means lower on page.
    assert metrics["higher"]["title_y_points"] <= metrics["neutral"]["title_y_points"]
    assert metrics["neutral"]["title_y_points"] < metrics["lower"]["title_y_points"]
    assert metrics["lower"]["title_y_points"] - metrics["neutral"]["title_y_points"] >= 20.0

    _sheet(rendered, ROOT / "position-comparison.png")
    (ROOT / "manifest.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

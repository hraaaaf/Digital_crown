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
from reportlab.lib.units import cm

from backend.services.generators.accounting_gen import AccountingGenerator
from scripts.audit_document_models import ACTS, HEADER_AR, HEADER_FR, FakeDB, _config, _make_logo, _normalize

ROOT = Path("document-content-position-audit")
PDF_DIR = ROOT / "pdf"
PNG_DIR = ROOT / "png"
PDF_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR.mkdir(parents=True, exist_ok=True)

POSITIONS = [
    ("higher", -0.8, "Plus haut (-8 mm)"),
    ("neutral", 0.0, "Neutre (0)"),
    ("lower", 1.5, "Plus bas (+15 mm)"),
]


def _line_y(doc: fitz.Document, needle: str) -> float:
    expected = _normalize(needle).casefold()
    for page in doc:
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                text = _normalize("".join(span.get("text", "") for span in line.get("spans", [])))
                if expected in text.casefold():
                    return round(float(line["bbox"][1]), 2)
    raise AssertionError(f"bbox not found for {needle!r}")


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
        assert 1 <= doc.page_count <= 2

        title_y = _line_y(doc, "NOTE D'HONORAIRES")
        header_y = _line_y(doc, "Dr. Achraf Benmoussa")
        full_text = _normalize("\n".join(page.get_text("text") for page in doc))
        for act, *_ in ACTS:
            assert _normalize(act) in full_text
        assert "18100.00" in full_text

        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
        png = PNG_DIR / f"swiss-{key}.png"
        pix.save(png)
        page_count = doc.page_count
        doc.close()

        metrics[key] = {
            "content_offset_y_cm": offset_y,
            "title_y_points": title_y,
            "header_y_points": header_y,
            "page_count": page_count,
        }
        rendered.append((f"{label} | titre y={title_y} pt", png))

    # PyMuPDF bbox y uses a top-left origin: larger y means lower on page.
    up_delta = metrics["neutral"]["title_y_points"] - metrics["higher"]["title_y_points"]
    down_delta = metrics["lower"]["title_y_points"] - metrics["neutral"]["title_y_points"]
    assert abs(up_delta - 0.8 * cm) <= 1.0
    assert abs(down_delta - 1.5 * cm) <= 1.0

    # Header must not move when only the body offset changes.
    header_positions = [metrics[key]["header_y_points"] for key, *_ in POSITIONS]
    assert max(header_positions) - min(header_positions) <= 0.1

    _sheet(rendered, ROOT / "position-comparison.png")
    (ROOT / "manifest.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

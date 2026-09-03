#!/usr/bin/env python3
"""Generate real Digital Crown A5 accounting documents for visual certification.

The harness calls the repository AccountingGenerator and BaseTemplate directly.
Arabic is shaped by the product _prepare_arabic path and painted as vector text
by ReportLab. PDF text extraction is intentionally not used as the Arabic
oracle because shaped/subset TrueType glyphs do not always round-trip to
Unicode through PDF extractors.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageOps

from backend.services.generators.accounting_gen import AccountingGenerator

ROOT = Path("document-models-audit")
PDF_DIR = ROOT / "pdf"
PNG_DIR = ROOT / "png"
PDF_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES = ["swiss", "royal", "clinical", "modern", "heritage"]
LABELS = {
    "swiss": "Swiss Clinic",
    "royal": "Royal Elite",
    "clinical": "Clinical Grid",
    "modern": "Modern Flush",
    "heritage": "L'Héritage",
}
HEADER_FR = [
    "Dr. Achraf Benmoussa",
    "Chirurgien Dentiste",
    "Soins - Endodontie",
    "Parodontologie - Orthodontie",
    "Prothèse - Chirurgie",
    "Implantologie - Blanchiment",
    "Esthétique - Spécialité personnalisée",
]
HEADER_AR = [
    "د. أشرف بنموسى",
    "طبيب جراح للأسنان",
    "علاج - علاج العصب",
    "أمراض اللثة - تقويم الأسنان",
    "تعويض الأسنان - جراحة",
    "زراعة الأسنان - تبييض الأسنان",
    "تجميل الأسنان - تخصص مخصص",
]
ACTS = [
    ("Consultation et bilan clinique complet", [11, 12], "Carte", 350.00),
    ("Détartrage ultrasonique des deux arcades", [16, 26, 36, 46], "Carte", 600.00),
    ("Traitement endodontique molaire", [36], "Espèces", 1800.00),
    ("Reconstitution coronaire composite postérieure", [36], "Espèces", 750.00),
    ("Couronne céramo-céramique sur molaire", [36], "Virement", 3200.00),
    ("Extraction chirurgicale dent de sagesse incluse", [48], "Carte", 1500.00),
    ("Implant dentaire ostéointégré", [46], "Virement", 6500.00),
    ("Couronne provisoire implanto-portée", [46], "Virement", 900.00),
    ("Blanchiment ambulatoire avec gouttières", [], "Carte", 2200.00),
    ("Contrôle post-opératoire et ajustement occlusal", [36, 46], "Espèces", 300.00),
]
EXPECTED_TOTAL = sum(row[3] for row in ACTS)


class FakeQuery:
    def __init__(self, value):
        self.value = value

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.value


class FakeDB:
    def __init__(self, config, user):
        self.config = config
        self.user = user

    def query(self, model):
        return FakeQuery(self.config if model.__name__ == "CabinetConfig" else self.user)


def _make_logo() -> str:
    upload_dir = Path("backend/static/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = "document-audit-logo.png"
    target = upload_dir / filename
    image = Image.new("RGBA", (400, 400), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((14, 14, 386, 386), fill="#003380")
    font_path = Path("backend/static/assets/fonts/Outfit-Bold.ttf")
    font = ImageFont.truetype(str(font_path), 145) if font_path.exists() else ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "DC", font=font)
    draw.text(
        ((400 - (bbox[2] - bbox[0])) / 2, (400 - (bbox[3] - bbox[1])) / 2 - bbox[1]),
        "DC",
        fill="white",
        font=font,
    )
    image.save(target)
    return filename


def _config(template: str, logo: str):
    return SimpleNamespace(
        primary_color="#003380",
        secondary_color="#1e40af",
        accent_color="#60a5fa",
        selected_template=template,
        font_fr="inter",
        header_font_scale=1.0,
        header_logo_scale=1.0,
        header_line_height=1.0,
        header_scale=1.0,
        header_logo_offset_x=0.0,
        header_logo_offset_y=0.0,
        footer_font_scale=1.0,
        footer_qr_scale=1.0,
        footer_line_height=1.0,
        qr_code_enabled=False,
        watermark_enabled=False,
        hide_header=False,
        hide_footer=False,
        use_letterhead=False,
        letterhead_path=None,
        logo_path=logo,
        header_lines_fr=HEADER_FR,
        header_lines_ar=HEADER_AR,
        footer_address="Rabat, Maroc",
        footer_phones="05 37 00 00 00",
        footer_email="contact@digitalcrown.local",
        adresse="Rabat, Maroc",
        telephone="05 37 00 00 00",
        nom_cabinet="Cabinet Dentaire Digital Crown",
        nom_praticien="Dr. Achraf Benmoussa",
        nom_praticien_ar="د. أشرف بنموسى",
        nom="Achraf Benmoussa",
        inpe="",
        inpe_etablissement="",
        ice="",
        if_="",
        contacts_json={},
        qr_code_type="VCARD",
        qr_code_value=None,
        qr_code_color=None,
        qr_code_label=None,
        qr_code_style="dots",
        qr_code_offset_x=0.0,
        qr_code_offset_y=0.0,
        cloture_note_template="Arrêtée la présente note d'honoraires à la somme de {total_words} TTC.",
        margin_top=3.6,
        margin_bottom=3.2,
        content_offset_y=0.0,
    )


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()


def _token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower()).replace("regular", "")


def _embedded_arabic_font(doc: fitz.Document, font_path: str) -> tuple[bool, list[str]]:
    expected = _token(Path(font_path).stem)
    resources = []
    for page in doc:
        for item in page.get_fonts(full=True):
            resources.append(str(item[3] or ""))
    normalized = [_token(name.split("+")[-1]) for name in resources]
    found = any(expected and (expected in name or name in expected) for name in normalized)
    return found, resources


def _span_metrics(doc: fitz.Document) -> dict:
    spans = []
    for page_no, page in enumerate(doc):
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = _normalize(span.get("text", ""))
                    if text:
                        spans.append(
                            {
                                "page": page_no + 1,
                                "text": text,
                                "font": span.get("font"),
                                "size": round(float(span.get("size", 0.0)), 3),
                                "bbox": [round(float(v), 2) for v in span.get("bbox", ())],
                            }
                        )
    sizes = [span["size"] for span in spans if span["size"] > 0]
    return {
        "minimum_span_size": min(sizes) if sizes else None,
        "maximum_span_size": max(sizes) if sizes else None,
        "spans": spans,
    }


def _contact_sheet(images: list[tuple[str, Path]], output: Path) -> None:
    thumb_w, thumb_h, label_h, gap = 520, 735, 52, 20
    cols = 2
    rows = max(1, math.ceil(len(images) / cols))
    sheet = Image.new(
        "RGB",
        (cols * thumb_w + (cols + 1) * gap, rows * (thumb_h + label_h) + (rows + 1) * gap),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for index, (label, path) in enumerate(images):
        image = ImageOps.contain(Image.open(path).convert("RGB"), (thumb_w, thumb_h))
        panel = Image.new("RGB", (thumb_w, thumb_h), "white")
        panel.paste(image, ((thumb_w - image.width) // 2, (thumb_h - image.height) // 2))
        row, col = divmod(index, cols)
        x = gap + col * (thumb_w + gap)
        y = gap + row * (thumb_h + label_h + gap)
        draw.text((x + 8, y + 16), label, fill="black")
        sheet.paste(panel, (x, y + label_h))
    sheet.save(output)


def main() -> None:
    logo = _make_logo()
    patient = SimpleNamespace(nom="ALAMI", prenom="Sara", date_naissance=dt.date(1990, 4, 12))
    payments = [
        SimpleNamespace(acte=act, dents=dents, dent=(dents[0] if dents else "-"), mode_reglement=mode, montant=amount)
        for act, dents, mode, amount in ACTS
    ]
    data = SimpleNamespace(
        id="AUDIT-FACT-10",
        doc_date=dt.date(2026, 9, 2),
        payments=payments,
        installments=[],
        is_global_note=False,
    )
    user = SimpleNamespace(id=1, nom="Benmoussa", prenom="Achraf", email="audit@digitalcrown.local")
    rendered = []
    manifest = {
        "generator": "backend.services.generators.accounting_gen.AccountingGenerator",
        "expected_total": EXPECTED_TOTAL,
        "templates": {},
    }

    for template in TEMPLATES:
        config = _config(template, logo)
        generator = AccountingGenerator(str(PDF_DIR / template / "generated"))
        assert generator.base_template.arabic_font == "ArabicFont"
        arabic_font_path = generator.base_template.arabic_font_path
        assert Path(arabic_font_path).exists()

        shape_calls = []
        original_prepare = generator.base_template._prepare_arabic

        def tracked_prepare(text, _original=original_prepare, _calls=shape_calls):
            prepared = _original(text)
            if any("\u0600" <= char <= "\u06ff" for char in str(text)):
                _calls.append({"source": str(text), "prepared": str(prepared)})
            return prepared

        generator.base_template._prepare_arabic = tracked_prepare
        generated = Path(
            generator.generate_note(
                patient,
                data,
                facture_number="F-2026-0010",
                db=FakeDB(config, user),
                user_id=1,
            )
        )
        assert len(shape_calls) >= len(HEADER_AR), (template, len(shape_calls))

        target_pdf = PDF_DIR / f"{template}.pdf"
        shutil.copy2(generated, target_pdf)
        doc = fitz.open(target_pdf)
        assert doc.page_count >= 1
        width, height = doc[0].rect.width, doc[0].rect.height
        assert abs(width - 419.5276) < 0.8, (template, width)
        assert abs(height - 595.2756) < 0.8, (template, height)

        page_texts = [_normalize(page.get_text()) for page in doc]
        extracted = _normalize(" ".join(page_texts))
        assert "F-2026-0010" in extracted
        for act, *_ in ACTS:
            assert _normalize(act) in extracted, f"{template}: missing act {act!r}"
        assert "TOTAL GÉNÉRAL" in extracted
        assert "18100.00" in extracted

        # A second page is acceptable only when real table content continues there.
        # An otherwise empty page carrying just the repeated header/footer and closing
        # sentence is a layout regression, not useful pagination.
        if len(page_texts) > 1:
            for page_no, page_text in enumerate(page_texts[1:], start=2):
                acts_on_page = [act for act, *_ in ACTS if _normalize(act) in page_text]
                assert acts_on_page, f"{template}: orphan page {page_no} without accounting rows"

        font_found, font_resources = _embedded_arabic_font(doc, arabic_font_path)
        assert font_found, (template, arabic_font_path, font_resources)

        page_pngs = []
        for page_no, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
            png = PNG_DIR / f"{template}-p{page_no + 1}.png"
            pix.save(png)
            page_pngs.append(str(png))
            rendered.append((f"{LABELS[template]} · page {page_no + 1}", png))
        metrics = _span_metrics(doc)
        doc.close()

        manifest["templates"][template] = {
            "page_count": len(page_pngs),
            "page_size_points": [round(width, 3), round(height, 3)],
            "arabic_font": generator.base_template.arabic_font,
            "arabic_font_path": arabic_font_path,
            "arabic_shape_calls": len(shape_calls),
            "arabic_font_resource_found": font_found,
            "font_resources": font_resources,
            "minimum_span_size": metrics["minimum_span_size"],
            "maximum_span_size": metrics["maximum_span_size"],
            "pdf": str(target_pdf),
            "pngs": page_pngs,
        }
        (ROOT / f"{template}-arabic-shaping.json").write_text(
            json.dumps(shape_calls, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (ROOT / f"{template}-spans.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    _contact_sheet(rendered, ROOT / "contact-sheet.png")
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render synthetic A5 ordonnance vs A4 cephalo PDFs for HUMAN review.

Never labels a visual comparison as clinically approved. Read PDF from isolated
CI artifact folder only, no real patient or external source.
"""
from __future__ import annotations
from pathlib import Path
import fitz
from PIL import Image, ImageDraw, ImageFont

SRC=Path("artifacts/ceph-pdf-v3")
STYLES=("swiss","royal","clinical","modern","heritage")

def render(path, *, zoom=1.2, page=0):
    doc=fitz.open(path)
    pix=doc[page].get_pixmap(matrix=fitz.Matrix(zoom,zoom), alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

def main():
    SRC.mkdir(parents=True, exist_ok=True)
    large=Image.new("RGB",(1250,875),"#eef1f4")
    rows=[]
    for i,style in enumerate(STYLES):
        ordonnance=SRC / f"ordonnance_{style}.pdf"
        bilan=SRC / f"bilan_{style}.pdf"
        if not ordonnance.exists() or not bilan.exists():
            raise FileNotFoundError(f"missing matched pair {style}")
        before=render(ordonnance)
        after=render(bilan)
        tile=Image.new("RGB",(1200,770),"#edf0f4")
        pen=ImageDraw.Draw(tile)
        pen.text((34,18),f"{style.upper()} | SAME CABINET CONFIG | ORDONNANCE (A5) vs BILAN (A4)",fill="#152e42")
        # Two actual PDF pages at native shape, so margins and header are visible.
        ordthumb=before.copy(); ordthumb.thumbnail((485,685))
        bilthumb=after.copy(); bilthumb.thumbnail((485,685))
        tile.paste(ordthumb,(40,55))
        tile.paste(bilthumb,(640,55))
        pen.text((40,744),"A5 — parcours OrdonnanceGenerator",fill="#354d63")
        pen.text((640,744),"A4 — BilanOrthoPDFGenerator",fill="#354d63")
        tile.save(SRC/f"comparaison_{style}.png")
        # Small overview for fast human scanning of all five.
        both=Image.new("RGB",(425,310),"#fff")
        od=ordthumb.copy();od.thumbnail((172,286))
        bd=bilthumb.copy();bd.thumbnail((172,286))
        both.paste(od,(10,19));both.paste(bd,(242,19))
        rows.append((style,both))

    summary=Image.new("RGB",(425*5,340),"#e8ecef")
    p=ImageDraw.Draw(summary)
    for j,(name,pair) in enumerate(rows):
        summary.paste(pair,(j*425,30))
        p.text((j*425+10,7),name.upper(),fill="#183448")
    summary.save(SRC/"comparaison_cinq_modeles.png")

    # A separate view of the final page catches footer-only/orphan problems.
    ends=Image.new("RGB",(485*5,710),"#ebedef")
    p=ImageDraw.Draw(ends)
    for j,name in enumerate(STYLES):
        source=SRC/f"bilan_{name}.pdf"
        doc=fitz.open(source)
        image=render(source,page=len(doc)-1)
        image.thumbnail((470,666))
        ends.paste(image,(j*485+8,33))
        p.text((j*485+8,8),f"{name.upper()} / PAGE {len(doc)} (LAST)",fill="#183448")
    ends.save(SRC/"dernieres_pages_cinq_modeles.png")
    print("V3_VISUAL_PAIRS_GENERATED: five A5/A4 pairs, five last pages, no human sign-off")

if __name__=="__main__":
    main()

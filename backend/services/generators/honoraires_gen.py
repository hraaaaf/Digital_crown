from __future__ import annotations

import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.services.base_template import NAVY_BLUE, PageCounter, PinnedCloture
from backend.services.generators.accounting_gen import AccountingGenerator
from backend.services.generators.accounting_pdf_readability import readable_accounting_font_floor


class HonorairesGenerator(AccountingGenerator):
    """P4 Note Honoraires renderer with fail-closed readability semantics.

    Unlike the historical accounting renderer, this generator never tries to
    rebuild the same consumed ReportLab flowable list to force a single page.
    Long notes are allowed to span pages and table typography never drops below
    the central accounting readability floor.
    """

    def _create_installments_table(self, installments, total_honoraires, p_color):
        if not installments:
            return None

        font_bold = self.base_template.premium_bold
        font_main = self.base_template.premium_font
        readable_floor = readable_accounting_font_floor()

        header_style = ParagraphStyle(
            name="HonorairesInstHeader",
            fontName=font_bold,
            fontSize=max(9, readable_floor),
            textColor=colors.white,
            alignment=TA_CENTER,
        )
        text_style = ParagraphStyle(
            name="HonorairesInstText",
            fontName=font_main,
            fontSize=max(9, readable_floor),
            textColor=p_color,
            alignment=TA_CENTER,
            leading=max(9, readable_floor) * 1.3,
        )

        table_data = [[
            Paragraph("ÉCHÉANCE / AVANCE", header_style),
            Paragraph("DATE", header_style),
            Paragraph("MONTANT (MAD)", header_style),
        ]]

        total_verse = 0.0
        amount_width = 3.2 * cm - 6
        for inst in installments:
            d_str = inst.date.strftime("%d/%m/%Y") if hasattr(inst.date, "strftime") else str(inst.date)
            amount_text = f"{float(inst.amount):.2f}"
            amount_style = self.base_template.get_adaptive_style(
                text_style,
                amount_text,
                amount_width,
                min_fs=readable_floor,
            )
            table_data.append([
                Paragraph(str(inst.label), text_style),
                Paragraph(d_str, text_style),
                Paragraph(amount_text, amount_style),
            ])
            total_verse += float(inst.amount)

        reste = total_honoraires - total_verse
        summary_style = ParagraphStyle(
            name="HonorairesInstSummary",
            fontName=font_bold,
            fontSize=max(10, readable_floor),
            textColor=p_color,
            alignment=TA_RIGHT,
        )
        reste_style = ParagraphStyle(
            name="HonorairesInstReste",
            fontName=font_bold,
            fontSize=max(10, readable_floor),
            textColor=colors.HexColor("#B45309"),
            alignment=TA_CENTER,
        )

        verse_text = f"<b>{total_verse:.2f}\u00A0MAD</b>"
        reste_text = f"<b>{reste:.2f}\u00A0MAD</b>"
        verse_style = self.base_template.get_adaptive_style(
            text_style,
            verse_text,
            amount_width,
            min_fs=readable_floor,
        )
        reste_amount_style = self.base_template.get_adaptive_style(
            reste_style,
            reste_text,
            amount_width,
            min_fs=readable_floor,
        )

        table_data.append([
            Paragraph("TOTAL VERSÉ", summary_style),
            "",
            Paragraph(verse_text, verse_style),
        ])
        table_data.append([
            Paragraph("RESTE À PAYER", summary_style),
            "",
            Paragraph(reste_text, reste_amount_style),
        ])

        table = Table(table_data, colWidths=[5.3 * cm, 3.3 * cm, 3.2 * cm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), p_color),
            ("GRID", (0, 0), (-1, -3), 0.3, p_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("SPAN", (0, -2), (1, -2)),
            ("SPAN", (0, -1), (1, -1)),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FFFBEB")),
            ("BOX", (0, -1), (-1, -1), 0.3, colors.HexColor("#FDE68A")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        return table

    def generate_note(self, patient, data, facture_number=None, db=None, user_id=None, **kwargs):
        filepath = self._get_save_path(patient, "NOTE", data, doc_id=facture_number)
        config = None
        if db and user_id:
            from backend.models import CabinetConfig
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()

        self.base_template.update_active_fonts(config)
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        font_main = self.base_template.premium_font
        font_bold = self.base_template.premium_bold
        readable_floor = readable_accounting_font_floor()

        is_global = bool(getattr(data, "is_global_note", False))
        title_text = "NOTE D'HONORAIRES GLOBALE" if is_global else "NOTE D'HONORAIRES"
        if facture_number:
            title_text += f" N° {facture_number}"

        num_acts = len(data.payments)
        compression_factor = 1.0
        if num_acts > 10:
            compression_factor = 0.75
        elif num_acts > 6:
            compression_factor = 0.85

        title_style = ParagraphStyle(
            name="HonorairesTitleA5",
            parent=self.styles["Normal"],
            fontName=font_bold,
            fontSize=max(17 * compression_factor, readable_floor),
            textColor=p_color,
            alignment=TA_CENTER,
            spaceAfter=12 * compression_factor,
        )
        elements = [
            Spacer(1, 0.4 * cm),
            Paragraph(f"<u><b>{title_text}</b></u>", title_style),
            Spacer(1, 0.8 * cm if num_acts > 8 else 1.0 * cm),
            self._create_header(patient, data, p_color),
            Spacer(1, 1.0 * cm if num_acts > 8 else 1.2 * cm),
        ]

        header_style = ParagraphStyle(
            name="HonorairesTableHeader",
            parent=self.styles["Normal"],
            fontName=font_bold,
            fontSize=max(10 * compression_factor, readable_floor),
            textColor=colors.white,
            alignment=TA_CENTER,
        )
        table_data = [[
            Paragraph("ACTE", header_style),
            Paragraph("DENT", header_style),
            Paragraph("PAIEMENT", header_style),
            Paragraph("HONORAIRES", header_style),
        ]]

        base_fs = max(10 * compression_factor, readable_floor)
        text_style = ParagraphStyle(
            name="HonorairesTableText",
            parent=self.styles["Normal"],
            fontName=font_main,
            fontSize=base_fs,
            textColor=p_color,
            alignment=TA_CENTER,
            leading=base_fs * 1.4,
        )
        acte_style = ParagraphStyle(
            name="HonorairesActeText",
            parent=self.styles["Normal"],
            fontName=font_main,
            fontSize=base_fs,
            textColor=p_color,
            alignment=TA_LEFT,
            leading=base_fs * 1.4,
        )

        total = 0.0
        acte_w, dent_w, pay_w, hon_w = 4.5 * cm, 1.8 * cm, 2.75 * cm, 2.75 * cm
        for payment in data.payments:
            dent_display = getattr(payment, "dent", "-")
            if getattr(payment, "dents", None):
                dent_display = ", ".join(str(value) for value in payment.dents)

            dent_text = str(dent_display)
            mode_text = str(getattr(payment, "mode_reglement", "EN ATTENTE"))
            amount_text = f"{float(payment.montant):.2f}"

            dent_style = self.base_template.get_adaptive_style(
                text_style, dent_text, dent_w - 0.22 * cm, min_fs=readable_floor
            )
            mode_style = self.base_template.get_adaptive_style(
                text_style, mode_text, pay_w - 0.22 * cm, min_fs=readable_floor
            )
            amount_style = self.base_template.get_adaptive_style(
                text_style, amount_text, hon_w - 0.22 * cm, min_fs=readable_floor
            )

            table_data.append([
                Paragraph(str(payment.acte), acte_style),
                Paragraph(dent_text, dent_style),
                Paragraph(mode_text, mode_style),
                Paragraph(amount_text, amount_style),
            ])
            total += float(payment.montant)

        total_words_style = ParagraphStyle(
            name="HonorairesTotalWords",
            parent=self.styles["Normal"],
            fontName=font_bold,
            fontSize=11,
            textColor=p_color,
            alignment=TA_RIGHT,
        )
        total_amount_style = ParagraphStyle(
            name="HonorairesTotalAmount",
            parent=self.styles["Normal"],
            fontName=font_bold,
            fontSize=10.5,
            textColor=p_color,
            alignment=TA_CENTER,
        )
        total_amount_text = f"<b>{total:.2f}\u00A0MAD</b>"
        total_amount_style = self.base_template.get_adaptive_style(
            total_amount_style,
            total_amount_text,
            hon_w - 0.22 * cm,
            min_fs=readable_floor,
        )
        table_data.append([
            Paragraph("<b>TOTAL GÉNÉRAL</b>", total_words_style),
            "",
            "",
            Paragraph(total_amount_text, total_amount_style),
        ])

        table = Table(
            table_data,
            colWidths=[acte_w, dent_w, pay_w, hon_w],
            repeatRows=1,
        )
        v_pad = 8 if num_acts <= 5 else (4 if num_acts <= 8 else 2)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), p_color),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -2), 0.3, p_color),
            ("SPAN", (0, -1), (2, -1)),
            ("ALIGN", (0, -1), (0, -1), "RIGHT"),
            ("TEXTCOLOR", (0, 1), (-1, -1), p_color),
            ("BOTTOMPADDING", (0, 0), (-1, -1), v_pad),
            ("TOPPADDING", (0, 0), (-1, -1), v_pad),
            ("BOTTOMPADDING", (0, -1), (-1, -1), v_pad + 4),
            ("TOPPADDING", (0, -1), (-1, -1), v_pad + 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(table)

        installment_table = self._create_installments_table(
            data.installments if is_global else [],
            total,
            p_color,
        )
        if installment_table:
            elements.append(Spacer(1, 1.2 * cm))
            elements.append(Paragraph(
                "SUIVI DES RÈGLEMENTS",
                ParagraphStyle(
                    "HonorairesInstTitle",
                    fontName=font_bold,
                    fontSize=10,
                    textColor=p_color,
                    spaceAfter=8,
                ),
            ))
            elements.append(installment_table)

        total_words = self._amount_to_words(total)
        total_words_elite = f"<b>{total_words.upper()}</b>"
        template = config.cloture_note_template if config and hasattr(config, "cloture_note_template") else None
        if not template:
            template = "Arrêtée la présente note d'honoraires à la somme de : {total_words} TTC."
        template = template.replace("Arrte", "Arrêté").replace("prsente", "présente")

        import re
        template = re.sub(r",?\s*soit\s+\{total_amount\}.*?(?=\.)", " TTC", template)
        template = template.replace("{total_amount}", "")
        cloture = template.format(
            total_words=total_words_elite,
            total_amount=f"{total:,.2f}".replace(",", " "),
        )
        cloture_style = ParagraphStyle(
            name="HonorairesCloture",
            parent=self.styles["Normal"],
            fontName=font_main,
            fontSize=9.5,
            textColor=p_color,
            alignment=TA_CENTER,
            leading=14,
        )
        elements.append(PinnedCloture(cloture, cloture_style))

        highlighted_teeth = []
        for payment in data.payments:
            if getattr(payment, "dents", None):
                highlighted_teeth.extend(int(value) for value in payment.dents)
            elif getattr(payment, "dent", None) and str(payment.dent).isdigit():
                highlighted_teeth.append(int(payment.dent))

        user_obj = None
        if db and user_id:
            from backend.models import User
            user_obj = db.query(User).filter(User.id == user_id).first()

        return self._build_pdf(
            filepath,
            elements,
            "",
            config=config,
            user=user_obj,
            highlighted_teeth=list(set(highlighted_teeth)),
            doc_id=facture_number,
            p_color=p_color,
        )

    def _build_pdf(
        self,
        filepath,
        elements,
        cloture_text,
        config=None,
        user=None,
        highlighted_teeth=None,
        doc_id=None,
        p_color=None,
    ):
        """Build exactly once and allow natural multipage flow.

        ReportLab consumes the supplied flowable list. Reusing that same list in
        a retry loop can overwrite a valid multipage note with an empty build.
        """
        p_width = A5[0]
        m_top, m_bottom, m_left, m_right = self.base_template.get_document_margins(config, p_width)
        draw_method = lambda canv, doc: self._draw_canvas(
            canv,
            doc,
            config=config,
            user=user,
            highlighted_teeth=highlighted_teeth,
            cloture_text="",
            p_color=p_color,
        )

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A5,
            rightMargin=m_right,
            leftMargin=m_left,
            topMargin=m_top,
            bottomMargin=m_bottom,
        )
        doc.doc_id = doc_id
        doc.qr_type = "PAYMENT"
        page_counter = PageCounter()
        doc.build(
            elements,
            onFirstPage=draw_method,
            onLaterPages=draw_method,
            canvasmaker=page_counter.make_canvas_class(),
        )
        return filepath.replace("\\", "/")

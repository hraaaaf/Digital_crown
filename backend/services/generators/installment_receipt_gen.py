# -*- coding: utf-8 -*-
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from backend.services.base_template import BaseTemplate, NAVY_BLUE, PageCounter

COLOR_PAID       = colors.HexColor('#10B981')
COLOR_CURRENT    = colors.HexColor('#F59E0B')
COLOR_FUTURE     = colors.HexColor('#94A3B8')
COLOR_PAID_BG    = colors.HexColor('#F0FDF4')
COLOR_CURRENT_BG = colors.HexColor('#FFFBEB')


class CheckBox(Flowable):
    """
    Case à cocher dessinée directement au canvas — indépendante de toute police.
    state : 'checked' | 'current' | 'empty'
    """
    SIZE = 10  # points

    def __init__(self, state='empty'):
        super().__init__()
        self.state = state
        self.width  = self.SIZE
        self.height = self.SIZE

    def wrap(self, availW, availH):
        return self.SIZE, self.SIZE

    def draw(self):
        s = self.SIZE
        c = self.canv

        if self.state == 'checked':
            border = COLOR_PAID
            fill   = COLOR_PAID
        elif self.state == 'current':
            border = COLOR_CURRENT
            fill   = colors.white
        else:
            border = COLOR_FUTURE
            fill   = colors.white

        # Carré
        c.setStrokeColor(border)
        c.setFillColor(fill)
        c.setLineWidth(1.2)
        c.roundRect(0, 0, s, s, 1.5, fill=1, stroke=1)

        if self.state == 'checked':
            # Coche blanche
            c.setStrokeColor(colors.white)
            c.setLineWidth(1.8)
            c.setLineCap(1)
            c.setLineJoin(1)
            path = c.beginPath()
            path.moveTo(s * 0.18, s * 0.50)
            path.lineTo(s * 0.42, s * 0.22)
            path.lineTo(s * 0.82, s * 0.72)
            c.drawPath(path, stroke=1, fill=0)

        elif self.state == 'current':
            # Rond amber au centre = "prochain à régler"
            c.setFillColor(COLOR_CURRENT)
            c.circle(s / 2, s / 2, s * 0.28, fill=1, stroke=0)


def generate_installment_receipt(
    patient_name: str,
    title: str,
    total_amount: float,
    items: list,
    output_dir: str,
    config=None,
    user=None,
) -> str:
    """
    Reçu/suivi de paiement A5 avec cases à cocher dessinées :
      ✓ vert   = réglé
      ● amber  = prochaine échéance (à encaisser)
      □ gris   = future
    """
    base = BaseTemplate()
    base.update_active_fonts(config)
    p_color   = colors.HexColor(config.primary_color) if (config and getattr(config, 'primary_color', None)) else NAVY_BLUE
    font_main = base.premium_font
    font_bold = base.premium_bold
    styles    = getSampleStyleSheet()

    os.makedirs(output_dir, exist_ok=True)
    filename = f"Suivi_Paiement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(output_dir, filename)

    # Première échéance non payée = "current"
    first_unpaid_idx = next((i for i, it in enumerate(items) if not it.get('paid')), None)

    # --- Styles typographiques ---
    def ps(name, **kw):
        base_kw = dict(parent=styles['Normal'], fontName=font_main, fontSize=9.5,
                       textColor=p_color, leading=12)
        base_kw.update(kw)
        return ParagraphStyle(name, **base_kw)

    title_style = ps('ITitle', fontName=font_bold, fontSize=16, alignment=TA_CENTER,
                     spaceAfter=4, leading=20)
    sub_style   = ps('ISub',   fontSize=10, textColor=colors.HexColor('#64748B'),
                     alignment=TA_CENTER, spaceAfter=2, leading=13)
    info_style  = ps('IInfo',  fontName=font_bold, fontSize=10, leading=14)
    date_style  = ps('IDate',  fontSize=10, alignment=TA_RIGHT, leading=14)
    th_style    = ps('ITH',    fontName=font_bold, fontSize=9,
                     textColor=colors.white, alignment=TA_CENTER, leading=11)
    cell_style  = ps('ICell',  alignment=TA_LEFT)
    ctr_style   = ps('ICtr',   alignment=TA_CENTER)

    # --- Éléments du document ---
    elements = [
        Spacer(1, 0.3 * cm),
        Paragraph("<u><b>SUIVI DE PAIEMENT</b></u>", title_style),
        Paragraph(title, sub_style),
        Spacer(1, 0.5 * cm),
    ]

    # En-tête patient / date
    hdr_data = [[
        Paragraph(f"Patient : <b>{patient_name}</b>", info_style),
        Paragraph(f"Le : <b>{datetime.now().strftime('%d/%m/%Y')}</b>", date_style),
    ]]
    hdr_tbl = Table(hdr_data, colWidths=[8.5 * cm, 3.5 * cm])
    hdr_tbl.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(hdr_tbl)
    elements.append(Spacer(1, 0.5 * cm))

    # --- Tableau des échéances ---
    # Colonne 0 : case à cocher (CheckBox Flowable)
    table_data = [[
        Paragraph("", th_style),
        Paragraph("Libellé", th_style),
        Paragraph("Date prévue", th_style),
        Paragraph("Montant", th_style),
    ]]

    row_styles = []

    for i, item in enumerate(items):
        row_num    = i + 1
        paid       = item.get('paid', False)
        is_current = (i == first_unpaid_idx)

        if paid:
            state     = 'checked'
            lbl_color = colors.HexColor('#6B7280')
            amt_color = COLOR_PAID
            dte_color = colors.HexColor('#6B7280')
            row_styles.append(('BACKGROUND', (0, row_num), (-1, row_num), COLOR_PAID_BG))
        elif is_current:
            state     = 'current'
            lbl_color = p_color
            amt_color = COLOR_CURRENT
            dte_color = p_color
            row_styles.append(('BACKGROUND', (0, row_num), (-1, row_num), COLOR_CURRENT_BG))
            row_styles.append(('FONTNAME',   (1, row_num), (1, row_num),  font_bold))
        else:
            state     = 'empty'
            lbl_color = colors.HexColor('#94A3B8')
            amt_color = colors.HexColor('#94A3B8')
            dte_color = colors.HexColor('#94A3B8')

        due_raw = item.get('due_date', '')
        try:
            due_fmt = datetime.strptime(due_raw, '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            due_fmt = due_raw

        amount = item.get('amount', 0)
        label  = item.get('label', '')

        lbl_s = ps(f'lbl{i}', textColor=lbl_color, alignment=TA_LEFT)
        amt_s = ps(f'amt{i}', textColor=amt_color, alignment=TA_CENTER,
                   fontName=font_bold if (paid or is_current) else font_main)
        dte_s = ps(f'dte{i}', textColor=dte_color, alignment=TA_CENTER)

        table_data.append([
            CheckBox(state=state),
            Paragraph(label, lbl_s),
            Paragraph(due_fmt, dte_s),
            Paragraph(f"{amount:.2f} MAD", amt_s),
        ])

    # Ligne total réglé
    total_paid      = sum(it.get('amount', 0) for it in items if it.get('paid'))
    total_remaining = (total_amount - total_paid) if total_amount > 0 else \
                      sum(it.get('amount', 0) for it in items if not it.get('paid'))

    ttl_s  = ps('ttl',  fontName=font_bold, textColor=p_color,    alignment=TA_RIGHT)
    pamt_s = ps('pamt', fontName=font_bold, textColor=COLOR_PAID,  alignment=TA_CENTER)

    table_data.append([
        Paragraph("", ctr_style),
        Paragraph("<b>TOTAL RÉGLÉ</b>", ttl_s),
        Paragraph("", ctr_style),
        Paragraph(f"<b>{total_paid:.2f} MAD</b>", pamt_s),
    ])

    col_widths = [0.9 * cm, 5.9 * cm, 2.7 * cm, 2.7 * cm]
    t = Table(table_data, colWidths=col_widths)

    tbl_styles = [
        ('BACKGROUND',  (0, 0),   (-1, 0),  p_color),
        ('VALIGN',      (0, 0),   (-1, -1), 'MIDDLE'),
        ('ALIGN',       (0, 0),   (0, -1),  'CENTER'),
        ('ALIGN',       (2, 0),   (3, -1),  'CENTER'),
        ('GRID',        (0, 0),   (-1, -2), 0.3, colors.HexColor('#E2E8F0')),
        ('LINEABOVE',   (0, -1),  (-1, -1), 1.5, p_color),
        ('TOPPADDING',  (0, 0),   (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0),   (-1, -1), 4),
        ('RIGHTPADDING',(0, 0),   (-1, -1), 4),
    ] + row_styles
    t.setStyle(TableStyle(tbl_styles))
    elements.append(t)

    # Récapitulatif global
    if total_amount > 0:
        elements.append(Spacer(1, 0.4 * cm))
        pct = int(total_paid / total_amount * 100) if total_amount else 0
        recap_s = ps('recap', fontSize=8.5, textColor=colors.HexColor('#64748B'),
                     alignment=TA_CENTER)
        elements.append(Paragraph(
            f"Total traitement : <b>{total_amount:.2f} MAD</b>  |  "
            f"Réglé : <b>{total_paid:.2f} MAD ({pct}%)</b>  |  "
            f"Restant : <b>{total_remaining:.2f} MAD</b>",
            recap_s
        ))

    # --- Build avec header/footer cabinet + Single-Page Force ---
    m_top, m_bottom, m_left, m_right = base.get_document_margins(config, A5[0])
    draw_method = lambda canv, d: base.draw_static_elements(canv, d, config=config, user=user)

    compression = 1.0
    for _ in range(7):
        scaled = BaseTemplate.scale_elements(elements, compression)
        doc = SimpleDocTemplate(filepath, pagesize=A5,
                                rightMargin=m_right, leftMargin=m_left,
                                topMargin=m_top, bottomMargin=m_bottom)
        doc.doc_id   = f"SUIVI-{datetime.now().strftime('%m%H%M')}"
        doc.qr_type  = 'PAYMENT'
        page_counter = PageCounter()
        doc.build(scaled, onFirstPage=draw_method, onLaterPages=draw_method,
                  canvasmaker=page_counter.make_canvas_class())
        if page_counter.page_count <= 1:
            break
        compression *= 0.82
        if compression < 0.35:
            break

    return filepath.replace("\\", "/")

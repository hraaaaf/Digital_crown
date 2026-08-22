import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.models import InstallmentPlan, Patient, CabinetConfig
from backend.services.base_template import BaseTemplate, PageCounter


def _cabinet_contact_lines(config: CabinetConfig) -> list[str]:
    """Projette les contacts canoniques de l'organisation pour le PDF."""
    lines: list[str] = []
    address = (getattr(config, "footer_address", None) or "").strip()
    if address:
        lines.append(escape(address))

    contacts: list[str] = []
    contacts_json = getattr(config, "contacts_json", None)
    if isinstance(contacts_json, dict):
        labels = {"fixe": "Tél", "mobile": "Mob", "whatsapp": "WhatsApp", "instagram": "Insta"}
        for key in ("fixe", "mobile", "whatsapp", "instagram"):
            info = contacts_json.get(key)
            if isinstance(info, dict) and info.get("enabled") and info.get("value"):
                contacts.append(f"{labels[key]}: {escape(str(info['value']).strip())}")

    # footer_phones reste une projection legacy de contacts_json pour les anciennes
    # installations. Il ne redevient jamais une nouvelle source métier.
    if not contacts:
        legacy_projection = (getattr(config, "footer_phones", None) or "").strip()
        if legacy_projection:
            contacts.append(escape(legacy_projection))

    if contacts:
        lines.append(" / ".join(contacts))
    return lines


def generate_installment_plan(
    plan: InstallmentPlan,
    patient: Patient,
    config: CabinetConfig,
    output_dir: str
) -> str:
    """Génère un PDF d'échéancier avec l'identité organisationnelle canonique."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"Echeancier_{patient.nom}_{patient.prenom}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(output_dir, filename)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=20,
        alignment=1
    )

    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.textColor = colors.HexColor('#334155')

    elements = []

    organization_name = (getattr(config, "nom_cabinet", None) or "Cabinet dentaire").strip()
    elements.append(Paragraph(f"<b>{escape(organization_name.upper())}</b>", title_style))
    contact_lines = _cabinet_contact_lines(config)
    if contact_lines:
        elements.append(Paragraph("<br/>".join(contact_lines), normal_style))
    elements.append(Spacer(1, 30))

    elements.append(Paragraph("<b>ÉCHÉANCIER DE PAIEMENT</b>", title_style))
    elements.append(Spacer(1, 20))

    patient_info = [
        ["Patient :", f"{patient.nom} {patient.prenom}"],
        ["Traitement :", plan.title],
        ["Montant Total :", f"{plan.total_amount:.2f} MAD"],
        ["Date :", datetime.now().strftime("%d/%m/%Y")]
    ]
    t_info = Table(patient_info, colWidths=[100, 300])
    t_info.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#334155')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 30))

    data = [["Échéance", "Date Prévue", "Montant (MAD)", "Statut"]]

    for inst in plan.installments:
        status_text = "Payé" if inst.status == "PAYE" else "En Attente"
        date_str = inst.due_date.strftime("%d/%m/%Y")
        data.append([inst.label, date_str, f"{inst.amount:.2f}", status_text])

    t_installments = Table(data, colWidths=[150, 100, 100, 100])
    t_installments.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('TOPPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))

    elements.append(t_installments)
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("<i>Document généré électroniquement par Digital Crown Elite Edition.</i>", normal_style))

    compression = 1.0
    for _ in range(7):
        scaled = BaseTemplate.scale_elements(elements, compression)
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        page_counter = PageCounter()
        doc.build(scaled, canvasmaker=page_counter.make_canvas_class())
        if page_counter.page_count <= 1:
            break
        compression *= 0.82
        if compression < 0.35:
            break

    return filepath

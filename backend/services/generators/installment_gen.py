import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.models import InstallmentPlan, Patient, CabinetConfig

def generate_installment_plan(
    plan: InstallmentPlan, 
    patient: Patient, 
    clinic: CabinetConfig, 
    output_dir: str
) -> str:
    """
    Génère un PDF d'échéancier de paiement de type "Premium".
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"Echeancier_{patient.nom}_{patient.prenom}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=20,
        alignment=1 # Center
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.textColor = colors.HexColor('#334155')

    elements = []

    # En-tête (Clinique)
    elements.append(Paragraph(f"<b>{clinic.name.upper()}</b>", title_style))
    elements.append(Paragraph(f"{clinic.address}<br/>Tél: {clinic.phone}<br/>Email: {clinic.email}", normal_style))
    elements.append(Spacer(1, 30))

    # Titre du document
    elements.append(Paragraph("<b>ÉCHÉANCIER DE PAIEMENT</b>", title_style))
    elements.append(Spacer(1, 20))

    # Informations Patient & Plan
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

    # Tableau des échéances
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

    # Footer
    elements.append(Paragraph("<i>Document généré électroniquement par Digital Crown Elite Edition.</i>", normal_style))

    doc.build(elements)
    
    return filepath

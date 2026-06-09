import logging
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend import models, database

logger = logging.getLogger(__name__)
router = APIRouter(tags=['Verification publique'])
def get_verification_html(title: str, subtitle: str, doc_type: str, patient_name: str, doc_date: str, primary_color: str = "#003380", status_text: str = "Authentique & Signé", status_color: str = "#10b981", is_valid: bool = True, warning_msg: str = "") -> str:
    icon_svg = '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10zM9 11l2 2 4-4" stroke-linecap="round" stroke-linejoin="round"/></svg>' if is_valid else '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10zM12 8v4M12 16h.01" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    gradient_color = "rgba(16, 185, 129, 0.05)" if is_valid else "rgba(239, 68, 68, 0.05)"
    shield_bg = "linear-gradient(135deg, #10b981 0%, #047857 100%)" if is_valid else "linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)"
    shield_shadow = "rgba(16, 185, 129, 0.3)" if is_valid else "rgba(239, 68, 68, 0.3)"
    pulse_bg = "rgba(16, 185, 129, 0.15)" if is_valid else "rgba(239, 68, 68, 0.15)"
    
    warning_html = f'<div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 16px; padding: 12px; margin-top: 20px; font-size: 12px; color: #ef4444; font-weight: 600;">{warning_msg}</div>' if warning_msg else ''

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portail de Vérification de Document Clinique</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;900&family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: {primary_color};
            --accent: {status_color};
        }}
        body {{
            margin: 0;
            padding: 0;
            background: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%);
            color: #f8fafc;
            font-family: 'Outfit', 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow-x: hidden;
        }}
        .container {{
            max-width: 500px;
            width: 90%;
            margin: 20px auto;
            text-align: center;
        }}
        .card {{
            background: rgba(15, 23, 42, 0.45);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 40px;
            padding: 40px;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
            animation: slideIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        .card::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, {gradient_color} 0%, transparent 60%);
            pointer-events: none;
        }}
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .shield-container {{
            width: 100px;
            height: 100px;
            margin: 0 auto 30px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .pulse-ring {{
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: {pulse_bg};
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0% {{ transform: scale(0.9); opacity: 1; }}
            100% {{ transform: scale(1.4); opacity: 0; }}
        }}
        .shield {{
            width: 70px;
            height: 70px;
            background: {shield_bg};
            border-radius: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 10px 25px {shield_shadow};
            position: relative;
            z-index: 10;
        }}
        .shield svg {{
            width: 32px;
            height: 32px;
            fill: none;
            stroke: white;
            stroke-width: 2.5;
        }}
        h1 {{
            font-size: 26px;
            font-weight: 900;
            margin: 0 0 8px;
            background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .subtitle {{
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            color: var(--primary);
            margin-bottom: 30px;
        }}
        .details-list {{
            text-align: left;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 24px;
            padding: 24px;
            margin-bottom: 30px;
        }}
        .detail-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 13px;
        }}
        .detail-item:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 10px;
            letter-spacing: 0.1em;
        }}
        .detail-val {{
            color: #f1f5f9;
            font-weight: 600;
        }}
        .footer-brand {{
            margin-top: 40px;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.3em;
            color: #475569;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .footer-brand svg {{
            width: 14px;
            height: 14px;
            stroke: #475569;
            stroke-width: 2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="shield-container">
                <div class="pulse-ring"></div>
                <div class="shield">
                    {icon_svg}
                </div>
            </div>
            <h1>{title}</h1>
            <div class="subtitle">{subtitle}</div>
            
            <div class="details-list">
                <div class="detail-item">
                    <span class="detail-label">Type</span>
                    <span class="detail-val">{doc_type}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Patient</span>
                    <span class="detail-val">{patient_name}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Date d'Émission</span>
                    <span class="detail-val">{doc_date}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Statut</span>
                    <span class="detail-val" style="color: {status_color};">{status_text}</span>
                </div>
            </div>
            
            {warning_html}
            
            <div class="footer-brand">
                <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                Digital Crown Elite v4.6
            </div>
        </div>
    </div>
</body>
</html>"""


@router.get("/verify/{public_id}/{document_type}", response_class=HTMLResponse)
def verify_special_document(public_id: str, document_type: str, db: Session = Depends(database.get_db)):
    config = db.query(models.CabinetConfig).first()
    p_color = config.primary_color if config else "#003380"
    cabinet_name = config.nom_cabinet if config else "Cabinet Digital Crown"
    
    try:
        if document_type == "RADIO":
            # C'est un rapport radio ou une analyse
            analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == int(public_id)).first()
            if not analysis:
                analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == int(public_id)).first()
            
            if analysis:
                patient = db.query(models.Patient).filter(models.Patient.id == analysis.patient_id).first()
                p_name = f"{patient.nom.upper()} {patient.prenom[0]}." if patient else "PATIENT INCONNU"
                doc_date = analysis.created_at.strftime("%d/%m/%Y à %H:%M")
                return HTMLResponse(content=get_verification_html(
                    title="Rapport Radiographique Certifié",
                    subtitle=cabinet_name,
                    doc_type="IMAGERIE / RADIO DENTEX IA",
                    patient_name=p_name,
                    doc_date=doc_date,
                    primary_color=p_color
                ))
        
        elif document_type == "BILAN":
            patient = db.query(models.Patient).filter(models.Patient.id == int(public_id)).first()
            if patient:
                p_name = f"{patient.nom.upper()} {patient.prenom[0]}."
                doc_date = patient.created_at.strftime("%d/%m/%Y")
                return HTMLResponse(content=get_verification_html(
                    title="Bilan Orthodontique Certifié",
                    subtitle=cabinet_name,
                    doc_type="DOSSIER & BILAN CLINIQUE",
                    patient_name=p_name,
                    doc_date=doc_date,
                    primary_color=p_color
                ))
    except Exception as e:
        logger.error(f"Error verifying special document: {str(e)}")
        
    return HTMLResponse(content=get_verification_html(
        title="Document Introuvable",
        subtitle="Erreur de Sécurité",
        doc_type="INCONNU",
        patient_name="NON DISPONIBLE",
        doc_date="NON SPÉCIFIÉE",
        primary_color="#ef4444",
        status_text="Non Certifié / Invalide",
        status_color="#ef4444",
        is_valid=False,
        warning_msg="Ce document n'a pas été authentifié par notre plateforme. Il s'agit potentiellement d'un document falsifié ou expiré."
    ))

@router.get("/verify/{doc_id}", response_class=HTMLResponse)
def verify_document(doc_id: str, db: Session = Depends(database.get_db)):
    config = db.query(models.CabinetConfig).first()
    p_color = config.primary_color if config else "#003380"
    cabinet_name = config.nom_cabinet if config else "Cabinet Digital Crown"
    
    try:
        # Recherche par ID ou nom de fichier
        doc = None
        if doc_id.isdigit():
            doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == int(doc_id)).first()
        if not doc:
            doc = db.query(models.DocumentArchive).filter(
                or_(
                    models.DocumentArchive.filename.contains(doc_id),
                    models.DocumentArchive.original_filename.contains(doc_id)
                )
            ).first()
            
        if doc:
            patient = db.query(models.Patient).filter(models.Patient.id == doc.patient_id).first()
            p_name = f"{patient.nom.upper()} {patient.prenom[0]}." if patient else "PATIENT INCONNU"
            doc_date = doc.created_at.strftime("%d/%m/%Y à %H:%M")
            return HTMLResponse(content=get_verification_html(
                title="Document Médical Certifié",
                subtitle=cabinet_name,
                doc_type=doc.document_type.value,
                patient_name=p_name,
                doc_date=doc_date,
                primary_color=p_color
            ))
    except Exception as e:
        logger.error(f"Error verifying document: {str(e)}")
        
    return HTMLResponse(content=get_verification_html(
        title="Document Introuvable",
        subtitle="Erreur de Sécurité",
        doc_type="INCONNU",
        patient_name="NON DISPONIBLE",
        doc_date="NON SPÉCIFIÉE",
        primary_color="#ef4444",
        status_text="Non Certifié / Invalide",
        status_color="#ef4444",
        is_valid=False,
        warning_msg="Ce document n'a pas été authentifié par notre plateforme. Il s'agit potentiellement d'un document falsifié ou expiré."
    ))

@router.get("/track/{doc_id}", response_class=HTMLResponse)
def track_document(doc_id: str, db: Session = Depends(database.get_db)):
    config = db.query(models.CabinetConfig).first()
    p_color = config.primary_color if config else "#003380"
    cabinet_name = config.nom_cabinet if config else "Cabinet Digital Crown"
    
    try:
        doc = None
        if doc_id.isdigit():
            doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == int(doc_id)).first()
        if not doc:
            doc = db.query(models.DocumentArchive).filter(
                or_(
                    models.DocumentArchive.filename.contains(doc_id),
                    models.DocumentArchive.original_filename.contains(doc_id)
                )
            ).first()
            
        if doc:
            patient = db.query(models.Patient).filter(models.Patient.id == doc.patient_id).first()
            p_name = f"{patient.nom.upper()} {patient.prenom[0]}." if patient else "PATIENT INCONNU"
            doc_date = doc.created_at.strftime("%d/%m/%Y à %H:%M")
            
            p_status = doc.payment_status.value if doc.payment_status else "NON DÉFINI"
            p_color_map = {
                "PAYE": "#10b981",
                "PARTIEL": "#f59e0b",
                "EN_ATTENTE": "#94a3b8",
                "A_ENCAISSER": "#3b82f6"
            }
            status_color = p_color_map.get(doc.payment_status.name if hasattr(doc.payment_status, 'name') else doc.payment_status, "#10b981")
            
            return HTMLResponse(content=get_verification_html(
                title="Suivi de Dossier Trésorerie",
                subtitle=cabinet_name,
                doc_type=f"HONORAIRES / {doc.document_type.value}",
                patient_name=p_name,
                doc_date=doc_date,
                primary_color=p_color,
                status_text=f"Statut Réglement : {p_status}",
                status_color=status_color
            ))
    except Exception as e:
        logger.error(f"Error tracking document: {str(e)}")
        
    return HTMLResponse(content=get_verification_html(
        title="Dossier Introuvable",
        subtitle="Erreur de Sécurité",
        doc_type="INCONNU",
        patient_name="NON DISPONIBLE",
        doc_date="NON SPÉCIFIÉE",
        primary_color="#ef4444",
        status_text="Non Référencé / Invalide",
        status_color="#ef4444",
        is_valid=False,
        warning_msg="Ce dossier de suivi de trésorerie n'a pas été authentifié par notre plateforme. Il s'agit potentiellement d'un dossier inexistant ou archivé."
    ))


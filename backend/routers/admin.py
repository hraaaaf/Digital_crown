from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text, desc
from typing import List, Optional, Dict
from datetime import datetime
import os
import subprocess
import logging

from backend import models, schemas, database
from backend.routers.auth import get_current_user, require_permission
from backend.services.zka_service import zka_service
from backend.services.sync_manager import sync_manager
from backend.services.qr_service import QRService
from backend.services.audit_service import audit_service
from backend.env_loader import current_backend_env_path
import qrcode
import io
import base64

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Admin & Dashboard"])

@router.get("/normalize-docs")
def normalize_docs(db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("admin"))):
    """Normalise les types de documents en DB."""
    try:
        db.execute(text("UPDATE document_archives SET document_type = 'NOTE_HONORAIRES' WHERE document_type::text IN ('note_honoraires', 'note_honoraire', 'NOTE_HONORAIRE');"))
        db.execute(text("UPDATE document_archives SET document_type = 'RAPPORT_CEPHALO' WHERE document_type::text IN ('bilan', 'BILAN', 'rapport_cephalo');"))
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("admin"))
):
    """Retourne les logs d'audit avec pagination et filtres."""
    # S8 : isolation multi-tenant STRICTE. Un admin ne voit QUE les logs de son
    # propre cabinet. Sans ce filtre, un admin du cabinet A lisait les IDs patients,
    # emails, IP et détails (incluant des noms) de TOUS les cabinets = fuite RGPD.
    query = db.query(models.AuditLog).filter(
        models.AuditLog.employer_id == current_user.get_employer_id()
    )
    if action:
        query = query.filter(models.AuditLog.action == action)
    if resource_type:
        query = query.filter(models.AuditLog.resource_type == resource_type)
    if severity:
        query = query.filter(models.AuditLog.severity == severity)
    total = query.count()
    logs = query.order_by(desc(models.AuditLog.timestamp)).offset(offset).limit(limit).all()
    return {
        "total": total,
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "user_id": log.user_id,
                "employer_id": log.employer_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "severity": log.severity,
                "ip_address": log.ip_address,
                "details": log.details,
            }
            for log in logs
        ],
    }


@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    emp_id = current_user.get_employer_id()
    
    total_p = db.query(models.Patient).filter(models.Patient.employer_id == emp_id).count()
    total_a = db.query(models.CephaloAnalysis).join(models.Patient).filter(models.Patient.employer_id == emp_id).count()
    db_recent = db.query(models.Patient).filter(
        models.Patient.employer_id == emp_id
    ).options(
        joinedload(models.Patient.actes)
    ).order_by(
        models.Patient.created_at.desc()
    ).limit(5).all()
    
    # Calcul de l'activité sur les 7 derniers jours
    weekly_activity = []
    weekly_patient_counts = []
    from datetime import timedelta
    for i in range(6, -1, -1):
        day = datetime.now().date() - timedelta(days=i)
        count = db.query(models.Patient).filter(
            models.Patient.employer_id == emp_id,
            func.date(models.Patient.created_at) == day
        ).count()
        # weekly_activity : pourcentage normalisé pour le mini-graphique (max 100%, plancher
        # 5% de style visuel). weekly_patient_counts : le compte brut, pour ne jamais avoir
        # à ré-inverser la normalisation côté frontend (audit fonctionnel 2026-07-12 —
        # l'ancienne formule inverse (val-5)/10 fabriquait un chiffre faux dès count >= 10).
        weekly_activity.append(max(5, min(100, count * 10)))
        weekly_patient_counts.append(count)

    recent_list = []
    for p in db_recent:
        last_acte = p.actes[-1] if p.actes else None
        recent_list.append({
            "id": p.id, "nom": (p.nom or "").upper(), "prenom": (p.prenom or "").capitalize(),
            "acte": last_acte.libelle if last_acte else "Consultation",
            "time": "Récent", "type": last_acte.type_acte.value if last_acte else "Ortho"
        })
    in_waiting = db.query(models.Appointment).filter(
        models.Appointment.employer_id == emp_id,
        models.Appointment.status == 'EN_S_ATTENTE'
    ).count()

    from datetime import timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    weekly_p = db.query(models.Patient).filter(
        models.Patient.employer_id == emp_id,
        models.Patient.created_at >= seven_days_ago
    ).count()

    # Pending team approval requests (only relevant for employer accounts)
    pending_team = db.query(models.User).filter(
        models.User.employer_id == emp_id,
        models.User.approval_status == "pending",
    ).count()

    # Team quota snapshot for dashboard notifications
    from backend.routers.team import PLAN_QUOTAS, _get_plan, _count_team
    owner = db.query(models.User).filter(models.User.id == emp_id).first()
    team_quota = None
    if owner:
        plan = _get_plan(owner)
        limits = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["GOLD"])
        counts = _count_team(db, emp_id)
        dentistes_used = counts["dentistes"] + 1
        team_quota = {
            "plan": plan,
            "dentistes_used": dentistes_used,
            "dentistes_max": limits["dentistes"],
            "secretaires_used": counts["secretaires"],
            "secretaires_max": limits["secretaires"],
            "upgrade_required": dentistes_used >= limits["dentistes"] or counts["secretaires"] >= limits["secretaires"],
        }

    return {
        "total_patients": total_p,
        "total_analyses": total_a,
        "recent_patients": recent_list,
        "weekly_activity": weekly_activity,
        "weekly_patient_counts": weekly_patient_counts,
        "in_waiting": in_waiting,
        "weekly_patients": weekly_p,
        "pending_team_requests": pending_team,
        "team_quota": team_quota,
    }


@router.get("/cabinet/me", response_model=schemas.PraticienProfileOut)
def get_cabinet_info(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    emp_id = current_user.get_employer_id()
    praticien = db.query(models.User).filter(models.User.id == emp_id).first()
    
    if not praticien: raise HTTPException(status_code=404, detail="Cabinet introuvable")
    
    # Injection des alias et données de config pour le frontend
    praticien.nom = praticien.nom_complet
    praticien.adresse = praticien.adresse_complete
    praticien.telephone = praticien.telephone_fixe
    praticien.inpe = (praticien.identifiants_legaux or {}).get("INPE", "")
    
    if praticien.cabinet_config:
        praticien.header_lines_fr = praticien.cabinet_config.header_lines_fr
        praticien.header_lines_ar = praticien.cabinet_config.header_lines_ar
        praticien.specialty_ids = praticien.cabinet_config.specialty_ids
        
    return praticien

@router.put("/cabinet/me", response_model=schemas.PraticienProfileOut)
def update_cabinet_info(settings: Dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("admin"))):
    emp_id = current_user.get_employer_id()
    praticien = db.query(models.User).filter(models.User.id == emp_id).first()
    
    if not praticien: raise HTTPException(status_code=404, detail="Cabinet introuvable")
    
    config = praticien.cabinet_config
    
    for key, value in settings.items():
        if key == "nom": praticien.nom_complet = value
        elif key == "adresse": praticien.adresse_complete = value
        elif key == "telephone": praticien.telephone_fixe = value
        elif key == "inpe":
            legaux = dict(praticien.identifiants_legaux or {})
            legaux["INPE"] = value
            praticien.identifiants_legaux = legaux
        elif hasattr(praticien, key): 
            setattr(praticien, key, value)
        
        # Sync with CabinetConfig if exists
        if config and hasattr(config, key):
            setattr(config, key, value)
            
    db.commit(); db.refresh(praticien)
    
    # Re-inject for response
    praticien.nom = praticien.nom_complet
    praticien.adresse = praticien.adresse_complete
    praticien.telephone = praticien.telephone_fixe
    if config:
        praticien.header_lines_fr = config.header_lines_fr
        praticien.header_lines_ar = config.header_lines_ar
        praticien.specialty_ids = config.specialty_ids
        
    return praticien



@router.get("/export-db")
def export_database(db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("admin"))):
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    # S8 : l'export complet de la base est l'opération la plus sensible de l'app
    # (exfiltration potentielle de toutes les données patients). Traçabilité CRITICAL.
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action="EXPORT_DB",
        resource_type="Database",
        resource_id=None,
        severity="CRITICAL",
        details=f"Export complet de la base déclenché ({now_str}).",
    )
    db_url = str(database.engine.url)
    if "sqlite" in db_url:
        db_path = db_url.replace("sqlite:///", "")
        return FileResponse(path=db_path, filename=f"backup_{now_str}.db")
    elif "postgresql" in db_url:
        dump_path = os.path.join(os.getcwd(), "static", "backups", f"backup_{now_str}.sql")
        os.makedirs(os.path.dirname(dump_path), exist_ok=True)
        url = database.engine.url
        env = os.environ.copy()
        if url.password: env['PGPASSWORD'] = url.password
        subprocess.run(["pg_dump", "-h", url.host or "localhost", "-U", url.username or "postgres", "-f", dump_path, url.database], env=env, check=True)
        return FileResponse(path=dump_path, filename=f"backup_{now_str}.sql")
    raise HTTPException(status_code=400, detail="Moteur non supporté")


@router.get("/zka-key-qr")
def get_zka_key_qr(db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("admin"))):
    """
    Génère un QR d'appairage mobile ZKA sécurisé.
    La masterKey NE transite PAS dans l'URL — le QR encode un token éphémère UUID (TTL 5 min).
    Le mobile échange ce token contre les credentials via POST /api/mobile/claim-token.
    """
    import uuid
    from datetime import timedelta

    emp_id = current_user.get_employer_id()

    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == emp_id).first()
    master_key = os.getenv("CABINET_MASTER_KEY_HEX")

    if not config or not master_key:
        raise HTTPException(status_code=404, detail="Configuration ZKA incomplète.")

    # Purger les tokens expirés de cet employeur (nettoyage passif)
    db.query(models.ZKAPairingToken).filter(
        models.ZKAPairingToken.employer_id == emp_id,
        models.ZKAPairingToken.expires_at < datetime.utcnow(),
    ).delete()

    # Générer un token éphémère à usage unique (5 min) - Code à 6 chiffres
    import random
    pairing_token = f"{random.randint(100000, 999999)}"
    db.add(models.ZKAPairingToken(
        token=pairing_token,
        employer_id=emp_id,
        public_id=config.public_id,
        master_key=master_key,
        role=current_user.role.value if current_user.role else "DENTISTE",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    ))
    db.commit()

    # S8 : l'émission d'un token d'appairage ouvre un accès mobile au cabinet.
    # Traçabilité sécurité (qui a généré un accès, quand).
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=emp_id,
        action="MOBILE_PAIRING_TOKEN_ISSUED",
        resource_type="ZKAPairingToken",
        resource_id=None,
        severity="WARNING",
        details="Token d'appairage mobile ZKA généré (TTL 5 min).",
    )

    # Le QR encode l'URL LAN du serveur avec le token — jamais la clé
    from backend.routers.mobile import get_lan_base_url
    base_url = get_lan_base_url()
    qr_payload = f"{base_url}/mobile/onboarding?token={pairing_token}"

    try:
        qr_bytes = QRService.generate_qr_bytes(
            qr_payload,
            color="#4F46E5",
            box_size=10,
            add_logo=False,
            qr_style="classic",
        )
        img_str = base64.b64encode(qr_bytes.getvalue()).decode()
        return {
            "qr_code": f"data:image/png;base64,{img_str}",
            "expires_in": 300,
            "lan_url": base_url,
            "token_code": pairing_token,
        }
    except Exception as e:
        logger.error(f"Erreur génération QR ZKA: {e}")
        raise HTTPException(status_code=500, detail="Échec de génération du QR Code.")


@router.post("/revoke-mobile")
def revoke_mobile_access(db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("admin"))):
    """Révoque l'accès mobile en changeant la clé maître et en forçant une synchro."""
    try:
        emp_id = current_user.get_employer_id()
        env_path = current_backend_env_path()
        
        # 1. Rotation de la clé (mémoire + fichier env actif)
        new_key = zka_service.rotate_master_key(env_path)
        
        # 2. Force une synchronisation immédiate avec la nouvelle clé
        # Cela rendra les anciens snapshots sur Supabase obsolètes ou illisibles avec l'ancienne clé
        sync_manager._perform_sync(emp_id)

        logger.info(f"🚨 Accès mobile révoqué par l'utilisateur {current_user.id}")
        # S8 : rotation de la clé maître = invalidation de tous les accès mobiles.
        # Opération de sécurité majeure, traçabilité CRITICAL.
        audit_service.log(
            db=db,
            user_id=current_user.id,
            employer_id=emp_id,
            action="MOBILE_ACCESS_REVOKED",
            resource_type="ZKAMasterKey",
            resource_id=None,
            severity="CRITICAL",
            details="Rotation de la clé maître ZKA — tous les accès mobiles révoqués.",
        )
        return {"status": "success", "message": "Accès mobile révoqué. Scannez le nouveau code pour vous reconnecter."}
    except Exception as e:
        logger.error(f"Erreur lors de la révocation ZKA: {e}")
        raise HTTPException(status_code=500, detail="Échec de la révocation")

@router.get("/backups")
def list_backups(current_user: models.User = Depends(require_permission("admin"))):
    """Liste les sauvegardes chiffrées existantes."""
    from backend.core.paths import AppPaths
    import os
    from datetime import datetime

    backups_dir = AppPaths.get_user_data_dir() / "backups"
    if not backups_dir.exists():
        return []

    backups = []
    for f in os.listdir(backups_dir):
        if f.endswith(".enc"):
            path = backups_dir / f
            stat = path.stat()
            backups.append({
                "filename": f,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
            
    return sorted(backups, key=lambda x: x["created_at"], reverse=True)

@router.post("/backups/trigger")
def trigger_backup(current_user: models.User = Depends(require_permission("admin"))):
    """Déclenche manuellement une sauvegarde chiffrée de la base de données."""
    from backend.services.backup_service import backup_service
    
    success = backup_service.run_daily_backup()
    if success:
        return {"status": "success", "message": "Sauvegarde chiffrée générée avec succès."}
    else:
        raise HTTPException(status_code=500, detail="Échec de la sauvegarde chiffrée.")

@router.get("/backups/download/{filename}")
def download_backup(filename: str, current_user: models.User = Depends(require_permission("admin"))):
    """Télécharge un fichier de sauvegarde."""
    from backend.core.paths import AppPaths
    from fastapi.responses import FileResponse
    import os
    
    if not filename.endswith(".enc"):
        raise HTTPException(status_code=400, detail="Fichier invalide.")
        
    backups_dir = AppPaths.get_user_data_dir() / "backups"
    file_path = backups_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable.")

    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")


_HEALTH_SEVERITY_RANK = {"ok": 0, "warning": 1, "unknown": 1, "none": 2, "critical": 2}


@router.get("/cabinet-health")
def get_cabinet_health(current_user: models.User = Depends(require_permission("admin"))):
    """Widget santé cabinet — DB, espace disque, backup local, backup hors-site.

    Lit le manifeste du backup planifié réel (tâche Windows programmée), jamais le
    dossier des backups manuels (/backups ci-dessus, DB seule) — seul le backup
    planifié (DB+médias ensemble) est un backup complet au sens de la doctrine
    (voir CLAUDE.md, SCHEDULED-TASK-BACKUP-REPLACE-1).
    """
    import json
    import shutil
    from pathlib import Path

    # --- Base de données ---
    database_section = {"status": "ok", "detail": None}
    try:
        with database.SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as e:
        database_section = {"status": "error", "detail": str(e)}

    # --- Espace disque (même résolution de RUNTIME_ROOT que scheduled_backup.py,
    # dupliquée volontairement plutôt qu'importée -- voir plan) ---
    runtime_root = Path(os.environ.get("DIGITALCROWN_RUNTIME_ROOT", r"C:\Users\lenovo\DigitalCrown-Runtime"))
    disk_warning_gb = float(os.environ.get("HEALTH_DISK_WARNING_GB", "20"))
    disk_critical_gb = float(os.environ.get("HEALTH_DISK_CRITICAL_GB", "5"))
    disk_section = {"status": "unknown", "free_gb": None, "total_gb": None}
    try:
        probe_path = runtime_root if runtime_root.exists() else Path(runtime_root.anchor or "C:\\")
        usage = shutil.disk_usage(probe_path)
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        if free_gb < disk_critical_gb:
            disk_status = "critical"
        elif free_gb < disk_warning_gb:
            disk_status = "warning"
        else:
            disk_status = "ok"
        disk_section = {"status": disk_status, "free_gb": round(free_gb, 1), "total_gb": round(total_gb, 1)}
    except Exception as e:
        logger.warning(f"Cabinet health : échec lecture espace disque ({type(e).__name__}).")

    # --- Backup local + hors-site (manifeste du backup planifié) ---
    backup_warning_hours = float(os.environ.get("HEALTH_BACKUP_WARNING_HOURS", "30"))
    backup_critical_hours = float(os.environ.get("HEALTH_BACKUP_CRITICAL_HOURS", "48"))
    backup_local_section = {"status": "none", "overall_status": None, "age_hours": None, "run_id": None}
    offsite_section = {"status": "NOT_CONFIGURED", "offsite_status": None, "db_copied": None, "media_copied": None}
    manifest_path = runtime_root / "backups" / "scheduled" / "manifests" / "latest.json"
    try:
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            age_hours = None
            completed_at = manifest.get("completed_at")
            if completed_at:
                completed_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                now = datetime.now(completed_dt.tzinfo) if completed_dt.tzinfo else datetime.utcnow()
                age_hours = (now - completed_dt).total_seconds() / 3600

            overall = manifest.get("overall_status")
            if overall not in ("SUCCESS", "PARTIAL") or age_hours is None:
                backup_status = "critical"
            elif age_hours > backup_critical_hours:
                backup_status = "critical"
            elif age_hours > backup_warning_hours or overall == "PARTIAL":
                backup_status = "warning"
            else:
                backup_status = "ok"

            backup_local_section = {
                "status": backup_status,
                "overall_status": overall,
                "age_hours": round(age_hours, 1) if age_hours is not None else None,
                "run_id": manifest.get("run_id"),
            }

            # Doctrine verrouillée : un souci hors-site n'a jamais l'air aussi grave
            # qu'un vrai problème DB/backup local pour un propriétaire non technique.
            offsite_status_raw = manifest.get("offsite_status")
            if offsite_status_raw in (None, "NOT_CONFIGURED"):
                offsite_widget_status = "NOT_CONFIGURED"
            elif offsite_status_raw == "SUCCESS":
                offsite_widget_status = "ok"
            else:
                offsite_widget_status = "warning"
            offsite_section = {
                "status": offsite_widget_status,
                "offsite_status": offsite_status_raw,
                "db_copied": manifest.get("offsite_db_copied"),
                "media_copied": manifest.get("offsite_media_copied"),
            }
    except Exception as e:
        logger.warning(f"Cabinet health : échec lecture manifeste backup ({type(e).__name__}).")

    overall_rank = max(
        _HEALTH_SEVERITY_RANK["critical" if database_section["status"] == "error" else "ok"],
        _HEALTH_SEVERITY_RANK[disk_section["status"]],
        _HEALTH_SEVERITY_RANK[backup_local_section["status"]],
    )
    overall_severity = {0: "ok", 1: "warning", 2: "critical"}[overall_rank]

    return {
        "database": database_section,
        "disk": disk_section,
        "backup_local": backup_local_section,
        "offsite": offsite_section,
        "overall_severity": overall_severity,
    }

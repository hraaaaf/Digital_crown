import logging
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from backend import models

logger = logging.getLogger("audit")

class AuditService:
    @staticmethod
    def log(
        db: Session,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        severity: str = "INFO",
        employer_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ):
        """
        Enregistre une action dans les logs systeme et en base de donnees.
        """
        # 1. Log fichier (Standard)
        timestamp = datetime.now().isoformat()
        log_msg = f"[{timestamp}] [{severity}] User:{user_id} | Action:{action} | Resource:{resource_type}:{resource_id} | Details:{details}"
        
        if severity == "CRITICAL":
            logger.critical(log_msg)
        elif severity == "WARNING":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
            
        # 2. Persistance BDD
        try:
            audit_entry = models.AuditLog(
                user_id=user_id,
                employer_id=employer_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                severity=severity,
                details=details,
                ip_address=ip_address
            )
            db.add(audit_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Echec de la persistance de l'audit log : {e}")
            db.rollback()

audit_service = AuditService()

from fastapi import HTTPException
from backend import models

from backend.services.audit_service import audit_service

def assert_patient_access(patient_id: int, current_user: models.User, db) -> None:
    """Raise 403 if the current user is not allowed to access the patient.
    Admins have full access. For other roles, ensure the patient belongs to the
    practitioner's cabinet."""
    if current_user.role == models.UserRole.ADMIN:
        return
        
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")
    
    # Check against the root employer ID (for multi-tenant cabinets)
    user_employer_id = current_user.get_employer_id()
    if patient.employer_id != user_employer_id:
        audit_service.log(
            db=db,
            user_id=current_user.id,
            employer_id=user_employer_id,
            action="ACCESS_DENIED",
            resource_type="Patient",
            resource_id=str(patient_id),
            severity="WARNING",
            details=f"Tentative d'accès au patient {patient_id} appartenant à l'employeur {patient.employer_id}"
        )
        raise HTTPException(status_code=403, detail="Accès refusé")

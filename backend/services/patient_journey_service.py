"""
Treatment Journey — agrégation en lecture seule du parcours patient.

Fusionne 9 sources indépendantes (Appointment, TreatmentPlanStep, DocumentArchive,
PanoramicAnalysis, CephaloAnalysis, Payment, Installment, LabJob, JourneyMilestone) en un
flux chronologique unique, sans jamais dupliquer la donnée : chaque table source reste la
seule vérité, ce module ne fait que lire et normaliser.

`Acte` est délibérément exclu (voir docs/TREATMENT_JOURNEY_DESIGN.md / STATE.md) : sur la
DB cabinet réelle, la table ne couvre que ~13% des patients et porte la signature de
données de seed — le vrai flux de facturation passe par Payment/DocumentArchive.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from backend import models, schemas

logger = logging.getLogger(__name__)

WINDOW_MONTHS = 12
FULL_HISTORY_CAP = 500
RELATED_REPORT_WINDOW_MINUTES = 5

_NEXT_APPOINTMENT_STATUSES = [
    models.AppointmentStatus.PREVU,
    models.AppointmentStatus.EN_SALLE_ATTENTE,
    models.AppointmentStatus.EN_FAUTEUIL,
    models.AppointmentStatus.CONFIRME,
]


def _parse_step_date(date_str: Optional[str], fallback: datetime) -> datetime:
    """TreatmentPlanStep.date_str est une string libre ("Aujourd'hui" par défaut),
    pas un DateTime — best-effort, retombe sur `fallback` (updated_at du plan) si non parseable."""
    if not date_str:
        return fallback
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return fallback


def _event(event_key, source, type_, ref_id, date, title, status, phase_hint,
           navigation_target, related_event_key=None) -> schemas.JourneyEventResponse:
    return schemas.JourneyEventResponse(
        event_key=event_key, source=source, type=type_, ref_id=ref_id, date=date,
        title=title, status=str(status), phase_hint=phase_hint,
        navigation_target=navigation_target, related_event_key=related_event_key,
    )


def _collect_events(db: Session, patient_id: int, since: Optional[datetime]) -> list:
    events = []

    # 1. Appointment (status=TERMINE) — événements passés de la timeline
    appt_q = db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id,
        models.Appointment.status == models.AppointmentStatus.TERMINE,
    )
    if since is not None:
        appt_q = appt_q.filter(models.Appointment.datetime_start >= since)
    for a in appt_q.all():
        events.append(_event(
            f"appointment:{a.id}", "appointment", "consultation", a.id, a.datetime_start,
            a.motif or "Consultation", a.status.value, "consultation",
            schemas.NavigationTarget.INLINE,
        ))

    # 2. TreatmentPlanStep (via TreatmentMasterPlan) — toujours inclus si PENDING (item ouvert)
    steps_q = (
        db.query(models.TreatmentPlanStep)
        .join(models.TreatmentMasterPlan, models.TreatmentPlanStep.plan_id == models.TreatmentMasterPlan.id)
        .filter(models.TreatmentMasterPlan.patient_id == patient_id)
        .options(joinedload(models.TreatmentPlanStep.master_plan))
    )
    for s in steps_q.all():
        step_date = _parse_step_date(s.date_str, s.master_plan.updated_at)
        is_open = s.status == models.PlanStatus.PENDING
        if since is not None and step_date < since and not is_open:
            continue
        events.append(_event(
            f"treatment_plan_step:{s.id}", "treatment_plan_step", "plan_step", s.id, step_date,
            s.title, s.status.value, "plan",
            schemas.NavigationTarget.TREATMENT_PLAN_TAB,
        ))

    # 3. DocumentArchive (tous types actifs, dernière version uniquement)
    docs_q = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        models.DocumentArchive.is_latest_version.is_(True),
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
        models.DocumentArchive.deleted_at.is_(None),
    )
    if since is not None:
        docs_q = docs_q.filter(models.DocumentArchive.created_at >= since)
    doc_type_to_phase = {
        "DEVIS": "devis",
        "NOTE_HONORAIRES": "prestation",
        "ORDONNANCE": "ordonnance",
        "CERTIFICAT": "certificat",
        "BILAN": "diagnostic",
        "RADIOGRAPHIE": "radio",
        "RAPPORT_CEPHALO": "radio",
    }
    doc_events = docs_q.all()
    for d in doc_events:
        dtype = d.document_type.value if hasattr(d.document_type, "value") else str(d.document_type)
        events.append(_event(
            f"document_archive:{d.id}", "document_archive", dtype, d.id, d.created_at,
            d.title or d.original_filename, d.status.value, doc_type_to_phase.get(dtype, "document"),
            schemas.NavigationTarget.DOCUMENT,
        ))

    # 4. PanoramicAnalysis
    pano_q = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.patient_id == patient_id)
    if since is not None:
        pano_q = pano_q.filter(models.PanoramicAnalysis.created_at >= since)
    pano_events = pano_q.all()
    for p in pano_events:
        events.append(_event(
            f"panoramic_analysis:{p.id}", "panoramic_analysis", "panoramique", p.id, p.created_at,
            "Analyse panoramique", "TERMINE", "radio",
            schemas.NavigationTarget.RADIOLOGY_TAB,
        ))

    # 5. CephaloAnalysis
    cephalo_q = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id)
    if since is not None:
        cephalo_q = cephalo_q.filter(models.CephaloAnalysis.created_at >= since)
    cephalo_events = cephalo_q.all()
    for c in cephalo_events:
        events.append(_event(
            f"cephalo_analysis:{c.id}", "cephalo_analysis", "cephalometrie", c.id, c.created_at,
            "Analyse céphalométrique", "CALIBRE" if c.is_calibrated else "NON_CALIBRE", "radio",
            schemas.NavigationTarget.RADIOLOGY_TAB,
        ))

    # Affichage groupé (pas de masquage) : un DocumentArchive(RAPPORT_CEPHALO/rapport pano) généré
    # à moins de 5 min d'une analyse pointe vers l'événement source.
    _link_related_reports(events, doc_events, pano_events, cephalo_events)

    # 6. Payment
    pay_q = db.query(models.Payment).filter(models.Payment.patient_id == patient_id)
    if since is not None:
        pay_q = pay_q.filter(models.Payment.payment_date >= since)
    for p in pay_q.all():
        events.append(_event(
            f"payment:{p.id}", "payment", "paiement", p.id, p.payment_date,
            f"Paiement — {p.amount:.2f} MAD", p.payment_method.value if hasattr(p.payment_method, "value") else str(p.payment_method),
            "paiement", schemas.NavigationTarget.ACCOUNTING_TAB,
        ))

    # 7. Installment (via InstallmentPlan) — toujours inclus si EN_ATTENTE (item ouvert)
    inst_q = (
        db.query(models.Installment)
        .join(models.InstallmentPlan, models.Installment.plan_id == models.InstallmentPlan.id)
        .filter(models.InstallmentPlan.patient_id == patient_id)
    )
    for i in inst_q.all():
        is_open = i.status == "EN_ATTENTE"
        ref_date = i.due_date
        if since is not None and ref_date < since and not is_open:
            continue
        events.append(_event(
            f"installment:{i.id}", "installment", "echeance", i.id, ref_date,
            f"Échéance — {i.label}", i.status, "paiement",
            schemas.NavigationTarget.ACCOUNTING_TAB,
        ))

    # 8. LabJob (via patient_id direct)
    lab_q = db.query(models.LabJob).filter(models.LabJob.patient_id == patient_id)
    if since is not None:
        lab_q = lab_q.filter(models.LabJob.created_at >= since)
    for lj in lab_q.all():
        events.append(_event(
            f"lab_job:{lj.id}", "lab_job", lj.type, lj.id, lj.created_at,
            f"Labo — {lj.type}", lj.status.value, "labo",
            schemas.NavigationTarget.LAB_PAGE,
        ))

    # 9. JourneyMilestone (jalons manuels, exclut les supprimés)
    milestone_q = db.query(models.JourneyMilestone).filter(
        models.JourneyMilestone.patient_id == patient_id,
        models.JourneyMilestone.deleted_at.is_(None),
    )
    if since is not None:
        milestone_q = milestone_q.filter(models.JourneyMilestone.milestone_date >= since)
    milestone_phase = {
        "DIAGNOSTIC": "diagnostic", "DEVIS_VALIDE": "devis",
        "CONTROLE": "controle", "CLOTURE": "cloture",
    }
    for m in milestone_q.all():
        mtype = m.milestone_type.value if hasattr(m.milestone_type, "value") else str(m.milestone_type)
        events.append(_event(
            f"journey_milestone:{m.id}", "journey_milestone", mtype, m.id, m.milestone_date,
            mtype.replace("_", " ").title(), mtype, milestone_phase.get(mtype, "autre"),
            schemas.NavigationTarget.INLINE,
        ))

    return events


def _link_related_reports(events: list, doc_events: list, pano_events: list, cephalo_events: list) -> None:
    """Affichage groupé optionnel — ne masque jamais un événement, ajoute juste related_event_key."""
    window = timedelta(minutes=RELATED_REPORT_WINDOW_MINUTES)
    analyses = [(f"panoramic_analysis:{p.id}", p.created_at) for p in pano_events]
    analyses += [(f"cephalo_analysis:{c.id}", c.created_at) for c in cephalo_events]
    if not analyses:
        return
    report_types = {"RAPPORT_CEPHALO", "RADIOGRAPHIE"}
    by_key = {e.event_key: e for e in events}
    for d in doc_events:
        dtype = d.document_type.value if hasattr(d.document_type, "value") else str(d.document_type)
        if dtype not in report_types:
            continue
        for akey, adate in analyses:
            if abs((d.created_at - adate).total_seconds()) <= window.total_seconds():
                ev = by_key.get(f"document_archive:{d.id}")
                if ev is not None:
                    ev.related_event_key = akey
                break


def _sort_key(event: "schemas.JourneyEventResponse"):
    return (-(event.date.timestamp()), event.source, event.ref_id)


def build_journey(db: Session, patient_id: int, employer_id: int, full_history: bool = False) -> schemas.PatientJourneyResponse:
    since = None if full_history else (datetime.now() - timedelta(days=WINDOW_MONTHS * 30))

    events = _collect_events(db, patient_id, since)
    events.sort(key=_sort_key)

    total_available = len(events)
    truncated = False
    if full_history and total_available > FULL_HISTORY_CAP:
        events = events[:FULL_HISTORY_CAP]
        truncated = True

    summary = _build_summary(db, patient_id)

    return schemas.PatientJourneyResponse(
        patient_id=patient_id,
        window_months=WINDOW_MONTHS,
        truncated=truncated,
        total_events_available=total_available,
        summary=summary,
        events=events,
    )


def _build_summary(db: Session, patient_id: int) -> schemas.JourneySummaryResponse:
    total_plan_steps = (
        db.query(func.count(models.TreatmentPlanStep.id))
        .join(models.TreatmentMasterPlan, models.TreatmentPlanStep.plan_id == models.TreatmentMasterPlan.id)
        .filter(models.TreatmentMasterPlan.patient_id == patient_id)
        .scalar() or 0
    )
    active_plan_steps = (
        db.query(func.count(models.TreatmentPlanStep.id))
        .join(models.TreatmentMasterPlan, models.TreatmentPlanStep.plan_id == models.TreatmentMasterPlan.id)
        .filter(
            models.TreatmentMasterPlan.patient_id == patient_id,
            models.TreatmentPlanStep.status == models.PlanStatus.PENDING,
        )
        .scalar() or 0
    )

    # Reste dû : même calcul que get_patient_financial_snapshot (patients.py) pour rester
    # cohérent avec le reste de l'app — la fiabilité de cette donnée est un problème connu et
    # séparé (backlog UNIFY-ACT-PERSISTENCE-1), pas réintroduit ici.
    total_billed = float(
        db.query(func.sum(models.Acte.montant)).filter(models.Acte.patient_id == patient_id).scalar() or 0.0
    )
    total_collected = float(
        db.query(func.sum(models.Payment.amount)).filter(models.Payment.patient_id == patient_id).scalar() or 0.0
    )
    remaining_due = max(total_billed - total_collected, 0.0)

    next_appt = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.patient_id == patient_id,
            models.Appointment.datetime_start >= datetime.now(),
            models.Appointment.status.in_(_NEXT_APPOINTMENT_STATUSES),
        )
        .order_by(models.Appointment.datetime_start.asc())
        .first()
    )

    last_doc = (
        db.query(func.max(models.DocumentArchive.created_at))
        .filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.is_latest_version.is_(True),
            models.DocumentArchive.status == models.DocumentStatus.ACTIF,
            models.DocumentArchive.deleted_at.is_(None),
        )
        .scalar()
    )

    return schemas.JourneySummaryResponse(
        active_plan_steps=int(active_plan_steps),
        total_plan_steps=int(total_plan_steps),
        remaining_due=round(remaining_due, 2),
        next_appointment=next_appt.datetime_start if next_appt else None,
        last_document_date=last_doc,
    )


def check_and_create_milestone(
    db: Session,
    patient_id: int,
    employer_id: int,
    milestone_type: "models.MilestoneType",
    milestone_date: datetime,
    note: Optional[str],
    confirm_duplicate: bool,
    created_by: int,
) -> schemas.JourneyMilestoneCreateResponse:
    """Verrouille la ligne Patient (SELECT ... FOR UPDATE) avant de vérifier/insérer —
    protège contre deux requêtes concurrentes créant chacune un doublon (n'a d'effet réel
    que sur PostgreSQL ; SQLite ne sérialise pas FOR UPDATE en connexions concurrentes)."""
    db.query(models.Patient).filter(models.Patient.id == patient_id).with_for_update().first()

    same_day_start = milestone_date.replace(hour=0, minute=0, second=0, microsecond=0)
    same_day_end = same_day_start + timedelta(days=1)
    existing = (
        db.query(models.JourneyMilestone)
        .filter(
            models.JourneyMilestone.patient_id == patient_id,
            models.JourneyMilestone.milestone_type == milestone_type,
            models.JourneyMilestone.milestone_date >= same_day_start,
            models.JourneyMilestone.milestone_date < same_day_end,
            models.JourneyMilestone.note == note,
            models.JourneyMilestone.deleted_at.is_(None),
        )
        .first()
    )

    if existing is not None and not confirm_duplicate:
        db.commit()  # libère le verrou sans rien créer
        return schemas.JourneyMilestoneCreateResponse(
            milestone=None, possible_duplicate=True, existing_milestone_id=existing.id,
        )

    milestone = models.JourneyMilestone(
        patient_id=patient_id,
        employer_id=employer_id,
        milestone_type=milestone_type,
        milestone_date=milestone_date,
        note=note,
        created_by=created_by,
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)

    return schemas.JourneyMilestoneCreateResponse(
        milestone=schemas.JourneyMilestoneOut.model_validate(milestone),
        possible_duplicate=existing is not None,
    )


def soft_delete_milestone(db: Session, patient_id: int, milestone_id: int, deleted_by: int) -> models.JourneyMilestone:
    milestone = (
        db.query(models.JourneyMilestone)
        .filter(
            models.JourneyMilestone.id == milestone_id,
            models.JourneyMilestone.patient_id == patient_id,
            models.JourneyMilestone.deleted_at.is_(None),
        )
        .first()
    )
    if milestone is None:
        return None
    milestone.deleted_at = datetime.now()
    milestone.deleted_by = deleted_by
    db.commit()
    db.refresh(milestone)
    return milestone

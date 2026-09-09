import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session
from backend import models
from backend.utils.accounting_utils import extract_amount_from_clinical_data
from datetime import datetime

logger = logging.getLogger(__name__)
_GENERATED_PAYMENT_PREFIX = "Lien Doc ID: "
_VOIDED_PAYMENT_PREFIX = "ANNULÉ — Lien Doc ID: "
_TRASHED_PAYMENT_PREFIX = "CORBEILLE — Lien Doc ID: "


class AccountingService:
    """
    Service de gestion comptable et apprentissage des actes fréquents.
    """

    @staticmethod
    def _visible_payment_filter():
        """Paiements visibles en trésorerie sans effacer l'historique financier.

        - paiement manuel : toujours réel, même si l'Acte lié est ensuite masqué ;
        - paiement généré par Document Studio : masqué si l'Acte dérivé est en
          corbeille ;
        - paiement généré puis annulé par une édition : toujours masqué ;
        - paiement directement lié à un document placé à la corbeille : masqué
          jusqu'à restauration du document.
        """
        notes = models.Payment.notes
        not_voided = or_(
            notes.is_(None),
            and_(
                ~notes.startswith(_VOIDED_PAYMENT_PREFIX),
                ~notes.startswith(_TRASHED_PAYMENT_PREFIX),
            ),
        )
        not_document_generated = or_(
            notes.is_(None),
            ~notes.startswith(_GENERATED_PAYMENT_PREFIX),
        )
        return and_(
            not_voided,
            or_(
                models.Payment.acte_id.is_(None),
                models.Acte.deleted_at.is_(None),
                and_(models.Acte.deleted_at.isnot(None), not_document_generated),
            ),
        )

    def record_act_usage(self, db: Session, doctor_id: int, act_name: str, price: float = 0.0, category: str = None):
        """
        Enregistre l'usage d'un acte clinique pour l'apprentissage des raccourcis.
        """
        try:
            act_name = act_name.strip()
            existing = db.query(models.DoctorActHabit).filter(
                models.DoctorActHabit.doctor_id == doctor_id,
                models.DoctorActHabit.act_name == act_name
            ).first()

            if existing:
                existing.usage_count += 1
                if price > 0:
                    existing.base_price = price
                if category:
                    existing.category = category
            else:
                new_habit = models.DoctorActHabit(
                    doctor_id=doctor_id,
                    act_name=act_name,
                    base_price=price,
                    category=category,
                    usage_count=1
                )
                db.add(new_habit)
            
            from backend.services.habits_engine import habits_engine
            
            db.commit()
            logger.info(f"✅ Habitude d'acte enregistrée : {act_name} pour Dr {doctor_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erreur record_act_usage : {e}")

    def get_frequent_acts(self, db: Session, doctor_id: int, limit: int = 8) -> List[Dict[str, Any]]:
        habits = db.query(models.DoctorActHabit).filter(
            models.DoctorActHabit.doctor_id == doctor_id
        ).order_by(models.DoctorActHabit.usage_count.desc()).limit(limit).all()
        
        return [
            {
                "id": h.id,
                "name": h.act_name,
                "base_price": h.base_price,
                "category": h.category,
                "usage_count": h.usage_count,
                "is_habit": True
            } for h in habits
        ]

    def search_acts(self, db: Session, doctor_id: int, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        query = query.strip()
        if not query:
            return []

        habits = db.query(models.DoctorActHabit).filter(
            models.DoctorActHabit.doctor_id == doctor_id,
            models.DoctorActHabit.act_name.ilike(f"%{query}%")
        ).order_by(models.DoctorActHabit.usage_count.desc()).limit(limit).all()

        habit_names = {h.act_name.lower() for h in habits}
        results = [
            {
                "id": f"habit_{h.id}",
                "name": h.act_name,
                "base_price": h.base_price,
                "category": h.category,
                "is_habit": True
            } for h in habits
        ]

        if len(results) < limit:
            catalog = (
                db.query(models.CatalogAct, models.Specialty.name)
                .join(models.Specialty, models.CatalogAct.specialty_id == models.Specialty.id)
                .filter(
                    models.CatalogAct.name.ilike(f"%{query}%"),
                    models.CatalogAct.is_active == True,
                )
                .order_by(models.CatalogAct.name)
                .limit(limit - len(results))
                .all()
            )

            for c, spec_name in catalog:
                if c.name.lower() not in habit_names:
                    results.append({
                        "id": f"cat_{c.id}",
                        "name": c.name,
                        "base_price": c.base_price,
                        "category": spec_name or "Général",
                        "is_habit": False
                    })

        return results

    def get_smart_bundles(self, act_names: List[str]) -> List[Dict[str, Any]]:
        bundles = []
        act_names_lower = [a.lower() for a in act_names]
        
        associations = {
            "détartrage": [
                {"name": "Polissage", "price": 100, "category": "Prévention"},
                {"name": "Application de Fluor", "price": 200, "category": "Prévention"}
            ],
            "extraction": [
                {"name": "Radio Alvéolaire", "price": 100, "category": "Radiologie"},
                {"name": "Comblement Alvéolaire", "price": 500, "category": "Chirurgie"}
            ],
            "implant": [
                {"name": "Scanner (CBCT)", "price": 800, "category": "Radiologie"},
                {"name": "Pilier de cicatrisation", "price": 450, "category": "Implantologie"}
            ],
            "carie": [
                {"name": "Radio Alvéolaire", "price": 100, "category": "Radiologie"}
            ]
        }

        for act in act_names_lower:
            for key, associated in associations.items():
                if key in act:
                    for item in associated:
                        if not any(item["name"].lower() in a for a in act_names_lower):
                            bundles.append(item)
                            
        from backend.services.habits_engine import habits_engine
        if len(act_names) > 0:
            pass
        
        return bundles

    def get_treasury_summary(self, db: Session, user_employer_id: int) -> Dict[str, Any]:
        docs = db.query(models.DocumentArchive).join(models.Patient).filter(
            or_(models.DocumentArchive.status == models.DocumentStatus.ACTIF, models.DocumentArchive.status == None),
            models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
            or_(models.DocumentArchive.is_collected == False, models.DocumentArchive.is_collected == None),
            or_(models.DocumentArchive.is_latest_version == True, models.DocumentArchive.is_latest_version == None),
            or_(models.DocumentArchive.is_accounted == True, models.DocumentArchive.is_accounted == None),
            models.Patient.employer_id == user_employer_id
        ).all()

        doc_ids_with_actes = {
            row[0] for row in db.query(models.Acte.document_archive_id)
            .filter(models.Acte.document_archive_id.isnot(None)).distinct().all()
        }
        docs = [d for d in docs if d.id not in doc_ids_with_actes]

        actes = db.query(models.Acte).join(models.Patient).filter(
            models.Acte.is_accounted == True,
            models.Acte.deleted_at.is_(None),
            or_(models.Acte.is_collected == False, models.Acte.is_collected == None),
            models.Patient.employer_id == user_employer_id
        ).all()

        pending_total_docs = sum(extract_amount_from_clinical_data(d.clinical_data) for d in docs if (d.payment_status == models.PaiementStatut.EN_ATTENTE or d.payment_status == models.PaiementStatut.A_ENCAISSER or d.payment_status == None))
        partial_total_docs = sum(extract_amount_from_clinical_data(d.clinical_data) for d in docs if d.payment_status == models.PaiementStatut.PARTIEL)
        pending_total_actes = sum(a.montant for a in actes if a.statut_paiement in [models.PaiementStatut.EN_ATTENTE, models.PaiementStatut.A_ENCAISSER])
        partial_total_actes = sum(a.montant for a in actes if a.statut_paiement == models.PaiementStatut.PARTIEL)

        items = []
        for d in docs:
            items.append({
                "id": f"doc_{d.id}",
                "patient_name": f"{d.patient.nom} {d.patient.prenom}",
                "patient_id": d.patient_id,
                "amount": extract_amount_from_clinical_data(d.clinical_data),
                "status": d.payment_status or models.PaiementStatut.EN_ATTENTE,
                "date": d.created_at.isoformat(),
                "type": "NOTE"
            })
            
        for a in actes:
            items.append({
                "id": f"acte_{a.id}",
                "patient_name": f"{a.patient.nom} {a.patient.prenom}",
                "patient_id": a.patient_id,
                "amount": a.montant,
                "status": a.statut_paiement or models.PaiementStatut.EN_ATTENTE,
                "date": a.date_debut.isoformat(),
                "type": "ACTE"
            })

        items.sort(key=lambda x: x["date"], reverse=True)

        today = datetime.now()
        installments = db.query(models.Installment).join(models.InstallmentPlan).join(models.Patient).filter(
            models.Installment.status == "EN_ATTENTE",
            models.Patient.employer_id == user_employer_id
        ).all()
        
        proactive_alerts = []
        for inst in installments:
            days_diff = (inst.due_date.date() - today.date()).days
            if days_diff < 0:
                proactive_alerts.append({
                    "id": f"alert_inst_{inst.id}",
                    "type": "OVERDUE",
                    "severity": "critical" if days_diff < -7 else "warning",
                    "message": f"Échéance en retard de {abs(days_diff)} jours pour {inst.plan.patient.nom} {inst.plan.patient.prenom} ({inst.amount} MAD)",
                    "patient_id": inst.plan.patient_id,
                    "amount": inst.amount,
                    "action": "Relancer le patient"
                })
            elif days_diff <= 3:
                proactive_alerts.append({
                    "id": f"alert_inst_{inst.id}",
                    "type": "UPCOMING",
                    "severity": "info",
                    "message": f"Échéance imminente (dans {days_diff} j) pour {inst.plan.patient.nom} {inst.plan.patient.prenom} ({inst.amount} MAD)",
                    "patient_id": inst.plan.patient_id,
                    "amount": inst.amount,
                    "action": "Préparer l'encaissement"
                })

        return {
            "pending_count": len(items),
            "pending_total": pending_total_docs + pending_total_actes,
            "partial_total": partial_total_docs + partial_total_actes,
            "cheques_count": len([i for i in items if i["status"] == models.PaiementStatut.A_ENCAISSER]),
            "items": items,
            "proactive_alerts": sorted(proactive_alerts, key=lambda x: -1 if x["severity"] == "critical" else 1)
        }

    def get_finance_kpis(self, db: Session, employer_id: int, today: datetime.date) -> Dict[str, Any]:
        """Centralise les KPIs financiers avec la même vérité de corbeille partout."""
        from datetime import datetime as dt, time as dt_time, timedelta
        from sqlalchemy import extract
        
        day_start = dt.combine(today, dt_time.min)
        day_end = dt.combine(today, dt_time.max)
        visible_payment = self._visible_payment_filter()
        
        today_revenue = (
            db.query(func.sum(models.Payment.amount))
            .join(models.Patient, models.Payment.patient_id == models.Patient.id)
            .outerjoin(models.Acte, models.Payment.acte_id == models.Acte.id)
            .filter(
                models.Patient.employer_id == employer_id,
                models.Payment.payment_date >= day_start,
                models.Payment.payment_date <= day_end,
                visible_payment,
            )
            .scalar() or 0.0
        )
        
        month_revenue = (
            db.query(func.sum(models.Payment.amount))
            .join(models.Patient, models.Payment.patient_id == models.Patient.id)
            .outerjoin(models.Acte, models.Payment.acte_id == models.Acte.id)
            .filter(
                models.Patient.employer_id == employer_id,
                extract("year", models.Payment.payment_date) == today.year,
                extract("month", models.Payment.payment_date) == today.month,
                visible_payment,
            )
            .scalar() or 0.0
        )
        
        last_month_last_day = today.replace(day=1) - timedelta(days=1)
        prev_month_revenue = (
            db.query(func.sum(models.Payment.amount))
            .join(models.Patient, models.Payment.patient_id == models.Patient.id)
            .outerjoin(models.Acte, models.Payment.acte_id == models.Acte.id)
            .filter(
                models.Patient.employer_id == employer_id,
                extract("year", models.Payment.payment_date) == last_month_last_day.year,
                extract("month", models.Payment.payment_date) == last_month_last_day.month,
                visible_payment,
            )
            .scalar() or 0.0
        )
        
        month_variation = None
        if prev_month_revenue > 0:
            month_variation = round(((month_revenue - prev_month_revenue) / prev_month_revenue) * 100, 1)
            
        week_start = dt.combine(today - timedelta(days=6), dt_time.min)
        weekly_rows = (
            db.query(
                func.date(models.Payment.payment_date).label("day"),
                func.sum(models.Payment.amount).label("total"),
            )
            .join(models.Patient, models.Payment.patient_id == models.Patient.id)
            .outerjoin(models.Acte, models.Payment.acte_id == models.Acte.id)
            .filter(
                models.Patient.employer_id == employer_id,
                models.Payment.payment_date >= week_start,
                visible_payment,
            )
            .group_by(func.date(models.Payment.payment_date))
            .all()
        )
        weekly_map = {str(r.day): float(r.total) for r in weekly_rows}
        weekly_revenue = [
            {"date": str(today - timedelta(days=6 - i)), "amount": weekly_map.get(str(today - timedelta(days=6 - i)), 0.0)}
            for i in range(7)
        ]
        
        patients_q = db.query(models.Patient).filter(models.Patient.employer_id == employer_id).all()
        debtors_list = []
        total_debt = 0.0

        for p in patients_q:
            p_acts = (
                db.query(func.sum(models.Acte.montant))
                .filter(
                    models.Acte.patient_id == p.id,
                    models.Acte.deleted_at.is_(None),
                )
                .scalar() or 0.0
            )
            p_pays = (
                db.query(func.sum(models.Payment.amount))
                .outerjoin(models.Acte, models.Payment.acte_id == models.Acte.id)
                .filter(
                    models.Payment.patient_id == p.id,
                    visible_payment,
                )
                .scalar() or 0.0
            )
            debt = float(p_acts) - float(p_pays)
            if debt > 0:
                total_debt += debt
                debtors_list.append({
                    "id": p.id,
                    "name": f"{p.prenom} {p.nom}",
                    "amount": round(debt, 2),
                    "phone": p.telephone,
                })

        debtors_list.sort(key=lambda x: x["amount"], reverse=True)
        debtors = debtors_list[:20]
        total_debt = round(total_debt, 2)
        
        return {
            "today_revenue": round(today_revenue, 2),
            "month_revenue": round(month_revenue, 2),
            "month_variation": month_variation,
            "weekly_revenue": weekly_revenue,
            "total_debt": total_debt,
            "debtors": debtors
        }

accounting_service = AccountingService()
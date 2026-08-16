import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from backend import models
from backend.utils.accounting_utils import extract_amount_from_clinical_data
from datetime import datetime

logger = logging.getLogger(__name__)

class AccountingService:
    """
    Service de gestion comptable et apprentissage des actes fréquents.
    """

    def record_act_usage(self, db: Session, doctor_id: int, act_name: str, price: float = 0.0, category: str = None):
        """
        Enregistre l'usage d'un acte clinique pour l'apprentissage des raccourcis.
        """
        try:
            act_name = str(act_name or "").strip()
            if not act_name or (act_name.startswith("--- ") and act_name.endswith(" ---")):
                return

            existing = db.query(models.DoctorActHabit).filter(
                models.DoctorActHabit.doctor_id == doctor_id,
                models.DoctorActHabit.act_name == act_name
            ).first()

            if existing:
                existing.usage_count += 1
                # Mettre à jour le prix si c'est une valeur non nulle
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
            
            # --- MPL : Enregistrement de la séquence ---
            from backend.services.habits_engine import habits_engine
            # On cherche le dernier acte du patient pour enregistrer la corrélation
            # Note: On a besoin du patient_id ici, on va l'ajouter en paramètre ou le déduire
            # Pour l'instant on se concentre sur l'usage simple, la séquence sera gérée par le routeur
            
            db.commit()
            logger.info(f"✅ Habitude d'acte enregistrée : {act_name} pour Dr {doctor_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erreur record_act_usage : {e}")

    def get_frequent_acts(self, db: Session, doctor_id: int, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Retourne les actes les plus fréquents pour la barre de raccourcis.
        """
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
        """
        Recherche un acte dans le catalogue global ET dans les habitudes du médecin.
        Les habitudes ont la priorité sur le prix.
        """
        query = query.strip()
        if not query:
            return []

        # 1. Chercher dans les habitudes du médecin
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

        # 2. Chercher dans le Catalogue Dynamique managé (CatalogAct + Specialty),
        #    source de vérité unique partagée avec les Réglages.
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
        """
        Suggère des 'bundles' d'actes basés sur les actes déjà saisis.
        Logique proactive pour ne rien oublier (ex: radio avec extraction).
        """
        bundles = []
        act_names_lower = [a.lower() for a in act_names]
        
        # Logique de règles (évolutive vers ML)
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
                            
        # 2. Logique Dynamique (Habits Engine)
        from backend.services.habits_engine import habits_engine
        # On simule un DB session ici si possible ou on passe par le routeur
        # Pour simplifier, on injecte les bundles dynamiques s'ils ne sont pas déjà présents
        if len(act_names) > 0:
            # On prendrait normalement une session db propre, mais ici on est dans un service
            # On va laisser le routeur combiner les deux pour éviter les circular imports complexes
            pass
        
        return bundles

    def get_treasury_summary(self, db: Session, user_employer_id: int) -> Dict[str, Any]:
        """
        Calcule un résumé de la trésorerie pour le Treasury Hub.
        Inclut les Documents (Notes) et les Actes marqués pour la compta.
        """
        # 1. Documents non encore encaissés (is_collected != True)
        docs = db.query(models.DocumentArchive).join(models.Patient).filter(
            or_(models.DocumentArchive.status == models.DocumentStatus.ACTIF, models.DocumentArchive.status == None),
            models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
            or_(models.DocumentArchive.is_collected == False, models.DocumentArchive.is_collected == None),
            or_(models.DocumentArchive.is_latest_version == True, models.DocumentArchive.is_latest_version == None),
            or_(models.DocumentArchive.is_accounted == True, models.DocumentArchive.is_accounted == None),
            models.Patient.employer_id == user_employer_id
        ).all()

        # UNIFY-ACT-PERSISTENCE-1 : ne pas compter un document deux fois (une fois via
        # son clinical_data JSON, une fois via ses Acte liés générés automatiquement par
        # documents.py::generate_document). Pas de garde filter_type ici — ce paramètre
        # n'existe pas sur cet endpoint.
        doc_ids_with_actes = {
            row[0] for row in db.query(models.Acte.document_archive_id)
            .filter(models.Acte.document_archive_id.isnot(None)).distinct().all()
        }
        docs = [d for d in docs if d.id not in doc_ids_with_actes]

        # 2. Actes non encore encaissés (is_collected != True)
        actes = db.query(models.Acte).join(models.Patient).filter(
            models.Acte.is_accounted == True,
            models.Acte.deleted_at.is_(None),
            or_(models.Acte.is_collected == False, models.Acte.is_collected == None),
            models.Patient.employer_id == user_employer_id
        ).all()

        # Calcul des totaux
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

        # 3. Intelligence Proactive : Détection des échéances (Installments)
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
        """Centralise le calcul des KPIs financiers pour le mobile (ou autres dashboards)."""
        from datetime import datetime as dt, time as dt_time, timedelta
        from sqlalchemy import extract
        
        day_start = dt.combine(today, dt_time.min)
        day_end = dt.combine(today, dt_time.max)
        
        # 1. Recettes du jour
        today_revenue = (
            db.query(func.sum(models.Payment.amount))
            .join(models.Patient, models.Payment.patient_id == models.Patient.id)
            .filter(
                models.Patient.employer_id == employer_id,
                models.Payment.payment_date >= day_start,
                models.Payment.payment_date <= day_end,
            )
            .scalar() or 0.0
        )
        
        # 2. Recettes du mois
        month_revenue = (
            db.query(func.sum(models.Payment.amount))
            .join(models.Patient, models.Payment.patient_id == models.Patient.id)
            .filter(
                models.Patient.employer_id == employer_id,
                extract("year", models.Payment.payment_date) == today.year,
                extract("month", models.Payment.payment_date) == today.month,
            )
            .scalar() or 0.0
        )
        
        # 3. Variation mois précédent
        last_month_last_day = today.replace(day=1) - timedelta(days=1)
        prev_month_revenue = (
            db.query(func.sum(models.Payment.amount))
            .join(models.Patient, models.Payment.patient_id == models.Patient.id)
            .filter(
                models.Patient.employer_id == employer_id,
                extract("year", models.Payment.payment_date) == last_month_last_day.year,
                extract("month", models.Payment.payment_date) == last_month_last_day.month,
            )
            .scalar() or 0.0
        )
        
        month_variation = None
        if prev_month_revenue > 0:
            month_variation = round(((month_revenue - prev_month_revenue) / prev_month_revenue) * 100, 1)
            
        # 4. Recettes 7 derniers jours
        week_start = dt.combine(today - timedelta(days=6), dt_time.min)
        weekly_rows = (
            db.query(
                func.date(models.Payment.payment_date).label("day"),
                func.sum(models.Payment.amount).label("total"),
            )
            .join(models.Patient, models.Payment.patient_id == models.Patient.id)
            .filter(
                models.Patient.employer_id == employer_id,
                models.Payment.payment_date >= week_start,
            )
            .group_by(func.date(models.Payment.payment_date))
            .all()
        )
        weekly_map = {str(r.day): float(r.total) for r in weekly_rows}
        weekly_revenue = [
            {"date": str(today - timedelta(days=6 - i)), "amount": weekly_map.get(str(today - timedelta(days=6 - i)), 0.0)}
            for i in range(7)
        ]
        
        # 5. Débiteurs (Actes - Paiements)
        patients_q = db.query(models.Patient).filter(models.Patient.employer_id == employer_id).all()
        debtors_list = []
        total_debt = 0.0

        for p in patients_q:
            p_acts = db.query(func.sum(models.Acte.montant)).filter(models.Acte.patient_id == p.id).scalar() or 0.0
            p_pays = db.query(func.sum(models.Payment.amount)).filter(models.Payment.patient_id == p.id).scalar() or 0.0
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
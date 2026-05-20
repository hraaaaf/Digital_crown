"""
Seed unique des données cliniques (contre-indications, pharmacopée marocaine, protocoles).
Charge les constantes du ClinicalRulesEngine en DB pour permettre les mises à jour
sans redéploiement. Idempotent : ne re-seed pas si les tables sont déjà peuplées.
"""
import logging
from sqlalchemy.orm import Session
from backend import models
from backend.services.clinical_rules_engine import ClinicalRulesEngine

logger = logging.getLogger(__name__)


def seed_clinical_data(db: Session) -> None:
    # Idempotence : ne rien faire si la table est déjà peuplée
    if db.query(models.ClinicalContraindication).count() > 0:  # Idempotence check
        return

    logger.info("🧬 Seeding données cliniques (contre-indications, pharmacopée, protocoles)...")

    # --- Contre-indications ---
    for antecedent, molecules in ClinicalRulesEngine.CONTRE_INDICATIONS.items():
        for molecule in molecules:
            db.add(models.ClinicalContraindication(antecedent=antecedent, molecule=molecule))

    # --- Pharmacopée marocaine ---
    for molecule, data in ClinicalRulesEngine.MAROC_PHARMACOPEIA.items():
        db.add(models.ClinicalDrug(
            molecule=molecule,
            brand_names=data.get("noms", []),
            dosages=data.get("dosages", []),
            form=data.get("forme"),
        ))

    # --- Protocoles par acte ---
    for procedure, data in ClinicalRulesEngine.PROTOCOLS.items():
        db.add(models.ClinicalProtocolDB(
            procedure=procedure,
            molecules=data.get("molecules", []),
            advice=data.get("conseil"),
        ))

    db.commit()
    logger.info("✅ Données cliniques seedées avec succès.")

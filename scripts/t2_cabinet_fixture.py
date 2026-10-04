"""Canonical synthetic cabinet fixture for GitHub Actions browser certification.

Creates five deterministic, strictly fictitious patients under the isolated T2
cabinet. Idempotent by (employer_id, numero_dossier). Never imported by product
startup; CI invokes it explicitly after the isolated runtime is ready.
"""
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend import database, models

OWNER_EMAIL = "t2-browser@cabinet.ma"

PATIENTS = (
    {
        "numero_dossier": "T2-0001",
        "nom": "CERTIFICATION",
        "prenom": "T2",
        "date_naissance": datetime(1990, 1, 1),
        "sexe": "M",
        "telephone": "0600000000",
        "email": "patient-0001@digitalcrown.invalid",
        "assurance": "AUCUNE",
    },
    {
        "numero_dossier": "T2-0002",
        "nom": "CERTIFICATION-B",
        "prenom": "T2B",
        "date_naissance": datetime(1992, 2, 2),
        "sexe": "F",
        "telephone": "0611111111",
        "email": "patient-0002@digitalcrown.invalid",
        "assurance": "AUCUNE",
    },
    {
        "numero_dossier": "T2-0003",
        "nom": "HONORAIRES",
        "prenom": "PARTIEL",
        "date_naissance": datetime(1985, 3, 3),
        "sexe": "F",
        "telephone": "0622222222",
        "email": "patient-0003@digitalcrown.invalid",
        "assurance": "AUCUNE",
    },
    {
        "numero_dossier": "T2-0004",
        "nom": "PARCOURS",
        "prenom": "MULTIACTES",
        "date_naissance": datetime(1978, 4, 4),
        "sexe": "M",
        "telephone": "0633333333",
        "email": "patient-0004@digitalcrown.invalid",
        "assurance": "AUCUNE",
    },
    {
        "numero_dossier": "T2-0005",
        "nom": "DOCUMENTS",
        "prenom": "HISTORIQUE",
        "date_naissance": datetime(2001, 5, 5),
        "sexe": "F",
        "telephone": "0644444444",
        "email": "patient-0005@digitalcrown.invalid",
        "assurance": "AUCUNE",
    },
)


def seed() -> None:
    with database.SessionLocal() as db:
        owner = db.query(models.User).filter(models.User.email == OWNER_EMAIL).first()
        if owner is None:
            raise RuntimeError("Canonical T2 fixture requires the isolated T2 certification user")

        ids = {}
        for row in PATIENTS:
            patient = db.query(models.Patient).filter(
                models.Patient.numero_dossier == row["numero_dossier"],
                models.Patient.employer_id == owner.id,
            ).first()
            if patient is None:
                patient = models.Patient(employer_id=owner.id, **row)
                db.add(patient)
                db.flush()
            else:
                # Canonical fixture is authoritative even when T2-0001 was
                # provisioned earlier by the isolated runtime bootstrap.
                for field, value in row.items():
                    setattr(patient, field, value)
            dossier = db.query(models.DossierClinique).filter(
                models.DossierClinique.patient_id == patient.id
            ).first()
            if dossier is None:
                db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
            ids[row["numero_dossier"]] = patient.id

        db.commit()

        rows = db.query(models.Patient).filter(
            models.Patient.employer_id == owner.id,
            models.Patient.numero_dossier.in_([p["numero_dossier"] for p in PATIENTS]),
        ).all()
        expected_by_number = {p["numero_dossier"]: p for p in PATIENTS}
        actual_by_number = {p.numero_dossier: p for p in rows}
        if set(actual_by_number) != set(expected_by_number) or len(rows) != len(PATIENTS):
            raise RuntimeError(
                f"T2 fixture membership mismatch: expected={sorted(expected_by_number)} "
                f"actual={sorted(actual_by_number)} count={len(rows)}"
            )
        for number, expected in expected_by_number.items():
            patient = actual_by_number[number]
            for field, value in expected.items():
                if getattr(patient, field) != value:
                    raise RuntimeError(
                        f"T2 fixture field mismatch: {number}.{field} "
                        f"expected={value!r} actual={getattr(patient, field)!r}"
                    )

        print("T2_CANONICAL_CABINET_FIXTURE_PASS", sorted(actual_by_number), flush=True)


if __name__ == "__main__":
    seed()

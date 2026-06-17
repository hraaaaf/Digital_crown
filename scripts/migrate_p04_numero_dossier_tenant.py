"""
migrate_p04_numero_dossier_tenant.py — P0.4 : unicité multi-tenant du numéro de dossier.

AVANT : index UNIQUE GLOBAL `ix_patients_numero_dossier (numero_dossier)`.
        => deux cabinets (employer_id) ne peuvent pas réutiliser le même numéro.
APRÈS : index simple (non-unique) `ix_patients_numero_dossier (numero_dossier)`
        + contrainte UNIQUE composite `(numero_dossier, employer_id)`.

GARANTIES (contraintes non-négociables) :
  - Aucune donnée patient touchée : on ne modifie QUE des index/contraintes.
  - Pré-condition vérifiée : si un numero_dossier est partagé entre plusieurs
    employer_id, on ABANDONNE sans rien changer (la migration serait risquée).
  - count_before == count_after (patients) prouvé.
  - Idempotent : ré-exécutable sans erreur (vérifie l'état avant chaque étape).
  - Transaction unique : tout réussit, ou rien n'est appliqué (ROLLBACK).

Usage :
    .\\venv\\Scripts\\python.exe scripts\\migrate_p04_numero_dossier_tenant.py
    .\\venv\\Scripts\\python.exe scripts\\migrate_p04_numero_dossier_tenant.py --dry-run
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, "backend", ".env"))

OLD_UNIQUE_INDEX = "ix_patients_numero_dossier"
NEW_CONSTRAINT = "uq_patients_numero_dossier_employer"

DRY_RUN = "--dry-run" in sys.argv


def main() -> int:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("[FATAL] DATABASE_URL introuvable", file=sys.stderr)
        return 2
    engine = create_engine(url)

    with engine.begin() as conn:  # transaction : commit en sortie, rollback si exception
        # --- 0. État courant ---------------------------------------------
        count_before = conn.execute(text("SELECT COUNT(*) FROM patients")).scalar()

        idx_is_unique = conn.execute(text(
            "SELECT indexdef FROM pg_indexes "
            "WHERE tablename='patients' AND indexname=:n"
        ), {"n": OLD_UNIQUE_INDEX}).scalar()
        old_is_unique = bool(idx_is_unique and "UNIQUE INDEX" in idx_is_unique)

        constraint_exists = conn.execute(text(
            "SELECT 1 FROM pg_constraint "
            "WHERE conname=:n AND conrelid='patients'::regclass"
        ), {"n": NEW_CONSTRAINT}).scalar() is not None

        print(f"Patients (before)            : {count_before}")
        print(f"Index global UNIQUE présent  : {old_is_unique}")
        print(f"Contrainte composite présente: {constraint_exists}")

        if not old_is_unique and constraint_exists:
            print("✅ Déjà migré — rien à faire (idempotent).")
            return 0

        # --- 1. Pré-condition de sûreté : aucun numéro partagé entre tenants
        cross = conn.execute(text(
            "SELECT COUNT(*) FROM ("
            "  SELECT numero_dossier FROM patients "
            "  WHERE numero_dossier IS NOT NULL "
            "  GROUP BY numero_dossier "
            "  HAVING COUNT(DISTINCT employer_id) > 1"
            ") x"
        )).scalar()
        if cross and cross > 0:
            print(f"[ABORT] {cross} numero_dossier partagé(s) entre employer_id différents. "
                  "Migration annulée (résolution manuelle requise).", file=sys.stderr)
            raise SystemExit(3)
        print("Pré-condition OK : 0 numéro partagé entre tenants.")

        if DRY_RUN:
            print("[DRY-RUN] Aucune modification appliquée. Annulation de la transaction.")
            raise _DryRunRollback()

        # --- 2. Migration (DDL conservatrice) ----------------------------
        # 2a. Contrainte UNIQUE composite (NULLs distincts => multiples NULL OK)
        if not constraint_exists:
            conn.execute(text(
                f'ALTER TABLE patients ADD CONSTRAINT {NEW_CONSTRAINT} '
                f'UNIQUE (numero_dossier, employer_id)'
            ))
            print(f"➕ Contrainte {NEW_CONSTRAINT} créée.")

        # 2b. Remplacer l'index global UNIQUE par un index simple (non-unique)
        if old_is_unique:
            conn.execute(text(f'DROP INDEX IF EXISTS {OLD_UNIQUE_INDEX}'))
            conn.execute(text(
                f'CREATE INDEX {OLD_UNIQUE_INDEX} ON patients (numero_dossier)'
            ))
            print(f"🔁 {OLD_UNIQUE_INDEX} : UNIQUE global → index simple.")

        # --- 3. Vérification post-migration ------------------------------
        count_after = conn.execute(text("SELECT COUNT(*) FROM patients")).scalar()
        if count_after != count_before:
            print(f"[FATAL] count_before({count_before}) != count_after({count_after}) "
                  "→ ROLLBACK.", file=sys.stderr)
            raise SystemExit(4)
        print(f"Patients (after)             : {count_after}  ✅ count_before == count_after")

    print("✅ Migration P0.4 appliquée et committée.")
    return 0


class _DryRunRollback(Exception):
    """Force le rollback de la transaction en dry-run."""


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except _DryRunRollback:
        print("[DRY-RUN] Transaction annulée — base inchangée.")
        raise SystemExit(0)

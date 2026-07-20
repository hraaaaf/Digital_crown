#!/usr/bin/env python
"""
S9 â€” VÃ©rificateur de durcissement PRODUCTION (lecture seule, rejouable).

ContrÃ´le la cohÃ©rence de la configuration AVANT dÃ©ploiement. Ne touche AUCUNE
donnÃ©e : lit uniquement `backend.config.settings`. Ã€ lancer avec la config cible
(ex: `ENVIRONMENT=production python scripts/prod_safety_check.py`).

Sortie : code 0 si aucune ERREUR ; code 1 si au moins une ERREUR bloquante.
Les WARNINGs n'Ã©chouent pas le check mais doivent Ãªtre revus par l'opÃ©rateur.
"""
import sys

# Permet l'exÃ©cution depuis la racine du repo (`python scripts/prod_safety_check.py`)
sys.path.insert(0, ".")

from backend.config import settings  # noqa: E402

WEAK_KEYS = {
    "SET_A_REAL_SECRET_KEY_IN_ENV",
    "dev_only_secret_key_change_me",
    "changeme",
    "secret",
}


def main() -> int:
    env = str(settings.ENVIRONMENT).lower()
    is_prod = env == "production"
    errors: list[str] = []
    warnings: list[str] = []

    # --- SECRET_KEY (toujours appliquÃ©) ---
    if settings.SECRET_KEY in WEAK_KEYS or len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY faible/par dÃ©faut (< 32 caractÃ¨res ou valeur connue).")

    # --- CORS (toujours appliquÃ© : '*' + credentials = faille) ---
    if "*" in settings.ALLOWED_ORIGINS:
        errors.append("ALLOWED_ORIGINS contient un wildcard '*' (incompatible allow_credentials).")

    # --- Invariants spÃ©cifiques production / cabinet (on-premise) ---
    # cabinet = production-like, SAUF SQLite : le mode cabinet solo repose sur
    # SQLite/SQLCipher local (chiffrÃ©), explicitement autorisÃ©.
    is_cabinet = env == "cabinet"
    if is_prod or is_cabinet:
        if settings.DEBUG:
            errors.append(f"DEBUG=True interdit en {env}.")
        if is_prod and settings.DATABASE_URL.strip().lower().startswith("sqlite"):
            errors.append("DATABASE_URL sur SQLite â€” la production exige PostgreSQL.")
        if is_prod and any(host in settings.ALLOWED_ORIGINS for host in ("localhost", "127.0.0.1")):
            warnings.append("ALLOWED_ORIGINS contient encore localhost/127.0.0.1 en production.")
    else:
        warnings.append(f"ENVIRONMENT='{env}' (â‰  production/cabinet) : invariants prod non bloquants.")

    # --- Capsule IA / tÃ©lÃ©mÃ©trie : confirmer l'opt-in explicite ---
    if settings.TELEMETRY_ENABLED:
        warnings.append("TELEMETRY_ENABLED=True â€” remontÃ©e cloud ACTIVE (opt-in confirmÃ© ?).")

    # --- Rapport ---
    print("=" * 64)
    print("S9 â€” PROD SAFETY CHECK (lecture seule)")
    print("=" * 64)
    print(f"ENVIRONMENT : {env}")
    print(f"DEBUG       : {settings.DEBUG}")
    print(f"DB          : {'sqlite' if settings.DATABASE_URL.lower().startswith('sqlite') else 'postgresql/autre'}")
    print("-" * 64)
    for w in warnings:
        print(f"  [WARN]  {w}")
    for e in errors:
        print(f"  [ERROR] {e}")
    print("-" * 64)
    if errors:
        print(f"RESULTAT : ECHEC â€” {len(errors)} erreur(s) bloquante(s).")
        return 1
    print(f"RESULTAT : OK â€” 0 erreur ({len(warnings)} avertissement(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

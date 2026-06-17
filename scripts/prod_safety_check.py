#!/usr/bin/env python
"""
S9 — Vérificateur de durcissement PRODUCTION (lecture seule, rejouable).

Contrôle la cohérence de la configuration AVANT déploiement. Ne touche AUCUNE
donnée : lit uniquement `backend.config.settings`. À lancer avec la config cible
(ex: `ENVIRONMENT=production python scripts/prod_safety_check.py`).

Sortie : code 0 si aucune ERREUR ; code 1 si au moins une ERREUR bloquante.
Les WARNINGs n'échouent pas le check mais doivent être revus par l'opérateur.
"""
import sys

# Permet l'exécution depuis la racine du repo (`python scripts/prod_safety_check.py`)
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

    # --- SECRET_KEY (toujours appliqué) ---
    if settings.SECRET_KEY in WEAK_KEYS or len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY faible/par défaut (< 32 caractères ou valeur connue).")

    # --- CORS (toujours appliqué : '*' + credentials = faille) ---
    if "*" in settings.ALLOWED_ORIGINS:
        errors.append("ALLOWED_ORIGINS contient un wildcard '*' (incompatible allow_credentials).")

    # --- Invariants spécifiques production ---
    if is_prod:
        if settings.DEBUG:
            errors.append("DEBUG=True interdit en production.")
        if settings.DATABASE_URL.strip().lower().startswith("sqlite"):
            errors.append("DATABASE_URL sur SQLite — la production exige PostgreSQL.")
        if any(host in settings.ALLOWED_ORIGINS for host in ("localhost", "127.0.0.1")):
            warnings.append("ALLOWED_ORIGINS contient encore localhost/127.0.0.1 en production.")
    else:
        warnings.append(f"ENVIRONMENT='{env}' (≠ production) : invariants prod non bloquants.")

    # --- Capsule IA / télémétrie : confirmer l'opt-in explicite ---
    if settings.TELEMETRY_ENABLED:
        warnings.append("TELEMETRY_ENABLED=True — remontée cloud ACTIVE (opt-in confirmé ?).")
    if settings.CLOUD_AI_ENABLED:
        warnings.append("CLOUD_AI_ENABLED=True — sortie IA cloud ACTIVE (opt-in confirmé ?).")
    if settings.CLOUD_AI_ENABLED and not settings.GEMINI_API_KEY:
        warnings.append("CLOUD_AI_ENABLED=True mais GEMINI_API_KEY vide.")

    # --- Rapport ---
    print("=" * 64)
    print("S9 — PROD SAFETY CHECK (lecture seule)")
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
        print(f"RESULTAT : ECHEC — {len(errors)} erreur(s) bloquante(s).")
        return 1
    print(f"RESULTAT : OK — 0 erreur ({len(warnings)} avertissement(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Digital Crown — Guide Claude Code

Digital Crown est une application **on-premise / local-first**. Le runtime principal vit sur le poste du cabinet ou son LAN. Firebase sert à l'identité/licence et services associés ; les données métier restent sous l'autorité du backend local.

> **Ordre de lecture obligatoire**
>
> 1. `STATE.md`
> 2. `CLAUDE.md`
> 3. règle applicable sous `.claude/rules/`
> 4. `SKILL.md` du domaine
> 5. agent spécialisé éventuel sous `.claude/agents/`
> 6. code, tests et runbooks référencés
>
> L'ancienne version détaillée reste disponible dans l'historique Git à `master@f6dd36e`.

## Architecture courante

- Backend : FastAPI + SQLAlchemy.
- Frontend : React 19 + Vite + TypeScript + Zustand.
- Mobile : PWA/Capacitor appairée au cabinet, réseau local, cache/offline.
- Automatisation : modèles locaux et moteurs déterministes.
- LLM : aucune dépendance LLM requise dans l'architecture courante.
- Packaging : PyInstaller + Inno Setup.

### Environnements

- `development` / `local` / `test` : développement/test.
- `cabinet` : production-like local ; `DEBUG` interdit, CORS wildcard interdit, SQLite/SQLCipher autorisé.
- `production` : mêmes exigences, PostgreSQL obligatoire.

Source : `backend/main.py::validate_environment_invariants()`.

## Routage des skills

- Choisir le skill par sémantique de tâche, pas par simple mot-clé.
- Lire intégralement le `SKILL.md` avant action.
- Respecter `context`, `allowed-tools`, `Forbidden`, workflow et `Output contract`.
- Si le skill impose un audit read-only, ne rien modifier pendant ce lot.
- Effectuer ensuite le handoff vers le skill/agent d'implémentation prévu.
- Les contrats détaillés restent dans `.claude/rules/`, `.claude/skills/` et `.claude/agents/` ; ne pas les dupliquer ici.

### Skills vérifiés le 13/08/2026

- `.claude/skills/audit-prescription-flow/SKILL.md`
- `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md`
- `.claude/skills/audit-panoramic-report-pipeline/SKILL.md`
- `.claude/skills/validate-cephalo-pipeline/SKILL.md`

Tous imposent un mode **read-only** pour leur phase d'audit/validation.

## Règles absolues d'ingénierie

- Ne jamais perdre, réinitialiser ou reseeder une vraie donnée utilisateur.
- Jamais de seed/demo sur une DB cabinet.
- Backup avant restore/migration à risque.
- Jamais de restore sur DB principale sans confirmation explicite.
- Toute opération de test qui écrit doit prouver qu'elle cible l'environnement isolé prévu.
- Toujours dériver le cabinet depuis l'identité backend, jamais depuis une valeur client non fiable.
- Médias sensibles : routes authentifiées et tenant-aware.
- Ne jamais logger secrets, tokens, mots de passe ou master key.
- Ne jamais inventer une donnée manquante ni masquer une incertitude.
- Tests verts ne valent pas certification du domaine.

## Pièges opérationnels

### Runtime réel

- Le dépôt de travail n'est pas le runtime cabinet.
- Ne jamais utiliser un process auto-reload contre le runtime réel.
- Utiliser les scripts de release immuable sous `backend/scripts/`.
- Un build de test ne doit jamais écraser un frontend réellement servi.

### Environnement de test

- Une variable shell isolée ne suffit pas si `load_backend_env()` recharge un fichier local.
- Pour un test d'écriture isolé, utiliser `DIGITALCROWN_ENV_FILE` vers un fichier dédié et vérifier explicitement la DB réellement résolue avant mutation.

### Database / migrations

- Ne pas supposer qu'Alembic s'exécute automatiquement.
- Lire le chemin runtime courant avant toute migration.
- Ne jamais ouvrir une DB SQLCipher avec `sqlite3` standard.
- Backup PostgreSQL via `pg_dump`.

### Backup

- Les backups planifiés utilisent une release immuable dédiée.
- Ne pas créer une implémentation parallèle si un service existant couvre déjà le besoin.
- Une réussite n'est prouvée qu'après vérification de l'artefact et du restore attendu selon le runbook.

### Packaging

- Conserver les hidden imports runtime requis dans `DigitalCrown.spec`.
- Ne jamais embarquer un `.env` contenant des secrets.
- `console=False` exige une journalisation fichier fiable.
- Le bootstrap first-run doit précéder les imports qui figent les settings.

## Documents / PDF

- Réutiliser les helpers typographiques et de layout existants.
- Une preview doit être read-only sur l'état métier.
- Après modification d'une route ou d'un générateur, faire un smoke réel/rehearsal adapté au risque.

## Tests et CI

### Backend

```bash
python -m pytest backend/tests -q
python scripts/prod_safety_check.py
```

### Frontend

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

### CI actuelle

`.github/workflows/ci.yml` contient :

- backend : install + prod safety check + pytest ;
- frontend : `npm ci` + tests + build ;
- garde production négatif.

Ne déclarer aucun head certifié sans preuve du run correspondant.

## Runbooks utiles

- `docs/CABINET_ONPREM_GUIDE.md`
- `docs/PREPROD_RUNBOOK.md`
- `docs/PATIENT_DATA_ROLLBACK.md`
- `STATE.md`

## Workflow par lot

1. Lire `STATE.md`.
2. Lire `CLAUDE.md`, la règle et le skill du domaine.
3. Cartographier scope et invariants.
4. Audit read-only d'abord lorsque le skill l'impose.
5. Implémenter dans un lot distinct.
6. Tests ciblés puis régression proportionnée au risque.
7. Smoke/rehearsal lorsque nécessaire.
8. Review indépendante si requise.
9. Mettre à jour les canoniques et vérifier leur cohérence.
10. PR/merge/certification seulement après preuves.

**Dernière révision canonique : 13 août 2026.**

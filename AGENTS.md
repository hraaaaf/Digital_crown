# Digital Crown — Guide Codex

Digital Crown est une application de gestion de cabinet **on-premise / local-first**. Le runtime principal vit sur le poste du cabinet ou son LAN. Firebase sert à l'identité/licence et services associés ; les données métier restent sous l'autorité du backend local.

> **Ordre de lecture obligatoire**
>
> 1. `STATE.md`
> 2. `AGENTS.md`
> 3. règle de domaine sous `.claude/rules/`
> 4. `SKILL.md` correspondant au scope
> 5. code, tests, sources ou runbooks référencés
>
> L'ancienne version détaillée de ce guide reste disponible dans l'historique Git à `master@f6dd36e`.

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

## Règles absolues

### Données et isolation

- Ne jamais perdre, réinitialiser ou reseeder une vraie donnée utilisateur.
- Jamais de seed/demo sur une DB cabinet.
- Backup avant restore/migration à risque.
- Jamais de restore sur DB principale sans confirmation explicite.
- Toute opération de test qui écrit doit prouver qu'elle cible l'environnement isolé prévu.
- Toujours dériver le cabinet via `current_user.get_employer_id()` ; jamais depuis une valeur client non fiable.
- Toute route patient-scopée doit appliquer le guard d'accès backend approprié.
- Médias sensibles : routes authentifiées et tenant-aware, jamais accès statique public.
- Ne jamais logger secrets, tokens, mots de passe ou master key.

### Domaines scientifiques / cliniques

Pour tout scope clinique ou scientifique :

- lire `.claude/rules/scientific-engineering.md` ;
- lire le `SKILL.md` correspondant ;
- respecter strictement son mode read-only ou implementation ;
- ne pas inventer de donnée manquante ;
- ne pas introduire de constante non sourcée ;
- conserver provenance, versions et états explicites ;
- tests verts ne valent pas validation scientifique ;
- review indépendante avant merge lorsque le skill l'exige.

## Skills à router explicitement

- Prescription : `.claude/skills/audit-prescription-flow/SKILL.md`
- Diagnostic : `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md`
- Panoramique : `.claude/skills/audit-panoramic-report-pipeline/SKILL.md`
- Céphalométrie : `.claude/skills/validate-cephalo-pipeline/SKILL.md`

Les skills d'audit sont **read-only**. Un finding se corrige dans un lot séparé.

## Pièges opérationnels

### Runtime réel

- Le dépôt de travail n'est pas le runtime cabinet.
- Ne jamais lancer un process auto-reload contre le runtime réel.
- Utiliser les scripts de release immuable sous `backend/scripts/` pour les opérations cabinet.
- Un build de test ne doit jamais écraser un frontend réellement servi.

### Environnement de test

- Exporter seulement `DATABASE_URL` dans le shell ne garantit pas l'isolation si un fichier d'environnement local est rechargé.
- Pour un test d'écriture isolé, utiliser `DIGITALCROWN_ENV_FILE` vers un fichier dédié puis vérifier explicitement le `DATABASE_URL` réellement résolu.

### Database / migrations

- Ne pas supposer qu'Alembic s'exécute automatiquement.
- Lire le chemin runtime courant avant toute migration.
- Ne jamais ouvrir une DB SQLCipher avec `sqlite3` standard.
- Backup PostgreSQL via `pg_dump`, jamais par heuristique de chemin fichier.

### Backup

- Backup DB seul ne vaut pas forcément backup complet.
- Les backups planifiés utilisent une release immuable dédiée ; ne pas dupliquer la logique dans un script ad hoc.
- Une réussite n'est prouvée qu'après vérification de l'artefact et du restore attendu selon le runbook.

### Packaging

- Conserver les hidden imports runtime nécessaires dans `DigitalCrown.spec`.
- Ne jamais embarquer un `.env` contenant des secrets.
- `console=False` exige une journalisation fichier fiable.
- Le bootstrap first-run doit précéder les imports qui figent les settings.

### Modèles

- `backend/ai_models/` contient aussi des dépôts de recherche historiques.
- Ne pas embarquer un dépôt complet si seuls certains artefacts runtime sont nécessaires.
- Avant suppression ou packaging, vérifier les références runtime réelles.

## Documents / PDF

- Réutiliser les helpers typographiques et de layout existants.
- Éviter les règles de présentation ad hoc.
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

1. Lire `STATE.md` et le skill pertinent.
2. Cartographier scope et invariants.
3. Audit read-only d'abord lorsque le skill l'impose.
4. Implémenter dans un lot distinct.
5. Tests ciblés puis régression proportionnée au risque.
6. Smoke/rehearsal lorsque nécessaire.
7. Review indépendante si requise.
8. Mettre à jour les canoniques.
9. Vérifier leur cohérence.
10. PR/merge/certification seulement après preuves.

**Dernière révision canonique : 13 août 2026.**

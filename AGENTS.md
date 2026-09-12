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

### Installation / release cabinet — INVARIANT ABSOLU

Lire `docs/CABINET_CERTIFIED_RELEASE_POLICY.md` avant toute opération de build, packaging, installation, activation ou mise à jour cabinet.

- **Interdit d'installer ou démarrer `master`, `HEAD`, une branche, un tag ou un working tree.**
- `CODE_CERTIFIED` = code exact-SHA attesté par GitHub/Sigstore. **Ce niveau n'est PAS installable.**
- `INSTALLABLE_CERTIFIED` = `CODE_CERTIFIED` + bundle d'assets runtime certifié pour le même SHA + composition finale revalidée.
- **Seul `INSTALLABLE_CERTIFIED` est autorisé à atteindre un cabinet réel, PyInstaller ou Inno Setup.**
- Le CODE SHA nouvellement certifiable doit être le HEAD courant exact de `master`, 40 caractères.
- Toute release universelle couvre simultanément `BASIC`, `GOLD`, `ELITE` ; jamais trois forks/binaires divergents.
- Les noms release `BASIC/GOLD/ELITE` ne renomment pas implicitement les enums de licence historiques ; toute migration commerciale reste un lot séparé.
- `create_release.ps1` ne doit jamais recopier/reconstruire le working tree. Il doit vérifier hashes + provenance GitHub/Sigstore puis composer avec les assets runtime.
- La sélection des assets de `DigitalCrown.spec` doit rester dérivée de `backend/runtime_asset_certification.py`, jamais dupliquée à la main.
- `run_real_backend.ps1` doit rester fail-closed sur code + provenance + assets **avant** lecture de la config cabinet.
- `run.py` doit vérifier `INSTALLABLE_CERTIFIED` avant le first boot.
- Un merge sur `master` **ne signifie jamais installable**.
- Toute évolution pouvant toucher DB, migrations, patients, documents, médias, startup, seeds, paths, restore/backup, tenant filtering ou installer exige un rehearsal sur copie fraîche des données réelles avant certification destinée à un cabinet existant.
- Il est interdit de supprimer, neutraliser, path-filter ou contourner ces gates pour « débloquer » une release.

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
- Utiliser uniquement une release `INSTALLABLE_CERTIFIED` composée via les scripts sous `backend/scripts/`.
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
- Le bootstrap first-run doit précéder les imports qui figent les settings, mais **la vérification `INSTALLABLE_CERTIFIED` doit précéder le bootstrap first-run**.

### Modèles

- `backend/ai_models/` contient aussi des dépôts de recherche historiques.
- Ne pas embarquer un dépôt complet si seuls certains artefacts runtime sont nécessaires.
- La certification d'intégrité des assets ne vaut pas validation scientifique.
- Un asset scientifiquement épinglé dans `backend/scientific_assets.json` doit matcher path + taille + SHA-256 ; sinon release refusée.
- Les assets non encore épinglés restent explicitement déclarés comme tels ; ne jamais prétendre qu'ils sont scientifiquement certifiés.

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

`.github/workflows/cabinet-upgrade-postgres-cert.yml` est un gate PR global sans filtre de chemin et verrouille PostgreSQL 18 + préservation + politique de release.

Ne déclarer aucun SHA `CODE_CERTIFIED` sans preuve du run + attestation correspondants. Ne déclarer aucune version **installable** sans certificat final `INSTALLABLE_CERTIFIED` vérifié.

## Runbooks utiles

- `docs/CABINET_CERTIFIED_RELEASE_POLICY.md`
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
11. Pour distribution cabinet : certifier le HEAD master exact en `CODE_CERTIFIED`.
12. Certifier les assets runtime pour ce même SHA, composer en `INSTALLABLE_CERTIFIED`, puis seulement construire/activer.

**Dernière révision canonique : 12 septembre 2026.**

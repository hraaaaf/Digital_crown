# Digital Crown — Guide Codex

Digital Crown est un **cockpit clinique et administratif pour cabinet dentaire**, on-premise / local-first. Le runtime principal vit sur le poste du cabinet ou son LAN. Firebase sert à l'identité/licence et services associés ; les données métier restent sous l'autorité du backend local.

## Frontière documentaire — README client vs engineering

`README.md` est un **document client-facing** destiné au dossier remis au cabinet utilisateur. Il n'est jamais une source d'autorité technique ou d'exécution.

Règles obligatoires :

- `README.md` doit rester lisible par un praticien et son équipe, avec un langage simple mais précis ;
- il présente le produit réel, ses bénéfices, ses modules, son cadre d'utilisation, la sécurité au niveau client, la prise en main et les fonctions en cours de construction ;
- il ne doit pas contenir de SHA, PR, run CI, branches, dépendances internes, détails de certification ou instructions d'agent ;
- toute affirmation du README doit être vérifiée contre le code courant et les sources canoniques avant modification ;
- la roadmap V1, `STATE.md`, les audits, règles et runbooks restent les sources d'autorité engineering ;
- une fonction future peut être présentée comme **« en cours de construction »** uniquement si cette qualification est factuellement vraie et tracée dans la roadmap/compas produit ; ne jamais utiliser ce wording pour masquer une panne, une régression ou une fonction retirée ;
- les fonctions V1 livrées et les fonctions futures doivent être séparées sans ambiguïté ;
- les limites cliniques doivent être formulées clairement : assistance ≠ diagnostic autonome, mesure ≠ interprétation, absence de donnée ≠ donnée inventée ;
- les captures client doivent provenir d'écrans réels ou de preuves visuelles retenues ; ne jamais présenter un mockup comme une fonction livrée ;
- `AGENTS.md` et la documentation engineering ne doivent jamais être simplifiés au point de perdre les invariants de sécurité, certification ou gouvernance pour s'aligner sur le ton client du README.

> **Ordre de lecture obligatoire**
>
> 1. `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`
> 2. `STATE.md`
> 3. `AGENTS.md`
> 4. `.claude/rules/execution-scoring-verification.md`
> 5. règle de domaine sous `.claude/rules/`
> 6. `SKILL.md` correspondant au scope
> 7. code, tests, sources ou runbooks référencés
>
> L'ancienne version détaillée de ce guide reste disponible dans l'historique Git à `master@f6dd36e`.

## VERROU V1 — AUTORITÉ D'EXÉCUTION ABSOLUE

Jusqu'à ce que `V1_OPERATIONAL` soit explicitement enregistré dans `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md` :

- ce fichier est **la seule roadmap autorisée** ;
- un chantier, lot, feature, refactor, cleanup, recherche implémentée, merge, release ou déploiement hors du lot V1 actuellement déverrouillé doit être **refusé** ;
- seules les corrections, tests, preuves et mises à jour documentaires strictement nécessaires pour faire passer les gates du lot courant sont autorisées ;
- les PR ouvertes appartenant à des lots ultérieurs restent parkées et ne peuvent ni autoriser du travail ni être mergées hors séquence ;
- aucun autre `ROADMAP`, `PLAN`, `HANDOVER`, `BACKLOG`, `OBJECTIVE` ou document historique ne peut modifier l'ordre, le scope ou déverrouiller un lot ;
- un lot N+1 ne démarre qu'après closeout documenté du lot N avec Goal atteint, Success observable, Proof capturée, CI/tests requis verts et merge/post-merge terminé si applicable ;
- aucune mutation cabinet/production n'est autorisée avant le lot final de mise à jour cabinet et validation humaine explicite ;
- aucun déploiement Vercel n'est autorisé par ce verrou.

En cas de conflit, `DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md` prévaut.

## Architecture courante

- Backend : FastAPI + SQLAlchemy.
- Frontend : React 19 + Vite + TypeScript + Zustand.
- Mobile : PWA appairée au cabinet, réseau local, cache/offline ; tout wrapper natif futur reste un scope séparé tant qu'il n'est pas présent et certifié.
- Automatisation : modèles locaux et moteurs déterministes.
- LLM : aucune dépendance LLM requise dans l'architecture courante.
- Packaging : PyInstaller + Inno Setup.

### Environnements

- `development` / `local` / `test` : développement/test.
- `cabinet` : production-like local ; `DEBUG` interdit, CORS wildcard interdit, SQLite/SQLCipher autorisé.
- `production` : mêmes exigences, PostgreSQL obligatoire.

Source : `backend/main.py::validate_environment_invariants()`.

## Règles absolues

### Scoring d'exécution et vérification

Lire et appliquer **à chaque étape matérielle** `.claude/rules/execution-scoring-verification.md`.

- produire `EXECUTION_SCORE /10` puis `ADVERSARIAL_SCORE /10` ;
- retenir **le minimum**, jamais une moyenne ;
- tout écart `> 0.5` impose investigation, correction si possible, puis rescoring ;
- auto-revue du même agent : plafond `9.4/10` ; `9.5+` exige une vraie revue indépendante ;
- preuve/gate requis manquant ou rouge : max `7.9/10` ; régression : max `6.9/10` ; blocker sécurité/privacy/data/claim clinique : max `5.9/10` + `BLOCKED` ;
- UI sans vraie comparaison `Target ↔ Render` : fidélité visuelle max `7.5/10` ; une dimension critique faible ne peut jamais être masquée par une moyenne ;
- un lot n'est `VERIFIED` qu'avec `RETAINED_SCORE >= 9.0/10`, tous les gates binaires applicables verts et une **Perfection Pass finale** terminée.

Le score est une couche de preuve supplémentaire : il ne remplace jamais CI, rehearsal, validation humaine, review scientifique, sécurité ou politique de release.

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

`.github/workflows/ci.yml` contient backend install + prod safety check + pytest, frontend `npm ci` + tests + build, et garde production négatif.

`.github/workflows/cabinet-upgrade-postgres-cert.yml` est un gate PR global sans filtre de chemin et verrouille PostgreSQL 18 + préservation + politique de release.

Ne déclarer aucun SHA `CODE_CERTIFIED` sans preuve du run + attestation correspondants. Ne déclarer aucune version installable sans certificat final `INSTALLABLE_CERTIFIED` vérifié.

## Runbooks utiles

- `docs/CABINET_CERTIFIED_RELEASE_POLICY.md`
- `docs/CABINET_ONPREM_GUIDE.md`
- `docs/PREPROD_RUNBOOK.md`
- `docs/PATIENT_DATA_ROLLBACK.md`
- `STATE.md`

## Workflow par lot

1. Lire `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`, puis `STATE.md`, `.claude/rules/execution-scoring-verification.md` et le skill pertinent.
2. Vérifier que le scope demandé appartient au **lot V1 actuellement déverrouillé** ; sinon refuser le chantier.
3. Cartographier scope, invariants et gates binaires applicables.
4. Audit read-only d'abord lorsque le skill l'impose.
5. Implémenter uniquement le scope autorisé par le lot courant.
6. Après chaque étape matérielle : preuve + `EXECUTION_SCORE` + `ADVERSARIAL_SCORE` + minimum retenu ; investiguer tout écart `> 0.5`.
7. Tests ciblés puis régression proportionnée au risque.
8. Smoke/rehearsal lorsque nécessaire.
9. Review indépendante si requise, notamment pour toute revendication `>= 9.5/10`.
10. Mettre à jour le fichier canonique unique et vérifier sa cohérence.
11. Si le score atteint `9.0+`, exécuter la **Perfection Pass finale**, corriger les faiblesses améliorables, rerun les preuves impactées et rescorrer.
12. Ne marquer `VERIFIED` qu'avec score retenu `>= 9.0/10` **et** tous les gates binaires applicables verts.
13. PR/merge/certification seulement après preuves et gates satisfaits.
14. Pour distribution cabinet : certifier le HEAD master exact en `CODE_CERTIFIED`.
15. Certifier les assets runtime pour ce même SHA, composer en `INSTALLABLE_CERTIFIED`, puis seulement construire/activer.

**Dernière révision canonique : 20 septembre 2026 — séparation README client / documentation engineering verrouillée ; verrou V1 consolidé actif.**

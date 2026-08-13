# Architecture — Digital Crown

> Architecture canonique conceptuelle.
>
> État courant et blockers : `STATE.md`.
> Arborescence exacte : Git au commit audité.
>
> Dernière révision : **13 août 2026**.

## Positionnement

Digital Crown est une application **on-premise / local-first** exécutée sur le poste du cabinet ou son LAN.

Firebase sert à l'identité/licence et services associés. Le backend local reste l'autorité métier.

## Stack

| Couche | Technologie / rôle |
|---|---|
| Backend | FastAPI, Python, SQLAlchemy |
| Frontend | React 19, TypeScript, Vite, Zustand, Tailwind, Framer Motion |
| Mobile | PWA + Capacitor, cache/offline, appairage LAN |
| DB cabinet solo | SQLite/SQLCipher lorsque le mode `cabinet` le permet |
| DB production serveur | PostgreSQL 15+ |
| Documents | ReportLab + helpers internes |
| Automatisation | modèles locaux + moteurs déterministes |
| Auth / licence | JWT + services Firebase associés |
| Packaging | PyInstaller + Inno Setup |
| CI | GitHub Actions : backend, frontend, garde production |

Aucune dépendance LLM n'est requise dans l'architecture courante.

## Environnements

Source de vérité : `backend/main.py::validate_environment_invariants()`.

### development / local / test

Développement et tests. Toujours vérifier explicitement la configuration réellement résolue avant une opération d'écriture.

### cabinet

- production-like local ;
- `DEBUG` interdit ;
- CORS wildcard interdit ;
- SQLite/SQLCipher autorisé.

### production

- exigences production ;
- PostgreSQL obligatoire ;
- SQLite refusé.

## Frontières d'autorité

### Backend

Le backend décide :

- identité applicative ;
- isolation ;
- permissions ;
- validation métier ;
- écritures DB ;
- archivage ;
- génération de documents ;
- services métier.

### Frontend

Le frontend est un client non fiable :

- il ne définit pas l'isolation ;
- il ne constitue jamais la seule barrière d'autorisation ;
- ses permissions doivent rester cohérentes avec le backend.

### Mobile

Le mobile possède une surface de sécurité distincte :

- appairage ;
- credentials ;
- stockage local ;
- offline queue ;
- révocation.

Le chiffrement du transport ne suffit pas à garantir la sécurité du stockage local.

## Domaines applicatifs

Le repository couvre notamment :

- dossiers et suivi ;
- agenda / frontdesk ;
- parcours longitudinal ;
- documents / archives ;
- finance ;
- équipe ;
- catalogue ;
- laboratoire ;
- stock / partenaires ;
- analytics ;
- paramètres ;
- audit / backup ;
- imagerie et calculs avancés ;
- automatisations et alertes ;
- compagnon mobile.

L'existence d'un ancien fichier dans le dépôt ne signifie pas qu'il appartient au runtime actif. Toujours tracer imports, routes et appels avant de le considérer comme actif.

## Sécurité structurelle

- L'autorité d'isolation vient de l'identité backend, jamais d'une valeur client non fiable.
- Les ressources sensibles sont servies via des routes authentifiées.
- Protection path traversal sur les chemins de fichiers.
- Une absence de mécanisme de sécurité attendu doit produire un état explicite, pas un succès implicite.
- Secrets et master keys ne sont jamais journalisés.

## Database / runtime

- Le dépôt de travail n'est pas le runtime cabinet.
- Le runtime réel utilise des releases immuables.
- Ne pas supposer qu'Alembic s'exécute automatiquement ; lire le chemin courant.
- Ne jamais ouvrir une base SQLCipher avec `sqlite3` standard.
- PostgreSQL se sauvegarde via `pg_dump`.

## Backup

- Les backups planifiés utilisent une release dédiée.
- Éviter toute duplication ad hoc d'une logique déjà centralisée.
- Une réussite n'est prouvée qu'après vérification de l'artefact et du restore attendu selon le runbook.

Runbooks :

- `docs/CABINET_ONPREM_GUIDE.md`
- `docs/PREPROD_RUNBOOK.md`
- `docs/PATIENT_DATA_ROLLBACK.md`

## Packaging

- `DigitalCrown.spec` : build PyInstaller.
- `installer/DigitalCrown.iss` : installeur Windows.
- Ne jamais embarquer un `.env` contenant des secrets.
- `console=False` exige une journalisation fichier fiable.
- Le bootstrap first-run doit précéder les imports qui figent les settings.

## Tests / CI

`.github/workflows/ci.yml` contient actuellement :

- backend : installation + prod safety check + pytest ;
- frontend : `npm ci` + tests + build ;
- garde production négatif.

Aucun head n'est déclaré certifié sans preuve du run correspondant.

## Gouvernance

Lire avant action :

1. `STATE.md`
2. `AGENTS.md` ou `CLAUDE.md`
3. règle applicable sous `.claude/rules/`
4. `SKILL.md` correspondant au domaine
5. agent spécialisé éventuel
6. code, tests et runbooks référencés

Les audits marqués read-only restent read-only. Les correctifs sont des lots séparés.

## Sources de vérité

- État / blockers / prochaine action : `STATE.md`
- Architecture : `ARCHITECTURE.md`
- Guide Codex : `AGENTS.md`
- Guide Claude : `CLAUDE.md`
- Présentation projet : `README.md`
- Règles spécialisées : `.claude/rules/` et `.claude/skills/`
- Arborescence exacte : Git au commit audité

Ne jamais laisser une documentation historique contredire silencieusement le code courant : corriger, archiver ou marquer explicitement le document comme snapshot.

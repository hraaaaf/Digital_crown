# STATE — DigitalCrown

> Fichier de reprise canonique. Historique pré-audit : `docs/archive/STATE_2026-07-21.md`.

# État canonique manuel — 2026-08-14

## Baseline vérifiée

- Repository : `hraaaaf/Digital_crown`
- `master` après merge P0-1 : `8b442dfd613a608ac2e84f0a1690ba213aecfd5e`
- PR P0-1 : `#5` — MERGED
- Head candidat certifié avant merge : `9cb4b7f4b26260e7e9176299a44a9db0247c48bb`
- CI exact-head : run `31752891471`
- Backend : **2459 passed, 7 skipped, 4 warnings, 0 failed**
- Frontend tests : **SUCCESS**
- Frontend build : **SUCCESS**
- Garde production négative : **SUCCESS**

## Doctrine produit confirmée

- Application **on-premise / local-first**.
- Firebase : identité/licence, jamais source de vérité des dossiers patients.
- Architecture courante : modèles locaux + moteurs déterministes ; aucun LLM requis.
- Donnée patient requise mais absente = inconnue/non-évaluable ; jamais inventée.
- `tests green != validation scientifique`.
- Dans ce projet, `review` signifie par défaut **double-check complet par l’agent**, sauf demande explicite d’un reviewer externe.

## P0 — Safety & Integrity

### P0-1 — PRESCRIPTION-MISSING-DATA-FAIL-CLOSED — CLOSED ✅

Objectif : empêcher toute valeur patient synthétique/estimée de déclencher un calcul patient-spécifique lorsqu’une donnée requise manque.

Implémentation intégrée :
- garde backend explicite `evaluable/non_evaluable` ;
- âge absent reste `None` ;
- poids absent n’est jamais synthétisé ;
- antécédents absents restent explicitement incomplets ;
- enfant sans contexte sûr ne passe pas dans le chemin pédiatrique legacy ;
- plan non évaluable = zéro ligne automatique ;
- `PrescriptionGuideModal` exige un poids explicite pour l’automatisme pédiatrique ;
- `estimateWeightFromAge()` est neutralisé ;
- top-level `assessment.age` est masqué lorsque le contexte n’est pas évaluable ;
- tests backend/frontend missing-data ajoutés.

Double-check final avant merge :
- restauration de tests `clinical_rules_engine` + `habits_engine` supprimés accidentellement ;
- test honoraires rendu déterministe, sans assertion permissive `409 ou 422` ;
- diff final : 16 fichiers, aucun fichier parasite ;
- couverture backend finale supérieure au run précédent : 2459 tests passés.

Limite explicite :
- ce lot **ne valide pas scientifiquement** les constantes thérapeutiques/doses historiques du moteur legacy ;
- ces constantes restent une dette scientifique distincte.

Dette CI non bloquante :
- la CI force `httpx==0.27.2` pour compatibilité Starlette/TestClient ;
- cela entre en conflit déclaré avec `firebase-admin 7.5.0` et `ultralytics-platform 0.1.4`, qui demandent `httpx>=0.28` ;
- correction durable à traiter séparément : upgrade FastAPI/Starlette ou isolation des dépendances de test.

### P0-2 — CMO-NON-PRESCRIPTIVE-BOUNDARY — ACTIVE

Le service de synthèse clinique peut produire des conclusions trop prescriptives à partir de signaux textuels.

Frontière cible : **signal + preuve + incertitude + validation praticien**, sans conclusion thérapeutique autonome.

### P0-3 — SQLCIPHER-FAIL-CLOSED

Le démarrage local peut continuer si le driver de chiffrement attendu est indisponible. Un environnement exigeant le chiffrement ne doit jamais considérer ce cas comme sûr.

### P0-4 — PARTIAL-PAYMENT-NO-INFERENCE

Une écriture financière partielle peut être déduite automatiquement lorsque le montant exact manque. Toute écriture financière doit provenir d’un montant explicite.

### P0-5 — PRESCRIPTION-SAFETY-TENANT-GUARD

Une route patient-scopée de vérification prescription ne fait pas appliquer explicitement le guard tenant avant lecture du contexte patient.

### P0-6 — PREVIEW-MUST-BE-READ-ONLY

Un chemin de preview documentaire peut muter la base. Une preview doit conserver `count_before == count_after`.

## P1 — Hardening

- Secure Storage natif pour secrets/credentials mobiles longue durée.
- Revoir durée de vie et révocation des credentials mobiles.
- Whitelist Pydantic stricte pour les paramètres cabinet ; pas de mass assignment générique.
- Audit tenant exhaustif des routes patient-scopées.
- MIME + magic bytes systématiques sur uploads sensibles.
- Centraliser `hasAccess()` frontend.
- Quarantainer/supprimer les anciens moteurs non utilisés.

## P2 — Certification

- CI sur le head réellement candidat.
- Backend + frontend + build.
- Smoke live/rehearsal ciblé selon le risque.
- Audit visuel 390 / 768 / 1280 pour les lots UI concernés.
- Accessibilité clavier/ARIA sur contrôles custom.
- Validation scientifique céphalométrique source par source avant toute revendication autoritative.

## Skills scientifiques applicables

- `.claude/skills/audit-prescription-flow/SKILL.md`
- `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md`
- `.claude/skills/audit-panoramic-report-pipeline/SKILL.md`
- `.claude/skills/validate-cephalo-pipeline/SKILL.md`
- `.claude/rules/scientific-engineering.md`

## Lot actif

### LOT 2 — P0-2 CMO NON-PRESCRIPTIVE BOUNDARY — À AUDITER / CORRIGER

Prochaine action exacte : cartographier le service CMO/synthèse clinique actif, ses entrées, ses sorties, ses tests et les chemins où un signal textuel peut devenir une conclusion prescriptive ; définir ensuite le contrat fail-safe minimal avant modification.

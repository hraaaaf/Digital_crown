# STATE — DigitalCrown

> Fichier de reprise (handoff). **Lis-moi en premier** pour savoir où on en est.
> Le bloc AUTO ci-dessous est régénéré automatiquement à chaque fin de session : ne l'édite pas à la main.
> Les sections plus bas sont à toi (l'agent) : tiens-les à jour avant de t'arrêter.
>
> Historique canonique pré-audit conservé intégralement dans `docs/archive/STATE_2026-07-21.md`.

<!-- STATE:AUTO:START -->
## Dernière session (auto — ne pas éditer à la main)
- **Mis à jour :** 2026-07-21 10:39
- **Branche :** `master`
- **Worktree :** `C:/Users/lenovo/Documents/Cabinet/DigitalCrown`

### Fichiers touchés
- _(aucun fichier modifié détecté)_

### Dernières demandes
- _(rien à extraire)_
<!-- STATE:AUTO:END -->

# État canonique manuel — 2026-08-13

## Baseline vérifiée

- Repository : `hraaaaf/Digital_crown`
- Baseline auditée : `master@f6dd36eca196d614c2d81d1dd78d3f45e481323a`
- Baseline P0-1 avant correctif : `master@f01bab51595659e0fccb1fd89bd1a03b49d16316`
- Branche candidat : `fix/missing-data-guard-v2-2026-08-13`
- Candidat code+tests avant mise à jour de ce fichier : `73a5e2953e388e86287251e552c110421bcf0f5b`
- Aucun test ou run CI n'est déclaré réussi sans preuve d'exécution.

## Doctrine produit confirmée

- Application **on-premise / local-first**.
- Firebase : identité/licence et services associés, jamais source de vérité des dossiers patients.
- Architecture courante : modèles locaux + moteurs déterministes ; aucune dépendance LLM requise.
- Audits scientifiques = read-only ; correctifs = missions distinctes avec tests et review.
- Donnée manquante = inconnue/non-évaluable ; jamais valeur inventée.
- `tests green != validation scientifique`.

## P0 — Safety & Integrity

### P0-1 — PRESCRIPTION-MISSING-DATA-FAIL-CLOSED — IMPLEMENTED / NOT CERTIFIED

Audit initial : branche `audit/p0-1-prescription-missing-data-2026-08-13`, commit `e9d9f3a26395e19d933a074d74ba90195171a140`.

Human gate : principe fail-closed approuvé le 13/08/2026.

Correctif structurel implémenté sur `fix/missing-data-guard-v2-2026-08-13` :
- garde backend explicite `evaluable/non_evaluable` ;
- âge absent reste `None` ;
- poids absent n'est jamais synthétisé ;
- antécédents absents restent explicitement incomplets ;
- enfant sans poids structuré ne passe pas dans le moteur pédiatrique legacy ;
- plan non évaluable = zéro ligne automatique ;
- ancien service conservé dans `prescription_service_legacy.py` pour ne pas modifier silencieusement ses constantes ;
- `PrescriptionGuideModal` exige une donnée de poids explicite pour les automatismes pédiatriques ;
- `estimateWeightFromAge()` est neutralisé et ne fournit plus de valeur exploitable ;
- hook top-level `assessment.age` masqué lorsque l'évaluation n'est pas `evaluable`, afin de rendre inertes les adaptations patient-spécifiques du Studio legacy ;
- tests backend missing-data ajoutés ;
- tests frontend structurels missing-data ajoutés.

Contrôle statique au candidat `73a5e295...` :
- branche en avance de 9 commits sur `f01bab5`, derrière de 0 ;
- 8 fichiers code/tests dans le diff ;
- aucune migration DB ;
- aucun workflow modifié ;
- aucune donnée patient modifiée ;
- aucune constante scientifique volontairement revalidée ou remplacée dans ce lot.

Résidu connu :
- `PrescriptionAgenticStudio.tsx` contient encore du code legacy (dont anciennes valeurs littérales/adaptations locales), mais ses déclencheurs patient-spécifiques sont rendus inertes pour un contexte non évaluable par le garde backend + le GuideModal sûr. Nettoyage/quarantaine ultérieure recommandé après certification fonctionnelle.

### Certification P0-1 — BLOQUÉE EXTERNE

État réel : **NOT CERTIFIED / NOT MERGED**.

Preuves :
- aucun status check associé au candidat ;
- aucune exécution Actions visible sur les branches de certification ;
- l'intégration GitHub renvoie `403 Resource not accessible by integration` sur l'accès aux permissions Actions ;
- aucune PR n'a pu être créée via le connecteur dans cette session ;
- les tests ajoutés sont versionnés mais **non exécutés dans cette session**.

Interdiction : ne pas merger P0-1 sur `master` avant preuve d'exécution backend + frontend + build.

### P0-2 — CMO-NON-PRESCRIPTIVE-BOUNDARY

Le service de synthèse clinique peut produire des conclusions trop prescriptives à partir de signaux textuels. La frontière doit devenir : signal + preuve + incertitude + validation praticien.

### P0-3 — SQLCIPHER-FAIL-CLOSED

Le démarrage local peut continuer si le driver de chiffrement attendu est indisponible. Un environnement exigeant le chiffrement ne doit jamais considérer ce cas comme sûr.

### P0-4 — PARTIAL-PAYMENT-NO-INFERENCE

Une écriture financière partielle peut être déduite automatiquement lorsque le montant exact manque. Toute écriture financière doit provenir d'un montant explicite.

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

- Exécuter CI sur le head réellement candidat.
- Rejouer backend + frontend + build.
- Smoke live/rehearsal ciblé selon le risque.
- Audit visuel 390 / 768 / 1280 pour les lots UI concernés.
- Accessibilité clavier/ARIA sur contrôles custom.
- Finaliser validation scientifique céphalométrique source par source avant toute revendication autoritative.
- Vérifier cohérence README / AGENTS / CLAUDE / ARCHITECTURE après chaque gros lot.

## Skills scientifiques applicables

- `.claude/skills/audit-prescription-flow/SKILL.md`
- `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md`
- `.claude/skills/audit-panoramic-report-pipeline/SKILL.md`
- `.claude/skills/validate-cephalo-pipeline/SKILL.md`
- `.claude/rules/scientific-engineering.md`

## Lot canonique précédent — CLOSED

Intégré sur `master` le 13/08/2026 par fast-forward contrôlé depuis `audit/canonical-refresh-2026-08-13`.

- ✅ `README.md`, `STATE.md`, `AGENTS.md`, `CLAUDE.md`, `ARCHITECTURE.md` réalignés.
- ✅ ancien `STATE.md` archivé dans `docs/archive/STATE_2026-07-21.md`.
- ✅ aucun code/runtime/DB/workflow modifié par ce lot documentaire.

## LOT 1 — P0-1 audit — CLOSED

- ✅ route active cartographiée de l'UI au document ;
- ✅ missing-data/fallbacks backend et frontend identifiés ;
- ✅ propagation vers génération/archivage/habitudes identifiée ;
- ✅ tests existants et gaps recensés ;
- ✅ formulaire actif confirmé : `PrescriptionAgenticStudio` ;
- ✅ aucun code, règle, test, fixture ou donnée patient modifié pendant l'audit.

## Lot actif

### LOT 1B — PRESCRIPTION FAIL-CLOSED STRUCTURAL FIX — IMPLEMENTED / CERTIFICATION BLOCKED

Le correctif structurel est implémenté. Le lot ne peut pas être déclaré CLOSED tant que la régression exécutable n'est pas prouvée.

## Prochaine action exacte

Exécuter sur le head candidat final :

1. `python -m pytest backend/tests -q --maxfail=1`
2. dans `frontend/` : `npm test`
3. dans `frontend/` : `npm run build`
4. vérifier le diff exact-head et les tests P0-1 ciblés ;
5. corriger toute régression ;
6. recertifier ;
7. seulement après succès : PR/review, merge contrôlé vers `master`, contrôle post-merge et réalignement final des canoniques.

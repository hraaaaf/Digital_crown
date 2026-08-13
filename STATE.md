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
- Baseline LOT 1 : `master@c8669527c6eb9c5232afa4277b5cd4c387a862fd`
- Nature : audit statique/read-only. Aucun test ou run CI n'est déclaré réussi sans preuve d'exécution.

## Doctrine produit confirmée

- Application **on-premise / local-first**.
- Firebase : identité/licence et services associés, jamais source de vérité des dossiers patients.
- Architecture courante : modèles locaux + moteurs déterministes ; aucune dépendance LLM requise.
- Audits scientifiques = read-only ; correctifs = missions distinctes avec tests et review.
- Donnée manquante = inconnue/non-évaluable ; jamais valeur inventée.
- `tests green != validation scientifique`.

## Évaluation audit du 13/08/2026

- Qualité / ambition produit : **8,6 / 10**
- Readiness clinique/production : **6,6 / 10**
- Note globale audit : **7,7 / 10**

Ces notes sont une évaluation d'audit, pas un pourcentage de roadmap ni une certification de release.

## P0 — Safety & Integrity

### P0-1 — PRESCRIPTION-MISSING-DATA-FAIL-CLOSED — AUDIT CLOSED / BLOCKER CONFIRMED

Rapport détaillé versionné sur la branche `audit/p0-1-prescription-missing-data-2026-08-13`, commit `e9d9f3a26395e19d933a074d74ba90195171a140`.

Constats structurants confirmés :
- valeurs patient synthétiques/fallbacks dans le chemin de suggestion ;
- estimation frontend d'une donnée manquante pouvant influencer le guidage ;
- absence de source structurée de poids actuel dans le modèle Patient ;
- état d'antécédents manquant pouvant être confondu avec absence de signal ;
- logique métier dupliquée backend/frontend ;
- propagation possible vers document puis apprentissage d'habitudes ;
- tests missing-data/parité insuffisants.

**Décision :** LOT 1B doit rendre le flux fail-closed sans introduire de nouvelle constante scientifique.

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

## Skills scientifiques lus et applicables

- `.claude/skills/audit-prescription-flow/SKILL.md`
- `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md`
- `.claude/skills/audit-panoramic-report-pipeline/SKILL.md`
- `.claude/skills/validate-cephalo-pipeline/SKILL.md`
- `.claude/rules/scientific-engineering.md`

## Lot canonique — CLOSED

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

## Lot actif suivant

### LOT 1B — PRESCRIPTION FAIL-CLOSED STRUCTURAL FIX — À DÉMARRER

Objectif : supprimer toute utilisation métier d'une valeur patient inventée/estimée, introduire un état explicite `incomplete/non_evaluable`, rendre le backend autorité unique et empêcher la persistance/apprentissage d'une valeur non autoritative.

**Important :** ne pas modifier les constantes scientifiques existantes sans recherche de sources séparée.

## Prochaine action exacte

1. Lire l'agent/skill d'implémentation prescription.
2. Concevoir le contrat fail-closed minimal sans nouvelle constante scientifique.
3. Implémenter sur branche dédiée.
4. Ajouter tests ciblés missing-data + parité backend/frontend + persistance/document.
5. Exécuter régression proportionnée au risque.
6. Faire review scientifique indépendante.
7. Mettre à jour les canoniques puis certifier le head exact.

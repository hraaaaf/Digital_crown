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
- Audit : architecture, UX/UI, mobile, sécurité, proactivité, céphalométrie, panoramique, documents, prescriptions, comptabilité, paramètres et CI.
- Nature : **audit statique/read-only**. Aucun test ou run CI n'est déclaré réussi pour ce head sans preuve d'exécution.

## Doctrine produit confirmée

- Application **on-premise / local-first**.
- Firebase : identité/licence et services associés, jamais source de vérité des dossiers patients.
- Architecture clinique courante : modèles locaux + moteurs déterministes ; aucune dépendance LLM requise.
- Audits scientifiques = read-only ; correctifs = missions distinctes avec tests et review.
- `tests green != validation scientifique`.

## Évaluation audit du 13/08/2026

- Qualité / ambition produit : **8,6 / 10**
- Readiness clinique/production : **6,6 / 10**
- Note globale audit : **7,7 / 10**

Ces notes sont une évaluation d'audit, pas un pourcentage de roadmap ni une certification de release.

## Forces confirmées

- Couverture métier large : patient, agenda, Journey, documents, finance, équipe, mobile, imagerie, ortho, analytics.
- Compagnon mobile dédié avec appairage sécurisé et fonctionnement offline.
- Panoramique : séparation assistance machine / validation praticien.
- Céphalométrie : registre normatif versionné et refus des classifications ambiguës/non autoritatives.
- Proactivité : scheduler, déduplication, snooze, expiration, push et signaux cabinet/patient.
- CI versionnée avec backend, frontend et garde de configuration production.

## P0 — Safety & Integrity

### P0-1 — PRESCRIPTION-MISSING-DATA-FAIL-CLOSED

Une donnée patient manquante est remplacée par une valeur par défaut dans un chemin de suggestion clinique. Cette inférence doit être supprimée : donnée inconnue = état non-évaluable.

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
- Quarantainer/supprimer les anciens moteurs cliniques non utilisés.

## P2 — Certification

- Exécuter CI sur le head réellement candidat.
- Rejouer backend + frontend + build.
- Smoke live/rehearsal ciblé selon le risque.
- Audit visuel 390 / 768 / 1280 pour les lots UI concernés.
- Accessibilité clavier/ARIA sur contrôles custom.
- Finaliser validation scientifique céphalométrique source par source avant toute revendication autoritative.
- Vérifier cohérence README / AGENTS / CLAUDE / ARCHITECTURE après chaque gros lot.

## Skills scientifiques lus et applicables

- `.claude/skills/audit-prescription-flow/SKILL.md` : audit prescription read-only, puis handoff séparé pour correction.
- `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md` : audit états cliniques read-only ; pas de correction silencieuse.
- `.claude/skills/audit-panoramic-report-pipeline/SKILL.md` : audit upload → stockage → processing → review → report/PDF.
- `.claude/skills/validate-cephalo-pipeline/SKILL.md` : validation read-only de la chaîne céphalométrique et de ses invariants.
- `.claude/rules/scientific-engineering.md` : provenance, unités, contexte, missing-data, confirmation praticien et review indépendante obligatoires.

## Lot canonique en cours

Branche : `audit/canonical-refresh-2026-08-13`

- ✅ `README.md` aligné avec l'architecture locale déterministe actuelle.
- ✅ `STATE.md` rafraîchi avec l'audit du 13/08 et le backlog P0/P1/P2.
- ✅ ancien `STATE.md` archivé intégralement dans `docs/archive/STATE_2026-07-21.md`.
- ⏳ `AGENTS.md` : audit ligne par ligne sans perdre l'historique opérationnel.
- ⏳ `CLAUDE.md` : retirer les références Ollama/LLM obsolètes et aligner CI/architecture.
- ⏳ `ARCHITECTURE.md` : audit ciblé après AGENTS/CLAUDE.
- ⏳ Recertification documentaire avant PR/merge.

## Prochaine action exacte

1. Vérifier `AGENTS.md` sections Architecture / Tests / règles absolues.
2. Vérifier `CLAUDE.md` sur les mêmes dimensions.
3. Vérifier `ARCHITECTURE.md` sur les points impactés.
4. Comparer la branche à `f6dd36e`.
5. Ouvrir une PR canonique dédiée.
6. Reprendre ensuite le premier P0 avec le skill scientifique approprié.

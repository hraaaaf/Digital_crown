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
- Baseline initiale audit global : `master@f6dd36eca196d614c2d81d1dd78d3f45e481323a`
- Baseline LOT 1 audit prescription : `master@c8669527c6eb9c5232afa4277b5cd4c387a862fd`
- Nature des audits : **read-only**. Aucun test ou run CI n'est déclaré réussi sans preuve d'exécution.

## Doctrine produit confirmée

- Application **on-premise / local-first**.
- Firebase : identité/licence et services associés, jamais source de vérité des dossiers patients.
- Architecture courante : modèles locaux + moteurs déterministes ; aucune dépendance LLM requise.
- Audits scientifiques = read-only ; correctifs = missions distinctes avec tests et review.
- Donnée manquante = inconnue/non-évaluable ; jamais valeur inventée.
- `tests green != validation scientifique`.

## Évaluation audit global du 13/08/2026

- Qualité / ambition produit : **8,6 / 10**
- Readiness clinique/production : **6,6 / 10**
- Note globale audit : **7,7 / 10**

Ces notes sont une évaluation d'audit, pas un pourcentage de roadmap ni une certification de release.

## P0 — Safety & Integrity

### P0-1 — PRESCRIPTION-MISSING-DATA-FAIL-CLOSED — AUDIT CLOSED / BLOCKER CONFIRMED

Rapport : `docs/audits/P0_1_PRESCRIPTION_MISSING_DATA_AUDIT_2026-08-13.md`

Constats structurants confirmés :
- valeurs patient synthétiques/fallbacks utilisées dans le chemin de suggestion ;
- estimation frontend d'une donnée manquante pouvant participer au guidage de dose ;
- modèle Patient sans source structurée de poids actuel ;
- donnée d'antécédents manquante pouvant être confondue avec absence de signal ;
- logique clinique dupliquée backend/frontend ;
- valeurs suggérées pouvant atteindre PDF/archive puis apprentissage des habitudes ;
- tests missing-data/parité UI-API-PDF insuffisants.

**Décision :** aucune correction numérique/scientifique dans le lot d'audit. Le prochain lot doit d'abord rendre le système fail-closed sans inventer de nouvelle constante.

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

- `.claude/skills/audit-prescription-flow/SKILL.md` : audit prescription read-only, puis handoff séparé pour correction.
- `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md` : audit états cliniques read-only ; pas de correction silencieuse.
- `.claude/skills/audit-panoramic-report-pipeline/SKILL.md` : audit upload → stockage → processing → review → report/PDF.
- `.claude/skills/validate-cephalo-pipeline/SKILL.md` : validation read-only de la chaîne céphalométrique et de ses invariants.
- `.claude/rules/scientific-engineering.md` : provenance, unités, contexte, missing-data, confirmation praticien et review indépendante obligatoires.

## Lot canonique — CLOSED

Intégré sur `master` le 13/08/2026 par fast-forward contrôlé depuis `audit/canonical-refresh-2026-08-13`.

- ✅ `README.md`, `STATE.md`, `AGENTS.md`, `CLAUDE.md`, `ARCHITECTURE.md` réalignés.
- ✅ ancien `STATE.md` archivé dans `docs/archive/STATE_2026-07-21.md`.
- ✅ aucun code/runtime/DB/workflow modifié par ce lot documentaire.

## LOT 1 — P0-1 audit prescription — CLOSED

Branche d'audit : `audit/p0-1-prescription-missing-data-2026-08-13`

- ✅ route active prescription cartographiée de l'UI au PDF ;
- ✅ valeurs manquantes/fallbacks backend et frontend identifiés ;
- ✅ propagation vers génération/archivage/habitudes identifiée ;
- ✅ tests existants et gaps recensés ;
- ✅ formulaire actif confirmé : `PrescriptionAgenticStudio` ;
- ✅ aucun code, règle, test, fixture ou donnée patient modifié pendant l'audit ;
- ✅ rapport dédié créé.

## Lot actif suivant

### LOT 1B — PRESCRIPTION FAIL-CLOSED STRUCTURAL FIX — À DÉMARRER

Objectif : supprimer toute utilisation clinique d'une valeur patient inventée/estimée, introduire un état explicite `incomplete/non_evaluable`, rendre le backend autorité unique et empêcher la persistance/apprentissage d'une valeur non autoritative.

**Important :** ne pas modifier les constantes médicales/dosages existants sans recherche de sources séparée. Toute règle numérique conservée comme autoritative devra passer ensuite par `scientific-source-research`.

## Prochaine action exacte

1. Lire l'agent/skill d'implémentation prescription (`pharmacology-engineer` + règles scientifiques).
2. Concevoir le contrat fail-closed minimal sans nouvelle constante médicale.
3. Implémenter sur branche dédiée.
4. Ajouter tests ciblés missing-data + parité backend/frontend + persistance/PDF.
5. Exécuter régression proportionnée au risque.
6. Faire review scientifique indépendante.
7. Mettre à jour les canoniques puis certifier le head exact.

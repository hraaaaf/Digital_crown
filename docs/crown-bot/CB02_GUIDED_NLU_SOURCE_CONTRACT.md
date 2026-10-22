# CB-02 / Guided NLU — tranche A : contrat de parsing français ZERO-LLM

**Statut :** candidat expérimental **SOURCE-ONLY** sous PR DRAFT. **Aucune route FastAPI**, aucune injection dans la simulation `CrownBotWorkflowPreview` existante, aucun `/bot/execute`, aucun appel DB, aucun token, aucune écriture patient/RDV et aucun déploiement. Ce document **n'est pas** un certificat de fonctionnalité déployée.

**Base attendue :** CB-01 technique GREEN sur `master` `990a9efb5b9a76c86a41b5a0c214884c4776e66f`. **Dépendance restante** : CB-00/CB-01 qualification humaine et sélection pilote; une CI n'autorise pas la mise en service. CB-02 n'est pas CB-03 (transaction).

## Contrat vérifiable

Module : `backend/services/bot/guided_nlu_cb02.py`. Entrées : message français borné (1–160 caractères), **date de référence du cabinet fournie par un serveur de confiance**, `principal_scope` non vide et brouillon précédent optionnel **du même principal/cabinet**. Sans contexte : refus. Sans serveur ou avec données de contexte client invérifiables, l'intégration ne doit pas être activée.

Périmètre intentionnel : **seulement** trois intentions : `AGENDA_READ`, `PATIENT_LOOKUP`, `RDV_PREPARE`.
- `AGENDA_READ` : agenda aujourd'hui/demain/après-demain/AAA​A-MM-JJ ; syntaxe reconnue retourne `requires_server_authorization`, jamais une liste de rendez-vous.
- `PATIENT_LOOKUP` : sélecteur `Mme/Monsieur` ou identifiant, **jamais identité patient vérifiée** ; `requires_server_authorization`. Un homonyme, un patient étranger/inconnu ou un mauvais droit ne doivent être décidés que par le backend existant, après auth/RBAC/tenant.
- `RDV_PREPARE` : date/heure/patient/motif explicites → `preview_only`, **non exécutable** ; champ manquant → **une** `clarification` ciblée, ordre patient → date → heure → motif ; contradictions/actes dangereux → `refused`. Motifs limités à contrôle, consultation, détartrage ; aucune décision clinique inférée.
- Une correction explicite de date ou d'heure peut conserver les autres champs **dans le même scope uniquement** ; chaque champ expose `value`, `source` et `rule` et la correction est distinguée.
- `GuidedResult.executable=False` est invariant. Pas de pending action ID, pas d'exécution ni réservation.
- Contrat **français limité et conservateur** : accents et variantes contrôlées, pas de promesse de compréhension libre, dialectale ou multilingue. Le corpus ne constitue ni la performance réelle, ni un modèle IA.

## Gate automatisé

`.github/workflows/cb02-guided-nlu-contract.yml` doit démarrer sur la PR touchant le parseur/tests/workflow, en CI GitHub Ubuntu isolée sans LLM ni réseau applicatif. Tests `unittest` Python 3.12 stdlib : `backend/tests/test_guided_nlu_cb02.py`, **71 énoncés déclarés distincts**, générant **71 tests indépendants**, plus tests de correction, provenance, limites, fail-close cross-tenant. Vérifier le nombre **effectivement exécuté** et le résultat sur le SHA exact; ne pas remplacer un test rouge par une suppression d'assertion.

## Prochaine tranche B — NON INCLUSE

Après tests verts + revue et GO dédié : définir une API preview uniquement sous le flag **OFF par défaut**, et prouver qu'authentification, RBAC, lookup homonymes/tenant, journalisation sans PHI, server-timezone et zéro écriture restent fail-closed. Ensuite seulement un workflow UI clair : saisie, suggestion, correction et désambiguïsation visibles, avec FUE BEFORE/AFTER, accessibilité et tests humains. **CB-03** aura son propre GO et ses propres preuves SQLCipher/PostgreSQL de confirmation transactionnelle ; il n'est pas autorisé par cette tranche.

## Non-objectifs

Aucun déploiement Vercel ou cabinet, aucune donnée réelle, aucune migration, aucune nouvelle action clinique, aucune décision automatisée, pas de Pocket/mobile et pas de Desktop Commander comme prérequis CI. Ne pas promouvoir **CB-02 globalement VERIFIED** sur une preuve pure de parser.

# HANDOVER — Céphalométrie / COM « Analyse simplifiée » — clarification scientifique

**Date :** 2026-09-12  
**Repo :** `hraaaaf/Digital_crown`  
**Base master vérifiée avant ce handover :** `36091c89a6f4ae0679f40980e9f7f3e5e143d6be`  
**Handover précédent :** `docs/handovers/2026-09-12-cephalo-com-simplified-handover.md`

> Ce document **supersède uniquement les hypothèses scientifiques corrigées ci-dessous** du handover précédent. Le Goal global, les règles fail-closed, les 10 éléments COM et les exigences de certification restent applicables.

## GOAL

Aligner Digital Crown sur la fiche COM « Analyse simplifiée » réelle, avec exactement 10 éléments, sans injecter de mesures générales hors fiche et sans substitution géométrique silencieuse.

### Succès observable

- exactement 10 éléments COM dans la projection dédiée ;
- définition/construction/formule prouvée pour chaque ligne ou état explicite bloqué ;
- aucune mesure hors fiche injectée ;
- aucun calcul approximatif silencieux ;
- tests unitaires/géométriques verts ;
- analyse céphalométrique générale inchangée sauf écart prouvé ;
- aucun `CERTIFIED` sans source + code + test.

## INVENTAIRE COM VERROUILLÉ — 10 ÉLÉMENTS

### Analyse dentaire — 5

1. Surplomb
2. Recouvrement
3. I / Mandibulaire
4. I / Francfort
5. Inter-incisif I/I

### Analyse osseuse — 5

6. Angle de Tweed
7. Décalage osseux maxillo-mandibulaire par A′B′
8. Situation du maxillaire, point A, selon la construction COM
9. Situation de la mandibule, point B, selon la construction COM
10. Profondeur faciale — construction distincte à certifier séparément

## CORRECTION SCIENTIFIQUE N°1 — ANGLE DE TWEED

La formulation du handover précédent qui mettait en doute `Po-Or / Go-Me` comme construction FMA/Tweed est **à ne plus utiliser comme conclusion**.

État scientifique retenu pour la reprise :

- FMA/Tweed = angle entre le plan de Francfort et le plan mandibulaire ;
- la géométrie runtime historique `Po-Or` versus `Go-Me` est cohérente avec une construction classique FMA/Tweed ;
- il faut distinguer **géométrie de mesure** et **norme/référence COM** ;
- la norme/interprétation COM ne doit pas être activée sans source exacte ;
- le module `backend/services/cephalo_com_source_geometry.py` contient actuellement un blocker Tweed plus strict, hérité d'une dette source-spécifique. Ce blocker doit être réévalué contre le contrat COM exact avant modification ; ne pas le supprimer par simple convenance.

### Règle de reprise Tweed

Ne pas modifier la valeur géométrique si `Po-Or / Go-Me` est déjà calculé correctement. Ajouter/adapter uniquement la preuve géométrique, la provenance et les tests requis par le contrat COM.

## CORRECTION SCIENTIFIQUE N°2 — A′ / B′ / A′B′

### Construction COM acceptée et explicitement confirmée

1. Construire le plan de Francfort `FH = Po-Or`.
2. Construire la direction McNamara : perpendiculaire à FH passant par Nasion `N`.
3. Par le point `A`, tracer une droite **parallèle à la direction McNamara**.
4. L'intersection de cette droite avec FH est `A′`.
5. Par le point `B`, tracer une droite **parallèle à la direction McNamara**.
6. L'intersection de cette droite avec FH est `B′`.
7. Le décalage maxillo-mandibulaire COM est `A′B′`, mesuré sur Francfort.

### Formulation canonique courte

`A → parallèle au plan/direction McNamara → A′ sur Francfort`  
`B → parallèle au plan/direction McNamara → B′ sur Francfort`  
`Décalage maxillo-mandibulaire = A′B′ mesuré sur Francfort`

### Important

Mathématiquement, la construction est équivalente à une projection orthogonale sur FH puisque McNamara est perpendiculaire à FH. **L'implémentation, la documentation et les tests doivent néanmoins conserver la construction clinique explicite McNamara**, et non seulement le raccourci « projection orthogonale ».

### État logiciel déjà observé

- un calcul scalaire A′B′ existe historiquement par projection sur Francfort ;
- le résultat numérique peut donc déjà être correct ;
- l'écart identifié est surtout la **preuve explicite de construction** : A′/B′ et la direction McNamara ne sont pas nécessairement matérialisés comme objets/traces de construction ;
- ne pas réécrire un scalaire juste sans test démontrant un écart.

### Convention de signe

La convention de signe/direction A′B′ reste à dériver du contrat COM/source/projet. **Ne pas l'inventer.**

## CORRECTION SCIENTIFIQUE N°3 — SITUATION A / SITUATION B

Le précédent handover décrivait Situation A/B comme des distances par rapport à une verticale de Nasion. **Cette description est désormais insuffisante/fausse pour la reprise COM et ne doit pas être utilisée comme preuve.**

Ce qui est verrouillé :

- A et B participent à la construction par parallèles à McNamara vers Francfort ;
- A′ et B′ sont les intersections sur FH ;
- la construction de projection est donc connue.

Ce qui **n'est pas encore verrouillé** :

- la quantité exacte rapportée sous le libellé `Situation A` ;
- la quantité exacte rapportée sous le libellé `Situation B` ;
- unité, origine, sens/signe, éventuel angle ou coordonnée/distance associée.

### État requis

Tant que la quantité exacte n'est pas prouvée : `BLOCKED_SOURCE_PENDING` ou `SOURCE_LOCKED_CONSTRUCTION_PENDING`, jamais `CERTIFIED`.

## CORRECTION SCIENTIFIQUE N°4 — PROFONDEUR FACIALE

La profondeur faciale est **une construction indépendante**.

Interdictions :

- ne pas la dériver de A′B′ ;
- ne pas la dériver de A′ ou B′ ;
- ne pas réutiliser automatiquement la construction Situation A/B ;
- ne pas supposer « S vers verticale de Nasion » sans preuve COM exacte.

L'ancienne formulation du handover précédent sur `S vers verticale passant par Nasion` n'est plus suffisante comme contrat de certification.

État actuel : **construction COM exacte à retrouver/certifier séparément**.

## MESURES À NE PAS INJECTER DANS COM « ANALYSE SIMPLIFIÉE »

Sauf preuve directe issue de la fiche/source COM :

- SNA
- SNB
- ANB
- ligne E de Ricketts
- angle nasolabial
- classes molaire/canine
- toute autre mesure absente de la fiche COM

Elles peuvent rester dans l'analyse céphalométrique générale si correctement implémentées.

## ÉTAT REPO VÉRIFIÉ AU HANDOVER

- `master` vérifié : `36091c89a6f4ae0679f40980e9f7f3e5e143d6be` ;
- ce HEAD correspond au merge de la PR #453 de closeout R14 → R15 ;
- R14 est donc fermé sur master avant reprise de ce chantier COM ;
- aucun changement runtime COM n'a été écrit dans la présente fenêtre après les clarifications scientifiques ;
- aucune branche d'implémentation COM active au moment du démarrage du handover ;
- aucune PR d'implémentation COM ouverte par cette fenêtre ;
- aucun déploiement effectué ni requis.

## FICHIERS DÉJÀ IDENTIFIÉS COMME PERTINENTS

À relire sur le HEAD courant avant toute écriture :

- `backend/services/cephalo_com_evidence_ledger.py`
- `backend/services/cephalo_com_source_geometry.py`
- `backend/services/cephalo_engine.py`
- `backend/services/cephalo_constructions.py`
- `backend/services/cephalo_measurement_adapter.py`
- `backend/services/cephalo_construction_evidence_adapter.py`
- `backend/routers/cephalo_analysis_read.py`
- modules McNamara/CRANIOM et tests associés présents sur le master courant à retracer avant modification

## MATRICE DE CERTIFICATION À PRODUIRE

Pour chacune des 10 lignes :

`libellé fiche -> définition scientifique exacte -> landmarks -> construction -> formule -> référence/norme éventuelle -> implémentation actuelle -> écart -> état -> test`

États autorisés recommandés :

- `CERTIFIED`
- `SOURCE_LOCKED_CONSTRUCTION_PENDING`
- `BLOCKED_SOURCE_PENDING`
- `NOT_COMPUTABLE`

## ORDRE D'EXÉCUTION RECOMMANDÉ

1. Revalider `master`, HEAD, PRs et CI avant modification.
2. Relire les fichiers COM/McNamara/CRANIOM exacts sur ce HEAD.
3. Construire la matrice 10/10 avant correction large.
4. Pour A′B′ : vérifier que FH = Po-Or, McNamara ⟂ FH par N, A′/B′ = intersections des parallèles à McNamara avec FH.
5. Déterminer la convention de signe A′B′ depuis la source/contrat projet.
6. Tracer séparément la définition exacte de `Situation A` et `Situation B` ; ne pas déduire leur quantité du seul mécanisme de projection.
7. Tracer séparément la profondeur faciale.
8. Pour Tweed : conserver la géométrie correcte, séparer mesure brute et norme/interprétation, ajouter test dédié si absent.
9. Corriger uniquement les écarts prouvés.
10. Ajouter tests géométriques/fail-closed : rotation, translation, cas dégénéré, landmark manquant, cohérence de signe selon contrat, appartenance A′/B′ à FH, parallélisme à McNamara.
11. Si UI impactée : BEFORE → Goal → mockup/référence → implémentation → AFTER 390/768/1280 → comparaison/tests → score visuel.
12. PR dédiée, exact-head CI/T2, corrections si nécessaire, merge uniquement avec preuves.
13. Vérifier master post-merge et mettre à jour le canonique pertinent.

## NEXT EXACT

**Sur le master courant, produire d'abord la matrice scientifique 10/10 et vérifier le code A′B′/McNamara exact. Ne modifier le runtime que si l'écart est démontré.**

## SÉQUENCE RESTANTE

`audit exact HEAD → matrice 10/10 → A′B′ → Situation A → Situation B → profondeur faciale → Tweed + dentaire → corrections prouvées → tests → éventuelle validation UI → PR/CI/T2 → merge → master post-merge → closeout`

## NON-OBJECTIFS

- ne pas mélanger ce lot avec R15 ;
- ne pas réouvrir R14 ;
- ne pas injecter de norme non certifiée ;
- ne pas produire de diagnostic/indication thérapeutique depuis une mesure non certifiée ;
- ne pas déployer.

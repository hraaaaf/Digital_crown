# HANDOVER — Céphalométrie / COM « Analyse simplifiée »

Date: 2026-09-12
Repo: `hraaaaf/Digital_crown`
Base master vérifiée au démarrage: `3fc4313c78b179d9adbc905e074c196efcbf3fed`

## Goal
Recaler la vue/calcul **COM « Analyse simplifiée »** de Digital Crown sur la fiche COM source réelle, sans mélanger les mesures de l’analyse céphalométrique générale et sans introduire de substitution géométrique non sourcée.

### Succès observable
- les **10 éléments** présents sur la fiche COM sont représentés dans la projection COM dédiée ;
- chaque élément possède une définition/construction/formule sourcée ou un état `BLOCKED` explicite ;
- aucune mesure hors fiche COM n’est injectée dans cette vue spécifique ;
- aucun calcul approximatif silencieux ;
- tests unitaires/géométriques verts ;
- analyse céphalométrique générale inchangée sauf nécessité prouvée.

## Source fonctionnelle vérifiée
La fiche COM montre 2 blocs et 10 éléments.

### Analyse dentaire — 5
1. Surplomb
2. Recouvrement
3. I / Mandibulaire
4. I / Francfort
5. Inter-incisif I/I

### Analyse osseuse — 5
6. Angle de Tweed
7. Décalage osseux maxillo-mandibulaire par A’B’
8. Situation du maxillaire, point A, par rapport à la base du crâne / verticale de Nasion
9. Situation de la mandibule, point B, par rapport à la base du crâne / verticale de Nasion
10. Profondeur faciale, S vers verticale passant par Nasion

## Correction de cadrage
La projection COM spécifique ne doit pas être confondue avec l’analyse céphalométrique générale.

À ne pas injecter dans **COM Analyse simplifiée** sauf preuve directe issue de la fiche/source COM :
- SNA
- SNB
- ANB
- ligne E de Ricketts
- angle nasolabial
- classes molaire/canine
- toute autre mesure absente de la fiche source.

Ces mesures peuvent rester disponibles dans l’analyse céphalométrique générale si elles sont déjà correctement implémentées et validées.

## Point scientifique critique
Le libellé **« Angle de Tweed »** doit être traité selon la construction exacte de la méthode/source COM.

Interdictions :
- ne pas déduire sa construction à partir d’un raccourci générique ;
- ne pas remplacer une construction source-spécifique manquante par `Po-Or`, `Go-Me`, `Go-Gn` ou toute autre ligne de convenance sans preuve ;
- si la géométrie exacte n’est pas verrouillée, état explicite `BLOCKED` / `NOT_COMPUTABLE`.

Le lot COM/Ricketts déjà mergé a renforcé le principe général : `source-specific geometry` > substitution silencieuse.

## État actuel vérifié
- L’inventaire fonctionnel de la fiche COM est maintenant complet : **10/10 éléments identifiés**.
- Ce qui n’est **pas encore certifié** : la conformité scientifique et logicielle des 10 calculs/constructions dans Digital Crown.
- Un audit précédent a montré un risque de mélange entre la sortie COM et des mesures céphalométriques générales ; ce point doit être revalidé sur le `master` courant avant toute modification.
- Ne pas toucher au chantier R14 dans ce lot.
- Aucun déploiement Vercel autorisé ou nécessaire.

## Matrice de certification à produire
Pour chacun des 10 éléments, documenter :

`libellé fiche -> définition scientifique exacte -> landmarks -> construction -> formule -> référence/norme éventuelle -> implémentation actuelle -> écart -> état -> test`

États recommandés :
- `CERTIFIED`
- `SOURCE_LOCKED_CONSTRUCTION_PENDING`
- `BLOCKED_SOURCE_PENDING`
- `NOT_COMPUTABLE`

Aucun `CERTIFIED` sans preuve source + code + test.

## Ordre d’exécution
1. Lire `AGENTS.md`, `STATE.md`, `docs/CEPHALO_DIAGNOSTIC_SPEC.md`, `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md`.
2. Vérifier `master`, HEAD, PRs céphalo ouverts et éventuelle évolution depuis ce handover.
3. Auditer les consommateurs backend/frontend de la sortie COM actuelle.
4. Construire la matrice scientifique des 10 éléments.
5. Séparer proprement la projection **COM Analyse simplifiée** de l’analyse céphalométrique générale si ce n’est pas déjà le cas.
6. Corriger uniquement les écarts prouvés.
7. Ajouter tests unitaires/géométriques, y compris cas `fail-closed`.
8. Si impact UI : appliquer impérativement BEFORE -> Goal -> mockup/référence -> implémentation -> AFTER mêmes viewports -> comparaison/tests -> score visuel.
9. Ouvrir PR dédiée, lancer CI/T2, corriger si nécessaire.
10. Merge uniquement après preuves exact-head, puis vérifier `master` post-merge et mettre à jour les docs canoniques pertinents.

## Non-objectifs
- ne pas démarrer R15 depuis ce lot ;
- ne pas modifier R14 ;
- ne pas activer de norme patient non certifiée ;
- ne pas produire de diagnostic/indication/plan thérapeutique à partir d’un paramètre non certifié ;
- ne pas déployer.

## Next exact
**Auditer sur le `master` courant où et comment les 10 éléments COM sont actuellement calculés/affichés, puis produire la matrice de certification avant toute correction de code.**

## Séquence restante
Audit actuel -> matrice 10/10 -> corrections prouvées -> tests -> éventuelle validation UI -> CI/T2 -> merge -> master post-merge -> closeout docs.

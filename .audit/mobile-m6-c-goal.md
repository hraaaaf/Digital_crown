# M6-C — Validation / signature au fauteuil — Goal verrouillé

Date : 2026-08-25
Baseline produit exact : `5f7325b58abd9c81e437d3c4e776e61f3a0bd0b0`
BEFORE : run `32879729585` — SUCCESS, artifact `9575352945`, digest `sha256:1eb071719d0e595af90c7603c67dc87847abe3ea619e31e74aa6594de7b4b427`.

## Goal

Durcir la signature mobile existante sans reconstruire le flow : depuis un rendez-vous patient, ouvrir la signature au fauteuil, choisir uniquement un devis réellement signable, signer avec un doigt/stylet sur un canvas responsive net, puis enregistrer une signature non vide validée côté serveur.

## Succès observable

1. Tous les contrôles interactifs du flow signature mesurent au moins 48 px de haut ou de largeur utile sur 390 / 430 / 768.
2. Le canvas adapte son backing store à sa taille CSS et au `devicePixelRatio`, sans étirement du tracé.
3. `Enregistrer` est impossible tant qu'aucun trait n'a été dessiné ; Effacer remet l'état à vide.
4. Le backend refuse indépendamment une signature vide, un payload non PNG, un base64 invalide, une image indécodable, une image hors limites et un document déjà signé.
5. Le backend réécrit la signature validée en PNG propre avant utilisation.
6. L'ownership cabinet/patient et la permission `patients` restent obligatoires.
7. Les devis déjà signés ne sont plus proposés comme documents à signer.
8. Aucun overflow horizontal et aucune erreur runtime inattendue.
9. Le glass, la hiérarchie et le flow existants sont conservés.

## BEFORE mesuré

- entrée `Signature au Fauteuil` : 37 px ;
- `Effacer` / `Enregistrer` : 42 px ;
- `Fermer` : 38 px ;
- select document : 35 px ;
- fermeture icône : 18 × 18 px ;
- signature vide acceptée sur les trois viewports ;
- backing canvas fixe 300 × 180 malgré CSS 314–340 × 180 ;
- aucune gestion DPR visible ;
- aucune validation média/limite bytes/garde déjà-signé visible côté serveur dans l'audit source.

## Cible visuelle

- modal glass existante conservée ;
- fermeture dans un bouton tactile 48 × 48 ;
- select hauteur 48 ;
- canvas légèrement plus haut et responsive, bordure claire, instruction discrète ;
- boutons Effacer / Enregistrer hauteur 48 ;
- Enregistrer désactivé avant premier trait, état actif seulement après encre ;
- feedback d'erreur local et compréhensible, sans chaîne technique.

## Non-goals

- pas de nouveau type de document ;
- pas de signature distante/cloud ;
- pas de biométrie ;
- pas de redesign du Dashboard ;
- pas de Vercel.

## Preuve finale requise

BEFORE → mockup → AFTER aux mêmes 390 / 430 / 768, tests backend ciblés, build frontend, CI exact-head, score visuel final.
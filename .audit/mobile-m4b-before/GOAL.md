# M4-B — Radio panoramique contextuelle — Goal verrouillé

Base produit BEFORE: `c6de4b7a86acc33ecfc2ae09e2b10da452281590`
Artifact BEFORE: `mobile-m4b-panoramic-before-diagnostic` / `9542280515`
Digest: `sha256:fa3460120e1c68018bf0bc21799d75273ac4d97ccf484b92a594ad3988e7eaf8`

## Goal
Depuis une radio panoramique précise dans l’historique desktop, ouvrir cette radio exacte sur le mobile appairé, sans changer l’identité visuelle Digital Crown.

## Succès
1. L’historique actif charge sans dépendre d’une Corbeille inexistante.
2. La suppression est présentée comme définitive, conforme au hard-delete backend réel.
3. Chaque examen actif expose une action explicite `Ouvrir sur mobile`.
4. Les contrôles modifiés/ajoutés font au moins 44 px sur les viewports certifiés.
5. QR et URL mobile ne contiennent ni patient ID, ni `PanoramicAnalysis.id`, ni chemin média.
6. `/mobile/context` affiche la radio exacte avec patient, date, statut du rapport et image protégée.
7. L’image mobile est obtenue par requête authentifiée liée au `context_key` + device puis convertie en Blob URL côté client.
8. Permission `panoramic`, cabinet, patient, device et existence de l’analyse sont revalidés serveur à chaque lecture.
9. Analyse supprimée, permission retirée, tenant/device incompatibles ou contexte invalide => fail-closed explicite.
10. 0 overflow horizontal et 0 erreur runtime inattendue sur AFTER.

## BEFORE mesuré
- 7/7 captures.
- Historique réel cassé par `GET /api/ia/patients/42/panoramic-trash` -> 404.
- Bouton suppression: 40 px.
- Boutons de modalité: 40 px.
- Mobile panoramique non supporté.
- Aucun `analysis.id` dans la route.
- 0 overflow horizontal.

## Décision UX
- L’action mobile vit sur la ligne de l’examen exact, pas dans un QR générique de Studio.
- Suppression de l’onglet fictif Corbeille/Restaurer dans ce lot; aucune migration de soft-delete n’est inventée.
- Le contexte mobile M4-B est consultatif et compact. Les gestes d’imagerie avancés restent au vrai lot M6 mobile-first.

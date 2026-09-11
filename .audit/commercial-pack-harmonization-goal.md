# Commercial packs — quota UI goal

## Goal
Afficher exactement les limites commerciales GOLD/PREMIUM/ELITE dans l'écran **Mon Équipe**, sans transformer le type de structure du cabinet en entitlement et sans modifier le layout existant.

## BEFORE vérifié
- Référence source exacte avant changement UI : `frontend/src/features/admin/TeamManager.tsx` blob `b781b4945abaddd0554f709e9d1519fee3e0fa25`.
- Le contrat frontend imposait `dentistes_max: number` et `secretaires_max: number` et rendait directement `used/max`.
- Le backend historique représentait ELITE par `999`, donc l'écran ne pouvait pas exprimer un véritable illimité.

## Succès observable
- GOLD affiche `1` dentiste max / `2` assistantes max.
- PREMIUM affiche `2` dentistes max / `6` assistantes max.
- ELITE reçoit `null` pour les maxima et affiche explicitement `Illimité`.
- Aucun sentinel `999` ne subsiste dans la politique commerciale.
- Aucun changement de structure, couleurs, spacing, CTA ou permissions.
- Aucun message `Quota atteint` pour ELITE.
- 390 px, 768 px et 1280 px : bannière lisible, sans overflow ni clipping.

## Mockup / référence
`.audit/commercial-pack-harmonization-mockup.svg`

## Preuve AFTER attendue
Même écran et mêmes viewports 390 / 768 / 1280, plus build frontend et tests backend/CI sur le HEAD exact.

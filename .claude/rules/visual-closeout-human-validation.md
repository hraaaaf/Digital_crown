---
paths:
  - "frontend/src/**"
  - "frontend/public/**"
  - "frontend/index.html"
  - "backend/templates/**"
---
# Visual closeout — validation humaine obligatoire

Cette règle est un **gate de procédure avant closeout**, pas un mécanisme de branch protection GitHub.

Pour tout lot qui modifie l'UI/UX ou un rendu visuel produit :

1. **BEFORE** : conserver les captures de référence pertinentes avant modification.
2. Écrire le **Goal visuel** et la référence/mockup attendue.
3. Implémenter le changement.
4. Exécuter les tests techniques adaptés (frontend tests/build, smoke ou CI selon le risque).
5. **AFTER** : produire de nouvelles captures sur les **mêmes viewports / mêmes états fonctionnels** que le BEFORE.
6. Comparer BEFORE / AFTER, relever les écarts et fournir un score visuel argumenté.
7. **Remettre les captures AFTER au propriétaire du projet pour validation humaine explicite.**
8. Tant que cette validation explicite n'est pas reçue :
   - statut obligatoire : `BLOQUÉ HUMAIN — VALIDATION CAPTURES` ;
   - ne pas déclarer le lot validé, clos, certifié ou terminé ;
   - ne pas effectuer le closeout documentaire final ;
   - ne pas présenter les tests verts comme une validation visuelle.
9. Après validation explicite du propriétaire, reprendre immédiatement le closeout : canoniques, cohérence, Git/merge/certification selon le lot.
10. Toute nouvelle modification visuelle après validation invalide la validation précédente et exige de nouvelles captures AFTER.

## Preuve minimale attendue

- captures BEFORE pertinentes ;
- captures AFTER correspondantes ;
- mêmes viewports et mêmes états ;
- résultat des tests techniques ;
- comparaison visuelle ;
- validation explicite du propriétaire.

Un test technique vert prouve seulement la non-régression technique. **Il ne remplace jamais la validation humaine des captures avant closeout.**

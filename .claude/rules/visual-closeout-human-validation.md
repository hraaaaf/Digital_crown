---
paths:
  - "frontend/src/**"
  - "frontend/public/**"
  - "frontend/index.html"
  - "backend/templates/**"
---
# Visual closeout — validation humaine obligatoire

Cette règle est un **gate de procédure avant closeout**, pas un mécanisme de branch protection GitHub. Elle s'applique conjointement à `.claude/rules/execution-scoring-verification.md`.

Pour tout lot qui modifie l'UI/UX ou un rendu visuel produit :

1. **BEFORE** : conserver les captures de référence pertinentes avant modification.
2. Écrire le **Goal visuel** et la référence/mockup/Target attendue.
3. Implémenter le changement.
4. Exécuter les tests techniques adaptés (frontend tests/build, smoke ou CI selon le risque).
5. **AFTER / Render** : produire de nouvelles captures sur les **mêmes viewports / mêmes états fonctionnels** que le BEFORE.
6. Comparer explicitement **Target ↔ Render** et BEFORE ↔ AFTER, relever les écarts et fournir un score visuel argumenté.
7. Toute dimension critique (dimensions, densité, alignement, hiérarchie, overflow, comportement responsive, affordance fonctionnelle) agit comme un **hard cap** : elle ne peut jamais être masquée par une bonne moyenne sur les autres dimensions.
8. Sans comparaison réelle **Target ↔ Render**, la fidélité visuelle est plafonnée à `7.5/10`, même si les tests techniques sont verts.
9. Produire `EXECUTION_SCORE`, `ADVERSARIAL_SCORE` et `RETAINED_SCORE=min(...)` conformément à la règle canonique de scoring.
10. **Remettre les captures AFTER au propriétaire du projet pour validation humaine explicite.**
11. Tant que cette validation explicite n'est pas reçue :
   - statut obligatoire : `BLOQUÉ HUMAIN — VALIDATION CAPTURES` ;
   - ne pas déclarer le lot `VERIFIED`, validé, clos, certifié ou terminé ;
   - ne pas effectuer le closeout documentaire final ;
   - ne pas présenter les tests verts comme une validation visuelle.
12. Après validation explicite du propriétaire, reprendre immédiatement le closeout : Perfection Pass, rescoring, canoniques, cohérence, Git/merge/certification selon le lot.
13. Toute nouvelle modification visuelle après validation invalide la validation précédente et exige de nouvelles captures AFTER/Render.

## Preuve minimale attendue

- captures BEFORE pertinentes ;
- Target/mockup/référence explicite ;
- captures AFTER/Render correspondantes ;
- mêmes viewports et mêmes états ;
- résultat des tests techniques ;
- comparaison Target ↔ Render + BEFORE ↔ AFTER ;
- dimensions critiques vérifiées individuellement ;
- `EXECUTION_SCORE`, `ADVERSARIAL_SCORE`, minimum retenu et plafonds éventuels ;
- validation explicite du propriétaire.

Un test technique vert prouve seulement la non-régression technique. **Il ne remplace jamais la comparaison visuelle réelle ni la validation humaine des captures avant closeout.**

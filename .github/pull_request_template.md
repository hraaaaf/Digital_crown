## Goal / succès / preuve

- **Goal** :
- **Succès observable** :
- **Preuve** :

## Scoring obligatoire

- **EXECUTION_SCORE /10** :
- **ADVERSARIAL_SCORE /10** :
- **RETAINED_SCORE /10** = `min(EXECUTION_SCORE, ADVERSARIAL_SCORE)` :
- Écart `> 0.5` ? `oui / non`
- Si oui, investigation + preuve + rescoring :
- Plafond(s) appliqué(s), le cas échéant :

> Jamais de moyenne. Une dimension critique faible borne le score global.

## Gates binaires

- [ ] Tests/preuves requis présents et verts.
- [ ] Aucune régression constatée non corrigée.
- [ ] Aucun blocker sécurité / privacy / intégrité data / claim clinique-scientifique ouvert.
- [ ] Rehearsal/smoke requis effectué selon le risque.
- [ ] UI/UX : comparaison réelle `Target ↔ Render` sur les viewports/états requis, si applicable.
- [ ] UI/UX : validation humaine explicite des captures, si applicable.
- [ ] Revue indépendante réelle effectuée si une revendication `>= 9.5/10` est proposée.
- [ ] Perfection Pass finale effectuée si `RETAINED_SCORE >= 9.0/10`.
- [ ] Canoniques / handover / closeout mis à jour si requis par le lot.

## Plafonds à vérifier

- Même agent pour exécution + revue adversariale → `<= 9.4/10`.
- Test/gate requis rouge ou preuve requise absente → `<= 7.9/10`.
- Régression constatée → `<= 6.9/10` jusqu'à correction + nouvelle preuve.
- Blocker sécurité/privacy/data/claim clinique-scientifique → `<= 5.9/10` + `BLOCKED`.
- UI sans vraie comparaison `Target ↔ Render` → fidélité visuelle `<= 7.5/10`.

## Statut proposé

- Statut : `IN_PROGRESS / BLOCKED / BLOQUÉ HUMAIN / BLOQUÉ ASYNCHRONE / VERIFIED`
- `VERIFIED` autorisé uniquement si `RETAINED_SCORE >= 9.0/10`, tous les gates binaires applicables sont verts, aucune preuve obligatoire ne manque, aucun blocker n'est ouvert et la Perfection Pass finale est terminée.

Référence canonique : `.claude/rules/execution-scoring-verification.md`.

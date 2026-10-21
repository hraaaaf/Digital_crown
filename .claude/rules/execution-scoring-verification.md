# Execution scoring & verification — règle canonique globale

Cette règle s'applique au **candidat final de lot/sous-lot** et aux **gates critiques explicites**. Les micro-corrections, commits et tests ciblés conservent leurs preuves, mais n'entraînent pas une nouvelle notation administrative.

Le scoring ne remplace jamais un gate binaire, une preuve, un test requis, une validation humaine exigée, ni une règle de sécurité/clinique. Il s'y ajoute.

## 1. Deux scores obligatoires

Sur le HEAD candidat final (ou avant un gate critique autonome), produire séparément :

- `EXECUTION_SCORE /10` : qualité de l'exécution elle-même — correction, complétude, respect du scope, tests, preuves, réversibilité et absence de régression connue.
- `FUE_EVIDENCE_SCORE /10` : qualité des preuves FUE réellement exécutées et des contrôles spécialisés déclenchés par le risque — preuves manquantes, cas limites, régressions, incohérences, dimensions critiques faibles, faux positifs de CI, sécurité/privacy/data/claim clinique.

Le score retenu est toujours :

`RETAINED_SCORE = min(EXECUTION_SCORE, FUE_EVIDENCE_SCORE)`

**Jamais de moyenne.** Une dimension critique faible ne peut jamais être cachée par des dimensions fortes.

## 2. Divergence obligatoire à investiguer

Si `abs(EXECUTION_SCORE - FUE_EVIDENCE_SCORE) > 0.5` au verdict, le candidat final est insuffisamment compris :

1. identifier la cause de l'écart ;
2. investiguer avec preuve/test/relecture ciblée ;
3. corriger ce qui est réellement améliorable dans le scope ;
4. recalculer les deux scores.

Tant que cette investigation n'est pas faite, le score ne peut pas servir à un closeout.

## 3. Plafonds non négociables

Les plafonds suivants s'appliquent au score correspondant **et donc au `RETAINED_SCORE`** :

- `10/10` : score **non accessible à une auto-revue conversationnelle**, même si les preuves et les gates sont parfaits ; aucune attente d'un évaluateur externe ne doit en être déduite.
- `>= 9.5/10` : **hors plage pour une auto-évaluation FUE conversationnelle** ; ce score supérieur n'est jamais un prérequis implicite au closeout. Le score normal `VERIFIED` commence à `9.0/10` et peut être atteint avec la FUE et les tests et les gates effectivement requis.
- Quand la même conversation auto-évalue la FUE : plafond de prudence `9.4/10`. Ne pas présenter des personas simulés comme des utilisateurs humains indépendants.
- Test requis rouge, gate requis non vert, ou preuve requise absente : plafond `7.9/10`.
- Régression constatée : plafond `6.9/10` jusqu'à correction et nouvelle preuve de non-régression.
- Blocker sécurité, privacy, intégrité data ou claim clinique/scientifique : plafond `5.9/10` **et statut `BLOCKED`**.
- UI/UX sans comparaison réelle `Target ↔ Render` sur les viewports/états requis : fidélité visuelle plafonnée à `7.5/10`.

Ces plafonds sont cumulatifs : **le plus restrictif gagne**.

## 4. Dimensions critiques

Une moyenne interne est interdite si elle masque une faiblesse critique. Exemples :

- DB/data integrity ;
- sécurité/privacy/tenant isolation ;
- claim clinique/scientifique ;
- migration/restore/release ;
- dimensions/layout critiques UI ;
- compatibilité patient/document/media ;
- preuve de reproduction ou de non-régression requise.

Si une dimension critique n'atteint pas le niveau requis, elle borne le score global même si les autres dimensions sont excellentes.

## 5. Gate `VERIFIED`

Un lot ne peut être marqué **`VERIFIED`** que si, simultanément :

1. `RETAINED_SCORE >= 9.0/10` ;
2. **tous les gates binaires applicables sont verts** ;
3. aucune preuve obligatoire ne manque ;
4. aucun blocker n'est ouvert ;
5. la Perfection Pass finale est terminée.

À défaut, utiliser un statut exact tel que `IN_PROGRESS`, `BLOCKED`, `BLOQUÉ HUMAIN — VALIDATION CAPTURES`, `BLOQUÉ ASYNCHRONE — CI EN COURS`, ou autre état factuel adapté. Ne jamais employer `VERIFIED` par convention ou parce que la CI principale est verte.

## 6. Perfection Pass finale obligatoire

Dès que le candidat final atteint ou dépasse `9.0/10`, effectuer **une Perfection Pass consolidée** avant VERIFIED ; après correction, refaire uniquement les preuves invalidées et la confirmation finale :

1. chercher explicitement les faiblesses restantes ;
2. distinguer limites intrinsèques / hors scope / réellement améliorables ;
3. corriger immédiatement celles qui sont réellement améliorables dans le scope ;
4. rerun les preuves/tests impactés ;
5. refaire `EXECUTION_SCORE` et `FUE_EVIDENCE_SCORE` ;
6. retenir de nouveau le minimum.

Une Perfection Pass qui trouve une faiblesse améliorable mais ne la corrige pas interdit `VERIFIED`.

## 7. Format minimal de preuve

À chaque décision finale de lot ou gate critique applicable :

- `Goal` ;
- `Succès observable` ;
- `Preuve` ;
- `EXECUTION_SCORE` ;
- `FUE_EVIDENCE_SCORE` ;
- `RETAINED_SCORE` ;
- plafonds appliqués le cas échéant ;
- divergence `> 0.5` : oui/non, investigation si oui ;
- `Next exact`.

Pour le closeout d'un lot, ajouter la liste des gates binaires et leur état.

## 8. UI/UX

**Règle FUE-first :** sélectionner FUE-0, FUE-I ou FUE-G selon le parcours réellement disponible, exécuter les scénarios et produire des preuves inspectables. Les revues A/B et reviewers externes ne sont pas des gates par défaut ; les contrôles sécurité, clinique, humain et physique applicables restent obligatoires.

Cette règle complète `.claude/rules/visual-closeout-human-validation.md` :

- BEFORE + Goal + Target/mockup + implémentation + AFTER mêmes viewports/états restent obligatoires ;
- la comparaison **Target ↔ Render** doit être réelle et explicite ;
- aucune erreur critique de dimensions, densité, alignement, hiérarchie ou comportement responsive ne peut être compensée par une bonne moyenne visuelle ;
- sans Target ↔ Render réel, fidélité visuelle `<= 7.5/10` ;
- la validation humaine explicite exigée par la règle visuelle reste un gate binaire indépendant du score, demandé sur le candidat visuel final et non à chaque itération.

## 9. Domaines cliniques et scientifiques

Les scores ne valident jamais scientifiquement un moteur, une norme, une dose, un diagnostic, un pronostic ou une interprétation. Les skills/règles scientifiques et leurs sources restent autoritaires. Un blocker de claim clinique/scientifique impose `BLOCKED` et le plafond `5.9/10` jusqu'à résolution prouvée.

**Révision FUE-first : 19 octobre 2026.**

**Révision Autopilot 2026-10-20 : scoring au candidat final, plafonds et gates critiques inchangés.**

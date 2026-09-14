# Test matrix — Mutuelles dentaires

Statut : CONCEPTION ONLY — aucun test runtime ajouté.
Date : 2026-09-14.

## Goal
Définir les cas minimaux permettant de prouver qu'une future intégration est déterministe, fail-closed et rétrocompatible avant activation cabinet.

## A. Construction du DTO
1. Patient assuré lui-même, données complètes → champs AUTO remplis depuis Patient/Cabinet/Honoraires.
2. Bénéficiaire distinct de l'assuré → aucune identité d'assuré inventée ; champs absents dans `unresolved_fields`.
3. CIN/affiliation absents → dossier patient général reste valide ; blocage uniquement si le template/règle l'exige.
4. Une dent FDI → valeur exacte conservée.
5. Plusieurs dents FDI → ordre/ensemble reproduit sans parsing du libellé.
6. Dent invalide/non structurée → aucun numéro inventé.

## B. Ligne Honoraires ↔ Acte
7. Historique : même `document_archive_id`, même nombre de lignes actives/Acte actifs → association par index autorisée.
8. Historique : nombre divergent → `LINK_AMBIGUOUS`, NGAP automatique interdit.
9. Acte soft-deleted → jamais utilisé pour une ligne active.
10. Shrink puis expand → ancienne ligne supprimée jamais rematchée silencieusement.
11. Futur `source_line_uid` présent → association par UID prioritaire, indépendante de l'ordre.
12. Réordonnancement avec UID → identité de ligne conservée.

## C. CatalogAct / NGAP
13. `catalog_act_id` absent → aucun code NGAP automatique.
14. `CatalogAct.code` de type `INTERNAL` → jamais interprété NGAP.
15. Mapping unique, actif, sourcé/hashé → `EXACT`.
16. Plusieurs règles valides → `AMBIGUOUS`, choix praticien obligatoire.
17. Aucun mapping → `NO_MATCH`, aucun code inventé.
18. Mapping expiré/non vérifié → `OUTDATED`, fail-closed.
19. Même entrée + même version/hash → même résultat déterministe.
20. Changement référentiel → ancien document conserve son snapshot/version.
21. Multi-actes même séance → règle de cumul versionnée testée, jamais simple somme implicite.

## D. Templates
22. Template sans hash/version → rendu final interdit.
23. Template hashé + version connue → rendu autorisable sous réserve des autres gates.
24. Changement binaire/template → nouvelle version ; anciennes réimpressions inchangées.
25. Champ `INSURER_ONLY` → toujours vierge côté cabinet.
26. Cachet/signature non configurés → jamais générés artificiellement.

## E. Pièces
27. Ordonnance existante requise et disponible → réutilisation P1.
28. Ordonnance requise mais absente → `MANUAL_REQUIRED`/blocage explicite.
29. Radio exigée par règle et disponible → référence document existant.
30. Radio exigée mais absente → blocage explicite, aucune pièce fantôme.

## F. Non-régression DB
31. Migration additive sur copie DB → même nombre de patients avant/après.
32. mêmes IDs Patient/Acte/DocumentArchive conservés.
33. aucune valeur existante modifiée par la migration.
34. dossiers historiques sans nouveaux champs toujours lisibles/éditables.
35. rollback → application historique relit la DB sans perte.
36. aucun backfill inventé de `catalog_act_id`, CIN, affiliation ou NGAP.

## G. Validation métier
37. échantillon soin conservateur ;
38. endodontie ;
39. extraction ;
40. prothèse fixe/amovible ;
41. ODF/entente préalable ;
42. cas nécessitant radio ;
43. cas ambigu volontaire.

Pour chaque fixture métier : source Honoraires → Acte → CatalogAct → résultat NGAP → champs template, avec validation par praticien avant activation.

## Critère de succès du futur chantier d'intégration
Aucun cas P0/P1 en échec, aucun mapping silencieux, aucune perte DB, et reproduction historique prouvée avec versions/hashes archivés.
# FACAD F01.13 — passage #2 : contre-vérification index C02 (scientifique, NON clinique)
**11 octobre 2026 — FACAD 21/39 = 53,8 %, global 41/99 = 41,4 % : aucun nouveau gate fermé.**

## Preuve réelle
- [Archive existante #38102158028](https://github.com/hraaaaf/Digital_crown/actions/runs/38102158028), artefact #11688004374 : métadonnées source C02 exactes, ZIP SHA256 `d121d062920dea17cecb5ff43c778a93681283530b21a582f044b9f9186d0bd3`, ZIP sans erreur.
- Document `C02_Lateral Cephalometry Library - Measurements.pdf` 34 pages, SHA256 original `4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548`. Index **hash de texte de chaque 34 pages**, sans republier un PDF propriétaire.
- **25 tokens** cherchés à délimitation stricte ; **8** avec au moins une page correspondante, 17 non identifiés par ces tokens ; cooccurrences d'étiquettes lexicales sur **7 pages indexées (5, 10, 19, 20, 22, 24, 30)** et **24 lignes appariées** au total. Ce ne sont PAS des relations repère→mesure ni des formules.
- Échantillons d'index : `SNA/SNB/ANB` pages 1 et 5, `InterIncisal` 1 et 10, `PFH` 2/19/20, `Xi` 3/24, `CF` 3/24, `Max-Mand` 3/22/30. Pas de lien géométrique démontré par nom.
- Source C01 distincte: métadonnées **12 pages**, SHA256 `a977f219b6c9b95543551fe7a6e48587ac597b065e0200ab844e20ed322ba119`, constructions non attribuées un à un.
- Rapport B65 : **65** analyses UIA observées, **42** triplets UIA CSV en Git, **23** sans triplets Git stricts ; crosswalk huit profils prioritaires ([source](https://github.com/hraaaaf/Digital_crown/blob/5f433fdff65819e598b6d054c7c99cef22c07dd5/docs/audits/facad_trial_20261011/FACAD_F01_13_WAVE5_SOURCE_CROSSWALK.json)). Comparaison numérique FACAD↔Digital Crown sur le même cas **0**.
- Le manuel officiel FACAD 3.14 a des définitions générales d'opérateurs géométriques, **non** les relations exactes de tous les profils et signes. Référence <https://www.facad.com/dox/dox314/FacadRefMan.pdf> (page web PDF pas accessible pour double vérification visuelle complète à ce passage).

## Verdict F01.13
- **Audit de lacunes approfondi**, mais **gate OPEN** : pages originales par mesure, ordre des repères et normes par variant, signes/arrondi/calibration, liens source C01→C02→définition profil et évaluation scientifique indépendante absents.
- 2 perspectives adversariales **internes** : provenance **8/10**, vérification scientifique de formules **0/10** ; sécurité minimaliste **9/10**, droits Ilexis autorisés **0/10**. D3 `OPEN_RED`, `CONVERGED=false`.
- Aucun logiciel FACAD relancé, aucune formule inventée, aucun PDF/vendor data redistribué.

**Pour clôturer :** sous droit fournisseur et protocole d'accès, bâtir la matrice `profile → mesure → arguments → construction C01 page/source → formule/valeur C02 → unité, signe, norme et variante` puis comparer au contrat de mesure CEPH08 ; toute absence doit rester `UNKNOWN`, pas `CERTIFIED`.

**Progression après passage #2 : FACAD 21/39 = 53,8 %, GLOBAL 41/99 = 41,4 %**, variation 0.

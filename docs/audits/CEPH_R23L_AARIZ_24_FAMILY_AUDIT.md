# CEPH R23-L — audit read-only des 24 repères Aariz par famille anatomique

**Statut initial : RESULTAT SCIENTIFIQUE FROZEN FAIL ; AUDIT NON CLINIQUE.**
Source figée : `docs/audits/evidence/lot04/`, lot de 150 radios du jeu d'acceptation Aariz, modèle SRPose38 ONNX SHA256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`. **Aucun nouveau passage du modèle.**

## Ce qu'on mesure — les points, pas les angles

Le modèle ONNX retourne 38 canaux de coordonnées. L'évaluation Aariz d'origine contient 24 repères nommés en correspondance anatomique selon le mapping opérationnel DC gelé. Elle compare **les coordonnées localisées**, en mm après calibration de chaque radio, au goldset de référence Aariz. Elle contient également 9 mesures propagées en aval mais **ce rapport n'utilise pas leurs angles pour évaluer le placement des points**.

La définition officielle anatomique des 38 canaux du challenge CL-Detection2023 n'est pas démontrée dans les sources du checkpoint ; la liaison `canal numéro → nom S/N/A/etc.` de Digital Crown est un **mapping historique local**, marqué `SOURCE_LOCK_REQUIRED`. L'erreur de placement mesurée inclut donc l'effet possible d'un mapping incorrect, sans prouver qu'il est incorrect.

## Résultats observés dans l'acceptance record original

| Famille Aariz compatible | PASS | FAIL | Total |
|---|---:|---:|---:|
| Osseux | 1 | 13 | 14 |
| Dentaire | 0 | 4 | 4 |
| Tissus mous / cutané | 0 | 6 | 6 |
| **Total** | **1** | **23** | **24** |

Le seul point PASS est **Me**. `23/24 FAIL` signifie *non-conformité aux seuils préenregistrés REFERENCE_EQUIVALENCE_V1*. Cela ne veut pas dire que les points sont toujours mal placés, ni que le modèle est inutilisable sur chaque radio individuelle.

### Zones à inspecter en priorité

| Repère | Famille | Erreur p95 modèle | Seuil p95 de référence | Ratio |
|---|---|---:|---:|---:|
| Pog_soft (pogonion cutané) | Cutané | 8,135 mm | 1,334 mm | 6,10× |
| PNS | Osseux | 5,221 mm | 0,985 mm | 5,30× |
| Ar | Osseux | 8,902 mm | 2,220 mm | 4,01× |
| N (nasion) | Osseux | 7,490 mm | 1,891 mm | 3,96× |
| S (selle turcique) | Osseux | 1,698 mm | 0,457 mm | 3,72× |
| A | Osseux | 6,491 mm | 1,966 mm | 3,30× |
| L1_apex | Dentaire | 5,371 mm | 2,985 mm | 1,80× |

Ces seuils sont **uniquement ceux qui étaient gelés avant l'évaluation**. Il est interdit d'assouplir les seuils après avoir observé l'échec.

### Risque « appareil / domaine image » à investiguer

D'après les agrégats originaux, le p95 du repère N varie selon les dispositifs :
- ART Plus, `n=55` : 8,511 mm ;
- Rotograph EVO, `n=11` : 9,078 mm ;
- Hyperion X5, `n=20` : 2,327 mm.

Ces différences **ne démontrent pas** un défaut propre à un constructeur : échantillons inégaux, cas cliniques différents, protocole d'acquisition et incertitude de référence peuvent confondre. Ce sont des indicateurs à tester ensuite, pas de nouveaux critères de PASS.

## Peut-on vérifier l'hypothèse des canaux inversés maintenant ?

**Pas à partir des seules preuves agrégées publiées.** L'artefact LOT04 contient les coordonnées des 38 prédictions par radio et les erreurs déjà calculées pour les 24 correspondances, mais **pas les 24 couples `(x,y)` de vérité humaine par radio**. Le résidu individuel entre `prédiction canal i` et `référence réelle du nom j` n'est donc pas récupérable pour établir une permutation `i ↔ j` causale.

Une permutation choisie en regardant les 150 cas d'acceptation violerait de toute façon la politique d'ensemble `untouched`, car elle ajusterait le mapping sur les données de test. On peut émettre des **hypothèses anatomiques issues des sources** mais pas les adopter comme identité officielle sans dictionnaire organisateur ou revue experte sur un jeu de développement distinct, suivie d'une nouvelle évaluation préenregistrée sur un jeu indépendant.

## Ce que la nouvelle CI prouve

Le script `scripts/audit_ceph_r23l_aariz_point_families.py` :
- valide les SHA des preuves, le modèle exact et le hash canonique du manifeste gelé ;
- exige 150 cas distincts, 38 coordonnées modèle par cas, exactement 24 lignes d'acceptation et seuils ;
- reproduit le PASS/FAIL de chaque repère à partir des **seuils d'origine** sans retuning ;
- sépare osseux/dentaire/cutané, publie les médianes, p95, ratios, directions médianes et statistiques par appareil (avec tailles n et avertissement exploratoire) ;
- **n'infère aucune nouvelle sortie du poids et ne calcule aucune différence de repères non observée** ;
- produit seulement `report.json` et `README.md` agrégés, pas d'images, noms patients ni coordonnées de cas.

Le dossier initial `docs/audits/evidence/lot04/` est **non modifié**, tout comme poids, API, base, références et labels.

## Suites scientifiques valables

1. Accéder légalement au couple officiel CL-Detection2023 même image / 38 indices humains pour un contrôle descriptif; la demande aux organisateurs a été envoyée et ne présume aucun droit.
2. Ou travailler sur un jeu Aariz **de développement** avec images, coordonnées humaines appariées et droit d'accès; résoudre les définitions osseuses/dentaires/cutanées sous revue d'orthodontiste.
3. Préenregistrer toute hypothèse `i ↔ j`, garder le jeu d'acceptation indépendant, puis produire une **nouvelle** comparaison reproductible; ne jamais modifier ni requalifier rétroactivement le verdict LOT04 gelé.
4. Même une amélioration technique ne remplace ni la preuve de licence de redistribution du checkpoint, ni les 6 HOLD Ricketts, ni les futures validations cliniques.

**Verdict :** R23-L est une investigation de causalité *non conclue*, et n'autorise aucun changement de mapping, signature clinique, fusion, déploiement, ou mise en service réelle. `CEPH_DETECTOR_SELECTED` reste NON SATISFAIT, **CLINICAL NO-GO**, feuille de route **41/99**.

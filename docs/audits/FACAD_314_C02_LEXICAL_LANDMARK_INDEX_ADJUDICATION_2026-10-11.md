# FACAD 3.14 C02 — vérification de l'index des cooccurrences (source originale SHA-pinnée)

**Date :** 2026-10-11. **Statut :** SOURCE-INDEX-VERIFIED / CLINICAL-EQUIVALENCE-NOT-VERIFIED. **Périmètre :** observation/recherche seulement, PR documentaire [#829](https://github.com/hraaaaf/Digital_crown/pull/829), aucun commit moteur clinique ni interaction dossier patient.

## 1. Source et run vérifiés

- [Windows Actions EXPERIMENTAL #38102158028](https://github.com/hraaaaf/Digital_crown/actions/runs/38102158028) : **COMPLETED/SUCCESS**, source HEAD **`21c2615da54938b00a728dc7d231e19e9777e714`**, une tentative. Les étapes installation Quick Demo, arrêt du processus FACAD auto-lancé, index SHA/page et index proximité ont effectivement terminé SUCCESS.
- Artifact **`11688004374`** : `facad-c02-minimal-source-page-index-21c2615da54938b00a728dc7d231e19e9777e714`, ZIP SHA256 **`d121d062920dea17cecb5ff43c778a93681283530b21a582f044b9f9186d0bd3`** ; noms des **seuls trois** membres : `c02-pdf-minimal-index.json`, `c02-landmark-cooccurrence.json`, `installed-manual-status.txt`.
- Index source JSON SHA256 **`011f9330320c46ce2b776506710080bc42826c4155e54ea9e9600ee5ed5158a4`** (identique à l'index source du précédent run #38101420112). Index cooccurrences JSON SHA256 **`a6903d480aa21c97b8bce40d5f13b1a3666e9b102fa4432cb4d8127fb84edf28`** ; le champ `source_index_sha256` de l'index cooccurrences référence exactement le hash de l'index source embarqué.
- Manuel **`C02_Lateral Cephalometry Library - Measurements.pdf`**, installation FACAD officielle sur runner GitHub Windows jetable, **34 pages**, **5 718 901 octets**, SHA256 exact **`4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548`**, 34 pages indexées séquentiellement, 34 couches texte d'au moins 80 caractères. Le ZIP ne contient PAS le PDF ni du texte intégral.

## 2. Résultat réel par page (lexical, non géométrique)

| Page PDF 1-based | Étiquettes ciblées sur la page | Lignes correspondantes dans l'extraction texte | Liens géométriques établis |
|---:|---|---:|---|
| 5 | SNA, SNB, ANB | 3 | 0 |
| 10 | InterIncisal | 1 | 0 |
| 19 | PFH | 4 | 0 |
| 20 | PFH | 3 | 0 |
| 22 | Max-Mand | 1 | 0 |
| 24 | Xi, CF | 11 | 0 |
| 30 | Max-Mand | 1 | 0 |
| **Total** | 8 étiquettes sur 7 pages | **24** | **0** |

Le collecteur repère uniquement les mots entiers d'une liste fermée avec un SHA256 de chaque ligne extraite, un numéro de ligne, sa longueur, le nom cible et des noms de repères susceptibles de partager la ligne. **Deux lignes de la page 24** contenant la cible `Xi` mentionnent aussi le token `OL` (lignes **18 et 21** de l'extraction p.24, longueurs **5 et 8 caractères**, respectivement). **Ceci est une cooccurrence, pas la preuve que l'axe `OL` intervient dans la construction de `Xi` ; aucune formule, aucune direction, aucun signe, ni aucune relation de dépendance ne peut être dérivé de ces deux petites chaînes.** Les **22 autres lignes** n'ont pas de deuxième terme détecté par le collecteur. Cela ne prouve pas l'absence de relations dans le dessin, les autres lignes, les pages non ciblées, ou l'éditeur FACAD.

**Autre limitation :** les noms internes UIA `Angle4p`, `Angle3p`, `Angle2ln`, `Dist2p`, `DistLine`, `ProjLine`, `Proj90Line` ne sont pas des occurrences whole-token du texte PDF C02 selon le premier index. **Ne pas conclure qu'ils ne sont pas définis dans FACAD.** Les signes et l'ordre vectoriel ne sont pas extraits par cet instrument lexical.

## 3. Audit de preuve exécuté localement (deux perspectives)

**A. Revue adversariale interne — traçabilité/anti-fausse preuve (score strict 8/10, documentaire uniquement).** Relecture ZIP effective avec `zipfile` + `hashlib` + `json` et assertions : exactement les 3 fichiers attendus ; 34 numéros de page consécutifs ; deux documents renvoient au SHA de source identique, 34 pages et taille exactes ; `source_index_sha256` correspond octet pour octet à l'index inclus ; 24 objets ligne disposent d'un SHA à 64 chiffres hex et `landmark_relationship_verified=false` ; sept pages et histogramme recomptés ; 2 lignes positives `Xi` + `OL`, pas 2 formules. Aucune contradiction détectée dans ce petit périmètre. **Aucun accès aux pages visuelles ni aux définitions**, donc pas 10/10.

**B. Revue adversariale interne — sécurité et sciences (score strict 3/10 pour preuve de formules/parité ; 7/10 pour confinement de l'artefact).** Le générateur n'inclut ni texte explicatif ni PDF, ni dossier patient ; `source_text_redistributed=false`, `patient_data_processed=false`, `clinical_equivalence_certified=false`, `vendor_formula_verified=false`. Le statut Windows contient `NO_PATIENT_READ_OR_EXPORT=true`, `FACAD_PROCESS_ABSENT_BEFORE_DOCUMENT_INVENTORY=true`, et **`CLINICAL_APP_AUTO_STARTED_BY_INSTALLER=true`** : l'installation a lancé FACAD puis le script l'a arrêté avant de lire le PDF. **Cela n'établit PAS l'isolation d'écritures FAC03**, qui reste **OPEN_RED** ; il faudrait vérifier l'attribution d'éventuelles écritures dans les dossiers partagés. Aucun reviewer clinique humain indépendant, aucune comparaison numérique.

## 4. Gates inchangés et prochaine décision

| Gate | État conservé | Motif |
|---|---|---|
| Official C02 PDF source/index | VERIFIED (metadata & lexical) | Source officielle SHA/34 pages et références de page traçables |
| F01.13 correspondance science et formules | OPEN | Aucune extraction de formule ou dessin certifié |
| FAC03_D3 | OPEN_RED | Aucune preuve d'isolation des écritures |
| FAC05 parité scientifique FACAD ↔ Digital Crown | NOT_TESTED | Aucun même cas calibré comparé sur deux calculateurs |
| CLINICAL_EDIT_ALLOWED | false | Bloque les usages patients Save/Load |
| CONVERGED | false | Deux revues cliniques indépendantes absentes et défauts de preuve ouverts |
| Avancement roadmap canonique | **39/99 (39,4%)** | Pas de nouveau jalon entièrement clôturé |

**Next prioritaire et falsifiable** : une extraction *très courte, page par page et autorisée* des définitions/diagrammes pertinents sur FACAD C02 (p.5, p.10, p.19–20, p.22, p.24, p.30), sans publier le PDF propriétaire ; capturer les conventions sémantiques/signées et la correspondance entre noms d'éditeur et noms du manuel avec approbation scientifique ; seulement ensuite comparer des oracles géométriques sur fixtures non cliniques alignées. **Ne pas déduire une formule d'une cooccurrence.**

Aucune fusion, aucun déploiement, aucune case de la roadmap promue par cette étude.

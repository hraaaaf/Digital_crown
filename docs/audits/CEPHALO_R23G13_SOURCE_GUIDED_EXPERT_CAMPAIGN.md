# Digital Crown — CEPH-UXCLIN-01 / R23-G13 — Source guide Atlas2009 + protocole pré-annotation experte

**Statut : GUIDE DOCUMENTAIRE ET OUTIL PUBLIC DE RECHERCHE UNIQUEMENT. Clinical NO-GO.**
**Édition** : `RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1`.
**Support expérimental** : exactement les deux téléradiographies publiques Wikimedia ANUG (2014) et Challiyan (2023), source/image SHA G11, attribution CC BY-SA 4.0. Ce ne sont pas des images du goldset Aariz ; aucune calibration physique ni orientation vérifiée n'est établie pour elles.

## Résultat source documenté et limite critique

L'inventaire `docs/audits/schemas/cephalo_r23g13_source_specific_landmark_guides_v1.json` reprend **21/21 identités littérales G9** et pour chacune : description prudente en français, source précise **existante dans le dépôt**, court extrait de preuve vérifié par logiciel, interdictions d'alias, décision opératoire. Le script `scripts/cephalo_r23g13_public_source_guided_workbook.py` revérifie que **chaque extrait est réellement présent** dans la version de source lue sur HEAD GitHub avant d'insérer les guides dans l'atelier G12. Toute dérive de fichier/nom/autorité/identité bloque le build.

**Distinguer définition conceptuelle et protocole de clic individuel.** Les sources de Digital Crown sont déjà source-locked pour leur **usage géométrique** et non des fiches illustrées validées de répétabilité des annotations humaines sur JPEG. 15 descriptions sont suffisamment déterminées pour laisser poser un **brouillon de coordonnées manuelles NON VALIDÉES**. Les **six autres** sont conservées en HOLD jusqu'à une règle opératoire écrite et revue indépendamment :

| Identité en HOLD | Ce qui manque avant un clic fidèle |
|---|---|
| `Ba` | Point exact du contour basion dans le protocole Ricketts en présence de double contour |
| `FOP_PREMOLAR_Ricketts` | Contact/intercuspidation bicuspide précis, règle de choix en cas de superpositions |
| `FOP_MOLAR_Ricketts` | Contact/intercuspidation molaire précis, convention de choix et construction FOP |
| `GO_Ricketts_PFH` | Convention de construction/identification du Gonion propre à Go→CF, non alias generic Go |
| `L6_DISTAL_Ricketts` | Placement opératoire de la référence distale de la molaire inférieure sur FOP ; ne pas transposer sans preuve la règle A6 supérieure |
| `PNS_Ricketts` | Contour de l'épine nasale postérieure et correspondance à l'identité spécifique Atlas2009, sans alias PNS générique |

**Aucun de ces six HOLD n'est automatiquement éligible au clic dans l'atelier.** Ils ne deviendront pas actifs par le simple fait d'ajouter un nombre de pixels ou un `verified=true` dans le JSON. L'arbitrage clinique documenté et signé précède toute autorisation.

Les **15 autres descriptions** restent aussi `clinical_definition_verified=false` et `expert_consensus_complete=false`. Les tests Playwright utilisent seulement des **clics synthétiques**, pas un repérage orthodontique, ni une validation numérique des mesures Atlas33.

## Parcours préparé pour une future campagne humaine

**PRE-REGISTRATION — avant voir/comparer des résultats.** Enregistrer dans le dossier gouverné hors CI : version exacte du protocole Atlas2009, SHA des 2 fichiers, rôle de chaque image, droits d'étude, identifiants anonymes, objectif (étude de faisabilité opératoire vs vérité clinique), résolutions et qualité visuelle, politique des 6 HOLD, tolérances clinique par repère et par facteur *justifiées*, exclusions/NOT_COMPUTABLE, plan de répétition intra, moment et méthode d'adjudication, gel de toute cohorte d'acceptation. Les deux JPEG **sans échelle connue** autorisent la démonstration de coordonnées en pixels et, sous réserves, une analyse de répétabilité pixel, mais **pas une précision en mm ni une validation de distances cliniques**. Ne pas proposer de norme 2 mm arbitraire.

**Qualification et indépendance.** Deux praticiens orthodontistes distincts qualifiés et authentifiés par le protocole de gouvernance, expert A et expert B, annotent **les mêmes images** en sessions séparées ; empêcher qu'ils consultent les marques/exports de l'autre, le détecteur, les coordonnées CI ou le résultat adjudiqué. Un simple jeton de l'interface ne prouve PAS leur qualification, signature ou indépendance. Conserver preuve de compétence et convention de contribution en zone protégée, **pas** dans GitHub.

**Traçabilité observationnelle.** Conserver dans un dossier local approuvé : SHA image, source scientifique (doc/version), ID du repère, position `x/y` dans les pixels source, champs `NOT_VISIBLE` et `UNRESOLVED`, justification, profil de qualité/superposition, horodatage, examinateur pseudonymisé, historique des corrections. L'atelier G13 n'est qu'un **prototype de placement et un export DRAFT** ; il ne constitue pas une eCRF à audit trail signé. Étendre l'outil clinique sous revue sécurité/vie privée et la politique d'accès avant de lui donner ce rôle.

**Orientation et calibration.** Pour chaque cliché de mesure, documenter les axes anatomiques antérieur et supérieur dans la même image, inversion/mirroring, acquisition/provenance, validation externe indépendante. La calibration `mm_per_pixel` doit provenir d'une échelle/taille étalon vérifiée **sur le même cliché**. Sans calibration : toute mesure en mm reste `NOT_COMPUTABLE`. Sans orientation vérifiée : mesure signée / projection directionnelle non autorisée. Sur ces deux JPEG, l'état reste **INCONNU / NON VÉRIFIÉ** même si l'image semble orientée normalement.

**Adjudication et fiabilité.** Après le gel des annotations aveugles A/B, comparer l'écart en pixels et les cas non identifiables avec leurs dénominateurs. Calculer un accord intra-observateur sur un sous-ensemble préenregistré, sans voir les premiers clics ; convenir de re-lecture tierce des désaccords, **sans faire passer leur moyenne pour vérité**. Après règles opératoires complètes, comparer chaque repère aux calculs géométriques Atlas33 source-locked et annoncer erreurs/signées et couverture par facteur (pas seulement une moyenne globale). Aucun score clinique sans justifications métrologiques et évaluateur indépendant.

**Jeu d'acceptation.** Ne pas réutiliser les 150 cas Aariz `test` pour ajuster la politique; ces deux clichés publics ne sont pas des exemples Aariz et leur sélection/usage doit être enregistrée comme jeu de faisabilité **EXPOSÉ**. Une fois des clics expérimentaux observés par le développeur, ces images ne constituent pas un test vierge indépendant pour les mêmes critères.

## Fichiers et utilisation locale

- [Guide JSON des 21 points](schemas/cephalo_r23g13_source_specific_landmark_guides_v1.json) (extraits probants vérifiés sur les sources du dépôt, non sur images anatomiques).
- `scripts/cephalo_r23g13_public_source_guided_workbook.py` : reconstruit G12 offline à partir des mêmes **2 JPEG identifiés**, insère les fiches et **désactive le placement des six HOLD**.
- `audit/cephalo_r23g13_contract_tests/test_source_guides.py` : 10 tests stricts sur les 21 IDs, citations réellement trouvables, anti-traversal, NO-GO, six HOLD non promouvables.
- `audit/cephalo_r23g13_contract_tests/g13_source_guide_browser.cjs` : navigation réelle sur les deux images, source et définition affichées, clic HOLD refusé en capture, placement provisoire autorisé sur une identité source-décrite, deux viewports desktop et captures exclusivement synthétiques.
- `.github/workflows/cephalo-r23g13-source-guides.yml` : CI expérimental sur exact HEAD, sans backend clinique, sans déploiement et sans images patient.

```bash
python -m scripts.cephalo_r23g13_public_source_guided_workbook \
  --input-dir /DOSSIER/LOCAL/DEUX_JPEG_PUBLICS \
  --output-dir /DOSSIER/LOCAL/ATELIER_G13_VIDE
python -m http.server 8765 --bind 127.0.0.1 --directory /DOSSIER/LOCAL/ATELIER_G13_VIDE
```

Ouvrir localement `http://127.0.0.1:8765/`. Ne pas y charger d'images patients. Les seuls fichiers image produits par cette commande sont des copies des deux sources publiques, gardées **hors dépôt**. Les artefacts CI contiennent des captures de démonstration synthétiques attribuées **CC BY-SA 4.0** et des rapports textuels de provenance.

## Décision / transition

**Ce que ce lot peut valider :** correspondance documentaire des 21 entrées G9, rigueur des 6 HOLD, présence de source exacte, interaction UI réelle sur deux JPEG public-only, continuité du flux G12 et zéro promotion clinique. **Ce qu'il ne peut pas valider :** source primaire Atlas contrôlée page par page, illustrations d'un atlas protégé, identité et fiabilité humaine, orientation/calibration en mm, performance sur l'anatomie, 33 facteurs cliniquement mesurables.

La future décision de retrait des 6 HOLD nécessite une procédure explicite, distincte et révisée par deux réels orthodontistes, accompagnée de documentation de source Atlas, preuves et nouveau SHA/revues. Les écrans/résultats actuels ne sont jamais une référence clinique, même si la CI est entièrement verte. Ni merge ni déploiement autorisé.

**Roadmap :** W1-W3 descriptions → G9 compatibilité Atlas/Aariz → G10 contrat expert intake → G11 deux vrais JPEG → G12 atelier clic pixels → **G13 guides 21 et HOLD + préparation protocole humain** → campagne expert réelle/calibrée → validation Atlas33 → closeout.

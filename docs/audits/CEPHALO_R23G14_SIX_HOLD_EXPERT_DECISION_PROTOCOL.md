# CEPH-UXCLIN-01 — R23-G14 / SIX-HOLD EXPERT DECISION PACK
**État 2026-10-17 : DÉCISIONS DOCUMENTAIRES PRÉPARÉES. SIX REPÈRES TOUJOURS EN HOLD.**
**Édition** : `RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1`. **0/33 mesure clinique validée.** Aucun patient réel, annotation experte, signature indépendante ou calibration n'a été fournie. **Pas de merge, déploiement, activation du Focus clinique.**

## Résultat et périmètre réel

Dans G13, **21 identités Atlas** ont été documentées, mais six ne bénéficient pas d'une règle de placement sur pixel suffisamment univoque pour constituer une référence humaine reproductible. Le dossier `docs/audits/schemas/cephalo_r23g14_six_hold_expert_adjudication_v1.json` est une **matrice d'arbitrage**, pas un dossier de résultats : **six cartes**, état exact `HOLD__EXTERNAL_HUMAN_ADJUDICATION_REQUIRED`, source-lock documentaire existant, courte phrase vérifiée dans le dépôt, hypothèse de travail explicitement NON autoritaire, trois questions concrètes par point, risques d'alias et littérature extérieure de portée strictement délimitée.

La recherche bibliographique externe a identifié des descriptions génériques crédibles ; **aucune** ne démontre à elle seule l'équivalence entre le point générique et l'identité contractuelle Atlas2009 de Digital Crown.

| HOLD | État des sources — preuves et limites | Décision clinique G14 |
|---|---|---|
| `Ba` | Basion : marge antérieure médiane du foramen magnum selon [Anatomy of Foramen Magnum, NCBI](https://www.ncbi.nlm.nih.gov/books/NBK526041/) et [étude céphalométrique 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11010784/) ; l'article ne gèle pas le choix du pixel Atlas2009 en contours doubles. | **HOLD** : protocole pratique de contour + définition Atlas à revoir |
| `FOP_PREMOLAR_Ricketts` | Le source-lock local exige contact postérieur prémolaire ; [Ricketts 1978, ligne d'occlusion](https://pubmed.ncbi.nlm.nih.gov/281884/) éclaire le concept de l'occlusion, mais ne donne **pas** dans son résumé la coordonnée 2-D prémolaire exigée. | **HOLD** : définir contact cible et règle d'image sous superposition |
| `FOP_MOLAR_Ricketts` | Même construction FOP postérieure, distincte des plans Steiner/Downs et de l'ancrage molaire générique. Ricketts 1978 seul ne tranche pas le point d'intercuspidation molaire sur le cliché. | **HOLD** : choisir occlusion visée et règles de sélection |
| `GO_Ricketts_PFH` | Le source-lock Wave C exige Go manuel spécifique pour Go→CF. Une [étude de landmark 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11010784/) décrit un **Gonion générique** par bissectrice de tangentes ; ce n'est pas une preuve que Go_PFH Atlas a la même identité. | **HOLD** : comparer l'édition exacte et documenter mode de construction |
| `L6_DISTAL_Ricketts` | Le source-lock Wave A impose un repère distal de la première molaire inférieure selon FOP. La règle tangente A6 du maxillaire (document U6) **ne s'applique pas automatiquement** à L6 ; les [études Ricketts 2014](https://pubmed.ncbi.nlm.nih.gov/24696824/) confirment les familles de mesures, pas leur alias. | **HOLD** : règle de référence distale L6 de l'édition Atlas |
| `PNS_Ricketts` | [StatPearls NCBI](https://www.ncbi.nlm.nih.gov/books/NBK594272/table/article-131913.table1/) décrit la pointe de l'épine postérieure ; [une étude CBCT](https://pmc.ncbi.nlm.nih.gov/articles/PMC11869799/) décrit l'extrémité postérieure du palais osseux. Leur identité d'annotation sur un cliché latéral **n'est pas certifiée identique** à `PNS_Ricketts`. | **HOLD** : décider contour/cas ambigu, prouver l'équivalence source |

**Ne pas confondre preuve d'existence de la source et preuve clinique de l'image.** Les extraits du dépôt sont vérifiés textuellement au même HEAD par le script G14. Les sources web ne sont pas invoquées comme nouvel Atlas primaire et aucun passage protégé du livre n'est reproduit ou illustré artificiellement.

## Ce qu'il faut exactement obtenir de deux experts humains

Pour chacune des six cartes, et **avant** de retirer tout HOLD, obtenir séparément deux lectures A et B d'orthodontistes qualifiés, réels, identifiés dans un registre privé (jamais publics dans la PR). Utiliser **la même version scientifique** et une description de pixel/source-image par repère. Réponses à enregistrer sur un support clinique protégé :

1. **Edition/traçabilité :** références bibliographiques primaires exactes (édition Atlas2009 chapitre, page/figure avec permission légale), règle de placement opérationnelle et contrôles de source, validés indépendamment par A puis B.
2. **Image/ambiguïté :** identifier au moins un exemple autorisé où le point est visible et au moins un cas en double contour ou non visible ; classer `VISIBLE_UNAMBIGUOUS`, `VISIBLE_AMBIGUOUS`, `NOT_VISIBLE`, `NOT_APPLICABLE`. Aucun clic forcé si incertitude.
3. **Identité et équivalences :** expliquer les alias interdits et les cas de conflit `Pt≠PR`, `Gonion générique≠GO_PFH`, `U6 A6 ≠ règle L6`, `PNS générique≠PNS_Ricketts`; ne jamais masquer un manque de preuve par une substitution.
4. **Répétabilité :** annoter séparément les mêmes images, sans consulter l'autre expert ni les captures synthétiques de CI, répéter plus tard un sous-ensemble préenregistré et conserver tous les conflits et exclusions.
5. **Métrologie indépendante :** orientations antérieure/supérieure et mirroring sur même image ; pour les distances, étalon physique enregistré dans l'image et provenance du `mm_per_pixel` réellement prouvée. **ANUG/Challiyan publics n'ont pas d'étalon vérifié ici.**
6. **Décision motivée :** examiner chaque divergence A/B et signer le registre privé avec un troisième arbitrage préenregistré si nécessaire ; le logiciel G14 **n'accepte ni n'émet de verdict expert GO** sur la seule base de JSON.

### Jeu de fichiers et stratégie de données

- **Corpus de faisabilité :** ANUG (2014, Wikimedia), Challiyan (2023, Wikimedia), CC BY-SA 4.0, HASH SHA1 et SHA256 recontrôlés par G11 et G12. Les deux images sont **exposées au développeur**, n'appartiennent pas au corpus Aariz et ne constituent pas un jeu de validation final indépendant.
- **Aariz LOT02** : corpus distinct de 1 000 céphalogrammes dont 150 cas test réservés ; ne pas y introduire les deux images publiques par faux identifiant ni contaminer le test avec sélection post hoc. Aucun besoin de reprendre le poste distant `DESKTOP-3MAJEEH` pour la **démo publique**.
- **Données patient :** aucune dans ce lot. Les qualifications, annotations réelles et éventuels futurs clichés privés doivent rester sur un dispositif approuvé à accès contrôlé ; **ne pas les téléverser sur GitHub/CI, Notion ou une capture publique**.
- **Risque d'image non calibrée :** analyse éventuelle de répétabilité en pixels seulement, ne pas publier de résultat en mm ni valider des facteurs Atlas33 linéaires/signés.

## Contrôle automatisé et opérabilité de l'atelier

`scripts/cephalo_r23g14_six_hold_review_workbook.py` valide les **21** guides G13, les **six HOLD** et leur correspondance stricte aux sources exactes du dépôt, les **six cartes** avec questions explicites, les niveaux d'évidence externes (domaine NCBI/PubMed limité) et **tous** les booléens de non-approbation. Il construit l'atelier local G13/G12 sur les **deux fichiers JPEG originaux** et ajoute un panneau lecture seule affichant, à la sélection d'un HOLD, son hypothèse non autoritaire, ses questions d'arbitrage et ses sources sous forme textuelle. Il **ne débloque jamais** la création de points pour ces six identités.

`audit/cephalo_r23g14_contract_tests/test_six_hold_pack.py` vérifie les tentatives de promotion clinique, faux experts, sources malformées, alias, injection de coordonnées et dérives des citations. `g14_real_public_review_browser.cjs` vérifie dans Chromium 1280×900 et 1600×1000 **12 refus de clic par viewport** (six repères × deux vrais JPEG), sans succès clinique inventé. Les anciens tests navigateurs G12/G13 (clic, export brouillon) sont rejoués pour détecter une régression. Un rapport CI texte et des captures des deux radiographies publiques avec avertissements de HOLD sont publiés, avec attribution CC BY-SA 4.0 ; jamais les JPEG privés.

Exemple local après récupération légitime des deux originaux :

```bash
python -m scripts.cephalo_r23g14_six_hold_review_workbook \
  --input-dir /DOSSIER/DEUX_JPEG_WIKIMEDIA_ORIGINAUX \
  --output-dir /DOSSIER/ATELIER_G14_VIDE
python -m http.server 8765 --bind 127.0.0.1 --directory /DOSSIER/ATELIER_G14_VIDE
```

Puis ouvrir localement `http://127.0.0.1:8765/`. Ne pas modifier les booléens du dossier vers `true` pour simuler un arbitrage : toute telle mutation est refusée par la CI. Une éventuelle levée future sera une nouvelle décision documentée sur un HEAD propre avec vrais experts et validation distincte.

## Gate de clôture du sous-lot

**G14 peut atteindre GREEN en QA de préparation** (preuves exact HEAD, tests source/Chrome/sécurité et statut HOLD conservé). **G14 ne peut PAS atteindre clinical GO**, reviewer signatures ≥2, repère débloqué, goldset indépendant calibré ni 33/33 facteurs anatomiquement vérifiés sans vraie campagne externe. Deux relectures adversariales du code dans la même session restent **internes**, pas des reviewers humains indépendants. Pas de merge ou déploiement sans accord explicite.

**Roadmap :** G9 strict Atlas33/Aariz → G10 intake sécurisé → G11 originaux Wikimedia → G12 pixels interactifs → G13 21 guides + six HOLD → **G14 dossiers opérationnels d'arbitrage** → deux vrais orthodontistes et programme d'annotations → références calibrées → validation réelle des mesures Atlas33 → closeout.

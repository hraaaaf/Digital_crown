# Céphalo-N — Constructions primaires par analyse

Statut : **SOURCE-LOCK PRIMAIRE V2 — DÉCISION TWEED FERMÉE — ZÉRO CODE CLINIQUE**

Date : 2026-09-15

Dépend de :

- `docs/audits/CEPHALO_GLOBAL_ANALYSIS_VALIDATION.md`
- `docs/audits/CEPHALO_LANDMARKS_PLANES_SOURCE_LOCK.md`
- `docs/audits/CEPHALO_SRPOSE38_PROVENANCE.md`

## Goal / Succès / Preuve

**Goal** — verrouiller, analyse par analyse, les constructions géométriques réellement décrites par les sources primaires avant toute extension du moteur.

**Succès** — pour chaque construction critique : source/version, définition, convention Digital Crown actuelle et verdict `MATCH`, `PARTIAL`, `WRONG_VARIANT`, `MISSING`, `SOURCE_LOCK_REQUIRED` ou `SELECTED_DC_CONTRACT`.

**Preuve** — articles primaires Steiner 1953, Tweed 1954, Ricketts et al. 1972, Ricketts 1981 et McNamara 1984, recoupés avec les modules géométriques actuels de Digital Crown, plus décision clinique du 2026-09-15 de conserver `Po-Or` pour le Frankfort Tweed Digital Crown.

Aucune norme nouvelle, interprétation diagnostique ou modification de calcul n’est activée par ce document.

---

# 1. Verdict transversal

| Analyse/version | Construction critique | Source primaire / décision | DC actuel | Verdict |
|---|---|---|---|---|
| Steiner 1953 | SN, NA, NB, axes incisifs, Go-Gn | Steiner 1953 | modules dédiés correspondants | `MATCH/PARTIAL` selon landmark supply |
| Steiner 1953 | distances U1-NA / L1-NB | Steiner 1953 | volontairement absentes | `MISSING_CORONAL_SURFACE` |
| Tweed 1954 strict historique | Frankfort du triangle | Tweed 1954 | `Po-Or` | `WRONG_VARIANT_FOR_1954` si présenté comme strict historique |
| Digital Crown Tweed | Frankfort du triangle | décision clinique DC 2026-09-15 | `Po-Or` | **`SELECTED_DC_CONTRACT`** |
| Tweed | axe incisive inférieure apex→bord incisif | Tweed 1954 | apex→incisal | `MATCH` |
| McNamara 1984 | FH | Po anatomique-Orbitale | primitives Po-Or | `MATCH_GEOMETRY / AUTO_ID_UNVERIFIED` |
| McNamara 1984 | Nasion perpendicular | ⟂ FH par N | primitive réutilisable | `MATCH_GEOMETRY` |
| McNamara 1984 | Co-A / Co-Gn anatomique / ANS-Me | article 1984 | module linéaire dédié | `MATCH_GEOMETRY / LANDMARK_GATE` |
| McNamara 1984 | facial axis | PTM→Gn construit; angle avec Ba-N | pas encore contrat complet McNamara | `PARTIAL` |
| Ricketts 1981 | true FH | vrai Porion-Orbitale, pas ear-rod | Po-Or geometry | `MATCH_GEOMETRY / AUTO_ID_UNVERIFIED` |
| Ricketts 1981 | facial axis | Pt-Gn céphalométrique vs Ba-N | module dédié | `MATCH` au niveau construction |
| Ricketts 1981 | mandibular plane | FH vs `Sub.Go.-M.` | non implémenté en strict 1981 | `MISSING / SOURCE_LOCK_REQUIRED` |
| Ricketts 1981 | Oral Gnomon | ANS-Xi-Pm | absent | `MISSING` |
| Ricketts 1981 | PTV / U6 | PTV construit depuis région pterygoïdienne | absent en contrat strict | `MISSING / SOURCE_LOCK_REQUIRED` |
| Ricketts frontal 1981 | 12 facteurs | PA/frontale | pas de pipeline frontal validé | `BLOCKED_MODALITY` |

---

# 2. Steiner — 1953 core

Source primaire : Cecil C. Steiner, **“Cephalometrics for you and me”**, *American Journal of Orthodontics*, 1953;39(10):729-755. DOI `10.1016/0002-9416(53)90082-7`.

## 2.1 Constructions verrouillées

Le papier 1953 utilise explicitement :

- `SN` comme base de référence ;
- `NA` et `NB` pour la position sagittale A/B et les incisives ;
- l’axe de l’incisive supérieure par rapport à `NA` ;
- l’axe de l’incisive inférieure par rapport à `NB` ;
- l’angle inter-incisif comme mesure supplémentaire ;
- le plan occlusal par rapport à `SN` ;
- `Go-Gn` comme représentation du corps/plan mandibulaire dans ce protocole ;
- `GoGn-SN` et l’incisive inférieure par rapport à `Go-Gn`.

Le moteur `cephalo_steiner_geometry.py` contient déjà :

- SNA ;
- SNB ;
- ANB ;
- U1/NA angulaire ;
- L1/NB angulaire ;
- SN/Go-Gn.

**Verdict** : `MATCH_GEOMETRY` pour ces constructions, sous réserve que les landmarks injectés soient anatomiquement validés.

## 2.2 Distances incisives linéaires

La source primaire évalue la position linéaire de la couronne par rapport à NA/NB. Le module Digital Crown refuse volontairement de substituer le bord incisif à la surface/position coronaire requise.

**Verdict** : `CORRECTLY_FAIL_CLOSED`.

Bloquants :

- `U1_labial/mesial_crown` source-locké ;
- `L1_labial/mesial_crown` source-locké.

## 2.3 Steiner 1959

SND, point D/D-line et extensions 1959 restent une **couche de version séparée**.

Aucun `D_point` SRPose local ne peut être déclaré automatiquement équivalent au point D de Steiner 1959 sans source de définition et validation du canal.

**Verdict** : `SOURCE_LOCK_REQUIRED`.

---

# 3. Tweed — source historique 1954 et contrat Digital Crown retenu

Source primaire : Charles H. Tweed, **“The Frankfort-mandibular incisor angle (FMIA) in orthodontic diagnosis, treatment planning and prognosis”**, *Angle Orthodontist*, 1954;24:121-169.

Source de copie primaire vérifiée : PDF distribué par **The Tweed Foundation** dans sa liste de lecture officielle.

## 3.1 Frankfort historique de Tweed 1954

Le texte primaire décrit sa construction du Frankfort ainsi :

- point situé **4,5 mm au-dessus du centre géométrique de l’ear rod** ;
- relié au **bord inférieur de l’orbite**.

Il ne s’agit donc pas, dans ce papier 1954, d’un `Porion anatomique → Orbitale` strict.

### Digital Crown actuel

`cephalo_tweed_merrifield_geometry.py` calcule :

- FMA : `Go→Me` vs `Po→Or` ;
- IMPA : axe L1 apex→incisal vs `Go→Me` ;
- FMIA : axe L1 apex→incisal vs `Po→Or`.

Le code ne construit aucun point « 4,5 mm au-dessus du centre de l’ear rod ».

### Verdict historique

`DC_TWEED_PO_OR_V1 ≠ TWEED_1954_STRICT_FH`

Classification historique : `WRONG_VARIANT_FOR_TWEED_1954_STRICT` si l’on prétend reproduire mot pour mot la construction de 1954.

Cela ne signifie pas que `Po-Or` est une mauvaise référence clinique. Cela signifie seulement que la provenance doit être correctement nommée.

## 3.2 Incisive inférieure

Tweed décrit l’axe de l’incisive mandibulaire par une ligne passant par :

- l’apex ;
- le bord incisif.

Le module Digital Crown utilise `L1_apex → L1_incisal`.

**Verdict** : `MATCH_GEOMETRY`, sous réserve du mapping anatomique des deux points.

## 3.3 Décision clinique Digital Crown — fermée

Décision clinique du 2026-09-15 : **conserver notre façon de tracer Frankfort avec `Po-Or`** pour Tweed.

Contrat retenu :

`DC_TWEED_ANATOMICAL_FH_VARIANT = Porion anatomique → Orbitale`

Conséquences :

- FMA/FMIA actuels ne sont pas recalculés ni migrés ;
- aucune donnée patient ou document historique n’est modifié ;
- l’implémentation runtime actuelle reste inchangée ;
- `TWEED_1954_STRICT_EAR_ROD_FH` reste documenté comme variante historique non active ;
- l’UI et la documentation future ne doivent pas présenter la variante DC comme reproduction géométrique stricte du papier 1954 ;
- toute future couche normative Tweed doit versionner explicitement sa compatibilité avec `DC_TWEED_ANATOMICAL_FH_VARIANT`. Les normes historiques ne doivent pas être déclarées strictement concordantes avec une géométrie différente sans validation.

**Verdict Digital Crown** : `SELECTED_DC_CONTRACT`.

---

# 4. McNamara — 1984

Source primaire : James A. McNamara Jr., **“A method of cephalometric evaluation”**, *American Journal of Orthodontics*, 1984;86(6):449-469. DOI `10.1016/S0002-9416(84)90352-X`.

Source primaire hébergée par University of Michigan / McNamara Lab.

## 4.1 Frankfort et Nasion perpendicular

McNamara définit explicitement :

- **Porion anatomique** = aspect supérieur du méat auditif externe ;
- **Orbitale** = point le plus inférieur du rebord orbitaire osseux ;
- Frankfort = Po anatomique-Or ;
- Nasion perpendicular = ligne perpendiculaire à FH passant par N.

Il avertit explicitement que le machine porion/ear rod peut être éloigné du Porion anatomique.

**Verdict DC** :

- géométrie Po-Or : `MATCH_GEOMETRY` ;
- N-perp : `MATCH_GEOMETRY` ;
- liaison SRPose `Po`/`Or` : `LEGACY_AUTO_UNVERIFIED`.

## 4.2 Incisives

Procédure primaire :

- point A vertical = parallèle à N-perp passant par A ;
- distance à la **surface faciale de l’incisive supérieure** ;
- distance de la **surface faciale de l’incisive inférieure** à A-Pog.

Le bord incisif seul n’est donc pas une substitution suffisante pour ces distances.

**Verdict** : `MISSING_CORONAL_SURFACE` pour une implémentation stricte.

## 4.3 Mandibule et facial axis

McNamara demande :

- facial plane `N-Pog` ;
- mandibular plane `Go-Me` ;
- `Gn_constructed` = intersection de ces deux plans ;
- facial axis = aspect postéro-supérieur de la fissure ptérygo-maxillaire (`PTM`) → Gn construit ;
- référence craniale `Ba-N` ;
- Condylion = point le plus postéro-supérieur du contour condylien ;
- Co-A = longueur effective du midface ;
- Co-Gn **anatomique** = longueur mandibulaire effective ;
- ANS-Me = hauteur faciale antérieure inférieure.

Point critique : McNamara emploie **deux Gn différents selon l’usage** :

- `Gn_constructed` pour le facial axis ;
- `Gn_anatomic` pour Co-Gn.

**Décision DC obligatoire** : ces deux IDs ne doivent jamais partager silencieusement le même contrat.

## 4.4 Airway

Définitions primaires :

- upper pharynx = distance entre le contour postérieur du palais mou et le point le plus proche de la paroi pharyngée postérieure, sur la moitié antérieure du palais mou ;
- lower pharynx = distance entre l’intersection du bord postérieur de la langue avec le bord inférieur de la mandibule et le point le plus proche de la paroi pharyngée postérieure.

McNamara précise qu’une petite largeur supérieure n’est qu’un **indicateur de possible atteinte** et que le diagnostic requiert un examen ORL.

**Verdict** : `MISSING_LANDMARKS / FAIL_CLOSED_DIAGNOSTIC`.

---

# 5. Ricketts — contrat 1972 + Summary Descriptive Analysis 1981

Sources primaires :

1. Ricketts RM, Bench RW, Hilgers JJ, Schulhof R. **“An overview of computerized cephalometrics.”** *American Journal of Orthodontics*. 1972;61(1):1-28. DOI `10.1016/0002-9416(72)90172-8`.
2. Ricketts RM. **“Perspectives in the clinical application of cephalometrics. The first fifty years.”** *Angle Orthodontist*. 1981;51(2):115-150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

Le papier 1981 fournit la Summary Descriptive Analysis 11 latérale + 12 frontale. Le papier 1972 explicite plusieurs constructions informatiques utilisées dans cette famille.

## 5.1 True Frankfort

Ricketts 1981 précise que l’analyse latérale utilise le **true Frankfort horizontal basé sur le true porion plutôt que l’ear rod**. Le cue sheet donne le Facial Angle `N-Pog to FH (True Porion not Ear Rod)`.

**Verdict DC** : `MATCH_GEOMETRY` pour Po-Or, mais `AUTO_ID_UNVERIFIED` tant que le canal `Po` du détecteur n’est pas anatomiquement validé.

Cette convention est explicitement différente du Frankfort historique de Tweed 1954, tout en coïncidant avec le choix actif `Po-Or` de Digital Crown pour Tweed.

## 5.2 Facial axis et Gn céphalométrique

Ricketts 1981 :

- facial axis = `Pt-Gn` ;
- comparé à `Ba-N` ;
- Pt est au bord inférieur du foramen rotundum / région ptérygoïdienne décrite dans le papier.

Ricketts et al. 1972 explicite `cephalometric gnathion` comme l’intersection du **facial plane** et du **mandibular plane**.

Digital Crown :

`ricketts_constructed_gn_v1 = intersection(N-Pog, Go-Me)`

puis :

`ricketts_facial_axis_deg_v1 = angle(Ba-N, Pt-Gn_constructed)`.

**Verdict** : `MATCH_CONSTRUCTION`, sous réserve de `Ba`, `Pt`, `Pog`, `Go`, `Me` source-lockés au niveau input.

## 5.3 Pt vs PTM

Ricketts 1981 décrit Pt comme un point cranial au niveau du bord inférieur du foramen rotundum, au-dessus/en arrière du contour de la fosse ptérygo-palatine. La figure 9A le distingue de la construction PTV.

McNamara 1984 utilise pour son facial axis **l’aspect postéro-supérieur de la fissure ptérygo-maxillaire (PTM)**.

**Verdict** :

`Pt_Ricketts ≠ PTM_McNamara` sauf preuve explicite contraire.

Le mapping local `PT_point` et `Ptm` contient deux IDs séparés, ce qui est favorable, mais leur sémantique automatique reste non démontrée.

## 5.4 Xi et Pm

Ricketts 1981 :

- Xi = centre du ramus construit par bisection de sa hauteur et de sa profondeur/largeur ; figure 9B décrit la construction ;
- Pm/protuberance menti = point à la terminaison supérieure de l’os cortical dense de la symphyse, au début de la concavité au-dessus du menton ;
- corpus axis = Pm-Xi ;
- Oral Gnomon = angle `ANS-Xi-Pm`.

**Verdict DC** : `MISSING` pour Xi/Pm et Oral Gnomon stricts.

## 5.5 PTV et molaire supérieure

Ricketts 1981 figure 9A :

- PTV = verticale à true FH élevée depuis le point `PR` de la base des ailes ptérygoïdiennes ;
- la position de la molaire supérieure est mesurée en avant de PTV jusqu’au distal de la couronne.

Le cue sheet 1981 donne `Upper First Molar to PTV`.

Le simple ID SRPose local `U6` ne prouve ni le **point distal exact de la couronne**, ni le point de construction PTV.

**Verdict** : `MISSING_STRICT_CONTRACT`.

## 5.6 Mandibular plane 1981

Le cue sheet 1981 définit :

`Mandibular Plane (FH to Sub. Go.-M.)`

Cette écriture n’autorise pas à substituer silencieusement le `Go-Me` de Tweed/McNamara.

Digital Crown ne possède pas encore un contrat strict `Sub.Go.-M.` Ricketts 1981.

**Verdict** : `MISSING / SOURCE_LOCK_REQUIRED`.

## 5.7 Frontal 1981

Le cue sheet frontal confirme 12 facteurs, dont NC-NC, J→frontal facial plane, Ag-Ag, symétrie, B6-B6, B3-B3, relations molaires/fronto-denture et crossbite.

Aucune projection latérale ne peut fournir ces données.

**Verdict** : `BLOCKED_MODALITY`.

Le conflit normatif Ag-Ag reste `NORM_HOLD` : le cue sheet indique +1,25 mm/an alors que le tableau 9 donne +1,35 mm/an et ses valeurs âge 3→18 concordent avec +1,35.

---

# 6. Conséquences d’architecture

## 6.1 IDs à séparer obligatoirement

- `FH_TWEED_1954_EAR_ROD` ≠ `FH_DC_TWEED_PO_OR_V1` ; le second est le contrat Digital Crown retenu ;
- `Pt_Ricketts` ≠ `PTM_McNamara` ;
- `Gn_Ricketts_cephalometric` / `Gn_McNamara_constructed` doivent porter leur convention, même si leurs constructions peuvent coïncider ;
- `Gn_McNamara_anatomic` reste distinct du Gn construit ;
- `Pog_hard` ≠ `Pog_soft` ;
- `MP_TWEED_GO_ME` ≠ `MP_RICKETTS_SUB_GO_M` ;
- `U6_Ricketts_distal_crown` ≠ un `U6` générique non défini.

## 6.2 Réutilisation autorisée

Une primitive mathématique peut être partagée si son **contrat sémantique** reste versionné. Exemple : angle entre deux lignes, projection perpendiculaire, distance signée.

Une ligne clinique ne doit pas être partagée uniquement parce qu’elle utilise deux coordonnées aux noms ressemblants.

---

# 7. Gates scientifiques

## Gate A — Tweed geometry

**Fermé.** Contrat retenu : `DC_TWEED_ANATOMICAL_FH_VARIANT = Po-Or`. Aucun changement runtime n’est nécessaire, puisque le moteur calcule déjà FMA/FMIA avec `Po-Or`.

Le contrat historique `TWEED_1954_STRICT_EAR_ROD_FH` reste documenté mais non actif.

La compatibilité des **normes historiques strictes** avec la variante DC reste un sujet distinct de source-lock normatif ; elle ne doit pas être supposée par simple héritage du nom « Tweed ».

## Gate B — SRPose semantics

**Ouvert.** Le mapping local est `LEGACY_AUTO_UNVERIFIED`; ce document source-locke les **définitions attendues**, pas la vérité anatomique des 38 canaux.

## Gate C — Ricketts PA

**Bloqué par modalité.** Une téléradiographie latérale ne peut pas fournir les 12 facteurs frontaux.

---

# 8. Next exact

1. matérialiser `DC_TWEED_ANATOMICAL_FH_VARIANT = Po-Or` dans les futurs contrats scientifiques sans modifier les valeurs runtime ;
2. écrire les contrats scientifiques de landmarks/constructions restants ;
3. créer des fixtures manuelles source-lockées pour tester les primitives géométriques ;
4. n’implémenter une nouvelle mesure qu’après fermeture de son gate landmark + plan/ligne + modalité ;
5. traiter séparément le source-lock des normes Tweed pour la variante DC.

Aucune mesure clinique, norme ou interprétation n’a été modifiée dans ce lot.
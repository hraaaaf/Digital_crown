# SRPose38 — LANDMARK CONTRACT

**Parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Statut :** ordre/noms certifiés ; définitions COM critiques partiellement certifiées ; ambiguïtés explicites.

## CONTRAT D'ORDRE

Le modèle SRPose38 émet 38 sorties `0..37`. Le dataset CL-Detection2023 les définit dans le même ordre que ses landmarks `1..38` :

`runtime_index = CL_number - 1`

| idx | CL | Landmark | ID Digital Crown |
|---:|---:|---|---|
|0|1|Sella|S|
|1|2|Nasion|N|
|2|3|Orbitale|Or|
|3|4|Porion|Po|
|4|5|Subspinale|A|
|5|6|Supramental|B|
|6|7|Pogonion|Pog|
|7|8|Menton|Me|
|8|9|Gnathion|Gn|
|9|10|Gonion|Go|
|10|11|Incision Inferius / Lower Incisor|L1_incisal|
|11|12|Incision Superius / Upper Incisor|U1_incisal|
|12|13|Upper Lip|Ls_soft|
|13|14|Lower Lip|Li_soft|
|14|15|Subnasale|Sn_soft|
|15|16|Soft Tissue Pogonion|Pog_soft|
|16|17|Posterior Nasal Spine|PNS|
|17|18|Anterior Nasal Spine|ANS|
|18|19|Articulare|Ar|
|19|20|D|D_point|
|20|21|U1A|U1_apex|
|21|22|L1A|L1_apex|
|22|23|Columella|Cm|
|23|24|Pterygomaxillary Fissure|Ptm|
|24|25|Condylion|Co|
|25|26|Pronasale|Prn|
|26|27|Basion|Ba|
|27|28|PT|PT_point|
|28|29|Bolton|Bo|
|29|30|UL'|Ls2|
|30|31|LL'|Li2|
|31|32|Gnathion of Soft Tissue|Gn_soft|
|32|33|Menton of Soft Tissue|Me_soft|
|33|34|Glabella|G_soft|
|34|35|Nasion of Soft Tissue|N_soft|
|35|36|Cervical Point|C_point|
|36|37|Upper Molar|U6|
|37|38|Lower Molar|L6|

## SOURCES DE PROVENANCE

### Ordre SRPose / CL-Detection

- Hongyuan Zhang et al., *Deep Learning Techniques for Automatic Lateral X-ray Cephalometric Landmark Detection: Is the Problem Solved?*, 2024. La Figure 3 fournit les 38 noms dans l'ordre CL-Detection. https://arxiv.org/html/2409.15834v1
- Repo SRPose `5k5000/CLdetection2023`, commit `18d17d1934970016e7610c4849311900b8d1f191`, configuration MMPose `cephalometric.py` : exactement 38 sorties indexées `0..37`.
- Runtime Digital Crown PR #388 : mapping modèle et pipeline ONNX intégrés.

### Définitions anatomiques de contrôle

Deux sources peer-reviewed indépendantes sont utilisées pour les points COM critiques :

- *Artificial-Intelligence-Based Cephalometric Landmark Detection in Lateral Cephalograms*, Table 1 : définitions S, N, Or, Po, A, B et autres points classiques. https://pmc.ncbi.nlm.nih.gov/articles/PMC13466904/
- *Accuracy of computerized automatic identification of cephalometric landmarks by a designed software*, Table 1 : définitions A, B, ANS, PNS, Gn, Go, Me, N, Or, Po, Pog, S et apex/bords incisifs. https://pmc.ncbi.nlm.nih.gov/articles/PMC3746488/

Source de contrôle supplémentaire :

- *Incisor and Soft Tissue Characteristics of Adult Bimaxillary Protrusion Patients among Different Skeletal Anteroposterior Classifications*, Table 1. https://pmc.ncbi.nlm.nih.gov/articles/PMC11119585/

## DÉFINITIONS OPÉRATIONNELLES — LANDMARKS COM CRITIQUES

| ID | Définition opérationnelle retenue | Sources concordantes | État |
|---|---|---|---|
| `S` | centre géométrique de la selle turcique / fosse hypophysaire sur le cliché latéral | Zhang/CL-Detection + PMC13466904 + PMC3746488 | `CERTIFIED_FOR_GEOMETRY` |
| `N` | point le plus antérieur de la suture fronto-nasale sur le plan médian | PMC13466904 + PMC3746488 + PMC11119585 | `CERTIFIED_FOR_GEOMETRY` |
| `Or` | point le plus inférieur du rebord orbitaire visible | PMC13466904 + PMC3746488 | `CERTIFIED_FOR_GEOMETRY` |
| `Po` | point le plus supérieur du méat acoustique externe anatomique visible | PMC13466904 + PMC3746488 | `CERTIFIED_WITH_CAUTION` |
| `A` | point médian le plus profond de la concavité antérieure maxillaire entre ANS et le procès/alvéole incisif | PMC13466904 + PMC3746488 + PMC11119585 | `CERTIFIED_FOR_GEOMETRY` |
| `B` | point médian le plus profond de la concavité antérieure de la symphyse mandibulaire entre région alvéolaire incisive et Pog | PMC13466904 + PMC3746488 + PMC11119585 | `CERTIFIED_FOR_GEOMETRY` |
| `Me` | point le plus inférieur du contour de la symphyse mandibulaire | PMC3746488 + PMC11119585 | `CERTIFIED_FOR_GEOMETRY` |
| `L1_incisal` | bord/tip incisif de l'incisive mandibulaire de référence | PMC3746488 + CL-Detection #11 | `CERTIFIED_FOR_GEOMETRY` |
| `U1_incisal` | bord/tip incisif de l'incisive maxillaire de référence | PMC3746488 + CL-Detection #12 | `CERTIFIED_FOR_GEOMETRY` |
| `L1_apex` | apex radiculaire de l'incisive mandibulaire de référence | PMC3746488 + CL-Detection #22 | `CERTIFIED_FOR_GEOMETRY` |
| `U1_apex` | apex radiculaire de l'incisive maxillaire de référence | PMC3746488 + CL-Detection #21 | `CERTIFIED_FOR_GEOMETRY` |
| `Go` | landmark gonial. Les sources ne sont pas parfaitement uniformes : point postéro-inférieur anatomique vs point construit par bissectrice des tangentes au ramus et bord inférieur | PMC3746488 + littérature classique | `ANALYSIS_DEFINITION_REQUIRED` |

## AMBIGUÏTÉS À NE PAS MASQUER

### Porion

La littérature distingue parfois **porion anatomique** et **machine porion/ear rod**. SRPose38 fournit un landmark `Porion` détecté sur l'image. Digital Crown ne doit pas substituer silencieusement un ear-rod à ce point. Toute analyse qui exige un autre type de Porion doit le déclarer explicitement.

### Gonion

`Go` est le principal gate COM restant parmi les repères de base : une définition comme « point postéro-inférieur de l'angle mandibulaire » et un **Gonion construit** par tangentes/bissectrice ne sont pas interchangeables mathématiquement. Le registre d'analyse devra définir lequel COM/Tweed utilise avant certification de FMA/IMPA.

### Incisives

Le modèle fournit un bord incisif et un apex pour chaque incisive de référence, ce qui permet de définir l'axe long. Le choix de la dent représentative lorsqu'il existe un dédoublement radiographique doit rester celui de la convention source de l'analyse ; il ne sera pas deviné par une règle locale.

## DÉCISION DE COMPATIBILITÉ

Ne pas renommer brutalement les IDs runtime existants. Maintenir un registre canonique avec alias de compatibilité, puis migrer les consommateurs avec tests.

## GATE LOT 3

Pour chaque point consommé par une analyse :

1. définition anatomique opérationnelle ;
2. synonymes/alias ;
3. ambiguïtés documentées ;
4. ≥2 sources sérieuses lorsque disponibles ;
5. dépendances géométriques ;
6. comportement `NOT_COMPUTABLE` en absence/incertitude critique.

## ÉTAT LOT 3

**COM critique : partiellement fermé.** Tous les repères de base nécessaires au COM sont définis sauf la convention exacte de `Go` à rattacher à la source COM/Tweed et la définition autoritative des constructions `A'`, `B'` / verticale de Nasion.

## NEXT EXACT

1. identifier la définition COM/Tweed autoritative du plan mandibulaire/Gonion ;
2. identifier la construction autoritative `A'B'` et verticale de Nasion utilisée par la fiche COM ;
3. matérialiser ces constructions dans le registre Lot 4 ;
4. écrire des golden tests géométriques avant toute norme clinique.

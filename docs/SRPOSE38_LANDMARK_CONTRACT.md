# SRPose38 — LANDMARK CONTRACT

**Parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Statut :** ordre/noms certifiés ; définitions opérationnelles détaillées encore ouvertes.

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

- CL-Detection2023 / article associé : nomenclature des 38 points et dataset multi-centre.
- Repo SRPose `5k5000/CLdetection2023`, configuration MMPose : 38 keypoints indexés `0..37`.
- Runtime Digital Crown PR #388 : mapping modèle et pipeline ONNX intégrés.

## DÉCISION

Ne pas renommer brutalement les IDs runtime existants. Introduire/maintenir un registre canonique avec alias de compatibilité, puis migrer les consommateurs avec tests.

## GATE LOT 3

Pour chaque point consommé par une analyse, documenter :
- définition anatomique opérationnelle ;
- synonymes/alias ;
- ambiguïtés éventuelles ;
- source ;
- dépendances géométriques ;
- comportement en absence/incertitude.

## NEXT

Priorité aux landmarks COM : S, N, Or, Po, A, B, Me, Go, U1/L1 incisal et apex.

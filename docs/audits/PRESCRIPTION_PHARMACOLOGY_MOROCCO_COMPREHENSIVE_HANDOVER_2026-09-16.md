# HANDOVER — Digital Crown — Référentiel thérapeutique & bucco-dentaire Maroc

Date: 2026-09-16
Status: ACTIVE — CONTINUE IN NEW CONVERSATION
Repository: `hraaaaf/Digital_crown`
Working branch: `docs/pharmacology-m1-handover-20260915`
Branch HEAD at handover start: `04da3d71b23ed7087c873cc9e0f01b26b77aae4a`
Master HEAD verified at handover start: `bdaaf53de219512cbbd286d5691eedff47f3c9d8`

## 1. GOAL CANONIQUE

Construire pour Digital Crown un référentiel marocain aussi complet que raisonnablement démontrable de ce qu'un chirurgien-dentiste peut prescrire, recommander ou utiliser pour les soins/prévention bucco-dentaires au Maroc.

Le référentiel doit couvrir deux grands ensembles :

1. médicaments et thérapeutiques cliniques ;
2. OTC, parapharmacie, hygiène, prévention, orthodontie, implant/parodonte, prothèse amovible et autres produits bucco-dentaires pertinents pour le patient.

Le projet n'est PAS limité aux 7 molécules Wave 1 historiques et n'est PAS un simple chantier de téléchargement de RCP.

## 2. SUCCÈS

Pour chaque médicament, documenter seulement lorsque la preuve le permet :
- DCI ;
- spécialités/formes marocaines vérifiables ;
- dosage/concentration ;
- indication dentaire ;
- posologie adulte ;
- posologie pédiatrique pondérale si applicable ;
- âge/poids ;
- durée ;
- dose maximale ;
- contre-indications ;
- précautions ;
- interactions ;
- sources et statut de preuve.

Pour chaque produit non médicamenteux :
- catégorie ;
- composition/actifs importants si pertinent ;
- usage/indication ;
- population/âge ;
- mode et fréquence d'utilisation ;
- précautions/contre-indications si applicables ;
- exemples/formes disponibles au Maroc quand vérifiables ;
- sources et statut de preuve.

Succès final = couverture auditée + données cliniques validées + provenance traçable + aucune donnée clinique incertaine promue automatiquement.

## 3. RÈGLES DE SÉCURITÉ — NON NÉGOCIABLES

- Fail closed sur dose, âge, poids, durée, maximum, contre-indications et interactions incertains.
- Ne jamais inventer une spécialité marocaine, une AMM, une posologie, une présentation ou un RCP.
- Une absence de lien/RCP public AMMPS ne prouve pas une absence réglementaire.
- Les sources étrangères peuvent soutenir la pharmacologie clinique mais ne prouvent pas une autorisation/commercialisation marocaine.
- Ne jamais déduire molécule, dose ou posologie depuis les actes dentaires/NGAP.
- Aucun mécanisme de prescription clinique ne doit être activé avant validation du dataset correspondant.
- Les entrées incomplètes restent explicitement `TO_VALIDATE`, `TO_VERIFY_MA`, `SPECIALIST_OR_EXCEPTION`, etc.

## 4. DÉCISION PROPRIÉTAIRE — AMMPS

Décision explicite du propriétaire le 2026-09-16 : **NE RIEN ENVOYER À L'AMMPS**.

Donc :
- aucun formulaire ;
- aucun email ;
- aucun appel/contact ;
- aucune demande externe.

La recherche publique AMMPS en lecture seule reste autorisée.

Le brouillon de demande AMMPS existant est archivé `DO NOT SEND`. Toute réactivation exige une nouvelle autorisation explicite du propriétaire.

## 5. INVENTAIRE MAÎTRE EXISTANT

Fichier :
`docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_MASTER_INVENTORY_2026-09-16.csv`

État constaté avant handover : inventaire déjà structuré avec **170 entrées recensées** :
- **68 médicaments** ;
- **102 oral-care / adjacent-care**.

Ces nombres décrivent l'inventaire recensé actuel ; ils ne constituent PAS une preuve d'exhaustivité finale.

### Médicaments déjà recensés — familles

- antalgiques/antipyrétiques ;
- AINS ;
- antibiotiques et associations pertinentes ;
- antifongiques ;
- antiviraux ;
- muqueuse orale ;
- anesthésiques locaux/topiques et vasoconstricteurs ;
- hémostase ;
- xérostomie médicamenteuse ;
- sédation ;
- médicaments/gaz d'urgence au cabinet.

### Oral-care / para déjà recensé — familles

- dentifrices : fluorés, pédiatriques, haut fluor, sensibilité, érosion, blanchiment, SLS-free, bouche sèche, hydroxyapatite ;
- bains de bouche : chlorhexidine, CPC, huiles essentielles, fluor, peroxyde, hexétidine, povidone iodée, dioxyde de chlore, zinc, benzydamine, salin, bicarbonate ;
- fluor professionnel, SDF ;
- reminéralisation ;
- xérostomie/substituts salivaires ;
- brosses manuelles/électriques/pédiatriques/ortho/post-chirurgicales/prothèse ;
- gratte-langue ;
- fil dentaire, tape, PTFE, Superfloss, enfile-fil, brossettes, picks, irrigateurs ;
- hygiène implant/parodontale ;
- adhésifs/fixatifs de prothèse : crème, poudre, bande, pad ;
- nettoyants et accessoires de prothèse ;
- orthodontie : cire, silicone de protection, nettoyants aligneurs/appareils, boîtes ;
- hypersensibilité ;
- halitose ;
- blanchiment pertinent au soin ;
- gels/films/patchs de muqueuse ;
- révélateurs de plaque ;
- chewing-gum/xylitol ;
- protège-dents ;
- produits de dentition avec safety review ;
- sevrage tabagique adjacent-care lorsque pertinent.

## 6. PÉRIMÈTRE À NE PAS OUBLIER

Le propriétaire a explicitement demandé : **"tout ce qui est para... faut rien oublier"**.

L'audit de couverture doit donc rechercher activement les trous, notamment :
- prévention carieuse par âge/risque ;
- parodontologie et implants ;
- orthodontie fixe/aligneurs/contention ;
- prothèses amovibles ;
- pédiatrie ;
- xérostomie ;
- halitose ;
- hypersensibilité ;
- érosion ;
- mucites/aphtes/irritations ;
- post-opératoire et post-extraction non médicamenteux ;
- blanchiment supervisé/recommandé ;
- prévention des traumatismes buccaux ;
- produits patient réellement recommandés par les dentistes au Maroc.

### Hors périmètre par défaut

- cosmétiques purs sans bénéfice bucco-dentaire démontré ;
- gadgets marketing sans indication/usage dentaire établi ;
- matériaux restaurateurs, instruments, équipements et dispositifs techniques du cabinet nécessitant un référentiel matériel/matériovigilance distinct ;
- recommandations commerciales non sourcées.

## 7. SOURCES / PROVENANCE

Pour les faits cliniques à risque : validation croisée par au moins 2 sources sérieuses, primaires si possible ; troisième source si divergence ou risque élevé.

Séparer systématiquement :
1. preuve d'existence/présentation au Maroc ;
2. preuve réglementaire marocaine quand disponible ;
3. preuve pharmacologique/clinique ;
4. recommandation d'usage/hygiène ;
5. simple présence commerciale, qui ne vaut pas validation clinique.

AMMPS public peut être utilisé en lecture seule pour le contexte marocain.

## 8. HISTORIQUE RCP À CONSERVER SANS LE CONFONDRE AVEC LE GOAL

Le chantier RCP historique a établi une infrastructure de provenance stricte.

Invariant `SNAPSHOT_VERIFIED` : document AMMPS officiel exact + URL exacte + date + PDF local réel + bytes + SHA + présentation exacte + revue indépendante.

Les 7 anciennes familles Wave 1 restent non activées lorsque la preuve réglementaire marocaine requise manque :
- paracétamol ;
- ibuprofène ;
- amoxicilline ;
- pénicilline V ;
- métronidazole ;
- clarithromycine ;
- clindamycine.

Ce travail reste une couche de provenance, pas la définition du nouveau périmètre.

## 9. TRAVAIL DÉJÀ VÉRIFIÉ HISTORIQUEMENT

Merges historiques pharmacologie :
- M1-A PR #517 → `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`
- M1-B0 PR #518 → `81bf142021cdf4770e9c6ca92078306ac4898783`
- M1-B1 PR #519 → `21651f22df9ba5210078969aa46abc527ba9e2bd`
- Wave 1 evidence refresh PR #522 → `12f2550aaa38f3045095152ab862b587db109238`
- deterministic gate PR #526 → `a396acfd6570ff24ca683009e1f31bdb3f2c0d92`
- gate repair PR #537 → `fb3a870e2fba92a005a3e3de57ee378042b23be3`
- M1-B2 PR #525 → `601cee32bab3169143cf61ca917e35d7bd1d6ee5`

M1-B2 historique : 33 tests ciblés passés + oracle déterministe PASS + revue indépendante sans blocker/major/missing tests, mais `clinical_activation_authorized=false`.

Ne pas réutiliser ces preuves comme validation du nouveau référentiel complet.

## 10. ÉTAT DE BRANCHE AU HANDOVER

Working branch : `docs/pharmacology-m1-handover-20260915`

HEAD vérifié juste avant création du présent handover :
`04da3d71b23ed7087c873cc9e0f01b26b77aae4a`

Dernier commit alors observé :
`docs(pharmacology): add inventory gap addendum`

Master vérifié au même moment :
`bdaaf53de219512cbbd286d5691eedff47f3c9d8`

Important : au démarrage d'une nouvelle conversation, re-vérifier immédiatement master HEAD + working branch HEAD avant toute écriture.

## 11. NEXT EXACT — NOUVELLE CONVERSATION

1. Lire ce handover.
2. Re-vérifier `master` HEAD et `docs/pharmacology-m1-handover-20260915` HEAD.
3. Lire intégralement :
   - `PRESCRIPTION_PHARMACOLOGY_MOROCCO_MASTER_INVENTORY_2026-09-16.csv` ;
   - `PRESCRIPTION_PHARMACOLOGY_MOROCCO_M1_INTERNAL_CONTINUATION_2026-09-16.md` ;
   - le gap addendum le plus récent présent sur la branche.
4. Auditer les **170 entrées recensées** pour doublons, catégories manquantes et trous de couverture.
5. Compléter d'abord la taxonomie/inventaire ; ne pas commencer par remplir massivement les posologies.
6. Une fois l'inventaire stabilisé, enrichir par lots cliniques cohérents avec validation croisée.
7. Pour chaque donnée clinique incertaine : rester fail-closed.
8. Préparer ensuite revue indépendante avant toute promotion/activation clinique.

## 12. SÉQUENCE RESTANTE

Taxonomie exhaustive → audit des trous → inventaire maître stabilisé → preuve Maroc par entrée → enrichissement clinique par familles → validation croisée → tests de cohérence/déterminisme → revue indépendante → correction des findings → décision explicite sur activation clinique → closeout/merge.

## 13. CRITÈRE DE CLOSEOUT

Ne pas déclarer le référentiel complet/VERIFIED tant que :
- couverture non auditée ;
- entrées critiques manquantes ;
- champs cliniques critiques non sourcés ;
- contradictions non résolues ;
- revue indépendante requise absente ;
- tests/gates applicables non verts.

Aucun pourcentage global n'est fixé dans ce handover faute de métrique d'exhaustivité finale démontrée.

---

NEXT EXACT: audit exhaustif des 170 entrées + gap analysis de couverture avant enrichissement clinique.

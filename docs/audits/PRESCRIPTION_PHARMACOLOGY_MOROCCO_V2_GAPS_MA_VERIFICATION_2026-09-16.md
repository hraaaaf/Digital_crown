# Digital Crown — V2 gaps — vérification Maroc

Date: 2026-09-16
Status: MARKET/PROVENANCE PASS — NO CLINICAL ACTIVATION

## Goal
Vérifier au Maroc les quatre lignes ajoutées par `PRESCRIPTION_PHARMACOLOGY_MOROCCO_INVENTORY_ADDENDUM_V2_2026-09-16.csv`, en séparant strictement :
1. présence commerciale au Maroc ;
2. preuve réglementaire marocaine ;
3. preuve clinique internationale ;
4. activation clinique Digital Crown.

Aucun contact AMMPS n'a été effectué.

## Résultats

### OC-INT-013 — floss holder / reusable floss handle
**Présence marché Maroc : VERIFIED_MARKET_MA**

Preuves croisées :
- GUM Maroc (`gum.co.ma`) référence le `Fil Flosbrush Réf : 847` dans sa gamme de fils dentaires.
- MaPara Maroc référence `GUM FIL DENTAIRE FLOSBRUSH` et le décrit comme `porte-fil` avec environ 250 utilisations.
- Jumia Maroc référence également `Gum Fil Flosbrush 250 usages Réf : 847` comme porte-fil dentaire.

Conclusion : la famille porte-fil réutilisable/assisté est réellement représentée sur le marché marocain.

**Preuve réglementaire Maroc : NOT_ASSESSED / NOT_REQUIRED_FOR_MARKET_CLAIM**
Cette passe ne transforme pas une présence commerciale de dispositif/accessoire en validation réglementaire.

**Clinical activation : NO**

Sources :
- https://www.gum.co.ma/fils-dentaires/
- https://mapara.ma/dentaire/1909-gum-fil-dentaire-flosbrush.html
- https://www.jumia.ma/ar/gum-fil-flosbrush-250-usages-ref-847-flossette-porte-fil-dentaire-brossette-batonnet-brosse-a-dents-67657573.html

### OC-FLUOR-004 — prescription/high-strength home-use fluoride gel
**Présence marché Maroc : VERIFIED_MARKET_MA**

Produit observé : `X-Pur NaF Gel 120 ml`, fluorure de sodium 1,1 % / 5 000 ppm F.

Preuves croisées Maroc :
- Parapharmacie Casablanca : fiche active et achetable au Maroc.
- Nova Para : fiche Maroc du même produit.
- ParaFarmacia.ma : fiche Maroc du même produit.

Preuve fabricant : Oral Science documente `X-PUR NaF Gel`, 1,1 % NaF / 5 000 ppm F.

Conclusion : la famille gel fluoré forte concentration à domicile est réellement présente commercialement au Maroc.

**Preuve réglementaire AMMPS : TO_VERIFY_MA**
Aucune preuve AMMPS publique exacte n'a été établie dans cette passe. La présence en parapharmacie ne vaut ni AMM ni statut de prescription marocain.

**Clinical activation : NO**

Sources :
- https://parapharmaciecasablanca.ma/product/x-pur-naf-gel-120ml-2/
- https://novapara.ma/products/x-pur-naf-gel-120ml
- https://parafarmacia.ma/produit/x-pur-naf-gel-120ml/
- https://mail.oralscience.com/fr/produits/gel-naf/

### OC-TEETH-002 — firm/chilled teething ring
**Présence marché Maroc : VERIFIED_MARKET_MA**

Preuves croisées :
- GoBébé Maroc : anneaux de dentition réfrigérants MAM/Mammia disponibles.
- ABM Para Maroc : Bébé Confort anneau de dentition à réfrigérer.
- Nova Para Maroc : MAM anneau de dentition réfrigérant +4m.
- KINGPHAR Maroc : Bébé Confort anneau de dentition à réfrigérer.

Conclusion : la famille non médicamenteuse `anneau de dentition réfrigéré` est clairement représentée au Maroc.

**Preuve réglementaire médicament : N/A**
Accessoire non médicamenteux dans ce référentiel ; les règles de sécurité produit restent applicables.

**Clinical activation : NO**

Sources :
- https://gobebe.ma/anneau-de-dentition/
- https://abmpara.ma/product/bebe-confort-anneau-de-dentition-a-refrigerer-bleu-4-24m/
- https://novapara.ma/products/mam-anneau-de-dentition-refrigerant-4m
- https://kingphar.ma/bebe-maman/32265-bebe-confort-anneau-de-dentition-a-refrigerer.html

### MED-FLUOR-001 — dietary fluoride supplement drops/tablets/lozenges
**Présence marché Maroc : TO_VERIFY_MA**

Aucune source publique actuelle suffisamment fiable n'a été trouvée dans cette passe pour démontrer une spécialité commercialisée/autorisation marocaine exacte de supplément fluoré systémique.

Des sources étrangères documentent la classe et des spécialités telles que ZYMAFLUOR, mais elles ne prouvent pas le statut Maroc. Elles ne doivent donc pas être utilisées pour renseigner une présentation, une dose ou une autorisation marocaine.

**Preuve réglementaire Maroc : TO_VERIFY_MA**
**Clinical activation : NO**

## Statuts à reporter dans le dataset
- `OC-INT-013` → `VERIFIED_MARKET_MA` ; source Maroc = `MA_MARKET_CROSSCHECKED`.
- `OC-FLUOR-004` → `VERIFIED_MARKET_MA` ; source Maroc = `MA_MARKET_CROSSCHECKED_REGULATORY_PENDING`.
- `OC-TEETH-002` → `VERIFIED_MARKET_MA` ; source Maroc = `MA_MARKET_CROSSCHECKED`.
- `MED-FLUOR-001` → rester `TO_VERIFY` / `TO_VERIFY_MA`.

## Guardrails
- `VERIFIED_MARKET_MA` signifie seulement présence commerciale marocaine croisée ; ce n'est pas une AMM, un RCP ou une validation clinique.
- aucune posologie ou concentration n'est promue vers un moteur de prescription sans validation clinique/réglementaire correspondante ;
- aucune absence de résultat public AMMPS ne prouve une absence réglementaire ;
- aucun contact AMMPS ;
- `clinical_activation = NO` pour les quatre lignes.

## Next exact
Reporter les trois statuts `VERIFIED_MARKET_MA` dans `MASTER_DATASET_V1`, conserver `MED-FLUOR-001` fail-closed, puis introduire la normalisation canonique des doublons sans suppression historique.

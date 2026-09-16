# Digital Crown — Maroc — Para bucco-dentaire — clinical taxonomy pass 3

Date: 2026-09-17
Status: TAXONOMY / CLINICAL FAMILY VALIDATION — MOROCCO PRODUCT PROOF SEPARATE — NO CLINICAL ACTIVATION

## Goal
Fermer la macro-taxonomie para restante : orthodontie/aligners/retainers, implant/perio, prothèses amovibles, blanchiment, post-op, protection traumatique et pédiatrie.

## Orthodontie / aligners / retainers
Familles distinctes à inventorier :
- brosse orthodontique / mono-touffe;
- brossettes interdentaires et aides adaptées aux brackets;
- fil/superfloss/threader selon dispositif;
- irrigateur comme adjuvant, pas substitut universel;
- cire orthodontique pour irritation mécanique temporaire;
- nettoyant pour aligner/retainer/appareil amovible;
- boîte de rangement ventilée adaptée au dispositif;
- produits fluorés ou reminéralisants uniquement selon risque/indication, pas automatiquement parce que le patient est orthodontique.

L'ADA insiste sur le maintien des soins dentaires et de l'hygiène pendant le traitement orthodontique et reconnaît les nettoyants pour appareils dentaires amovibles comme catégorie distincte. Les claims de nettoyants restent produit-spécifiques.

Statut: `CLINICAL_FAMILY_SUPPORTED`; produit Maroc: `TO_VERIFY_BY_PRODUCT`; activation: `NO`.

Sources:
- https://www.ada.org/resources/ada-library/oral-health-topics/home-care
- https://www.ada.org/resources/research/science/ada-seal-of-acceptance/ada-seal-category-requirements-overview

## Implant / parodonte
Familles à inventorier sans créer de fausse catégorie « implant-only » lorsqu'un dispositif standard suffit :
- brosse manuelle/électrique adaptée;
- brossettes interdentaires dimensionnées;
- fil/superfloss/threader selon architecture prothétique;
- irrigateur adjuvant;
- brosse mono-touffe;
- produits antimicrobiens uniquement si indication clinique spécifique.

Règle taxonomique : préférer un `indication_tag=implant/perio` sur les aides génériques plutôt que dupliquer le même produit comme nouvelle entité. Les bains antimicrobiens ne remplacent pas l'hygiène mécanique.

Statut: `CLINICAL_FAMILY_SUPPORTED`; activation: `NO`.

Source:
- https://www.ada.org/resources/ada-library/oral-health-topics/home-care

## Prothèses amovibles
Familles distinctes :
- brosse à prothèse;
- nettoyant prothèse/appareil amovible : comprimé, solution, crème/pâte/gel selon produit;
- adhésif : crème, poudre, wafer/strip selon produit;
- boîte de stockage;
- reline/rebasage OTC : `SAFETY_REVIEW_REQUIRED`, ne pas assimiler à une correction clinique durable d'une prothèse mal adaptée.

ADA/ACP : nettoyage quotidien; les nettoyants ne doivent pas être utilisés dans la bouche; éviter l'eau chaude/bouillante qui peut déformer la prothèse. Les adhésifs peuvent améliorer temporairement rétention/stabilité mais ne corrigent pas une prothèse mal adaptée. Certains adhésifs contiennent du zinc; l'usage excessif est un risque et l'ACP recommande par précaution d'éviter les adhésifs contenant du zinc.

Statut: nettoyants/adhésifs `CLINICAL_FAMILY_SUPPORTED`; reline OTC `SAFETY_REVIEW_REQUIRED`; Maroc `TO_VERIFY_BY_PRODUCT`; activation `NO`.

Source:
- https://www.ada.org/resources/ada-library/oral-health-topics/dentures

## Blanchiment / stain removal
Séparer :
- dentifrice détachant/blanchissant (principalement action sur taches extrinsèques selon produit);
- strips OTC;
- gel OTC paint-on/tray;
- gouttière personnalisée + gel fourni/supervisé par dentiste;
- blanchiment au fauteuil;
- blanchiment interne dent non vitale = acte clinique, pas para grand public.

Actifs principaux documentés : peroxyde d'hydrogène et peroxyde de carbamide. Effets indésirables fréquents : sensibilité dentaire transitoire et irritation gingivale. Seules les dents naturelles blanchissent; les restaurations couleur dent ne blanchissent pas de la même manière. AAPD déconseille le blanchiment cosmétique arcade complète en denture primaire ou mixte.

Statut: `CLINICAL_FAMILY_SUPPORTED`; concentration/protocole/âge `PRODUCT_OR_PROTOCOL_SPECIFIC`; Maroc `TO_VERIFY_BY_PRODUCT`; activation `NO`.

Source:
- https://www.ada.org/resources/ada-library/oral-health-topics/whitening

## Post-op non médicamenteux
Familles candidates :
- poche froide externe / cold pack;
- compresses/gazes adaptées;
- brosse postop très souple si recommandée pour la situation;
- solutions/barrières non médicamenteuses pour confort muqueux uniquement avec claim produit validé.

Ne pas encoder comme standard universel : fréquence/durée/indication dépendent du geste. Toute solution contenant un actif médicamenteux bascule dans la couche médicament/antiseptique correspondante.

Statut: `TAXONOMY_SUPPORTED_PROTOCOL_SPECIFIC`; Maroc `TO_VERIFY_BY_PRODUCT`; activation `NO`.

## Protection traumatique
Familles :
- mouthguard sportif stock/boil-and-bite;
- mouthguard custom-fitted;
- boîte de rangement adaptée.

AAPD encourage les mouthguards correctement adaptés dans les activités à risque d'atteinte orofaciale et recommande aux dentistes de prescrire/fabriquer ou orienter les patients à risque accru. L'ADA reconnaît `Athletic Mouthguards` comme catégorie de produit de protection contre les traumatismes d'impact.

Statut: `CLINICAL_FAMILY_SUPPORTED`; fit/type `PATIENT_AND_ACTIVITY_SPECIFIC`; Maroc `TO_VERIFY_BY_PRODUCT`; activation `NO`.

Sources:
- https://www.aapd.org/research/oral-health-policies--recommendations/prevention-of-sports-related-orofacial-injuries/
- https://www.ada.org/resources/research/science/ada-seal-of-acceptance/ada-seal-of-acceptance-product-categories

## Pédiatrie / nourrisson
Familles :
- brosse nourrisson/enfant à petite tête et poils souples;
- dentifrice fluoré pédiatrique — quantité/concentration/âge selon recommandations et produit;
- aides de dentition non médicamenteuses sûres, produit-spécifiques;
- révélateur de plaque chez enfant capable de l'utiliser correctement, sous encadrement approprié;
- mouthguard sportif selon activité/risque;
- aides de dextérité/caregiver pour besoins spécifiques.

Bains de bouche : ne pas généraliser chez <6 ans; ADA déconseille l'usage sauf direction du dentiste à cause du risque d'ingestion. Les gels de dentition médicamenteux restent `SAFETY_REVIEW_REQUIRED`, distincts des teethers non médicamenteux.

Statut: `CLINICAL_FAMILY_SUPPORTED_WITH_AGE_GUARDS`; Maroc `TO_VERIFY_BY_PRODUCT`; activation `NO`.

Sources:
- https://www.ada.org/resources/ada-library/oral-health-topics/mouthrinse-mouthwash
- https://www.aapd.org/research/oral-health-policies--recommendations/use-of-fluoride/

## Canonicalization decisions
- Un produit générique utilisé en orthodontie + implant + perio n'est pas dupliqué : une entité canonique + plusieurs `indication_tags`.
- Nettoyants prothèses et nettoyants aligners/retainers partagent éventuellement une famille technique mais gardent compatibilité matériau/dispositif produit-spécifique.
- Whitening toothpaste ne doit pas dupliquer la ligne dentifrice détachant : un `entity_canonical_id` unique + claims/tags.
- Mouthguard sportif reste distinct d'une gouttière occlusale thérapeutique/bruxisme.
- Post-op non médicamenteux reste séparé des antiseptiques et médicaments.

## Guardrails
- Family supported ≠ produit Maroc prouvé.
- Pas de claim universel « implant-specific », « orthodontic-specific » ou « whitening » sans actif/dispositif exact.
- Aucun dispositif DTC ne remplace diagnostic, planification ou suivi professionnel lorsqu'ils sont nécessaires.
- Aucun contact AMMPS.

## Next exact
Construire la matrice para consolidée avec `canonical_id`, famille, actif/matériau, forme, indication_tags, age_guard, evidence_status, Morocco_status, product_specific et activation; ensuite lancer la localisation Maroc par famille.
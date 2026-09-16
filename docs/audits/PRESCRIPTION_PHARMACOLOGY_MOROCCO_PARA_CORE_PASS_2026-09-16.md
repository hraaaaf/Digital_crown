# Digital Crown — Oral-care Maroc — Para core pass

Date: 2026-09-16
Status: RESEARCH ONLY — NOT FOR CLINICAL ACTIVATION

## Goal
Structurer les premières familles para à forte fréquence d'usage : dentifrices, bains de bouche et fluor, avec indication, âge/population, mode d'emploi, précautions et preuve Maroc séparées.

## Dentifrices fluorés — usage quotidien

### Famille standard fluorée
- Indication : prévention de la carie et hygiène quotidienne.
- ADA : brossage 2 fois/jour avec dentifrice fluoré.
- Enfant <3 ans : quantité <= un léger frottis / grain de riz, sous supervision.
- Enfant 3–6 ans : quantité <= un petit pois, sous supervision.
- Après 6 ans : quantité selon produit/âge; supervision jusqu'à maîtrise fiable du brossage et de l'expectoration.
- Ne pas déduire la concentration exacte par âge depuis une marque; conserver `ppm_fluoride` comme champ produit.
- Maroc : GUM Maroc commercialise plusieurs dentifrices par indication, dont Kids, Junior, prévention quotidienne, sensibilité, orthodontie et bouche sèche.

Sources cliniques :
- https://www.ada.org/resources/ada-library/oral-health-topics/fluoride-topical-and-systemic-supplements
- https://www.ada.org/resources/ada-library/oral-health-topics/toothpastes
- https://www.aapd.org/research/oral-health-policies--recommendations/fluoride-therapy/

Source Maroc :
- https://www.gum.co.ma/dentifrices/

## Dentifrices hypersensibilité

### Nitrate de potassium / fluorure stanneux / autres actifs validés par produit
- Indication : hypersensibilité dentinaire après diagnostic différentiel.
- Le référentiel doit stocker `active_ingredient`, concentration, indication fabricant, durée minimale avant réévaluation et précautions.
- Ne pas promettre d'efficacité équivalente entre actifs différents sans preuve comparative.
- Maroc : présence de dentifrices sensibilité dans le catalogue GUM Maroc; validation marque/par-marque à poursuivre.

Sources :
- https://www.ada.org/resources/ada-library/oral-health-topics/toothpastes
- https://www.gum.co.ma/dentifrices/

## Dentifrices gingivaux / parodontaux

### Chlorhexidine faible concentration + CPC / fluorure stanneux / antimicrobiens selon produit
- Indication : adjuvant au contrôle mécanique de plaque selon profil patient; jamais substitut du brossage/interdentaire.
- Exemple Maroc vérifié : GUM GINGIDEX dentifrice 0,06% chlorhexidine + 0,05% CPC, 1450 ppm fluor; fabricant marocain le positionne en maintenance parodontale et contrôle de plaque.
- Usage fabricant GUM : brossage après repas ou au moins 2 fois/jour pendant >=2 minutes.
- Population GUM brochure : adultes et enfants à partir de 7 ans pour ce produit; ne pas généraliser à toute chlorhexidine.
- Statut : `PRODUCT_SPECIFIC`, pas protocole universel.

Sources :
- https://gum.co.ma/produit/dentifrice-gingidex-1755/
- https://gum.co.ma/wp-content/uploads/2022/12/Depliant-GUM.pdf
- https://www.ada.org/resources/ada-library/oral-health-topics/home-care

## Bains de bouche thérapeutiques — règles générales

- ADA : les bains de bouche thérapeutiques peuvent cibler plaque/gingivite, mauvaise haleine ou carie selon actif.
- Ils ne remplacent pas brossage + nettoyage interdentaire.
- Enfants <6 ans : éviter sauf indication explicite du dentiste, en raison du risque d'ingestion.
- Toujours stocker : actif, concentration, alcool oui/non, âge minimum, fréquence, temps de contact, durée, `rinse_and_spit`, interactions/précautions.

Source :
- https://www.ada.org/resources/ada-library/oral-health-topics/mouthrinse-mouthwash

## Chlorhexidine 0,12% / 0,2%

- Indications possibles : contrôle de plaque/gingivite en adjuvant; certaines situations postopératoires ou ulcérations selon contexte.
- SDCEP : 0,2% chlorhexidine ou eau salée peut être conseillée dans certaines ulcérations courtes non traumatiques; avertissement que l'usage chez <12 ans dépend des licences produits.
- Effets indésirables importants à afficher : coloration dents/langue/restaurations, altération du goût; calcul supragingival possible.
- Ne pas attribuer une durée standard unique à toutes les formulations; `duration` doit être liée au produit/indication.
- Maroc : familles chlorhexidine présentes dans catalogue GUM Maroc; exemple GINGIDEX 0,12% documenté dans brochure locale.

Sources :
- https://www.ada.org/resources/ada-library/oral-health-topics/mouthrinse-mouthwash
- https://www.acutedentalproblems.sdcep.org.uk/guidance/management-of-oral-conditions/common-oral-conditions/oral-ulceration/
- https://gum.co.ma/wp-content/uploads/2022/12/Depliant-GUM.pdf

## CPC / huiles essentielles

- ADA : CPC, chlorhexidine et huiles essentielles peuvent réduire plaque/gingivite en complément de l'hygiène mécanique.
- CPC peut aussi être utilisé pour le contrôle de l'halitose selon formulation.
- Ne pas présenter comme équivalents à la chlorhexidine pour toutes indications.

Source :
- https://www.ada.org/resources/ada-library/oral-health-topics/mouthrinse-mouthwash

## Bain de bouche fluoré

### NaF 0,05%
- ADA : 0,05% NaF (~230 ppm F) est une concentration courante pour rinçage quotidien chez >6 ans.
- <6 ans : non recommandé en routine à cause du risque d'ingestion répétée.
- Indication : prévention carieuse, en particulier si risque accru selon jugement clinique.

### NaF 0,2%
- ADA : 0,2% NaF (~920 ppm F) peut être utilisé une fois par semaine dans certains programmes/situations à risque élevé; plus forte concentration = supervision/prescription selon contexte.

Source :
- https://www.ada.org/resources/ada-library/oral-health-topics/fluoride-topical-and-systemic-supplements

## Fluor professionnel

### Vernis fluoré NaF
- Indication : prévention/contrôle carieux selon risque individuel.
- AAPD : fait partie des modalités topiques professionnelles reconnues en pédiatrie.
- Concentration et protocole doivent être attachés au produit exact; ne pas créer de fréquence automatique universelle.

### Gel/foam professionnel
- ADA : produits professionnels peuvent être nettement plus concentrés que l'usage domestique (ex. 1,23% ion fluorure / 12 300 ppm dans certains produits).
- Utilisation professionnelle uniquement selon produit et risque.

Sources :
- https://www.aapd.org/research/oral-health-policies--recommendations/fluoride-therapy/
- https://www.ada.org/resources/ada-library/oral-health-topics/fluoride-topical-and-systemic-supplements

## Disponibilité Maroc — exemples vérifiés

- GUM Maroc : dentifrices prévention, gencives, sensibilité, enfant, orthodontie, bouche sèche; bains de bouche et accessoires.
- GUM GINGIDEX : dentifrice 0,06% chlorhexidine + 0,05% CPC + 1450 ppm fluor; brochure locale également documente bain de bouche chlorhexidine 0,12%.
- Ces exemples prouvent présence de familles/produits sur le marché marocain; ils ne constituent pas une recommandation commerciale.

Sources Maroc :
- https://www.gum.co.ma/dentifrices/
- https://www.gum.co.ma/bains-de-bouche/
- https://gum.co.ma/produit/dentifrice-gingidex-1755/
- https://gum.co.ma/wp-content/uploads/2022/12/Depliant-GUM.pdf

## Guardrails
- `market_available` et `clinically_recommended` restent deux champs différents.
- L'âge minimum d'un produit suit le produit/la notice; ne pas généraliser depuis une marque à toute la classe.
- Les bains de bouche ne remplacent jamais l'hygiène mécanique.
- Les concentrations de fluor/chlorhexidine doivent être stockées explicitement.
- Aucun conseil commercial automatique par marque.

## Next exact
Enrichir : interdentaire/brosses/hydropulseurs, xérostomie/halitose, prothèse/adhésifs/nettoyants, orthodontie, implants/parodonte, blanchiment et pédiatrie; puis audit d'omissions para.

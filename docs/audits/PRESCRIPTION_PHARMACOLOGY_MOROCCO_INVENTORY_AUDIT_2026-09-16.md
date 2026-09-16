# Digital Crown — Référentiel thérapeutique & bucco-dentaire Maroc — Audit exhaustif inventaire

Date: 2026-09-16
Status: GAP ANALYSIS COMPLETE — COMPLETENESS NOT CERTIFIED

## Goal
Auditer les 170 lignes du `PRESCRIPTION_PHARMACOLOGY_MOROCCO_MASTER_INVENTORY_2026-09-16.csv`, distinguer les vrais manques des doublons/recouvrements de taxonomie, et fermer les omissions certaines avant enrichissement clinique ou réglementaire.

## Success criteria
- les 170 lignes de base ont été relues par famille ;
- les omissions certaines sont séparées des candidats à confirmer ;
- les doublons exacts et recouvrements sémantiques sont explicités ;
- aucune preuve internationale n'est transformée en preuve réglementaire marocaine ;
- aucune ligne nouvelle n'est activée cliniquement sans validation correspondante.

## État vérifié du corpus
- Base inventory: 170 lignes = 68 `medicine` + 102 `oral_care/adjacent_care` selon le handover canonique.
- Addendum historique déjà présent: 4 lignes supplémentaires (`MED-CORT-001`, `MED-CORT-002`, `OC-TP-014`, `OC-MUC-004`).
- Total énuméré avant ce pass: 174 lignes, mais ce nombre n'est **pas** un nombre de concepts cliniques uniques.
- `COMPLETENESS CERTIFIED`: **NO**.

## 1. Doublons exacts / quasi-exacts à normaliser

### D1 — benzocaïne topique
- `MED-MUC-007` — benzocaine topical
- `MED-LA-008` — benzocaine topical

Même entité pharmacologique libellée deux fois pour deux contextes. Conserver une entité canonique avec tags d'usage/contexte plutôt que deux produits indépendants.

### D2 — dentifrice blanchissant / détachant
- `OC-TP-010` — whitening/stain-removal toothpaste
- `OC-WHITE-001` — whitening/stain-removal toothpaste

Doublon textuel. Une ligne canonique + tags `toothpaste` et `whitening` suffit.

### D3 — chewing-gum sans sucre/xylitol
- `OC-XERO-004` — sugar-free/xylitol gum
- `OC-GUM-001` — sugar-free/xylitol chewing gum

Même famille produit représentée sous xérostomie et prévention. Une entité canonique, plusieurs indications/tags.

## 2. Recouvrements sémantiques — ne pas fusionner sans forme/concentration
Ces couples/familles peuvent être légitimement distincts si la forme, la concentration ou l'usage est différent. Le schéma actuel ne l'exprime pas assez précisément :
- `MED-MUC-005` benzydamine mouthwash/spray ↔ `OC-RINSE-014` benzydamine mouthrinse ;
- `MED-MUC-006` lidocaine viscous/topical ↔ `MED-LA-007` lidocaine topical spray/gel ;
- `OC-TP-005` stannous fluoride toothpaste ↔ `OC-SENS-002` stannous fluoride desensitizing product ;
- `OC-TP-006` potassium nitrate toothpaste ↔ `OC-SENS-001` potassium nitrate desensitizing product ;
- `OC-TP-007` arginine + calcium carbonate toothpaste ↔ `OC-SENS-003` corresponding desensitizing product ;
- `OC-TP-008` strontium toothpaste ↔ `OC-SENS-004` strontium desensitizing product ;
- `OC-TP-013` hydroxyapatite toothpaste ↔ `OC-REM-002` hydroxyapatite remineralization product ;
- mouthrinse actives CPC/zinc/chlorine dioxide ↔ halitosis product families `OC-HAL-*`.

### Décision de schéma
Avant fusion finale, chaque ligne doit pouvoir porter au minimum `active_or_material`, `form`, `concentration_or_strength`, `route_or_use`, `indication_tags` et `entity_canonical_id`. Sans cela, le comptage d'exhaustivité est gonflé par les usages multiples d'un même produit.

## 3. Omissions certaines confirmées

### G1 — Porte-fil / floss holder
**Absent** de la base. `floss threader` n'est pas un `floss holder`.

Preuve clinique externe: l'ADA distingue explicitement floss holders, floss threaders et floss picks parmi les produits liés au fil dentaire.

Action: ajouter une ligne dédiée `floss holder / reusable floss handle`, statut Maroc `TO_VERIFY_MA`, activation `NO`.

Source: American Dental Association, *Dental Floss/Interdental Cleaners*, mise à jour août 2026.

### G2 — Fluor topique forte concentration auto-appliqué à domicile — gel
**Absent comme forme dédiée.** Le master contient dentifrices 2800/5000 ppm et gel/foam professionnel, mais pas le gel fluoré à domicile en tant que famille distincte.

Preuves cliniques externes:
- ADA: distingue les fluorures auto-appliqués à domicile (dont gels) des applications professionnelles ; décrit des gels auto-appliqués sur prescription et des gels/pâtes de prescription pour patients à risque carieux élevé.
- AAPD: distingue systémique, professionnel et home-use dans la thérapie fluorée.

Action: ajouter une ligne `prescription/high-strength home-use fluoride gel`, statut Maroc `TO_VERIFY_MA`, activation `NO`.

### G3 — Suppléments fluorés systémiques
**Absents** de la base.

Preuves cliniques externes:
- ADA: famille distincte de suppléments fluorés alimentaires (gouttes/comprimés/pastilles), prescription conditionnée notamment au risque carieux et à l'exposition fluorée de l'eau.
- AAPD: traite explicitement les suppléments fluorés alimentaires comme une modalité systémique séparée.

Action: ajouter une ligne de famille `dietary fluoride supplement — drops/tablets/lozenges`, statut Maroc `TO_VERIFY_MA`, clinique `SPECIALIST_OR_EXCEPTION`, activation `NO`.

Important: aucune dose, tranche d'âge ou indication opérationnelle ne doit être activée à partir de recommandations étrangères. Le contexte réglementaire marocain et l'exposition fluorée locale doivent être établis séparément.

## 4. Pédiatrie — correction de sécurité

### `OC-TEETH-001` — teething gel
La présence dans l'inventaire est acceptable pour représenter le marché et appliquer un garde-fou, mais cette ligne ne doit **pas** devenir une recommandation clinique générique.

- AAPD: recommande d'éviter les anesthésiques topiques/OTC pour douleur de dentition chez le nourrisson en raison d'un risque de toxicité.
- FDA: benzocaïne/lidocaïne topiques pour dentition peuvent entraîner des événements graves ; alternatives non médicamenteuses privilégiées.

Action: conserver la ligne comme `SAFETY_REVIEW_REQUIRED / MARKET_ONLY_OR_EXCLUSION` jusqu'à caractérisation produit-spécifique. Ne jamais mapper automatiquement `teething gel` vers benzocaïne/lidocaïne recommandée.

### Anneau de dentition ferme/réfrigéré
Famille non médicamenteuse soutenue comme option symptomatique sûre dans les références pédiatriques. Elle peut être inventoriée comme accessoire pédiatrique, mais elle est secondaire au Goal thérapeutique et doit garder `TO_VERIFY_MA`.

### Brosse à doigt nourrisson
La coverage matrix l'avait signalée comme sous-famille à fermer. Les références ADA/AAPD actuelles soutiennent surtout une petite brosse souple adaptée à l'âge ; la base contient déjà `OC-BRUSH-010 infant/child toothbrush`.

Décision: **ne pas créer de ligne clinique obligatoire `finger brush` à ce stade**. Si un produit marocain précis est observé, le classer comme variante marché de la famille pédiatrique, sans surclassement clinique.

## 5. Gaps de scope à garder ouverts — pas encore des lignes obligatoires

Ces zones peuvent élargir le référentiel si le Goal final signifie réellement « tout ce qu'un dentiste marocain peut prescrire/recommander », mais elles demandent une décision de frontière et une passe scientifique dédiée :
- douleur orofaciale/neuropathique/TMD et médicaments de spécialiste ;
- médecine buccale spécialisée (immunomodulation, dermatoses/lichen plan, etc.) ;
- produits post-opératoires non médicamenteux spécifiques au domicile au-delà des rinçages/brosses déjà inventoriés ;
- aides d'hygiène adaptées aux handicaps/dextérité réduite.

Statut: `SCOPE_BOUNDARY_REVIEW`, pas `MISSING_CONFIRMED`.

## 6. Incohérence à corriger dans la coverage matrix
La phrase indiquant que « le principal travail restant est désormais l'enrichissement de ligne et la vérification Maroc, pas la construction d'une nouvelle taxonomie » est trop forte.

État prouvé après cet audit:
- la macro-taxonomie A–Z est utile ;
- mais au moins trois omissions de famille/forme sont confirmées ;
- plusieurs doublons et recouvrements empêchent de convertir le nombre de lignes en métrique d'exhaustivité ;
- la taxonomie n'est donc pas encore fermée.

## 7. Sources croisées utilisées pour ce pass
1. American Dental Association — *Dental Floss/Interdental Cleaners* — floss holders/threaders/picks et familles interdentaires.
2. American Dental Association — *Fluoride: Topical and Systemic Supplements* — fluorures auto-appliqués/professionnels et suppléments systémiques.
3. American Dental Association — *Topical Fluoride Clinical Practice Guideline* — fluorures topiques professionnels et prescription-strength home-use.
4. American Academy of Pediatric Dentistry — *Fluoride Therapy*, Reference Manual 2026-2027.
5. American Dental Association — *Toothbrushes* — brossage dès éruption avec brosse souple adaptée à l'âge.
6. American Academy of Pediatric Dentistry — *Perinatal and Infant Oral Health Care* — prévention et sécurité de la dentition.
7. U.S. FDA — *Safely Soothing Teething Pain in Infants and Children* — risques benzocaïne/lidocaïne pour dentition.

Les sources 1–7 soutiennent la classification clinique/générique uniquement. Elles ne prouvent aucune autorisation, disponibilité, spécialité, concentration ou RCP au Maroc.

## 8. Verdict du pass inventaire
- `170 rows reviewed`: YES.
- `base inventory exhaustive`: NO.
- `macro-family coverage useful`: YES.
- `taxonomy closed`: NO.
- `exact/quasi-exact duplicate pairs`: 3 confirmés.
- `semantic overlap clusters`: au moins 8 à normaliser.
- `confirmed missing families/forms`: 3.
- `safety correction`: teething gel must remain non-recommendation/fail-closed pending product-specific review.
- `clinical activation`: NO CHANGE.
- `AMMPS contact`: NONE.

## Next exact
1. Ajouter les trois omissions confirmées dans un addendum V2 sans toucher à l'historique du CSV 170 lignes.
2. Ajouter la famille non médicamenteuse `firm/chilled teething ring` comme option pédiatrique non pharmacologique, `TO_VERIFY_MA`, sans recommandation automatique.
3. Mettre à jour la coverage matrix pour retirer l'affirmation de taxonomie essentiellement fermée et enregistrer les doublons/recouvrements.
4. Ensuite seulement, lancer la vérification Maroc de ces nouvelles lignes et poursuivre l'enrichissement par paquets homogènes.

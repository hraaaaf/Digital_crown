# Digital Crown — Pharmacologie dentaire Maroc — topiques muqueux / anesthésiques

Date: 2026-09-16
Status: VERIFIED PARTIAL CLINICAL PASS — NO CLINICAL ACTIVATION

## Goal
Fermer les principaux risques et usages des lignes `benzydamine`, `lidocaine viscous/topical` et `benzocaine topical`, sans confondre données cliniques internationales, statut produit marocain et activation clinique.

## 1. Benzydamine — MED-MUC-005 / OC-RINSE-014

### Preuve clinique croisée
- NHS : benzydamine = AINS local utilisé pour douleur/inflammation de la bouche, notamment ulcères, langue/gencives douloureuses et douleur après chirurgie dentaire ; formes bain de bouche, spray et pastille.
- SmPC 2025-2026 : benzydamine 0,15% en bain de bouche/spray est un analgésique/anti-inflammatoire local ; usages incluent ulcération aphteuse et douleur après chirurgie dentaire.

### Âge / forme
- Les limites d'âge dépendent fortement de la forme.
- NHS : spray possible dans certaines présentations pédiatriques ; bain de bouche seulement à partir de 13 ans.
- SmPC d'un bain de bouche 0,15% : réservé aux adultes et ≥13 ans / non adapté ≤12 ans.
- SmPC spray 0,15% : schémas pédiatriques existent, y compris <6 ans selon poids, mais **ces schémas sont produit-spécifiques étrangers et ne sont pas promus dans Digital Crown** tant qu'une présentation marocaine exacte n'est pas verrouillée.

### Durée / sécurité
- SmPC bain de bouche : traitement continu généralement ≤7 jours sauf supervision médicale.
- Prudence si antécédent d'hypersensibilité AINS/aspirine ou asthme ; certaines formulations contiennent de l'éthanol.

### Maroc
`TO_VERIFY_MA` dans le pass actuel : aucune présentation marocaine exacte n'a été suffisamment verrouillée.

### Décision
`CLINICAL_FAMILY_SUPPORTED / PRODUCT_SPECIFIC_MA_PENDING / activation NO`.

Sources :
- https://www.nhs.uk/medicines/benzydamine/about-benzydamine/
- https://www.nhs.uk/medicines/benzydamine/who-can-and-cannot-use-benzydamine/
- https://www.medicines.org.uk/emc/product/102500/smpc
- https://www.medicines.org.uk/emc/product/101959/smpc

## 2. Lidocaïne visqueuse/orale — MED-MUC-006

### Preuve clinique / sécurité
- DailyMed 2026 : lidocaïne orale topique 2% visqueuse = anesthésique des muqueuses de la bouche et du pharynx.
- Boxed warning : convulsions, arrêt cardio-pulmonaire et décès ont été rapportés chez des enfants <3 ans lorsque le produit n'était pas utilisé strictement selon les recommandations.
- Pour la douleur de dentition, la lidocaïne visqueuse orale **ne doit généralement pas être utilisée**.
- Chez <3 ans pour d'autres indications, usage à réserver aux situations où des alternatives plus sûres ne sont pas disponibles ou ont échoué, avec respect strict dose/fréquence.

### Maroc
- AMMPS : `XYLOCAINE VISQUEUSE 0,02`, gel oral, retiré du marché.
- AMMPS : d'autres formes dentaires/topiques de lidocaïne existent avec statuts distincts, notamment `XYLONOR` commercialisé et `XYLOCONTACT` AMM sans prix.

### Décision
La ligne générique `lidocaine viscous/topical` doit être éclatée par forme dans le dataset final. `XYLOCAINE VISQUEUSE` retirée ne doit jamais être substituée automatiquement par une autre lidocaïne topique.

`activation NO`.

Sources :
- https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=ae40021b-8df8-4b16-aac0-dcec88f76c7d
- https://www.ammps.gov.ma/basesdedonnes/liste_marocaine_des_medicaments?page=482

## 3. Lidocaïne topique dentaire — MED-LA-007

### Maroc
AMMPS :
- `XYLONOR` — solution pour usage dentaire, lidocaïne base + cétrimide, commercialisé.
- `XYLOCONTACT` — crème pour usage dentaire, lidocaïne, AMM sans prix.
- `XYLOCAINE` gel 2% et nébuliseur 5% : non commercialisés dans la base observée.

### Guardrail
- Chaque forme doit conserver concentration/composition exacte.
- Toute lidocaïne topique contribue à l'exposition totale à la lidocaïne lorsqu'elle est associée à une injection.
- Les règles de sécurité pédiatrique d'une forme visqueuse orale ne doivent pas être extrapolées aveuglément à une autre présentation, mais constituent un signal fort imposant une revue âge/forme.

### Décision
`PARTIAL_VERIFIED_MA / PRODUCT_SPECIFIC / activation NO`.

Source :
- https://www.ammps.gov.ma/basesdedonnes/liste_marocaine_des_medicaments?page=482

## 4. Benzocaïne topique — MED-MUC-007 / MED-LA-008

### Preuve sécurité croisée
- FDA : les produits oraux contenant benzocaïne ne doivent pas être utilisés pour douleur de dentition chez l'enfant ; chez les <2 ans, risque de méthémoglobinémie potentiellement grave ou fatale.
- FDA : même chez les ≥2 ans/adultes, la méthémoglobinémie reste le risque critique à signaler.
- AAPD local anesthesia pass déjà présent dans le repo : la benzocaïne est un anesthésique topique dentaire courant, mais le risque de méthémoglobinémie reste un garde-fou majeur.

### Maroc
- Un fournisseur dentaire marocain commercialise un gel oral topique à benzocaïne 20%, ce qui prouve une présence marché de matériel/produit dentaire.
- Aucune validation AMMPS médicament exacte n'est acquise dans cette passe.

### Décision
- `MARKET_DENTAL_SUPPLY_MA_ONLY`.
- `SAFETY_REVIEW_REQUIRED`.
- aucun usage dentition ; aucun automatisme pédiatrique ; aucune dose générique.
- les deux lignes historiques sont reliées au même `canonical_entity_id` dans le mapping V1.

Sources :
- https://www.fda.gov/consumers/consumer-updates/safely-soothing-teething-pain-infants-and-children
- https://www.fda.gov/media/113345/download

## 5. Cohérence avec la pédiatrie dentition
- `OC-TEETH-001 teething gel` reste `SAFETY_REVIEW_REQUIRED / MARKET_ONLY_OR_EXCLUSION` tant que la composition n'est pas connue.
- Ne jamais mapper automatiquement `teething gel` vers benzocaïne ou lidocaïne.
- `OC-TEETH-002 teething ring / teether` reste non médicamenteux avec revue sécurité produit-spécifique.

## Verdict
- benzydamine : clinique soutenue, Maroc non verrouillé.
- lidocaïne visqueuse : sécurité critique verrouillée, forme historique marocaine retirée.
- lidocaïne topique dentaire : présence Maroc prouvée par forme spécifique.
- benzocaïne : usage topique dentaire connu, mais présence Maroc seulement commerciale et risque méthémoglobinémie critique.
- activation clinique : NO CHANGE.

## Next exact
1. Structurer ce pass en CSV par forme.
2. Reporter les statuts Maroc des anesthésiques locaux dans la couche maître sans extrapoler de doses.
3. Auditer `sucralfate oral/local`, `triamcinolone oral paste`, `hydrocortisone buccal`, `dexamethasone/prednisolone topical rinse` avec statut Maroc séparé.

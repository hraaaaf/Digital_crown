# Digital Crown — Maroc — Kit d'urgence cabinet dentaire — localisation

Date: 2026-09-17
Status: RESEARCH ONLY — PROTOCOL-ONLY — FAIL-CLOSED

## Goal
Localiser au Maroc les composants du noyau d'urgence déjà validé cliniquement par SDCEP/RCUK, sans confondre présence commerciale, équivalence de forme et protocole d'urgence.

## Résultat par composant

### Adrénaline IM 1:1000 requise par le protocole clinique
- Medicament.ma confirme une présentation marocaine `ADRENALINE SOTHEMA 0.25 MG/ML`, solution injectable, statut commercialisé (mise à jour 2025/2026).
- Cette concentration n'est PAS équivalente à la concentration 1 mg/mL (1:1000) du protocole SDCEP.
- Statut pour le besoin exact du kit: `FORM_CONCENTRATION_MISMATCH` / `TO_VERIFY_MA_EXACT_1MG_ML`.
- Activation: `NO`.

### Aspirine dispersible 300 mg
- AMMPS confirme des formes d'acide acétylsalicylique au Maroc, notamment 500 mg comprimé avec AMM sans prix et d'autres associations commercialisées.
- La forme exacte `dispersible 300 mg` requise par le protocole n'est pas prouvée dans cette passe.
- Statut: `TO_VERIFY_MA_EXACT_FORM_STRENGTH`.
- Activation: `NO`.

### Glucagon IM 1 mg
- Recherche publique ciblée AMMPS/web de cette passe: absence de preuve suffisamment propre d'une présentation Maroc actuelle correspondant exactement au besoin du protocole.
- Statut: `TO_VERIFY_MA`.
- Activation: `NO`.

### Trinitrine / GTN spray
- Medicament.ma recense `NATISPRAY 0.3 MG/DOSE`, aérosol, comme commercialisé au Maroc.
- Le protocole SDCEP documenté dans la passe clinique utilise 400 microgrammes/dose; `0.3 mg` = 300 microgrammes et ne doit pas être traité comme équivalent automatique.
- Statut: `MARKET_EVIDENCE_MA_300MCG_DOSE` + `PROTOCOL_STRENGTH_MISMATCH`.
- Activation: `NO`.

### Midazolam oromucosal 5 mg/mL
- AMMPS RMMG confirme des formes `MIDAZOLAM MYLAN 5 MG/ML` injectables IM/IV/rectales.
- Aucune forme oromucosale/buccale 5 mg/mL n'est prouvée au Maroc dans cette passe.
- Une forme injectable ne peut pas être substituée automatiquement à une forme oromucosale.
- Statut: `TO_VERIFY_MA_OROMUCOSAL_FORM`.
- Activation: `NO`.

### Glucose oral
- Le protocole exige une source orale de glucose, mais cette passe n'a pas verrouillé un produit médical marocain exact standardisé pour le cabinet.
- Statut: `TO_DEFINE_PROTOCOL_PRODUCT_MA`.
- Activation: `NO`.

### Oxygène médical
- Produit/protocole de secours, non assimilable à une ligne de médicament ambulatoire.
- Cadre fournisseur, bouteille/détendeur/débit et exigences locales du cabinet restent à documenter séparément.
- Statut: `TO_VERIFY_MA_SUPPLY_AND_REGULATORY_FRAMEWORK`.
- Activation: `NO`.

### Salbutamol inhalé 100 microgrammes/dose
- AMMPS RMMG confirme des génériques salbutamol 100 µg aérosol (`BUTAMYL`, `INALER`).
- Medicament.ma recense également `VENTOLINE 100 µg`, flacon pressurisé, comme commercialisé.
- Attention: une présentation VENTOLINE nébules 2.5 mg/2.5 mL apparaît `Non Commercialisé` dans la base AMMPS; les formes doivent rester distinctes.
- Statut besoin inhalateur 100 µg: `VERIFIED_FORM_MA`.
- Activation: `NO`; usage strictement `PROTOCOL_ONLY`.

### Antihistaminiques possibles
- Le protocole clinique cite cétirizine, chlorphénamine ou loratadine pour certaines réactions allergiques légères; ils ne remplacent jamais l'adrénaline dans l'anaphylaxie.
- Localisation Morocco exacte par DCI/forme non clôturée dans cette passe.
- Statut: `TO_VERIFY_MA_BY_DCI_AND_FORM`.
- Activation: `NO`.

## Sources Morocco/public
- AMMPS base médicaments: https://ammps.gov.ma/recherche-medicaments?page=1
- AMMPS RMMG: https://ammps.gov.ma/repertoire-medicaments-generiques
- AMMPS RMMG salbutamol page 14: https://ammps.gov.ma/repertoire-medicaments-generiques?page=14
- AMMPS database VENTOLINE region/page: https://www.ammps.gov.ma/basesdedonnes/liste_marocaine_des_medicaments?page=461
- Medicament.ma ADRENALINE SOTHEMA 0.25 mg/mL: https://medicament.ma/medicament/adrenaline-sothema-0-25-mg-ml-solution-injectable/
- Medicament.ma NATISPRAY 0.3 mg/dose: https://medicament.ma/medicament/natispray-03-mgdose-aerosol/
- Medicament.ma VENTOLINE 100 µg: https://medicament.ma/medicament/ventoline-suspension-pour-inhalation-en-flacon-pressurise-hfa-134a-100-mcgdose/
- AMMPS RMMG midazolam page 11: https://ammps.gov.ma/repertoire-medicaments-generiques?page=11

## Clinical source layer
Le besoin clinique exact reste celui documenté dans `PRESCRIPTION_PHARMACOLOGY_MOROCCO_CLINICAL_PASS3_EMERGENCIES_2026-09-16.md`, fondé sur SDCEP + Resuscitation Council UK. Le présent fichier ne modifie aucun protocole ni aucune dose.

## Safety decisions
- Aucune substitution automatique entre concentrations, formes ou voies.
- Une présence commerciale n'autorise pas l'activation clinique.
- Les écarts 250 µg/mL vs 1 mg/mL adrénaline et 300 µg vs 400 µg/dose GTN sont des mismatches explicites, pas des équivalences.
- Toute ligne exacte non prouvée reste fail-closed.
- Aucun contact AMMPS effectué.

## Next exact
Créer la couche structurée de classification `VERIFIED_FORM_MA / TO_VERIFY_MA / MISMATCH / PROTOCOL_ONLY`, puis poursuivre vers le dataset para complet sans ouvrir les gates cliniques.

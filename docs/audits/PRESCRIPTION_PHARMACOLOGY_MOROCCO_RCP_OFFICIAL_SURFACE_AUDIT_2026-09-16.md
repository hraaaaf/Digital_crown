# Prescription Pharmacology Morocco — Official AMMPS RCP Surface Audit

Date: 2026-09-16
Status: VERIFIED RESEARCH — no manifest mutation, no clinical activation

## Goal
Déterminer, après le census global et le mapping strict des RCP actifs, si une voie publique officielle AMMPS permet de récupérer un RCP exact pour les 7 familles Wave 1 sans fabriquer d'URL ni utiliser une source réglementaire étrangère comme substitut.

## Success
Le lot documentaire est réussi si :
1. les surfaces officielles AMMPS consultées sont identifiées ;
2. les constats sont séparés de toute inférence d'absence ;
3. la compatibilité avec le contrat M1 est vérifiée ;
4. la prochaine voie officielle exploitable est explicitée ;
5. aucune entrée manifest n'est promue sans PDF AMMPS réel.

## Contrat repo vérifié
Le canonique `PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_M1.md` impose pour `SNAPSHOT_VERIFIED` :
- document récupéré depuis l'AMMPS officielle ;
- URL officielle exacte ;
- date ;
- artefact PDF local réel ;
- bytes locaux concordants ;
- SHA-256 réel ;
- identité de présentation ;
- revue scientifique indépendante avant changement réglementaire mergé.

Le deterministic safety gate exige lui aussi une provenance HTTPS AMMPS officielle. ANSM/EMA ou autre régulateur étranger ne peuvent donc pas remplacer la preuve réglementaire marocaine dans M1.

## Preuve préalable — mapping des 48 RCP actifs
Run GitHub Actions #15 `35142068612` sur `cbb223eff8ce6cc4f8765cf03e495e1e69385769`: SUCCESS.
Artifact `10465272557`, digest `sha256:15857f36225b3f04375170db9f26e8fb7fe1548c8399efa523db58e52384ad78`.

Résultat :
- 48/48 hrefs actifs strictement liés à leur `modalId` ;
- aucun RCP actif n'est prouvé comme appartenant aux familles dentaires Wave 1 ;
- le dernier match lexical `AMOXICIL...` était contenu après l'identité `SMOFKABIVEN E` et ne prouve aucun RCP SOCLAV ;
- aucun manifest modifié ; aucune activation clinique.

## Surface 1 — Recherche médicaments AMMPS
Source officielle : `https://www.ammps.gov.ma/recherche-medicaments`.

Les probes ciblés et le census global ont établi que les familles Wave 1 disposent d'entrées AMMPS courantes mais que leurs contrôles RCP observés sont désactivés. Le census complet a trouvé 9908 contrôles, 48 actifs et 9860 désactivés sur 826/826 pages, sans page échouée.

Interprétation autorisée : aucun lien RCP actif exploitable n'a été observé pour les 7 familles cibles dans cette surface au moment du scan.

Interprétation interdite : conclure qu'un RCP réglementaire n'existe pas.

## Surface 2 — Liste Marocaine des médicaments
Source officielle : `https://www.ammps.gov.ma/basesdedonnes/liste_marocaine_des_medicaments`.

Exemples vérifiés le 2026-09-16 :
- CLAMOXYL 500 mg poudre pour suspension buvable, flacon 60 ml, AMM enregistrée et commercialisé, substance active AMOXICILLINE : `Lien RCP / NAF -` ;
- CLARADOL 500 mg comprimé effervescent, AMM enregistrée et commercialisé, PARACETAMOL : `Lien RCP / NAF -` ;
- ZECLAR 25 mg/ml granulé pour suspension buvable, AMM enregistrée et commercialisé, CLARITHROMYCINE : `Lien RCP / NAF -` ;
- ZECLAR 500 mg comprimé pelliculé, AMM enregistrée et non commercialisé, CLARITHROMYCINE : `Lien RCP / NAF -` ;
- plusieurs présentations enregistrées/commercialisées d'AMOXICILLINE + ACIDE CLAVULANIQUE, dont AUGMENTIN, affichent également `Lien RCP / NAF -`.

Ce champ `-` constitue une preuve de non-exposition publique du lien sur cette surface pour ces entrées. Il ne constitue pas une preuve explicite d'absence réglementaire du document.

## Surface 3 — Répertoire Marocain des Médicaments Génériques
Source officielle : `https://ammps.gov.ma/repertoire-medicaments-generiques`.

Utilité : identité/package-level et EAN pour les génériques, notamment le métronidazole oral. Cette surface ne remplace pas le RCP et ne peut pas servir de fallback réglementaire dans le contrat M1.

## Surface 4 — canal institutionnel AMMPS courant
Source officielle : `https://www.ammps.gov.ma/reclamation`.

La page AMMPS courante expose une `Fiche de Réclamation Client` destinée à recueillir, traiter et suivre les réclamations relatives aux services de l'Agence. Elle permet notamment :
- catégorie `Professionnel de santé` ;
- thématique `Réglementaire / Juridique` ;
- champ `Service ou dossier concerné` ;
- description des faits et `Résultat attendu / Demande formulée` ;
- pièces jointes PDF/JPG/PNG ;
- envoi via la plateforme AMMPS ;
- numéro de traitement des réclamations publié : `08 000 000 18`.

Le site AMMPS courant publie également ses coordonnées institutionnelles à Rabat et les parcours `Déposer une réclamation` / `Déposer un recours`.

Ce canal actuel est préféré pour la première demande documentaire formelle, car il est présent sur la surface institutionnelle 2026 et fournit un mécanisme de suivi.

Une communication AMMPS historique du 15/02/2019 publie par ailleurs le canal du Service de l'enregistrement pour les demandes d'information concernant l'enregistrement des médicaments : `enregistrement.dmp@sante.gov.ma` avec `u.dm.dmp@sante.gov.ma` indiqué entre parenthèses. Ce canal est conservé comme preuve historique officielle, mais son actualité opérationnelle n'est pas supposée sans réponse.

## État Wave 1 après audit officiel
- paracetamol: `PENDING` — identité AMMPS présente, aucun PDF RCP exact capturé ;
- ibuprofen: `PENDING` — identité AMMPS présente, aucun PDF RCP exact capturé ;
- amoxicillin: `PENDING` — présentations exactes confirmées, dont CLAMOXYL, mais aucun PDF RCP exact capturé ;
- penicillin_v: `PENDING` — présentation AMMPS présente, aucun PDF RCP exact capturé ;
- metronidazole: `PENDING` — présentations orales confirmées dans RMMG et recherche médicaments, aucun PDF RCP exact capturé ;
- clarithromycin: `PENDING` — ZECLAR/présentations AMMPS confirmées, aucun PDF RCP exact capturé ;
- clindamycin: `PENDING_CURRENT_PRESENTATION_DISCOVERY` — aucune présentation systémique/orale courante utile n'est encore prouvée dans le pass actuel.

Aucun de ces états n'autorise `UNAVAILABLE_VERIFIED`.

## Demande documentaire recommandée
Utiliser en priorité la Fiche de Réclamation Client AMMPS courante, catégorie `Professionnel de santé`, thématique `Réglementaire / Juridique`, afin de demander pour chaque famille prioritaire soit :
1. l'URL publique exacte du RCP marocain courant ; ou
2. une copie officielle du RCP courant avec identification exacte de la présentation ; ou
3. une confirmation explicite de la procédure/statut documentaire si le RCP n'est pas publiquement disponible.

Champs à demander : nom commercial, DCI, dosage, forme, présentation, statut AMM/commercialisation, identifiant réglementaire si communicable, URL RCP officielle ou document officiel.

## Garde-fous
- aucune URL `/uploads/rcp/...` ne sera devinée ;
- `Lien RCP / NAF -` n'est pas transformé en `UNAVAILABLE_VERIFIED` ;
- aucun document ANSM/EMA n'est utilisé comme substitut à la provenance AMMPS ;
- aucune donnée clinique, posologie, indication ou règle de prescription n'est activée ;
- aucune soumission AMMPS n'est faite sans human gate explicite ;
- toute réponse AMMPS devra encore être liée à l'identité exacte, vérifiée en bytes/PDF/SHA-256 et revue indépendamment avant promotion du manifest.

## Verdict
La voie publique AMMPS a été explorée suffisamment pour fermer le scraping ciblé comme stratégie principale : le mécanisme RCP existe et fonctionne, mais aucun RCP actif pertinent aux 7 familles Wave 1 n'a été prouvé. La prochaine étape rationnelle est une demande documentaire officielle via le canal AMMPS courant de réclamation/suivi, soumise à human gate avant envoi.

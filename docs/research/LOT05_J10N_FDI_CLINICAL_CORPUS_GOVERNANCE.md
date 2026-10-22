# LOT05 / J10N — Constitution d'un corpus FDI-32 sous contrôle : protocole, double lecture et barrières GitHub

**22/10/2026 — PR Draft empilée sur J10M #1028.**

## Objet et état réel

Après J10M, aucun des jeux FDI-32 publiquement examinés ne démontre simultanément droits complets des radiographies, usage commercial, droit de traitement cloud et traçabilité de provenance. Notre choix est **de construire d'abord un protocole de corpus maîtrisé**, et non de contourner le blocage par un entraînement expérimental de photos cliniques prises sur Internet. **Aucune radiographie n'a été collectée, copiée ou téléversée dans cette PR.**

Le statut est :
- **GO technique** : conception des schémas, des étiquettes FDI 11–18/21–28/31–38/41–48 et simulation de contrôle qualité sur données géométriques entièrement synthétiques via GitHub Actions.
- **NO-GO juridique/clinique** : collecte secondaire d'images du cabinet, traitement à distance, transfert transfrontalier, entraînement de vraies radios, packaging poids et usage sur patients. La modification d'un fichier JSON ou le succès de CI ne constitue **jamais** une approbation légale, médicale ou CNDP.

## 1. Dossier réglementaire à constituer au Maroc AVANT toute donnée réelle

Le cadre marocain **loi 09-08 / CNDP** exige une analyse de la finalité, des données de santé, du responsable du traitement et de la notification applicable. La CNDP distingue autorisation préalable et exceptions/déclaration dans certains traitements de soins par praticien soumis au secret professionnel : **une utilisation secondaire pour entraîner un système commercial doit être analysée indépendamment des traitements de soins**. Un changement de finalité est mentionné comme motif d'autorisation, et les recherches médicales peuvent exiger un protocole et des éléments d'éthique. Sources premières : [CNDP notifier un traitement](https://www.cndp.ma/notifier-un-traitement/), [CNDP autorisation préalable](https://www.cndp.ma/notifier-une-demande-dautorisation-prealable/), [CNDP procédures de notification](https://www.cndp.ma/procedures-de-notification-process/).

**Surtout pour GitHub Actions** : la CNDP décrit des conditions propres au **transfert de données personnelles vers l'étranger** (formulaire F118, existence préalable d'une déclaration/autorisation approuvée, pays destinataire, garanties/justifications) : [fiche officielle CNDP](https://www.cndp.ma/transfert-de-donnees-a-letranger/). L'absence de nom sur une radio **ne suffit pas à démontrer une anonymisation irréversible ni le droit d'expédier des données de santé sur des runners publics**. Déterminer avec un conseil CNDP/clinique si les images sont personnelles ou anonymisées, les catégories de données, les bases légales, les clauses contractuelles avec hébergeur/sous-traitant, les restrictions pays, et documenter toute autorisation requise. **Aucune image réelle sur GitHub Actions tant que ce dossier n'a pas été validé.**

Dossier de preuves à conserver **hors GitHub**, avec contrôle d'accès strict :
1. Responsable du traitement, sous-traitant, finalité exacte « constitution d'un jeu d'entraînement FDI pour produit commercial », origine précise des clichés et politique d'accès.
2. Droits sur les images par site d'acquisition, accord de mise à disposition/entraînement et de réutilisation des **poids dérivés** dans Digital Crown, éventuels droits des tiers et contrats.
3. Information des personnes concernées et fondement approprié au traitement secondaire, modalités d'opposition/retrait quand applicables et détermination documentée des usages autorisés.
4. Dossier CNDP et avis professionnel réglementaire, contrat/confidentialité du sous-traitant, périmètre des transferts, mesures de sécurité, durée de conservation, purge, sauvegardes, contrôle des accès et journalisation.
5. Évaluation clinique/éthique du protocole de recherche et de qualité, et justification scientifique du volume/des critères de sélection.
6. Dé-identification contrôlée (DICOM, overlays visibles, noms d'établissement, marqueurs, métadonnées de fichier, géométrie éventuellement ré-identifiante) avec **audit humain et contrôle de résidualité**. Les radios restent médicales et potentiellement sensibles.
7. Identifiants de dossiers de preuve conservés dans un registre privé : **ni noms, ni CIN, ni date de naissance, ni originaux, ni clés, ni SHA de fichiers cliniques sur GitHub / Notion public / artifacts de PR**.

La matrice non clinique `LOT05_J10N_CLINICAL_RIGHTS_INTAKE_CHECKLIST.json` comporte **16 vérifications** marquées PENDING ou DRAFT_SYNTHETIC_ONLY. **Elle ne contient aucune attestation personnelle et ne peut pas donner un GO.**

## 2. Contrat d'annotation et revue indépendante

Il s'agit de **FDI permanent**, pas de numérotation des dents temporaires, et non de diagnostic. Consignes à formaliser pour la version clinique future :
- Annoter **chaque dent permanente visible** avec le numéro FDI exact selon la convention d'orientation de la panoramique. Ne pas imposer 32 dents à chaque film : absences, extractions et anodontie/édentement doivent rester représentables.
- Noter hors de l'annotation « bounding box + FDI » les ambiguïtés liées à implants, dents incluses, superpositions, rotations/inversions gauche-droite, prothèses et jeunes patients. Ne pas transformer un manque d'annotation en « dent saine ».
- Deux chirurgiens-dentistes lisent séparément les images, **sans copier les annotations** de l'autre. Les discordances de numéro, présence ou boîte (IoU de boîtes, seuil technique initial **0,70 sur le banc synthétique uniquement**) déclenchent un **arbitrage d'un troisième lecteur distinct** et une trace de décision. Ce seuil est un paramètre d'assurance-qualité expérimental, **pas** un seuil de performance clinique validé.
- Enregistrer dans le système autorisé hors GitHub un identifiant de source, le statut de droits, la révision et les vérifications d'orientation. Découpler le mapping sujet ↔ image ↔ annotateur de la livraison finale du dataset et chiffrer les éléments sensibles.
- La validation d'une radiographie edentée sans dent visible doit être explicite pour les deux relecteurs (zéro boîte ≠ annotation manquante).

## 3. Hygiène du protocole d'entraînement et tests

Les règles de futur partitionnement (à tester avant entraînement sur données admises) :
- Regrouper **par patient/origine clinique**, avant toute augmentation, et préserver tous les clichés d'un même patient dans le même ensemble train/validation/test.
- Regrouper les doublons/quasi-doublons et leurs **images augmentées** dans une seule partition, pour éviter une fuite par rotations ou recadrages entre train/test. Les clés perceptuelles et hash de vrais pixels restent en stockage sécurisé **hors GitHub**.
- Réserver un **test externe par site**, distinct des établissements d'entraînement et de validation, dans un jeu jamais vu lors du réglage des hyperparamètres. Le test externe implique une provenance vérifiée et des droits propres à ce test.
- Mesurer séparément sensibilité/rappel par dent, précision des numéros FDI, association boîte/numéro, erreurs de quadrant gauche/droite, dents absentes, cas difficiles, taux de films entièrement justes, et intervalles d'incertitude. Procéder à une relecture indépendante par praticien; ne jamais assimiler une mAP seule à une certification clinique.
- Tout déploiement futur nécessite revue réglementaire du dispositif logiciel selon son usage, vérification du Windows service, sécurité du stockage local, et validation praticien requise pour chaque suggestion.

## 4. Livrables du lot J10N (SYNTHETIC ONLY)

`experiments/lot05_j10n_fdi_synthetic_annotation_quality.py` : générateur autonome de **5 enregistrements fictifs purement textuels** (pas d'image, pas de DICOM, pas de nom), **4 groupes sujets fictifs**, 32 classes FDI autorisées, train/val/test externe, source synthétique distincte pour le test, un groupe dupliqué **dans le même split**, un exemple d'édentement explicitement confirmé et un désaccord de lecteurs qui nécessite un troisième arbitrage. Contrôles :
- Schéma **strictement fermé** (toute clé extra telle que `patient_name`, `dicom_file`, `diagnosis` rejetée) et identifiants explicitement fictifs `SYN-...`.
- Classe FDI valide, pas de dent dupliquée dans un film, boîte normalisée finie et dans les limites, orientation revue, deux identités d'annotateurs distinctes, arbitrage obligatoire du désaccord, pas d'acceptation silencieuse de dent supprimée.
- Séparation des sujets, doublons/quasi-doublons et des sites externes avant apprentissage; détection de hash identique et impossibilité d'avoir même sujet sous plusieurs splits.
- Appel au garde juridique **J10L**, qui conserve `REAL_DATA_TRAINING_BLOCKED_SYNTHETIC_ONLY`. **Le programme n'a aucun argument de lecture d'un vrai dataset**, de fichier DICOM ou d'images.
- Résultat archivé : **uniquement indicateurs agrégés JSON** (nombres de groupes, erreurs vérifiées, adjudications fictives et statut NO-GO) : aucune clé sujet ni forme/boîte par enregistrement.

`experiments/test_lot05_j10n_fdi_synthetic_annotation_quality.py` : tests adversariaux contre fausse autorisation, champs PHI/DICOM, erreur FDI, gauche/droite non vérifiée, doublon, fuite sujets / quasi-doublons et site externe, double revue frauduleuse, absence d'arbitrage, erreur de boîte et absence de dent traitée implicitement.

`.github/workflows/lot05-j10n-synthetic-annotation-qa.yml` : jobs GitHub Actions sans téléchargement de modèle/images, pure **stdlib** Python 3.11 sur Ubuntu/Windows après préflight J10I/J10L. Fichiers d'artefacts **JSON agrégé seulement**. Pas de secrets cliniques, pas de déploiement.

## 5. Prochain événement réellement nécessaire

Cette PR **ne peut pas** obtenir par elle-même les droits d'un corpus clinique : **seuls les responsables légitimes des images, les praticiens et les organismes compétents** peuvent attester les conditions d'origine, traitements et usages.

Étape suivante pour Digital Crown : désigner un responsable légal, déterminer la base juridique et les obligations CNDP pour la finalité commerciale FDI, rédiger/approuver le protocole de collecte/annotation et documenter le traitement des données hors GitHub. Puis seulement, sur un environnement expressément autorisé et protégé, collecter progressivement des images et les faire relire selon ce protocole. Le choix de runners GitHub pour l'entraînement sur vraies images devra être réexaminé *séparément*. Aucun GO réglementaire ou clinique ni copie de radiographies ne peut découler d'un workflow public réussi.

**Contrat utilisateur stable :** le PDF panoramique validé J10H est **un bilan écrit uniquement**, avec image radiographique stockée séparément et protégée dans l'onglet Imagerie.

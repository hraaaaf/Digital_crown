# CEPH-UXCLIN-01 — R23-G15 · Deux revues humaines indépendantes hors ligne / six HOLD Atlas2009

**2026-10-17 — STATUT : mécanisme de collecte et de comparaison préparé. ZÉRO avis humain collecté.** `clinical_release=false`, aucune mesure Atlas33 validée et aucune signature de praticien attestée par G15.

## Pourquoi G15

G14 a rendu vérifiables les dossiers source des six points toujours bloqués : `Ba`, `FOP_PREMOLAR_Ricketts`, `FOP_MOLAR_Ricketts`, `GO_Ricketts_PFH`, `L6_DISTAL_Ricketts`, `PNS_Ricketts`. Les sources générales Ricketts / PubMed / NCBI ont été **explicitement limitées à leur périmètre documentaire**. Elles ne prouvent pas un protocole de clic dans le chapitre 13 du profil Atlas2009, ni une compétence humaine ni une calibration.

L'exécution clinique à faire est **une tâche humaine réelle**, pas un agent ou un test automatisé : deux orthodontistes authentifiés, travaillant indépendamment, doivent lire la source primaire Atlas2009 autorisée et documenter le même ensemble de six identités, dans des sessions séparées. L'automatisation G15 **ne certifie ni la qualification des participants, ni leur indépendance, ni leurs signatures**. Des signatures/identités et l'accord d'usage doivent être traités dans un registre institutionnel contrôlé, hors dépôt.

## Mode d'emploi d'un dossier privé A/B

L'administrateur scientifique habilité détient un checkout du HEAD G15 et un lieu sûr **en dehors du dépôt Git**, auquel seul l'administrateur a accès. Exécuter :

```bash
python -m scripts.cephalo_r23g15_offline_independent_review prepare \
  --private-output-dir /CHEMIN/PROTEGE/CEPH_G15_SESSIONS
```

Ce répertoire, qui doit être vide, reçoit :

- `A/independent_review.html` — questionnaire strictement indépendant de l'expert A.
- `B/independent_review.html` — questionnaire strictement indépendant de l'expert B.
- `PRIVATE_REVIEW_INSTRUCTIONS.txt` — règles de confidentialité et de transmission séparée.

**Distribuer uniquement le formulaire correspondant** à chaque praticien, en l'accompagnant de l'accès légitime à l'édition Atlas2009 (pas de copie piratée), du protocole de recherche approuvé et des mêmes clichés si des illustrations/annotations sont réalisées sur une infrastructure clinique distincte. Les deux experts ne doivent jamais se voir mutuellement les réponses avant clôture. Les deux formulaires sont autonomes : pas de compte, connexion, image ni appel réseau requis. Chaque expert remplit :

1. Un jeton pseudonyme non personnel différent A/B.
2. Pour **chacun des six repères**, trois réponses aux questions anatomiques déjà gelées dans G14.
3. Le statut du repère : `HOLD_UNRESOLVED`, `RULE_PROPOSED_FOR_ADJUDICATION`, `REJECTED_AS_NON_EQUIVALENT`, ou `NOT_VISIBLE_IN_PUBLIC_IMAGES`.
4. La référence précise de la page/figure du chapitre 13 de l'Atlas2009 et une règle de clic détaillée lorsqu'une procédure est proposée.
5. Une politique explicite pour les doubles contours, repères non visibles et exclusions, sans imposer de clic arbitraire.

Le bouton **Exporter** télécharge localement le JSON de sa session. Aucun `localStorage`, réseau, transfert automatique, métadonnée d'identité réelle ou image privée n'est utilisé dans ces formulaires. L'opérateur doit faire parvenir sa réponse à l'administrateur **via un canal privé autorisé**, jamais sur GitHub/Actions/Notion/chat.

## Comparer sans mélanger les réponses ni autoriser un point

Quand l'administrateur dispose de **deux réponses réelles**, il peut exécuter localement :

```bash
python -m scripts.cephalo_r23g15_offline_independent_review compare \
  --review-a /CHEMIN/PRIVE/A_RESPONSE.json \
  --review-b /CHEMIN/PRIVE/B_RESPONSE.json \
  --aggregate-out /CHEMIN/PRIVE/G15_SYNTHÈSE_REDACTEE.json
```

Le validateur refuse :
- le même jeton pseudonyme sous deux rôles, toute substitution de l'un des six IDs et tout changement du HEAD G14 source gelé ;
- une session partielle (trois réponses non remplies pour un point) ou une « règle proposée » dépourvue de source primaire / politique d'incertitude ;
- des champs non autorisés (p. ex. coordonnées anatomiques, image, identifiants patient, pièces justificatives sensibles) ;
- toute promotion par booléens `actual_signature_externally_verified=true`, `human_credentials_externally_verified=true` ou `clinical_release=true`.

Le rapport de sortie contient **uniquement les statuts de chaque relecteur et les accords/désaccords**, aucun jeton, identité, réponse en texte libre, source protégée, patient ou cliché. Une concordance de statut `RULE_PROPOSED_FOR_ADJUDICATION` signifie seulement « deux formulaires proposent d'arbitrer » : **ce n'est pas la validation d'une règle**. Si les procédures diffèrent dans le texte, cela doit être jugé indépendamment lors de l'adjudication humaine, car le compteur de statuts ne prouve pas un accord anatomique.

`clinical_release=false`, `clinically_unlocked_hold_count=0`, `atlas33_clinical_measurements_validated=0`, `real_reviewer_qualifications_verified=false` restent obligatoires pour **tout** rapport G15, même lorsque les deux formulaires sont complets.

## Validation et garde de périmètre

`audit/cephalo_r23g15_contract_tests/test_offline_review.py` utilise des réponses **entièrement synthétiques** afin de rejeter les fausses signatures, le même examinateur sous deux rôles, les contenus incomplets, les fausses identités anatomiques, l'absence de source, la promotion clinique et les données patient. Le scénario navigateur réel `g15_two_offline_forms_e2e.cjs` vérifie une interface **390×844 (mobile autonome)** et **1280×900 (desktop)**, l'absence de réseau et l'export manuel des formulaires A/B. Le test de comparaison doit détecter un désaccord injecté artificiellement et produire le même NO-GO clinique.

**Ces tests ne concernent pas l'affichage mobile de l'application Digital Crown elle-même** : uniquement le formulaire autonome hors ligne. L'existence d'une fonction mobile de repérage dans Digital Crown n'a pas été revendiquée.

Les artefacts CI, si le run aboutit, doivent contenir **uniquement une copie d'écran marquée SYNTHÉTIQUE et un rapport agrégé SYNTHÉTIQUE**. Les deux réponses intégrales utilisées pour l'e2e restent privées et éphémères sur le runner et ne sont pas publiées.

## Conditions de levée future des HOLD (hors G15)

Même après collecte, il faut absolument la vérification réelle, indépendante et traçable des qualifications et des deux signatures, les pages/figures de l'Atlas2009 effectivement consultées et approuvées, la résolution des désaccords selon méthode préenregistrée, les règles illustrées sur clichés autorisés, les politiques `NOT_VISIBLE` et ambiguïtés, l'étalon mm/pixel et l'orientation anatomique même image, la répétabilité inter/intra-expert et la confrontation à un oracle numérique distinct. Les deux clichés publics ANUG/Challiyan utilisés pour les tests G11–G14 sont un jeu de **faisabilité exposé**, pas un goldset clinique intact ; Aariz LOT02 est un autre dataset avec jeu test réservé.

**Pas d'accord par défaut, pas de signature fictive, pas d'activation d'Atlas33 à partir d'un fichier JSON signé de façon non vérifiée.** Une éventuelle décision de déblocage sera un lot séparé avec revues indépendantes réelles sur même HEAD, tests et accord clinique explicite. La PR G15 reste source-only, DRAFT, non mergée, non déployée.

## Roadmap

W1/W2/W3 source descriptions ✓ → G9 strict IDs ✓ → G10 admission metadata ✓ → G11 deux JPEG réels ✓ → G12 clicks pixels ✓ → G13 guides et six HOLD ✓ → G14 protocoles source ✓ → **G15 formulaires A/B et comparaison technique** → recueillir effectivement les signatures/avis de deux orthodontistes OPEN → adjudication clinique illustrée OPEN → goldset calibré OPEN → Atlas33 clinique / closeout OPEN.

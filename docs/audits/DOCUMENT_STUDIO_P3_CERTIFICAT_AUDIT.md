# Document Studio — P3 Certificat — audit

Date de l'audit : 2026-08-15

## Statut

P3 Certificat n'est **pas certifié final** à ce stade.

Le décorticage pratique, technique et médico-légal a produit des correctifs dédiés, mais les PR ouvertes ne peuvent pas être certifiées par GitHub Actions tant que le blocage compte `Billing & plans` empêche les jobs de démarrer. Les runs observés échouent avant toute étape (`steps=[]`, `runner_id=0`).

Aucun pourcentage d'avancement global n'est déclaré tant que l'audit complet, la CI réellement exécutée, les merges et la validation runtime/visuelle ne sont pas clos.

## Baseline déjà mergée

### PR #48 — Nature du document

- mergée ;
- trois parcours explicites : `Arrêt de travail`, `Certificat de Présence`, `Certificat médical` ;
- `Certificat médical` ouvre un contenu libre rédigé par le praticien ;
- aucune suggestion diagnostique ou clinique n'est injectée dans ce contenu ;
- migration des anciennes valeurs prévue ;
- durée applicable uniquement au parcours arrêt de travail.

### PR #49 — Dates + durée

- mergée ;
- date d'émission distincte du début du repos ;
- présence et certificat libre n'exposent pas de durée/date de repos inutile ;
- réouverture historique avec fallback compatible.

Baseline `master` auditée : `a7fc4417e39120ff844c119fd2f4cfe42239bb8b`.

## Lots P3 ouverts

| PR | Scope | Base | Head audité | État GitHub | Certification |
|---|---|---|---|---|---|
| #52 | signature manuscrite + signataire explicite | master | `53e91d82110cf155674294474d2a7c079d6f62c8` | open / mergeable | non certifiée |
| #53 | validation UX praticien | master | `00f85c37639dc5537a2e19387a273e9e91cda1bb` | open / mergeable | non certifiée |
| #54 | signal contextuel non prescriptif | master | `7371793eaa4857dbbd03e461e38bccb422c23f5e` | open / mergeable | CI exact-head bloquée avant steps |
| #55 | identité datée + intégrité PDF | #52 | `f859e9ba652a36bfc4553318d56716ede19fe0d2` | open / mergeable | non certifiée |
| #56 | contrat backend fail-closed | master | `9976a7a5a4a06665dc5601e8af101414d45b9aa7` | open / mergeable | non certifiée |
| #57 | suppression assertions PDF non vérifiées | #55 | `954ae116b174778d9d60056b36ae242ef52f0e3f` | open / mergeable | non certifiée |
| #58 | QR validation fail-closed | #57 | `407c0d8a1814246fe7b8aa4df99648d399dcb34f` | open / mergeable | non certifiée |
| #59 | identité réelle dans zone de signature | #58 | `cee04dbf08c792795fe10046b4ea763b781384ac` | open / mergeable | non certifiée |
| #60 | état neuf sans choix clinique + preview/UX | #53 | `f800925a2b0e72af6816feda1277459a0dca7804` | open / mergeable | CI exact-head à recertifier |
| #63 | impression sûre Certificat uniquement | #60 | `84ad80b14c82a4eb7b297b16526afe55f82af161` | open / mergeable | run 31908774717 : 3 jobs failure avant toute étape, Billing & plans |
| #61 | routage PDF, noms de fichiers, texte libre long | #59 | `f59fb121904b9bf61f67ee3e8d73fdbecf46a2f2` | open / mergeable | run 31908239478 bloqué avant steps |

## Audit pratique

### 1. Nature du certificat

État cible : le praticien choisit explicitement la nature du document.

Correctifs préparés :

- un nouveau certificat démarre avec `type=''` ;
- aucune durée n'est préremplie (`days=0`) ;
- la policy frontend préserve l'état « aucun type sélectionné » ;
- l'auto-preview reste silencieux tant que le formulaire est incomplet ;
- le backend refuse un `reason` ou des `days` uniquement injectés par les defaults Pydantic et non réellement fournis par le client.

### 2. Durée

État cible : aucune durée clinique automatique.

Correctifs préparés :

- suppression du slider prérempli ;
- saisie numérique explicite par le praticien ;
- `Arrêt de travail` : durée obligatoire, entière, borne technique 1..365 ;
- aucune durée n'est issue du signal contextuel ;
- présence et certificat libre purgent les anciens champs de durée/début non applicables.

La borne 1..365 est une borne technique de validation, pas une durée médicale recommandée.

### 3. Signal contextuel

État cible : un signal documentaire peut attirer l'attention mais ne décide jamais du certificat.

Correctifs préparés :

- aucun signal sans élément du jour ;
- un simple rendez-vous `PRÉVU`, `CONFIRMÉ`, `ABSENT`, annulé/refusé/expiré ne constitue pas une preuve de présence ;
- seuls les statuts correspondant à une présence physique observée (`EN_S_ATTENTE`, `EN_FAUTEUIL`, `TERMINÉ`) peuvent soutenir le signal ;
- un acte du jour peut fournir un contexte ;
- chirurgie : signal informatif « évaluer si un repos est nécessaire », sans durée ;
- aptitude/sport : aucune synthèse automatique de certificat d'aptitude ;
- le frontend affiche le contexte sans appliquer automatiquement type, contenu ou durée.

### 4. Certificat médical libre

État cible : texte entièrement sous responsabilité du praticien.

Correctifs préparés :

- contenu libre requis ;
- aucune complétion clinique automatique ;
- échappement ReportLab des données variables ;
- texte long conservé à taille normale et autorisé à passer sur plusieurs pages ;
- aucune miniaturisation progressive jusqu'à 6 pt ;
- identité du signataire portée dans la zone de signature et non injectée dans le texte médical libre.

### 5. PDF et assertions

Assertions automatiques supprimées :

- pas de transformation `mineur -> éviction scolaire` ;
- pas de déduction `dossier ortho -> soins orthodontiques` ;
- pas d'affirmation `remis en main propre à sa demande` sans donnée qui l'établit ;
- certificat de présence limité à une présence constatée ;
- âge calculé à la date d'émission ;
- branding pris sur le cabinet employeur mais signataire conservé comme praticien connecté ;
- noms/observations échappés avant markup ReportLab ;
- raison PDF inconnue : refus, aucun fallback implicite vers arrêt de travail ;
- nom de fichier patient assaini contre séparateurs/caractères de chemin.

### 6. Signature

État cible : signataire réel, signature manuscrite.

Correctifs préparés :

- rôles autorisés : praticien (`ADMIN`/`DENTISTE`) ;
- secrétaire : fail-closed ;
- identité du signataire obligatoire ;
- zone blanche dédiée de 2,4 cm ;
- légende : `Dr <nom> — Signature manuscrite du praticien` ;
- aucun fac-similé, cachet, griffe ou signature automatique injecté par le logiciel.

### 7. QR

Le mode QR `VALIDATION` était incohérent : le PDF était généré avant l'archive avec un identifiant temporaire et aucune route `/verify/{id}` n'a été retrouvée dans le dépôt.

Correctif préparé : désactivation uniquement du QR `VALIDATION` sur le certificat tant qu'un vrai contrat de vérification n'existe pas. Les QR contact/site/localisation restent inchangés.

### 8. Preview, impression, doublon, archive

- preview : aucune archive ;
- preview invalide : aucun appel backend inutile ;
- le direct-print Certificat sur un `pdfUrl` potentiellement ancien est évité par #63 : le bouton `Préparer impression` génère et archive un PDF frais, puis ouvre ce fichier final pour impression ;
- le hook partagé n'est pas modifié et les autres types de documents conservent leur comportement actuel ;
- doublon : conflit contrôlé puis possibilité de forcer une nouvelle version ;
- archive : snapshot de `req.data` ;
- réouverture : type, durée, début du repos, texte libre et date du document sont réhydratés.

## Audit médico-légal

Source officielle consultée : Secrétariat Général du Gouvernement, décret n° 2-96-989 du 5 janvier 1999 rendant applicable le code de déontologie des médecins-dentistes.

Points directement pertinents :

- article 9 : certificat de complaisance interdit ;
- article 23 : certificats/attestations/documents établis conformément aux constatations que le médecin-dentiste est en mesure de faire ; signature manuscrite obligatoire ; griffe ou procédé de substitution interdit ;
- article 24 : soins conformes aux données acquises de la science.

Conséquence de conception retenue pour P3 : le logiciel ne doit pas inventer un fait clinique/documentaire, décider automatiquement d'une durée, ni remplacer la signature du praticien.

Ce rapport est un audit logiciel/médico-documentaire du module ; il ne constitue pas une consultation juridique indépendante ni une certification réglementaire externe.

## Tests ajoutés dans les lots

Couverture préparée notamment pour :

- migrations des anciens types ;
- état neuf sans type/durée ;
- contenu libre requis ;
- durée explicitement saisie ;
- statuts RDV positifs/négatifs pour présence ;
- signataire autorisé/non autorisé ;
- zone manuscrite ;
- âge à date d'émission ;
- échappement PDF ;
- propriétaire du branding multi-dentiste ;
- sémantique conservatrice du PDF ;
- QR fail-closed ;
- routage exact des types ;
- noms de fichiers ;
- texte libre long ;
- auto-preview invalide ;
- action `Préparer impression` Certificat isolée du direct-print des autres documents.

## Blocages réels avant certification finale

1. **CI GitHub Actions** : blocage compte `Billing & plans` ; les runs observés, y compris #63 run `31908774717`, échouent avant toute étape (`steps=[]`, `runner_id=0`). Aucun échec de test applicatif ne peut être déduit de ces runs.
2. **Merges** : les PR sont encore ouvertes et certaines sont empilées ; elles doivent être fusionnées dans l'ordre de dépendance puis recertifiées sur la baseline finale.
3. **Régression finale** : backend + frontend + PDF après convergence des piles.
4. **Runtime/visuel** : génération réelle des trois parcours et inspection du PDF final requises après convergence.
5. **Closeout canonique** : roadmap/statut/changelog à mettre à jour uniquement après preuves finales.

## Ordre de convergence recommandé

Lots indépendants :

1. #54 — signal contextuel ;
2. #56 — contrat backend.

Pile UX :

1. #53 ;
2. #60 ;
3. #63.

Pile PDF :

1. #52 ;
2. #55 ;
3. #57 ;
4. #58 ;
5. #59 ;
6. #61.

Après chaque merge parent : rebase/retarget du lot enfant si nécessaire, CI exacte-head réellement exécutée, puis merge. Après convergence : régression P3 complète + validation runtime/visuelle + mise à jour des fichiers canoniques.

## Amélioration non bloquante identifiée

Le dépôt ne contient pas de garde SPA générique de type `useBlocker/usePrompt` pour protéger les formulaires non archivés lors d'une navigation applicative. Éviter une implémentation isolée uniquement pour Certificat ; traiter ce point comme amélioration transversale du Document Studio.
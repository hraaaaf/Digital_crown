# Document Studio — P3 Certificat — audit

Date de l'audit : 2026-08-15

## Statut

P3 Certificat est **convergé côté code sur `master`**, mais n'est **pas certifié final**.

L'utilisateur a explicitement demandé de poursuivre malgré l'indisponibilité de GitHub Actions. Les runs concernés ont échoué avant toute étape (`steps=[]`, `runner_id=0`) pour un blocage `Billing & plans`; aucun résultat de test applicatif n'est donc revendiqué à partir de ces runs.

Le closeout final reste conditionné à une régression réellement exécutée et à une validation runtime/visuelle des trois parcours Certificat.

## Baseline et convergence

Baseline initiale auditée : `a7fc4417e39120ff844c119fd2f4cfe42239bb8b`.

PR fonctionnelles P3 désormais mergées sur `master` :

- #48 — Nature du document ;
- #49 — Dates + durée ;
- #54 — signal contextuel non prescriptif ; merge `c60331bea48e35ffb9ba4eeb424dfe4c43362511` ;
- #56 — contrat backend fail-closed ; merge `5249a62dc97a86ca35364180db7531db10754213` ;
- #53 — validation UX praticien ; merge `a16b6b851bcd2a114723932d285fab511dc48549` ;
- #52 — signature manuscrite + signataire DENTISTE uniquement ; merge `238c631339f265dc07cedfc73e318ae6be38a64e` ;
- #60 — état neuf sans choix clinique + preview/UX ; merge `46800f5ef17d8a519fd1c66106a2a1e23c92f513` ;
- #63 — impression sûre limitée au Certificat ; merge `595f52b843fe74b74f673b5f77492f9f85c51b46` ;
- #55 — identité datée + intégrité PDF ; merge `873f4227f601ea4c0d12fd994743b56109907dbc` ;
- #57 — suppression des assertions PDF non vérifiées ; merge `282d2f32f91fbee7e9b5fb300711a19456efcd19` ;
- #58 — QR validation fail-closed ; merge `50c8bfc8a183935c8993b390e13f91b84bcea071` ;
- #59 — identité réelle du signataire dans la zone manuscrite ; merge `b4f91b97fd74491f6a7c41de1a5ca7a62fd51a94` ;
- #61 — routage PDF, noms de fichiers et texte libre long ; merge `91a93ca3bade4a33f7968f82d4e5bd9a14b3d481`.

## Audit pratique synthétique

### Nature / durée
- nouveau certificat : `type=''`, `days=0` ;
- aucun type ni durée clinique préremplis ;
- auto-preview silencieux tant que l'état est invalide ;
- backend refuse les defaults implicites ;
- arrêt de travail : durée entière explicite 1..365, borne technique et non recommandation médicale.

### Signal contextuel
- aucun signal sans élément du jour ;
- seuls `EN_S_ATTENTE`, `EN_FAUTEUIL`, `TERMINÉ` peuvent soutenir une présence à partir d'un RDV ;
- un simple `PRÉVU`, `CONFIRMÉ`, `ABSENT`, annulé/refusé/expiré ne constitue pas une preuve de présence ;
- aucun type ni durée n'est appliqué automatiquement ;
- aucune aptitude/sport n'est synthétisée automatiquement.

### Certificat médical libre / PDF
- contenu entièrement rédigé par le praticien et obligatoire ;
- aucune complétion clinique automatique ;
- données variables échappées avant markup ReportLab ;
- texte libre long autorisé en multi-page sans miniaturisation illisible ;
- aucune inférence `mineur -> éviction scolaire`, `ortho -> soins orthodontiques`, ou `remis en main propre à sa demande` ;
- raison PDF inconnue refusée ;
- nom de fichier patient assaini.

### Signature
- seul le rôle `DENTISTE` est autorisé à signer ;
- `ADMIN` et `SECRETAIRE` sont refusés fail-closed faute d'attribut distinct prouvant une qualification de chirurgien-dentiste ;
- identité du signataire obligatoire ;
- zone blanche dédiée 2,4 cm ;
- signature manuscrite uniquement ; aucun fac-similé, griffe ou substitution logicielle.

### QR / preview / impression / archive
- QR `VALIDATION` neutralisé tant qu'aucun contrat `/verify/{id}` valide n'existe ;
- preview n'archive pas ;
- preview invalide n'appelle pas le backend ;
- `Préparer impression` génère/stocke un PDF frais pour Certificat sans modifier le flux des autres documents ;
- doublon géré par version forcée ;
- snapshot `req.data` archivé puis réhydraté à la réouverture.

## Audit médico-légal

Source officielle consultée : Secrétariat Général du Gouvernement, décret n° 2-96-989 du 5 janvier 1999 rendant applicable le code de déontologie des médecins-dentistes.

Points directement pertinents :
- article 9 : certificat de complaisance interdit ;
- article 23 : certificat conforme aux constatations que le médecin-dentiste est en mesure de faire ; signature manuscrite obligatoire ; griffe ou procédé de substitution interdit ;
- article 24 : actes conformes aux données acquises de la science.

Conséquence de conception retenue pour P3 : le logiciel ne doit pas inventer un fait clinique/documentaire, décider automatiquement d'une durée, ni remplacer la signature du praticien.

Ce rapport est un audit logiciel/médico-documentaire du module ; il ne constitue pas une consultation juridique indépendante ni une certification réglementaire externe.

## Limite de preuve CI

GitHub Actions n'a pas fourni de validation exploitable sur les derniers heads P3. Exemple : run #63 `31908774717`, trois jobs en échec avant toute étape, `runner_id=0`, annotation `Billing & plans`.

La convergence ci-dessus est donc une convergence de code audité et mergé, **pas une CI verte**.

## Restant avant certification finale P3

1. Régression réellement exécutée sur la baseline `master` convergée : backend + frontend + PDF.
2. Runtime réel des trois parcours : `Arrêt de travail`, `Certificat de Présence`, `Certificat médical` libre.
3. Inspection visuelle des PDF générés, notamment texte libre long, zone de signature, identité praticien et absence de QR de validation invalide.
4. Mise à jour finale ROADMAP/STATUS/CHANGELOG uniquement après ces preuves.

## Amélioration non bloquante

Le dépôt ne contient pas de garde SPA générique `useBlocker/usePrompt` pour protéger les formulaires non archivés lors d'une navigation applicative. À traiter transversalement dans Document Studio, pas uniquement sur Certificat.

# Sources — Mutuelles dentaires Maroc

Date de recherche : 2026-09-14.
Règle : distinguer source institutionnelle, référence cabinet validée et copie secondaire. Aucun formulaire n’est activé dans le runtime dans ce lot.

## CNOPS — page institutionnelle verrouillée, binaire officiel exact non récupéré
- Page institutionnelle : `https://www.cnops.org.ma/fr/infopratiques`
- Page de téléchargement institutionnelle : `https://www.cnops.org.ma/fr/node/115`
- La CNOPS expose explicitement une section `Feuille de soins dentaires` et une entrée de téléchargement correspondante.
- Dossier dentaire : `https://www.cnops.org.ma/fr/dossierem?r=117`
- Soins dentaires : `https://www.cnops.org.ma/fr/soins-dentaires`
- Convention chirurgiens-dentistes hébergée CNOPS : arrêté n°1962-06 ; son article 10 impose l’usage de feuilles conformes aux modèles arrêtés par l’ANAM.
- Nomenclature hébergée CNOPS : `https://cnops.org.ma/sites/default/files/2022-10/Nomeclature_0.pdf`
- Copie visuelle secondaire : `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnops-feuille-de-soins-dentaire.pdf`
- La copie secondaire est détectée comme PDF de **2 pages** par le backend documentaire consulté le 2026-09-14.
- Le binaire exact derrière le téléchargement CNOPS n’a pas pu être récupéré dans ce lot : la page institutionnelle est indexée mais la récupération directe expire côté source.
- Aucun SHA-256 CNOPS n’est donc déclaré.
- Statut : `VERIFIED_INSTITUTIONAL_PAGE / OFFICIAL_BINARY_RETRIEVAL_PENDING`.

### Exigences CNOPS recoupées sur source institutionnelle
Pour le médecin dentiste, la CNOPS indique notamment : identité assuré/bénéficiaire, INPE, cachet/signature, date des soins, honoraires et actes sur schéma dentaire. Selon les actes, note/facture, IF/ICE et radiographies sont également exigés.

## CNSS — référence cabinet validée
- Référence cabinet : `https://dentiste-rabat.com/wp-content/uploads/2023/03/610-1-04_2.pdf`
- Référence imprimée : `610-1-04`, Réf. ANAM `1.2.03.01`.
- Validation métier : praticien utilisateur, 2026-09-14.
- Le backend documentaire détecte le PDF de référence comme document de **2 pages**.
- Les octets du fichier n’ont pas pu être récupérés dans l’environnement de travail courant ; aucun SHA-256 n’est donc inventé.
- Statut : `VERIFIED_CABINET_REFERENCE / BINARY_HASH_PENDING / PRIMARY_LOCK_PENDING`.
- Autre copie secondaire : `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnss-feuille-de-soins-dentaires.pdf`

Une source secondaire contradictoire avait mentionné `611-1-04`; la référence cabinet retenue reste `610-1-04`.

## Mutuelle des FAR / DMFAR — référence cabinet validée
- Portail officiel : `https://mutuelle.far.ma`
- Copie publique validée visuellement par le praticien utilisateur : `https://fr.scribd.com/document/1025435428/Feuille-de-Mutuelle-FAR-2021-1`
- Validation métier confirmée dans la conversation le 2026-09-14.
- Contenu observé : identité adhérent/bénéficiaire, INPE, page ordonnance, page `SOINS ET PROTHESE DENTAIRE (INPE)`, date, position dent, nature des travaux, coefficient, honoraires, schéma dentaire.
- Le binaire téléchargeable exact n’est pas disponible de manière fiable depuis la copie Scribd dans l’environnement courant ; aucun SHA-256 n’est déclaré.
- Statut : `VERIFIED_CABINET_REFERENCE / BINARY_HASH_PENDING / PRIMARY_LOCK_PENDING`.

La validation cabinet n’est pas présentée comme preuve que le binaire Scribd est la version institutionnelle courante.

## NGAP / TNR — sources d’autorité
### ONMD
- NGAP : `https://www.onmd.ma/ngap`
- Communiqué 01/26 du 02/02/2026 : `https://onmd.ma/actualites-communiques/communique-du-conseil-national-de-lordre-national-des-medecins-dentistes-relatif-a-la-feuille-de-soins-dentaires-et-a-la-ngap-n-0126`
- Niveau : PRIMAIRE MÉTIER.

### ANAM
- Réglementation : `https://anam.ma/anam/reglementation/textes-en-relation-avec-le-domaine-de-la-sante/`
- Niveau : PRIMAIRE INSTITUTIONNEL.

### Index pratique secondaire
- `https://www.ngap-maroc.com/`
- Usage : recherche/contrôle ; jamais seule autorité d’un code automatique.

## Politique de verrouillage d’un template
Avant implémentation d’un renderer, conserver : organisme, référence exacte, URL/source, date de récupération, SHA-256 du binaire lorsque réellement récupéré, nombre de pages, version/date imprimée, mapping des champs, règles/pièces, statut de validation institutionnelle et/ou cabinet.

Les références cabinet peuvent guider la préparation et les tests visuels hors runtime. Elles ne doivent pas être élevées artificiellement au statut `VERIFIED_PRIMARY`.

Si le binaire exact n’est pas récupérable, le statut reste explicitement `BINARY_HASH_PENDING` ; un hash ne doit jamais être déduit d’une URL, d’une capture ou d’un index web.
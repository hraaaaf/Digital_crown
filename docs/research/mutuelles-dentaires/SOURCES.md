# Sources — Mutuelles dentaires Maroc

Date de recherche : 2026-09-14.
Règle : distinguer source institutionnelle, référence cabinet validée et copie secondaire. Aucun formulaire n’est activé dans le runtime dans ce lot.

## CNOPS — page institutionnelle verrouillée, binaire à hasher
- Page institutionnelle : `https://www.cnops.org.ma/fr/infopratiques`
- La page CNOPS expose une section `Feuille de soins dentaires` avec visuels/téléchargement.
- Dossier dentaire : `https://www.cnops.org.ma/fr/dossierem?r=117`
- Soins dentaires : `https://www.cnops.org.ma/fr/node/195`
- Entente préalable : `https://www.cnops.org.ma/fr/node/121`
- Nomenclature hébergée CNOPS : `https://cnops.org.ma/sites/default/files/2022-10/Nomeclature_0.pdf`
- Copie visuelle secondaire : `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnops-feuille-de-soins-dentaire.pdf`
- Statut : `VERIFIED_INSTITUTIONAL_PAGE / BINARY_HASH_PENDING`.

## CNSS — référence cabinet validée
- Référence cabinet : `https://dentiste-rabat.com/wp-content/uploads/2023/03/610-1-04_2.pdf`
- Référence imprimée : `610-1-04`, Réf. ANAM `1.2.03.01`.
- Validation métier : praticien utilisateur, 2026-09-14.
- Statut : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.
- Autre copie secondaire : `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnss-feuille-de-soins-dentaires.pdf`

Une source secondaire contradictoire avait mentionné `611-1-04`; la référence cabinet retenue reste `610-1-04`.

## Mutuelle des FAR / DMFAR — référence cabinet validée
- Portail officiel : `https://mutuelle.far.ma`
- Copie publique validée visuellement par le praticien utilisateur : `https://fr.scribd.com/document/1025435428/Feuille-de-Mutuelle-FAR-2021-1`
- Validation métier confirmée dans la conversation le 2026-09-14.
- Contenu observé : identité adhérent/bénéficiaire, INPE, page ordonnance, page `SOINS ET PROTHESE DENTAIRE (INPE)`, date, position dent, nature des travaux, coefficient, honoraires, schéma dentaire.
- Statut : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.

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
Avant implémentation d’un renderer, conserver : organisme, référence exacte, URL/source, date de récupération, SHA-256 du binaire, nombre de pages, version/date imprimée, mapping des champs, règles/pièces, statut de validation institutionnelle et/ou cabinet.

Les références cabinet peuvent guider la préparation et les tests visuels hors runtime. Elles ne doivent pas être élevées artificiellement au statut `VERIFIED_PRIMARY`.

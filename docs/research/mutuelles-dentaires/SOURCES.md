# Sources — Mutuelles dentaires Maroc

Date de recherche : 2026-09-14.
Règle : une copie publique non officielle sert uniquement à comprendre la structure ; elle ne devient jamais un template canonique.

## CNOPS — primaire

### Feuille / dossier dentaire
- Source : `https://www.cnops.org.ma/fr/dossierem?r=117`
- Niveau : PRIMAIRE.
- Usage : exigences de dossier dentaire, identité assuré/bénéficiaire, praticien/INPE, actes, honoraires, pièces et accords selon cas.

### Références conventionnelles / nomenclature
- Source hébergée CNOPS : `https://cnops.org.ma/sites/default/files/2022-10/Nomeclature_0.pdf`
- Niveau : PRIMAIRE/HÉBERGEMENT INSTITUTIONNEL.
- Usage : cadre NGAP général ; doit être recoupé avec ONMD/ANAM avant constitution du référentiel applicatif.

### Copie de formulaire
- `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnops-feuille-de-soins-dentaire.pdf`
- Niveau : SECONDAIRE.
- Usage : repérage visuel uniquement jusqu’au verrouillage/hash d’un original officiel courant.

## CNSS — référence cabinet validée, source primaire encore à verrouiller

Référence visuelle validée par le praticien utilisateur le 2026-09-14 comme étant le formulaire effectivement utilisé dans son cabinet :
- `https://dentiste-rabat.com/wp-content/uploads/2023/03/610-1-04_2.pdf`
- Référence : `610-1-04`
- Validation : `VERIFIED_CABINET_REFERENCE`

Cette validation métier permet d’utiliser ce document comme référence fonctionnelle et visuelle pour la préparation hors runtime. Elle ne remplace pas le verrouillage ultérieur d’un binaire officiel courant depuis une source primaire CNSS avant activation applicative.

Autre copie secondaire observée :
- `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnss-feuille-de-soins-dentaires.pdf`

Une source secondaire contradictoire avait mentionné `611-1-04`; la référence `610-1-04` est désormais retenue comme référence cabinet validée, sans la déclarer `VERIFIED_PRIMARY`.

Statut template : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.

## Mutuelle des FAR / DMFAR — officiel courant non verrouillé

- Portail officiel : `https://mutuelle.far.ma`
- Niveau : PRIMAIRE pour l’existence du portail, mais le formulaire dentaire courant n’a pas pu être récupéré dans ce lot.

Une copie publique observée contient notamment :
- page d’identité assuré/bénéficiaire/praticien ;
- page `ORDONNANCE` ;
- page `SOINS ET PROTHESE DENTAIRE (INPE)` avec date, position dent, nature des travaux, coefficient et honoraires.

Cette copie reste informative et non canonique tant que le document officiel courant n’est pas verrouillé.

Statut template : `UNVERIFIED_PRIMARY_LOCK_REQUIRED`.

## NGAP / TNR — sources d’autorité

### ONMD
- NGAP : `https://www.onmd.ma/ngap`
- Communiqué 01/26 du 02/02/2026 relatif à la feuille de soins dentaires et à la NGAP : `https://onmd.ma/actualites-communiques/communique-du-conseil-national-de-lordre-national-des-medecins-dentistes-relatif-a-la-feuille-de-soins-dentaires-et-a-la-ngap-n-0126`
- Niveau : PRIMAIRE MÉTIER.

### ANAM
- Réglementation santé : `https://anam.ma/anam/reglementation/textes-en-relation-avec-le-domaine-de-la-sante/`
- Niveau : PRIMAIRE INSTITUTIONNEL.

### Index pratique secondaire
- `https://www.ngap-maroc.com/`
- Niveau : SECONDAIRE.
- Usage permis : recherche/contrôle ergonomique ; interdit comme seule autorité de génération automatique.

## Politique de verrouillage d’un template
Avant toute implémentation d’un renderer assureur, enregistrer :
- organisme ;
- nom/référence exacte du document ;
- URL primaire ;
- date de récupération ;
- hash SHA-256 du binaire ;
- nombre de pages ;
- version/date imprimée si disponible ;
- mapping des champs ;
- règles/pièces associées ;
- statut `VERIFIED_PRIMARY`.

Sans ces métadonnées, le template reste recherche uniquement.
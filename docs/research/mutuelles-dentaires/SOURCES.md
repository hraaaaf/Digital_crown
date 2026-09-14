# Sources — Mutuelles dentaires Maroc

Date de recherche : 2026-09-14.
Règle : distinguer source institutionnelle, référence cabinet validée et copie secondaire. Aucun formulaire n’est activé dans le runtime dans ce lot.

## CNOPS — source institutionnelle verrouillée au niveau page, binaire à hasher

### Page officielle « Info pratiques / Feuille de soins »
- Source institutionnelle : `https://www.cnops.org.ma/fr/infopratiques`
- La page CNOPS affiche explicitement une section `2- Feuille de soins dentaires`, avec les deux faces/images du formulaire et une entrée de téléchargement `Feuille de soins dentaires`.
- Statut : `VERIFIED_INSTITUTIONAL_PAGE`.
- Limite : le binaire exact de téléchargement n’a pas été récupéré/hashé dans ce lot ; le renderer reste donc interdit.

### Dossier dentaire / exigences
- Source : `https://www.cnops.org.ma/fr/dossierem?r=117`
- Niveau : PRIMAIRE.
- Vérifié : identité assuré/malade, INPE praticien, cachet/signature, date des soins, honoraires et renseignement des actes sur le schéma dentaire ; selon cas note d’honoraires/facture, IF/ICE et radios.

### Soins dentaires / pièces selon actes
- Source institutionnelle : `https://www.cnops.org.ma/fr/node/195`
- Niveau : PRIMAIRE.
- Usage : exigences par type de soin, dent concernée, radios et éléments administratifs.

### Entente préalable
- Source institutionnelle : `https://www.cnops.org.ma/fr/node/121`
- Niveau : PRIMAIRE.
- Usage : actes soumis à accord préalable et pièces associées.

### Références conventionnelles / nomenclature
- Source hébergée CNOPS : `https://cnops.org.ma/sites/default/files/2022-10/Nomeclature_0.pdf`
- Niveau : PRIMAIRE/HÉBERGEMENT INSTITUTIONNEL.
- Usage : cadre NGAP général ; à recouper avec ONMD/ANAM pour le référentiel applicatif.

### Copie visuelle secondaire
- `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnops-feuille-de-soins-dentaire.pdf`
- Niveau : SECONDAIRE.
- Usage : contrôle visuel seulement tant que le binaire institutionnel exact n’est pas hashé.

Statut template CNOPS : `VERIFIED_INSTITUTIONAL_PAGE / BINARY_HASH_PENDING`.

## CNSS — référence cabinet validée, primaire encore à verrouiller

Référence visuelle validée par le praticien utilisateur le 2026-09-14 comme formulaire effectivement utilisé dans son cabinet :
- `https://dentiste-rabat.com/wp-content/uploads/2023/03/610-1-04_2.pdf`
- Référence : `610-1-04`
- Validation : `VERIFIED_CABINET_REFERENCE`

Cette validation métier autorise son usage comme référence fonctionnelle/visuelle de préparation hors runtime. Elle ne vaut pas verrouillage institutionnel du binaire courant.

Autre copie secondaire :
- `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnss-feuille-de-soins-dentaires.pdf`

Une source secondaire contradictoire avait mentionné `611-1-04`; la référence retenue est `610-1-04` car validée par le cabinet.

Statut template CNSS : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.

## Mutuelle des FAR / DMFAR — validation métier encore requise

- Portail officiel : `https://mutuelle.far.ma`
- Niveau : PRIMAIRE pour l’existence du portail ; binaire dentaire courant non récupéré.
- Copie publique fournie/observée : `https://fr.scribd.com/document/1025435428/Feuille-de-Mutuelle-FAR-2021-1`

La copie publique contient notamment :
- identité assuré/bénéficiaire/praticien ;
- page `ORDONNANCE` ;
- page `SOINS ET PROTHESE DENTAIRE (INPE)` avec date, position dent, nature des travaux, coefficient et honoraires.

Statut template FAR : `CABINET_VISUAL_CONFIRMATION_PENDING / PRIMARY_LOCK_PENDING`.

## NGAP / TNR — sources d’autorité

### ONMD
- NGAP : `https://www.onmd.ma/ngap`
- Communiqué 01/26 du 02/02/2026 : `https://onmd.ma/actualites-communiques/communique-du-conseil-national-de-lordre-national-des-medecins-dentistes-relatif-a-la-feuille-de-soins-dentaires-et-a-la-ngap-n-0126`
- Niveau : PRIMAIRE MÉTIER.

### ANAM
- Réglementation santé : `https://anam.ma/anam/reglementation/textes-en-relation-avec-le-domaine-de-la-sante/`
- Niveau : PRIMAIRE INSTITUTIONNEL.

### Index pratique secondaire
- `https://www.ngap-maroc.com/`
- Niveau : SECONDAIRE.
- Usage permis : recherche/contrôle ; jamais seule autorité d’un code automatique.

## Politique de verrouillage d’un template
Avant implémentation d’un renderer :
- organisme ;
- nom/référence exacte ;
- URL/source ;
- date de récupération ;
- SHA-256 du binaire ;
- nombre de pages ;
- version/date imprimée si disponible ;
- mapping des champs ;
- règles/pièces ;
- statut de validation institutionnelle et/ou cabinet.

Sans ces métadonnées, le template reste hors runtime.

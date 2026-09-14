# Template lock status — CNOPS / CNSS / FAR

Date : 2026-09-14.
Statut : RESEARCH ONLY — aucun renderer activé.

## Goal
Verrouiller la référence exacte de chaque formulaire avec provenance, nombre de pages et SHA-256 dès que les octets sont récupérables. Ne jamais inventer un hash ni promouvoir une copie secondaire en source primaire.

## CNOPS
- page institutionnelle confirmée : `https://cnops.org.ma/infopratiques` ; elle expose explicitement une section `Feuille de soins dentaires` et un téléchargement ;
- page institutionnelle dossier dentaire confirmée : `https://www.cnops.org.ma/fr/dossierem?r=117` ; elle exige notamment identité assuré/bénéficiaire, INPE, cachet/signature, date, honoraires et schéma dentaire ;
- copie visuelle secondaire : `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnops-feuille-de-soins-dentaire.pdf` ;
- PDF secondaire observé comme document 2 pages via l'index web ;
- binaire institutionnel exact : NON RÉCUPÉRÉ dans cette session ; accès direct CNOPS en timeout ;
- SHA-256 : NON CALCULÉ ; aucune valeur ne doit être inventée ;
- statut : `VERIFIED_INSTITUTIONAL_PAGE / BINARY_HASH_PENDING`.

## CNSS
- référence cabinet : `610-1-04`, Réf. ANAM `1.2.03.01` ;
- URL : `https://dentiste-rabat.com/wp-content/uploads/2023/03/610-1-04_2.pdf` ;
- PDF observé comme document 2 pages via l'index web ;
- aperçu indexé cohérent avec le formulaire bilingue CNSS validé cabinet ;
- binaire non récupéré localement dans cette session à cause d'un échec de téléchargement/résolution ;
- SHA-256 : NON CALCULÉ ;
- statut : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.

## FAR
- référence cabinet validée : `Feuille de Mutuelle FAR 2021-1` ;
- copie publique : `https://fr.scribd.com/document/1025435428/Feuille-de-Mutuelle-FAR-2021-1` ;
- portail institutionnel : `https://mutuelle.far.ma` ;
- validation métier cabinet : ACQUISE le 2026-09-14 ;
- binaire institutionnel exact : NON VERROUILLÉ ;
- SHA-256 : NON CALCULÉ ;
- statut : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.

## Règle de lock final
Un template ne passe à `BINARY_LOCKED` que si les éléments suivants sont tous présents :
1. source exacte ;
2. date de récupération ;
3. nombre de pages ;
4. SHA-256 calculé sur les octets réellement archivés ;
5. version/référence imprimée si présente ;
6. comparaison visuelle avec la référence métier ;
7. statut de confiance séparant validation cabinet et source primaire.

## Blocage externe actuel
Le blocage concerne uniquement la récupération fiable des octets depuis les sources web dans cette session. Il ne bloque pas la préparation des tests, du plan de migration ni de l'audit anti-doublon.
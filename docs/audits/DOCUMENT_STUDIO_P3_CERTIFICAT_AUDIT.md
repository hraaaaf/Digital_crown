# Document Studio — P3 Certificat + Document Libre — audit

Date initiale : 2026-08-15  
Extension Document Libre : 2026-08-16

## Statut

P3 est **convergé côté engineering pour les lots Certificat et Document Libre corrigés**, mais n'est **pas certifié final**.

Limites de preuve actuelles :
- GitHub Actions échoue encore avant exécution réelle des jobs sur les heads observés (`steps=[]`, `runner_id=0`) ; aucune CI verte n'est revendiquée pour les lots récents ;
- l'utilisateur a explicitement demandé de continuer malgré ce gate indisponible ;
- aucune interaction authentifiée runtime ni inspection visuelle finale des PDF issus du `master` convergé n'est encore revendiquée ;
- une dette sécurité P3-H reste ouverte sur la permission d'émission de Document Libre/Lettre.

Aucun pourcentage global P3 n'est déclaré tant que ces gates ne sont pas fermés.

## Convergence Certificat

PR fonctionnelles mergées :

- #48 — Nature du document ;
- #49 — Dates + durée ;
- #54 — signal contextuel non prescriptif ; merge `c60331bea48e35ffb9ba4eeb424dfe4c43362511` ;
- #56 — contrat backend fail-closed ; merge `5249a62dc97a86ca35364180db7531db10754213` ;
- #53 — validation UX praticien ; merge `a16b6b851bcd2a114723932d285fab511dc48549` ;
- #52 — signature manuscrite + signataire DENTISTE uniquement ; merge `238c631339f265dc07cedfc73e318ae6be38a64e` ;
- #60 — état neuf sans choix clinique + preview/UX ; merge `46800f5ef17d8a519fd1c66106a2a1e23c92f513` ;
- #63 — impression sûre Certificat ; merge `595f52b843fe74b74f673b5f77492f9f85c51b46` ;
- #55 — identité datée + intégrité PDF ; merge `873f4227f601ea4c0d12fd994743b56109907dbc` ;
- #57 — suppression assertions PDF non vérifiées ; merge `282d2f32f91fbee7e9b5fb300711a19456efcd19` ;
- #58 — QR validation fail-closed ; merge `50c8bfc8a183935c8993b390e13f91b84bcea071` ;
- #59 — identité réelle du signataire dans la zone manuscrite ; merge `b4f91b97fd74491f6a7c41de1a5ca7a62fd51a94` ;
- #61 — routage PDF, noms de fichiers et texte libre long ; merge `91a93ca3bade4a33f7968f82d4e5bd9a14b3d481`.

### Contrat Certificat obtenu

- nouveau certificat : `type=''`, `days=0` ; aucun type ni durée clinique préremplis ;
- arrêt de travail : durée entière explicite 1..365, borne technique uniquement ;
- certificat médical libre : contenu 100 % praticien obligatoire ;
- présence : seuls des événements réellement compatibles avec une présence (`EN_S_ATTENTE`, `EN_FAUTEUIL`, `TERMINÉ` ou acte réalisé) peuvent soutenir le signal ;
- `PRÉVU`, `CONFIRMÉ`, `ABSENT`, annulé/refusé/expiré ne constituent pas une preuve de présence ;
- aucune mutation automatique type/durée ;
- aucun fallback inconnu vers arrêt de travail ;
- aucune inférence `mineur -> éviction scolaire`, `ortho -> soins orthodontiques` ou `remis en main propre` ;
- QR `VALIDATION` neutralisé sans contrat `/verify/{id}` valide ;
- signataire : rôle `DENTISTE` uniquement, identité obligatoire, zone de signature manuscrite, aucun fac-similé/griffe/substitution ;
- impression Certificat : PDF final frais préparé avant impression.

## Convergence Document Libre

Baseline antérieure :
- #40 — validation visuelle des champs `libreTitle`/`libreContent` + boutons de toolbar non-submit ; CI antérieure 3/3 SUCCESS ; merge déjà présent avant cette extension.

Lots ajoutés pendant l'audit complet :

- #64 — **P3-D contrat + PDF sûr** ; merge `3d9bcd29330fbb1f8be51b53b77718fda88d5d49` ;
- #65 — **P3-E impression sûre** ; merge `b8e0480b6bdfc6c4c61d4ef31c7ea42b75a59a5c` ;
- #66 — **P3-F auto-preview invalide silencieux** ; merge `cf805726553431849b514575c79f4648f6b552e0` ;
- #67 — **P3-G protection des brouillons** ; merge `7ec3f6777b5af22d6cc5c4af286d0d6da9d76918`.

### P3-D — contrat + PDF sûr

Défauts corrigés :
- titre/contenu doivent être explicitement fournis et non vides ;
- bornes de volume : titre 200 caractères, contenu 100 000 ;
- formats strictement `A4 | A5` ; alignements strictement `left | center | right | justify` ;
- données variables échappées avant ReportLab ;
- allowlist de markup issue de la toolbar : `b`, `i`, `u`, `font size=16` ; markup arbitraire échappé ; balises autorisées déséquilibrées rendues sûres ;
- tableau Markdown normalisé, largeur bornée au document et en-tête répétable ;
- nom de fichier patient/titre assaini contre séparateurs et caractères de contrôle ;
- branding d'un dentiste sous-compte résolu depuis le cabinet employeur ;
- âge calculé à la date du document ;
- `Masquer l'en-tête patient` ne masque plus la date ;
- document long rendu en multi-page à taille normale au lieu d'être compressé jusqu'à 6 pt ;
- titre avec caractères XML (`&`, `<`, `>`) échappé après transformation d'affichage pour préserver les entités valides.

Tests source ajoutés pour ces contrats. Ils n'ont pas été déclarés exécutés avec succès dans cette session.

### P3-E — impression

- Document Libre rejoint Certificat sur le flux `Préparer impression` ;
- génération/archivage d'un PDF frais avant impression ;
- l'ancien aperçu ne peut plus être utilisé comme impression finale par ce bouton ;
- Ordonnance/Devis/Honoraires restent hors scope et inchangés.

### P3-F — preview

- titre ou contenu Libre invalide : auto-preview abandonné silencieusement avant appel backend ;
- validation finale stricte inchangée ;
- un brouillon valide reste prévisualisable.

### P3-G — protection de saisie

- toute mutation utilisateur Libre marque le brouillon dirty : titre, contenu, destinataire, date/lieu, masquage patient, format, alignement, toolbar/tableau ;
- fermeture/rechargement navigateur protégés par `beforeunload` ;
- changement d'onglet demande confirmation ;
- refus = aucune navigation ; confirmation = abandon explicite + reset ;
- après archivage Libre réussi, dirty-state remis à zéro ; un échec de génération ne le réinitialise pas.

## Archive / réutilisation / templates

### Réutilisation vérifiée statiquement

Le snapshot `req.data` archivé permet la réouverture et la réhydratation de :
- titre ;
- contenu ;
- destinataire ;
- date/lieu personnalisé ;
- masquage de l'en-tête patient ;
- format A4/A5 ;
- alignement.

La réutilisation d'un Document Libre archivé existe donc réellement.

### Templates dédiés

Aucune bibliothèque de templates Document Libre n'est branchée dans l'interface active. Le moteur générique `DocumentTemplate` existe dans le projet, mais `create_document_libre` ne l'utilise pas dans le parcours actif audité.

Verdict : **fonctionnalité absente**, pas faux succès caché. Une bibliothèque de templates Libre serait une amélioration produit ultérieure, pas un prérequis de sécurité du P3 actuel.

## P3-H — dette sécurité permission d'émission

### Fait vérifié

`DOCUMENT_TYPE_PERMISSIONS` mappe encore :
- `libre -> patients` ;
- `lettre -> patients` ;
- `lettre_medicale -> patients` ;
- `document_libre -> patients`.

Les sous-comptes `SECRETAIRE` reçoivent `patients=True` par défaut, tandis que `clinical=False` par défaut. Un compte secrétaire standard peut donc actuellement atteindre la génération/archivage de Document Libre/Lettre dès lors qu'il accède au patient.

### Recommandation retenue

Remapper ces quatre types vers la permission **`clinical`** :
- fail-closed par défaut pour une secrétaire ;
- actif par défaut pour un dentiste ;
- toujours configurable explicitement par le praticien pour un collaborateur auquel il souhaite déléguer ce droit.

### État

**OUVERT / BLOQUANT DE CLOSEOUT P3.**

Le connecteur GitHub utilisé ici ne propose pas de micro-patch serveur et `backend/routers/documents.py` est suffisamment volumineux pour qu'une réécriture intégrale, uniquement pour quatre valeurs, soit un risque de régression disproportionné. Aucun faux correctif n'est revendiqué.

## Audit médico-documentaire Certificat

Source officielle consultée : Secrétariat Général du Gouvernement, décret n° 2-96-989 du 5 janvier 1999 rendant applicable le code de déontologie des médecins-dentistes.

Points retenus :
- art. 9 : certificat de complaisance interdit ;
- art. 23 : certificat conforme aux constatations du médecin-dentiste, signature manuscrite obligatoire, substitution interdite ;
- art. 24 : actes conformes aux données acquises de la science.

Conséquence de conception P3 : le logiciel ne doit pas inventer un fait clinique/documentaire, décider automatiquement d'une durée ni remplacer la signature du praticien.

Ce rapport est un audit logiciel/médico-documentaire ; il ne constitue pas une certification réglementaire ou un avis juridique indépendant.

## CI — limite de preuve

Sur les lots Document Libre récents :
- #64 run `31914469209` : 3 jobs failure avant steps ;
- #65 run `31914543653` : 3 jobs failure avant steps ;
- #66 run `31914693644` : 3 jobs failure avant steps ;
- #67 run préparatoire `31914866255` : 3 jobs failure avant steps avant réalignement final de la branche.

Ces échecs n'attestent aucun échec applicatif : les jobs n'ont pas exécuté leurs étapes. Ils ne constituent pas non plus une validation.

## Verdict UX statique P3

### Certificat

Architecture désormais cohérente et fail-closed : choix explicites, absence d'automatisme clinique prescriptif, validation praticien, PDF et signature mieux alignés sur le document réel.

### Document Libre

Points forts :
- édition libre simple ;
- toolbar et tableaux ;
- format/alignement ;
- preview ;
- archive/réouverture ;
- impression finale fraîche ;
- protection contre perte de brouillon ;
- PDF long lisible.

Limite UX non bloquante : la toolbar insère encore du markup visible (`<b>`, `<i>`, etc.) dans le textarea. C'est fonctionnel mais pas un éditeur WYSIWYG premium. À traiter comme amélioration P7, pas comme défaut de sécurité P3.

## Restant avant certification finale P3

1. Corriger **P3-H** : `libre/lettre/... -> clinical` + tests RBAC ciblés.
2. Exécuter une régression réelle sur le `master` final : frontend + backend + PDF.
3. Runtime authentifié des trois parcours Certificat.
4. Runtime authentifié Document Libre : saisie, toolbar, tableau, A4/A5, alignement, preview, archive, réouverture, abandon protégé, impression.
5. Inspection visuelle des PDF finaux, notamment multi-page Libre et signature Certificat.
6. Mettre à jour ROADMAP/STATUS/CHANGELOG au closeout final uniquement après ces preuves.

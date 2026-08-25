# M4-C — Document contextuel — Goal verrouillé

Baseline produit : `cb66d2f379803220d1a81f307db803737a167c94`
BEFORE : run `32829274229`, artifact `9556142341`, 7/7 captures.

## Goal

Depuis un `DocumentArchive` canonique précis dans la bibliothèque desktop, générer un pont QR opaque qui ouvre exactement ce document sur le mobile appairé, sans exposer d’identifiant patient, d’identifiant document, de nom de fichier ou de chemin média dans le QR ou l’URL mobile.

## Succès observable

1. Le bridge ne s’affiche que pour les documents canoniques actifs (`DocumentArchive`).
2. Les documents `legacy:*` sont explicitement marqués `Ancien format · desktop uniquement` et ne proposent ni bridge mobile, ni corbeille, ni édition structurée impossible.
3. La permission est dérivée du type réel du document et revalidée à l’émission, au ciblage utilisateur, à la résolution et au chargement média :
   - ordonnance → prescriptions ;
   - rapport cephalo → cephalo ;
   - devis / honoraires / note / échéancier → accounting ;
   - libre / lettre → clinical ;
   - certificat / photo / radiographie / autre → patients.
4. Patient, cabinet/tenant, document ACTIF, appareil et utilisateur cible sont revalidés côté serveur.
5. QR : seul le token opaque temporaire est transporté vers `/mobile/onboarding`.
6. Mobile final : `/mobile/context` sans ID ni query.
7. Le mobile affiche patient, type, nom/titre utile, date et document exact ; le binaire est chargé par POST authentifié avec `context_key` puis Blob URL.
8. Un document en corbeille, supprimé, fichier manquant, permission retirée ou appareil différent échoue explicitement, sans fallback Agenda silencieux.
9. Les actions touchées sur la bibliothèque font au moins 44×44 px.
10. La corbeille/restauration/suppression définitive des documents canoniques appliquent la même permission typée que leur lecture/téléchargement.
11. 0 overflow horizontal et 0 erreur runtime inattendue sur 390 / 430 / 768 / 1280.
12. M4-A Patient et M4-B Panoramique restent verts.

## Décision legacy

M4-C ne migre pas les documents `legacy:*` à la volée. Le bridge serveur actuel transporte un `resource_id` canonique entier et le backend refuse déjà explicitement la corbeille legacy. Ajouter une migration documentaire implicite dans un flow QR serait un changement de modèle métier non réversible et hors scope.

Le legacy reste consultable/téléchargeable sur desktop avec son chemin sécurisé existant, mais est présenté honnêtement comme non portable dans ce lot.

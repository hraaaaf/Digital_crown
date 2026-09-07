# DIGITAL CROWN — MOB-5F — PATIENTS / QUICK DOCUMENT STUDIO — AUDIT

Status: CLOSED — MERGED — POST-MERGE GREEN

## Goal

Permettre de produire un document courant depuis le cockpit patient mobile, idéalement en moins de 30 secondes, sans dupliquer le moteur Document Studio desktop ni affaiblir les contrôles patient/RBAC.

## Baseline produit

- product baseline: `e30b858f58686f5f7bef19ca93f1c5dae42929c9`
- branche lot: `ux/mobile-documents-mob5f`
- route de preuve: `/mobile/demo?demo=1&tab=patients`
- viewports: 390x844, 430x932, 768x1024

## BEFORE verrouillé

Run: `34143420251` — SUCCESS
Artifact: `10026785108`
Digest: `sha256:b827b8b31f7bb604667d1a8df624eda98b1aa794ac25145f8c7acec72af5bdff`
HEAD capture: `f70498efc7d7f9b56c85bde5be6c3194ec2b3bf6`
Baseline produit prouvée: `e30b858f58686f5f7bef19ca93f1c5dae42929c9`

Constat:
- cockpit patient fonctionnel;
- Photo clinique / Scanner / Dernier document / Dernière pano présents;
- aucune entrée `Créer un document`;
- HTTP 200 aux trois viewports;
- 0 page error;
- 0 console error;
- 0 overflow horizontal.

## État interne vérifié

### Cockpit patient mobile

`backend/routers/mobile_patient_cockpit.py` garde le patient et ses ressources tenant-scoped et permission-gated.

Capacités existantes conservées:
- recherche patient;
- identité / dossier / assurance / alerte médicale;
- prochain rendez-vous;
- snapshot financier si permission;
- ressources documentaires et panoramiques existantes;
- contexte opaque device-bound pour ouvrir `patient`, `document` ou `panoramic`.

MOB-5F ajoute uniquement l'entrée documentaire et enrichit l'endpoint chiffré `/api/mobile/quick-actions/capabilities` avec les permissions documentaires exactes.

### Moteur documentaire canonique

Source de vérité: `POST /api/documents/generate`.

Types backend disponibles:
- ordonnance;
- certificat;
- devis;
- note / honoraires;
- libre / lettre;
- échéancier.

MOB-5F réutilise directement ce moteur. Aucun second générateur, aucun modèle DB parallèle, aucun stockage mobile documentaire.

Contrôles conservés:
- permission backend par type;
- accès patient tenant-scoped;
- validation Pydantic spécialisée (`OrdonnanceData`, `CertificatData`, `DevisData`, `HonorairesData`, `LibreData`);
- preview serveur;
- archivage canonique;
- détection de doublon / cohérence / règles financières existantes.

### Auth mobile

`backend/routers/auth.py:get_current_user` accepte les JWT `type=mobile` via `_decode_mobile_identity`, puis `require_permission` reste l'autorité. Aucun adapter d'auth ni bypass RBAC n'a été ajouté.

## Périmètre MOB-5F implémenté

Depuis un CTA unique `Créer un document` dans le cockpit patient:
1. Ordonnance
2. Certificat
3. Devis
4. Honoraires
5. Document libre

Échéancier n'est pas porté dans le Quick Document Studio: il reste un flux financier dédié et ne doit pas être compressé artificiellement dans ce lot.

Consentement / consignes postop / courrier-orientation ne sont pas inventés comme nouveaux types médico-légaux. Le courrier simple peut utiliser `Document libre`; les modèles dédiés restent à traiter lorsque leur source canonique existe.

## RBAC UI + serveur

Le serveur expose désormais, dans l'enveloppe mobile chiffrée existante:
- `can_create_prescription` → `prescriptions`;
- `can_create_certificate` → `patients`;
- `can_create_devis` → `accounting`;
- `can_create_honoraires` → `accounting`;
- `can_create_free_document` → `clinical`.

Ces valeurs reflètent `DOCUMENT_TYPE_PERMISSIONS` du router canonique. Le sheet filtre les familles avec ces booléens et échoue fermé si les capacités ne peuvent pas être chargées. Le backend revérifie encore la permission lors de `/documents/generate`.

Le contrat historique `can_pay` a été restauré à son comportement combiné `['accounting', 'payments']` après détection par la CI PR. Le test backend verrouille désormais les neuf capacités du Quick Action Hub.

## Contrat preview / archivage

Le mobile ne passe plus directement à l'archive:
1. formulaire;
2. `preview=true&archive=false`;
3. contenu/payload verrouillé pour confirmation;
4. `Archiver le document` explicite;
5. `archive=true&preview=false` avec le même payload validé.

La preview démo est locale et ne contacte jamais le cabinet.

## Alerte médicale Ordonnance

Le composant recharge en lecture seule le cockpit du patient en vraie session et réaffiche `medical_alert_summary` dans l'éditeur Ordonnance lorsqu'une alerte existe. En preview isolée, cette donnée peut être injectée sans aucun appel réseau; un test dédié verrouille ce comportement.

## Validation croisée des payloads

Comparaison effectuée contre `backend/schemas/documents.py`:
- `DocumentRequest` autorise les cinq familles utilisées;
- devis: `teeth_data` est une liste et `prix_unitaire` est borné 0..1 000 000;
- honoraires: `montant` est strictement positif et ≤ 1 000 000;
- certificat: durée d'arrêt 1..365 et contenu requis pour certificat médical;
- libre: alias `title/content` acceptés;
- ordonnance: structure `medications` canonique.

Trois écarts détectés pendant l'audit ont été corrigés avant certification finale: `teeth_data={}`, montant Honoraires à 0 et capacité Honoraires initialement reliée à `payments` au lieu du guard canonique `accounting`.

## AFTER certifié

- product HEAD: `91688ffc2d5bf97e584844f972a12df717fc74da`
- run: `34149391346` — SUCCESS
- artifact: `10028850934`
- digest: `sha256:8b27d1c8658d0472f663a152d14bf463cfd519a7ac6ca5d65e4af7811c94080e`
- 390x844 / 430x932 / 768x1024
- 0 overflow horizontal
- 0 page error
- 0 console error
- 0 requête API réelle en preview
- 5 familles visibles
- flow Certificat prouvé jusqu'à `Aperçu prêt` puis `Archiver le document`
- score visuel: **9.1/10**

Réserve visuelle connue: à 390 px, la navigation fixe mord légèrement la zone d'actions initiale avant scroll; le sheet et la confirmation restent propres.

## PR / merge / post-merge

- PR `#365` merged
- HEAD final PR `d39c9a207f1bc8b54333a332d7b6ea44a5ef9c58`
- CI PR `34152892582` — SUCCESS
- T2 `34152892437` — SUCCESS
- Patient P7 `34152892745` — SUCCESS
- certs mobiles MOB-5A/B/C/D/E — SUCCESS
- merge exact `d9d1c255be6c9878ce6b7127c7f723cfb61e38a0`
- CI post-merge master `34163696668` — SUCCESS
- backend `Tests & durcissement` — SUCCESS
- frontend tests + build — SUCCESS
- garde production — SUCCESS

## Success

Tous les critères de fermeture sont maintenant prouvés:
- CTA `Créer un document` visible depuis le patient;
- familles filtrées par permissions exactes;
- 5 familles utilisent le moteur canonique;
- preview puis confirmation d'archive explicites;
- tests ciblés + build verts;
- AFTER 390/430/768 sans overflow, page error, console error ni requête API réelle en preview;
- flow Certificat prouvé jusqu'à `Archiver le document`;
- inspection BEFORE/AFTER + score visuel documentés;
- PR + merge exact + post-merge CI verts;
- aucun Vercel.

MOB-5F est CLOSED.

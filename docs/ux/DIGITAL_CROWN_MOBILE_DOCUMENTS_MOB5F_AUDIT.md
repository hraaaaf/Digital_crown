# DIGITAL CROWN — MOB-5F — PATIENTS / QUICK DOCUMENT STUDIO — AUDIT

Status: AUDIT LOCKED — BEFORE PENDING — IMPLEMENTATION NOT STARTED

## Goal

Permettre de produire un document courant depuis le cockpit patient mobile, idéalement en moins de 30 secondes, sans dupliquer le moteur Document Studio desktop ni affaiblir les contrôles patient/RBAC.

## Baseline produit

- product baseline: `e30b858f58686f5f7bef19ca93f1c5dae42929c9`
- branche lot: `ux/mobile-documents-mob5f`
- route de preuve prévue: `/mobile/demo?demo=1&tab=patients`
- viewports: 390x844, 430x932, 768x1024

## État interne vérifié

### Cockpit patient mobile

`backend/routers/mobile_patient_cockpit.py` est actuellement explicitement read-only.

Capacités existantes:
- recherche patient;
- identité / dossier / assurance / alerte médicale;
- prochain rendez-vous;
- snapshot financier si permission;
- ressources documentaires et panoramiques existantes;
- création d'un contexte opaque device-bound pour ouvrir `patient`, `document` ou `panoramic`.

Le mobile sait donc retrouver le patient et ouvrir une ressource existante. Il ne propose pas de création de document.

### UI patient mobile

`MobilePatientsView.tsx` expose aujourd'hui:
- Photo clinique;
- Scanner;
- Dernier document;
- Dernière pano.

Gap exact: aucune entrée `Créer un document` depuis le patient sélectionné.

### Moteur documentaire canonique

`POST /documents/generate` est la source de vérité existante.

Types supportés par le moteur:
- ordonnance;
- certificat;
- devis;
- note / honoraires;
- libre / lettre;
- échéancier.

Contrôles déjà présents:
- permission par type (`prescriptions`, `patients`, `accounting`, `clinical`);
- `assert_patient_access`;
- validation payload côté frontend;
- preview;
- archivage;
- détection de doublons avec résolution explicite;
- cohérence clinique déterministe;
- règles comptables spécifiques pour documents financiers.

Décision d'architecture: MOB-5F réutilise ces contrats. Aucun second moteur de génération documentaire mobile.

### Frontend Document Studio existant

Le desktop possède déjà les briques certifiées ou testées pour:
- Ordonnance;
- Certificat;
- Devis;
- Note Honoraires;
- Échéancier;
- Document Libre;
- traitement des états dirty;
- patient boundary;
- preview / archivage / impression.

`patientDocumentBoundary.ts` réinitialise les brouillons lors d'un changement de patient. Cette propriété de sécurité doit être conservée dans tout flux mobile.

## Benchmark externe retenu

Le benchmark produit converge sur une action documentaire directement disponible depuis le contexte patient:
- CareStack: quick links patient pour prescription/form/letter;
- Open Dental / ODTouch: actions cliniques et prescriptions depuis le patient sélectionné.

Principe retenu: entrée unique et évidente dans le cockpit patient, puis flow mobile compact. Pas de copie du hub desktop à sept onglets.

## Périmètre recommandé V1 MOB-5F

Priorité au flux courant et <30 s:
1. Ordonnance
2. Certificat
3. Document libre
4. Devis

Les flux Honoraires / Échéancier restent accessibles via les fonctions financières existantes mais ne sont pas inclus d'office dans le Quick Document V1 tant que leur UX mobile spécifique n'est pas auditée. Cette exclusion ne supprime aucune capacité desktop.

## Invariants

- patient préselectionné et non ambigu;
- alerte médicale visible avant une ordonnance;
- permissions backend restent autoritaires;
- aucune donnée patient dans une URL de bridge;
- aucun brouillon ne traverse un changement de patient;
- preview avant archivage pour les documents sensibles;
- archivage via le moteur canonique;
- preview demo totalement isolée du réseau cabinet;
- aucune régression sur les actions patient existantes.

## Success

Le lot est réussi seulement si:
- `Créer un document` est atteignable depuis un patient sélectionné;
- les types autorisés sont filtrés selon les permissions;
- au moins Ordonnance / Certificat / Libre / Devis utilisent le moteur canonique;
- preview puis archivage sont explicites;
- le patient reste verrouillé pendant le draft;
- tests RBAC / patient boundary / payload / erreurs passent;
- AFTER 390/430/768 sans overflow, page error ni console error;
- comparaison BEFORE/AFTER documentée;
- score visuel documenté;
- CI PR puis post-merge vertes.

## Preuve attendue

- artifact BEFORE sur baseline `e30b858f...`;
- tests frontend ciblés;
- tests backend ciblés si un adapter mobile est ajouté;
- build frontend;
- artifact AFTER 390/430/768;
- report de capacités / overflow / erreurs;
- PR + CI + merge exact + post-merge CI.

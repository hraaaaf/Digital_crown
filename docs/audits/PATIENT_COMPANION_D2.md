# PATIENT COMPANION D2 — STAFF OPERABILITY

Status: PRE-MERGE CERTIFIED

## Goal
Rendre les capacités d'administration Patient Companion D0 réellement opérables depuis la fiche patient du cabinet, sans nouveau moteur métier ni nouvelle source de vérité.

## Success
Depuis `/patients/:id`, le praticien principal peut :
1. voir l'état d'accès Companion du patient ;
2. créer ou réémettre une invitation ;
3. afficher temporairement le code/QR d'invitation avec expiration ;
4. partager/révoquer des Documents et Media déjà existants ;
5. révoquer complètement l'accès Companion.

Après reload, l'état durable est reconstruit depuis les modèles D0 existants. Aucun secret d'invitation n'est persisté en clair côté frontend.

## Certified pre-merge proof — 2026-09-16

Product validation HEAD: `5018fbbfd4144f1f8f7c19417458a8164762570c`.

- CI générale #4521: SUCCESS.
- Patient Companion D2 Visual #40: SUCCESS.
- UX Continuity PatientDetails #98: SUCCESS.
- T2 Runtime Browser #3393: SUCCESS.
- Cabinet Upgrade PostgreSQL #908: SUCCESS.
- P7 Final #1749: SUCCESS.
- P1 Architecture #117: SUCCESS.
- Media C4 #99: SUCCESS.
- Overlay #198: SUCCESS.
- Indicators #229: SUCCESS.
- Billing Visual #241: SUCCESS.
- AFTER inspecté aux viewports 390×844, 768×1024 et 1280×900.
- Artefact D2 #40: `patient-companion-d2-before-after-5018fbbfd4144f1f8f7c19417458a8164762570c`.
- Digest artefact: `sha256:d635b215a5832110e743cc07a34c75366b199bf944f11f5add7140cd228f20fa`.
- Validation visuelle humaine: APPROUVÉE le 2026-09-16.
- BEFORE verrouillé sur `8f74464998a721414e67957e0c9346f6a67efdb2`.
- DB de certification isolée ; aucune DB cabinet touchée.
- Aucun déploiement Vercel.

Le commit documentaire de closeout qui porte ce fichier n'altère pas le code produit certifié ci-dessus. Depuis le merge CI #529, les grosses régressions backend génériques et PostgreSQL sont volontairement certifiées post-merge sur `master`; elles ne doivent plus être relancées à chaque commit de PR.

## Anti-dup audit — locked insertion point
Flux staff canonique vérifié :
`App.tsx -> /patients/:id -> frontend/src/features/patients/PatientDetails.tsx -> PatientDetailsInner.tsx`.

Insertion D2 : un onglet `Companion` dans `PatientDetailsInner.tsx`, visible uniquement à `ownerOrAdmin`.

Raisons :
- l'identité patient est déjà résolue ici ;
- le RBAC staff est déjà calculé ici ;
- `PatientDocuments`, `PatientMediaTimeline`, Agenda et les stores patients existants restent canoniques ;
- aucun store Companion global n'est nécessaire.

## Existing canonical surfaces reused
- Patient : `usePatientStore` + `/patients/:id` existants.
- Documents : `frontend/src/features/patients/PatientDocuments.tsx` et modèles/endpoints Document existants.
- Media : `PatientMediaTimeline` / Media Core existants.
- Agenda : surface Agenda existante ; D2 n'ajoute aucune mutation de rendez-vous patient.
- RBAC : `ownerOrAdmin` frontend + `require_companion_admin` backend D0.
- Notifications/push : moteur existant inchangé ; D2 ne crée aucun moteur d'envoi.
- QR : service QR existant du repo ; aucune nouvelle dépendance/service distant.

## Contract gap resolved
Le handover mentionnait un GET staff de statut/account, mais aucun endpoint D0 certifié ne permettait à l'UI staff de reconstruire l'état durable après reload.

Résolution minimale : projection READ-ONLY staff sur les modèles D0 existants. Elle ne crée aucune table, aucun dual-write et aucun nouveau moteur métier. Elle expose seulement les informations nécessaires à l'administration D2 et jamais le secret d'invitation hashé.

## Security invariants
- aucun secret d'invitation dans localStorage/sessionStorage ;
- secret visible uniquement dans l'état mémoire UI après création/réémission, jusqu'à expiration/changement patient/unmount ;
- aucun hash de secret renvoyé au frontend ;
- aucune ouverture/téléchargement brut de Document/Media côté patient ;
- aucune délégation employé/assistante sans scope RBAC séparé ;
- aucun remote gateway ;
- aucune modification directe de rendez-vous par le patient ;
- aucune nouvelle source Patient/Appointment/Document/Media ;
- aucune migration destructive ;
- aucune DB réelle touchée pendant le développement/tests.

## UI BEFORE / AFTER
BEFORE = fiche patient existante sans surface Companion.

AFTER = surface Companion intégrée à la fiche patient avec :
- état accès ;
- invitation/réémission ;
- QR + code + expiration éphémères ;
- Documents/Media canoniques avec partage/révocation ;
- révocation complète des accès Companion.

### Responsive result
- 390×844 : NBA non superposé, actions rapides masquées, shell compact, métriques Companion compactes, invitation remontée.
- 768×1024 : recouvrement corrigé en limitant le sticky du header à `lg`.
- 1280×900 : comportement desktop sticky conservé.

Le correctif responsive ne modifie aucun endpoint, modèle, RBAC, stockage ou moteur D0.

## Explicit exclusions preserved
- nouveau moteur métier Companion ;
- nouveau store persistant frontend ;
- nouveau moteur notification/messagerie ;
- appointment write patient ;
- raw document/media patient access ;
- employee delegation ;
- remote gateway ;
- Vercel/deployment sans autorisation explicite.

## Current integration state
Branch: `feat/patient-companion-d2-staff-ui`.
PR: #523.
Product validation HEAD: `5018fbbfd4144f1f8f7c19417458a8164762570c`.
Master rechecked after CI policy merge #529: `8a37913c23f182a8de4e0f1dd0e2049e48b7267f`.
The D2 branch is currently diverged from master; mergeability must be restored/rechecked before merge.

## Remaining gates
1. Reconcile D2 with current master without altering the certified D2 product behavior.
2. Recheck PR mergeability and exact diff.
3. Merge only after explicit user authorization.
4. Post-merge: verify the single heavy backend regression + PostgreSQL/cabinet certification on the D2 merge commit, then mark D2 CLOSED.

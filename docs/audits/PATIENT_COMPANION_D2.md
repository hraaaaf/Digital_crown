# PATIENT COMPANION D2 — STAFF OPERABILITY

Status: IN PROGRESS

## Goal
Rendre les capacités d'administration Patient Companion D0 réellement opérables depuis la fiche patient du cabinet, sans nouveau moteur métier ni nouvelle source de vérité.

## Success
Depuis `/patients/:id`, le praticien principal peut :
1. voir l'état d'accès Companion du patient ;
2. créer ou réémettre une invitation ;
3. afficher temporairement le code/QR d'invitation avec expiration ;
4. partager/révoquer des Documents et Media déjà existants ;
5. révoquer complètement l'accès Companion.

Après reload, l'état durable doit être reconstruit depuis les modèles D0 existants. Aucun secret d'invitation ne doit être persisté en clair côté frontend.

## Proof required before CLOSED
- tests backend fonctionnels + RBAC + sécurité ;
- tests frontend ciblés ;
- non-régression DB/patients/documents/media/auth ;
- BEFORE et AFTER sur les mêmes viewports ;
- comparaison visuelle + score ;
- CI sur HEAD exact ;
- validation humaine du HEAD exact ;
- merge uniquement après autorisation explicite ;
- post-merge CI + cohérence roadmap/canonique.

## Anti-dup audit — locked insertion point
Flux staff canonique vérifié :
`App.tsx -> /patients/:id -> frontend/src/features/patients/PatientDetails.tsx -> PatientDetailsInner.tsx`.

Insertion D2 : un onglet `Companion` dans `PatientDetailsInner.tsx`, visible uniquement à `ownerOrAdmin`.

Raisons :
- l'identité patient est déjà résolue ici ;
- le RBAC staff est déjà calculé ici ;
- `PatientDocuments`, `PatientMediaTimeline`, Agenda et les stores patients existants restent canoniques ;
- aucun store Companion global n'est nécessaire.

## Existing canonical surfaces to reuse
- Patient : `usePatientStore` + `/patients/:id` existants.
- Documents : `frontend/src/features/patients/PatientDocuments.tsx` et modèles/endpoints Document existants.
- Media : `PatientMediaTimeline` / Media Core existants.
- Agenda : surface Agenda existante ; D2 n'ajoute aucune mutation de rendez-vous patient.
- RBAC : `ownerOrAdmin` frontend + `require_companion_admin` backend D0.
- Notifications/push : moteur existant inchangé ; D2 ne crée aucun moteur d'envoi.
- QR : réutiliser le service QR déjà présent dans le repo ; aucune nouvelle dépendance/service distant.

## Contract gap discovered before implementation
Le handover mentionnait un GET staff de statut/account, mais aucun endpoint D0 certifié ne permet actuellement à l'UI staff de reconstruire l'état durable après reload.

Décision minimale : ajouter une projection READ-ONLY staff sur les modèles D0 existants. Elle ne crée aucune table, aucun dual-write et aucun nouveau moteur métier. Elle expose seulement les informations nécessaires à l'administration D2 et jamais le secret d'invitation hashé.

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

## UI target / BEFORE contract
BEFORE = fiche patient actuelle, onglets existants `Suivi / Clinique / Radiologie / Documents / Archives / Finances` selon permissions, sans surface Companion.

Target = ajouter `Companion` comme surface d'administration cohérente avec la fiche patient :
- carte état accès ;
- action invitation/réémission ;
- panneau éphémère QR + code + expiration ;
- listes compactes Documents/Media existants avec état partagé et action partager/révoquer ;
- zone danger pour révocation complète.

Le target ne doit pas introduire une navigation parallèle, un dashboard global Companion ou une nouvelle identité visuelle.

## Explicit exclusions
- nouveau moteur métier Companion ;
- nouveau store persistant frontend ;
- nouveau moteur notification/messagerie ;
- appointment write patient ;
- raw document/media patient access ;
- employee delegation ;
- remote gateway ;
- Vercel/deployment sans autorisation explicite.

## Current implementation branch
`feat/patient-companion-d2-staff-ui`

Base de création vérifiée : `8f74464998a721414e67957e0c9346f6a67efdb2`.

Ne jamais considérer ce SHA comme master courant sans re-vérification.

# PATIENT COMPANION D2 — STAFF OPERABILITY

Status: **CLOSED — merged and post-merge certified**

Repository: `hraaaaf/Digital_crown`
PR: `#523` — MERGED
Certified PR head: `206f58e6571c6fdfa2af8e726ce032d694928799`
Merge commit: `6cc0c41fd64d40ef8929bebe11c67ecc4fc42672`
Post-merge CI: `#4574` / run `35100604875` — **SUCCESS**
Post-merge PostgreSQL: `#917` / run `35100604888` — **SUCCESS**

## Goal

Rendre les capacités d'administration Patient Companion D0 réellement opérables depuis la fiche patient du cabinet, sans nouveau moteur métier ni nouvelle source de vérité.

## Success

Depuis `/patients/:id`, le praticien principal/admin peut :
1. voir l'état d'accès Companion du patient ;
2. créer ou réémettre une invitation ;
3. afficher temporairement le code/QR d'invitation avec expiration ;
4. partager/révoquer des Documents et Media déjà existants ;
5. révoquer complètement l'accès Companion.

Après reload, l'état durable est reconstruit depuis les modèles D0 existants. Aucun secret d'invitation n'est persisté en clair côté frontend.

## Implemented scope

- onglet `Companion` intégré dans `PatientDetailsInner.tsx` ;
- accès UI limité au rôle `ownerOrAdmin` ;
- projection staff read-only de l'état Companion depuis les modèles D0 existants ;
- invitation/réémission avec secret éphémère mémoire-only ;
- QR/code temporaire + expiration ;
- partage/révocation de Documents et Media canoniques ;
- révocation complète des accès Companion ;
- aucun nouveau store métier persistant ;
- aucune nouvelle source Patient/Appointment/Document/Media ;
- aucune migration DB destructive ;
- aucune DB cabinet réelle touchée pendant développement/certification ;
- aucun déploiement Vercel.

## Canonical insertion point / anti-dup audit

Flux staff canonique vérifié :
`App.tsx -> /patients/:id -> frontend/src/features/patients/PatientDetails.tsx -> PatientDetailsInner.tsx`.

Insertion D2 : un onglet `Companion` dans `PatientDetailsInner.tsx`, visible uniquement à `ownerOrAdmin`.

Raisons :
- identité patient déjà résolue ici ;
- RBAC staff déjà calculé ici ;
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

Le handover initial mentionnait un GET staff de statut/account, mais aucun endpoint D0 certifié ne permettait à l'UI staff de reconstruire l'état durable après reload.

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

## Pre-merge final certification

Exact PR head: `206f58e6571c6fdfa2af8e726ce032d694928799`.

Final targeted evidence on this exact head:
- Patient Companion D2 Visual `#51` — **SUCCESS** ;
- targeted backend `backend/tests/test_patient_companion_d2_staff.py` executed successfully inside D2 visual gate ;
- Media C4 Visual `#105` — **SUCCESS** ;
- CI `#4561` — **SUCCESS** ;
- UX Continuity PatientDetails `#104` — **SUCCESS** ;
- Patient Billing Visual `#247` — **SUCCESS** ;
- Patient Indicators Truth `#235` — **SUCCESS** ;
- T2 Runtime Browser `#3428` — **SUCCESS** ;
- Patient UX1-C Overlay `#204` — **SUCCESS** ;
- Patient P1 Architecture `#123` — **SUCCESS** ;
- Patient P7 Final `#1755` — **SUCCESS** ;
- PR Merge Summary `#29` — **SUCCESS** ;
- M6-I Biometric Passkey skipped as expected.

D2 visual artifact:
- name: `patient-companion-d2-before-after-206f58e6571c6fdfa2af8e726ce032d694928799` ;
- artifact id: `10445102246` ;
- digest: `sha256:364f886ec8c7f998f0137a63d12ed4514a7661cf18584f49c9e88fce3784b011` ;
- BEFORE/AFTER captured at 390×844, 768×1024 and 1280×900.

Historical product proof retained from `5018fbbfd4144f1f8f7c19417458a8164762570c` remains useful as visual/product reference, but closure is based on the exact final PR head and post-merge evidence above/below.

## Merge proof

PR `#523 — Patient Companion D2 — staff operability` was merged after explicit owner authorization.

- PR head at merge: `206f58e6571c6fdfa2af8e726ce032d694928799` ;
- merge commit: `6cc0c41fd64d40ef8929bebe11c67ecc4fc42672` ;
- merge commit has parents `2c36a04d90933d70fe8d501f44b9f8e04f7acca0` and D2 PR head `206f58e6571c6fdfa2af8e726ce032d694928799` ;
- GitHub commit signature verified ;
- no Vercel deployment performed.

## Post-merge proof

Exact merge SHA certified: `6cc0c41fd64d40ef8929bebe11c67ecc4fc42672`.

### CI #4574 / run 35100604875 — SUCCESS

Observed successful jobs include:
- `Full backend regression (post-merge)` — SUCCESS ;
- `Full backend regression suite (DB / patients / documents included)` step — SUCCESS ;
- `Frontend (tests & build)` — SUCCESS ;
- frontend `Test suite` — SUCCESS ;
- frontend `Build` — SUCCESS ;
- `Garde production (négatif)` — SUCCESS.

The M4 contextual bridge jobs skipped by workflow conditions are not D2 failures.

### Cabinet Upgrade PostgreSQL #917 / run 35100604888 — SUCCESS

Observed successful jobs include:
- `PostgreSQL 18 + immutable release invariants` — SUCCESS ;
- `Run cabinet preservation and release-policy gates on PostgreSQL 18` — SUCCESS ;
- `Windows PowerShell 5.1 release guards` — SUCCESS ;
- `Preserve Windows PowerShell 5.1 API compatibility` — SUCCESS.

## Explicit exclusions preserved

- nouveau moteur métier Companion ;
- nouveau store persistant frontend ;
- nouveau moteur notification/messagerie ;
- appointment write patient ;
- raw document/media patient access ;
- employee delegation ;
- remote gateway ;
- Vercel/deployment sans autorisation explicite.

## Closure decision

**D2 = CLOSED.**

Closure basis:
- scope borné implémenté ;
- D0/D1 security and canonical-data boundaries preserved ;
- targeted exact-head D2 and Media certification green ;
- UI responsive evidence present ;
- PR merged after explicit owner authorization ;
- full post-merge backend regression green on exact merge SHA ;
- frontend tests/build green on exact merge SHA ;
- production negative guard green ;
- PostgreSQL 18 cabinet preservation/release-policy certification green ;
- no real cabinet DB touched by development/certification ;
- no Vercel deployment.

## Next exact

There is **no canonical Patient Companion D3 defined in the repository at D2 closeout**.

The competitive roadmap still names the remaining Patient Companion continuation `D1+ — useful patient workflows beyond the minimum shell`, followed by Lot E `Connect Hub`.

Before any new Patient Companion implementation:
1. read `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md` plus D0/D1/D2 canonicals ;
2. re-check current master / open PRs / exact-head CI ;
3. bound the next patient workflow scope and anti-duplication contract ;
4. do not invent a D3 label unless the roadmap is explicitly revised to create one.

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

## Mobile simplification target — locked before implementation

### BEFORE observed at 390×844
La certification visuelle du HEAD `1f0e419b7821ce8cd2407f206bcb1a1ed473a428` est techniquement verte mais l'écran réel est trop dense : toast NBA global superposé, actions rapides redondantes, barre d'onglets longue, métriques Companion empilées verticalement et trop de hauteur consommée avant l'action d'invitation.

### Goal mobile
À 390×844, comprendre l'état Companion et atteindre l'action d'invitation sans combattre l'interface, tout en gardant intactes les capacités métier et le rendu tablette/desktop.

### Reference / wireframe
```text
[←] NOM PATIENT                 [assurance]
    dossier · âge               [alerte si utile]

[Suivi] [Clinique] [Image] [Docs] [Companion] [Finance]  ← barre compacte scrollable

Patient Companion                     [↻]
[Actifs 0] [Invitation attente] [Partages 0]             ← 3 métriques compactes

Invitation
[email________________________________]
[lien________] [15 min________]
[        CRÉER / RÉÉMETTRE L'INVITATION        ]

QR/code si généré

Documents / Médias / Révocation plus bas
```

### Implementation constraints
- masquer sur mobile la rangée d'actions rapides redondantes, sans supprimer leurs routes/fonctions ;
- ne pas afficher le toast NBA contextuel sur l'onglet Companion ;
- compacter uniquement la présentation mobile du shell patient et du résumé Companion ;
- aucune modification des endpoints, du RBAC, du stockage, des modèles ou des règles D0 ;
- conserver tablette/desktop fonctionnellement et visuellement stables ;
- AFTER obligatoire aux mêmes viewports 390×844, 768×1024, 1280×900.

### Success observable
- aucune superposition de toast NBA sur Companion ;
- header mobile plus court ;
- actions rapides non redondantes absentes à 390 px ;
- 3 métriques visibles sur une seule rangée mobile ;
- invitation atteignable plus haut dans le premier écran ;
- aucune régression tests/build/certifications.

## Responsive validation checkpoint — 2026-09-16

- Le correctif mobile est limité à la présentation de `PatientDetails`/Companion ; aucun endpoint, modèle, RBAC, stockage ou moteur D0 n'est modifié.
- Le header patient n'est plus sticky sous le breakpoint `sm`, afin d'éviter le recouvrement observé à 390×844.
- Les actions rapides restent disponibles à partir de `sm` et sont masquées sur mobile étroit.
- Les onglets gardent un seul libellé DOM canonique et utilisent un libellé visuel compact sur mobile, afin de préserver l'accessibilité et les probes navigateur sans dupliquer le texte.
- Le commit produit `e3a8c8544bcdfc1e3ba15fbfa48c013922bbd472` contient le correctif single-node des onglets. Les runs PR déclenchés directement par ce commit bot ont été classés `action_required` par GitHub ; ce statut ne constitue pas une validation produit.
- Le présent commit documentaire sert de nouveau HEAD humain pour relancer les certifications exactes sur le même contenu produit.
- Statut maintenu `IN PROGRESS` tant que CI exacte, preuves AFTER finales, audit visuel et validation humaine ne sont pas acquis.

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

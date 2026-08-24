# Mobile M6.2 — Offline Truth — CLOSEOUT

Date: 2026-08-24
Status: CLOSED

## Goal

Établir une seule vérité offline pour l’expérience mobile : un seul Service Worker, une seule queue applicative liée au cabinet et au device, aucun succès de mutation sans confirmation HTTP, et un refresh mobile device-bound cohérent.

## Résultat livré

- Workbox `pwa-sw.js` est l’unique Service Worker applicatif ; zéro cache API dans le SW.
- `frontend/public/sw.js` supprimé.
- Migration des installations existantes : ancien `/sw.js` désinscrit, cache `dc-mobile-v10` supprimé, IndexedDB `sync-db` supprimée, reload unique si l’ancien SW contrôle encore la page.
- Queue applicative unique `zka_action_queue_v2`, scoped `cabinetPublicId + deviceId` ; l’ancienne queue n’est jamais rejouée.
- Changement cabinet/device : snapshot et queue purgés.
- HTTP 4xx/5xx = erreur réelle ; queue uniquement sur panne réseau/Abort/Timeout.
- Replay : action retirée seulement après `response.ok`.
- Status et DELETE utilisent un action ID stable via `X-Mobile-Action-Id`.
- DELETE mobile tenant-scoped et idempotent pour le replay après réponse perdue.
- Déplacement RDV non canonique non mis en queue avant M6.3.
- 401 mobile : refresh par `/api/mobile/refresh-token`, jamais par `/auth/refresh`.
- Refresh rejeté 401/403 : session locale effacée ; panne réseau ou HTTP 500 ne simule pas une révocation.
- Labo : statut `SENT` seulement après persistance backend réussie.
- IndexedDB reste le driver durable mobile obligatoire ; aucun fallback `localStorage` pour la clé maître ou les credentials durables.
- Initialisation IndexedDB rendue lazy pour éviter d’initialiser le stockage mobile au simple import de `api.ts` dans les contextes non mobiles/tests.

## Preuves exactes

- Branche produit : `mobile/m6-offline-truth`.
- PR : #231.
- Base : `7774cecf1b33650b5a302eff72e2a8c033438d4c`.
- HEAD produit certifié : `0c2ab389ba67672da5cd9aacb600f258afc5de70`.
- Intégrité avant merge : ahead 1 / behind 0, 1 commit, 13 chemins.
- CI exact-head finale : run `32722484488` — SUCCESS.
- Backend : **2778 passed, 8 skipped, 4 warnings, 0 failed**.
- Frontend : **107 fichiers de tests / 439 tests passés**, build SUCCESS.
- Garde production négative : SUCCESS.
- T2 Runtime Browser : run `32722484020` — SUCCESS.
- Patient P7 Final : run `32722483992` — SUCCESS.
- Catalog Connected Truth : run `32722484062` — SUCCESS.
- Merge master : `2695d214e88cf36c58325b39b7b7c02f19827830`.
- Aucun déploiement Vercel.

## Historique correctif

Le premier HEAD `b9d0941cc1781c5525226ff1231482a0d24f4447` n’a pas été accepté comme vert : backend, garde production, T2, P7 et Catalog étaient verts, et les 439 assertions frontend passaient, mais Vitest signalait 6 rejets non gérés `localforage: No available storage method found`.

Cause : `localforage.INDEXEDDB` était configuré au niveau module et devenait transitivement initialisé dans des tests non mobiles via `api.ts`.

Correction finale : configuration IndexedDB lazy, sans fallback `LOCALSTORAGE`, puis recertification complète au HEAD `0c2ab389...`.

Une revue supplémentaire a aussi détecté que supprimer `public/sw.js` ne supprimait pas les données déjà conservées par les anciens téléphones. La migration explicite `sync-db` + `dc-mobile-v10` + désinscription `/sw.js` a donc été ajoutée avant la certification finale.

## Limites / dettes connues

- `X-Mobile-Action-Id` n’est pas encore adossé à un registre générique de déduplication serveur. M6.2 ne revendique donc pas une idempotence universelle ; seules les opérations rejouables du lot ont été rendues sûres par leur sémantique (`status` par affectation, DELETE idempotent).
- Le déplacement RDV reste non canonique jusqu’à M6.3 et n’est volontairement pas mis en queue.
- Le contrat patient/RDV complet par ID, date de naissance, sexe explicite et duplicate handling reste M6.3.
- `npm audit` du frontend a signalé **20 vulnérabilités de dépendances** lors de la certification : 2 low, 2 moderate, 15 high, 1 critical. Elles constituent une dette de dépendances distincte ; M6.2 ne les corrige pas et ne les masque pas.
- Les warnings backend SQLAlchemy SuperAdmin existants restent non bloquants : 4 warnings, 0 échec.

## UI/UX

M6.2 ne modifie pas le layout ni la composition des écrans. Le gate visuel BEFORE/mockup/AFTER n’est donc pas applicable à ce lot.

## Next exact — M6.3 Patient/RDV canonique + Agenda UX

1. Captures BEFORE du vrai `AddApptModal` intégré à l’Agenda en 390/430/768.
2. Goal visuel + wireframe.
3. Patient identifié par `patient_id`, jamais par nom.
4. Création patient canonique avec date de naissance + sexe F/M explicite, sans valeur inventée.
5. Réutiliser le duplicate contract canonique `/api/patients/` et sélectionner `existing_patient.id` sur 409.
6. Création RDV par `/api/appointments/` et `patient_id`.
7. Enforcer `_find_conflicts` dans create/update ; update avec `exclude_id`.
8. Reschedule canonique via `PUT /api/appointments/{id}`.
9. Mobile patients : exclure soft-deleted ; legacy create fail-closed/délégation plutôt que données inventées.
10. AFTER 390/430/768, comparaison BEFORE/mockup/AFTER, tests et score visuel.

M6.2 est CLOSED sur les preuves ci-dessus. Aucun Vercel.

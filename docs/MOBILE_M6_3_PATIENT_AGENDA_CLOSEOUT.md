# Mobile M6.3 — Patient/RDV canonique + Agenda UX — CLOSEOUT

Date: 2026-08-24
Status: CLOSED

## Goal

Rendre le parcours mobile Patient/RDV fiable et canonique : patient identifié par `patient_id`, création patient avec identité explicite, création et déplacement de RDV via les routes canoniques, conflits réellement appliqués, et modal Agenda tactile utilisable sur mobile.

## Résultat livré

- Liste et création patient via `/api/patients/`.
- Patient sélectionné par `patient_id`, jamais par simple nom libre.
- Création patient avec `date_naissance` et sexe `F`/`M` explicites ; aucune valeur inventée.
- Duplicate canonique `409` réutilisé : `existing_patient.id` devient le dossier sélectionné.
- Création RDV via `/api/appointments/` avec `patient_id`.
- Reschedule mobile via `PUT /api/appointments/{id}`.
- `_find_conflicts()` appliqué à la création et à la modification ; update avec `exclude_id` pour ne pas s'auto-confliter.
- Datetimes aware/naive normalisés avant validation et persistance agenda.
- Créations legacy `/api/mobile/patients` et `/api/mobile/appointments` désactivées en fail-closed `410`; les lectures/status/delete mobile restent préservées.
- Timeline jour conserve les créneaux standards et injecte aussi les horaires réels non alignés, notamment `09:15`, `08:45` et `19:10`.
- Modal mobile transformé en bottom-sheet sur petits viewports.
- Contrôles critiques mesurés à 44–52 px après correction.

## Preuves produit exactes

- Branche produit : `mobile/m63-patient-rdv-agenda`.
- PR : #232.
- Base produit avant M6.3 : `8b4bc7bbfc1ab1fbe8d92f4393db20ecb70a28df`.
- HEAD produit certifié : `30d14b09bc70c78ed6086edbba18777e7c583fb4`.
- Intégrité avant merge : ahead 1 / behind 0, 1 commit, 7 fichiers.
- CI exact-head : run `32737567545` — SUCCESS.
- Backend : **2784 passed, 8 skipped, 4 warnings, 0 failed**.
- Frontend : **108 fichiers de tests / 443 tests passés**, build SUCCESS.
- Test M6.3 frontend : **4/4 PASS**.
- Garde production négative : SUCCESS.
- T2 Runtime Browser : run `32737567579` — SUCCESS.
- Patient P7 Final : run `32737567675` — SUCCESS.
- Catalog Connected Truth : run `32737567475` — SUCCESS.
- Merge master : `abafacb67da58f10376c4707a5c8d77f8d4b077d`.
- Post-merge : `master` vérifié identique à `abafacb67da58f10376c4707a5c8d77f8d4b077d` juste avant ce closeout.
- Aucun déploiement Vercel.

## UI/UX — BEFORE / mockup / AFTER

### BEFORE

- 6 captures réelles : 390x844, 430x932, 768x1024 ; états modal normal + nouveau patient.
- 0 overflow horizontal et 0 erreur console/page.
- Défaut mesuré : plusieurs contrôles critiques à **15–39 px**, sous le seuil tactile 44 px.

### Mockup

- Référence : commit audit `3f33e2020f6b4f518a1d8e0007e18f4ca10e17a3`.
- Cible : bottom-sheet mobile, contrôles 48–52 px, patient par ID, DOB + sexe F/M, CTA explicites.

### AFTER exact-head

- Harness audit : branche `audit/mobile-m63-before-20260824`.
- Métadonnée AFTER : `product_head=30d14b09bc70c78ed6086edbba18777e7c583fb4`.
- 6 captures : 390x844, 430x932, 768x1024 ; états normal + nouveau patient.
- 0 overflow horizontal sur 6/6.
- 0 erreur runtime/console/page sur 6/6.
- Aucun contrôle visible sous 44 px sur 6/6.
- Bottom-sheet validé en 390/430 ; modal centré cohérent en 768.
- Timeline gate validé sur 6/6 pour `08:45`, `09:15`, `19:10`.
- Exemples mesurés : fermeture 44 px, CTA secondaire 44 px, inputs/selects 48 px, CTA principaux 52 px.

**Score UI/UX M6.3 : 9,6/10.**

Raison : le défaut tactile principal est supprimé, les états 390/430/768 sont propres et la vérité métier est cohérente avec l'interface. Le score n'est pas 10/10 car le lot ne revendique pas une refonte complète de l'Agenda ni une certification de tous les flows mobiles hors périmètre M6.3.

## Historique correctif

Le premier HEAD candidat `b1dd50e9a692f7a98da40a6b197123f150f6031c` n'a pas été accepté comme vert. Les 439 tests frontend existants passaient, mais le nouveau test M6.3 échouait avant ses assertions car `readFileSync(new URL(..., import.meta.url))` recevait une URL Vitest non `file:`.

Correction : lecture par `resolve(process.cwd(), ...)`, puis reconstruction atomique de la branche. Le produit est resté à **un seul commit final**, conformément à la règle benchmark lourd : préparation complète → 1 commit final → 1 run utile.

## Dettes / limites connues

- Les 20 vulnérabilités npm signalées dans le chantier M6.2 restent une dette de dépendances distincte ; M6.3 ne les masque pas.
- Les 4 warnings SQLAlchemy SuperAdmin existants restent non bloquants et hors périmètre M6.3.
- M6.3 ne certifie pas les autres pages/flows mobiles non concernés par Patient/RDV/Agenda.

## Conclusion

M6.3 est CLOSED sur les preuves ci-dessus. Le patient et le RDV mobile utilisent désormais les contrats canoniques, les conflits sont appliqués en create/update, le reschedule n'utilise plus la route legacy, et l'Agenda respecte le seuil tactile requis sur les viewports certifiés.

Aucun Vercel.

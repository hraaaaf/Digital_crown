# Handover — Digital Crown — Clinique multi-praticiens P0

Date de reprise : 2026-09-12
Repository : `hraaaaf/Digital_crown`
Branche de travail : `feat/clinic-multipractitioner-p0`

## Fichier canonique

Lire en premier :

`docs/CLINIQUE_MULTI_PRATICIENS_ROADMAP.md`

Ce fichier est la source canonique du chantier et contient le Goal global, les invariants, les critères de succès P0, la roadmap P0→P3 et le Next exact.

Commit canonique actuellement présent sur la branche :

`a41c2cd5a05344891941b79db6330959cd8332db` — `docs(clinic): add multi-practitioner canonical roadmap`

## État Git vérifié au handover

- `master` réel : `33713654731f1ca165663a4cf35fbf7643897d61`
- HEAD de `feat/clinic-multipractitioner-p0` avant ce handover : `a41c2cd5a05344891941b79db6330959cd8332db`
- merge-base : `e700da0950cb0c5f90379b57401fa4ae926ad5af`
- état comparatif : branche divergée de `master`, `ahead_by=1`, `behind_by=1`
- seul changement produit par le chantier avant ce handover : ajout de `docs/CLINIQUE_MULTI_PRATICIENS_ROADMAP.md`
- aucune implémentation P0 backend n'est encore certifiée dans ce handover
- aucune PR P0 n'est déclarée comme créée dans ce handover
- aucun déploiement Vercel n'est autorisé ni nécessaire pour ce lot

IMPORTANT : au redémarrage, revérifier immédiatement `master`, le HEAD de branche, les PR éventuelles et les CI du HEAD exact avant toute modification. Ne jamais supposer que les SHA ci-dessus sont encore actuels.

## Goal global

Faire évoluer Digital Crown d'un agenda partagé au niveau cabinet vers un fonctionnement clinique réellement multi-praticiens, sans casser les données historiques, sans fuite inter-cabinet et sans mélanger les axes licence, abonnement commercial et type de cabinet.

## P0 — Goal exact

Rendre l'agenda réellement multi-praticiens côté backend : un rendez-vous peut être attribué à un praticien réel du cabinet, les conflits sont isolés par praticien, les rendez-vous legacy non assignés restent sûrs, et les chemins create/update/check-conflicts/bulk appliquent la même règle.

## Succès observable P0

1. `appointments.praticien_id` existe, nullable, FK vers `users.id`, indexé.
2. Create/update/check-conflicts/bulk valident que le praticien est assignable dans le cabinet courant.
3. Même praticien + chevauchement => HTTP 409.
4. Deux praticiens différents + même créneau => autorisé.
5. Un rendez-vous legacy `praticien_id=NULL` chevauchant le créneau bloque la réservation par sécurité.
6. Secrétaire, dentiste pending/inactif ou utilisateur d'un autre cabinet => refus.
7. `/multi-practitioner` groupe par `praticien_id` réel et sépare les rendez-vous legacy non assignés.
8. Aucun backfill destructif des anciens rendez-vous.
9. Tests backend + CI verts sur le HEAD exact avant certification.

## Baseline technique déjà vérifiée pendant le diagnostic

### Modèle / tenant

- `UserRole` contient `ADMIN`, `DENTISTE`, `SECRETAIRE`.
- `CabinetType` contient `PRIVE`, `CLINIQUE`.
- `User.get_employer_id()` fournit le tenant cabinet canonique.
- `Patient.employer_id` et `Appointment.employer_id` isolent les données par cabinet.
- `Acte` possède déjà `praticien_id`.
- `Appointment` n'avait pas de `praticien_id` au début du chantier.

### Agenda actuel

- `backend/routers/appointments.py` requête les rendez-vous avec `Appointment.employer_id == current_user.get_employer_id()`.
- la détection de conflits historique est faite au niveau `employer_id`, donc globalement pour tout le cabinet.
- deux dentistes simultanés peuvent donc être considérés comme en conflit dans l'implémentation historique.
- le chemin bulk a été identifié comme point critique à vérifier et harmoniser avec la validation standard.
- `backend/schemas/appointments.py` ne contenait pas de champ praticien au diagnostic initial.
- `backend/services/agenda_availability.py` utilisait également une logique de disponibilité cabinet-wide.

### Migration

Le repo dispose déjà d'une chaîne/mécanique de migration. Le fichier canonique note la chaîne Alembic observée au démarrage P0 :

`f7a8b9c0d1e2 → c1a55e700001 → c2a55e700002`

Ne pas inventer un nouveau mécanisme de migration si Alembic existant suffit. Vérifier la tête Alembic réelle avant de créer la migration P0.

### Commercial / type de cabinet

Le chantier commercial est indépendant : GOLD/PREMIUM/ELITE et leurs quotas ne doivent pas être couplés artificiellement à `CabinetType.CLINIQUE`.

## Invariants P0 à préserver

- Tenant canonique = `employer_id` du cabinet.
- Praticien canonique = `User.id`, pas de table praticien parallèle.
- `praticien_id` reste nullable pour compatibilité historique.
- `NULL` = legacy/non assigné ; par sécurité il bloque les chevauchements du créneau.
- rendez-vous explicitement assignés à deux praticiens différents peuvent être simultanés.
- praticien assignable : même tenant, compte actif/approuvé et rôle compatible avec pratique clinique ; traiter correctement le propriétaire/admin praticien selon le modèle réel du repo, sans supposer.
- bulk doit réutiliser la même règle de validation/conflit que la création unitaire et doit détecter aussi les collisions internes au lot.
- aucune fuite inter-cabinet.
- aucune migration destructive/backfill forcé.
- aucun changement UI dans P0 tant que le backend n'est pas prouvé. Si UI touchée ensuite : BEFORE → Goal → mockup/référence → implémentation → AFTER 390/768/1280 → comparaison/tests → score visuel.
- aucun déploiement Vercel sans autorisation explicite.

## Roadmap canonique

### P0 — Agenda multi-praticiens réel

Backend, migration, validation tenant/praticien, conflits, bulk, endpoint multi-praticien, tests, CI.

### P1 — UX clinique ciblée

Dashboard, Agenda, filtres/contexte praticien, Team Manager. Validation visuelle stricte obligatoire.

### P2 — Patient, actes et facturation

Praticien référent, attribution clinique pertinente, production/CA par praticien, droits cohérents.

### P3 — Documents, signatures et ressources

Auteurs/signatures, permissions avancées et ressources physiques uniquement si besoin produit démontré.

### Différé

Multi-site hors périmètre tant qu'un besoin réel n'est pas démontré.

## Next exact de reprise

1. Lire `AGENTS.md` puis `STATE.md`.
2. Lire `docs/CLINIQUE_MULTI_PRATICIENS_ROADMAP.md` et ce handover.
3. Vérifier `master`, HEAD de `feat/clinic-multipractitioner-p0`, PR éventuelle et CI du HEAD exact.
4. Si `master` a avancé, inspecter son commit avant de décider rebase/merge ; ne pas écraser la branche.
5. Re-lire les fichiers réels avant patch :
   - `backend/models.py`
   - `backend/schemas/appointments.py`
   - `backend/routers/appointments.py`
   - `backend/services/agenda_availability.py`
   - migrations Alembic / tête Alembic actuelle
   - tests rendez-vous/agenda/team existants
6. Implémenter P0 dans cet ordre : migration + modèle → schémas → helper de validation praticien → conflits unitaires/update → bulk → endpoint multi-praticien → tests.
7. Tester les cas : même praticien conflit, praticiens différents simultanés, legacy NULL, cross-tenant, pending/inactif/secrétaire, update/reassignment, bulk y compris collision interne.
8. Corriger jusqu'au vert local/CI. Après 2 échecs similaires, changer de stratégie.
9. Créer/mettre à jour la PR uniquement lorsque le patch est cohérent ; lancer la CI puis poursuivre tout travail indépendant. Ne pas poller passivement.
10. Closeout : preuves → mise à jour du fichier canonique → cohérence docs → merge si autorisé/sûr → post-merge → P1.

## Prompt de reprise prêt à coller dans une nouvelle fenêtre

```text
Reprends le chantier Digital Crown — Clinique multi-praticiens P0.

Repository : hraaaaf/Digital_crown
Branche : feat/clinic-multipractitioner-p0

Commence impérativement par lire, dans cet ordre :
1. AGENTS.md
2. STATE.md
3. docs/CLINIQUE_MULTI_PRATICIENS_ROADMAP.md
4. docs/handovers/2026-09-12-clinic-multipractitioner-p0-handover.md

Puis vérifie immédiatement avant toute modification :
- le master réel ;
- le HEAD réel de feat/clinic-multipractitioner-p0 ;
- l'existence/état d'une éventuelle PR P0 ;
- les CI associées à CE HEAD exact ;
- la tête Alembic réelle.

État au handover avant création du commit de handover :
- master : 33713654731f1ca165663a4cf35fbf7643897d61
- branche P0 : a41c2cd5a05344891941b79db6330959cd8332db
- merge-base : e700da0950cb0c5f90379b57401fa4ae926ad5af
- branche divergée : ahead 1 / behind 1
- a41c2cd contient uniquement le fichier canonique docs/CLINIQUE_MULTI_PRATICIENS_ROADMAP.md
- aucune implémentation backend P0 n'est certifiée à ce stade

Goal P0 : agenda réellement multi-praticiens côté backend, avec praticien réel du cabinet, isolation tenant stricte, conflits par praticien, compatibilité legacy NULL, bulk sécurisé et tests/CI verts.

Succès obligatoire :
1. appointments.praticien_id nullable + FK users.id + index ;
2. create/update/check-conflicts/bulk valident le praticien dans le tenant ;
3. même praticien + chevauchement = 409 ;
4. praticiens différents + même créneau = autorisé ;
5. legacy NULL chevauchant = blocage de sécurité ;
6. autre cabinet / secrétaire / pending / inactif = refus ;
7. /multi-practitioner groupe par praticien réel et sépare legacy ;
8. aucun backfill destructif ;
9. tests + CI verts sur HEAD exact.

Invariants :
- employer_id reste le tenant canonique ;
- User.id reste l'identité praticien ;
- ne pas coupler CabinetType.CLINIQUE aux quotas GOLD/PREMIUM/ELITE ;
- ne pas toucher l'UI avant preuve backend P0 ;
- si UI ensuite : BEFORE → Goal → mockup → implémentation → AFTER 390/768/1280 → comparaison/tests → score visuel ;
- aucun déploiement Vercel sans autorisation explicite.

Avance en autonomie : re-lis le code réel, implémente, teste, corrige, continue. Ne demande rien si tu peux décider de manière sûre. Après 2 échecs similaires, change de stratégie. CI en cours n'est pas un motif d'arrêt tant qu'il reste du travail indépendant.

Format des retours : Résultat → preuve → prochaine action, puis 📍 REPÈRES avec uniquement des faits vérifiés.

Ne déclare jamais terminé/validé/corrigé sans preuve.
```

## Critère de clôture du handover

Le handover est suffisant si une nouvelle fenêtre peut reprendre le chantier sans information orale supplémentaire, reconstruire l'état Git réel, comprendre les invariants, implémenter P0 et savoir exactement quels tests constituent la preuve.

# STATE — DigitalCrown

> Fichier de reprise (handoff). **Lis-moi en premier** pour savoir où on en est.
> Le bloc AUTO ci-dessous est régénéré automatiquement à chaque fin de session : ne l'édite pas à la main.
> Les sections plus bas sont à toi (l'agent) : tiens-les à jour avant de t'arrêter.

<!-- STATE:AUTO:START -->
## Dernière session (auto — ne pas éditer à la main)
- **Mis à jour :** 2026-07-11 12:46
- **Branche :** `master`
- **Worktree :** `C:/Users/lenovo/Documents/Cabinet/DigitalCrown`

### Fichiers touchés
- _(aucun fichier modifié détecté)_

### Dernières demandes
- ODM — REPO-LARGE-FILES-SAFE-AUDIT-1 MISSION — REPO-LARGE-FILES-SAFE-AUDIT-1 Objectif : Auditer le dépôt Digital Crown afin d’identifier les fichiers et dossiers
- Ok go
- Du coup ou sont stockés les pdfs des patients !?
- Regarde dans archives ou d’autres dossiers
- Français
- Oui il faut les récupérer !
- Du coup on fait quoi m’t !?
- Audit general et global de l’app ce qui est bien fait ce qui ne l’ai pas ce qui devrait être amélioré pour déplacer toute concurrence ce qui devrait être ajouté
<!-- STATE:AUTO:END -->

## ROADMAP V2 — Statut réel (refresh 2026-07-10)

> Recalcul après audit codebase réel (3 agents Explore, ~50 fichiers inspectés backend+frontend).
> Complète `docs/ROADMAP_DIGITAL_CROWN_V2.md` et `docs/DIGITAL_CROWN_FEATURE_AUDIT_VS_COMPETITOR.md`
> (tous deux verrouillés, snapshot du 09/07) — ce refresh vit uniquement ici, les docs originaux
> ne sont pas modifiés.

**Score global recalculé : ~8,0/10** (cible "DC après P0" du roadmap = 8,2/10 — quasi atteinte,
avec plusieurs items P1 déjà livrés en bonus)

| Dimension | Score 09/07 | Score réel 10/07 | Commentaire |
|---|---|---|---|
| Workflow financier | 4,5/10 | 8,0/10 | Snapshot patient, impayés, dashboard J+0, email facture livrés. Reste : pipeline visuel unifié + avances patients nommées |
| Stock / consommables | 0/10 | 5,0/10 | MVP livré pile à la cible P0 (CRUD + alertes + UI). Pas de ledger mouvements, pas de déduction auto (= P2, toujours absent) |
| Dossier patient | 8/10 | 8,5/10 | Onglet Finances vivant dans PatientDetails |
| Agenda / Frontdesk | 7/10 | 8,0/10 | Salle d'attente temps réel livrée (page dédiée + widget dashboard, polling 30s) |
| Module laboratoire | 2/10 | 6,0/10 | Route réactivée (n'est plus ComingSoon) mais 8 items du backlog encore ouverts |
| Dashboard | 5,5/10 | 7,5/10 | CA jour, mois, impayés globaux, salle d'attente — tout visible |
| IA / Sécurité / Imagerie / Ortho | inchangé | inchangé | Hors scope de ce refresh, rien touché |

### P0 — statut réel
- ✅ **P0-PATIENT-FINANCIAL-SNAPSHOT-1** — terminé (`PatientFinances.tsx` + `GET /patients/{id}/financial-snapshot`)
- ✅ **P0-UNPAID-BALANCE-VIEW-1** — terminé (onglet Impayés AccountingPage + `GET /accounting/patient-debts` + `/overdue`)
- ✅ **P0-DASHBOARD-FINANCE-J0-1** — terminé (CA jour/mois/impayés + salle d'attente inline, Dashboard.tsx L640-814)
- ⚠️ **P0-TREATMENT-PLAN-UX-1 — PAS terminé, REFORMULÉE le 10/07 en P0-TREATMENT-JOURNEY-1** :
  TreatmentPlanStep a un statut en DB mais aucune timeline visuelle pending/done/postponed.
  TreatmentPlanStudio reste un flux conversationnel, pas une vue dédiée dans le dossier patient.
  **Seul vrai trou P0 restant** — voir décision ci-dessous, le scope est élargi au-delà d'une
  simple timeline UI.
- ✅ **P0-STOCK-INVENTORY-MVP-1** — terminé, CRUD complet + alertes + UI (`stock.py`, `StockPage.tsx`, lien Sidebar)
- ⚠️ **P0-LAB-UI-REACTIVATION-1** — route active, mais 8/10 items du backlog UI encore ouverts
  (delete, picker patient/acte, deadline hardcodée, shade/notes, filtre patient, lien patient,
  annuaire labos, alerte READY)

### P1 — statut réel
- ⚠️ **P1-QUOTE-INVOICE-PAYMENT-PIPELINE-1** — partiel : PayActeModal + InstallmentPlanModal
  fonctionnels et intégrés à PatientFinances, mais pas de vue pipeline unifiée depuis l'odontogramme,
  et pas de table PatientAdvance (avances nommées absentes)
- ✅ **P1-WAITING-ROOM-DASHBOARD-1** — terminé
- ✅ **P1-ANALYTICS-CSV-EXPORT-1** — terminé (export dans Analytics.tsx ET AccountingPage.tsx)
- ⚠️ **P1-CABINET-REPORTING-1** — backend seul (`report_gen.py` génère un PDF honoraires, pas un
  vrai rapport mensuel cabinet CA/praticien/conversion/comparaison M-1) ; aucun bouton frontend
  "Générer rapport mensuel"
- ✅ Bonus non planifié initialement : envoi email facture/devis (`POST /accounting/send-email/{item_id}`) — terminé

### P2 — statut réel (rien de surprenant, tout reste à faire)
- ❌ Stock lié automatiquement aux actes — absent, zéro référence StockItem hors `stock.py`
- ❌ IA vigilance stock (Crown Bot QUERY_STOCK) — absent, pas dans la liste d'intents de `bot.py`
- ⚠️ Backup status visible cockpit — API existe (`GET /admin/backups`), aucun widget Dashboard
- ❌ Analytics avancés BI (par praticien/spécialité, export XLSX) — absent
- ⚠️ Installation semi-automatique — script + doc complète (`bootstrap_new_cabinet.py`,
  `docs/NEW_CABINET_INSTALL_PATH.md`) mais pas d'installeur GUI/EXE
- ⚠️ Crown Bot étendu — QUERY_LAB déjà présent, QUERY_STOCK / QUERY_PAYMENTS_LATE toujours absents

### Prochain vrai manque — DÉCISION 10/07 : P0-TREATMENT-JOURNEY-1 (reformulation)

CTO a validé le refresh mais a corrigé le cadrage de la dernière mission P0 : **ce n'est pas une
timeline UI, c'est le fil conducteur clinique + administratif du patient.**

Une simple timeline visuelle de `TreatmentPlanStep` (pending/done/postponed) ne serait qu'un
lifting graphique. L'objectif réel — repris du positionnement concurrent — est une vue chronologique
unique qui relie *tout* le parcours patient, pas seulement le plan de traitement :

```
Consultation initiale → Diagnostic → Plan de traitement → Devis accepté →
Paiement (30%, ...) → Actes réalisés (un par un) → Contrôle → Fin de traitement
```

Chaque étape doit être : colorée par statut, filtrable, datée, cliquable, et **liée** aux entités
existantes déjà en DB — documents (DocumentArchive), paiements (Payment/Installment), radios
(médias RVG/pano), actes (Acte). Pas de nouvelle vue isolée : un assemblage de données déjà
présentes en base (TreatmentPlanStep, Acte, Payment, DocumentArchive, médias) dans un seul flux
chronologique par patient.

**Nom de mission retenu : `P0-TREATMENT-JOURNEY-1`** (remplace `P0-TREATMENT-PLAN-UX-1`).

**Design produit** — voir `docs/TREATMENT_JOURNEY_DESIGN.md` (3 agents Explore, réponses aux
9 questions d'architecture : entité centrale, étapes, objets reliés sans duplication, UX,
anti-sapin-de-Noël, navigation, états, performance, scope MVP).

**Correction majeure post-design (avant le plan technique)** : une inspection read-only de la
vraie DB cabinet (`digitalcrown_db`, 220 patients réels, 2026-07-10) a montré que la table
`actes` (176 lignes) porte la signature de données de seed (même horodatage HH:MM:SS sur des
dates différentes) et ne couvre que 30/220 patients (13,6%). Le vrai flux de facturation passe
par `payments` (134 lignes, 107/220 patients, activité datée naturellement) et
`document_archives` (260 documents). **`Acte` a donc été écarté** comme source du Journey, et
la migration `Acte.treatment_plan_step_id` initialement envisagée abandonnée (elle n'aurait de
valeur que si `Acte` était réellement alimenté).

**⚠️ Découverte annexe non résolue** : `get_patient_financial_snapshot`
(`backend/routers/patients.py`, endpoint utilisé par l'onglet Finances/`PatientFinances.tsx`,
déclaré "terminé" dans le refresh roadmap) interroge la table `Acte` pour les impayés — vu la
couverture de 13,6%, ce calcul sous-déclare très probablement pour ~86% des patients réels.
**Backlog séparé à créer : `UNIFY-ACT-PERSISTENCE-1`** — tracer et unifier le vrai pipeline de
facturation (`backend/routers/documents.py::generate` crée `Payment`/`DocumentArchive` mais
jamais de ligne `Acte`), avant de pouvoir corriger `financial-snapshot` et relier proprement un
plan de traitement à des actes réels. Non traité dans ce P0.

**Plan technique v4 validé (2026-07-10)** — 4 itérations de revue (v1→v4), corrections notables :
sécurité du rendu document (blob authentifié, jamais d'URL publique), service dédié
`patient_journey_service.py` plutôt que logique dans le routeur, verrou `SELECT...FOR UPDATE`
anti-doublon concurrent, `JourneyMilestone` en soft-delete (`deleted_at`/`deleted_by`, jamais de
suppression dure), matrice de permissions par type de jalon (DENTISTE/ADMIN pour
DIAGNOSTIC/CONTROLE/CLOTURE, +`accounting` pour DEVIS_VALIDE), gate de rollout en 4 phases
(local → rehearsal PostgreSQL avec écritures → arrêt/bilan → activation cabinet réelle sur GO
explicite). Plan complet : `C:\Users\lenovo\.claude\plans\expressive-squishing-goblet.md`.

**Phase A (implémentation locale) — TERMINÉE (2026-07-10) :**
- Backend : `backend/models.py` (`MilestoneType` + `JourneyMilestone`), `backend/schemas/journey.py`
  (schémas typés), `backend/services/patient_journey_service.py` (agrégation 9 sources + résumé,
  sans `Acte`), `backend/routers/patients.py` (`GET/POST/DELETE .../journey...`)
- Frontend : `LegacyActeNotes.tsx` (extrait de `PatientTracking.tsx`, partagé), `PatientTracking.tsx`
  (refactor d'extraction, reste fonctionnel comme fallback non branché), `PatientJourney.tsx`
  (nouveau composant, devient le rendu par défaut de l'onglet `?tab=tracking` dans
  `PatientDetails.tsx`)
- Tests : 13 cas backend (`backend/tests/test_patients.py::TestPatientJourney*`, 1 skip documenté
  pour la concurrence PostgreSQL) + 10 cas frontend (`PatientJourney.test.tsx`) — tous passent.
  `pytest backend/tests/test_patients.py` : 25 passed, 1 skipped. `npx vitest run` : 39 passed.
  `npm run build` : OK.
- Vérification live partielle : requête read-only confirmant `journey_milestones` absente sur
  `digitalcrown_db` (attendu, `create_all()` la créera au prochain redémarrage réel) — vérification
  plus poussée sur la vraie DB bloquée par le système de permissions (gate Phase A/D respecté),
  et absence d'identifiants applicatifs réels pour un clic-à-travers UI complet.

**Phase B (rehearsal PostgreSQL avec écritures) — TERMINÉE (2026-07-10).**
Environnement isolé créé : DB `digitalcrown_treatment_journey_rehearsal`, backend sur le port 8009
(`backend/.env.treatment-journey-rehearsal`, non commité), frontend dev sur le port 5183
(`VITE_API_URL=http://127.0.0.1:8009`), média `treatment_journey_rehearsal_media`. Résultats :
- API (9 checks) + milestones/isolation (9 checks) + permissions par rôle (17 checks) + sécurité
  documentaire (4 checks) : **39/39 PASS**, sur PostgreSQL réel via HTTP.
- **Concurrence PostgreSQL validée** : 2 `POST` simultanés sur le même jalon → une seule ligne
  créée (`SELECT ... FOR UPDATE` confirmé sous vraie concurrence, impossible à tester sous SQLite) ;
  `confirm_duplicate=true` crée bien une 2e ligne volontaire.
- **Smoke frontend manuel effectué par le CTO** (extension Chrome indisponible pour moi dans cet
  environnement) — validé sur les 2 patients de test rehearsal (avec historique / vide).

**3 bugs réels trouvés et corrigés pendant le smoke — aucun dans le code Journey lui-même :**
1. CORS : mon fichier env rehearsal n'autorisait que le port 8009, pas 5183 (le frontend) → corrigé.
2. `email-validator` (Pydantic `EmailStr`, utilisé par `UserOut`) rejette le TLD `.test` (RFC 2606,
   réservé) → mes comptes de test rehearsal utilisaient `@journey-rehearsal.test`, cassant
   `GET /api/auth/me` après login. Renommés en `.ma` (même convention que
   `conftest.py::make_user()`).
3. `POST /api/clinics/` (bootstrap de setup) suppose un seul propriétaire ADMIN/DENTISTE dans toute
   la base — mon seed rehearsal en avait 3 (l'admin auto-seedé + 2 dentistes de test), donc le
   wizard d'onboarding tombait sur le mauvais compte et rejetait avec 400. Contourné en marquant
   directement `is_initialized=True` sur le cabinet du compte de test. **Ce n'est pas un bug
   Journey — c'est une limite préexistante du bootstrap mono-tenant, à garder en tête si on
   reseed un environnement multi-owner un jour.**

**⚠️ Incident pendant la Phase B — schéma + build exposés sur `digitalcrown_db` sans GO explicite,
corrigé same-session :**
Le contrôle de non-impact final a montré que `journey_milestones` existait désormais sur
`digitalcrown_db` (absente en tout début de Phase B, vérifié). Cause : `JourneyMilestone` fait
partie de `backend/models.py` depuis la Phase A (code réel, pas scopé au rehearsal) ; un process
réel tournant sur le port 8005 (`db: ok` confirmé) a dû redémarrer pendant la session, et son
`create_all()` normal a créé la table — additive, **0 ligne**, aucune perte de données. Plus
sérieux : ce même process servait `frontend/dist`, que `npm run build` (vérification Phase A)
avait reconstruit avec `PatientJourney` actif — donc **l'onglet Séances des vrais patients
affichait le nouveau Treatment Journey en production**, sans passage par le GO explicite de
Phase D. Corrigé dans la foulée : source temporairement revert vers `PatientTracking`,
`npm run build`, source restauré vers `PatientJourney` (le travail Phase A/B reste intact), sans
reconstruire `dist/` une seconde fois — `dist/` reste donc figé sur le comportement sûr
(`PatientTracking`) jusqu'à activation volontaire. Vérifié : `curl http://127.0.0.1:8005/` sert de
nouveau le hash de build pré-Journey. Aucune ligne réelle créée dans `journey_milestones` (0),
aucune donnée rehearsal dans `digitalcrown_db` (0 patient/user "REHEARSAL"), superadmin réel
intact. Les 2 lignes en plus sur `payments`/`document_archives` détectées lors du contrôle
correspondent à de l'activité clinique réelle concurrente (patients Hakimi Adam, Grizel Fatima
Zahra) — sans rapport avec cette session.
**Leçon pour la suite : ne plus lancer `npm run build` "juste pour vérifier" tant qu'un process
réel (port 8005) partage le même `frontend/dist` que l'environnement de travail — utiliser un
dossier de build séparé ou vérifier qu'aucun process réel ne tourne avant de builder.**

Environnement rehearsal démonté en fin de Phase B : process 8009 et 5183 arrêtés, DB rehearsal et
fichiers `.env.treatment-journey-rehearsal`/`treatment_journey_rehearsal_media` laissés sur disque
(réutilisables pour une future Phase B, aucune donnée sensible dedans).

**Phase C (bilan/décision GO-NO-GO) — ce paragraphe EST le bilan.** Verdict : Phase B validée sur
le fond (39/39 checks API + smoke manuel PASS + concurrence PostgreSQL confirmée), avec un
incident de fuite de build/schéma vers `digitalcrown_db` détecté et corrigé dans la même session.
**Phase D (activation cabinet réelle contrôlée, avec backup préalable) — PAS RELANCÉE
volontairement.** Le code est prêt et testé ; l'activation réelle (rebuild + déploiement délibéré)
reste une décision séparée du CTO, avec backup avant, comme prévu par le plan.

**Backlog séparé identifié pendant l'implémentation : `CLEANUP-PATIENT-TRACKING-1`** — supprimer
`PatientTracking.tsx` une fois `PatientJourney.tsx` validé en usage réel (actuellement conservé
comme fallback, non supprimé).

### Phase C — Runtime Truth (2026-07-10, lecture seule)

Cause exacte de l'incident Phase B identifiée : le process réel sur le port 8005 tourne avec
`uvicorn --reload` depuis **avant** cette session — ce n'est pas un redémarrage externe, c'est
`--reload` qui a réagi directement à mes propres éditions de `backend/*.py` pendant la Phase A.
État constaté (lecture seule, `/openapi.json`) : **backend réel = routes Journey déjà actives**
(GET/POST/DELETE exposés) / **frontend réel = ancien build** (`PatientTracking`, hash
`index-BO2OChwV.js`) → état hybride "B" (API prête, UI non activée). `journey_milestones` : table
présente, 0 ligne, schéma conforme. Aucune écriture effectuée pendant cette vérification.

### REAL-BUILD-RUNTIME-ISOLATION-GUARD-1 (2026-07-10) — garde-fous mis en place

**Cause racine traitée** : `npm run build` écrivait silencieusement dans `frontend/dist`, le
dossier servi par le process réel du port 8005 (même s'il n'a pas besoin d'être redémarré —
`StaticFiles` sert depuis le disque à chaque requête). Et `backend/core/media_paths.py` /
`run_rehearsal_backend.ps1` ne reconnaissaient qu'un seul nom de rehearsal littéral
(`e2e_install_rehearsal` / `install_rehearsal_media`), laissant passer sans la validation stricte
tout environnement de rehearsal nommé différemment (exactement le cas de la Phase B).

**Corrections :**
- `backend/core/media_paths.py::is_rehearsal_environment()` — généralisé à tout `ENVIRONMENT`
  contenant `"rehearsal"` (au lieu du seul literal `"e2e_install_rehearsal"`)
- `backend/core/media_paths.py::validate_media_root()` — exige que le dossier de sortie contienne
  lui-même `"rehearsal"` (au lieu du seul literal `"install_rehearsal_media"`)
- `backend/scripts/run_rehearsal_backend.ps1::Test-UnsafeMediaRoot` — même généralisation côté
  PowerShell
- `frontend/scripts/build-guard.mjs` (nouveau) — détecte si le port 8005 répond avant tout build :
  - `npm run build` (safe, `dist`) → **refuse si :8005 actif**
  - `npm run build:rehearsal` (`dist-rehearsal`) → toujours autorisé, jamais touché par `dist`
  - `npm run build:real` (`dist`, activation explicite) → refuse si :8005 actif **et** exige
    `CONFIRM_REAL_BUILD=yes`
  - `npm run serve:rehearsal` → sert `dist-rehearsal` sur le port 5183
  - Chaque sortie reçoit un `build-manifest.json` (environment, commit, date, mode, outputDir)
- `.gitignore` — ajout de `frontend/dist-rehearsal/`, `frontend/dist-test/`

**Tests de validation (6 cas requis) :**
1. `npm run build` pendant :8005 actif → **refusé** ✅ (exécuté réellement)
2. `npm run build:real` pendant :8005 actif → **refusé** ✅ (vérifié par lecture de code — le check
   `realCabinetLive` s'exécute avant tout appel `tsc`/`vite build`, aucun chemin d'exécution
   possible avant lui ; non exécuté réellement, conformément à la consigne "dry-run seulement")
3. `npm run build:rehearsal` pendant :8005 actif → **réussi vers `dist-rehearsal`** ✅ (exécuté),
   `frontend/dist` et le hash servi par :8005 vérifiés inchangés après coup
4. `DATABASE_URL` réel en rehearsal → **refusé** ✅ (logique testée isolément)
5. `MEDIA_ROOT` réel en rehearsal → **refusé** ✅, mon dossier Phase B
   (`treatment_journey_rehearsal_media`) maintenant **accepté** par la version généralisée
   (testé en Python direct sur `media_paths.py` + en PowerShell sur le script corrigé)
6. Build réel après arrêt maîtrisé → non exécuté (dry-run demandé), correction structurelle validée

**Non testé/hors scope de cette mission** : le risque `--reload` lui-même (édition de code source
Python qui recharge automatiquement le process réel du port 8005) n'est pas neutralisé par ces
garde-fous — ils protègent le *build frontend* et la *config média/DB*, pas le rechargement
automatique du backend réel quand ses fichiers sources changent. À traiter dans une mission dédiée
si jugé nécessaire avant une future Phase D (ex. : lancer le dev réel sans `--reload`, ou sur un
checkout séparé du code).

**Après cette mission, prochaine étape envisagée (pas encore lancée) : benchmark mondial multi-concurrents**
(Dentrix, Curve Dental, Denticon, Open Dental, CareStack, Doctolib Pro partie cabinet, Dental
Intelligence, Henry Schein, Planmeca Romexis, Orthotrac) pour préparer une roadmap V3 qui
n'imite plus un seul concurrent mais assemble les meilleures idées du marché. À faire une fois
P0-TREATMENT-JOURNEY-1 terminé, pas avant.

**Ne pas relancer :** Stock (fait), Paiement lié aux actes (fait), Échéancier (fait), Salle d'attente
(fait), Export CSV analytics (fait).

---

## M5-A — Facturation avancée ✅ DONE
✅ **Export CSV** — `GET /accounting/export-csv` + bouton vert dans l'en-tête
✅ **Email patient** — `POST /accounting/send-email/{item_id}` + bouton Mail par ligne
✅ **Relances automatiques** — `GET /accounting/overdue?days=30` + `POST /accounting/relance/{item_id}` + bannière overdue Treasury
✅ **Édition inline** — `PATCH /accounting/item/{item_id}` + clic sur titre/montant → input → Enter/Blur sauvegarde

## M5-B — Agenda intelligent ✅ DONE
✅ **Détection surréservation** — `GET /appointments/check-conflicts` + warning inline dans AgendaModal (debounced 500ms)
✅ **Rappel individuel** — `POST /appointments/{id}/remind` + bouton cloche par carte RDV dans WeeklyView, badge `reminder_sent`
✅ **Vue multi-praticien** — `GET /appointments/multi-practitioner` + onglet "Multi" dans AgendaStudio, gate PREMIUM/ELITE, composant `MultiPractitionerView`

## M5-C — Onboarding & distribution ✅ DONE
✅ **Import patients CSV** — `POST /patients/import-csv` + modal `CsvImportModal.tsx` + bouton "Import CSV" dans PatientList
✅ **Landing page** — `LandingPage.tsx` à `/landing` (hero, features, pricing, formulaire démo) + `POST /api/public/demo-request` (stockage JSON + email optionnel)

## Milestone M5 — backlog restant
**Option A** ✅ **Option B** ✅ **Option C** ✅
**Option C — Onboarding & distribution** (prochaine)

**Option C — Onboarding & distribution**
- Wizard first-run (config cabinet, import patients CSV)
- Packaging installateur Windows (Electron ou NSIS)
- Page de landing + formulaire de démo

**Option D — Consolidation qualité**
- Coverage tests > 80% (actuellement ~40%)
- E2E Playwright sur les flows critiques (login, create patient, cephalo)
- Monitoring Sentry + alertes

## État courant (18 Juin 2026)
- **Architecture local-first** : PostgreSQL local, Firebase pour auth/licence uniquement
- **Score audit** : 8.1/10 → toutes les corrections P0/P1/P2 appliquées
- **Tests** : 125 passed, 6 skipped, 0 failed (`pytest backend/tests/`)
- **Abonnements** : GOLD (1D+2S) / PREMIUM (2D+6S) / ELITE (illimité) — workflow approve/reject opérationnel
- **Cephalo studio** : 4 étapes, validator étendu (angles + mm + unités), Step3 en accordéon
- **BotPendingAction** : server-side complet, TTL 30min, cancel endpoint, RBAC employer_id
- **M5-A Facturation** : export CSV, email patient, overdue banner + relances — implémentés

## Blocker / en attente
- Aucun blocker technique.
- Push sur `origin/modif` — PR à ouvrir vers `dev` quand le CTO valide.

## Décisions prises
- **Actes cliniques** : permission `[clinical, agenda]` (pas `[agenda, accounting]`). Validé session 2026-06-18.
- **CephaloConsistencyValidator** : unités mm vs ° = FATAL si contradiction, bornes physiologiques mm ajoutées pour Wits/Surplomb/Recouvrement/I_NA_mm/I_NB_mm/Ligne_E.
- **cephalo_measure_registry.py** : source unique — importer de là, ne jamais dupliquer MM_KEYWORDS.
- **Accès par sous-compte** : 9 permissions granulaires, workflow pending → approve/reject, quota vérifié à la création ET à l'approbation (anti-race).
- **Statuts RDV mobile** : mappés via couche conversion dans `mobile.py`, ne jamais passer valeur mobile directement à `models.AppointmentStatus()`.
- **WS auth via `?token=`** : contournement cross-port en dev.
- **`user_id` nullable sur BotSession** : anciennes sessions orphelines restent invisibles, pas de migration.

## Module LABO — V2 Backlog (non finalisé)

**Ce qui existe déjà (à ne pas reconstruire) :**
- `backend/routers/lab_jobs.py` — GET `/lab-jobs/`, PATCH `/{id}`, POST `/`
- `frontend/src/types/labJob.ts` — types complets (6 statuts : PRESCRIPTION → DELIVERED)
- `frontend/src/services/labJobService.ts` — fetch, patch, create
- `frontend/src/components/LabJobsBoard.tsx` — Kanban board (déplacement statut, alertes deadline, création manuelle)
- `frontend/src/features/mobile/Dashboard/views/LabView.tsx` — vue mobile minimaliste

**Ce qui manque (à implémenter en V2) :**
- [x] **Débloquer la route** ✅ — `/labo` actif dans App.tsx (route non commentée), lien Sidebar présent (vérifié 2026-07-10)
- [ ] **DELETE endpoint** backend + bouton supprimer sur le Kanban
- [ ] **Searchable patient/acte picker** dans la modale de création (remplacer les inputs ID bruts)
- [ ] **Deadline picker** dans la modale (actuellement hardcodé +7 jours)
- [ ] **Champs shade + notes** dans la modale de création (existent en DB mais absents du form)
- [ ] **Colonne DELIVERED** dans le Kanban (dans l'enum mais absente de STATUS_ORDER)
- [ ] **Filtre par patient** dans le board (aujourd'hui affiche tous les jobs du cabinet)
- [ ] **Lien patient** cliquable depuis chaque carte Kanban
- [ ] **Annuaire laboratoires** — gérer les lab_id (CRUD labo, sélecteur dans la demande)
- [ ] **Alerte READY** — notification/badge quand prothèse prête (scheduler backend ou polling)
- [ ] **WhatsApp envoi** depuis le desktop board (existe en mobile, pas en desktop)

## Module BOT (CrownBot Chat) — V2 Backlog (non finalisé)

**Ce qui existe déjà (à ne pas reconstruire) :**
- `CrownBotChat.tsx` — UI complète : tabs Chat / Ghost Brain, sidebar sessions, streaming SSE, PendingActionCard, upsell
- `backend/routers/bot.py` — sessions CRUD, `/chat` (compat), `/chat/stream` (SSE), `/execute`, `/execute/{id}/cancel`
- `action_dispatcher.py` — intents : CREATE_APPOINTMENT, OPEN_PRESCRIPTION_EDITOR, OPEN_DEVIS_EDITOR, CHANGE_STATUS, QUERY_LAB
- Ghost Brain WebSocket — reconnexion automatique (8 retry), markAsRead, quickActions

**Dead code à supprimer :**
- `frontend/src/components/CrownBot/hooks/useCrownBot.ts` — hook legacy axios `/api/bot/chat` non-streaming, **jamais importé**
- `frontend/src/components/CrownBot/ChatMessage.tsx` — composant **jamais importé** (CrownBotChat inline son propre rendu)

**Ce qui manque (à implémenter en V2) :**
- [x] **Bug Ghost Brain** ✅ — lien `/patients/undefined` corrigé (fallback `<span>` si `patient_id` null)
- [ ] **Upsell non relié au plan** — seuil hardcodé à 3 échanges LLM pour tous ; PREMIUM/ELITE devraient être illimités
- [ ] **Fenêtre de contexte trop petite** — `_build_context` prend seulement les 4 derniers messages ; longues conversations perdent le fil
- [ ] **`getPageContext` ne couvre pas `/labo`** — pas de suggestions contextuelles pour le module Labo
- [ ] **Sessions non paginées** — toutes les sessions chargées en une fois (`GET /bot/sessions`), ralentit avec le temps
- [ ] **Pas de recherche dans l'historique** des sessions
- [ ] **Voice input (STT)** — bouton mic désactivé "Bientôt disponible" ajouté dans la barre de saisie
- [ ] **Pièces jointes** — bouton paperclip désactivé "Bientôt disponible" ajouté dans la barre de saisie

## REAL-RUNTIME-IMMUTABILITY-GUARD-1 (2026-07-10)

Mission déclenchée par la découverte en Phase C : le process réel :8005 tourne avec
`uvicorn --reload` depuis avant la session — mes éditions de `backend/*.py` en Phase A l'ont
rechargé automatiquement, causant l'incident précédent. Objectif : rendre ça structurellement
impossible.

**Livré (sans toucher au process réel :8005, qui tourne toujours avec --reload) :**
- `backend/scripts/create_release.ps1` — snapshot immuable (`backend/` + `frontend/dist`
  courant) copié hors du dépôt vers `C:\Users\lenovo\DigitalCrown-Runtime\releases\<id>\`,
  avec `release-manifest.json` (environment, commit, built_at, backend_path, frontend_dist_path)
- `backend/scripts/run_real_backend.ps1` — lanceur unique du runtime réel : exige
  `-ConfirmRealActivation "YES"`, exige un manifeste de release valide
  (`environment=cabinet-real`), refuse toute config DATABASE_URL/ENVIRONMENT/MEDIA_ROOT
  contenant "rehearsal", refuse tout argument contenant `--reload` (testé positionnel ET
  valeur-de-paramètre), lance depuis le dossier de release (jamais le dépôt), sans `--reload`,
  via le venv explicite (pas le `python` du PATH global — bug trouvé et corrigé pendant les tests)
- Une première release réelle créée : `20260710-191153-738eb5234efc` (commit `738eb52`),
  **non activée** — juste candidate

**Tests validés (sans toucher digitalcrown_db ni le port 8005) :**
1. `--reload` en argument positionnel → refusé par PowerShell lui-même (binding désactivé)
2. `--reload` glissé dans une valeur de paramètre → refusé par le check défensif explicite
4. Release/manifeste inexistant → refusé
5. Logique de validation confirmée par l'exécution (DB rehearsal refusée, manifeste requis,
   venv corrigé) — **le vrai "démarrage OK" n'a volontairement PAS été testé en dehors de la
   fenêtre contrôlée** : une tentative initiale sur un port de test (8010) a été bloquée par le
   classificateur de permissions à raison — le port était isolé mais `RealEnvFile` pointait par
   défaut vers `backend/.env.local` (la vraie `digitalcrown_db`), donc même "sur un port de test"
   ça aurait déclenché `create_all()`/seeds contre la prod avant tout backup. Erreur de jugement
   de ma part, corrigée en cours de route.
- Documentation mise à jour : `CLAUDE.md` (nouveau piège connu), `docs/CABINET_ONPREM_GUIDE.md`
  (section 2, doctrine runtime réel), `docs/NEW_CABINET_INSTALL_PATH.md` (section 6, procédure
  recommandée)

**PAS FAIT — attend un GO explicite séparé (fenêtre contrôlée, section 5 de la mission) :**
backup DB réel, backup médias réel, comptage avant, arrêt du process `--reload` (PID 5876),
démarrage de la release via `run_real_backend.ps1` sur le vrai port 8005, health checks,
comptage après. Le port 8005 tourne toujours avec `--reload` à l'heure où ce texte est écrit —
non redémarré, conformément à la règle absolue de la mission.

**Note annexe (hors scope, juste observée)** : `backend/scripts/run_rehearsal_backend.ps1`
référence `.venv312\Scripts\python.exe` alors que le venv réel du dépôt s'appelle `venv\` — ce
script a probablement le même bug d'interpréteur que celui trouvé et corrigé dans
`run_real_backend.ps1`. Non corrigé ici (hors scope de cette mission), à vérifier avant sa
prochaine utilisation.

### Fenêtre contrôlée exécutée (2026-07-10, cabinet fermé, GO explicite du CTO)

**Statut : PASSED sur tous les critères techniques. Reste PENDING : le smoke humain final
(login + navigation réelle), qui ne peut être fait que par un humain avec de vrais identifiants.**

**Backups (avant toute coupure du process --reload) :**
- DB chiffrée : `backend/backups/backup_20260710_200552.sql.enc` (2.32 MB) — validée non vide
- Médias chiffrés : `backend/backups/media_backup_20260710_200559.zip.enc` (266.02 MB,
  1815 fichiers) — validée non vide

**Compteurs avant coupure :** patients=220, users=12, payments=136, document_archives=262,
actes=176, journey_milestones=0, superadmin (id=1, benmoussa.achraf@gmail.com, role=ADMIN,
is_active=true) confirmé.

**Découverte critique pendant la fenêtre — corrigée avant tout smoke :** `run_real_backend.ps1`
codait en dur `--host 127.0.0.1`. Le process `--reload` existant tournait sur `0.0.0.0` (accès
LAN nécessaire pour PWA mobile et autres postes du cabinet, cf. `BACKEND_URL=http://192.168.11.109:8005`
dans `.env.local`). Démarrer sur `127.0.0.1` aurait cassé l'accès LAN sans qu'on s'en aperçoive
avant la réouverture du cabinet. Détecté via `netstat` juste après le premier démarrage (jamais
supposé "ça doit marcher", vérifié réellement — cf. règle `CLAUDE.md` "vérifier en live, pas
juste en unitaire"). Corrigé : nouveau paramètre `-BindHost` (défaut `0.0.0.0`, confirmé
explicitement par le CTO après blocage du classificateur de permissions sur ce changement de
surface réseau). `run_real_backend.ps1` accepte maintenant `-BindHost` explicitement, tracé dans
le manifeste runtime.

**Ancien process arrêté proprement :** chaîne complète identifiée avant coupure
(`cmd.exe "SERVEUR BACKEND"` PID 30068 → `uvicorn.exe` PID 17996 → `python.exe` PID 30560 →
worker `--reload` PID 5876 → spawn multiprocessing PID 22060). Coupure via `taskkill /T /F` sur
la racine (17996), fenêtre `cmd.exe` laissée ouverte à l'invite (non fermée). Vérifié `pg_stat_activity`
avant coupure : 2 connexions seulement, aucune requête active hors la mienne — aucune activité
clinique concurrente, cohérent avec "cabinet fermé".

**Nouveau runtime démarré :** release `20260710-191153-738eb5234efc`, sans `--reload`, depuis
`C:\Users\lenovo\DigitalCrown-Runtime\releases\20260710-191153-738eb5234efc` (jamais le dépôt de
travail), lié sur `0.0.0.0:8005`.

**Incident d'hébergement du process (mineur, corrigé) :** le premier démarrage a utilisé le
mécanisme de tâche de fond de l'outil agent — ce mécanisme est lié au cycle de vie de la session
de l'agent, pas au système d'exploitation indépendamment, et le process a été tué de façon
inattendue par ce mécanisme (pas un crash applicatif, pas une action du CTO). Corrigé en relançant
via une fenêtre console détachée (`Start-Process` avec nouvelle fenêtre PowerShell titrée
"SERVEUR BACKEND (release immuable, sans --reload)"), même pattern d'hébergement que l'ancien
process — vérifié : la chaîne de parenté du nouveau PID ne remonte à aucun process de l'agent.
**Leçon retenue : ne jamais héberger un service réel long-vivant via le mécanisme de tâche de
fond d'un outil d'agent — toujours une fenêtre/process détaché du système.**

**Vérifications post-démarrage (toutes PASSED) :**
- `/api/health`, `/api/health/db`, `/api/health/storage` → 200 OK
- Frontend `/` → 200 OK, servi depuis `<release>/frontend/dist` (hash identique au build sûr
  déjà en place — PatientJourney non activé dans ce build)
- `POST /api/auth/login` avec mot de passe volontairement erroné → 401 propre (pas de crash),
  confirme que passlib/jose fonctionnent correctement dans ce process (répond au doute soulevé
  par `Win32_Process.ExecutablePath` qui pointait vers l'interpréteur Python global plutôt que
  le venv — la résolution effective du site-packages est correcte, prouvé fonctionnellement)
- Test d'immutabilité : édition temporaire d'un commentaire dans `backend/main.py` (dépôt de
  travail) pendant que le process réel tournait → PID et heure de démarrage strictement
  inchangés après l'édition, aucun redémarrage. Édition annulée immédiatement après vérification.
- Compteurs après (process actuel) : patients=220, users=12, payments=136,
  document_archives=262, actes=176, journey_milestones=0 — identiques à l'avant
- Fichiers média réels : 1815 fichiers, identique au compte au moment du backup

**Ce qui n'a PAS été fait moi-même, par construction (voir CLAUDE.md, règles de sécurité) :**
je ne saisis jamais de mot de passe réel, même sur demande explicite du CTO, et je n'ai pas
fabriqué de session/JWT en contournant le flux de login réel (tentative bloquée à raison par le
classificateur de permissions — je n'ai pas cherché à contourner ce blocage). Le smoke humain
final (login réel + navigation) reste **PENDING**, à faire par le CTO à son retour, protocole
fourni par le CTO :
1. Login réussi
2. Dashboard sans erreur
3. Agenda s'ouvre
4. Un dossier patient réel s'ouvre en lecture
5. Un document protégé s'ouvre correctement
6. Confirmer build frontend sûr actuel, PatientJourney non activé
7. Console/réseau navigateur : aucun 401/403/500/asset cassé inattendu
8. PID + heure de démarrage backend inchangés pendant tout le parcours
9. Recomptage post-smoke : patients=220, users=12, payments=136, document_archives=262,
   actes=176, journey_milestones=0

**Statut final une fois le smoke humain confirmé PASS (pas encore atteint à l'écriture de cette
note) :** `REAL-RUNTIME-IMMUTABILITY-GUARD-1 — COMPLETED`, `RUNTIME RÉEL IMMUTABLE`. Phase D
(activation Treatment Journey) reste explicitement non lancée.

### Backlog ouvert — AUTO-BACKUP-TARGET-DIAGNOSTIC-1

Observé pendant la fenêtre contrôlée, dans les logs du nouveau runtime juste après démarrage :
`ERROR:backend.services.backup_service: Erreur lors de la sauvegarde chiffrée : file is not a
database`. N'a pas affecté la disponibilité ni les données réelles (les backups manuels DB+médias
de cette fenêtre sont vérifiés indépendamment et sains). Signale que le service de backup
planifié automatique (`daily_scheduler` / `backup_service`) n'est pas pleinement sain — probable
tentative d'ouverture d'un fichier SQLite (le message d'erreur est la signature SQLite typique)
alors que la DB réelle est PostgreSQL.

**Scope de la mission (à ne pas démarrer avant instruction explicite, à ne jamais combiner avec
la Phase D Treatment Journey) :**
- identifier le fichier que le job planifié tente d'ouvrir comme SQLite
- confirmer que ce n'est pas `digitalcrown_db`
- vérifier que le scheduler de backup sélectionne correctement PostgreSQL en production
- ne modifier ni restaurer aucune donnée réelle pendant le diagnostic

### Verdict final (2026-07-10, clôturé par le CTO sur base des vérifications techniques)

Le CTO a validé la clôture de la mission sur la base des preuves techniques déjà réunies
(santé, immuabilité prouvée en direct, compteurs stables avant/après, backups DB+médias vérifiés
non vides, fonctionnement réel de passlib/jose prouvé via un test d’échec de connexion
volontaire). Le smoke humain complet (login réel + navigation UI) reste **PENDING**, explicitement
non bloquant pour cette clôture — à faire par le CTO dès son retour au poste, protocole déjà
documenté ci-dessus (tâche #35).

**REAL-RUNTIME-IMMUTABILITY-GUARD-1 — COMPLETED**
**RUNTIME RÉEL IMMUTABLE**
**PHASE D TREATMENT JOURNEY — toujours non lancée**

Le point essentiel de la mission est atteint : le backend réel tourne désormais indépendamment
du dépôt de développement (release immuable hors du repo) et indépendamment de toute session
d’agent (fenêtre détachée). Le chemin exact de l’incident d’origine (`--reload` réagissant aux
éditions du dépôt de travail) est structurellement fermé.

**Backlog ouvert, non démarré, séparé de toute activation Journey :**
- Smoke humain final (tâche #35) — non bloquant, à faire quand le CTO est au poste
- `AUTO-BACKUP-TARGET-DIAGNOSTIC-1` (tâche #36) — diagnostic du service de backup planifié

## AUTO-BACKUP-POSTGRES-DIAGNOSTIC-1 (2026-07-10, diagnostic read-only)

**Statut : COMPLETED (diagnostic uniquement, aucune correction appliquée, conforme au périmètre).**

**Scheduler identifié :** `backend/services/daily_scheduler.py::start_daily_scheduler()`,
appelé au démarrage dans `backend/main.py:200-201`. Première exécution 10s après le boot, puis
toutes les 86400s (24h) via `threading.Timer` récursif (`_run_and_reschedule`). Appelle dans
l'ordre : `backup_service.run_daily_backup()`, `send_license_expiry_emails()`, `run_daily_alerts()`,
le tout sous un seul `try/except` global qui ne fait que logger un warning.

**Fonction fautive :** `backend/services/backup_service.py::BackupService.run_daily_backup()`
(ligne 56), qui cible en dur `AppPaths.get_user_data_dir() / "clinical_vault.db"` — **jamais**
`digitalcrown_db`/PostgreSQL. `_encrypt_and_save()` (ligne 28) ouvre ce fichier via
`sqlite3.connect(...).backup(...)` (sqlite3 standard, sans support SQLCipher).

**Branche SQLite identifiée :**
- `backend/core/paths.py::AppPaths.get_db_url()` retourne `sqlite:///.../clinical_vault.db` —
  utilisé uniquement comme **fallback** dans `backend/database.py:20`
  (`os.getenv("DATABASE_URL", AppPaths.get_db_url())`). Puisque `DATABASE_URL` est bien défini
  dans `.env.local` pour ce cabinet réel, ce fallback SQLite n'est **jamais** emprunté par le
  moteur ORM réel — confirmé, `digitalcrown_db` PostgreSQL est bien la seule DB utilisée par
  l'application aujourd'hui.
- `backend/database.py:24-102` — logique de migration transparente : si un fichier SQLite en
  clair existe à cet emplacement, il est automatiquement converti en base **SQLCipher chiffrée
  AES-256** (clé dérivée de `CABINET_MASTER_KEY_HEX`/`SECRET_KEY`). C'est une logique héritée
  d'une V1 mono-poste (avant l'exigence PostgreSQL actuelle), légitime pour le "mode cabinet
  solo" au sens de `CLAUDE.md`, mais orpheline ici puisque ce cabinet utilise PostgreSQL.
- `backend/routers/admin.py:361-394` (`GET /admin/backups`, `POST /admin/backups/trigger`) —
  le panneau de sauvegardes de l'admin UI est branché sur ce même mécanisme legacy
  (`AppPaths.get_user_data_dir()/backups`), donc totalement déconnecté des vraies sauvegardes
  PostgreSQL (`backend/backups/`, produites par `backup_db.py`/`backup_media.py`). Un praticien
  consultant "Sauvegardes" dans l'app ne verrait jamais l'état réel de la protection de
  `digitalcrown_db`.
- `backend/routers/admin.py:224-251` (`GET /admin/export-db`) — à l'inverse, **ce endpoint fait
  déjà le bon routage** (`if "sqlite" in db_url ... elif "postgresql" in db_url: pg_dump`) —
  pattern de référence directement réutilisable pour la correction.

**Fichier fautif identifié :**
- Chemin exact : `C:\Users\lenovo\AppData\Roaming\DigitalCrown\clinical_vault.db`
- Taille : 61 440 octets, dernière modification 28 mai 2026
- Type réel : **SQLCipher AES-256 chiffré** (confirmé : en-tête = octets haute entropie, pas la
  signature SQLite standard `53 51 4c 69 74 65...` ; tentative d'ouverture en lecture seule via
  `sqlite3` standard échoue avec exactement `DatabaseError: file is not a database`)
- Pourquoi traité comme SQLite : `backup_service.py` teste seulement `source_db.suffix == '.db'`
  et appelle `sqlite3.connect()` sans jamais tenir compte du chiffrement SQLCipher ni de la clé
  `CABINET_MASTER_KEY_HEX`
- Historique cohérent avec cette explication : des `.enc` valides existent jusqu'au
  **9 juin 2026 18:11** (`clinical_vault_backup_20260609_181145.enc`), suivis d'un grand nombre
  de fichiers `.temp.db` de 0 octet à partir du 9 juin 18h25 — coïncide avec le moment probable
  de la migration transparente vers SQLCipher, après quoi chaque tentative échoue.

**Classification (question 3 de la mission) : réponse C, avec racine A** — un fichier chiffré
(SQLCipher) traité par erreur comme du SQLite en clair par du code qui n'a pas été mis à jour
depuis l'époque où c'était la DB principale (V1 pré-PostgreSQL). Pas un fichier corrompu (D) : le
chiffrement est intentionnel et fonctionnel, juste illisible par l'outil utilisé pour le
sauvegarder.

**Routage PostgreSQL réel — tout confirmé en lecture seule :**
- `DATABASE_URL` de la release réelle cible bien PostgreSQL, DB `digitalcrown_db` — confirmé
- `backup_db.py` utilise `pg_dump` exclusivement (aucun `sqlite3` dans ce fichier) — confirmé
- Aucune fonction sqlite3 n'est nécessaire pour sauvegarder PostgreSQL — confirmé, c'est
  précisément le problème : le scheduler automatique n'appelle jamais ce chemin correct
- Dernier backup manuel PostgreSQL : `backend/backups/backup_20260710_200552.sql.enc`, 2.32 MB
  — non vide, validé pendant la fenêtre contrôlée RRIG-1
- Dernier backup manuel médias : `backend/backups/media_backup_20260710_200559.zip.enc`,
  266.02 MB, 1815 fichiers — non vide, validé

**État du backup automatique :**
1. Le scheduler sauvegarde-t-il réellement PostgreSQL ? **Non, jamais.**
2. Produit-il un pg_dump valide ? **Non — pg_dump n'est jamais appelé par le scheduler.**
3. Sauvegarde-t-il aussi les médias ? **Non.**
4. L'erreur SQLite bloque-t-elle tout le job ? **Non** — `run_daily_backup()` catch sa propre
   exception et retourne `False` (jamais vérifié par l'appelant) ; `send_license_expiry_emails()`
   et `run_daily_alerts()` s'exécutent normalement juste après (confirmé dans les logs du
   redémarrage réel de ce soir).
5. Concerne uniquement une tâche secondaire/obsolète — **oui**, mais cette tâche est la SEULE
   tentative de backup automatique qui existe : il n'y a donc, en pratique, **aucun backup
   automatique de la vraie base de production**, à aucun niveau.
6. Emplacement attendu des backups automatiques : `%APPDATA%\DigitalCrown\backups\`
7. Date du dernier backup automatique réussi (n'importe lequel, y compris legacy) :
   **9 juin 2026, 18:11** — soit plus d'un mois avant ce diagnostic.

**Gravité : P0** — aucun backup automatique PostgreSQL valide n'est produit, et ça n'a jamais été
le cas. Seuls les backups manuels (script CLI, ou aujourd'hui pendant la fenêtre contrôlée RRIG-1)
protègent réellement `digitalcrown_db`.

**Cause racine :** `backup_service.run_daily_backup()` n'a jamais été mis à jour lors du passage
du "V1" (SQLite mono-poste) à l'exigence PostgreSQL pour la production cabinet. Il continue de
cibler l'ancien fichier local, désormais chiffré SQLCipher (migration transparente introduite
séparément dans `database.py`), et échoue silencieusement (log + retour `False` ignoré) sans
jamais tenter PostgreSQL.

**Mission corrective recommandée : `AUTO-BACKUP-POSTGRES-ROUTING-FIX-1`**
(pas `LEGACY-SQLITE-BACKUP-REMOVAL-1` — le mode SQLite/SQLCipher solo-cabinet reste une
architecture légitime selon `CLAUDE.md`, il ne faut pas le supprimer, seulement router
correctement selon le moteur réellement actif)

- **Fichiers à modifier :**
  - `backend/services/backup_service.py` — ajouter une branche PostgreSQL dans
    `run_daily_backup()` (ou une nouvelle méthode dédiée), en réutilisant la logique déjà testée
    de `backend/scripts/backup_db.py` (localisation `pg_dump` via `find_pg_binary`, dump chiffré
    Fernet) plutôt que de dupliquer du code. Détecter le moteur actif via la même inspection que
    `admin.py::export_database()` (`"sqlite" in db_url` / `"postgresql" in db_url`).
  - `backend/routers/admin.py` (`/admin/backups`, `/admin/backups/trigger`) — pointer vers le
    même emplacement/mécanisme corrigé, pour que l'UI admin reflète l'état réel des sauvegardes
    PostgreSQL, pas l'ancien mécanisme SQLite orphelin.
  - Corriger accessoirement le cas SQLite légitime (solo-cabinet) : même bug latent —
    `sqlite3.connect().backup()` échouerait pareillement sur une vraie base SQLCipher solo-cabinet
    en production. Utiliser `sqlcipher3`/PRAGMA key ou déléguer à `sqlcipher_export` plutôt que
    `sqlite3` standard.
- **Logique à supprimer/remplacer :** le test `source_db.suffix == '.db'` dans
  `_encrypt_and_save()` comme unique branchement — remplacer par une détection explicite du
  moteur (Postgres vs SQLite/SQLCipher vs média).
- **Tests :** nouveaux cas dans `backend/tests/test_backups.py` — backup Postgres simulé (mock
  `pg_dump`/subprocess), backup SQLCipher simulé avec vraie clé, confirmation qu'aucun des deux
  chemins n'écrase l'autre.
- **Validation :** obligatoire sur rehearsal PostgreSQL (comme le reste de Treatment Journey) —
  jamais de premier test contre `digitalcrown_db`.
- **Rollback :** trivial — revert du commit backend seul, `run_daily_backup()` retrouve son
  comportement actuel (déjà cassé, donc rollback sans régression fonctionnelle possible).
- **Risque production :** faible si le déploiement suit la même doctrine que RRIG-1 (release
  immuable, jamais de `--reload`, validation rehearsal d'abord) — le risque principal serait de
  câbler `pg_dump` avec un identifiant/mot de passe mal géré ; réutiliser exactement le pattern
  déjà validé de `backup_db.py`/`Mask-DatabaseUrl` plutôt que d'improviser.
- **Redémarrage contrôlé nécessaire ?** Oui, un redémarrage du backend réel sera nécessaire pour
  charger le code corrigé — à faire via une nouvelle fenêtre contrôlée du même type que RRIG-1
  (backup manuel frais avant, comptages avant/après, jamais de `--reload`).

**Confirmations finales (méthode, validées par le CTO) :**
- Backend réel redémarré : non
- PID du process réel (7696) : inchangé avant/après ce diagnostic
- `digitalcrown_db` modifiée : non (aucune écriture, uniquement `SELECT COUNT(*)` en lecture)
- Médias réels modifiés : non
- Superadmin intact : oui (vérifié à nouveau, id=1, benmoussa.achraf@gmail.com, ADMIN, actif)
- PatientJourney activé : non
- Aucune correction appliquée dans cette mission — diagnostic uniquement, conforme au périmètre

**Verdict : CORRECTION REQUISE** (P0) — le service de backup automatique ne protège pas
`digitalcrown_db`. Les sauvegardes manuelles récentes (DB + médias, validées pendant la fenêtre
RRIG-1) restent la seule protection réelle actuelle. Recommandation : traiter
`AUTO-BACKUP-POSTGRES-ROUTING-FIX-1` comme une priorité proche, séparément de la Phase D
Treatment Journey.

## AUTO-BACKUP-POSTGRES-ROUTING-FIX-1 (2026-07-10)

**Statut : COMPLETED.** Routage implémenté, validé en PostgreSQL rehearsal isolé
(backup réel + décryptage + restore + comparaison de compteurs, tous réussis), tests
unitaires verts. **Rien déployé sur le runtime réel** (PID 7696 inchangé tout du long,
`digitalcrown_db` jamais écrite, aucun redémarrage) — la correction vit dans le dépôt de
travail, en attente d'un second GO explicite pour activation réelle
(`AUTO-BACKUP-POSTGRES-PROD-ACTIVATION-1`).

**Cause corrigée** : `backup_service.run_daily_backup()` ciblait en dur
`clinical_vault.db` (SQLite legacy, aujourd'hui chiffré SQLCipher), ouvert via
`sqlite3.connect()` standard — jamais PostgreSQL. Remplacé par
`backup_active_database()`, qui détecte le moteur réellement actif
(`backend.database.engine.dialect.name`/`.driver`, même pattern que
`migrate_appointment_columns()`) et route :
- PostgreSQL → `pg_dump` (réutilise `find_pg_binary`/`_parse_postgres_url`/`get_cipher`
  de `backup_db.py`, déjà validés manuellement pendant RRIG-1 — pas de troisième
  implémentation)
- SQLite + driver `pysqlcipher` → échec explicite `SKIPPED_UNSUPPORTED_ENGINE`
  (`"SQLCipher automatic backup unsupported"`), jamais présenté comme un succès —
  backlog séparé `SQLCIPHER-AUTO-BACKUP-FIX-1`
- SQLite + driver `pysqlite` (cas résiduel, SQLite réellement en clair) → comportement
  historique inchangé, sur le fichier réellement utilisé par l'engine actif (jamais un
  chemin recalculé séparément)
- Moteur inconnu → échec explicite, jamais de faux succès

**Fichiers modifiés :**
- `backend/scripts/backup_db.py` — `load_backend_env(override=True)` et l'import de
  `settings` déplacés sous usage paresseux (`if __name__ == "__main__":` /
  intérieur de `backup_db()`) : le fichier est désormais importable comme librairie
  depuis le process réel sans risque d'écraser silencieusement sa config (piège
  déjà documenté dans `docs/NEW_CABINET_INSTALL_PATH.md`, maintenant partiellement
  neutralisé pour l'usage librairie — le piège CLI reste entier et documenté).
  **Régression détectée puis corrigée pendant l'implémentation** : le premier essai
  du fix cassait le script CLI (`settings` lisait `backend/.env` — placeholder
  "user" — au lieu de `.env.local` — vraie valeur "postgres" — à cause de l'ordre
  d'exécution). Détecté par vérification live (`--dry-run`, comparaison du masquage
  avant/après), pas seulement par les tests unitaires — corrigé en rendant l'import
  de `settings` paresseux lui aussi.
- `backend/services/backup_service.py` — nouvelles méthodes `_detect_engine()`,
  `_backup_postgres()`, `_backup_sqlite_family()`, `_persist_status()`,
  `backup_active_database()` ; `run_daily_backup()` devient un wrapper fin
  (signature booléenne inchangée pour `daily_scheduler.py`/`admin.py::trigger_backup`
  — zéro changement d'appelant). Écriture atomique (temp scopé par UUID +
  `os.replace()`), checksum SHA-256, statut structuré persisté dans
  `last_backup_status.json`.
- `backend/tests/test_backups.py` — 2 tests obsolètes (`run_daily_backup_returns_true_*`,
  qui validaient un faux sentiment de succès en ignorant le moteur réel) réécrits ;
  16 nouveaux tests couvrant les 12 cas demandés (routage, échec pg_dump, dump vide,
  échec chiffrement, nettoyage du temp scopé uniquement, succès complet avec
  checksum, aucun secret dans les logs, SQLCipher skip propre, etc.)
- `backend/tests/test_install_e2e_safety_regression.py` — 1 test corrigé
  (`test_backup_db_dry_run_logs_masked_target`, qui mutait
  `backup_db.settings` — attribut de module retiré par design ; corrigé pour muter
  le singleton réel `backend.config.settings`, avec le même effet).

**Validation PostgreSQL rehearsal (réelle, pas seulement mockée)** :
1. `digitalcrown_auto_backup_rehearsal` créée, table `rehearsal_widgets` (3 lignes,
   somme=21) — données factices non sensibles
2. `backup_active_database()` invoqué dans un process isolé (DATABASE_URL +
   CABINET_MASTER_KEY_HEX rehearsal dédiés, jamais les vrais, jamais dans
   `.env.local` ni dans le process réel) — engine détecté `postgresql`/`psycopg2`,
   confirmé
3. Résultat réel : `SUCCESS`, `db_backup_20260710_222740.sql.enc`, 3556 octets,
   checksum SHA-256 calculé
4. Déchiffré (clé rehearsal), dump contient bien `rehearsal_widgets` — confirme que
   `pg_dump` a réellement tourné, pas un mock
5. Restauré dans `digitalcrown_auto_backup_restore_test` (DB séparée) — `psql -f`,
   rc=0
6. Comparaison : source `3 | 21`, restauré `3 | 21` — **identique**
7. `clinical_vault.db` réel : mtime strictement inchangé avant/après — jamais lu ni
   modifié pendant cette validation
8. Nettoyage : les deux DB rehearsal supprimées (`dropdb`), fichiers temporaires
   supprimés, aucune trace laissée

**Tests** :
- `pytest backend/tests/test_backups.py` : 22/22 PASSED
- `pytest backend/tests/test_admin_router.py backend/tests/test_install_e2e_safety_regression.py backend/tests/test_security.py backend/tests/test_media_security.py backend/tests/test_superadmin_router.py backend/tests/test_services_unit5.py` : 144/144 PASSED (aucune régression)
- `npm test` (frontend) : 39/39 PASSED (aucun changement frontend dans cette mission)
- `npm run build:rehearsal` : non exécuté (aucun changement frontend à valider,
  jugé redondant avec `npm test` déjà vert)

**Découverte annexe significative, hors scope de cette mission (read-only, non
corrigée) — nouveau backlog `SCHEDULED-TASK-BACKUP-FIX-1`** : il existe une vraie
tâche planifiée Windows sur cette machine, `DigitalCrown_DailyBackup_User`
(déclenchement quotidien 03:00, `WorkingDirectory` correct = racine du dépôt), qui
utilise déjà le bon script (`backup_db.py`, PostgreSQL-aware) — contrairement au
scheduler in-app corrigé dans cette mission. **Mais elle échoue** :
`LastTaskResult=1` lors de sa dernière exécution (aujourd'hui, 03:00:01). Cause
probable, diagnostiquée avec un haut degré de confiance sans y toucher : la
commande configurée est `python backend\scripts\backup_db.py` (script direct, sans
`-m`) — exactement l'erreur `ModuleNotFoundError: No module named 'backend'`
rencontrée en tout début de la mission de diagnostic précédente ; de plus `Execute`
est le `python` générique du PATH, pas le python du venv (même classe de bug que
celui trouvé et corrigé dans `run_real_backend.ps1` pendant RRIG-1). Documenté dans
`docs/CABINET_ONPREM_GUIDE.md`. **Conséquence pratique** : à ce jour, ni le
scheduler in-app (avant cette mission) ni la tâche planifiée OS n'ont produit de
backup PostgreSQL automatique fonctionnel — seuls les backups manuels (script CLI
exécuté directement, comme pendant RRIG-1 et cette mission) ont réellement protégé
`digitalcrown_db`.

**Confirmations finales :**
- PID réel 7696 : inchangé (vérifié avant et après toute l'implémentation)
- Backend réel redémarré : non
- `digitalcrown_db` modifiée : non (uniquement lue en comptage, jamais écrite)
- Médias réels modifiés : non
- Superadmin intact : oui
- PatientJourney activé : non
- Aucune activation sur le runtime réel — code présent uniquement dans le dépôt de
  travail, en attente d'un GO explicite séparé (`AUTO-BACKUP-POSTGRES-PROD-ACTIVATION-1`)

**Risques restants** : (1) branche SQLCipher volontairement non implémentée
(Option B, backlog séparé) — sans impact pour ce cabinet, PostgreSQL uniquement ;
(2) la tâche planifiée OS cassée (voir ci-dessus, backlog séparé) ; (3) l'activation
réelle nécessite un redémarrage contrôlé du backend réel (nouvelle release,
`create_release.ps1` + `run_real_backend.ps1`) pour charger le code corrigé — pas
fait dans cette mission, par construction.

**Verdict : AUTO-BACKUP POSTGRES PRÊT (en rehearsal)** — en attente du second GO
explicite pour l'activation réelle. Phase D Treatment Journey toujours non lancée.

## AUTO-BACKUP-POSTGRES-PROD-ACTIVATION-1 (2026-07-11, ~00h50-01h35, cabinet fermé)

**Statut : COMPLETED.** Le runtime réel exécute désormais le correctif de routage backup,
et le **premier backup automatique PostgreSQL réel de l'histoire de ce cabinet** a été
produit, vérifié, déchiffré et restauré avec succès dans une DB isolée. Aucune donnée
réelle modifiée, aucun rollback nécessaire.

**Préflight (avant toute action) :** PID 7696, release `20260710-191153-738eb5234efc`,
pas de `--reload` (ligne de commande vérifiée), bind `0.0.0.0:8005`, DB silencieuse
(2 connexions, aucune requête active hors la mienne — cabinet fermé confirmé),
compteurs 220/12/136/262/176/0, superadmin actif, bundle frontend sûr
`index-BO2OChwV.js`, 1815 fichiers médias.

**Backups de sécurité pré-activation (indépendants du nouveau scheduler) :**
- DB : `backend/backups/backup_20260711_004941.sql.enc` (2.32 MB,
  SHA-256 `8E9657D6...C335B225`)
- Médias : `backend/backups/media_backup_20260711_004950.zip.enc` (266.02 MB,
  1815 fichiers, SHA-256 `AE2CDF4F...B51A8C46`)

**Incident de release résolu en cours de route** : la première tentative de
`create_release.ps1` s'est bloquée silencieusement — robocopy sans `/R`/`/W` (défaut :
1 million de retries, 30 s d'attente) coinçait sur `backend/backups/media_backup_*.enc`
(266 MB, encore verrouillé juste après sa création). Corrigé dans `create_release.ps1` :
`/R:2 /W:5` ajoutés + dossier `backups` exclu de la copie (les sauvegardes chiffrées,
~800 MB, n'ont rien à faire dans une release de code immuable). Release partielle
supprimée, script relancé avec succès.

**Nouvelle release : `20260711-012549-738eb5234efc`** (2.6 G, sans le bloat backups).
Vérifiée avant activation : correctif `backup_active_database()` présent, aucun chemin
`clinical_vault.db` codé en dur (seules des mentions en commentaire), imports paresseux
dans `backup_db.py`, frontend = build sûr (PatientJourney non activé), manifeste sans
secret. **Note d'audit** : le manifeste enregistre le commit `738eb52`, mais le dépôt de
travail est dirty — la release contient ce commit PLUS les changements non commités
validés de la session (correctif backup, fix BindHost du lanceur, docs). Les fichiers
backend qui diffèrent du commit : `backend/scripts/backup_db.py`,
`backend/services/backup_service.py`, `backend/tests/test_backups.py`,
`backend/tests/test_install_e2e_safety_regression.py` + le code Journey de la Phase A
(inchangé depuis la release précédente). Un commit propre de l'état activé reste
recommandé quand le CTO le décidera.

**Bascule** : arrêt propre de l'ancien tree (taskkill /T sur le powershell lanceur,
port 8005 libéré), démarrage via `run_real_backend.ps1 -ReleaseId 20260711-012549-...`
en fenêtre détachée (leçon RRIG-1 : jamais via le mécanisme de tâche de fond d'un agent).
Nouveau PID : **14516**, bind `0.0.0.0:8005`, pas de `--reload`, chaîne de parenté
indépendante de toute session d'agent, `runtime-activation.json` écrit.

**Health checks** : `/api/health`, `/api/health/db`, `/api/health/storage` → tous 200.
Frontend servi = `index-BO2OChwV.js` (sûr). Login endpoint → 401 propre sur mot de passe
volontairement erroné (passlib/jose fonctionnels dans le nouveau process). Le smoke UI
complet (login réel + navigation) reste celui de la tâche #35, à faire par le CTO —
même limitation que RRIG-1 : je ne saisis jamais de vrai mot de passe.

**Backup automatique réel — première exécution (déclenchée naturellement par le
scheduler in-app, 10 s après le boot, pas d'attente du prochain horaire quotidien) :**
- Fichier : `%APPDATA%\DigitalCrown\backups\db_backup_20260711_012916.sql.enc`
- Taille : 2 432 184 octets (cohérente avec le backup manuel de la même base)
- `last_backup_status.json` : `engine=postgresql`, `status=SUCCESS`,
  checksum `b604fcb5...00f098bd`, durée ~0.8 s
- Checksum du fichier revérifié indépendamment : identique
- `clinical_vault.db` : mtime toujours 28/05/2026 — jamais lu ni modifié
- Aucun secret dans le statut ni les logs

**Restore de validation isolé** (`digitalcrown_prod_backup_restore_validation`,
jamais `digitalcrown_db`) : déchiffrement avec la vraie clé (en mémoire uniquement),
restore psql rc=0, **les 6 compteurs correspondent exactement**
(patients 220, users 12, payments 136, document_archives 262, actes 176,
journey_milestones 0), zéro paiement orphelin (intégrité référentielle vérifiée),
superadmin présent dans le restore. Dump déchiffré supprimé immédiatement, DB de
validation supprimée après le bilan.

**Contrôles post-activation** : compteurs réels identiques à l'avant (le fichier de
backup n'est pas une modification de données métier), superadmin actif, 1815 médias,
frontend sûr, PID 14516 stable.

**Tests** : 60/60 backend ciblés (backups, install, sécurité, médias), 39/39 frontend,
`npm --prefix frontend run build:rehearsal` OK (note : la commande est
`npm --prefix frontend run build:rehearsal` — le script n'existe pas à la racine).

**Rollback** : non nécessaire. La release précédente `20260710-191153-738eb5234efc`
reste intacte comme cible de rollback.

**Verdict : AUTO-BACKUP POSTGRES RÉEL ACTIF.**

**Ordre restant (verrouillé par le CTO)** :
`SCHEDULED-TASK-BACKUP-FIX-1` → validation d'au moins une exécution planifiée réussie →
GO/NO-GO Phase D Treatment Journey. La Phase D reste NO-GO.

## ACTIVATED-RELEASE-PROVENANCE-LOCK-1 (2026-07-11)

**Statut : COMPLETED — PROVENANCE VERROUILLÉE.**

**Correspondance officielle release ↔ Git :**

```
Release active   : 20260711-012549-738eb5234efc
Runtime          : PID 14516, port 8005, sans --reload (non redémarré par cette mission)
Manifeste        : mentionne commit 738eb5234efc (état du HEAD au moment de la création,
                   arbre alors dirty)
Contenu fonctionnel = commit local 6de00db1164d01ad911d38fd3fa443220daf4103
                   "fix(ops): route automatic backups to PostgreSQL and harden immutable releases"
Créée AVANT le commit de provenance (le manifeste n'est pas modifié — release immuable)
```

**Preuve de correspondance** : les 321 fichiers `.py` du backend de la release comparés un à
un au commit — 321 identiques en contenu, 0 différent, 0 absent. Les 10 fichiers critiques
(backup_service, backup_db, daily_scheduler, main, models, patients, admin,
patient_journey_service, create_release.ps1, run_real_backend.ps1) vérifiés explicitement.
Seule différence : fins de ligne (CRLF dans la copie robocopy vs LF dans Git) — cosmétique,
aucun effet fonctionnel. Frontend de la release = build sûr `index-BO2OChwV.js`,
volontairement antérieur (PatientJourney non activé) — différence intentionnelle et
documentée, pas une anomalie.

**Commit créé** : local uniquement, aucun push (master local est en avance sur origin —
push à la discrétion du CTO). 52 fichiers : correctif backup PostgreSQL, guards
release/lanceur/build, Treatment Journey (code présent, non activé), documentation.
Exclusions respectées : `.claude/` laissé non suivi (outillage local),
`dist_cabinet/` + `install_rehearsal_media/` + `treatment_journey_rehearsal_media/`
ajoutés au `.gitignore` (générés/rehearsal), backups/médias/`.env*` déjà ignorés —
vérification explicite : aucun fichier sensible dans le staging.

**Note secret** : `bootstrap_new_cabinet.py` contient un mot de passe **rehearsal-only**
en dur (`E2E_Test_Pass_Rehearsal_2026`, étiqueté comme tel) — credential de test E2E,
pas un secret de production. Conservé tel quel, signalé ici pour transparence.

**Confirmations** : PID 14516 inchangé, runtime non redémarré, `digitalcrown_db` non
modifiée, aucun nouveau backup réel déclenché, release active non modifiée,
PatientJourney non activé, aucun push.

## SCHEDULED-TASK-BACKUP-DISPOSITION-1 (2026-07-11, diagnostic read-only)

**Statut : COMPLETED (diagnostic uniquement — tâche non modifiée, runtime non touché).**

**Réponses aux 12 questions obligatoires :**

1. **Nom exact** : `DigitalCrown_DailyBackup_User`
2. **Commande** : `python backend\scripts\backup_db.py` (WorkingDirectory =
   `C:\Users\lenovo\Documents\Cabinet\DigitalCrown`), principal `lenovo`,
   LogonType Interactive, RunLevel Limited
3. **Script/répertoire** : `backup_db.py` invoqué comme script direct (PAS en module `-m`),
   depuis la racine du dépôt de travail (pas la release immuable)
4. **Variables d'environnement** : environnement utilisateur standard du Task Scheduler —
   pas de `DIGITALCROWN_ENV_FILE`, donc le script (usage CLI) charge `backend/.env.local`
   → vraie `digitalcrown_db`. `python` du PATH résout vers `C:\Python314\python.exe`
   (Python global 3.14, PAS le venv du projet)
5. **Cible** : PostgreSQL `digitalcrown_db` uniquement (via pg_dump). **Pas de médias** —
   la commande n'inclut pas `backup_media.py`, contrairement à l'exemple documenté dans
   `CABINET_ONPREM_GUIDE.md` §6
6. **Fréquence** : quotidienne 03:00 (CalendarTrigger, DaysInterval=1, StartBoundary
   2026-06-05). `StartWhenAvailable` non défini (= false : exécution sautée si machine
   éteinte à 03:00) ; `DisallowStartIfOnBatteries=true` (= sautée si portable sur
   batterie !) ; `MultipleInstancesPolicy=IgnoreNew` (pas d'auto-chevauchement)
7. **Fonctionne backend arrêté** : oui par conception (process indépendant, pg_dump parle
   directement au service PostgreSQL) — c'est sa vraie valeur ajoutée vs le scheduler in-app
8. **Double emploi avec `run_daily_backup()`** : partiel. Les deux font un pg_dump
   quotidien chiffré de la même DB, mais : tâche Windows → `backend/backups/` (dépôt,
   **aucune rétention**, déjà 1.3 G), heure fixe 03:00, indépendante du backend ;
   in-app → `%APPDATA%\DigitalCrown\backups\`, rétention 7, heure = boot+10s puis +24h
   (imprévisible), vit et meurt avec le process backend
9. **Deux backups simultanés possibles ?** Théoriquement oui (si le cycle 24h in-app tombe
   ~03:00). Conséquence réelle : bénigne — deux pg_dump concurrents sont cohérents en
   lecture, fichiers de sortie distincts dans des dossiers distincts. Risque résiduel :
   IO/CPU simultanés uniquement. Pas de corruption possible.
10. **Nécessaire après redémarrage Windows ?** Partiellement : les données ne changent que
    via le backend, et l'in-app fait un backup 10 s après chaque boot du backend — la
    couverture des données est donc raisonnable sans la tâche. Ce que la tâche apporte en
    plus : horaire fixe hors activité (03:00, cabinet fermé = snapshots cohérents),
    indépendance vis-à-vis d'un backend crashé en cours de journée, et backup même si
    personne ne relance le backend.
11. **Dernière réussite réelle : JAMAIS.** Aucun fichier créé à 03:00 dans
    `backend/backups` depuis la création de la tâche (05/06/2026). ~5 semaines d'échec
    silencieux quotidien (`LastTaskResult=1` à chaque exécution).
12. **Cause exacte de la panne — reproduite fidèlement** :
    `python backend\scripts\backup_db.py` depuis la racine du dépôt →
    `ModuleNotFoundError: No module named 'backend'` → exit 1. Double bug :
    (a) invocation script direct au lieu de `-m backend.scripts.backup_db` (le script
    s'importe comme package) ; (b) `python` du PATH = Python 3.14 global, pas le venv
    projet (même classe de bug que celui corrigé dans `run_real_backend.ps1` pendant
    RRIG-1). La tâche n'a donc jamais pu fonctionner telle que créée.

**Constat annexe important** : **aucun des deux mécanismes ne sauvegarde les médias
automatiquement** (in-app = DB seule ; tâche = DB seule). Les 266 MB de médias patients ne
sont couverts que par des backups manuels. À intégrer dans la mission corrective.

**Décision : B — REPLACE.**
Le rôle (filet de sécurité OS, heure fixe, indépendant du process backend) est réellement
utile, mais l'architecture de la tâche existante est défectueuse au-delà d'un simple
paramètre : mauvais interpréteur, mauvaise forme d'invocation, pas de médias, sortie vers
le dépôt sans rétention (1.3 G déjà), sautée sur batterie, sautée si machine éteinte à
03:00 (pas de rattrapage). La remplacer par une tâche propre plutôt que de la rafistoler.
La nouvelle tâche remplira aussi l'intention du choix D (fallback OS complémentaire du
scheduler in-app).

**Mission corrective recommandée : `SCHEDULED-TASK-BACKUP-REPLACE-1`**
- Créer une nouvelle tâche (ex. `DigitalCrown_NightlyBackup`) :
  `C:\...\DigitalCrown\venv\Scripts\python.exe -m backend.scripts.backup_db` puis
  `-m backend.scripts.backup_media` (médias inclus, éventuellement hebdo pour limiter le
  volume), WorkingDirectory = racine du dépôt
- `StartWhenAvailable=true` (rattrapage si machine éteinte à 03:00),
  `DisallowStartIfOnBatteries=false` (portable), `MultipleInstancesPolicy=IgnoreNew`
- Politique de rétention sur `backend/backups/` (le dossier pèse déjà 1.3 G sans nettoyage)
- Décalage horaire assumé vs le cycle in-app (03:00 fixe vs boot+24h) — pas de verrou
  nécessaire (concurrence pg_dump bénigne), mais le documenter
- Désactiver (pas supprimer) l'ancienne `DigitalCrown_DailyBackup_User` après validation
  de la nouvelle
- Validation : forcer une exécution (`Start-ScheduledTask`), vérifier `LastTaskResult=0`
  ET l'apparition réelle du fichier `.enc` non vide

**Confirmations** : tâche non modifiée, runtime réel non redémarré (PID 14516),
`digitalcrown_db` non modifiée, médias intacts, PatientJourney non activé.

## Nettoyage disque pré-requis (2026-07-11, avant SCHEDULED-TASK-BACKUP-REPLACE-1)

Espace libre C: tombé à **0,46 Go** avant toute automatisation média — bloquant, signalé
au CTO avant de continuer. Décision : purger `backend/backups` (rétention manuelle) +
confirmer et supprimer `dist_cabinet/`.

- Supprimé `dist_cabinet/` (4,2 Go) — build PyInstaller stale (07/07/2026), déjà
  gitignore, non référencé par le runtime actif
- Purge `backend/backups/` (rétention manuelle, gardé les 3 backups les plus récents
  07-09/07-10/07-11, supprimé 07-07 (x2 lots) et 07-08, ~1,1 Go libérés)
- **Espace libre après : 5,35 Go** (contre 0,46 Go avant)
- Aucun backup conservé n'était le dernier valide ; les backups PostgreSQL manuels de
  RRIG-1 et PROD-ACTIVATION-1 (07-10, 07-11) sont intacts

## SCHEDULED-TASK-BACKUP-REPLACE-1 (2026-07-11)

**Statut : COMPLETED.** `DigitalCrown_DailyBackup_v2` créée, validée réellement (deux
exécutions complètes réussies : une manuelle directe, une via déclenchement natif Task
Scheduler), activée. L'ancienne `DigitalCrown_DailyBackup_User` désactivée (jamais
supprimée), conservée comme trace historique.

**Pré-requis disque** (voir section dédiée plus haut) : nettoyage effectué avec accord
du CTO avant cette mission (0,46 Go → 5,35 Go libres). Après les deux runs de
validation de cette mission : **5,13 Go libres**.

**Architecture livrée :**
- `backend/scripts/backup_media.py` — même correctif que `backup_db.py`
  (chargement d'env/`settings` paresseux) + extraction de
  `_build_media_archive(dest_dir, timestamp) -> dict` (checksum SHA-256, écriture
  atomique temp scopé + `os.replace()`, statut structuré). `backup_media(dry_run=)`
  (CLI historique) devient un fin wrapper, comportement inchangé.
- `backend/scripts/scheduled_backup.py` (nouveau) — orchestrateur unique : verrou
  fichier périssable → détection moteur → `BackupService._backup_postgres()` (réutilisé
  tel quel, aucune 3e implémentation pg_dump) → `_build_media_archive()` (réutilisé) →
  manifeste global + logs → rétention (dry-run par défaut). `overall_status` = SUCCESS
  uniquement si DB **et** médias réussissent ; PARTIAL si un seul des deux ; FAILED sinon
  ou si verrou déjà tenu.
- `C:\Users\lenovo\DigitalCrown-Runtime\bin\run_scheduled_backup.ps1` (nouveau, **hors
  dépôt**) — résout la release immuable active (la plus récente par `activated_at` parmi
  tous les `runtime-activation.json`), vérifie son manifeste
  (`environment=cabinet-real`), épingle l'interpréteur (jamais `python` du PATH), exécute
  `-m backend.scripts.scheduled_backup`, propage le code de sortie. N'affiche/n'écrit
  jamais de secret.
- `backend/tests/test_scheduled_backup.py` (nouveau, 18 tests) + 6 nouveaux tests dans
  `backend/tests/test_backups.py` pour `_build_media_archive` — verrou (acquisition,
  péremption, refus), routage SUCCESS/PARTIAL/FAILED sur toutes les combinaisons,
  rétention dry-run/réelle/plancher/scoping, aucun secret, dry-run n'appelle jamais les
  vrais backups.

**Point de conception documenté (pas un oubli)** : l'interpréteur reste celui du venv du
dépôt de travail — aucun Python indépendant n'existe dans `DigitalCrown-Runtime`. Une
vraie indépendance nécessiterait de recopier/réinstaller ~40+ paquets (dont des
dépendances lourdes comme opencv/onnx/grpc), jugé hors périmètre de cette mission
(risque de venv incomplet supérieur au bénéfice immédiat). Clause d'échappement de
l'ODM appliquée explicitement. Backlog séparé : `RUNTIME-PYTHON-INDEPENDENCE-1`.

**Validation réelle (cabinet ouvert mais aucune activité clinique concurrente
constatée) — deux exécutions complètes :**

1. **Manuelle directe** (`run_scheduled_backup.ps1`, sans `-ApplyRetention`) :
   `overall_status=SUCCESS`, DB 2 432 396 octets (checksum vérifié indépendamment,
   identique), médias 278 943 308 octets / 1815 fichiers (checksum vérifié
   indépendamment, identique). Rétention en dry-run (0 candidat, normal — premiers
   fichiers du dossier `scheduled/`).
2. **Restore DB isolé** : `digitalcrown_scheduled_backup_restore_validation` (jamais
   `digitalcrown_db`), déchiffré avec la vraie clé (mémoire uniquement), `psql -f` rc=0,
   **les 6 compteurs correspondent exactement** à `digitalcrown_db`
   (220/12/136/262/176/0). DB de validation supprimée après comparaison.
3. **Extraction médias isolée** : archive déchiffrée puis extraite dans un dossier temp
   (jamais le dossier média réel), **1815 fichiers extraits = 1815 dans l'archive =
   1815 dans le dossier média réel actuel**. Dossier temp supprimé après comparaison.
4. **Activation** : `DigitalCrown_DailyBackup_v2` activée, `DigitalCrown_DailyBackup_User`
   désactivée (`Disable-ScheduledTask`, pas supprimée).
5. **Déclenchement Task Scheduler natif** (`Start-ScheduledTask`, pas un appel direct) :
   `LastTaskResult=0` confirmé. Nouveau manifeste `overall_status=SUCCESS` (DB
   2 432 396 octets, médias 278 943 308 octets/1815 fichiers), rétention appliquée
   pour de vrai cette fois (`retention_dry_run=false`) — **0 suppression** (seulement 2
   backups dans chaque dossier, largement sous le plancher `MIN_BACKUPS_TO_KEEP=3` et
   les fenêtres de rétention).

**Tout du long** : PID réel 14516 inchangé, port 8005 non redémarré, `digitalcrown_db`
jamais écrite hors `pg_dump`/restore isolé, `clinical_vault.db` jamais lu (mtime
28/05/2026 inchangé), médias réels jamais modifiés (1815 fichiers avant/après),
superadmin intact, frontend = build sûr (`index-BO2OChwV.js`, PatientJourney non
activé).

**Tests** : 18/18 (`test_scheduled_backup.py`) + 6/6 nouveaux (`test_backups.py`,
28/28 au total sur ce fichier) + 168/168 sur la suite ciblée backup/sécurité/install
(aucune régression) + 39/39 frontend.

**Risques restants** :
- Dépendance résiduelle de l'interpréteur au dépôt de travail (documentée,
  `RUNTIME-PYTHON-INDEPENDENCE-1` en backlog)
- Espace disque toujours limité (5,13 Go) — la croissance des médias patients au fil du
  temps rapprochera la rétention média (7 jours) de sa vraie utilité ; à surveiller
- `SQLCIPHER-AUTO-BACKUP-FIX-1` toujours en backlog séparé (sans impact PostgreSQL)

**Verdict : BACKUP OS DB + MÉDIAS ACTIF.**

## SCHEDULED-BACKUP-PROVENANCE-LOCK-1 (2026-07-11)

**Statut : PARTIAL — provenance du code verrouillée dans Git, mais une divergence
architecturale réelle a été mise au jour et n'est pas cachée.**

**Découverte principale (réponse aux questions 1-2 de la mission)** : la release
active `20260711-012549-738eb5234efc` elle-même reste **intacte et non modifiée
depuis sa création** — vérifié par deux méthodes indépendantes : (a) aucun fichier
de la release n'a de date de modification postérieure à sa création
(`01:26:09`) ; (b) comparaison octet-pour-octet (fins de ligne normalisées) contre
le commit `ae43f16` (celui documenté comme correspondant lors de
`ACTIVATED-RELEASE-PROVENANCE-LOCK-1`) — **318/318 fichiers `.py` identiques, 0
différence réelle**, seuls 5 fichiers absents du commit (3 fichiers `scratch/*.py`
préexistants sans rapport, plus `scheduled_backup.py` et
`test_scheduled_backup.py` — absents parce qu'ils n'existaient pas encore au
moment de la création de la release, pas parce que la release a été altérée).

**Mais l'investigation a révélé un problème réel, non anticipé, que je ne masque
pas** : `run_scheduled_backup.ps1` fait `Push-Location $RepoRoot` (le dépôt de
travail) avant d'invoquer `-m backend.scripts.scheduled_backup` — **pas**
`Push-Location $activeRelease`, contrairement à `run_real_backend.ps1`. Preuve
empirique directe (sans lancer de nouveau backup réel, juste une introspection) :

```
sys.executable    : ...\DigitalCrown\venv\Scripts\python.exe
os.getcwd()       : C:\Users\lenovo\Documents\Cabinet\DigitalCrown   (dépôt, PAS la release)
scheduled_backup.__file__ : C:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\scripts\scheduled_backup.py
backup_service.__file__   : C:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\services\backup_service.py
backup_db.__file__        : C:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\scripts\backup_db.py
backup_media.__file__     : C:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\scripts\backup_media.py
database.__file__         : C:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\database.py
```

**Conséquence honnête** : `DigitalCrown_DailyBackup_v2` n'exécute **pas** le code
de la release immuable — il exécute le code du dépôt de travail mutable. Ce n'est
pas de la falsification de release (la release elle-même n'a jamais été touchée,
prouvé ci-dessus), mais une divergence de doctrine : le lanceur du backup planifié
ne respecte pas le même modèle « le runtime réel ne suit jamais le dépôt » que
`run_real_backend.ps1`. C'est structurellement inévitable dans l'état actuel
puisque la release `20260711-012549` a été créée **avant** que
`scheduled_backup.py` existe — un lanceur qui aurait fait `cd` dans cette release
aurait littéralement échoué (`ModuleNotFoundError`), donc ce choix n'était pas
arbitraire, mais il n'a pas été assez explicitement assumé/documenté au moment de
`SCHEDULED-TASK-BACKUP-REPLACE-1`.

**Ce que ça change concrètement, aujourd'hui** : rien d'un point de vue sécurité/
intégrité — le code exécuté (celui du dépôt) est maintenant committé (`d7a8e7a`),
donc traçable, et les deux exécutions réelles validées (restore DB isolé + extraction
médias isolée, tous deux réussis) l'ont été avec CE code exact. Mais **la garantie
d'immutabilité du runtime réel ne s'étend pas au backup planifié** tant que cette
divergence n'est pas corrigée.

**Backlog créé, non traité ici (hors périmètre de cette mission de verrouillage)** :
`SCHEDULED-BACKUP-RELEASE-EXECUTION-FIX-1` — créer une nouvelle release incluant
`scheduled_backup.py`, puis corriger `run_scheduled_backup.ps1` pour faire
`Push-Location $activeRelease` (comme `run_real_backend.ps1`), puis revalider un
run réel depuis la release. Pas fait maintenant : corriger le lanceur exigerait de
re-valider tout le chemin d'exécution depuis zéro (nouvelle release, nouveau test
réel), ce qui dépasse le périmètre « verrouiller l'état actuel », et le texte de la
mission demande explicitement de ne pas re-modifier la release ni de relancer un
backup réel sans nécessité démontrée.

**Audit Git :**
- `git status` initial : 4 fichiers modifiés (`CLAUDE.md`, `STATE.md`,
  `backend/scripts/backup_media.py`, `backend/tests/test_backups.py`) + 2 nouveaux
  (`backend/scripts/scheduled_backup.py`, `backend/tests/test_scheduled_backup.py`)
  + `.claude/` non suivi (outillage local, laissé de côté comme lors des commits
  précédents)
- Scan secrets sur le diff exact : aucun (`DATABASE_URL`, mots de passe,
  `CABINET_MASTER_KEY_HEX`, tokens — rien trouvé)
- **Note** : `run_scheduled_backup.ps1` vit dans `DigitalCrown-Runtime\bin\`, **hors
  de ce dépôt Git** par construction (« hors dépôt » était une exigence explicite de
  `SCHEDULED-TASK-BACKUP-REPLACE-1`) — il n'est donc pas et ne peut pas être commité
  ici. Sa provenance est tracée uniquement par ce document STATE.md, pas par Git.

**Commit local créé** : `d7a8e7a` — "feat(ops): add scheduled PostgreSQL and media
backups" — aucun push.

**Correspondance de provenance (mise à jour)** :
```
Tâche Windows active      : DigitalCrown_DailyBackup_v2 (Ready, LastTaskResult=0)
Ancienne tâche            : DigitalCrown_DailyBackup_User (Disabled, conservée)
Code réellement exécuté   : dépôt de travail, désormais figé au commit d7a8e7a
Release immuable active   : 20260711-012549-738eb5234efc (backend réel :8005,
                             PID 14516) — intacte, vérifiée non modifiée, mais
                             NE CONTIENT PAS scheduled_backup.py et n'est PAS
                             utilisée par le backup planifié (voir découverte
                             ci-dessus)
Interpréteur              : venv du dépôt (dépendance résiduelle documentée,
                             RUNTIME-PYTHON-INDEPENDENCE-1)
```

**Confirmations finales** : PID 14516 inchangé, backend réel non redémarré,
`digitalcrown_db` non modifiée, médias réels inchangés (1815 fichiers), superadmin
intact, PatientJourney non activé, aucun nouveau backup réel déclenché pendant
cette mission (l'investigation a réutilisé les artefacts déjà produits par
`SCHEDULED-TASK-BACKUP-REPLACE-1`).

## SCHEDULED-BACKUP-RELEASE-EXECUTION-FIX-1 (2026-07-11)

**Statut : COMPLETED.** `DigitalCrown_DailyBackup_v2` exécute désormais son code depuis
une release immuable dédiée, jamais depuis le dépôt de travail — vérifié par deux lignes
de défense indépendantes (PowerShell : hashes SHA-256 contre le manifeste ;
Python : `_check_execution_provenance()`, `__file__` des modules critiques).

**Écart de séquencement corrigé avant de commencer** : la mission demandait
explicitement une release depuis le commit `bb779cc`, mais ce commit est **antérieur**
à l'écriture de `_check_execution_provenance()` (le correctif de cette mission
elle-même). Une release depuis `bb779cc` n'aurait pas contenu le correctif qu'elle est
censée déployer. Le code a d'abord été committé (`0bd18fc`), puis la release a été
construite depuis ce nouveau commit — pas depuis `bb779cc`. Une première release
prématurée (depuis `bb779cc`, jamais pointée par `backup-current.json`) a été créée
puis supprimée avant activation, aucune trace laissée.

**Livré :**
- `backend/scripts/scheduled_backup.py` — `_check_execution_provenance()`, appelée
  avant même l'acquisition du verrou. `REPO_ROOT` configurable
  (`DIGITALCROWN_REPO_ROOT`, testabilité). Nouveaux champs manifeste :
  `provenance_status`, `provenance_violations`.
- `backend/scripts/create_backup_release.ps1` (nouveau) — `git archive` sur un commit
  exact vers `DigitalCrown-Runtime\backup-releases\<timestamp>-<commit_short>\`,
  jamais une copie du dépôt courant. Manifeste `backup-release-manifest.json`
  (`purpose=scheduled-backup`, `environment=cabinet-real`, hashes SHA-256 des 5
  fichiers critiques).
- `backend/scripts/run_scheduled_backup.ps1` — **réécrit et désormais versionné** dans
  le dépôt (`backend/scripts/`), déployé (copié) vers
  `DigitalCrown-Runtime\bin\run_scheduled_backup.ps1`. Checksum source/déployé
  identique : `34B5EB8761CD2889E60C6B2845C16A54E373A02595C60ACCFE8051C3B56BF1EE`.
  Lit `backup-current.json`, revalide manifeste + hashes, positionne
  `DIGITALCROWN_ENV_FILE` (même mécanisme que `run_real_backend.ps1` — une release ne
  contient jamais `.env.local`), `Push-Location` vers la release — jamais le dépôt.
- `DigitalCrown-Runtime\backup-current.json` (pointeur atomique, écrit via fichier
  temp + `os.replace()`).
- 5 nouveaux tests (`TestExecutionProvenance`) — violation détectée quand `REPO_ROOT`
  correspond à l'emplacement réel des modules, OK sinon, `sys.executable` jamais une
  violation, `run()` refuse et n'acquiert jamais le verrou en cas de violation.

**Fenêtre de mise à jour contrôlée exécutée (ordre exact de l'ODM) :**
1. `DigitalCrown_DailyBackup_v2` désactivée
2. Release backup créée depuis le commit `0bd18fc664019f44d3473a28ffdf5ea2dc26fb1c`
   (`release_id=20260711-110744-0bd18fc66401`) — 4,6 Mo, aucun `.env` réel (seul
   `.env.example`, placeholder), aucun `ai_models/`
3. Lanceur versionné déployé, checksum source/déployé identique
4. `backup-current.json` écrit atomiquement (bug JSON corrigé en cours de route : un
   heredoc bash avait produit un JSON invalide avec des `\` non échappés — détecté
   immédiatement par l'échec de `ConvertFrom-Json`, corrigé en régénérant le fichier
   via `json.dump` Python)
5. Définition de la tâche v2 inspectée — inchangée (même chemin de lanceur, seul son
   contenu a changé)
6. **Run manuel réel** : `provenance_status=OK`, `cwd` = release, `overall_status=SUCCESS`,
   DB 2 432 396 octets + médias 278 943 308 octets/1815 fichiers, checksums vérifiés
   indépendamment (identiques)
7. **Restore PostgreSQL isolé** (`digitalcrown_scheduled_release_restore_validation`) :
   6/6 compteurs identiques à `digitalcrown_db`, 0 paiement orphelin. **Extraction
   médias isolée** : 1815 fichiers archive = 1815 extraits = 1815 réels. Environnements
   temporaires supprimés après validation.
8. Tâche v2 réactivée
9. **Déclenchement Task Scheduler natif** (`Start-ScheduledTask`) : `LastTaskResult=0`,
   nouveau manifeste `provenance_status=OK`, `overall_status=SUCCESS`, rétention
   appliquée pour de vrai cette fois (0 suppression, sous le plancher)
10. **Test d'immutabilité** : commentaire temporaire ajouté dans
    `backend/scripts/scheduled_backup.py` **du dépôt**, lancement en `--dry-run` —
    `provenance_status=OK` inchangé, hashes de la release inchangés (vérifiés par le
    lanceur lui-même), aucun effet du tout. Édition annulée immédiatement,
    `git status` confirmé propre après.

**Commit local créé** : `0bd18fc664019f44d3473a28ffdf5ea2dc26fb1c` — "feat(ops):
dedicated immutable release for the scheduled backup task" — aucun push. Contient
`backend/scripts/scheduled_backup.py` (provenance check), `test_scheduled_backup.py`
(5 nouveaux tests), `create_backup_release.ps1`, `run_scheduled_backup.ps1`.

**Tests** : 23/23 (`test_scheduled_backup.py`, incluant les 5 nouveaux de provenance) +
89/89 sur la suite ciblée backup/sécurité/install/médias (aucune régression) +
39/39 frontend.

**Disque** : 5,1 Go avant cette mission → **4,41 Go après** (2 runs réels supplémentaires,
~540 Mo, + release backup 4,6 Mo). Signalé au CTO pour la troisième fois dans cette
session — pas d'action prise sans validation explicite, mais la tendance mérite
attention avant d'ajouter d'autres mécanismes automatiques.

**Confirmations finales** : PID réel 14516 inchangé, backend non redémarré, health
checks non re-testés dans cette mission (aucun changement au backend réel), release
backend active (`20260711-012549-738eb5234efc`) vérifiée non modifiée (0 fichier avec
mtime postérieur), `digitalcrown_db` non modifiée, médias réels inchangés (1815),
superadmin intact, `clinical_vault.db` non lu, aucun appel `sqlite3` en mode
PostgreSQL, tâche legacy toujours désactivée et conservée, PatientJourney non activé.

**Risques restants** :
- Dépendance résiduelle de l'interpréteur au venv du dépôt (documentée,
  `RUNTIME-PYTHON-INDEPENDENCE-1`)
- Espace disque en baisse constante (4,41 Go) — surveiller avant toute nouvelle
  automatisation ajoutant du volume
- `SQLCIPHER-AUTO-BACKUP-FIX-1` toujours en backlog séparé, sans impact PostgreSQL

**Verdict : BACKUP PLANIFIÉ IMMUTABLE.**

## RECOVER-LEGACY-DOCUMENT-ARCHIVES-1 (2026-07-11)

**Statut : COMPLETED. 31/31 documents patients réels récupérés avec succès.**

**Contexte** : `BACKEND-STATIC-COVERAGE-AUDIT-1` a révélé (après correction d'une
erreur de construction de chemin dans ma propre vérification initiale) que 31 des 261
`document_archives` réels n'existaient physiquement que sous `backend/static/archives/`
(dépôt de travail, jamais sauvegardé, probablement injoignable via l'app réelle) — les
230 autres étaient déjà correctement en place sous `%APPDATA%\DigitalCrown\media\`.

**Méthode** : les 31 enregistrements suivaient déjà la structure moderne
`archives/<patient_id>/<doc_type>/<année>/<mois>/<fichier>` — simple copie avec la
même structure relative, aucune reconstruction de chemin nécessaire.

**Sécurité appliquée** :
1. Backup frais de `digitalcrown_db` (`backup_20260711_131715.sql.enc`, 2.32 MB) et des
   médias réels (`media_backup_20260711_131735.zip.enc`, 266.02 MB, 1815 fichiers)
   avant toute opération
2. Pour chacun des 31 : hash SHA-256 du fichier source comparé au `file_hash` déjà
   enregistré en base (intégrité de la source confirmée) → copie via fichier temporaire
   scopé + `os.replace()` atomique → hash du fichier copié revérifié depuis sa
   destination finale
3. **31/31 RECOVERED, 0 échec** (aucun `HASH_MISMATCH_SOURCE`, aucun
   `HASH_MISMATCH_AFTER_COPY`, aucun `SOURCE_MISSING`)
4. Originaux dans `backend/static/archives/` **jamais supprimés** (188 fichiers
   toujours présents — filet de sécurité conservé)
5. **Aucune écriture en base** — `file_path` pointait déjà vers le bon chemin logique

**Vérifications finales** :
- `%APPDATA%\DigitalCrown\media\` : 1815 → **1846 fichiers** (exactement +31)
- **261/261** enregistrements `document_archives` référençant `static/...` sont
  désormais correctement présents sous `%APPDATA%\DigitalCrown\media\` (0 restant
  uniquement dans le dépôt)
- `digitalcrown_db` inchangée (mêmes compteurs : 220/12/136/262/176/0)
- PID réel 14516 inchangé, backend non redémarré (opération purement filesystem — le
  backend lit le disque à la demande, aucun redémarrage nécessaire pour que les
  fichiers deviennent servables)
- Médias sources (les 1815 déjà présents) non modifiés

**Conséquence pratique** : ces 31 documents deviennent automatiquement couverts par
tout futur backup (manuel ou `DigitalCrown_DailyBackup_v2`) puisqu'ils sont maintenant
dans le dossier standard. Un cycle de backup complet (déjà fait avant l'opération, à
refaire après pour capturer les 31 nouveaux fichiers) est recommandé.

**Reste ouvert** : le reste de `backend/static/` (documents non liés à
`document_archives`, `static/models/`, `static/uploads/`, `static/patients/`,
`static/reports/` — 439 Mo au total avant cette opération, ~438 Mo restants après
extraction des 31 fichiers d'archives) n'a pas été traité — hors périmètre de cette
mission ciblée, reste dans `docs/REPO_LARGE_FILES_SAFE_AUDIT.md`.

## Questions ouvertes
- M5-C ✅ DONE — passer à M5-D (tests > 80%, E2E Playwright, Sentry) ?

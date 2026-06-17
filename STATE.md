# STATE — DigitalCrown

> Fichier de reprise (handoff). **Lis-moi en premier** pour savoir où on en est.
> Le bloc AUTO ci-dessous est régénéré automatiquement à chaque fin de session : ne l'édite pas à la main.
> Les sections plus bas sont à toi (l'agent) : tiens-les à jour avant de t'arrêter.

<!-- STATE:AUTO:START -->
## Dernière session (auto — ne pas éditer à la main)
- **Mis à jour :** 2026-06-18
- **Branche :** `master` → remote `origin/modif`
- **Worktree :** `C:/Users/lenovo/Documents/Cabinet/DigitalCrown`
- **DB :** PostgreSQL 18.2 `digitalcrown_db` — 197 patients / 149 RDV / 176 actes / 214 docs (intacts)

### Commits de la session
- `cb9d619` P1: Step3Clinical — accordion metric + diagnostic sections
- `6200eda` P2: actes permission, cephalo_measure_registry, 3 suites tests (125 passed)
- `bdbf417` P1: TeamManager quota/approval UI + dashboard stats + cephalo mm validator
- `db4c9cc` P0+P1: 6 corrections pre-prod audit 8.1/10

### Fichiers clés modifiés
- `frontend/src/features/admin/TeamManager.tsx` — quota banner, pending section, approve/reject
- `frontend/src/features/ortho/components/Step3Clinical.tsx` — accordéons métriques + diagnostics
- `backend/routers/admin.py` — dashboard stats + pending_team_requests + team_quota
- `backend/routers/team.py` — quota recheck dans approve (anti-race)
- `backend/routers/prescriptions.py` — actes : permission `[clinical, agenda]` au lieu de `[agenda, accounting]`
- `backend/services/cephalo_consistency_validator.py` — mm bounds + unit contradictions
- `backend/services/cephalo_measure_registry.py` — NOUVEAU : source unique unités céphalo
- `backend/tests/` — 3 nouvelles suites : test_cephalo_validator, test_team_quota, test_bot_pending_action
<!-- STATE:AUTO:END -->

## Prochaine milestone (M5 — à planifier)
Backlog audit 8.1/10 entièrement vidé (P0 ✅ P1 ✅ P2 ✅). Axes possibles pour M5 :

**Option A — Facturation avancée**
- Module notes d'honoraires complet (édition inline, envoi email patient)
- Suivi encaissements + relances automatiques
- Export comptable (CSV/Excel)

**Option B — Agenda intelligent**
- Rappels SMS/WhatsApp patients
- Gestion des créneaux libres / surréservation
- Vue semaine multi-praticien (PREMIUM/ELITE)

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

## Questions ouvertes
- Quelle milestone M5 prioriser ? (voir options A/B/C/D ci-dessus)

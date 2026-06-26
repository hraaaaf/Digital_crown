# STATE — DigitalCrown

> Fichier de reprise (handoff). **Lis-moi en premier** pour savoir où on en est.
> Le bloc AUTO ci-dessous est régénéré automatiquement à chaque fin de session : ne l'édite pas à la main.
> Les sections plus bas sont à toi (l'agent) : tiens-les à jour avant de t'arrêter.

<!-- STATE:AUTO:START -->
## Dernière session (auto — ne pas éditer à la main)
- **Mis à jour :** 2026-06-26 19:06
- **Branche :** `master`
- **Worktree :** `C:/Users/lenovo/Documents/Cabinet/DigitalCrown`

### Fichiers touchés
- _(aucun fichier modifié détecté)_

### Dernières demandes
- ordonnance : quand je décoche Mentions légales (Radioprotection) ça se décoche pas sur l'ordonnance ça s'affiche quand meme tous les documents il faut détecter 
- This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation. Summary:
- Can you push to github !?
- Pre existing like what !? En francais
<!-- STATE:AUTO:END -->

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
- [ ] **Débloquer la route** — `App.tsx` ligne 32 & 175 sont commentées → décommenter + ajouter entrée Sidebar
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

## Questions ouvertes
- M5-C ✅ DONE — passer à M5-D (tests > 80%, E2E Playwright, Sentry) ?

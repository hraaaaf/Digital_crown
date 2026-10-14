# Crown Bot ZERO-LLM — POC isolé (2026-10-14)

**Statut : EXPÉRIMENTAL, NON BRANCHÉ À LA PRODUCTION — aucune donnée patient.**

## Goal et périmètre
Démontrer les transitions déterministes de trois parcours chat sans LLM, sans nouvelle dépendance, sans DB, sans réseau, et sans modifier les routes actuelles.

1. `/patient` → identifiant numérique → proposition **QUERY_PATIENT** (lecture à autoriser côté serveur).
2. `/rdv` → patient → date ISO future ou présente → heure → durée explicite → confirmation exacte → proposition **CREATE_APPOINTMENT**.
3. `/devis` → patient → acte connu → confirmation exacte → proposition **OPEN_DEVIS_EDITOR**, flag `draft_only` (navigation vers éditeur, **pas** devis enregistré).

**Une proposition n'est jamais exécutée dans ce POC.** L'exécution effective reste hors scope et doit utiliser une action ID serveur, le contrôle de rôle et de cabinet, un contrôle de disponibilité et la confirmation métier existante.

## État existant examiné
Source de base : `master@814ec74d4a48cf6046e6b8dbcf1e16aa8e034f25`.

- `backend/services/bot/intent_parser.py` : NLU déterministe regex / mots clés / fuzzy, 14 intentions via `intents_config.py`.
- `backend/services/bot/action_dispatcher.py` : handlers de lecture, de préparation et 4 executors dont rendez-vous, changement statut et ouverture d'éditeurs.
- `backend/routers/bot.py` : sessions isolées utilisateur / cabinet, `/chat`, `/chat/stream`, `/execute`; expiration action 30 minutes et permissions vérifiées.
- `frontend/src/components/CrownBot/CrownBotChat.tsx` : interface chat existante, envoi `mobileFetch` selon chemin mobile; présence de route mobile ne prouve pas une certification Pocket ou un UX responsive réussi.
- `backend/tests/test_bot_action_strict.py` : validations HTTP négatives (422/403/404/409/410), ne prouve pas absence de courses de confirmations simultanées.

## Pourquoi pas un framework complet
Conserver FastAPI / React / RBAC et les contrats action déjà présents. XState n'est justifié que si la complexité des parcours grandit réellement ; React ChatBotify n'est justifié que si les surfaces UI existantes sont déficientes. Aucun remplacement immédiat de Crown Bot ni dépendance installée.

## Risques et garde-fous manquants avant vraie intégration
- **BLOCKER potentiel** : `/bot/execute` ne verrouille pas atomiquement l'état `pending` avant l'exécution métier ; deux confirmations simultanées doivent être testées sous PostgreSQL.
- **MAJOR potentiel** : `/bot/execute` marque `executed` après retour de dispatcher même si `BotResponse.action_type == 'error'`. Vérifier transaction / audit / erreurs.
- **MAJOR potentiel** : le choix du premier patient correspondant au nom peut lever une ambiguïté sans intervention du praticien.
- **MAJOR potentiel** : l'exception lors du contrôle `AgendaException` est logguée puis le flux continue ; pas de réservation automatique sur données non vérifiées.
- Pas de preuve de contrôle de conflit horaire au moment du commit ni de comportement multi-worker.
- Pas d'action de devis persistée dans le POC ; `OPEN_DEVIS_EDITOR` reste une ouverture d'éditeur.
- Aucune règle de prescription, recommandation clinique, données sensibles ou documents réels.
- Vérification mobile réelle 390 / 430 px, desktop 1280 px et zoom 200 % différée car aucune UI modifiée par ce POC.

## Contrat et validation
- Code : `backend/services/bot/workflow_poc.py` (module autonome non importé par `bot.py`).
- Tests : `backend/tests/test_crown_bot_zero_llm_poc.py` via `unittest` (fixtures synthétiques).
- GitHub Actions : `.github/workflows/crown-bot-zero-llm-poc.yml`, limité au `pull_request` qui touche les fichiers POC ou `workflow_dispatch`.
- Vérifier le **run et SHA exact** avant toute mention « PASS ».
- La réussite du workflow valide **uniquement le moteur isolé**, pas les parcours applicatifs API, RBAC en situation réelle, sécurité/concurrence, génération de devis ni UX.

## Next
1. Vérifier GitHub Actions puis corriger échecs du POC.
2. Revue adversariale A logique/clinical safety et B autorisations/concurrence/replay, sur même HEAD exact.
3. Nouveau lot distinct : implémenter un adaptateur FastAPI **derrière feature flag OFF**, IDs d'actions et vérification stricte patient/tenant, dates/fuseau et disponibilité; tests HTTP PostgreSQL synthétiques.
4. Validation desktop & mobile réelle, preuve AFTER, revue et décision humaine avant activation.

**Aucun déploiement Vercel / merge / activation sans accord explicite.**

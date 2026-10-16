# Crown Bot ZERO-LLM — intégration expérimentale (14 octobre 2026)

## PRE / source de vérité
Base : `master@9158902e034c22b162873d5fd44ea7afd45f3e16`.
POC source : PR #884, HEAD `64cd114dcbb58e73682a5df40f542b4f594b64d4` ; 18/18 tests isolés : https://github.com/hraaaaf/Digital_crown/actions/runs/38549885114 .

## Changements et contrat d'intégration
- Copie du moteur déterministe du POC et des tests associés sur une branche actuelle ; aucun LLM, dépendance ou appel réseau ajouté.
- `Settings.CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED` = `False` par défaut.
- `POST /api/bot/workflows/preview` : nouvelle API d'aperçu protégée par auth, permission canonique `patients/agenda/accounting`, et contrôle patient *actuel* par cabinet, préservant la vieille API `/chat` et `/chat/stream`.
- Les 3 commandes `/patient`, `/rdv`, `/devis` rejouent au plus 8 entrées de 1–80 caractères, côté serveur, sans persistance de conversation. Toute commande inconnue ou entrée supplémentaire est rejetée.
- `/patient` effectue une lecture minimale nom/prénom/id après contrôle RBAC et tenant ; `/rdv` et `/devis` renvoient **uniquement des propositions de simulation**, jamais des UUID `BotPendingAction`. Le retour client est **non exécutable** ; ce n'est ni une réservation, ni un devis sauvegardé.
- `/bot/execute` désormais : vérification rôle/type avant `UPDATE WHERE status='pending' AND expires_at>now`, prise en charge atomique enregistrée comme `executing` et *committée* avant l'action ; les doubles appels ne peuvent pas réexécuter la même pending-action. Une erreur explicite de dispatcher marque `failed` et renvoie HTTP 409 ; une exception marque `failed` puis est propagée. Succès devient `executed`.
- `executing` bloqué après crash, jamais rejoué automatiquement : le rapprochement manuel reste nécessaire pour savoir si le métier a été committé avant le crash. Ne pas confondre mécanisme at-most-once et transaction métier exactly-once.

## Tests et limites de preuve
GitHub Actions `.github/workflows/crown-bot-zero-llm-integration.yml` : tests POC sans dépendance + tests réels API via TestClient/SQLite in-memory, y compris flag désactivé, auth 401, validation, RBAC, isolation cabinet, zéro écriture, 409 erreur métier, succès/replay, action en cours bloquée.

Le run GitHub Actions devra être vérifié sur le **HEAD exact** avant certification. **Pas encore de preuve multi-processus PostgreSQL**, ni avant/après UI desktop/mobile (aucun frontend touché). Ne pas valider une intégration effective de l'UI à ce stade.

### Revues adversariales internes à mener après tests
- A — sémantique de FSM, diagnostics fail-closed, pas d'acte clinique autonome, pas d'ajout silencieux de données.
- B — RBAC/tenant, replay/TOCTOU, contention simultanée sur PG, rollback des écritures, audit et crash.
Tant que l'une des conditions exige une correction ou une preuve supplémentaire : **OPEN, non CONVERGED**.

## Avant activation / déploiement (nouveau lot distinct)
1. Tests concurrentiels avec véritables sessions PostgreSQL indépendantes et échec volontaire au milieu du commit.
2. Nouvelle autorisation métier **au moment de l'écriture** : date/heure/fuseau Europe-Casablanca ou règle locale explicite, congés filtrés par cabinet, disponibilité du praticien/fauteuil, conflits et absence d'homonymes.
3. Endpoint pour transformer la proposition en action ID serveur ; workflow confirmation réellement séparé et idempotent.
4. Raccordement UX client sur feature flag avec test réel **mobile 390/430 px et desktop** before/after, navigation accessible, fallback OFF.
5. Double revue propre sur le même HEAD, preuves tests et validations humaines, puis décision explicite de merge et déploiement.

**Pas de merge, Vercel, activation, données réelles ou dépenses autorisées dans ce lot.**

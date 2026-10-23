# CB-02 tranche B — raccordement français guidé API + UI (source-only)

**Base de la PR :** branche source de [CB-02 tranche A #1033](https://github.com/hraaaaf/Digital_crown/pull/1033), non encore fusionnée. Dépendance obligatoire : ne PAS fusionner la tranche B seule dans master. Aucune autorisation de déploiement ni de mise en service n'est acquise.

## Contrat / threat model

- Route expérimentale POST `/api/bot/guided/preview` dans `backend/routers/bot_guided_nlu_cb02.py`, incluse séparément sur le backend. **Double flag** serveur `CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED=false` **ET** `CROWN_BOT_GUIDED_NLU_ENABLED=false` par défaut; OFF → 404. Authentification existante → 401 anonyme, RBAC live → 403 (Agenda, Patient ou les deux pour RDV). Aucune route d'exécution.
- Entrée Pydantic bornée `utterance` ≤160 caractères ; `chosen_patient_id` optionnel seulement en réponse à l'existence d'un sélecteur de patient reconnu. `extra=forbid` empêche `execute`, `previous`, `pending_action_id` et autres champs falsifiés.
- Jour métier dérivé exclusivement de `cabinet_day_context` (timezone backend), jamais du navigateur. `principal_scope` lié au `employer_id:user.id` courant, non retourné. Aucun brouillon précédent transmis par le client; la correction UI consiste à éditer/reposter le texte intégral.
- Résolution patient : `lookup_patient_candidates` existant, filtrage explicite `employer_id` et `deleted_at is None`. Aucun lookup si droits absents. Même 404 inconnu/étranger/supprimé. Homonymes → liste bornée ; un choix doit être encore présent dans les correspondances courantes sur la **même phrase** et le **même cabinet** ; sinon 409. Le label `server_verified` est produit **uniquement côté serveur** après cette vérification. Le texte initial est une mention non fiable.
- RDV complet => **`preview_only`, `proposal: null`, `executable: false`** ; pas de `BotPendingAction`, pas d'UUID, aucun verrou de créneau et aucune prise de RDV. Une phrase incomplète ou ambiguë ne permet aucune écriture.
- L'agenda naturel est **une interprétation autorisée d'intention/date**, pas une requête au vrai calendrier dans cette tranche. Le bouton canonique « Mon programme » CB-01 conserve sa lecture réelle et ses guards. Aucune prétention « mes RDV sont affichés » depuis le parseur CB-02.

## Interface

Composant `CrownBotGuidedNluCb02.tsx`, inclus dans `CrownBotWorkflowPreview` seulement si **`VITE_CROWN_BOT_GUIDED_NLU_ENABLED=true`**, valeur `false` dans `frontend/.env.example`. Le panneau CB-01 parent garde sa propre condition de flag. Zone de saisie texte modifiable, champs reconnus + provenance, questions/refus en `role=status`, erreurs en `role=alert`, choix homonymes avec 44px de cible, mémoire locale volatile uniquement, résultat effacé si texte change ou serveur rejette. Aucune liaison avec `/bot/execute`, `PendingActionCard` ou les états réels d'écriture.

## Gates attendus

- Le workflow existant [Crown Bot ZERO-LLM Integration Gate](https://github.com/hraaaaf/Digital_crown/actions/workflows/crown-bot-zero-llm-integration.yml) couvre maintenant le nouveau `backend/tests/test_bot_guided_nlu_cb02_api.py` et `CrownBotGuidedNluCb02.test.tsx`, **en plus** des tests de sécurité historique (PG/SQLCipher/action replay).
- Le workflow CB-02 tranche A reste obligatoire pour les 71 formulations + négatifs. Les tests API couvrent OFF/OFF, anonyme, 403 avant lookup, 404 étranger/inconnu/supprimé, homonyme et choix obsolète, zéro écriture de RDV/action, refus d'exécution.
- Les captures Windows natif 200%/NVDA pour le **nouveau** composant, et les essais utilisateurs humains, sont **NON_RUN** tant qu'une campagne visuelle dédiée de tranche B n'existe pas. Ne jamais recycler les preuves CB-01 pour revendiquer CB-02 UI.
- Test de source/CI sur **SHA exact**, review des différences, approval humain de capture si applicable, puis décision distincte de fusion. La branche B ne doit pas devancer la fusion de la branche A.

**Non autorisé :** production, Vercel, flags ON au cabinet, patients réels, Pocket, action clinique, CB-03. État post-B attendu uniquement « READY FOR REVIEW source » si tous les gates pertinents sont verts, sinon OPEN.

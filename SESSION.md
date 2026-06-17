# 📓 Journal de Session - Digital Crown

---

### 📅 Date : 17 Juin 2026 (session — Roadmap de redressement pré-production + Sprint 0)
**Intervenant** : CTO Saninova + Claude (Opus 4.8)

#### 🎯 Contexte
Audit pré-production section par section. App **avec données patients réelles** : 195 patients, 149 RDV, 176 actes, 164 dossiers cliniques, 212 documents, 115 paiements. Base vivante = **PostgreSQL 18.2 `digitalcrown_db`** (localhost) — PAS SQLite/SQLCipher dans cet env (le bloc SQLCipher de `config.py` ne s'active que si l'URL commence par `sqlite`). Les `.db` à la racine + `%APPDATA%/DigitalCrown/clinical_vault.db` sont des reliquats.

#### 🔒 Contraintes NON-NÉGOCIABLES (valables pour TOUS les sprints)
- JAMAIS supprimer / réinitialiser / recréer / reseeder / écraser des données patients.
- JAMAIS `Base.metadata.drop_all()`, JAMAIS dropper la table patients, JAMAIS régénérer IDs/`numero_dossier`.
- JAMAIS déplacer/supprimer un fichier patient sans migration réversible.
- Migrations conservatrices uniquement : colonne nullable → backfill → contrainte. `count_before == count_after` (patients/appointments/actes/dossiers/documents/paiements) **prouvé à chaque sprint** en rejouant `scripts/preflight_data_audit.py`.
- Backend = seule autorité. Frontend = non fiable. LLM = non fiable, enfermé en capsule (pas d'accès DB/outils/actions/fichiers/PII, sortie validée par schéma).
- Pas de cross-tenant : chaque `patient_id` vérifié contre `employer_id`. Aucun fichier patient public. Télémétrie/cloud OFF par défaut (opt-in explicite). Aucune simulation IA clinique silencieuse en prod. masterKey jamais en clair. Sortie IA clinique = validation praticien.

#### ✅ Sprint 0 — Filet de sécurité + audit (DONE)
- **Backup** : `backups/digitalcrown_db_20260617_102554.dump` (pg_dump custom, 356 Ko, exit 0). Intégrité vérifiée `pg_restore -l` → 48/48 tables.
- **Audit read-only** : `scripts/preflight_data_audit.py` (transaction `SET TRANSACTION READ ONLY`, rejouable). Rapports : `artifacts/preflight/preflight_audit_*.{json,md}`.
- **Résultats** : 0 orphelin FK · 0 doublon `numero_dossier` · **0 `numero_dossier` partagé entre tenants → migration P0.4 sûre sans nettoyage** · patients tous `employer_id` (NOT NULL). `employer_id NULL` sur 5 tables (clinical_rules/diagnostic_templates/medicaments = référentiel global par conception ; audit_logs = events système ; users 8/9 = comptes propriétaires) — **aucune donnée patient en péril**.

#### 🧱 P0 — Blockers production (vérifiés dans le code réel)
1. **✅ P0.1 Télémétrie ON par défaut — FAIT.** Flag `TELEMETRY_ENABLED` (config.py, défaut False) ; garde `_telemetry_enabled()` en tête des deux fonctions de `telemetry.py` ; tâches non enregistrées dans `auth.py` si OFF ; collection Firestore `business_intelligence_leak` → renommée `cabinet_usage_metrics` ; docstring « mouchard » supprimée. Audit rejoué : counts intacts.
2. **✅ P0.2 Fichiers patients publics — FAIT.** `main.py` : routes authentifiées (`Depends(get_current_user)`) pour `uploads/panoramic`, `uploads/radios`, `media/archives`, `media/documents`, enregistrées AVANT les mounts (précédence Starlette) → mêmes URLs, zéro changement frontend (cookie `access_token`). Branding/clinics/assets restent publics. Vérifié : anonyme 401, authentifié 200, traversal bloqué, audit intact.
3. **✅ P0.4 Collision multi-tenant `numero_dossier` — FAIT.** `models.py` : `unique=True` retiré de `numero_dossier` + `UniqueConstraint("numero_dossier","employer_id", name="uq_patients_numero_dossier_employer")`. Migration idempotente transactionnelle `scripts/migrate_p04_numero_dossier_tenant.py` (pré-condition 0 numéro partagé entre tenants sinon ABORT ; ADD CONSTRAINT composite + index global UNIQUE → index simple ; assert count_before==count_after). Audit rejoué : counts intacts.
4. **✅ P0.8 Simulation IA clinique silencieuse en prod — FAIT.** Garde `_is_production()` (`ENVIRONMENT==production`) dans `panoramic_service.PanoramicEngine.predict()` (modèle absent ou erreur d'inférence → `RuntimeError`, plus de `_run_simulation()`) **et** `sota_panoramic_service.SOTAPanoramicEngine.analyze()` (session absente ou erreur → refus). En dev la simulation reste active. Le flux produit `detect_teeth_only` (IA nomme les dents seulement, 0 pathologie devinée) est inchangé. Vérifié : prod refuse (RuntimeError), dev simule, audit intact (195/176/212).

#### 🗺️ Sprints suivants (durcissement, post-P0)
- S1 permissions (ordonnances/actes/compta) · S2 Crown Bot `pending_action` côté serveur · S3 capsule IA (contexte anonymisé, schéma strict, validateur, token vault jamais loggé) · S4 AI Gateway multi-provider (Ollama local-first, cloud opt-in) · S5 mobile/ZKA · S6 documents/uploads · S7 sûreté clinique · S8 audit logs · S9 CI/prod. Une branche par sprint, audit rejoué à chaque étape.

#### ▶️ Décision
Mode validation : **appliquer puis rejouer l'audit** (prouver count_before==count_after). On commence par les P0.
**Périmètre tranché après audit (17 juin) : ROADMAP COMPLÈTE S1→S9, écriture SESSION.md après chaque étape.**

#### ✅ S1 — Permissions ordonnances/actes/compta (DONE)
Audit des gardes `require_permission` / `assert_patient_access` sur prescriptions, actes, comptabilité, échéanciers, documents.
- **Faille critique corrigée** : `prescriptions.create_acte` n'avait **NI permission NI `assert_patient_access`** → écriture cross-tenant possible (créer un acte sur le patient d'un autre cabinet). Ajout `assert_patient_access(patient_id)` **avant** le `try` (sinon le `except Exception` l'aurait converti en 500) + garde `require_permission(["agenda","accounting"])`.
- Actes : `update_acte`, `upload_acte_attachment`, `get_patient_actes` → ajout `require_permission(["agenda","accounting"])` (avaient déjà le tenant via `assert_patient_access`).
- Compta : `get_accounting_honoraires`, `get_treasury_hub`, `mark_as_paid`, `export_accounting_pdf` n'avaient **aucune** permission (juste `get_current_user`) → un collaborateur sans droit compta lisait/encaissait. Ajout `require_permission("accounting")` (et `["accounting","payments"]` pour `mark_as_paid`). Tenant déjà assuré par le filtrage `employer_id` des requêtes.
- Déjà conformes (vérifié) : `installments.py` (tout `accounting` + `assert_patient_access`), `accounting.py` plans/payments, `documents.generate_document` (`require_document_permission` mappe ordonnance→prescriptions, honoraires/devis/échéancier→accounting + `assert_patient_access`).
- **Reste pour S6** : routes documents non-financières (`archive`/`list`/`download`/`trash`/`restore`/`delete`/`report`) en `get_current_user` — durcissement accès doc à traiter au sprint Documents.
- Vérifié : routers importent OK ; audit rejoué (195/176/212) — **aucune donnée touchée** (changement code only).

#### ✅ S2 — Crown Bot `pending_action` côté serveur (DONE)
Principe : le LLM/regex ne fait que **proposer** des intentions ; toute écriture passe par `POST /bot/execute` (confirmation utilisateur). On a durci ce point d'exécution car la `pending_action` est **entièrement contrôlée par le client**.
- **Faille tenant corrigée** : `_exec_create_appointment` utilisait le `patient_id` client **sans vérification de cabinet** → confirmer une `pending_action` forgée rattachait le patient d'un autre cabinet à mon `employer_id`. Ajout `assert_patient_access(patient_id, user, db)` avant l'écriture. Idem `_exec_open_prescription` / `_exec_open_devis` (redirect sur `patient_id` client). `_exec_change_status` était déjà sûr (filtre `employer_id`).
- **Permission fail-closed** : `bot_execute` faisait `ACTION_PERMISSIONS.get(type)` → `None` pour un type non mappé → `require_bot_permission(user, None)` ne vérifiait rien. Désormais un type absent d'`ACTION_PERMISSIONS` est **refusé (403) avant** le dispatcher (allowlist explicite).
- **Propagation des refus** : `ActionDispatcher.execute` ré-émet les `HTTPException` (403/404 tenant/permission) au lieu de les avaler en `BotResponse(error)` → un refus reste un refus côté API.
- Rappels déjà en place (vérifiés) : chat/stream valident permission via `_parse_and_authorize` (`INTENT_PERMISSIONS`) ; sessions/messages filtrés par `employer_id` + `user_id` ; contexte LLM anonymisé (`data_sanitizer`). Confinement LLM complet → S3.
- Vérifié : imports OK ; audit rejoué (195/176/212) — **aucune donnée touchée**.

#### ✅ S3 — Capsule IA confinée (DONE)
Objectif : LLM = composant **non fiable**, sans accès DB/outils/actions/fichiers/PII, sortie schématisée, et **aucune donnée hors cabinet** sans opt-in explicite.
- **Audit des chemins LLM (4 fichiers à sortie réseau)** :
  - `bot/llm_parser.py` → Ollama **local** (`LLM_API_BASE` défaut `localhost:11434`), prompt **anonymisé** via `data_sanitizer.sanitize()`, sortie **schématisée** (intents/entités fermés), restore + suppression des tokens orphelins. ✅ Confiné.
  - `card_extractor.py` → Ollama **local uniquement**, image = carte de visite **du praticien** (onboarding), zéro PII patient, aucun fallback cloud. ✅ Hors risque.
  - `notification_service.py` → WhatsApp/SMS (Twilio/WhatsMate), **pas un LLM** → hors périmètre capsule.
  - `ai_coherence.py` (vigilance clinique) → **FUITE CLOUD identifiée**.
- **Faille corrigée (ai_coherence)** : le fallback `_gemini_fallback` expédiait le **contexte clinique** (`doc_data` = médicaments/dosages/montants, libellés d'actes récents, habitudes docteur — tous **non masqués**) vers **Gemini (cloud Google)**, gardé uniquement par la présence de `GEMINI_API_KEY`. Viole « cloud OFF par défaut / opt-in explicite » + confinement capsule. (NB : `patient_info` était déjà masqué via `pii_masker.mask_patient_context` — tranche d'âge, genre, antécédents — mais le **document** ne l'était pas.)
- **Correctif** : nouveau flag `Settings.CLOUD_AI_ENABLED: bool = False` (`config.py`). La sortie cloud est désormais verrouillée : condition amont `if settings.CLOUD_AI_ENABLED and settings.GEMINI_API_KEY` + **défense en profondeur** (refus à l'entrée de `_gemini_fallback` si flag False, même appelé directement). Tant que le flag est False (défaut), **aucune donnée clinique ne quitte le cabinet** ; l'IA reste 100 % locale (Ollama) et les vérifs déterministes de Phase 1 (`clinical_coherence.py`) restent actives.
- **Reste pour S4** : formaliser la sélection multi-provider (AI Gateway) autour de ce flag (Ollama local-first, cloud opt-in unifié), et étendre l'anonymisation du `doc_data` si un jour une sortie cloud est activée.
- Vérifié : syntaxe OK ; audit rejoué (195/176/212) — **aucune donnée touchée**.

#### ✅ S4 — AI Gateway multi-provider / Ollama local-first (DONE)
Objectif : un **point de contrôle unique** de la politique d'egress LLM, **local-first**, pour que « cloud OFF par défaut » soit garanti et auditable d'un coup d'œil.
- **Constat avant** : aucun gateway. Endpoints éparpillés — `bot/llm_parser.py` lit `LLM_API_BASE` (env var **libre**, défaut `localhost:11434/v1`), `ai_coherence.py`/`card_extractor.py` via `settings.OLLAMA_URL`. Risque : `LLM_API_BASE` pointé vers un endpoint **cloud** → fuite hors cabinet **sans opt-in** (la sanitization anonymise la PII mais la règle « cloud OFF par défaut » s'applique quand même).
- **Nouveau module `backend/services/ai_gateway.py`** : seul endroit où la politique d'egress IA est décidée.
  - `cloud_ai_allowed()` → lit le flag S3 `CLOUD_AI_ENABLED` (False par défaut).
  - `is_local_endpoint(url)` → loopback + plages LAN privées (RFC1918 : `10.`, `192.168.`, `172.16-31.`, `169.254.`, `*.local`).
  - `resolve_llm_base(requested)` → **local conservé tel quel ; distant autorisé seulement si opt-in ; sinon refus + repli FORCÉ sur le local** (`OLLAMA_URL/v1`). Aucune donnée ne quitte le cabinet sans opt-in.
- **Câblage** : `llm_parser.__init__` résout désormais `LLM_API_BASE` via `resolve_llm_base()` → les 3 sites d'appel (`parse`/`complete`/`stream_completion`) héritent automatiquement de la garde. (`ai_coherence` reste verrouillé par le même flag depuis S3 ; `card_extractor` est local-only.)
- **Tests** : `localhost` et `192.168.x` conservés ; `api.openai.com` **bloqué→repli local** quand `CLOUD_AI_ENABLED=False`, **autorisé** quand True ; défaut `cloud_ai_allowed()=False`.
- Vérifié : syntaxe OK ; tests gateway OK ; audit rejoué (195/176/212) — **aucune donnée touchée**.

#### ✅ S5 — Mobile / ZKA (DONE)
Audit du surface mobile (`backend/routers/mobile.py`) : isolation tenant **OK partout** (toutes les requêtes RDV/patients/documents/signature filtrent `employer_id`, 403/404 si hors cabinet). **Deux failles corrigées** :
- **A. masterKey en clair (non-négociable violé)** : `claim_pairing_token` avait un **mode legacy** qui renvoyait `record.master_key` **en clair** dans le JSON si le client n'envoyait pas de clé publique — et le frontend (`OnboardingScanner.tsx`) utilisait justement ce chemin (`{ token }` seul). Sur LAN HTTP, la clé maître transitait en clair.
  - **Backend** : mode legacy **supprimé**, ECDH (secp256r1) rendu **obligatoire** → 400 si `client_public_key_hex` absent ; la masterKey ne sort que chiffrée (AES-256-GCM, secret partagé HKDF-SHA256, `info="zka_mobile_bridge"`, nonce 12 o préfixé).
  - **Frontend** : nouveau helper `services/zka/ecdhPairing.ts` (WebCrypto P-256 : `generateClientKeyPair` + `deriveMasterKey`) ; `OnboardingScanner.exchangeToken` génère la paire, envoie la clé publique, déchiffre la masterKey localement. Plus aucune masterKey en clair sur le réseau.
  - **Interop validée end-to-end** : test croisé Node WebCrypto ↔ Python `cryptography` → masterKey récupérée identique (MATCH). Confirmé `HKDF salt=None` (Python) ≡ `salt = 32 octets nuls` (WebCrypto).
- **B. `get_mobile_role` fail-open** : token révoqué/invalide/claim manquant retournait `"DENTISTE"` (rôle le **plus** privilégié → accès finances dans `snapshot`). Désormais **fail-closed** au moindre privilège (`"SECRETAIRE"`). (Défense en profondeur ; la révocation est déjà bloquée en amont par `get_mobile_employer_id` → 401.)
- **Note compat** : seuls les **nouveaux** appairages passent par claim-token ; les appareils déjà appairés gardent leurs credentials stockés. Frontend + backend mis à niveau en lock-step.
- Vérifié : syntaxe backend OK ; `tsc --noEmit` frontend propre ; interop crypto OK ; audit rejoué (195/176/212) — **aucune donnée touchée**.

#### ✅ S6 — Documents / uploads (DONE)
Audit complet du router documents + tous les endpoints d'upload des routers.
- **État constaté** : le report S1/S2 (« routes documents en `get_current_user` ») était **déjà en grande partie traité** — `list`/`archive`/`trash`/`restore`/`delete`/`report` ont leur gate (`has_permission(...)` ou `require_document_permission(...)`) en plus de `assert_patient_access` (tenant). Vérifié un par un.
- **Lacune restante corrigée** : `download_document` (l.374) validait token + tenant mais **sans gate de permission** → un utilisateur sans `accounting` pouvait télécharger un PDF financier (devis/honoraires) de son propre cabinet.
  - Ajout : branche **legacy** (fichier patient générique) → `has_permission("patients")` ; branche **doc DB** → `require_document_permission(doc.document_type.value, ...)` (symétrique à generate/archive : ordonnance→`prescriptions`, devis/honoraires→`accounting`, cephalo→`cephalo`, etc.). Protection path-traversal legacy déjà présente (`safe_root`) conservée.
- **Autres uploads vérifiés** : `ia.upload_radio` (`require_permission("cephalo")`), `ia.upload_panoramic` (`require_permission("panoramic")`), `prescriptions.upload_acte_attachment` (gaté en S1), `clinics.me/logo` + `me/letterhead` (auth + tenant via `get_employer_id`, écriture dans le dossier du cabinet, type/taille validés ; branding cabinet, zéro PII patient). Tous sûrs.
- Vérifié : syntaxe OK ; audit rejoué (195/176/212) — **aucune donnée touchée**.

#### ✅ S7 — Sûreté clinique (DONE)
Objectif : toute sortie IA clinique requiert la validation du praticien et ne se substitue pas au jugement clinique.
- **Audit des sorties IA cliniques** :
  - `ai_advisor.generate_diagnostic` → NLG **déterministe** (GhostBrain), **aucun egress réseau** → pas de souci capsule/gateway.
  - Alertes `ai_coherence` (🤖) et `clinical_intelligence.get_patient_summary` → **advisory** (affichées, non contraignantes, jamais auto-appliquées).
  - Panoramique → déjà **déterministe + annotation manuelle** du praticien (pas de diagnostic IA auto).
  - **Disclaimers existants confirmés** : `bilan_ortho_elite.html` (« souverainement validé et assumé par le praticien signataire ») ; `bilan_gen.py` (« Synthèse automatique en attente de validation », « Aucun plan de traitement saisi par le praticien »).
- **Gaps comblés** :
  - `panoramic_elite.html` : ajout d'un disclaimer « Analyse radiologique assistée par ordinateur … demeure souverainement validée et assumée par le praticien signataire … ne se substitue pas au jugement clinique. »
  - `clinical_intelligence.get_full_diagnostic` : ajout d'une constante `AI_VALIDATION_DISCLAIMER` appendue à la synthèse markdown (branches complète + données manquantes) + flag `requires_validation: True` dans la réponse API.
- **Confirmé : aucune auto-finalisation** — le diagnostic IA n'entre dans un PDF officiel que sur action praticien (frontend), jamais écrit silencieusement au dossier.
- **⚠️ Note données live** : pendant cette étape, le compteur Patients est passé de **195 → 196**. Investigation read-only : patient `id=273 « EL JIYAD Hanane »`, `employer_id=1`, **créé 2026-06-17 12:25:37** = inscription patient **réelle via l'app en production** pendant la session (cabinet en activité). **Aucun lien avec mes éditions** (template HTML + disclaimer en mémoire ne créent pas de lignes DB) ; Actes/Documents/RDV restent 176/212/149. **Nouveau baseline d'audit : 196 / 176 / 212.** Donnée patient réelle — conservée, jamais touchée.
- Vérifié : syntaxe OK ; audit rejoué (196/176/212, +1 patient d'origine externe légitime) — **mes changements n'ont touché aucune donnée**.

#### ✅ S8 — Audit logs (DONE)
Objectif : journalisation traçable et **étanche entre cabinets** des opérations sensibles.
- **Audit du sous-système** : `AuditService.log` (fichier + persistance BDD `AuditLog`) est solide ; couverture déjà en place pour login (fail/inactive/success/google/logout/signup), patient CREATE/UPDATE/DELETE, acte CREATE/UPDATE, RDV CREATE/UPDATE/DELETE, cephalo/panoramic DELETE, document GENERATE, `ACCESS_DENIED` cross-tenant.
- **🔴 Fuite cross-tenant corrigée (`admin.get_audit_logs`)** : la requête `db.query(models.AuditLog)` n'était **pas filtrée par `employer_id`** → un admin du cabinet A lisait les IDs patients, emails, IP et détails (incluant des noms) de **TOUS les cabinets**. Ajout du filtre `employer_id == current_user.get_employer_id()`. **Faille RGPD / isolation multi-tenant fermée.**
- **Angles morts de couverture comblés** (ajout `audit_service.log`, opérations jusque-là non tracées en BDD) :
  - `admin.export_database` → `EXPORT_DB` (CRITICAL) — dump complet = opération la plus sensible de l'app.
  - `admin.get_zka_key_qr` → `MOBILE_PAIRING_TOKEN_ISSUED` (WARNING) — émission d'un accès mobile.
  - `admin.revoke_mobile_access` → `MOBILE_ACCESS_REVOKED` (CRITICAL) — rotation clé maître (n'était qu'en `logger.info`, désormais en BDD).
  - `bot.bot_execute` → `BOT_EXECUTE` (WARNING) — trace au point d'étranglement toute écriture confirmée par le LLM (origine Crown Bot).
- **⚠️ Note données live** : pendant cette étape, Patients **196 → 197** et Documents **212 → 214**. Investigation read-only : patient `id=274 « BOUDIAB »` créé **2026-06-17 12:40:33** + ordonnances `id=253/252` (patients 274/273) créées ~12:27–12:40 = activité **réelle de l'app en production** pendant la session. Mes edits S8 sont **statiques** (un filtre `SELECT` en lecture + des appels `audit_service.log` qui ne s'exécutent que si l'endpoint est appelé — je n'ai appelé aucun endpoint) et l'audit a tourné à 15:10 : **aucune ligne créée par mon code**. **Nouveau baseline : 197 / 176 / 214** (RDV 149). Donnée patient réelle — conservée, jamais touchée.
- Vérifié : syntaxe OK (`admin.py`, `bot.py`) ; audit rejoué (197/176/214) — **mes changements n'ont touché aucune donnée**.

#### ✅ S9 — CI / prod (DONE) — 🏁 ROADMAP DE REDRESSEMENT COMPLÈTE
Objectif : empêcher un déploiement avec une config non durcie + gate CI automatisé.
- **Audit prod** : garde `SECRET_KEY` déjà présent au démarrage (`main.py` lifespan) ; CORS local-first (origines LAN/localhost intentionnelles, regex IP privée) ; `DEBUG=False`, `TELEMETRY_ENABLED=False`, `CLOUD_AI_ENABLED=False` par défaut (opt-in). Suite de tests existante : **86 passed / 6 skipped**.
- **Gaps comblés** :
  - `main.py` (lifespan) : **invariants production fail-fast** ajoutés — si `ENVIRONMENT=production`, refus de démarrer si `DEBUG=True`, `DATABASE_URL` sur SQLite, ou wildcard `*` dans `ALLOWED_ORIGINS`. Sans effet en développement.
  - `scripts/prod_safety_check.py` (**créé**) : vérificateur rejouable lecture seule. Contrôle SECRET_KEY (toujours), wildcard CORS (toujours), et invariants prod (DEBUG/SQLite/localhost) si `ENVIRONMENT=production` ; signale l'opt-in télémétrie/cloud IA. Exit 1 si erreur bloquante. Vérifié : dev+clé faible → exit 1 ; dev+vraie clé → exit 0 ; simulation prod non durcie → 3 erreurs.
  - `.github/workflows/ci.yml` (**créé**) : pipeline 2 jobs — (1) `test` : install deps + `prod_safety_check` + `pytest backend/tests` (SQLite in-memory isolé, zéro donnée réelle) ; (2) `prod-gate` : test **négatif** prouvant que le garde refuse bien une config prod non durcie.
- **Note** : le repo n'est pas (encore) sous git ; le workflow est livré prêt à l'emploi pour le `git init` / push.
- Vérifié : syntaxe `main.py` OK ; suite **86 passed / 6 skipped** (inchangée) ; `prod_safety_check` validé dans les 2 modes ; audit rejoué **197 / 176 / 214** (RDV 149, 0 orphelin, 0 doublon) — **mes changements n'ont touché aucune donnée**.

---

### 📅 Date : 17 Juin 2026 (session — Nouveau roadmap M4/M2/M1/M3)
**Intervenant** : CTO Saninova + Claude (Opus 4.8)

#### ✅ M4 — Landmarks overlay fix (radio visible sous les landmarks) (DONE)

**Contexte** : dans le Studio Céphalométrique (Étape 1), la radio radiographique était invisible — seuls les landmarks SVG étaient visibles.

**Cause racine (primaire)** :
Les fichiers radio sont servis par `@app.get("/api/static/uploads/radios/{rel_path:path}")` avec `Depends(get_current_user)` (`main.py` l.463-470). Un `<image href>` SVG ou `<img src>` natif ne peut pas joindre l'en-tête `Authorization: Bearer <jwt>` → **401 → radio invisible**, landmarks SVG en mémoire toujours visibles.

**Analyse du coordinate space** : les deux moteurs d'inférence (PyTorch `vision_service.py` et ONNX YOLO11x `sota_vision_service.py`) scalent les landmarks vers les **coordonnées originales de l'image** via `scale_x = orig_w / target_size` et `scale_y = orig_h / target_size`. Le viewBox SVG (`imgDim`) doit donc correspondre aux dimensions naturelles de l'image — régler `imgDim` sur `naturalWidth × naturalHeight` du blob est correct.

**Correctifs appliqués** (`frontend/src/features/ortho/CephaloWorkspace.tsx`) :
1. **Import** : `import { API_BASE, api } from '../../services/api'` (ajoute le client Axios authentifié).
2. **useEffect auth-aware** : sur une URL HTTP(S) protégée → `api.get(imageSrc, { responseType: 'blob' })` (joint le Bearer token) → `URL.createObjectURL` → `store.setImageSrc(blobUrl)`. Sur un blob/data URL déjà local → `new Image().onload → setImgDim(natural dims)`.
3. **Fix de revocation** : `createdBlobUrl = null` après `store.setImageSrc(blobUrl)` pour que le cleanup n'annule pas le blob URL transféré au store (correction d'un bug race condition cleanup→revoke avant le second rendu).
4. **Fallback** : en cas d'échec du fetch authentifié (dev sans auth, base64) → tentative de chargement direct.

**Audit post-fix** :
- `scripts/preflight_data_audit.py` rejoué → **Patients : 197 · RDV : 149 · Actes : 176 · Documents : 214 · 0 orphelin · 0 doublon** (baseline inchangé).
- Aucune donnée patient touchée (fix frontend uniquement, zéro migration, zéro écriture DB).

---

#### ✅ M2 — Calculs céphalo + permission PDF + isolation CabinetConfig (DONE)

**Contexte** : 5 bugs de calcul angulaire dans le Studio Céphalométrique, 1 faille de permission sur l'endpoint PDF, 1 bug d'isolation multi-tenant dans la factory de documents.

##### Bugs de calcul angulaire — analyse mathématique

`_get_clinical_angle(p1,p2, p3,p4)` utilise `abs(a1-a2)%180` (atan2 des directions). `computeAngle` frontend utilise le produit scalaire → [0°, 180°]. Dans les deux cas, la convention direction du premier segment détermine si l'on obtient l'angle direct ou son supplément.

**Corrections backend (`backend/services/cephalo_engine.py`)**
- **SNA** l.325 : `_get_clinical_angle(S,N, N,A)` → `_get_clinical_angle(N,S, N,A)` (direction de référence doit partir de N, pas de S)
- **SNB** l.330 : idem pour B. Résultat : ~82° au lieu du ~98° précédent (supplément), ANB reste cohérent (sna-snb).

**Corrections frontend (`frontend/src/features/ortho/cephaloUtils.ts`)**
- **SNA/SNB** l.276-277 : `computeAngle(s,n, n,a/b)` → `computeAngle(n,s, n,a/b)` (symétrique backend)
- **`computeInterIncisalAngle`** l.83 : `return computeAngle(u1i,u1a, l1i,l1a)` → `return 180 - computeAngle(...)` (angle inter-incisif est l'angle obtus ~131°, le produit scalaire retournait le supplément ~49°)
- **I/Francfort** l.329 et l.394 : `computeAngle(u1i,u1a, po,or_)` → `computeAngle(u1a,u1i, po,or_)` (inverser sens I1 pour obtenir l'angle obtus ~107° au lieu de ~73°)
- **Nasolabial** l.412 : `computeAngle(cm,sn, sn,ls)` → `computeAngle(sn,cm, sn,ls)` (ordre des arguments : la columelle part de sn → cm, pas de cm → sn)

##### Faille de permission PDF (`backend/routers/patients.py` l.449)
`POST /{patient_id}/pdf` utilisait `require_permission("patients")` — tout utilisateur avec accès patients pouvait générer un rapport céphalo sans droit `cephalo`. Corrigé → `require_permission("cephalo")`.

##### Isolation CabinetConfig (`backend/services/document_factory.py` l.76-81)
`_get_cabinet_config(user_id, db)` filtrait `CabinetConfig.owner_id == user_id`. Pour un collaborateur (non-propriétaire du cabinet), `user_id != employer_id` → la config n'était pas trouvée → erreur 500 ou `ValueError`. Corrigé : lookup du User pour obtenir `get_employer_id()`, puis filtre sur l'`employer_id` (propriétaire du cabinet). Isolation multi-tenant garantie.

**Audit post-fix** :
- `scripts/preflight_data_audit.py` rejoué → **Patients : 197 · RDV : 149 · Actes : 176 · Documents : 214 · 0 orphelin · 0 doublon** (baseline inchangé).
- Aucune donnée touchée (fixes code uniquement, zéro migration, zéro écriture DB).

#### ✅ Cross-tenant média + CephaloConsistencyValidator (DONE)

##### Cross-tenant média (`backend/main.py`)
**Problème** : les routes `/api/static/uploads/radios/`, `/api/static/uploads/panoramic/`, `/api/static/archives/`, `/api/static/documents/` vérifiaient uniquement `get_current_user` (auth anonyme bloquée) mais **pas l'appartenance au cabinet**. Un utilisateur connecté du cabinet B connaissant l'UUID d'un fichier du cabinet A pouvait y accéder.

**Correctif** : helper `_assert_media_tenant(db, employer_id, model_cls, path_col, fragment)` — fait une requête jointure `model → Patient` pour retrouver le fichier par son nom dans la DB. Si trouvé et `patient.employer_id != current_user.get_employer_id()` → 403. Si fichier non référencé en DB (legacy) → laisser passer (conservatif). Toutes les dépendances `db: Session = Depends(database.get_db)` ajoutées aux 4 handlers. Imports `database, models` ajoutés au bloc P0.2.

Table de correspondance :
- Radios → `CephaloAnalysis.image_original_path LIKE '%radios/{rel_path}'`
- Panoramic → `PanoramicAnalysis.image_path LIKE '%panoramic/{rel_path}'`
- Archives → `DocumentArchive.file_path LIKE '%{rel_path}'`
- Documents → `DocumentArchive.file_path LIKE '%{rel_path}'`

##### CephaloConsistencyValidator (`backend/services/cephalo_consistency_validator.py`)
**Problème** : aucun validateur n'existait. Un PDF pouvait être généré avec SNA = 120° ou ANB ≠ SNA-SNB.

**Nouveau module** : `CephaloConsistencyValidator.validate(angles_data)` → `ValidationResult(fatals, warnings, is_valid)`.
- **FATAL** (bloque PDF) : valeur hors bornes physiologiques absolues ; SNA-SNB ≠ ANB (écart > 1.5°) ; contradiction classe squelettique (ANB>4° mais SNA<SNB).
- **WARNING** (non bloquant) : valeur hors norme clinique ; combinaisons I/F + inter-incisif incohérentes.
- Bornes : SNA [60-105°], SNB [58-102°], ANB [-10,15°], Inter-incisif [80-180°], I/Francfort [60-155°], IMPA [60-125°], Nasolabial [50-160°].

**Branchement** : appelé dans `patients.POST /{patient_id}/pdf` et `documents.POST /patients/{patient_id}/report` avant `doc_factory.create_cephalo_report`. Réponse 422 avec `{fatals, warnings}` si invalide.

**Endpoint de pré-validation** : `GET /patients/{patient_id}/cephalo-validation` (permission `cephalo`) → permet au frontend d'afficher les warnings avant de déclencher le PDF.

**Smoke test** : cas normal → valid=True, 0 fatal, 0 warning. Cas aberrant (SNA=120°, inter-incisif=49°) → valid=False, 3 fatals.

**Audit post-fix** :
- `scripts/preflight_data_audit.py` rejoué → **Patients : 197 · RDV : 149 · Actes : 176 · Documents : 214 · 0 orphelin · 0 doublon** (baseline inchangé).
- Aucune donnée touchée (nouveau service + modification routes, zéro migration, zéro écriture DB).

#### ✅ M1 — Plans GOLD/PREMIUM/ELITE + approbation équipe (DONE)

##### Modèle (`backend/models.py`)
- Nouveau `SubscriptionPlan` enum : `GOLD` / `PREMIUM` / `ELITE`
- Nouveau `ApprovalStatus` enum : `pending` / `approved` / `rejected`
- Colonnes ajoutées à `User` : `subscription_plan VARCHAR(20)`, `approval_status VARCHAR(20) NOT NULL DEFAULT 'approved'`, `approval_note TEXT`

##### Migration (`scripts/migrate_m1_subscription_plans.py`)
- Idempotente, transactionnelle, rejouable. Vérifie `count_before == count_after`.
- Résultat : 8 propriétaires → `GOLD + approved`, 1 sous-compte existant → `approved`. 9 users, counts intacts.

##### Quotas par plan
| Plan | Dentistes max (owner inclus) | Assistantes max |
|------|---|---|
| GOLD | 1 | 2 |
| PREMIUM | 2 | 6 |
| ELITE | ∞ | ∞ |
- Pending + approved comptent (anti-gaming).

##### Backend auth (`backend/routers/auth.py`)
- Login bloqué si `approval_status == "pending"` → 403 "en attente d'approbation" + audit log `LOGIN_PENDING`
- Login bloqué si `approval_status == "rejected"` → 403 "demande refusée" + audit log `LOGIN_REJECTED`
- Guard via `getattr(user, "approval_status", "approved")` → rétrocompat si colonne absente.

##### Router team (`backend/routers/team.py`) — nouveaux endpoints
- `GET /team/quota` → `QuotaOut` (plan, used/max dentistes + secretaires, pending_count, can_add_*)
- `POST /team/` → compte en PENDING + `is_active=False` + vérification quota avant création (402 si quota atteint)
- `POST /team/{id}/approve` → `approved + is_active=True`
- `POST /team/{id}/reject` → `rejected + is_active=False + approval_note`

##### Schémas (`backend/schemas/auth.py`)
- `TeamMemberOut` enrichi : `approval_status`, `approval_note`
- Nouveau `QuotaOut` : plan, dentistes_used/max, secretaires_used/max, pending_count, can_add_*

**Audit post-M1** :
- `scripts/preflight_data_audit.py` rejoué → **Patients : 197 · RDV : 149 · Actes : 176 · Documents : 214 · 0 orphelin · 0 doublon** (baseline inchangé).
- Migration conservative : 3 colonnes ajoutées, 0 ligne créée/supprimée.

#### ✅ Bot server-side — `BotPendingAction` + exécution par UUID (DONE)

**Objectif** : la `pending_action` ne transite plus du client au serveur — seul un UUID de 30 min est renvoyé au frontend.

##### Modèle (`backend/models.py`)
- Nouveau `BotPendingAction` : `id UUID PK`, `session_id FK`, `user_id FK`, `employer_id`, `action_type`, `params_json JSON`, `status`, `expires_at`, `created_at`, `executed_at`

##### Migration (`scripts/migrate_bot_pending_actions.py`)
- Idempotente. Crée `bot_pending_actions` via `Base.metadata.tables[...].create()`. Counts patients/docs vérifiés avant/après.

##### Backend (`backend/routers/bot.py`)
- `_store_pending_action()` : persiste la `pending_action` en DB (TTL 30 min), retourne l'UUID.
- `_persist_bot_message()` : stocke l'action et ajoute `pending_action_id` dans `raw_data` + message SSE.
- `POST /bot/execute` : accepte uniquement `{ pending_action_id }` — récupère en DB, vérifie `user_id + employer_id + status + expires_at`, exécute, marque `executed`.
- `POST /bot/execute/{action_id}/cancel` : marque `cancelled`.

##### Frontend (`frontend/src/components/CrownBot/CrownBotChat.tsx`)
- `pendingActionId?: string` ajouté au type `Message`.
- SSE handler stocke `pending_action_id` reçu dans le message bot.
- `handleConfirmAction(msgId, actionData, actionId?)` envoie `{ pending_action_id: actionId }` au lieu du payload complet.
- `PendingActionCard.onConfirm` passe `msg.pendingActionId` ; `onCancel` appelle `POST /bot/execute/{id}/cancel` avant de nettoyer l'UI.

**Garanties** : le client ne peut plus forger de `pending_action` — seul l'UUID (32 caractères, TTL 30 min, propriété `user_id + employer_id` vérifiée côté serveur) est exécutable. Aucune écriture DB sans confirmation utilisateur.

---

#### ✅ M3 — Onboarding céphalo UX : Step4 redesigné (DONE)

**Objectif** : remplacer l'UI chat « Ghost Brain » (lente, linéaire) par une interface structurée en 4 sections avec validation clinique live et 3 boutons d'action clairs.

**Fichier modifié** : `frontend/src/features/ortho/components/Step4Documents.tsx` (réécriture complète)

##### 4 sections

1. **Synthèse Céphalométrique** (col gauche) — 7 cards d'angles (SNA/SNB/ANB/I-Francfort/IMPA/Inter-incisif/Nasolabial) avec code couleur 3 niveaux (vert = norme clinique, amber = hors norme, rouge = fatal hors bornes physiologiques). Section "Détails techniques" collapsible (table de tous les angles calculés).

2. **Dossier Photographique** (col gauche) — grille photos réorganisée sous la synthèse (compact 2-4 cols).

3. **Checklist de validation** (col droite) — 5 critères en temps réel :
   - Image chargée (imageSrc)
   - Calibration effectuée (isCalibrated)
   - Landmarks complets (N/N requis)
   - Cohérence clinique des angles → `GET /patients/{id}/cephalo-validation` (bouton "Actualiser")
   - Diagnostic rédigé (diag.synthese_diagnostique non vide)

4. **Plan de traitement** (col droite) — formulaire remplaçant le chat : technique orthodontique, stade CVM, stratégie thérapeutique (textarea), appareil orthopédique si denture non permanente.

##### 3 boutons d'action
- **Prévisualiser** → `handlePreview()` (ouvre LivePreview modal, blob interne, 0 archivage)
- **Brouillon PDF** → génère PDF via API (`POST /patients/{id}/pdf`), télécharge localement comme `brouillon-bilan-{nom}.pdf`, **sans** archiver dans `document_archives`
- **Valider & Archiver** → appelle d'abord `GET /patients/{id}/cephalo-validation` ; si fatals → 🚫 bloqué avec toast ; si warnings → toast + archivage ; si clean → `handlePrint()` (archive officielle). Bouton désactivé si image manquante, landmarks incomplets, ou fatals présents.

##### Banner d'erreur fatale
Bandeau rouge pleine largeur si des erreurs fatales sont présentes (liste des erreurs du CephaloConsistencyValidator).

**Vérifications** :
- `tsc --noEmit` → 0 erreur TypeScript
- `npx vite build` → build propre, 0 avertissement nouveau
- Aucune migration, aucune écriture DB — composant frontend uniquement.

---

### 📅 Date : 17 Juin 2026 (session — Refonte logique Panoramique)
**Intervenant** : CTO Saninova + Claude (Opus 4.8)

#### 🦷 Refonte Panoramique — 3 demandes livrées (DONE)

**1) L'IA ne nomme QUE les dents (zéro pathologie auto).**
- `upload-panoramic` n'appelle plus le modèle 4-classes (`predict`) mais `panoramic_engine.detect_teeth_only()` (nouveau, `backend/services/panoramic_service.py`) → `detections: []`, mode `TOOTH_DETECTION_ONLY`. La grille FDI reste rendue côté client (`XRayCanvas`). `predict()` conservé pour R&D mais hors flux produit.

**2) Annotation manuelle « smart » + bilan pro déterministe SANS LLM.**
- `panoramic_report_engine.py` **entièrement réécrit** : suppression de `_generate_ai_synthesis` (appel Groq/Ollama) → synthèse 100 % déterministe (`_build_synthesis`), phrases cliniques par anomalie (`_phrase_for`), section **CONDUITE À TENIR** (CCAM déterministe), normalité conditionnelle sinus/os/ATM.
- Store (`usePanoramicStore.ts`) : ajout `dent_absente` + `appareil` (Prothèse, multi-dents) à la taxonomie ; nouveau `GLOBAL_FINDINGS` (lyse généralisée légère/modérée/sévère, parodontite généralisée, édentements totaux, denture mixte) ; state `globalFindings` + `toggleGlobalFinding` ; **persistance localStorage** (`persist`) → plus de perte si onglet fermé ; `resetAll()` au démarrage de chaque upload (anti-contamination inter-patient).
- `PanoramicStudio.tsx` : panneau **Constats Généraux** (sidebar diagnostics) ; envoi `global_findings` à la génération.
- Schéma `PanoramicReportRequest.global_findings` ; persistance `manual_anomalies` + `global_findings` dans `detections_data`.

**3) Prévisualiser + éditer le bilan (ligne / paragraphe).**
- `ReportViewer.tsx` : mode **édition ligne par ligne** (titres `###` stylés, puces `-`, ajout/suppression de lignes) + bouton Enregistrer.
- Nouvel endpoint `PUT /ia/panoramic/{id}/report` (schéma `PanoramicReportEdit`) → persiste le markdown édité ; le PDF Élite repart du `report_narrative` édité.

**Vérifs** : `tsc --noEmit` propre ; import router+schemas OK ; smoke-test moteur de bilan OK (sortie pro, sans LLM).

---

### 📅 Date : 16 Juin 2026 (session — Audit Panoramique)
**Intervenant** : CTO Saninova + Claude (Opus 4.8)

#### 🦷 Audit Panoramique — Score global : 7.1/10

##### Architecture globale — 7/10
**Solide :** pipeline Upload → YOLO11x ONNX → FDI mapping → Rapport markdown → PDF WeasyPrint ; validation dentiste (reject + anomalies manuelles) ; permission gate `require_permission("panoramic")` ; audit log sur suppression ; mode simulation gracieux si modèle absent ; CMO Agent déclenché en background.
**Problèmes :**
- **Double engine** : `panoramic_service.PanoramicEngine` (utilisé) ET `sota_panoramic_service.SOTAPanoramicEngine` (mort) → confusion + dead code
- **`PanoramicWorker.ts` (127 lignes) = dead code** : préprocess retourne `Float32Array` vide, postprocess retourne `[]`, jamais importé nulle part. Prévu pour inférence navigateur (ONNX Runtime Web), jamais finalisé
- **Zustand non persisté avant validation** : anomalies manuelles vivent dans `usePanoramicStore` → si l'onglet est fermé avant `POST /ia/generate-panoramic-report`, tout est perdu silencieusement
- `detections_data` et `report_narrative` JSON brut SQLite sans validation de schéma

##### Étape 1 — Upload & Inférence IA — 7.5/10
**Solide :** CLAHE preprocessing (clipLimit=4.5, tileGrid=12×12) avant YOLO ; letterbox resize sans déformation ; seuils adaptatifs par classe (Lésion périapicale 0.12 → très sensible, Dent incluse 0.30 → strict) ; NMS avec dédup FDI+classe à 50px.
**Problèmes :**
- **Seulement 4 classes IA** : Carie, Carie Profonde, Lésion Périapicale, Dent Incluse — le référentiel que le dentiste peut saisir manuellement en contient 31 (Alvéolyse, Tartre, Implant, Opacité sinusienne, etc.)
- **FDI mapping parabole hardcodée** `y = 0.15(x-0.5)² + 0.52` — non corrigeable si courbe occlusion anormale (béance, Cl. III)
- Pas de barre de progression visible pendant l'inférence CPU (peut durer 5-15 s)
- Pas de validation de contenu fichier : seul le poids (10 MB) est vérifié — une photo de profil ou un PDF passerait

##### Étape 2 — Canvas & Validation (XRayCanvas) — 8/10
**Solide :** grille FDI 32 dents, bounding boxes couleur-codées, rejected = dashed+grisé, popover 6 catégories × 31 anomalies, multi-select range parodontal (`isMultiTooth=true`), magnifier ×8.
**Problèmes :**
- **🔴 Anomalies manuelles invisibles sur le canvas** : l'utilisateur ajoute "Carie émail dent 16" via le popover → apparaît dans la liste de droite MAIS aucun marqueur/bounding box n'est généré sur la radio. Incohérence majeure.
- Confidence score non affiché dans la liste de détections → impossible de trier visuellement par sévérité
- Logique `mapFdi()` dupliquée entre `XRayCanvas.tsx` (front) et `panoramic_service.py` (back) → toute correction de la courbe doit être faite dans deux endroits

##### Étape 3 — Rapport Clinique (panoramic_report_engine.py) — 6/10
**Solide :** rapport déterministe ancré sur vraies détections ; fusion IA + manuelles ; annotations libres en section dédiée ; sanitisation PII avant LLM ; dégradation gracieuse si LLM absent.
**Problèmes :**
- **Pas de sévérité** : "Carie" et "Carie Profonde" génèrent la même section — pas de hiérarchisation URGENT/SURVEILLANCE/RAS
- **LLM sans timeout explicite** dans `generate_markdown()` → si Ollama lent, `/ia/generate-panoramic-report` peut bloquer 30-60 s
- **Codes CCAM présents dans le code backend mais absents du rapport/PDF** — feature amorcée jamais terminée
- Rapport entièrement regénéré (y compris appel LLM) à chaque validation même si seule une détection est rejetée

##### Étape 4 — Comparaison Temporelle T0/T1 — 6.5/10
**Solide :** algo `(fdi, classe)` → new/resolved/worsened(+10% conf)/stable ; dates affichées ; mode side-by-side.
**Problèmes :**
- Comparaison limitée aux 2 dernières analyses — pas de ligne temporelle multi-points
- **Worsening = delta confiance ≥10% = proxy fragile** : deux prises légèrement différentes peuvent varier de 10% sans vraie progression clinique
- **Anomalies manuelles ignorées dans le comparateur** : seules les détections IA sont comparées. "Alvéolyse dent 26" ajoutée manuellement à T0 n'apparaît pas dans le delta
- Pas de possibilité de désigner manuellement la radio de référence (T0) — uniquement la 2ème plus récente

##### Étape 5 — PDF Elite (panoramic_elite_gen.py) — 7.5/10
**Solide :** header brandé, QR code document-spécifique, inclusion image céphalométrique optionnelle, métriques SNA/SNB/IMPA si profil dispo, WeasyPrint robuste.
**Problèmes :**
- Path résolution fragile : `api/static/` vs `/api/static/` → PDF sans image sans erreur levée
- Inclure SNA/SNB/IMPA dans un rapport de radio panoramique est cliniquement incohérent (deux examens distincts) — risque de confusion pour un assureur ou spécialiste
- Codes CCAM absents du PDF alors que le backend les calcule déjà

##### Backend sécurité — 7.5/10
**Problèmes :**
- Aucune validation que le fichier uploadé est bien une radio (magic bytes JPEG/PNG/DICOM, dimensions minimales)
- Fichier physique non nettoyé si l'inférence crashe après `shutil.copy`
- `report_narrative` écrasé sans versionning à chaque validation

---

#### 🎯 Backlog Panoramique — Top 7 (par impact)

| # | Tâche | Modèle | Effort | Impact |
|---|---|---|---|---|
| 1 | **Anomalies manuelles visibles sur canvas** — bounding box synthétique colorée par dent | Sonnet 4.6 | 1 jour | 🔴 UX critique |
| 2 | **Auto-save anomalies manuelles** — `localStorage` dès l'ajout, clé `panoramic_manual_{analysisId}` | Haiku 4.5 | 0.5 jour | 🔴 Perte de données |
| 3 | **Timeout LLM 8s** + flag `llm_used: bool` dans la réponse rapport | Haiku 4.5 | 0.5 jour | 🟠 Stabilité |
| 4 | **Anomalies manuelles dans le comparateur T0/T1** — croiser `detections + manual_anomalies` | Sonnet 4.6 | 1 jour | 🟠 Clinique |
| 5 | **Sévérité dans le rapport** — 3 niveaux URGENT/SURVEILLANCE/RAS en tête de rapport | Sonnet 4.6 | 1 jour | 🟠 Clinique |
| 6 | **Supprimer dead code** — `sota_panoramic_service.py` + `PanoramicWorker.ts` | Haiku 4.5 | 0.5 jour | 🟡 Dette technique |
| 7 | **Validation fichier upload** — magic bytes + dimensions minimales (>800×400px) | Sonnet 4.6 | 0.5 jour | 🟡 Robustesse |

---

### 📅 Date : 16 Juin 2026 (session — Audit Céphalométrie + Fractionnement PrescriptionAgenticStudio)
**Intervenant** : CTO Saninova + Claude (Sonnet 4.6)

#### ✂️ Fractionnement `PrescriptionAgenticStudio.tsx` (1746 → 5 fichiers)
Fichier trop volumineux découpé en composants autonomes :

| Fichier | Lignes | Rôle |
|---|---|---|
| `PrescriptionAgenticStudio.tsx` | 958 | Orchestrateur (state + logique) |
| `DrugRow.tsx` | 300 | Ligne médicament unique (allergy overlay, ghost brain, autocomplete) |
| `PrescriptionGuideModal.tsx` | 288 | Guide de prescription (référentiel curé + dictionnaire national) |
| `QuickEntryBar.tsx` | 116 | Saisie rapide avec suggestions |
| `prescriptionTypes.tsx` | 109 | Types, constantes, helpers (FORMES, presets, fuzzyMatch) |

- `DrugItem` re-exporté depuis le fichier principal → les 3 consommateurs (`DocumentHub.tsx`, `useDocumentStore.ts`, `useDocumentGenerator.ts`) fonctionnent sans changement.
- `tsc --noEmit` : 0 erreur.

---

#### 🦷 Audit Céphalométrie — Score global : 7.1/10

##### Architecture globale — 7.5/10
**Solide :** séparation math (`cephaloUtils.ts`) / UI (`CephaloTracingLayer`) / state (`useOrthoStore`) ; `computeStep3Data()` 100% déterministe hors-ligne ; gestion coords SVG v4.2 via `getScreenCTM().inverse()` ; calibration mm/pixel obligatoire.
**Problèmes :**
- **Double repository** : `features/ortho/cephaloRepository.ts` ET `services/cephaloRepository.ts` → contrats d'API qui dérivent silencieusement. **À fusionner : garder `features/ortho/`, supprimer `services/`.**
- `id.toLowerCase()` partout pour les landmarks → bug de case-sensitivity masqué
- `CephaloStudio.tsx` (composant standalone) ne parle pas au store Zustand → landmarks non sauvés si ouvert hors workflow
- `LocalState.version` incrémenté mais jamais utilisé pour la détection de conflits

##### Étape 1 — Upload Radio + Placement des Points — 8/10
**Solide :** Drag via Pointer Events + `getScreenCTM().inverse()` (fix v4.2) ; magnifier ×3 adaptatif ; wedge zones dynamiques (IMPA ±5°/±10°, I/F ±5°/±10°) ; filtres image ; auto-estimation CVM ; détection IA 40 points.
**Problèmes :**
- Pas de validation visible du nombre de points placés → le praticien peut valider avec 5 points manquants sans alerte
- **VTO** (Virtual Treatment Outcome) incomplet : store + backend OK, mais l'UI n'expose les sliders que dans un menu caché → feature fantôme
- `L1_apex` / `U1_apex` auto-générés avec 85px hardcodé → erreur silencieuse si échelle différente
- Aucun guide de séquence de placement (40 points sans ordre anatomique suggéré)

**Proposition : "Séquenceur de points"** — liste latérale cochable groupée (Squelette crânien → Maxillaire → Mandibule → Dentaire → Tissus mous). UX majeure pour un débutant.

##### Étape 2 — Analyse des Moulages — 5.5/10
**Problèmes (critiques) :**
- Pas d'analyse de **Bolton** (ratio antérieur 91.3% ± 1.91 — donnée critique pour l'espace incisif)
- Pas d'**asymétrie** détectée (Classe II droit ≠ Classe I gauche = subdivision, cas fréquent)
- Pas d'encombrement numérique (mm) par arcade
- Pas d'upload photo de moulage pour le PDF
- DDM clinique saisie sans aide contextuelle sur comment la mesurer

**À implémenter :**
- Champ "Encombrement estimé (mm)" par arcade
- Bolton antérieur automatique si les 12 mesures sont saisies
- Upload photo optionnel visible dans le PDF Step 4

##### Étape 3 — Diagnostic Clinique (auto via `computeStep3Data`) — 9/10
**Solide :** calcul automatique de SNA/SNB/ANB/IMPA/FMIA/Ligne E/angle naso-labial/classe squelettique/pattern vertical ; consensus Steiner+McNamara ("Classe II (Tendance III)") ; DDM Réelle = DDM Clinique + (IMPA−90)/2.5 ; CVM Baccetti ; `generateTreatmentPlan()` déterministe.
**Problèmes :**
- **🔴 Auto-fill écrase les corrections manuelles** : tout déplacement de landmark réécrit les valeurs que le praticien vient de corriger à la main
- Wits absent de `computeStep3Data` (dans les specs mais non calculé automatiquement)
- **Typo** : `mcnmara` au lieu de `mcnamara` dans le code (logs incohérents) → à corriger
- Recalcul T1/T2 non déclenché par l'effet auto

**À implémenter : mécanisme "verrou de champ"** — icône 🔒 par valeur auto-calculée. Si verrouillé, l'auto-fill ne réécrit plus ce champ. Pattern standard des outils CAD médicaux.

##### Étape 4 — Ghost Brain & Plan de Traitement — 6/10
**Solide :** T1 (1 an) et T2 (5 ans) morphing avec vecteurs Ricketts/Tweed ; facteurs lip-follow physiologiquement corrects (Ls→U1 à 75%, Li→L1 à 80%) ; stop automatique à 18 ans.
**Problèmes :**
- **🔴 Vecteurs de croissance hardcodés, ignorent le CVM** : un enfant CS1 a une trajectoire radicalement différente d'un CS5. C'est le problème clinique le plus sérieux.
- Un seul modèle de croissance (Ricketts) — pas de Björk, pas de Pancherz pour Classe II
- `bilan_ortho_engine.generate_bilan()` : fichier backend non trouvé → dead code ou module non versionné
- Pas de diff automatique entre deux analyses successives du même patient

**Fix CVM-adaptatif (backend `cephalo_engine.py`) :**
```python
GROWTH_MULTIPLIERS = {
    'CS1': 1.0,   # potentiel max
    'CS2': 0.85,
    'CS3': 0.70,  # pic pubertaire
    'CS4': 0.45,
    'CS5': 0.20,
    'CS6': 0.05,  # croissance terminée
}
# vecteur_annuel × GROWTH_MULTIPLIERS[cvm_stage]
```

##### Backend (`cephalo_engine.py` / `cephalo_service.py`) — 7/10
**Problèmes :**
- `angles_data` et `landmarks_data` stockés en JSON brut SQLite sans validation de schéma → breaking change corrompt les analyses historiques silencieusement
- Auto-calibration "Phase 4" : si elle échoue, `mm_per_pixel` tombe à 0.1 (défaut hardcodé) sans alerte praticien
- Pas de versionning des analyses (historique des modifications perdu)

##### UX / Performance — 7/10
**Problèmes :**
- `CephaloTracingLayer.tsx` = **1283 lignes** → même problème que `PrescriptionAgenticStudio` avant fractionnement
- Pas d'indicateur de progression global (% points placés, calibration OK/KO)
- Pas de raccourcis clavier documentés pour naviguer entre points

---

#### 🎯 Backlog Céphalométrie — Top 5 (par impact clinique)

| # | Tâche | Modèle conseillé | Effort | Impact |
|---|---|---|---|---|
| 1 | **Verrou de champ Étape 3** — empêcher l'auto-fill d'écraser les corrections manuelles | Sonnet 4.6 | 1 jour | 🔴 Critique |
| 2 | **CVM-adaptatif T1/T2** — multiplier les vecteurs croissance par le stade CVM patient | Opus 4.8 | 2 jours | 🔴 Clinique |
| 3 | **Étape 2 : Bolton + asymétrie + encombrement mm** | Sonnet 4.6 | 2-3 jours | 🟠 Important |
| 4 | **Fusion des deux repos frontend** — supprimer `services/cephaloRepository.ts` | Haiku 4.5 | 0.5 jour | 🟠 Dette technique |
| 5 | **Séquenceur de points Étape 1** — checklist anatomique latérale | Sonnet 4.6 | 1 jour | 🟡 UX |
| 6 | **Fractionnement `CephaloTracingLayer.tsx`** (1283 lignes) | Sonnet 4.6 | 1 jour | 🟡 Maintenance |
| 7 | **Typo `mcnmara → mcnamara`** dans le code | Haiku 4.5 | 5 min | 🟡 Log hygiene |

---

### 📅 Date : 16 Juin 2026 (session — mobile/CORS, documents PDF, catalogue, ordonnance pédiatrique)
**Intervenant** : CTO Saninova + Claude (Opus 4.8)

#### 🌐 Mobile / réseau — fin des bugs d'IP DHCP
- **CORS** (`main.py`) : `allow_origin_regex` acceptait seulement `https://` → bloquait le LAN en `http://`. Élargi à `https?://` + toute IP LAN privée sur `:5173`. Cause du toast « Serveur injoignable » sur mobile (PC passé de `.122` à `.123` via DHCP).
- **Auto-détection partout** (`mobile.py`, `auth.py`) : `_detect_lan_ip()` partagé + `get_lan_frontend_url()` + `resolve_frontend_url()`. La redirection OAuth (`auth.py`) n'utilise plus le `FRONTEND_URL` figé (`.109`) → auto-détecté ; un vrai domaine resterait respecté. Plus aucune IP en dur côté runtime.

#### 📄 Documents PDF (`base_template.py`)
- **Titre remonté de ~0.3 cm dans TOUS les documents** : `bottom_spacing` 0.8→0.5 cm + `default_top` 4.2/4.5→3.9/4.2. Vérifié : 0.27 cm de marge sous le séparateur (pas de chevauchement).
- **Texte du header agrandi (~+12 %)** : nombres magiques (24/14, 26/16) répétés 14× → **centralisés en 4 constantes** `HEADER_FS_FR_TITLE/SUB`, `HEADER_FS_AR_TITLE/SUB` (27/16, 29/18). Le scale utilisateur (`header_font_scale`) reste pleinement fonctionnel par-dessus.

#### 🗂️ Catalogue Dynamique (réglages)
- **Modification du tarif d'un acte préétabli** : le badge prix devient cliquable → prompt pré-rempli → `PUT /catalog/acts/{id}` (endpoint backend qui existait déjà ; ajout `updateAct` au store). Garde-fous : annulation, valeur invalide, no-op si inchangé, virgule décimale.

#### 💊 Ordonnance — saisie rapide pédiatrique + validation Ghost Brain (`clinical_rules.ts`, `PrescriptionAgenticStudio.tsx`)
- **Suggestion = dosage + posologie SELON L'ÂGE** (avant : nom seul). `getAgeAwareDosing(name, age, weight?)` : adulte → dose adulte ; enfant <15 → `pediatric_calc` (poids saisi sinon estimé `(âge×2)+8`). Branché sur autocomplete ET saisie rapide ; ne remplit que les champs vides.
- **Champs manuels agrandis verticalement** (nom/dose `py-2.5`, posologie `textarea rows=2` + `min-h` + interligne).
- **Validation Ghost Brain inline** (`validatePrescriptionLine`) : vérifie (1) existence du dosage (« doliprane 350 mg » → non répertorié), (2) adéquation à l'âge (dose adulte chez enfant, dépassement mg/kg/j), (3) contre-indications vs antécédents. Référentiel **fiable et extensible** : molécules dentaires + marques avec `available_strengths_mg` + `max_mg_per_kg_day`. Hors référentiel → **silencieux** (pas de fausse alerte ni de faux feu vert).
- **Guide de Prescription** (ex-« Guide Pédiatrique » — renommé car il couvre désormais TOUS les médicaments, l'âge pilotant dose adulte/enfant) : référentiel curé passé de **6 → 12 molécules** (+ Rodogyl/Birodogyl, Clindamycine, Azithromycine, Chlorhexidine, Miconazole, Codéine⚠️) avec `category` + `notes` de sécurité. Modal amélioré : **catégories** + **poids auto-estimé depuis l'âge** + **contre-indications surlignées pour CE patient** (croisement antécédents). Doses = références standard, « à valider par le praticien ».
- **Guide = navigateur de TOUT le dictionnaire national** : la barre de recherche du guide interroge `/medications/search` (4234 médicaments). Chaque résultat affiche nom/DCI/dosage/forme + bouton « ajouter ». Si la DCI/marque correspond à une molécule curée → badge **POSOLOGIE DISPO** avec dose pédiatrique selon l'âge + CI + surlignage patient ; sinon badge **RÉFÉRENCE** (dosage/forme nationaux, posologie « à définir » — jamais inventée). `medication_dict.search()` enrichi (dosage/unite/forme, limit 30) ; `addMolecule` accepte la forme.

#### 🌍 Dictionnaire national des médicaments — INTÉGRÉ
- **Source** : Référentiel CNOPS (data.gov.ma, Open Data **ODbL**, XLSX, ~5900 lignes) — colonnes NOM / DCI1 / DOSAGE1 / UNITE / FORME / PRESENTATION / PPV. Réserve : millésime **2014** (prix dépassés, existence des molécules/dosages valable).
- **Conversion** : XLSX → `backend/data/medications_ma.json` (4234 entrées uniques, 472 Ko) via parser stdlib (zipfile/XML, sans nouvelle dépendance).
- **Backend** : `medication_dict.py` (chargé en mémoire au 1er accès) + `routers/medications.py` → `GET /medications/search` (autocomplétion nationale) et `GET /medications/validate?name=&dosage=` (le dosage existe-t-il ? gère les associations comme Augmentin). Monté dans `main.py`.
- **Front** : `runMedCheck` (debounce 350 ms) appelle `/medications/validate` sur changement de nom/dose → l'existence du dosage est désormais vérifiée pour **~4200 médicaments** (plus seulement les 6 dentaires). La validation curée (`clinical_rules`) ne garde que **âge + contre-indications** (jugements cliniques absents du fichier officiel) → séparation propre, pas de doublon de message.
- Vérifié : « DOLIPRANE 350 » → inexistant (dispo 100/150/200/300/500mg, 1g) ; « ZINNAT 999 » → inexistant ; recherche OK. Suite : 86 passed / 0 régression.

#### 🔐 Audit RBAC assistante (SECRETAIRE) — RAS
- **Agenda** : accès par défaut (`agenda: True`), tous les endpoints `appointments` gardés par `require_permission("agenda")`.
- **Ajouter/modifier patient** : OK (`patients: True`). **Supprimer** : bloqué (rôle DENTISTE/ADMIN requis dans `delete_patient`, + log audit). Cohérent, rien à corriger.

#### 🗂️ Catalogue d'actes UNIFIÉ (agenda ↔ Réglages)
- **Bug trouvé** : la recherche d'actes de l'agenda interrogeait `ClinicalActCatalog` (**jamais seedé → vide**) + 10 actes codés en dur, alors que le Catalogue Dynamique (Réglages) vit dans `CatalogAct`. Deux catalogues déconnectés.
- **Fix** : `accounting_service.search_acts` + branche recherche-vide (`/actes/catalog/search`) pointent désormais sur **`CatalogAct` + Specialty** (source unique). Recherche vide → habitudes + **tout le catalogue managé**.
- **Seed enrichi + additif + auto** : `seed_catalog()` devient idempotent (upsert par nom, sans doublon), enrichi (+PEDODONTIE, +DIAGNOSTIC & URGENCE → 11 spécialités / 62 actes), et **appelé au démarrage** (`main.py`) — plus besoin de lancer le script manuellement.
- **Ajout d'acte depuis l'agenda** : si l'acte tapé est absent → bouton « Ajouter X aux actes » → panneau inline (**tarif + catégorie** parmi les spécialités existantes, ou DIVERS). Endpoint `POST /actes/catalog/quick-add` (get-or-create spécialité, dédup par nom). L'acte est aussitôt sélectionné et réutilisable.

#### 🔮 Ghost Brain proactif — fuite de connexion DB sur la WebSocket
- **Audit** : pipeline en 4 couches — génération (`daily_scheduler.run_daily_alerts`, Timer 24h, règles `habits_engine.check_proactive_triggers`) → stockage (`ghost_memory_service`, dédup hash SHA-256) → diffusion WS (`ai_feedback:/ws/ghost-insights`) → feedback loop (`/feedback`).
- **Bug 🔴** : la WS injectait `Depends(get_db)` → **session DB tenue ouverte toute la durée de la connexion** (des heures) = 1 connexion du pool monopolisée par onglet → risque d'épuisement (cf. QueuePool du 9 juin). + poll `COUNT` toutes les 2 s.
- **Fix** : suppression du `Depends(get_db)` ; **session courte** `SessionLocal()` pour l'auth puis **par tick** (libérée avant le `sleep`, connexion rendue au pool entre deux sondages) ; intervalle 2 s → 5 s.
- ⏳ Restant (non fait, noté) : scheduler `threading.Timer` sans heure fixe/persistance ; double stockage `ProactiveAlert`+`GhostMemoryLog`.

#### 📦 Fichiers volumineux (audit, non fractionnés)
Tiers vendoré `backend/ai_models/*` (mmpose/CLdetection) à ignorer. Nôtres à découper si besoin : `PrescriptionAgenticStudio.tsx` (1746, prioritaire), `CephaloTracingLayer.tsx` (1283), `AccountingPage.tsx` (1097), `models.py` (1088), `base_template.py` (1043), `action_dispatcher.py` (1002), `Dashboard.tsx` (1000).

#### ⚡ Perf — flood de requêtes à l'ouverture d'un dossier patient
- **Cause** : `PatientScoreBadge` (rendu par ligne dans `PatientList`) appelait `GET /patients/{id}/score` **par patient** → ~270 requêtes (chacune = 3 requêtes DB assiduité/solvabilité) à chaque rendu de la liste.
- **Fix backend** : `patient_scoring_service.calculate_scores_bulk()` calcule TOUS les scores en **3 requêtes agrégées** (group by) + endpoint **`GET /patients/scores`** (un seul appel). Route déclarée AVANT `/{patient_id}`.
- **Fix front** : nouveau store `usePatientScoresStore` (batch unique, dédoublonnage des appels concurrents) ; `PatientScoreBadge` lit le store au lieu de fetch individuel. ~270 requêtes → **1**.
- Vérifié : batch == calcul unitaire (même score/grade).

#### ✅ Vérifs
`tsc --noEmit` OK (toutes les modifs front), `py_compile` OK, suite **86 passed / 6 skipped / 0 régression**, seed idempotent + quick-add (dédup/catégorie) + scoring batch testés. Frontend → Vite HMR ; backend (CORS/auto-IP/catalogue/quick-add/scores batch) → **redémarrage requis**.

---

### 📅 Date : 16 Juin 2026 (session CrownBot — refonte du cerveau LLM)
**Intervenant** : CTO Saninova + Claude (Opus 4.8)
**Objectif** : Audit CrownBot (score 4.8/10) + correctifs dans l'ordre A→B→C.

#### (A) 3 bugs 🔴 qui neutralisaient le LLM
- **Fallback LLM mort** (`bot.py`) : `confidence < 0.85 AND intent == "UNKNOWN"` se réduisait à "UNKNOWN" (UNKNOWN a toujours conf 0.0) → le LLM ne corrigeait jamais un match regex faux. Remplacé par `intent == "UNKNOWN" OR confidence < LLM_CONFIDENCE_THRESHOLD` (0.80).
- **Dates LLM jamais en ISO** (`llm_parser._normalize_entities`) : `"demain"` partait tel quel → `datetime.fromisoformat("demain")` crashait. Ajout `_normalize_date_to_iso` (dateparser), `_normalize_time` (HH:MM), durée→int. Valeur invalide écartée (clarification) au lieu de crash.
- **Prompt LLM sans heure/durée** : RDV via LLM bouclait en clarification. Prompt étendu + approche **hybride** : `_fill_structured_gaps` complète les entités structurées (date/heure/durée/dent/id) via le parser regex déterministe appliqué au message original.

#### (B) Streaming SSE
- `llm_parser` : `complete()` (appel unifié, **dédoublonne les 3 httpx.Client**) + `stream_completion()` (SSE OpenAI, deltas).
- `data_sanitizer.restore_stream()` : restauration token-safe au fil des chunks (retient tout `[TOKEN` incomplet → aucune fuite de token tronqué ; supprime les orphelins hallucinés).
- `dispatcher` : greeting/unknown dédoublonnés (`build_conversational` + `_conversational_response`).
- Nouvel endpoint **`POST /bot/chat/stream`** : events `session`/`token`/`final`. Seuls GREETING/UNKNOWN streamés depuis le LLM ; read/write émis en un bloc. UNKNOWN compte dans le quota upsell, GREETING reste gratuit.
- Front (`CrownBotChat.tsx`) : `handleSend` consomme le flux via `fetch`+reader (EventSource ne gère pas le header Bearer). `/bot/chat` non-stream conservé (rétrocompat).

#### (C) Historique par patient + CHANGE_STATUS
- **`BotSession.patient_id`** (nullable FK) + migration `b2c3d4e5f6a7`. Le front envoie `patient_id` quand le bot est ouvert depuis `/patients/:id` ; injection auto de l'entité patient pour les intents patient-centrés (lève la clarification "quel patient ?").
- **`CHANGE_STATUS` implémenté** (était un stub) : détection statut NL (`_STATUS_KEYWORDS`), résolution du RDV (aujourd'hui sinon prochain), `write_pending` + `_exec_change_status` qui applique en DB.
- Fix bonus : emoji statut agenda (les clés `PLANIFIE/EN_COURS` ne matchaient plus l'enum depuis le renommage `PREVU`) + filtre `!= AppointmentStatus.ANNULE` dans `_handle_query_patient`.

#### ✅ Vérifs
- `py_compile` OK, `tsc --noEmit` OK. Tests unitaires : normalisation entités LLM, restore_stream (token coupé + orphelin), détection statut. **Suite complète : 86 passed / 6 skipped, 0 régression** (`test_crownbot_changes.py` ajouté).
- ⚠️ Code mort repéré (non importé) : `frontend/.../CrownBot/hooks/useCrownBot.ts` + `ChatMessage.tsx` → à supprimer.
- ⚠️ Le fetch streaming front bypasse l'auto-refresh 401 de l'intercepteur axios (le bot est secondaire ; retry manuel). À surveiller si tokens courts.

---

### 📅 Date : 16 Juin 2026
**Intervenant** : CTO Saninova + Claude (Sonnet 4.6)
**Objectif** : Bouclage V1 commercialisation (local-first) + audit RBAC / mobile / PWA + fixes.

---

### 🎯 Décision d'architecture — Local-First confirmé
- **Pas de domaine, pas de SaaS hébergé.** Tout tourne en local (`%APPDATA%`, SQLite).
- **Seul lien en ligne = Firebase** : signup (`pending_clients`), validation SuperAdmin, kill-switch licence (sync toutes les 6h vers SQLite, `main.py:151`).
- Le login lui-même reste local (SQLite) mais gated par la licence venue du online. Middleware licence : cache 60s, **fail-open** si DB inaccessible (`main.py:81`).

### ✅ V1 commercialisation — commit `3377eb7`
- Signup public `/register` avec `accept_terms` + `accept_privacy` obligatoires + push Firebase.
- Emails transactionnels (`email_service.py`) : signup reçu, notice admin, compte activé, expiration licence.
- SuperAdmin `/validate` → email activation + 30j d'essai auto.
- Pages légales `/terms` et `/privacy` (`LegalPage.tsx`) — **à faire valider par un juriste avant lancement public**.
- `check-production-readiness.ps1` : 10 vérifications avant lancement.
- `config.py` : SMTP, Google OAuth, SUPPORT_EMAIL, APP_PUBLIC_URL.

### 🔍 Audit RBAC / rôles — RAS, déjà conforme
- 3 rôles : `ADMIN`, `DENTISTE`, `SECRETAIRE`. Distinction clinique/cabinet via `cabinet_type` (PRIVE/CLINIQUE) + `clinic_id` + hiérarchie `employer_id`.
- **Décision validée** : pour CHAQUE sous-compte (dentiste associé OU assistante), le proprio attribue librement les accès case par case. C'est l'option déjà implémentée — `TeamManager.tsx` propose les 2 rôles + 9 permissions cochables ; `team.py` sanitize et applique. Aucun changement nécessaire.
- Accès total réservé au proprio (`role∈ADMIN/DENTISTE` ET `employer_id=NULL`). Tout sous-compte est permission-gated quel que soit son rôle.

### 🔧 Fixes mobile + PWA — commit `f6b5552`
- 🔴 **Bug bloquant** : `AppointmentStatus.PLANIFIE` n'existe pas → création RDV mobile crashait (AttributeError). Init désormais `PREVU`.
- 🔴 **Bug bloquant** : update statut mobile acceptait `"PLANIFIE"`/`"EN_COURS"` → ValueError. Ajout couche de mapping bidirectionnelle mobile↔métier (`_MOBILE_TO_BACKEND_STATUS` / `_to_mobile_status`).
- 🟠 Snapshot/liste RDV renvoyaient les valeurs FR brutes (`"TERMINÉ"`) → `termineCount` toujours 0. Corrigé.
- 🟠 Email superadmin codé en dur (`benmoussa.achraf@gmail.com`) → lit `SUPERADMIN_EMAIL` (env).
- 🟠 PWA : icônes carrées générées (192/512/512-maskable) — l'ancienne `logo.png` 677×369 était déformée. `manifest.json` + `index.html` mis à jour, bloc `screenshots` (fichiers inexistants) supprimé.
- **Fichiers** : `backend/routers/mobile.py`, `frontend/public/manifest.json`, `frontend/index.html`, `frontend/public/icon-{192,512,512-maskable}.png`.

### 📋 Reste pour la commercialisation (config, pas de code)
- SMTP (host/from/password), `SUPERADMIN_EMAIL`, validation juridique CGU/Privacy.
- Pas de domaine requis (local-first).

### ➡️ Prochaine session : **CrownBot / chatbot**
Voir la branche `crownbot` (déjà mergée) et l'audit préliminaire plus bas (score 4.8/10). Pistes ouvertes : streaming des réponses, couverture d'intents, historique par patient (`patient_id`), qualité du parsing LLM multi-turn.

---

### 📅 Date : 12 Juin 2026 (session 2)
**Intervenant** : CTO Saninova + Claude (Sonnet 4.6)
**Objectif** : 4 bugfixes post-recette + CrownBot upsell Premium + documentation architecture.

---

### 🎯 Réalisations

#### 54. Fix Login email/password — "Erreur réseau" (CONFIRMÉ CORRIGÉ)
- **Cause racine** : `authService.login()` utilisait `new FormData()` qui génère un corps `multipart/form-data`, alors que FastAPI `OAuth2PasswordRequestForm` exige `application/x-www-form-urlencoded`
- **Fix** : `new URLSearchParams()` (sérialise correctement) + `withCredentials: true`
- **Chaîne vérifiée** : `LoginPage.tsx` → `authService.login()` → `POST /api/auth/login` (OAuth2PasswordRequestForm) ✅
- **Fichier** : `frontend/src/services/auth.ts`

#### 55. Fix Tour guidé — réapparaît à chaque session
- **Cause** : `handleClose` dans `TourLauncher.tsx` fermait juste le modal sans écrire en `localStorage` → `TOUR_STORAGE_KEY` jamais valorisé → tour relancé à chaque rechargement
- **Fix** : `localStorage.setItem(TOUR_STORAGE_KEY, TOUR_VERSION)` avant `setIsOpen(false)`
- **Fichier** : `frontend/src/components/GuidedTour/TourLauncher.tsx`

#### 56. Fix Radio panoramique — numéros FDI illisibles
- **Cause** : groupe `<g>` à `opacity-40` + texte `rgba(255,255,255,0.5)` sans fond → labels invisibles sur fond radio sombre
- **Fix** : opacité fixe `0.82`, fond `rgba(0,0,0,0.72)` arrondi derrière chaque numéro, texte `rgba(255,255,255,0.95)`, contour dent `0.3→0.5`
- **Fichier** : `frontend/src/features/panoramic/XRayCanvas.tsx`

#### 57. Fix Tendances de la Semaine — données mockées
- **Cause** : `AnalyticsCharts.tsx` utilisait un tableau `mockData` hardcodé, jamais connecté au backend
- **Fix** : fetch `GET /admin/dashboard/stats` → `weekly_activity` (7 jours réels, normalisé 0-100%) avec libellés de jours dynamiques relatifs à aujourd'hui
- Y-axis `%`, tooltip "Activité", fallback silencieux si le fetch échoue
- **Fichier** : `frontend/src/features/analytics/AnalyticsCharts.tsx`

#### 58. CrownBot — Upsell Premium après 3 échanges LLM
- **Backend** : flag `used_llm: true` ajouté dans `raw_data` du `BotMessage` à chaque appel Ollama/LLM réel (les réponses regex ne comptent pas). Comptage post-save par session → retourne `show_upsell: true` dès `llm_exchange_count >= 3`.
- **Frontend** : `PremiumUpsellCard` inline — dégradé amber/orange, icône `Crown`, 3 avantages Premium, CTA "Passer à Premium" → `/settings?tab=license`, bouton "Plus tard" (dismiss local). Affiché sous la réponse bot qui déclenche le seuil.
- **Fichiers** : `backend/routers/bot.py`, `frontend/src/components/CrownBot/CrownBotChat.tsx`

#### 59. Documentation — ARCHITECTURE.md créé
- Arborescence complète commentée (970 entrées) avec description inline pour chaque fichier/dossier significatif
- 4 flux de données documentés : génération PDF, auth, panoramique, CrownBot
- Table de conventions (ports, auth, stores, branches)
- **Fichier** : `ARCHITECTURE.md`

#### 60. Documentation — README.md mis à jour
- Version `v2.0_Ghost_Hub` → `v3.0_CrownBot`
- Port corrigé `8000` → `8005` (partout)
- Références `SKILLS.md` / `ROADMAP.md` supprimées (fichiers inexistants)
- Section "Nouveautés Juin 2026" ajoutée (CrownBot, Échéancier, Analytics réel, 4 bug fixes)
- Architecture simplifiée avec renvoi vers `ARCHITECTURE.md`
- **Fichier** : `README.md`

---

### 📋 Reste à faire

#### Phase 3 (prochaine session)
- **3A** Documents Hub → wizard 4 slides (Devis + Honoraires)
- **3B** Radio panoramique → 5 slides de tagging
- **3C** Bot → historique par patient (lier sessions à `patient_id`)
- **Céphalo P1** → typo `mcnmara` → `mcnamara`, warning HUD, recalcul T1/T2 post-landmark

---

### 📅 Date : 12 Juin 2026 (session 1)
**Intervenant** : CTO Saninova + Claude (Sonnet 4.6)
**Objectif** : Fix échéancier PDF + alignement flux Document Studio.

#### Réalisations

##### Échéancier — Génération PDF unifiée avec Devis/Honoraires
- `InstallmentStudio.tsx` : supprimé boutons internes Aperçu/Imprimer, ajout prop `onPayloadChange`
- `useDocumentGenerator.ts` : gestion complète `activeTab === 'echeancier'` — POST `/installments/generate-preview`, blob URL, print/archive
- `StudioFooter.tsx` : early return sur `plan` seulement (plus `echeancier`) → boutons Aperçu/Enregistrer/Imprimer actifs
- `DocumentHub.tsx` : `echeancierPayload` state branché sur `generatorParams`
- `backend/services/generators/installment_receipt_gen.py` : générateur A5 ReportLab avec CheckBox (✓/●/□)
- `backend/routers/installments.py` : endpoint `/generate-preview` avec normalisation chemin `AppPaths`

---

### 📅 Date : 11 Juin 2026 (session 3)
**Intervenant** : CTO Saninova + Claude (Sonnet 4.6)
**Objectif** : Sprint 15 corrections UI (recette post-connexion mobile) + fix bot mobile + audit sécurité LLM.

---

### 🎯 Score : 79 → 87 / 100

| Module | Avant | Après | Statut |
|---|---|---|---|
| Ordonnance UX (fuzzy saisie, KIN, bouton Apprendre) | 6/10 | 9/10 | ✅ Sprint UI |
| Honoraires (reset dents, auto-row, Bridge) | 7/10 | 9/10 | ✅ Sprint UI |
| Agenda (Ghost on-demand, prix masqués, nav patient) | 6/10 | 9/10 | ✅ Sprint UI |
| Réglages (clavier arabe, sauvegarde persistante) | 5/10 | 9/10 | ✅ Sprint UI |
| Bot mobile (401, token, redirect) | 0/10 | 9/10 | ✅ Hotfix |
| Sécurité LLM (audit complet) | ?/10 | 10/10 | ✅ Audit |

---

### 🚀 Sprint — 15 corrections UI (recette mobile)

#### 35. Ordonnance — Smart saisie fuzzy (Levenshtein ≤2)
- Ajout `fuzzyMatch()` locale — tolère les fautes de frappe sur les noms de médicaments
- Fallback sur `DEFAULT_MOROCCO_PRESETS` quand l'API retourne 0 résultats
- **Fichier** : `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudio.tsx`

#### 36. Ordonnance — KIN auto-fill
- `KIN_PRESET` ajouté : dosage `-`, forme `BAIN DE BOUCHE`, posologie `1 rinçage / jour pendant 7 jours`
- `'kin'` ajouté dans `formesMap`
- Auto-fill déclenché dans `applySuggestion` quand le nom tapé est "KIN"
- **Fichier** : `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudio.tsx`

#### 37. Ordonnance — Suppression bouton "Apprendre ces posologies"
- Bouton supprimé (l'apprentissage se fait déjà silencieusement à chaque archive/save via `useDocumentGenerator.ts`)
- **Fichier** : `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudio.tsx`

#### 38. Honoraires — Reset odontogramme après "Valider la Caisse"
- `setGroupSelectedTeeth([])`, `setOdontogramMode('individual')`, reset items après fermeture modal
- **Fichier** : `frontend/src/features/admin/AccountingStudio.tsx`

#### 39. Honoraires — Suppression auto-ajout de ligne
- Supprimé : `if (idx === items.length - 1 && !item.description && val.trim()) addEmptyRow()`
- **Fichier** : `frontend/src/features/admin/AccountingStudio.tsx`

#### 40. Honoraires — PONT → Bridge
- "Ponts & Prothèses" → "Bridge & Prothèses" (mode label)
- `backend/services/panoramic_report_engine.py` : "Pont de 3 éléments" → "Bridge de 3 éléments"
- `frontend/src/data/clinical-protocols/bridge-3-elements.json` : "Pont dentaire" → "Bridge dentaire"

#### 41. Agenda — Ghost Intelligence on-demand
- `showGhostPanel` state (défaut `false`) — panneau caché jusqu'au clic explicite
- Les 3 fetch (appointment-intel, ghost hub, smart booking) déclenchés uniquement sur `showGhostPanel === true`
- Bouton `<Ghost>` discret visible quand patient sélectionné
- Reset à `false` quand modal ferme
- **Fichier** : `frontend/src/features/agenda/AgendaModal.tsx`

#### 42. Agenda — Suppression des prix dans la liste des actes
- Retiré : badge `{selectedAct.base_price} MAD` dans l'acte sélectionné
- Retiré : `{act.base_price} MAD` dans la liste de suggestion
- **Fichier** : `frontend/src/features/agenda/AgendaModal.tsx`

#### 43. Agenda — "Créer" navigue vers formulaire patient
- `onClick` → `navigate('/patients/new')` + `onClose()`
- **Fichier** : `frontend/src/features/agenda/AgendaModal.tsx`

#### 44. Agenda — Bouton "Modifier" profil patient
- Bouton "Modifier" dans la card patient sélectionné → `navigate('/patients/{id}/edit')` + `onClose()`
- **Fichier** : `frontend/src/features/agenda/AgendaModal.tsx`

#### 45. Réglages — Clavier arabe `custom_specialty_ar` (stale closure)
- `onChar` lit maintenant `useSettingsStore.getState().profile.custom_specialty_ar` au lieu de la closure captée à la création
- **Fichier** : `frontend/src/features/admin/Settings/tabs/ProfileTab.tsx`

#### 46. Réglages — Bouton "Mettre à jour le profil" explicite
- Nouveau bouton sticky en bas qui appelle `saveProfile()` (PUT `/clinics/me`)
- État `saving`/`saved` avec feedback visuel
- **Fichier** : `frontend/src/features/admin/Settings/tabs/ProfileTab.tsx`

#### 47. Réglages — Clarification palette thème
- Texte ajouté sous le titre Palette : "Ces couleurs s'appliquent à l'application et aux documents générés."
- **Fichier** : `frontend/src/features/admin/Settings/tabs/branding/StudioControls.tsx`

---

### 🔥 Hotfix — Bot mobile (3 causes racines)

#### 48. Backend : `get_current_user` rejette les tokens `type=mobile`
- **Cause** : condition `token_type != "access"` rejetait tous les tokens mobiles (type = `"mobile"`, sub = int)
- **Fix** : accepte `type=mobile` avec lookup par `user_id` (int) au lieu d'email
- **Fichier** : `backend/routers/auth.py`

#### 49. Frontend : token mobile (IndexedDB) pas dans `localStorage`
- **Cause** : `api.ts` lit `localStorage.getItem('token')` — les tokens mobiles sont en IndexedDB (localforage)
- **Fix** : sync `creds.access_token → localStorage` au mount et dans `fetchSnapshot`
- **Fichier** : `frontend/src/features/mobile/Dashboard/hooks/useMobileDashboard.ts`

#### 50. Frontend : 401 mobile → redirect `/login` (circuit breaker)
- **Cause** : le code 401 sans refresh token valide déclenchait `_authFailed = true` + redirect
- **Fix** : guard `if (window.location.pathname.startsWith('/mobile'))` pour court-circuiter le redirect
- Même guard sur 402
- **Fichier** : `frontend/src/services/api.ts`

---

### 🔒 Audit Sécurité LLM — Résultat : PASS ✅

**Mur de confidentialité confirmé intact.** Aucune donnée nominative ne fuite vers un LLM externe.

| Service | LLM externe ? | Données envoyées |
|---|---|---|
| `bot/llm_parser.py` | Groq (intent parsing) | Message sanitizé uniquement (`DataSanitizer`) |
| `bot/action_dispatcher.py` | Oui (greeting/unknown) | Message sanitizé — données patient jamais touchées par le LLM |
| `panoramic_report_engine.py` | Groq/Ollama (synthèse) | Labels YOLO anonymisés via `data_sanitizer.sanitize()` |
| `ai_coherence.py` | Ollama / Gemini fallback | `mask_patient_context()` : tranche d'âge, genre, antécédents — pas de nom/phone |
| `ai_advisor.py` | Non | NLG déterministe 100% local |
| `panoramic_ai_advisor.py` | Non | Arbre décisionnel Zero-LLM |
| `prescription_agentic_service.py` | Non | Règles locales |
| `cmo_agent_service.py` | Non | NLG déterministe |
| `ghost_memory_service.py` | Non | Stockage DB pur |
| `rag_context.py` | Non directement | Utilisé pour insights UI — jamais injecté dans un prompt |

**Note** : le fallback Gemini de `ai_coherence.py` (cloud) utilise `mask_patient_context()` avant envoi — acceptable, à documenter dans la politique de données.

---

### 📅 Date : 12 Juin 2026
**Intervenant** : CTO Saninova + Claude (Sonnet 4.6)
**Objectif** : Hotfixes post-recette — 3 bugs réglages + WhatsApp rappel direct.

---

### 🔥 Hotfixes rapides

#### 51. Nom de la structure vide à chaque rechargement
- **Cause** : `fetchProfile` construisait l'objet `profile` avec 30+ champs mais omettait `nom_cabinet` — champ présent en DB mais jamais mappé côté frontend
- **Fix** : ajout `nom_cabinet: res.data.nom_cabinet || ''` dans le mapping `fetchProfile`
- **Fichier** : `frontend/src/features/admin/Settings/hooks/useSettingsStore.ts`

#### 52. En-tête bilingue — "Benmoussa Achraf" au lieu de "Dr. Benmoussa Achraf"
- **Cause (backend)** : le PUT `/clinics/me` écrasait `header_lines_fr[0]` avec `nom_val` brut à chaque sauvegarde — le préfixe `Dr.` était perdu
- **Fix backend** : auto-préfixe `Dr.` si le nom ne commence pas déjà par `Dr.`, `Pr.`, `Docteur`, `Professeur`
- **Fichier** : `backend/routers/clinics.py`
- **Cause (frontend)** : `fetchProfile` chargeait `header_lines_fr` tel quel depuis la DB — les anciennes données sans préfixe n'étaient pas corrigées au chargement
- **Fix frontend** : normalisation de `header_lines_fr[0]` au fetch — préfixe `Dr.` ajouté si absent (correction transparente des données historiques)
- **Fichier** : `frontend/src/features/admin/Settings/hooks/useSettingsStore.ts`

#### 53. WhatsApp rappel échéancier — n'ouvrait pas la conversation du patient
- **Cause 1** : `wa.me/?text=...` sans numéro → ouvre WhatsApp sans destinataire
- **Cause 2** : numéro marocain local `0612345678` non converti en format international `wa.me`
- **Fix** : fetch `GET /patients/{patientId}` au mount pour récupérer `telephone_mobile` → `telephone` → `telephone_fixe`; normalisation complète : `0XXXXXXXXX` → `212XXXXXXXXX`, strip `+`/`00`/espaces/tirets
- **URL finale** : `https://wa.me/212XXXXXXXXX?text=...` → ouvre directement la fenêtre du patient
- **Fichier** : `frontend/src/features/admin/DocumentStudio/Forms/InstallmentStudio.tsx`

---

### 📅 Date : 10 Juin 2026
**Intervenant** : CTO Saninova + Claude (Sonnet 4.6)
**Objectif** : Audit complet du MASTER PLAN vs état réel du code — Phase 1 Quick Wins (bugs + nettoyage UI + PDF scaling).

---

### 🎯 Audit Global — Score 52 → 67 / 100

| Module | Avant | Après | Statut |
|---|---|---|---|
| Ordonnance (toggle + presets) | 4.5/10 | 7.5/10 | ✅ Phase 1 |
| PDF scaling tous générateurs | 6/10 | 8/10 | ✅ Phase 1 |
| Dashboard (métriques) | 1/10 | 7/10 | ✅ Phase 1 |
| Trigger radio post-prothèse | 0/10 | 0/10 | ⏳ Phase 2 |
| Hamburger mobile/tablette | 4/10 | 4/10 | ⏳ Phase 2 |
| Annotations légales toggle | 2/10 | 2/10 | ⏳ Phase 2 |

---

### 🚀 Phase 1 — Quick Wins

#### 15. Dashboard — Nettoyage métriques inutiles
- **Supprimé** le bloc "Status Système / Elite Cloud Connecté" (`Dashboard.tsx:401-409`)
- **Fix bug `+3072% efficacité`** : `(total_analyses || 3) * 12%` était une formule sans sens (256 analyses × 12 = +3072%). Remplacé par `stats.completion_rate` conditionnel
- **Renommé** "Intelligence Analytique" → "Résumé de la semaine"
- **Fichier** : `frontend/src/pages/Dashboard.tsx`

#### 16. Fix toggle Méd ↔ Radio (ordonnance — saisie manuelle)
- **Cause racine** : Le bouton Microscope appelait 4 fois `onUpdateDrug` séquentiellement. Chaque appel à `generator.setHasChanges(true)` pouvait interférer. En pratique, les mutations étaient correctement chainées via `prev =>` mais la mécanique restait fragile.
- **Fix** : 4 appels remplacés par une seule mutation atomique `setDrugs(prev => prev.map(d => d.id === drug.id ? { ...d, type: 'EXAMEN', dosage: '', forme: '', posologie: '' } : d))` — même chose pour le toggle retour MEDICAMENT
- **Fichier** : `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudio.tsx:1045-1056`

#### 17. Presets ordonnance → 2 dropdowns séparés
- **Refonte UI** : chips horizontaux (scroll) → 2 blocs `<select>` avec `ChevronDown`
  - **Bloc 1 "Protocoles Système"** : 6 `DEFAULT_MOROCCO_PRESETS` hardcodés
  - **Bloc 2 "Mes Ordonnances"** : presets utilisateur depuis `/prescriptions/habits/presets` + bouton `×` de suppression conditionnel sur la sélection active
- Ajout state `selectedUserPreset` pour gérer la suppression via le select
- **Fichier** : `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudio.tsx:773-852`

#### 18. PDF Single-Line + Font Auto-Scaling — tous générateurs
- **`base_template.py`** : ajout de la classe `PageCounter` (partagée par tous les générateurs)
- **`certificat_gen.py`** : import `PageCounter` + boucle de compression 6 tentatives (facteur ×0.85) + méthode `_scale_elements()` qui redimensionne `Paragraph` et `Spacer`
- **`libre_gen.py`** : même boucle + `get_adaptive_font_size` sur le titre + ` ` (non-breaking space) sur le titre pour empêcher le retour à la ligne
- **Note** : `accounting_gen.py` avait déjà ` ` + `get_adaptive_style` sur les actes ✓

---

### 📅 Date : 11 Juin 2026 (session 2)
**Intervenant** : CTO Saninova + Claude (Sonnet 4.6)
**Objectif** : Diagnostic et correction complète du pont LAN mobile (OFFLINE après appairage).

---

### 🔥 Hotfix Majeur — Pont Mobile LAN (OFFLINE post-pairing)

#### 28. Audit complet du flux QR → appairage → dashboard

**Cause racine identifiée** : `window.crypto.subtle` (Web Crypto API) est `undefined` en contexte HTTP non-localhost. Le téléphone accède au frontend via HTTP → le déchiffrement AES-256-GCM du snapshot échoue silencieusement dans un `catch {}` sans log → affichage "IMPOSSIBLE DE JOINDRE LE CABINET" même quand le backend répond correctement (HTTP 200).

**Bugs secondaires découverts :**
- `catch {}` sans paramètre dans `useMobileDashboard.ts` avalait toutes les erreurs sans trace → impossible à diagnostiquer
- `api_base_url` stockée en IndexedDB périmée quand l'IP du PC change (DHCP)
- `/api/mobile/ping` backend existait mais n'était jamais appelé côté frontend — l'état OFFLINE était basé sur `navigator.onLine` uniquement (WiFi connecté ≠ backend joignable)
- `get_lan_base_url()` retournait toujours `http://` même quand les certs SSL existent
- JWT mobile 365 jours — si révoqué, erreur 401 masquée en "Impossible de joindre le cabinet"

#### 29. Fix : CryptoService — @noble/ciphers (HTTP-compatible)

- **Cause** : `window.crypto.subtle` exige un contexte sécurisé (HTTPS ou localhost). Sur HTTP LAN, `subtle` = `undefined` → `TypeError` silencieux → OFFLINE
- **Fix** : Réécriture complète de `CryptoService.ts` avec `@noble/ciphers/aes` (pure JS, fonctionne en HTTP et HTTPS)
- API identique (`decryptPayload`, `encryptPayload`), format AES-256-GCM compatible backend
- Package installé : `@noble/ciphers` via npm
- **Fichier** : `frontend/src/services/zka/CryptoService.ts`

#### 30. Fix : catch silencieux → logging

- `catch {}` → `catch (err) { console.error('[MobileDashboard] fetchSnapshot failed:', err) }`
- **Fichier** : `frontend/src/features/mobile/Dashboard/hooks/useMobileDashboard.ts`

#### 31. Infrastructure HTTPS LAN (optionnelle, non bloquante)

- **Installation mkcert** via `winget install FiloSottile.mkcert`
- **Génération certificats** : `certs/cert.pem` + `certs/key.pem` pour `localhost`, `127.0.0.1`, `172.20.10.2`
- **`vite.config.ts`** : lecture conditionnelle des certs → Vite démarre en HTTPS si certs présents, HTTP sinon
- **`Start_DigitalCrown.bat`** : uvicorn avec `--ssl-certfile`/`--ssl-keyfile` si `certs/cert.pem` existe
- **`backend/config.py`** : ajout `https://localhost:5173` et `https://127.0.0.1:5173` dans ALLOWED_ORIGINS
- **`backend/main.py`** : regex CORS `allow_origin_regex` pour accepter toute IP LAN privée en HTTPS sur port 5173
- **`scripts/setup-https.ps1`** : script PowerShell de setup HTTPS (détection IP, génération certs, instructions iPhone)
- **`.gitignore`** : ajout `certs/`

#### 32. Backend : endpoint CA cert + mobileconfig iOS

- `GET /api/mobile/ca-cert` : sert un profil Apple `.mobileconfig` contenant le certificat CA mkcert
- Format `application/x-apple-aspen-config` → iOS affiche une dialog "Installer le profil" propre, pas un téléchargement brut
- Accessible sans authentification (clé publique)
- **Fichier** : `backend/routers/mobile.py`

#### 33. Backend : get_lan_base_url() — détection HTTPS auto

- Détecte si `certs/cert.pem` existe dans le répertoire projet → retourne `https://` au lieu de `http://`
- Le QR code généré encode automatiquement la bonne URL (HTTP ou HTTPS selon config)
- **Fichier** : `backend/routers/mobile.py`

#### 34. UX : écran cert-setup optionnel post-appairage

- Après appairage réussi : si `window.isSecureContext` → dashboard direct ; sinon → écran "Connexion sécurisée"
- Écran non bloquant : bouton **"Activer la sécurité"** (télécharge le `.mobileconfig`) + bouton **"Accéder au cabinet sans HTTPS"** (skip mémorisé via `localStorage.dc_cert_skipped`)
- Les fois suivantes : aucun écran (déjà sécurisé ou déjà skippé)
- **Fichier** : `frontend/src/features/mobile/Onboarding/OnboardingScanner.tsx`

---

### 📅 Date : 11 Juin 2026 (session 1)
**Intervenant** : CTO Saninova + Claude (Sonnet 4.6)
**Objectif** : Phase 2 complète + fix accès réseau LAN mobile.

---

### 🎯 Score : 67 → 79 / 100

| Module | Avant | Après | Statut |
|---|---|---|---|
| Trigger radio post-prothèse | 0/10 | 9/10 | ✅ Sprint 2A |
| Hamburger menu tablette | 4/10 | 9/10 | ✅ Sprint 2B |
| Annotations légales toggle | 2/10 | 9/10 | ✅ Sprint 2C |
| Accès LAN mobile | 0/10 | 9/10 | ✅ Hotfix |
| AppLoader logo | 2/10 | 9/10 | ✅ Hotfix |

---

### 🚀 Phase 2 — Features manquantes

#### 19. Sprint 2A — Trigger radio post-prothèse
- **Backend** (`documents.py`) : après génération honoraires, scan des items pour `couronne/prothèse/bridge/implant/facette/inlay/onlay` → retourne `suggest_radio: true`
- **Hook** (`useDocumentGenerator.ts`) : paramètre `onSuggestRadio?: () => void` + détection `res.data.suggest_radio`
- **Frontend** (`DocumentHub.tsx`) : `handleSuggestRadio` → toast interactif 12s avec bouton "Créer l'ordonnance" (`setActiveTab('ordonnance')`) et bouton "Ignorer"

#### 20. Sprint 2B — Hamburger menu mobile/tablette
- **`Sidebar.tsx`** : props `isOpen`/`onClose`, classe `lg:translate-x-0 -translate-x-full` par défaut, backdrop overlay `fixed inset-0 bg-black/40 lg:hidden` au clic
- **`MainLayout.tsx`** : état `isSidebarOpen`, bouton `<Menu>` fixe visible `lg:hidden` en haut à gauche (`z-[9998]`), fermeture automatique sur changement de route via `useEffect([location.pathname])`

#### 21. Sprint 2C — Annotations légales toggle
- **`schemas/documents.py`** : `OrdonnanceData.show_legal_annotations: bool = True`
- **`ordonnance_gen.py`** : warning "Radioprotection" conditionnel à `getattr(data, 'show_legal_annotations', True)` ; si désactivé et posologie présente, affiche quand même la posologie
- **`useDocumentGenerator.ts`** : `showLegalAnnotations?: boolean` dans les params, injecté dans le payload `show_legal_annotations: params.showLegalAnnotations !== false`
- **`DocumentHub.tsx`** : state `showLegalAnnotations` (défaut `true`), toggle switch UI au-dessus du formulaire ordonnance

---

### 🔥 Hotfixes — Accès LAN Mobile

#### 22. CORS réseau local
- **Cause** : `ALLOWED_ORIGINS` dans `backend/.env` ne listait que `localhost` et `127.0.0.1`
- **Fix** : ajout de `http://192.168.11.122:5173` dans `ALLOWED_ORIGINS`
- Test CORS validé : `curl OPTIONS` → `access-control-allow-origin: http://192.168.11.122:5173` ✓

#### 23. Pare-feu Windows — ports 8005 et 5173
- Règles inbound TCP créées via `netsh advfirewall` (PowerShell admin)

#### 24. OnboardingScanner — URL backend codée en dur
- **Cause** : `resolveApiBase()` tombait sur `import.meta.env.VITE_API_URL` (`127.0.0.1:8005`) quand l'URL contenait `:5173`
- **Fix** : nouvelle logique basée sur `window.location.hostname` — si LAN IP, utilise `${hostname}:8005`
- **Fichier** : `frontend/src/features/mobile/Onboarding/OnboardingScanner.tsx`

#### 25. QR code pont — URL frontend incorrecte
- **Cause** : `get_lan_base_url()` dans `mobile.py` retournait l'IP LAN mais sur le **port 8005** (backend), pas 5173 (frontend). Le mobile atterrissait sur FastAPI, pas React.
- **Fix** : `FRONTEND_URL=http://192.168.11.122:5173` dans `backend/.env`
- **Fichier** : `backend/routers/mobile.py` + `backend/.env`

#### 26. useMobileDashboard — "Impossible de joindre le cabinet"
- **Cause** : `creds.api_base_url` stocké lors du premier appairage contenait `localhost:8005`. Tous les `fetch` du dashboard mobile échouaient car localhost = le téléphone lui-même
- **Fix** : fonction `resolveApiBaseUrl(stored)` qui override à la volée si `stored` contient localhost mais `window.location.hostname` est une IP LAN — appliquée sur tous les appels `creds.api_base_url` (9 occurrences)
- **Fichier** : `frontend/src/features/mobile/Dashboard/hooks/useMobileDashboard.ts`
- **Note** : pas besoin de re-pairer le téléphone, la correction est runtime

#### 27. AppLoader — logo négatif remplacé
- **Cause** : `AppLoader.tsx` utilisait 17 paths SVG tracés manuellement avec gradient bleu — visuellement une version "négative" sans rapport avec le vrai logo
- **Fix** : remplacé par `logo.png` (identique à la Sidebar) avec animation premium :
  - Apparition spring scale (0.85 → 1, `cubic-bezier(0.34, 1.56, 0.64, 1)`)
  - Double anneau pulsant qui disparaît en fondu (phases décalées)
  - Blob glow bleu derrière le logo
  - 3 points rebondissants (stagger 180ms)
- **Fichier** : `frontend/src/components/AppLoader.tsx`

---

### ⚠️ Note Technique — Hook Quality Gate (faux positif)
Le hook `post_tool_use.py` utilise le pattern `PLACEHOLDER\s*[:\-]` avec `re.IGNORECASE`, ce qui matche les classes Tailwind CSS `placeholder:text-slate-400` dans les fichiers `.tsx`. Tous les edits ont bien été appliqués sur disque malgré le message d'erreur affiché.

**Fix permanent (1 ligne)** — ouvrir `C:\Users\lenovo\.claude\hooks\post_tool_use.py`, ligne 48 :
```
r"\b(TODO|FIXME|PLACEHOLDER|HACK|XXX)\s*[:\-]"
→
r"\b(TODO|FIXME|PLACEHOLDER|HACK|XXX)\s*[:\-](?!\w)"
```

---

### 📋 Reste à faire (Phases 3-4)

#### Phase 2 ✅ TERMINÉE (11 Juin 2026)

#### Phase 3 (prochaine session — 2 semaines)
- **3A** Documents Hub → vrai wizard 4 slides (Devis + Honoraires)
- **3B** Radio panoramique → 5 slides de tagging
- **3C** Bot → historique par patient (lier sessions à `patient_id`)

#### Phase 4 (architecture)
- **4A** Catalogue séquentiel traitements (machine à états agenda)
- **4B** Fuzzy match actes + `[+ Ajouter]` inline
- **4C** Entonnoir diagnostic examen clinique

---

### 📅 Date : 09 Juin 2026
**Intervenant** : Antigravity (Staff Software Engineer)
**Objectif** : Stabilisation critique — épuisement du pool de connexions SQLAlchemy, boucle 307, et fiabilisation du catalogue d'actes.

---

### 🚀 Accomplissements Techniques

#### 1. Fix Critique : Double Connexion DB par Requête (QueuePool Exhaustion)
- **Cause racine** : `auth.py`, `catalog.py` et `clinics.py` définissaient chacun une fonction `get_db()` locale distincte de `database.get_db`. FastAPI ne peut mettre en cache les dépendances qu'à partir du même objet-fonction — deux fonctions différentes = deux connexions distinctes par requête.
- **Conséquence** : Chaque requête authentifiée consommait 2 connexions au lieu d'une, divisant la capacité effective du pool par 2 (30 → 15). Sous charge normale, tout semblait OK. Sous rafale (plusieurs onglets patients ouverts simultanément), le pool s'épuisait immédiatement → `QueuePool limit of size 20 overflow 10 reached, timeout 30.00`.
- **Fix** : Remplacement des `def get_db()` locaux par un alias module-level vers `database.get_db` dans les 3 fichiers. FastAPI partage maintenant la même session DB pour `get_current_user` et l'endpoint lui-même.
- **Fichiers** : `backend/routers/auth.py`, `backend/routers/catalog.py`, `backend/routers/clinics.py`

#### 2. Fix : Boucle de Redirection 307 sur `/api/installments/patient/{id}`
- **Cause** : `installments.py` déclarait `router = APIRouter(prefix="/installments")` ET était monté dans `main.py` avec `prefix="/api/installments"`, créant le chemin réel `/api/installments/installments/patient/{id}`.
- **Conséquence** : Le frontend appelait `/api/installments/patient/259` → FastAPI ne trouvait pas de route → redirect 307 vers `/api/installments/patient/259/` → 404. Boucle infinie côté frontend.
- **Fix** : Suppression du `prefix="/installments"` du constructeur `APIRouter()` dans `installments.py`.
- **Fichier** : `backend/routers/installments.py`

#### 3. Hardening Pool : `pool_pre_ping=True`
- Ajout de `pool_pre_ping=True` sur le moteur PostgreSQL pour tester les connexions avant de les distribuer, évitant les erreurs silencieuses sur connexions mortes/périmées.
- Réduction `pool_size=20→10`, `max_overflow=10→5` pour coller à la charge réelle et éviter l'illusion d'une grande capacité.
- **Fichier** : `backend/database.py`

#### 4. Fix Sessions Précédentes (rappel)
- **Tests `test_backups.py`** : WinError 32 résolu via `try/finally` interne pour les connexions sqlite3.
- **`validationErrors is not defined`** : Ajout à l'interface `AccountingStudioProps` avec default `= []`.
- **`props is not defined`** : 7 occurrences `props.X` → noms de variables directs dans `AccountingStudio.tsx`.
- **Erreur Vite ligne 516 `DocumentHub.tsx`** : Bloc orphelin supprimé, 4 props corrects restaurés.
- **Catalogue vide** : Seed de 9 spécialités / 47 actes exécuté (`seed_catalog.py`).
- **TreatmentSelector** : UI inline d'ajout d'acte par spécialité (nom + tarif → `createAct()`).

---

### 🛠️ Commits Pushés
- `2ba65f6` — `fix: eliminate double DB connection per request and 307 redirect loop`

#### 5. Feat : Recherche patient live depuis le Dashboard
- **Problème** : Le bouton recherche du dashboard ne faisait que naviguer vers `/patients?search=...` — inutile, ça ouvre juste la liste.
- **Fix** : Remplacement par une recherche en temps réel. La saisie appelle `GET /patients/?search=q&limit=6`, les résultats s'affichent dans un dropdown inline (avatar, nom, n° dossier). Un clic ouvre directement le dossier patient. Spinner pendant le fetch, message "Aucun patient trouvé" si vide.
- **Fichier** : `frontend/src/pages/Dashboard.tsx`
- **Commit** : `1dc0215`

#### 6. Feat : Dictionnaire de motifs de première consultation + Ghost Brain
- **Problème** : Le motif de consultation était un textarea libre — non structuré, inutilisable par l'IA.
- **Solution** : 
  - `motifsDictionary.ts` : 9 catégories cliniques, 47 motifs (DOULEUR, URGENCE, PARO, ESTHÉTIQUE, CONSERVATRICE, PROTHÈSE, ORTHODONTIE, IMPLANTO, PRÉVENTION). Chaque motif a un niveau d'urgence, des `specialty_hints` et `act_hints`.
  - `MotifSelector.tsx` : sélecteur à tags avec recherche, catégories dépliables, badges urgence, compteur par catégorie, alerte "URGENCE DÉTECTÉE" si motif urgent sélectionné.
  - `AddPatientForm.tsx` : textarea remplacé par MotifSelector. Stockage JSON array d'IDs (rétrocompatible : ancien texte libre affiché tel quel).
  - `clinical_intelligence.py` : `MOTIF_CATALOG` backend + `_resolve_motifs()` pour parser. `get_patient_summary()` génère des alertes automatiques pour les motifs urgents et retourne `motif_specialties` + `motif_treatment_hints` pour injection dans le plan de traitement.
- **Commit** : `3b59f77`

#### 7. Fix : Double `/api` dans AgendaStudio
- **Cause** : `AgendaStudio.tsx` appelait `api.get('/api/upcoming-holidays')` et `api.get('/api/agenda/settings')` alors que l'instance `api` a déjà `baseURL = '.../api'`. Résultat : `/api/api/upcoming-holidays` → 307 → 404.
- **Fix** : Suppression du préfixe `/api/` redondant sur les 3 appels (`/upcoming-holidays`, `/agenda/settings`, `/agenda/exceptions`).
- **Fichier** : `frontend/src/features/agenda/AgendaStudio.tsx`
- **Commit** : `2d88f3e`

#### 8. Feat : CrownBot Copilote — fusion Ghost Brain + Guide contextuel
- **Objectif** : Désencombrer le header (supprimer GuideTower Compass + EliteAssistant orbe embedded), tout consolider dans le bouton bot flottant bas-droite.
- **Réalisé** :
  - `CrownBotChat.tsx` : deux onglets — 💬 Chat (historique sessions, envoi messages) + 🧠 Ghost Brain (WS, insights, markAsRead, TypewriterText, quickActions absorbés depuis `GhostBrainWidget`)
  - `getPageContext(pathname)` : message d'accueil + suggestions contextuels par route (dashboard, patients/:id, patients/new, patients, agenda, accounting, settings, bibliothèque). Reset au changement de route via `useEffect([location.pathname])`.
  - `onUnreadChange` prop : MainLayout reçoit le count Ghost Brain non lu → badge amber pulse sur le bouton flottant bot (masqué quand bot ouvert)
  - `Header.tsx` : suppression imports + composants `GuideTower` et `EliteAssistant`
  - `MainLayout.tsx` : état `ghostUnreadCount`, badge sur bouton bot, prop `onUnreadChange` passée à `CrownBotChat`
- **Fichiers** : `frontend/src/components/CrownBot/CrownBotChat.tsx`, `frontend/src/components/Header.tsx`, `frontend/src/components/Layout/MainLayout.tsx`
- **Commit** : `b9b22ba`

---

### 🌿 Branch : `crownbot` — CrownBot Hardening & Write Actions

#### Audit préliminaire (score 4.8/10 — 3 spécialistes)
- Backend Architect : 5.5/10 — `/bot/execute` stub critique, O(N) finance, lab sans `employer_id`
- AI Engineer : 3.5/10 — zéro contexte conversationnel, entity key mismatch LLM, couverture insuffisante
- Product Manager : 4.75/10 — write actions brisées (trust killer), JSON brut en confirmation, pas de streaming

#### 9–13. CrownBot Hardening & Write Actions (branch `crownbot`)

##### 9. DataSanitizer v2 — Mur béton données ↔ LLM
- **DATE** : `dateparser` FR/AR remplace le regex numérique qui manquait "demain", "lundi prochain", "15 juin"
- **NAME** : whitelist dentaire/médicale (~160 termes) évite les faux positifs sur "Urgence", "Lundi", etc.
- **AMOUNT** : nouvelle règle masque les montants financiers (MAD, DH, €, $)
- **PATIENT_ID** : masque les numéros de dossier/patient dans le contexte
- **restore()** : détecte tokens orphelins (hallucinations LLM), les supprime, log warning
- **sanitize_bot_response()** : méthode pour sanitizer réponses bot avant passage LLM (préparation contexte multi-turn)
- **Fichier** : `backend/services/security/data_sanitizer.py`
- **Commit** : `74a0f47`

##### 10. Fix `/bot/execute` — Actions d'écriture réelles
- `_exec_create_appointment`: crée `Appointment` en DB (patient_id résolu si absent, datetime parsé, employer_id injecté)
- `_exec_open_prescription` / `_exec_open_devis`: retournent `redirect_url` vers les modules dédiés
- `bot.py`: délègue à `dispatcher.execute()` — plus de stub
- **Commit** : `71aff40`

##### 11. Fix sécurité lab + LLM entity keys
- `_handle_query_lab`: filtre par `employer_id` via join `Patient` (évite data leak inter-cabinets)
- `llm_parser._normalize_entities()`: `date→target_date`, `tooth→tooth_number`, supprime les valeurs vides
- **Commit** : `71aff40`

##### 12. Contexte conversationnel multi-turn
- `bot.py /chat`: charge 4 derniers messages, sanitize les réponses bot avant passage LLM
- `llm_parser.py`: injecte le contexte sanitizé comme history OpenAI (`bot→assistant`)
- `intent_parser.py`: `_extract_prior_intent()` guide la classification sur les messages de clarification
- **Commit** : `0fb34e3`

##### 13. UX Confirmation card + Finance O(1)
- `PendingActionCard`: card lisible (Patient/Date/Heure/Motif) remplace le JSON brut
- `handleConfirmAction`: intercepte `redirect` → `navigate()` + `onClose()`
- Finance query: boucle Python O(N) → 2 subqueries GROUP BY (1 requête SQL)
- **Commit** : `3d68e26`
- **Branch poussée** : `crownbot` → https://github.com/lafabriquedapollon-cpu/Digital_crown/pull/new/crownbot

---

### 📋 Points de Vigilance
- **Backup service** : Le service de backup quotidien tente de sauvegarder `clinical_vault.db` qui n'est pas un SQLite valide dans l'environnement actuel → log `file is not a database`. Non bloquant mais à investiguer.
- **Endpoints AI lents** : `GET /api/patients/{id}/ai-summary` peut encore prendre plusieurs secondes selon la taille du dossier. Avec le fix pool, ça ne bloquera plus les autres requêtes mais l'UX gagnerait d'un skeleton loader côté frontend.

---

## 🦷 Audit Céphalo — Score 6.5/10

### Score par axe
| Axe | Score |
|---|---|
| Engine de calcul (backend) | 6/10 |
| Interface tracé (frontend) | 7.5/10 |
| Intégration IA | 7/10 |
| Persistance / sync | 7.5/10 |
| Correction clinique | 5/10 |

### Ce qui fonctionne bien
- Pipeline complet 4 étapes (upload → tracé → analyse → rapport PDF)
- Steiner + Tweed + McNamara + Wits calculés et interprétés avec Z-score + zones de compensation
- Calibration 2 points avec auto-calibration à l'upload
- Autosave débounced 600ms sur chaque mouvement de landmark + optimistic updates
- Studio VTO (U1/L1/mandibule) avec sliders
- Classe squelettique auto (consensus Steiner+McNamara)
- AI narrative → pré-remplissage des 5 champs diagnostiques
- WeasyPrint PDF fonctionnel

---

### 14. Fix P0 — IMPA null check + VTO non calibré (branche `crownbot`)
- **Commit** : `5f5ed6c`

#### Fix 1 : `if impa` → `if impa is not None` — `cephalo_service.py:137`
- **Cause** : `if impa` traitait un float faible (ex: 5.0°) comme falsy → DDM correction silencieusement ignorée
- **Fix** : `ddm_cephalo = (impa - 90) / 2.5 if impa is not None else 0`

#### Fix 2 : VTO affichait des mm fictifs sans calibration — `Step1Cephalo.tsx`
- **Cause** : `mmPerPixel || 0.1` — fallback arbitraire 0.1 mm/px donnait des valeurs cliniquement fausses sur images non calibrées
- **Fix** : `mmPerPixel ? (offset * mmPerPixel).toFixed(1) : 'NC'` sur les 3 sliders (U1, L1, Mandibule)

---

### 📋 Plan Céphalo — Corrections Restantes (à reprendre demain)

#### P1 — Typo schema `mcnmara` → `mcnamara`
- **Fichiers** : `backend/schemas/clinical.py:143`, `backend/routers/ia.py:95`
- **Problème** : `mcnmara_projections` dans le schéma (manque le 'a') vs `mcnamara_projections` dans l'engine → mismatch de clés silencieux à chaque `refine_analysis`
- **Fix** : Renommer `mcnmara_projections` → `mcnamara_projections` dans le schéma ET le routeur (les 2 en même temps pour rester cohérent)

#### P1 — Afficher `vision_metadata.warning` dans le HUD
- **Fichier** : `frontend/src/features/ortho/components/Step1Cephalo.tsx`
- **Problème** : Si l'IA détecte une image dégradée / utilise un mode fallback, le warning est capturé mais jamais affiché → clinicien ne sait pas que l'analyse est dégradée
- **Fix** : Dans le HUD bas-droite, ajouter une pastille amber si `visionMetadata.warning` est défini, avec le texte du warning en tooltip

#### P1 — Recalcul T1/T2 après édition manuelle des landmarks
- **Fichier** : `frontend/src/features/ortho/stores/useOrthoStore.ts`
- **Problème** : Après correction manuelle d'un landmark, `anglesData.t1_projection` / `t2_projection` ne sont pas mis à jour → ghost overlays deviennent incorrects
- **Fix** : Dans `updateLandmarksOptimistic` (après le debounce saveAnalysis), si la réponse backend contient `t1_projection` / `t2_projection`, mettre à jour `anglesData`

#### P2 — Longueur incisive hardcodée 85px dans `cephaloMath.ts`
- **Problème** : Le calcul IMPA frontend utilise 85px fixe → résultat faux sur toute image à zoom différent
- **Fix** : Calculer la longueur depuis les landmarks U1_tip → U1_apex si les deux sont posés, sinon désactiver l'affichage IMPA frontend (le backend a la valeur correcte)

#### P2 — Architecture : double `runAnalysis()` dans `useCephaloPersistence` + `useOrthoStore`
- **Problème** : Deux hooks indépendants implémentent la même logique d'upload/peuplement state → désynchronisation possible
- **Fix** : Faire en sorte que `useOrthoStore.runAnalysis()` délègue à `useCephaloPersistence.runAnalysis()` (ou fusionner en un seul store — sprint dédié)

# 📓 Journal de Session - Digital Crown

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

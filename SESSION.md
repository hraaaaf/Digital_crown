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

---

### 📋 Points de Vigilance
- **Backup service** : Le service de backup quotidien tente de sauvegarder `clinical_vault.db` qui n'est pas un SQLite valide dans l'environnement actuel → log `file is not a database`. Non bloquant mais à investiguer.
- **Endpoints AI lents** : `GET /api/patients/{id}/ai-summary` peut encore prendre plusieurs secondes selon la taille du dossier. Avec le fix pool, ça ne bloquera plus les autres requêtes mais l'UX gagnerait d'un skeleton loader côté frontend.

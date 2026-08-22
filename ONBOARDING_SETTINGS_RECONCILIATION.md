# Digital Crown — Onboarding ↔ Réglages / Clinic Identity Reconciliation

Status: **ACTIVE — P0 certification candidate; final contract run pending**

Branch: `agent/onboarding-settings-reconciliation`
PR: `#214` (draft)
Product audit base: `master@2bfe24fc62a79af0a13852cd091bd65c3e0fd384`

## Goal

Établir une seule vérité cohérente pour l’identité et la configuration du cabinet depuis la première création de compte jusqu’aux Réglages et à tous les consommateurs produit.

Chaîne réelle à réconcilier :

`Inscription / activation essai → onboarding → modèle backend/DB → Réglages → consommateurs → reprise de session`

Aucun déploiement Vercel sans autorisation explicite.

## Succès global

- [x] Inventaire onboarding
- [x] Inventaire Réglages correspondant
- [x] Modèles/API/DB actuels cartographiés
- [x] Entrées compte classiques + essai cartographiées
- [x] Doublons, champs morts, fallbacks et divergences majeures identifiés
- [x] Consommateurs directs principaux identifiés
- [x] Tests existants et trous de couverture inventoriés
- [x] BEFORE capturé : 70 écrans, 5 viewports
- [x] Défauts responsive BEFORE consignés
- [ ] Run contractuel final vert au HEAD candidat
- [ ] P1 modèle métier canonique
- [ ] P2 onboarding réconcilié
- [ ] P3 Réglages réconciliés
- [ ] P4 persistance/permissions durcies
- [ ] P5 legacy/migration
- [ ] P6 consommateurs réconciliés
- [ ] P7 certification UX AFTER
- [ ] P8 régression/closeout final

Aucun code produit n’a été modifié pendant P0.

---

# P0 — Audit & Truth Map

## 1. Entrées produit réelles

### Inscription classique

Frontend : `RegisterPage.tsx` → `authService.register()` → `POST /api/auth/signup`.

Le frontend envoie actuellement :
- email ;
- mot de passe ;
- `nom_complet` ;
- consentements.

Le backend `signup_client()` crée un `User` inactif/non licencié. Il **ne crée pas de `CabinetConfig`**.

Après validation SuperAdmin, l’utilisateur se connecte puis `init-status` le dirige vers le wizard si aucune configuration cabinet n’existe.

### Activation d’essai par code

Frontend : `ActivateTrialPage.tsx` → `POST /api/public/activate-trial`.

Le backend crée ou active :
- `User` ;
- `CabinetConfig(owner_id=user.id)` avec `is_initialized=False` ;
- nom cabinet/praticien partiellement prérempli.

L’utilisateur est ensuite invité à se connecter pour finaliser l’installation.

### Divergence d’entrée

Le même onboarding reçoit donc deux états initiaux différents :
1. classique : `User` sans `CabinetConfig` ;
2. essai : `User + CabinetConfig(is_initialized=false)`.

Le wizard final utilise pourtant le même `POST /api/clinics/`, dont l’ownership n’est pas lié au user authentifié. C’est une divergence structurelle P1/P4, pas un simple détail UX.

---

## 2. Onboarding réel

Module : `frontend/src/features/admin/SetupWizard/`.

7 étapes :
1. Identité
2. Spécialités
3. Contacts & identifiants
4. QR
5. Design documents
6. Thème applicatif
7. Confirmation

Persistance temporaire :
- wizard → `sessionStorage.digitalcrown-setup-storage` ;
- thème → `localStorage.digitalcrown_theme` immédiatement avant ACK backend.

Soumission finale :
1. `POST /api/clinics/`
2. upload logo éventuel
3. upload letterhead éventuel
4. reset store
5. dashboard

Ce flux n’est pas atomique.

Validation actuelle faible :
- étape 1 : nom cabinet/praticien/adresse non vides ;
- étape 2 : au moins une spécialité prédéfinie ;
- étape 3 : au moins un contact actif/non vide ;
- pas de validation métier forte observée pour ICE/IF/INPE.

Une spécialité personnalisée seule ne valide pas l’étape 2.

---

## 3. Réglages réel

Module : `frontend/src/features/admin/Settings/`.

Onglets :
- Profil Cabinet
- Design & Ambiance
- Catalogue Actes
- Horaires & Agenda
- Performance & Assistance
- Sécurité & Backup
- Mon Équipe

`SettingsContainer` est correctement fail-closed pour les surfaces profil : échec `GET /clinics/me` → état d’erreur + Réessayer, pas valeurs fictives modifiables.

Le frontend masque l’accès selon permissions, mais le backend n’applique pas encore ces permissions sur les mutations cabinet.

---

## 4. Modèle réel

### User

Porte actuellement :
- auth/session ;
- rôle ;
- permissions ;
- `nom_complet` ;
- coordonnées utilisateur ;
- `identifiants_legaux` JSON ;
- hiérarchie équipe via `employer_id` ;
- licence/abonnement.

`get_employer_id()` retourne l’employeur pour un sous-compte, sinon l’ID propre.

### CabinetConfig

Porte actuellement :
- identité structure ;
- praticien principal global ;
- type `PRIVE | CLINIQUE` ;
- spécialités ;
- contacts ;
- ICE / IF / INPE ;
- branding/documents ;
- QR ;
- thème ;
- préférences runtime ;
- `is_initialized`.

`owner_id` est unique : un owner possède au plus un `CabinetConfig`.

Le switch multi-cabinet frontend n’a pas de modèle backend correspondant démontré.

Aucun modèle `Administration` ou `Practice` n’a été trouvé.

`DocumentFactory.create_installment_plan()` référence `models.Clinic`, alors qu’aucune classe `Clinic` n’a été trouvée dans `backend/models.py`.

---

## 5. Matrice canonique P0

| Donnée métier | Onboarding | Réglages | Backend/DB | Verdict |
|---|---|---|---|---|
| Type structure | `cabinetType` | `cabinet_type` | `CabinetConfig.cabinet_type` | KEEP + FIX |
| Nom structure | `nomCabinet` | `nom_cabinet` | `CabinetConfig.nom_cabinet` | KEEP |
| Nom praticien FR | `nomPraticien` | `nom`/`nom_praticien` | `CabinetConfig.nom_praticien` + `User.nom_complet` | MERGE / DECIDE |
| Nom praticien AR | oui | oui | `CabinetConfig.nom_praticien_ar` | KEEP + ownership |
| Adresse structure | `adresse` | `adresse` | `footer_address` | KEEP + RENAME futur |
| Contacts structurés | `contacts_json` | `contacts_json` | `CabinetConfig.contacts_json` | KEEP canonique |
| `footer_phones` | dérivé | dérivé | persisté séparément | DUPLICATE |
| ICE | oui | oui | CabinetConfig + fallback User | MERGE |
| IF | frontend `if_` | `if` | alias Pydantic `if` → colonne `if_` | KEEP + FIX |
| INPE | oui | oui | CabinetConfig + fallback User | MERGE |
| Spécialités prédéfinies | oui | oui | `specialty_ids` | KEEP |
| Spécialité custom FR/AR | oui | oui | aucun champ DB/schema | DEAD / MISSING |
| Header FR/AR | généré | éditable/généré | CabinetConfig | KEEP + dériver |
| Logo | upload | upload/suppression | endpoint dédié | KEEP + atomicité |
| Letterhead | upload | upload/suppression | endpoint dédié | KEEP + atomicité |
| Couleurs/police/marges | oui | oui | CabinetConfig | KEEP |
| Template | défaut `swiss` | défaut `swiss` | défaut backend `classic` | DUPLICATE |
| QR | oui | oui | CabinetConfig | KEEP + sémantique |
| Thème UI | localStorage immédiat | preview puis save | backend + localStorage | DUPLICATE |
| Runtime prefs | non | oui | CabinetConfig + cache | SETTINGS ONLY |
| `activeCabinetId` | non | oui | localStorage seulement | FAKE / DEAD |

---

## 6. Défauts P0 prouvés

### CRITICAL

**P0-CRIT-01 — création cabinet sans authentification**

`POST /api/clinics/` n’a pas `get_current_user`. Il choisit le premier ADMIN/DENTISTE sans employeur, trié par date de création. Ownership potentiellement mauvais et frontière auth absente.

**P0-CRIT-02 — permissions Réglages absentes côté backend**

`PUT /clinics/me`, upload logo et letterhead exigent l’auth mais pas la permission `settings/admin`. Un sous-compte peut contourner l’UI.

**P0-CRIT-03 — payload Profil Réglages incompatible avec schema strict**

`CabinetConfigUpdate` utilise `extra="forbid"`, tandis que `saveProfile()` envoie le profil complet avec notamment `custom_specialty_fr`, `custom_specialty_ar`, `logo_path`, absents du schema update. Contrat attendu : 422.

### HIGH

**P0-HIGH-04 — IF perdu à la création** : wizard envoie `if_`, `CabinetConfigCreate` attend l’alias entrant `if` sans `populate_by_name=True`.

**P0-HIGH-05 — spécialité personnalisée non persistée** : UI onboarding + Réglages sans modèle/schema correspondant.

**P0-HIGH-06 — onboarding non atomique** : cabinet marqué initialisé avant uploads logo/letterhead séparés.

**P0-HIGH-07 — erreur init assimilée à setup requis** : `App.tsx` met `isInitialized=false` sur erreur de contrôle.

**P0-HIGH-08 — thème persisté localement avant ACK backend**.

**P0-HIGH-09 — faux succès offline desktop** : l’intercepteur Axios annonce « mise en file d’attente », renvoie un HTTP 200 synthétique `{_offline:true}`, mais n’appelle jamais `MobileStorage.enqueueAction`. La vraie queue IndexedDB existe côté mobile uniquement.

**P0-HIGH-10 — AccountingGenerator utilise `owner_id == user_id`** au lieu de l’employeur canonique pour un sous-compte.

**P0-HIGH-11 — `models.Clinic` fantôme** dans le chemin échéancier.

**P0-HIGH-17 — entrées compte divergentes** : signup classique sans CabinetConfig vs essai avec CabinetConfig non initialisé, puis même POST global non lié au user.

**P0-HIGH-20 — onboarding mobile overflow systématique** : les 7 étapes débordent sur 430 et 390 px. Mesure Playwright : `scrollWidth=569` pour les 14 captures concernées. Cause principale : stepper 7 pastilles `w-12` + `gap-4` + labels `whitespace-nowrap` dans un conteneur `px-8`.

### MEDIUM

**P0-MED-12 — faux multi-cabinet frontend** sans backend persistant correspondant.

**P0-MED-13 — identifiants légaux double source** : CabinetConfig puis `User.identifiants_legaux` fallback.

**P0-MED-14 — contacts double représentation** : `contacts_json` + `footer_phones` persisté.

**P0-MED-15 — confirmation onboarding incomplète / QR mal nommé**.

**P0-MED-16 — defaults frontend/backend divergents**, notamment `swiss` vs `classic`.

**P0-MED-18 — mot de passe frontend/backend incohérent** : Register + ActivateTrial autorisent `minLength=4`; backend exige 8.

**P0-MED-19 — message signup trompeur** : « Votre cabinet a bien été pré-enregistré » alors que signup classique ne crée qu’un User.

---

## 7. Ce qui est bien conçu et doit être conservé

- `CabinetConfig.owner_id` + `User.get_employer_id()` donnent une base simple pour un cabinet partagé par une équipe.
- `contacts_json` est la meilleure représentation structurée actuelle des coordonnées.
- `specialty_ids` est correctement structuré.
- Branding/QR/document sont centralisés dans CabinetConfig.
- Settings est fail-closed sur erreur de lecture profil.
- `PUT /clinics/me` utilise `exclude_unset=True`, donc pas de reset massif des champs absents.
- La hiérarchie équipe via `employer_id` est explicite.
- La queue mobile IndexedDB existe réellement, mais ne doit pas être confondue avec le comportement offline desktop.

---

## 8. Tests existants et trous

Couverture existante observée :
- `/clinics/me` auth ;
- `init-status` auth/tenant ;
- création config sur GET `/me` ;
- aliases update ;
- logo/letterhead ;
- whitelist stricte ;
- isolation tenant ;
- Settings store fail-closed avec API mockée.

Trous majeurs :
- POST `/clinics/` anonyme refusé ;
- owner binding exact ;
- IF round-trip ;
- custom specialty round-trip ;
- vrai payload Settings contre vrai schema backend ;
- permission backend Settings ;
- reprise après upload partiel ;
- erreur init fail-closed ;
- offline sans faux ACK ;
- sous-compte document comptable ;
- échéancier sans modèle fantôme ;
- SetupWizard E2E central.

---

## 9. BEFORE certifié comme preuve d’audit

Run source : `32560178433`
Artifact : `9472575193 — onboarding-settings-p0-before`
Digest : `sha256:4b80b57fd7d0dd5f33d98c04fbbb78cb5623b51056fef6df1227054e0cbefa95`

Contenu :
- 70 screenshots ;
- onboarding 7 étapes ;
- Réglages 7 onglets ;
- viewports 1440 / 1024 / 768 / 430 / 390 ;
- 0 erreur runtime/pageerror/console enregistrée ;
- 14 overflows, exclusivement SetupWizard 430/390 ;
- Réglages sans overflow sur les 5 viewports.

Le run visuel est rouge **parce que le baseline contient un défaut produit**, pas parce que la capture a échoué. Les 70 preuves sont présentes. P0 enregistre donc l’overflow comme finding et ne demande pas que le produit soit corrigé avant de fermer l’audit.

---

## 10. Architecture candidate P1

Hypothèse dominante à valider, sans créer de tables par réflexe :

### User
Auth, session, rôle, permissions, identité de compte.

### Organization / Cabinet
Faire de `CabinetConfig` la vérité organisationnelle : nom structure, type, adresse, contacts, identité légale, branding, préférences partagées.

### Practitioner
Ne créer une table distincte que si un praticien doit exister indépendamment d’un compte utilisateur. Sinon porter l’identité professionnelle par User + relation au cabinet.

### Membership
`employer_id` suffit tant que le produit reste mono-organisation. Une table Membership ne devient justifiée qu’avec un vrai besoin multi-organisation/multi-site ou rôles par organisation.

### Règle
Ne pas construire une architecture multi-cabinet parce qu’un switch frontend mort existe.

---

## 11. Tests obligatoires du chantier

T1 fresh install
T2 reload
T3 restart
T4 edit Settings → reload
T5 GET/SAVE failure fail-closed
T6 validation + Unicode FR/AR
T7 permissions
T8 multi-user
T9 consumer truth
T10 legacy
T11 anonymous clinic create refusé
T12 owner binding exact
T13 IF round-trip
T14 custom specialty round-trip ou suppression
T15 payload Settings réel → backend
T16 sous-compte sans settings refusé
T17 sous-compte autorisé explicitement défini
T18 reprise après upload partiel
T19 init-status indisponible → erreur, jamais faux setup
T20 offline → pending/error, jamais faux persisted
T21 sous-compte → config employeur dans documents
T22 échéancier sans `models.Clinic` fantôme
T23 password contract frontend/backend identique
T24 signup classic/trial convergent avant onboarding
T25 SetupWizard 390/430 sans overflow après correction UX

---

## 12. Roadmap

- **P0 — Audit & Truth Map** : certification candidate, contrat final à passer.
- **P1 — Canonical Data Model** : ownership + source de vérité minimale.
- **P2 — Onboarding Product Reconciliation** : REQUIRED NOW / OPTIONAL NOW / LATER / REMOVE.
- **P3 — Settings Reconciliation** : même contrat canonique.
- **P4 — Backend / Persistence / Permissions** : auth, permissions, validation, atomicité, erreurs.
- **P5 — Legacy Migration** : fresh/existing/partial/renamed/invalid/upgrade.
- **P6 — Consumer Reconciliation** : tous consommateurs sur vérité canonique.
- **P7 — UX Certification** : Goal visuel + mockup + AFTER + score.
- **P8 — Regression & Closeout** : tests globaux + docs + Git.

Pourcentage global : ne créditer P0 qu’après run contractuel vert et closeout documentaire. Aucun pourcentage intermédiaire inventé.

---

## Preuves code principales

- `frontend/src/App.tsx`
- `frontend/src/pages/RegisterPage.tsx`
- `frontend/src/pages/ActivateTrialPage.tsx`
- `frontend/src/services/auth.ts`
- `frontend/src/services/api.ts`
- `frontend/src/features/admin/SetupWizard/SetupWizard.tsx`
- `frontend/src/features/admin/SetupWizard/store/useSetupStore.ts`
- `frontend/src/features/admin/SetupWizard/steps/*`
- `frontend/src/features/admin/Settings/SettingsContainer.tsx`
- `frontend/src/features/admin/Settings/hooks/useSettingsStore.ts`
- `frontend/src/features/admin/Settings/types.ts`
- `frontend/src/utils/settingsAccess.ts`
- `backend/routers/auth.py`
- `backend/routers/public.py`
- `backend/routers/clinics.py`
- `backend/routers/team.py`
- `backend/schemas/auth.py`
- `backend/schemas/cabinet.py`
- `backend/models.py`
- `backend/services/document_factory.py`
- `backend/services/generators/accounting_gen.py`
- `backend/tests/test_clinics_router.py`
- `backend/tests/test_clinics_config.py`
- `backend/tests/test_clinic_init_status_tenant.py`
- `backend/tests/test_cabinet_settings_strict_whitelist.py`
- `frontend/src/features/admin/Settings/hooks/useSettingsStore.test.ts`

---

## Reprise

Chantier : `Onboarding ↔ Réglages`
Lot : `P0 — Audit & Truth Map`
Produit modifié : **non**
BEFORE : **70 captures acquises**
Finding UX principal : **SetupWizard overflow 569 px sur viewports 430/390**
Next exact : **run contractuel P0 vert → closeout P0 → P1 modèle canonique**.

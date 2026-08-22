# Digital Crown — Onboarding ↔ Réglages / Clinic Identity Reconciliation

Status: **ACTIVE — P0 CLOSED / P1 ACTIVE**

Branch: `agent/onboarding-settings-reconciliation`
PR: `#214` (draft)
Product audit base: `master@2bfe24fc62a79af0a13852cd091bd65c3e0fd384`
Current certified HEAD before this closeout: `eecb28cedd65bac8196ce8002c42893ad3ada28c`

## Goal

Établir une seule vérité cohérente pour l’identité et la configuration du cabinet depuis la première création de compte jusqu’aux Réglages et à tous les consommateurs produit.

Chaîne réelle :

`Inscription / activation essai → onboarding → modèle backend/DB → Réglages → consommateurs → reprise de session`

Aucun déploiement Vercel sans autorisation explicite.

## Mesure d’avancement

Le chantier comprend 9 lots canoniques P0→P8. Le pourcentage global est calculé uniquement sur les **lots entièrement certifiés** : `lots certifiés / 9`.

- P0 certifié : 1/9
- Avancement global certifié : **11,1 %**

Un lot partiellement réalisé ne reçoit aucun crédit intermédiaire.

---

# P0 — Audit & Truth Map — CLOSED ✅

## Goal P0

Cartographier sans modification produit les données, contrats, propriétaires, fallbacks, consommateurs, erreurs de persistance et surfaces UX entre création de compte, onboarding et Réglages.

## Succès P0

- [x] Inventaire onboarding
- [x] Inventaire Réglages correspondant
- [x] Modèles/API/DB actuels cartographiés
- [x] Entrées compte classique + essai cartographiées
- [x] Doublons, champs morts, fallbacks et divergences majeures identifiés
- [x] Consommateurs directs principaux identifiés
- [x] Tests existants et trous de couverture inventoriés
- [x] BEFORE : 70 écrans / 5 viewports
- [x] Responsive et erreurs runtime mesurés
- [x] Contrats critiques exécutés au HEAD
- [x] Aucun changement produit dans P0

## Preuves P0

### Contrat

Run : `32560853707 — Onboarding Settings P0 Certification #3`
Conclusion : **SUCCESS**
HEAD : `eecb28cedd65bac8196ce8002c42893ad3ada28c`

Le run prouve notamment :
- asymétrie IF à la création ;
- extras Settings rejetés par le schéma strict ;
- création cabinet sans `current_user` ;
- mutation cabinet sans permission Settings backend ;
- GET `/clinics/me` avec création/commit sur lecture ;
- mot de passe frontend 4 vs backend 8 ;
- signup classique = User sans CabinetConfig ;
- activation essai = User + CabinetConfig non initialisé ;
- erreur init convertie en `isInitialized=false` ;
- thème onboarding écrit localement avant ACK backend ;
- faux succès offline desktop ;
- consommateur comptable lié au raw `user_id` ;
- référence fantôme `models.Clinic`.

### BEFORE visuel

Run source : `32560178433`
Artifact : `9472575193 — onboarding-settings-p0-before`
Digest : `sha256:4b80b57fd7d0dd5f33d98c04fbbb78cb5623b51056fef6df1227054e0cbefa95`

Contenu :
- 70 screenshots ;
- onboarding 7 étapes ;
- Réglages 7 onglets ;
- 1440 / 1024 / 768 / 430 / 390 px ;
- 0 erreur `pageerror` / console enregistrée ;
- 14 overflows, exclusivement SetupWizard à 430/390 ;
- `scrollWidth=569` sur les 14 écrans concernés ;
- Réglages sans overflow sur les 5 viewports.

Le run BEFORE est rouge uniquement parce qu’il détecte ce défaut produit. La capture elle-même a abouti et constitue la preuve d’audit.

## Entrées produit réelles

### Inscription classique

`RegisterPage.tsx → authService.register() → POST /api/auth/signup`.

Le frontend envoie email, mot de passe, `nom_complet`, consentements. `signup_client()` crée un `User` inactif/non licencié et **aucun CabinetConfig**. Après validation SuperAdmin, la première connexion mène au setup si aucune config n’existe.

### Activation d’essai

`ActivateTrialPage.tsx → POST /api/public/activate-trial`.

Le backend crée/active `User` et crée `CabinetConfig(owner_id=user.id, is_initialized=False)` avec identité partielle, puis demande à l’utilisateur de finaliser l’installation.

### Divergence

Le wizard reçoit donc deux états :
1. classique : User seul ;
2. essai : User + CabinetConfig non initialisé.

Il termine pourtant via le même `POST /api/clinics/`, dont l’ownership n’est pas lié au user authentifié.

## Modèle actuel

### User

Porte auth/session, rôle, permissions, `nom_complet`, coordonnées utilisateur, `identifiants_legaux`, licence/abonnement et hiérarchie équipe via `employer_id`.

`get_employer_id()` retourne l’employeur pour un sous-compte, sinon l’ID propre.

### CabinetConfig

Porte identité structure, praticien principal global, type `PRIVE | CLINIQUE`, spécialités, contacts, ICE/IF/INPE, branding/document, QR, thème, préférences runtime et `is_initialized`.

`owner_id` est unique : un owner possède au plus un CabinetConfig.

Le switch multi-cabinet frontend n’a pas de modèle backend persistant démontré.

### Practitioner déjà implicite

`Acte.praticien_id` pointe sur `users.id`, et l’équipe peut contenir des `User(role=DENTISTE)` secondaires via `employer_id`. Le produit traite donc déjà `User` comme praticien réel.

## Matrice P0

| Donnée | Onboarding | Réglages | DB actuelle | Verdict |
|---|---|---|---|---|
| Type structure | `cabinetType` | `cabinet_type` | CabinetConfig | KEEP + FIX |
| Nom structure | `nomCabinet` | `nom_cabinet` | CabinetConfig | KEEP |
| Nom praticien FR | `nomPraticien` | `nom` / `nom_praticien` | CabinetConfig + User | MERGE |
| Nom praticien AR | oui | oui | CabinetConfig | MOVE/DECIDE |
| Adresse structure | `adresse` | `adresse` | `footer_address` | KEEP + RENAME futur |
| Contacts structurés | `contacts_json` | `contacts_json` | CabinetConfig | KEEP canonique |
| `footer_phones` | dérivé | dérivé | persisté | DUPLICATE |
| ICE | oui | oui | CabinetConfig + fallback User | MERGE |
| IF | frontend `if_` | `if` | alias `if` → colonne `if_` | KEEP + FIX |
| INPE | oui | oui | CabinetConfig + fallback User | SPLIT OWNER |
| Spécialités | oui | oui | `specialty_ids` | KEEP |
| Spécialité custom | oui | oui | aucune persistance | DEAD/MISSING |
| Header FR/AR | généré | éditable/généré | CabinetConfig | DERIVE |
| Logo / letterhead | upload | upload | CabinetConfig | KEEP + atomicité |
| Couleurs/police/marges | oui | oui | CabinetConfig | KEEP |
| Template | `swiss` | `swiss` | backend `classic` | FIX DEFAULT |
| QR | oui | oui | CabinetConfig | KEEP + sémantique |
| Thème UI | localStorage immédiat | preview/save | backend + localStorage | FIX |
| Runtime prefs | non | oui | CabinetConfig | SETTINGS ONLY |
| `activeCabinetId` | non | oui | localStorage | REMOVE/DEAD |

## Findings P0

### CRITICAL

**P0-CRIT-01 — création cabinet sans authentification**  
`POST /api/clinics/` choisit le premier ADMIN/DENTISTE sans employeur au lieu du user courant.

**P0-CRIT-02 — permissions Réglages absentes côté backend**  
Les mutations cabinet exigent l’auth, pas la permission `settings/admin` réellement appliquée côté UI.

**P0-CRIT-03 — payload Profil incompatible avec le schéma strict**  
`saveProfile()` envoie notamment `custom_specialty_fr/ar` et `logo_path`, alors que `CabinetConfigUpdate` les interdit.

### HIGH

- **P0-HIGH-04** IF perdu à la création (`if_` frontend vs alias `if`).
- **P0-HIGH-05** spécialité personnalisée non persistée.
- **P0-HIGH-06** onboarding non atomique avant uploads.
- **P0-HIGH-07** erreur init assimilée à setup requis.
- **P0-HIGH-08** thème écrit localement avant ACK backend.
- **P0-HIGH-09** faux succès offline desktop : HTTP 200 synthétique sans `enqueueAction`.
- **P0-HIGH-10** AccountingGenerator utilise `owner_id == user_id` au lieu de l’employeur canonique.
- **P0-HIGH-11** `models.Clinic` fantôme dans l’échéancier.
- **P0-HIGH-17** signup classique et essai produisent deux états initiaux divergents.
- **P0-HIGH-20** SetupWizard déborde à 430/390 ; cause primaire : stepper 7×`w-12`, `gap-4`, `whitespace-nowrap`, conteneur `px-8`.

### MEDIUM

- **P0-MED-12** faux multi-cabinet frontend.
- **P0-MED-13** identifiants légaux double source.
- **P0-MED-14** `contacts_json` + `footer_phones` double représentation.
- **P0-MED-15** confirmation onboarding incomplète / QR mal nommé.
- **P0-MED-16** defaults frontend/backend divergents (`swiss` vs `classic`).
- **P0-MED-18** password UI min 4 vs backend min 8.
- **P0-MED-19** signup annonce un cabinet pré-enregistré alors qu’il ne crée qu’un User.

## KEEP

- `User.get_employer_id()` + `CabinetConfig.owner_id` comme base mono-organisation.
- `contacts_json` comme structure canonique des contacts.
- `specialty_ids`.
- centralisation branding/QR/documents dans CabinetConfig.
- Settings fail-closed sur échec de lecture.
- `exclude_unset=True` sur update partiel.
- hiérarchie équipe `employer_id`.
- queue IndexedDB mobile réelle, distincte du faux comportement offline desktop.

---

# P1 — Canonical Data Model — ACTIVE

## Goal P1

Définir le modèle métier minimal qui donne un propriétaire unique à chaque donnée et couvre :
- dentiste seul ;
- cabinet avec assistant(e) ;
- clinique multi-praticiens ;
- centre dentaire à gestion centralisée ;
- inscription classique et activation essai ;
- documents produits au nom de la structure et/ou du praticien.

## Succès P1

P1 sera fermé uniquement si :
1. chaque donnée P0 reçoit un owner canonique ;
2. aucune nouvelle table n’est ajoutée sans besoin produit réel ;
3. la séparation identité compte / praticien / organisation est explicite ;
4. le multi-praticien fonctionne sans `nom_praticien` global ambigu ;
5. les identifiants légaux sont rattachés à leur vrai sujet ;
6. le modèle reste compatible avec le mono-organisation actuel ;
7. une stratégie legacy/backfill est définie avant P4/P5 ;
8. les consumers documentaires ont une règle explicite structure vs signataire.

## Hypothèse dominante déjà prouvée

Ne **pas** créer de table `Practitioner` maintenant :
- `Acte.praticien_id → User.id` existe déjà ;
- les dentistes secondaires sont déjà des User rattachés par `employer_id` ;
- créer Practitioner dupliquerait une identité métier existante sans besoin démontré.

Candidat minimal :

### User = compte + praticien

- authentification ;
- rôle/permissions ;
- nom professionnel/personnel ;
- coordonnées propres ;
- identifiants professionnels propres au praticien ;
- actes/signature quand le document dépend du praticien.

### CabinetConfig = organisation

- nom de structure ;
- type de structure ;
- adresse ;
- contacts ;
- identifiants fiscaux/organisationnels ;
- branding ;
- paramètres documentaires partagés ;
- QR ;
- thème/préférences partagées.

### employer_id = appartenance mono-organisation

Conserver tant que le produit ne démontre pas un vrai besoin multi-organisation/multi-site. Ne pas créer `Membership` ni une architecture multi-cabinet pour satisfaire un switch frontend mort.

### INPE

L’INPE doit être typé par sujet : il peut identifier un professionnel de santé ou un établissement. La future migration doit donc distinguer explicitement l’INPE praticien et l’INPE établissement au lieu de conserver un unique champ ambigu.

## Travail P1 restant

- vérifier tous les consommateurs de `nom_praticien`, `nom_praticien_ar`, ICE/IF/INPE ;
- définir la règle de signataire/document ;
- décider le rôle exact de `cabinet_type` sans inventer de modèle multi-site ;
- définir champs canoniques + aliases legacy + stratégie de migration ;
- produire la matrice source-of-truth P1 définitive.

---

# Tests obligatoires du chantier

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

# Roadmap

- **P0 — Audit & Truth Map — CLOSED ✅**
- **P1 — Canonical Data Model — ACTIVE**
- **P2 — Onboarding Product Reconciliation**
- **P3 — Settings Reconciliation**
- **P4 — Backend / Persistence / Permissions**
- **P5 — Legacy Migration**
- **P6 — Consumer Reconciliation**
- **P7 — UX Certification**
- **P8 — Regression & Closeout**

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

## Reprise

Chantier : `Onboarding ↔ Réglages`
Lot courant : `P1 — Canonical Data Model`
P0 : **CLOSED / run 32560853707 SUCCESS**
Produit modifié en P0 : **non**
BEFORE : **70 captures acquises**
Finding UX principal : **SetupWizard 569 px sur viewports 430/390**
Avancement global certifié : **11,1 % (1/9 lots)**
Next exact : **fermer la matrice propriétaire/signataire P1, puis définir champs canoniques et migration legacy avant P2**.

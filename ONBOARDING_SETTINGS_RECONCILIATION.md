# Digital Crown — Onboarding ↔ Réglages / Clinic Identity Reconciliation

Status: **ACTIVE — P0 code truth map written, certification pending**

Branch: `agent/onboarding-settings-reconciliation`
Base at creation: `master@2bfe24fc62a79af0a13852cd091bd65c3e0fd384`

## Goal

Établir une seule vérité cohérente pour l’identité et la configuration du cabinet/clinique/centre dentaire depuis le premier onboarding jusqu’aux Réglages, puis vérifier tous les consommateurs produit.

Chaîne canonique à réconcilier :

`Premier onboarding → modèle de données → backend/API → persistance → Réglages → consommateurs produit → reprise de session`

Aucun déploiement Vercel sans autorisation explicite.

## Succès global

- [x] Inventaire code des données demandées dans l’onboarding
- [x] Inventaire code des données correspondantes dans Réglages
- [x] Source backend/DB actuelle identifiée pour les données principales
- [x] Doublons, champs morts, fallbacks/sources concurrentes principales identifiés
- [ ] Modèle métier canonique final défini — P1
- [ ] Onboarding réduit au minimum réellement nécessaire — P2
- [ ] Réglages alignés sur le modèle canonique — P3
- [ ] Lecture/écriture/persistance/reload/restart vérifiés en runtime
- [ ] Permissions corrigées puis vérifiées en runtime
- [ ] Compatibilité legacy/migration vérifiée
- [ ] Tous les consommateurs produit utilisent la bonne donnée
- [ ] Captures BEFORE des surfaces onboarding + Réglages obtenues
- [ ] Toute UI touchée : BEFORE → Goal → mockup → AFTER → score
- [ ] Régression raisonnable verte

> P0 n’est pas certifié tant que les captures BEFORE et la preuve runtime ciblée ne sont pas obtenues. Aucun changement produit n’a été fait dans P0.

---

# P0 — Audit & Truth Map

## 1. Surface onboarding réelle

Module : `frontend/src/features/admin/SetupWizard/`

Le wizard comporte 7 étapes logiques :

1. **Identité** — type de structure, nom structure, praticien principal FR/AR, adresse.
2. **Spécialités** — spécialités prédéfinies + spécialité personnalisée FR/AR.
3. **Contacts & identifiants** — fixe/mobile/WhatsApp/Instagram, ICE, IF, INPE.
4. **QR** — VCARD, Website, Instagram, WhatsApp, Maps, Validation, Paiement.
5. **Design documents** — identité couleur, police, template, marges/scales, logo, letterhead.
6. **Thème applicatif** — thème UI.
7. **Confirmation** — résumé partiel puis soumission.

Store onboarding : `SetupWizard/store/useSetupStore.ts`.

Persistance temporaire :
- état wizard complet → `sessionStorage` sous `digitalcrown-setup-storage` ;
- thème applicatif → `localStorage.digitalcrown_theme` immédiatement, avant validation backend.

### Validation actuelle

- Étape 1 : `nomCabinet`, `nomPraticien`, `adresse` non vides.
- Étape 2 : au moins une spécialité **prédéfinie** dans `selectedSpecialties`.
- Étape 3 : au moins un contact activé et non vide.
- Pas de validation métier/format forte observée pour ICE/IF/INPE ou contacts dans le wizard.

Anomalie : une spécialité personnalisée seule ne satisfait pas l’étape 2, car la validation porte uniquement sur `selectedSpecialties.length`.

### Soumission finale

`SetupWizard.tsx` appelle successivement :

1. `POST /api/clinics/`
2. upload logo éventuel
3. upload letterhead éventuel
4. reset store
5. navigation dashboard

Ce flux n’est pas atomique : la configuration principale peut être marquée initialisée avant l’échec d’un upload logo/letterhead.

---

## 2. Surface Réglages réelle

Module : `frontend/src/features/admin/Settings/`

Onglets actuellement exposés selon permissions :
- Profil Cabinet
- Design & Ambiance
- Catalogue Actes
- Horaires & Agenda
- Performance & Assistance
- Sécurité & Backup
- Mon Équipe

Pour la réconciliation onboarding, les surfaces directement concernées sont surtout **Profil Cabinet**, **Design & Ambiance**, **Performance & Assistance**, puis **Mon Équipe** pour l’ownership.

`SettingsContainer.tsx` applique un fail-closed de lecture pour les onglets adossés au profil : si `GET /clinics/me` échoue, un état explicite d’erreur + Réessayer remplace les valeurs de repli. L’hypothèse initiale « fallback profil modifiable après échec GET » est donc **rejetée**.

Le store garde néanmoins des valeurs par défaut internes ; elles ne doivent jamais redevenir une vérité persistée ou modifiable en cas d’échec backend.

---

## 3. Modèle de données réel au HEAD audité

### `User`

Responsabilités actuellement observées :
- identité d’accès/authentication ;
- rôle ;
- permissions ;
- nom complet ;
- coordonnées personnelles/pro ;
- `identifiants_legaux` JSON ;
- hiérarchie d’équipe via `employer_id` ;
- abonnement/quota équipe.

`get_employer_id()` retourne `employer_id` pour un sous-compte, sinon l’ID propre.

### `CabinetConfig`

Responsabilités actuellement observées :
- identité du cabinet et praticien principal ;
- type `PRIVE | CLINIQUE` ;
- spécialités prédéfinies ;
- coordonnées affichées ;
- ICE / IF / INPE ;
- design documentaire ;
- logo / letterhead ;
- thème applicatif ;
- QR ;
- préférences runtime ;
- état `is_initialized`.

Ownership DB : **1 `CabinetConfig` maximum par `owner_id`** (`owner_id` unique).

Un champ `clinic_id` existe comme chaîne nullable, mais aucun mécanisme backend de switch multi-cabinet n’a été identifié dans ce flux.

### Modèles supposés puis invalidés

Aucun modèle `Administration` ni `Practice` n’a été trouvé dans `backend/models.py` au snapshot audité. Ils ne doivent donc pas être traités comme sources de vérité de ce chantier sans nouvelle preuve.

`DocumentFactory.create_installment_plan()` référence en revanche `models.Clinic`, alors qu’aucune classe `Clinic` n’a été trouvée dans `backend/models.py` : chemin consommateur à corriger/éliminer en P6 après test ciblé.

---

## 4. Matrice canonique de réconciliation — état actuel

| Donnée métier | Onboarding | Réglages | Backend/DB actuel | Source de vérité actuelle | Verdict P0 |
|---|---|---|---|---|---|
| Type structure | `cabinetType` | `cabinet_type` | `CabinetConfig.cabinet_type` | CabinetConfig | KEEP + FIX |
| Nom structure | `nomCabinet` | `nom_cabinet` | `CabinetConfig.nom_cabinet` | CabinetConfig | KEEP |
| Nom praticien principal FR | `nomPraticien` | `nom` → normalisé en `nom_praticien` | `CabinetConfig.nom_praticien` + `User.nom_complet` concurrent | ambiguë | MERGE / NEEDS DECISION |
| Nom praticien AR | oui | oui | `CabinetConfig.nom_praticien_ar` | CabinetConfig | KEEP + ownership à clarifier |
| Adresse structure | `adresse` → `footer_address` | `adresse` → normalisé `footer_address` | `CabinetConfig.footer_address` | CabinetConfig | KEEP + RENAME futur |
| Téléphones/contact rendu | dérivé en `footer_phones` | redérivé depuis contacts | `CabinetConfig.footer_phones` | dérivé | DUPLICATE |
| Contacts structurés | `contacts_json` | `contacts_json` | `CabinetConfig.contacts_json` | CabinetConfig | KEEP — candidat canonique |
| ICE | oui | oui | `CabinetConfig.ice` + fallback `User.identifiants_legaux` dans documents | concurrent | MERGE / NEEDS DECISION |
| IF | frontend envoie `if_` | Réglages utilise `if` | Pydantic alias entrant `if`, colonne `if_` | cassée à la création | KEEP + FIX |
| INPE | oui | oui | `CabinetConfig.inpe` + fallback User possible | concurrent | NEEDS DECISION |
| Spécialités prédéfinies | oui | oui | `CabinetConfig.specialty_ids` | CabinetConfig | KEEP |
| Spécialité personnalisée FR/AR | oui | oui | **aucun champ schema/model trouvé** | aucune | DEAD / MISSING BACKEND |
| Header FR/AR | généré | éditable/généré | `CabinetConfig.header_lines_fr/ar` | CabinetConfig | KEEP + FIX dérivation |
| Logo | fichier étape 5 | upload/suppression | `CabinetConfig.logo_path` via endpoint dédié | CabinetConfig | KEEP + FIX atomicité |
| Letterhead | fichier étape 5 | upload/suppression | `CabinetConfig.letterhead_path/use_letterhead` | CabinetConfig | KEEP + FIX atomicité |
| Couleurs documents | oui | oui | CabinetConfig | CabinetConfig | KEEP |
| Police document | oui | oui | CabinetConfig | CabinetConfig | KEEP |
| Template document | défaut frontend `swiss` | défaut frontend `swiss` | défaut schema/model `classic` | divergence defaults | KEEP + FIX |
| Marges/scales | oui | oui | CabinetConfig | CabinetConfig | KEEP |
| QR config | oui | oui | CabinetConfig | CabinetConfig | KEEP + FIX sémantique |
| Thème applicatif | oui + localStorage immédiat | preview puis save backend | CabinetConfig + localStorage | concurrent | KEEP + FIX |
| Préférences runtime | non | oui | CabinetConfig + localStorage cache | CabinetConfig attendu | LATER IN SETTINGS |
| `activeCabinetId` | non | oui | localStorage uniquement | aucune DB correspondante | FAKE / DEAD PATH |

---

## 5. Défauts P0 prouvés

### P0-CRIT-01 — création cabinet sans authentification

`POST /api/clinics/` n’a aucune dépendance `get_current_user`.

Il sélectionne le premier `ADMIN` ou `DENTISTE` sans employeur, trié par date de création. À défaut, il peut créer un administrateur depuis les secrets d’environnement.

**Impact** : ownership non déterministe vis-à-vis de l’utilisateur qui exécute l’onboarding ; frontière d’auth absente.

**Verdict** : `KEEP + FIX`, priorité P4 bloquante.

### P0-CRIT-02 — permissions Réglages non imposées côté backend

Le frontend applique `settings/admin`, mais les routes suivantes n’exigent que l’authentification :
- `PUT /clinics/me`
- upload logo
- upload letterhead

Un sous-compte authentifié sans permission Réglages peut donc contourner l’UI et appeler l’API directement.

**Verdict** : `KEEP + FIX`, priorité P4 bloquante.

### P0-CRIT-03 — payload Réglages incompatible avec le schéma strict

`CabinetConfigUpdate` utilise `extra="forbid"`.

`saveProfile()` envoie `{ ...profile, footer_phones, contacts_json }` ; le profil contient notamment :
- `custom_specialty_fr`
- `custom_specialty_ar`
- `logo_path`
- potentiellement `header_customized`

Ces champs ne sont pas définis dans `CabinetConfigUpdate` au snapshot audité.

**Conséquence contractuelle** : le backend Pydantic doit rejeter ces extras en 422. Les tests frontend actuels mockent `api.put` et ne traversent donc pas le vrai schéma backend.

**Verdict** : `KEEP + FIX`, priorité P3/P4 bloquante.

### P0-HIGH-04 — IF silencieusement perdu à la création

Frontend/types onboarding : `if_`.

Backend create : champ Pydantic interne `if_` avec alias entrant `if`, mais `CabinetConfigCreate` n’active pas `populate_by_name=True`.

La création appelle `model_dump(exclude_unset=True)` ; un `if_` envoyé par le frontend n’est donc pas reconnu comme champ explicitement défini et ne rejoint pas la DB.

`CabinetConfigUpdate`, lui, active `populate_by_name=True`, d’où une asymétrie create/update.

**Verdict** : `KEEP + FIX`.

### P0-HIGH-05 — spécialité personnalisée saisie mais non persistée

Le wizard et les Réglages exposent `custom_specialty_fr/ar`.

Aucun champ correspondant n’a été trouvé dans `CabinetConfigBase` ni `CabinetConfig`.

À la création, les extras sont ignorés par le modèle create par défaut ; à l’update strict, ils deviennent invalides.

**Verdict** : `DEAD / MISSING BACKEND`. Décider en P1 : ajouter au modèle canonique ou retirer l’UI.

### P0-HIGH-06 — onboarding non atomique

Le POST principal marque `is_initialized=True` puis les fichiers sont uploadés dans des requêtes séparées.

Un échec logo/letterhead après le POST peut laisser :
- cabinet initialisé ;
- wizard affichant un échec ;
- fichiers/configuration partiels ;
- prochain contrôle d’init susceptible d’empêcher de reprendre naturellement le wizard.

**Verdict** : `KEEP + FIX`.

### P0-HIGH-07 — erreur d’init frontend confondue avec « setup requis »

Dans `App.tsx`, une erreur lors de `checkInitStatus()` conduit à `isInitialized=false`.

Une indisponibilité backend peut donc être interprétée comme « cabinet non initialisé » et rediriger vers `/setup` au lieu d’un état d’erreur explicite.

**Verdict** : `FAKE/FALLBACK`, à rendre fail-closed.

### P0-HIGH-08 — thème onboarding persisté avant succès backend

L’étape thème écrit immédiatement `digitalcrown_theme` dans `localStorage`. La confirmation visuelle de l’étape ne contrôle pas cette persistance.

Un onboarding abandonné ou un POST final échoué peut donc laisser un thème durable qui n’existe pas dans la vérité backend.

**Verdict** : `DUPLICATE / KEEP + FIX`.

### P0-HIGH-09 — succès synthétique offline pour les mutations

L’intercepteur Axios global transforme une mutation réseau échouée alors que `navigator.onLine === false` en réponse synthétique HTTP 200 `{ _offline: true }`.

Le wizard et `saveProfile()` traitent toute promesse résolue comme succès backend. Ils peuvent donc reset/naviguer ou afficher « Configuration enregistrée » sans confirmation serveur.

La présence réelle d’une file de synchronisation durable n’a pas été prouvée dans P0 ; indépendamment de cela, le contrat UX actuel ne distingue pas « mis en attente » de « persisté ».

**Verdict** : `FAKE/FALLBACK`, bloquant pour la vérité de persistance.

### P0-HIGH-10 — consommateur comptable n’utilise pas l’employeur canonique

`AccountingGenerator.generate_note()` recherche `CabinetConfig.owner_id == user_id` directement.

Or le reste de l’architecture équipe utilise `current_user.get_employer_id()` pour partager le cabinet entre propriétaire et sous-comptes.

Un dentiste rattaché peut donc ne pas retrouver la configuration cabinet pour un document comptable et tomber sur des valeurs de repli.

**Verdict** : `KEEP + FIX`, P6.

### P0-HIGH-11 — générateur d’échéancier référence un modèle `Clinic` introuvable

`DocumentFactory.create_installment_plan()` appelle `models.Clinic`, mais aucune classe `Clinic` n’a été trouvée dans `backend/models.py` au snapshot audité.

**Verdict** : `DEAD/BROKEN CONSUMER` à confirmer par test ciblé P6.

### P0-MED-12 — multi-cabinet UI sans backend correspondant

DB : `CabinetConfig.owner_id` unique, donc un owner possède au plus un `CabinetConfig`.

Réglages : `activeCabinetId`, `switchCabinet()` et `active_cabinet_id` existent, mais `fetchProfile()` ne charge que `/clinics/me` et construit un tableau d’un seul cabinet.

**Verdict** : `FAKE / DEAD PATH`. Ne pas bâtir P1 autour du multi-cabinet tant qu’un vrai besoin et un vrai modèle ne sont pas décidés.

### P0-MED-13 — identifiants légaux en double source

Le footer document lit d’abord ICE/IF/INPE depuis `CabinetConfig`, puis utilise `User.identifiants_legaux` en fallback.

**Verdict** : `DUPLICATE / NEEDS DECISION`.

### P0-MED-14 — contacts en double représentation

`contacts_json` stocke la structure réelle ; `footer_phones` est reconstruit avec emojis et texte puis persisté séparément.

**Verdict** : garder `contacts_json` comme candidat canonique et rendre `footer_phones` dérivé/compatibilité, pas une seconde vérité éditable.

### P0-MED-15 — confirmation onboarding incomplète

L’étape 7 annonce « Vérifiez vos préférences finales » mais n’affiche notamment pas :
- nom de la structure ;
- ICE / IF / INPE ;
- détail complet des options documentaires.

Elle présente aussi toute configuration QR sous l’intitulé « Signature Digitale », y compris les QR qui ne sont pas une signature.

**Verdict** : `KEEP + FIX` UX, P2/P7.

### P0-MED-16 — defaults frontend/backend divergents

Exemple prouvé : `selected_template` vaut `swiss` dans le frontend onboarding/Réglages, mais `classic` dans le schéma/modèle backend par défaut.

**Verdict** : `DUPLICATE`, définir un seul défaut canonique.

---

## 6. Ce qui est correctement conçu et doit être conservé

### KEEP

- `CabinetConfig.owner_id` + `User.get_employer_id()` donnent une base simple pour un cabinet partagé par une équipe.
- `contacts_json` est une bonne représentation structurée des coordonnées.
- `specialty_ids` stocke les spécialités prédéfinies de façon structurée.
- Les réglages de design/QR/document sont regroupés dans `CabinetConfig`, ce qui permet aux générateurs de documents de consommer une configuration commune.
- `SettingsContainer` bloque correctement les surfaces Profil/Design/Performance si la lecture backend `/clinics/me` échoue.
- `PUT /clinics/me` utilise `model_dump(exclude_unset=True)` : les champs absents d’un payload partiel ne sont pas remis à leurs defaults.
- La hiérarchie équipe `User.employer_id` est explicite et les routes Team limitent la gestion aux comptes principaux.

---

## 7. Source de vérité recommandée pour P1 — proposition, pas encore décision finale

Le modèle minimal recommandé à tester contre les 4 scénarios métier :

### User
- login/session ;
- rôle ;
- permissions ;
- appartenance à l’organisation via `employer_id` tant que le modèle reste mono-organisation.

### Practitioner
Ne pas créer une nouvelle table par réflexe. D’abord évaluer si `User` suffit pour porter :
- nom professionnel ;
- coordonnées propres ;
- données professionnelles propres au praticien.

Une entité Practitioner distincte ne devient justifiée que si un praticien doit exister indépendamment d’un compte utilisateur.

### Organization / Cabinet
`CabinetConfig` est le candidat naturel à faire évoluer vers la vérité organisationnelle :
- nom structure ;
- type structure ;
- adresse ;
- contacts ;
- identité légale organisationnelle ;
- branding/document ;
- préférences partagées.

### Membership
Le lien `User.employer_id` est actuellement suffisant pour le modèle mono-organisation. Ne créer une vraie table Membership que si P1 valide un besoin multi-organisation/multi-site ou des rôles par organisation.

### Règle P1
Ne pas créer un modèle « multi-cabinet » simplement parce qu’un switch UI existe déjà. Le code actuel ne prouve pas le besoin métier ni l’implémentation.

---

## 8. Tests existants — couverture et trous

### Backend présent

Tests observés autour de :
- `/clinics/me` auth ;
- `init-status` auth + tenant ;
- création de config sur GET `/me` ;
- update aliases ;
- logo/letterhead ;
- strict whitelist update ;
- isolation tenant.

### Trous importants

Aucun test identifié qui prouve :
- `POST /clinics/` refuse l’anonyme ;
- le POST est lié au `current_user` ;
- le IF onboarding atteint la DB ;
- une spécialité personnalisée atteint la DB ;
- le vrai payload `saveProfile()` traverse `CabinetConfigUpdate` ;
- un sous-compte sans permission `settings` est refusé par `PUT /clinics/me` ;
- atomicité/reprise après échec logo/letterhead ;
- thème onboarding non persisté après échec ;
- génération document comptable par dentiste rattaché ;
- `models.Clinic` dans l’échéancier.

### Frontend présent

Les tests `useSettingsStore` vérifient correctement la doctrine :
- échec backend → pas de faux `saveSuccess` ;
- succès mocké → saved ;
- runtime preferences persistées seulement après succès mocké.

Limite : `api.put` est mocké, donc ces tests ne détectent ni le 422 réel du schéma strict ni le succès synthétique offline de l’intercepteur Axios.

Aucun test SetupWizard dédié n’a été identifié dans la suite centrale auditée.

---

## 9. Scénarios métier — verdict code actuel

### A. Chirurgien-dentiste seul
Le modèle `User owner + CabinetConfig` convient conceptuellement, mais la création non authentifiée, IF perdu et save Settings incompatible empêchent une certification.

### B. Cabinet avec assistant(e)
La hiérarchie `employer_id` est adaptée. En revanche l’API Réglages doit imposer les permissions côté backend, pas seulement masquer l’UI.

### C. Clinique multi-praticiens
Le `CabinetConfig.nom_praticien` global devient ambigu : l’identité de la structure et celle du praticien qui signe/génère un document doivent être séparées.

### D. Centre dentaire / gestion centralisée
Le code actuel ne démontre pas de vrai modèle multi-site/multi-cabinet. Ne pas prétendre le supporter via `switchCabinet` tant qu’un modèle persistant n’existe pas.

---

## 10. Consumers identifiés

| Consommateur | Lecture actuelle | Risque |
|---|---|---|
| Settings Profil/Branding | `/clinics/me` | payload write incompatible avec strict schema |
| Documents standard | CabinetConfig + user/employer selon générateur | divergences selon générateur |
| Footer légal | CabinetConfig puis `User.identifiants_legaux` fallback | double vérité |
| QR documents | CabinetConfig | dépend de la vérité contacts/adresse/QR |
| Céphalométrie | CabinetConfig via employer dans DocumentFactory | plutôt cohérent |
| Note honoraires / devis | AccountingGenerator lookup direct `user_id` | incohérent sous-compte |
| Échéancier | référence `models.Clinic` | modèle introuvable au snapshot |
| Équipe | `User.employer_id` | base ownership cohérente |
| Thème UI | CabinetConfig + localStorage | double vérité avant save onboarding |

Cette liste constitue les consommateurs directement prouvés dans P0. P6 devra étendre la recherche à tout consommateur indirect avant certification finale.

---

## 11. Tests obligatoires du chantier

- T1 Fresh install
- T2 Reload
- T3 Restart
- T4 Edit from Settings
- T5 Backend GET/SAVE failure fail-closed
- T6 Validation + Unicode/arabe/français si pertinent
- T7 Permissions
- T8 Multi-user
- T9 Consumer truth
- T10 Legacy

### Tests ciblés ajoutés à la roadmap après P0

- T11 anonymous `POST /clinics/` → 401/403 attendu
- T12 owner binding : création liée exactement au user authentifié
- T13 IF round-trip onboarding → DB → Settings → document
- T14 custom specialty round-trip ou suppression explicite de la feature
- T15 payload Settings réel → 200 sans extras interdits
- T16 sous-compte sans `settings` → update/upload cabinet refusé
- T17 sous-compte autorisé → comportement explicitement défini
- T18 échec upload post-create → état récupérable, sans faux onboarding terminé
- T19 backend init-status indisponible → erreur explicite, jamais redirection setup mensongère
- T20 offline mutation → état « en attente » ou échec, jamais « persisté backend » sans ACK
- T21 dentiste rattaché → documents utilisent la config employeur
- T22 échéancier → aucun modèle fantôme `Clinic`

---

## 12. Roadmap

### P0 — Audit & Truth Map — ACTIVE / CODE MAP WRITTEN
Aucune modification produit.

Reste pour certification P0 :
1. captures BEFORE onboarding + Réglages sur viewports retenus ;
2. preuve runtime ciblée des contrats critiques si un environnement exécutable est disponible ;
3. état GitHub/CI du commit documentaire ;
4. closeout P0 seulement après ces preuves.

### P1 — Canonical Data Model
Définir ownership et source de vérité la plus simple.

### P2 — Onboarding Product Reconciliation
Classer chaque champ : `REQUIRED NOW`, `OPTIONAL NOW`, `LATER IN SETTINGS`, `REMOVE`.

### P3 — Settings Reconciliation
Aligner Réglages avec la source canonique.

### P4 — Backend / Persistence / Permissions
Garantir lecture/écriture, validation, persistance, erreurs et permissions réelles.

### P5 — Legacy Migration
Fresh install + installation existante complète/partielle + champs renommés/manquants + upgrade sans ré-onboarding forcé.

### P6 — Consumer Reconciliation
Vérifier que tous les consommateurs lisent la même vérité canonique.

### P7 — UX Certification
BEFORE → Goal visuel → mockup → implémentation → AFTER → comparaison → score.

### P8 — Regression & Closeout
Tests globaux, documentation canonique, cohérence roadmap/état Git.

---

## 13. Preuves code principales

- `frontend/src/App.tsx`
- `frontend/src/features/admin/SetupWizard/SetupWizard.tsx`
- `frontend/src/features/admin/SetupWizard/store/useSetupStore.ts`
- `frontend/src/features/admin/SetupWizard/steps/*`
- `frontend/src/features/admin/Settings/SettingsContainer.tsx`
- `frontend/src/features/admin/Settings/hooks/useSettingsStore.ts`
- `frontend/src/features/admin/Settings/types.ts`
- `frontend/src/utils/settingsAccess.ts`
- `frontend/src/services/api.ts`
- `frontend/src/services/templateApi.ts`
- `frontend/src/types/template.ts`
- `backend/routers/clinics.py`
- `backend/routers/team.py`
- `backend/schemas/cabinet.py`
- `backend/models.py`
- `backend/services/document_factory.py`
- `backend/services/generators/accounting_gen.py`
- `backend/services/base_template.py`
- `backend/services/base_template_core.py`
- `backend/tests/test_clinics_router.py`
- `backend/tests/test_clinics_config.py`
- `backend/tests/test_clinic_init_status_tenant.py`
- `backend/tests/test_cabinet_settings_strict_whitelist.py`
- `frontend/src/features/admin/Settings/hooks/useSettingsStore.test.ts`

---

## Règles d’exécution

- Ne jamais supposer qu’un champ UI est persisté : vérifier jusqu’à la source finale.
- Ne jamais considérer une réponse API correcte sans vérifier son consommateur.
- Pas de redesign avant le modèle métier.
- Préférer une seule source de vérité.
- Une CI en cours n’arrête pas le chantier : poursuivre tout travail indépendant.
- Pour toute UI touchée : captures BEFORE + Goal + mockup + AFTER + score.
- Aucun Vercel sans autorisation explicite.
- Ne jamais créditer un lot sans preuve observable.
- Pour un benchmark lourd : préparation complète → 1 commit final → 1 run.

## Reprise / Handover

Chantier : `Onboarding ↔ Réglages`
Lot courant : `P0 — Audit & Truth Map`
Produit modifié : **non**
État : **Truth Map code écrite, P0 non certifié**
Next exact : obtenir les captures BEFORE et la preuve runtime ciblée des contrats P0 critiques ; ensuite certifier P0 et passer à P1.

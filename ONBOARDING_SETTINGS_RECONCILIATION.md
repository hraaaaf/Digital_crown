# Digital Crown — Onboarding ↔ Réglages / Clinic Identity Reconciliation

Status: **ACTIVE — P0 CLOSED / P1 CLOSED / P2 ACTIVE**

Branch: `agent/onboarding-settings-reconciliation`
PR: `#214` (draft)
Product audit base: `master@2bfe24fc62a79af0a13852cd091bd65c3e0fd384`

## Goal global

Une seule vérité cohérente :

`Inscription / activation essai → onboarding → backend/DB → Réglages → consommateurs → reprise de session`

Aucun déploiement Vercel sans autorisation explicite.

## Avancement canonique

Le chantier comprend 9 lots P0→P8. Crédit uniquement lorsqu’un lot est entièrement certifié.

- P0 CLOSED ✅
- P1 CLOSED ✅
- Lots certifiés : **2/9**
- Avancement global certifié : **22,2 %**

---

# P0 — Audit & Truth Map — CLOSED ✅

## Preuve

### Contrat

- Run : `32560853707 — Onboarding Settings P0 Certification #3`
- Conclusion : **SUCCESS**
- HEAD certifié : `eecb28cedd65bac8196ce8002c42893ad3ada28c`

### BEFORE visuel

- Run : `32560178433`
- Artifact : `9472575193 — onboarding-settings-p0-before`
- Digest : `sha256:4b80b57fd7d0dd5f33d98c04fbbb78cb5623b51056fef6df1227054e0cbefa95`
- 70 screenshots : 7 étapes onboarding + 7 onglets Réglages × 5 viewports
- Viewports : 1440 / 1024 / 768 / 430 / 390
- 0 erreur runtime/pageerror/console enregistrée
- 14 overflows : uniquement SetupWizard à 430/390
- `scrollWidth=569` sur les 14 écrans concernés
- Réglages sans overflow sur les 5 viewports

Aucun code produit modifié dans P0.

## Findings P0 bloquants

### CRITICAL

1. `POST /api/clinics/` sans `current_user`, ownership choisi globalement.
2. Mutations cabinet protégées par auth mais pas par permission Settings backend.
3. `saveProfile()` envoie des champs interdits par `CabinetConfigUpdate(extra="forbid")`.

### HIGH

4. IF perdu à la création (`if_` frontend vs alias entrant `if`).
5. Spécialité personnalisée UI sans persistance.
6. Onboarding non atomique avant uploads logo/letterhead.
7. Erreur init transformée en faux « setup requis ».
8. Thème onboarding persisté localement avant ACK backend.
9. Faux succès offline desktop : HTTP 200 synthétique, aucune mise en queue réelle par `api.ts`.
10. AccountingGenerator cherche la config sur `owner_id == user_id` au lieu de l’employeur.
11. Échéancier référence `models.Clinic` inexistant.
17. Signup classique et activation essai produisent deux états initiaux divergents.
20. SetupWizard déborde à 430/390 ; cause primaire : stepper 7×`w-12`, `gap-4`, labels `whitespace-nowrap`, padding `px-8`.

### MEDIUM

12. Switch multi-cabinet frontend sans backend persistant correspondant.
13. Identifiants légaux en double source CabinetConfig/User.
14. `contacts_json` + `footer_phones` comme deux représentations persistées.
15. Confirmation onboarding incomplète / QR mal nommé.
16. Defaults frontend/backend divergents, notamment `swiss` vs `classic`.
18. Password UI min 4 vs backend min 8.
19. Signup annonce un cabinet pré-enregistré alors qu’il ne crée qu’un User.

---

# P1 — Canonical Data Model — CLOSED ✅

## Goal P1

Définir le modèle minimal qui donne un propriétaire unique à chaque donnée, couvre solo/équipe/clinique et sépare explicitement organisation, praticien, acteur et signataire sans créer de tables spéculatives.

## Décision architecturale

### 1. `User` = compte + praticien

Aucune table `Practitioner` nouvelle.

Preuves repo :
- `Acte.praticien_id → users.id` ;
- les dentistes secondaires sont déjà des `User(role=DENTISTE)` ;
- `team.py` les rattache au compte principal via `employer_id` ;
- les plans PREMIUM/ELITE supportent plusieurs dentistes.

Owner canonique User :
- identité de connexion ;
- rôle/permissions ;
- nom professionnel FR ;
- futur nom professionnel AR ;
- coordonnées personnelles/professionnelles propres ;
- INPE **professionnel** ;
- identité du signataire sur les documents cliniques.

### 2. `CabinetConfig` = profil d’organisation

On conserve la table/modèle existant au lieu d’un renommage massif. Sémantiquement, elle devient l’`OrganizationProfile` du cabinet.

Owner canonique CabinetConfig :
- nom de structure ;
- type de structure ;
- adresse ;
- contacts structure ;
- ICE / IF de l’entité d’exercice/facturation ;
- INPE **établissement** s’il existe ;
- spécialités/services proposés par la structure ;
- logo / letterhead ;
- branding document ;
- QR organisation/document ;
- thème et préférences partagées.

### 3. `employer_id` = membership mono-organisation

Conserver le mécanisme actuel tant qu’aucun vrai besoin multi-organisation/multi-site n’est démontré.

Ne pas créer de table Membership maintenant.

### 4. `owner_id` n’est pas le signataire

`CabinetConfig.owner_id` reste la clé de tenancy du compte principal. Le propriétaire administratif n’est pas automatiquement le praticien qui signe un document.

### 5. Actor et Signer sont deux concepts différents

- **actor_user** : utilisateur qui déclenche l’action, utile pour audit/permissions ;
- **signer_user** : dentiste responsable/signataire lorsque le document l’exige ;
- **organization** : établissement émetteur/branding partagé.

Une secrétaire peut être actor autorisé d’un devis sans jamais devenir signer clinique.

## Pourquoi aucune table Practitioner

Créer Practitioner aujourd’hui introduirait `User ↔ Practitioner` pour représenter une personne que le produit représente déjà par User. Cela ajouterait migration, synchronisation et conflits sans valeur démontrée.

Une table Practitioner ne redevient justifiée que si un praticien doit exister indépendamment de tout compte utilisateur ou appartenir à plusieurs organisations. Ce besoin n’est pas prouvé dans le produit actuel.

## Type de structure

Décision : conserver physiquement `PRIVE | CLINIQUE` pour compatibilité P1/P5.

Règles :
- `PRIVE` signifie **cabinet dentaire**, pas « mono-praticien » ;
- `CLINIQUE` couvre **clinique / centre dentaire** tant qu’aucun comportement distinct ne justifie une troisième valeur ;
- le nombre de praticiens est dérivé de l’équipe réelle, jamais du `cabinet_type` ;
- ne pas ajouter SOLO/CABINET/CENTRE uniquement pour afficher plus de boutons.

Conséquence P2 : supprimer la promesse UI « Mono-praticien » attachée à `PRIVE`.

## Identifiants légaux

### ICE / IF

Owner canonique : **profil d’organisation / entité d’exercice et de facturation** dans CabinetConfig.

L’OMPIC décrit l’ICE comme identifiant uniforme de l’entreprise, pour personnes morales ou entreprises personnes physiques, aux côtés notamment de l’IF. Le fait qu’un cabinet soit exploité par une personne physique ne justifie donc pas de dupliquer ICE/IF dans User : CabinetConfig représente ici l’entité d’exercice/facturation.

Source primaire : OMPIC — `https://www.ompic.ma/fr/content/identifiant-commun-de-lentreprise`

### INPE

L’INPE ne peut pas rester un champ unique ambigu.

Les sources officielles ANAM et Ministère de la Santé distinguent explicitement :
- INPE professionnel de santé ;
- INPE établissement de santé.

Sources primaires :
- ANAM Guide INPE 2020 — `https://anam.ma/anam/wp-content/uploads/2021/11/Guide-INPE-2020.pdf`
- ANAM Référentiel administratif INPE 2023 — `https://anam.ma/anam/wp-content/uploads/2023/02/Referentiel-administratif-INPE-2023.pdf`
- Ministère de la Santé — activité « Code INPE ».

Target P4 :
- `User.inpe_professionnel` nullable ;
- `CabinetConfig.inpe_etablissement` nullable ;
- `CabinetConfig.inpe` devient legacy transitoire jusqu’à P5.

Aucun legacy INPE ne sera silencieusement classé professionnel/établissement sans preuve.

## Matrice source-of-truth P1

| Concept | Owner canonique | Champ cible / règle | Legacy actuel |
|---|---|---|---|
| Email/login | User | `email` | User |
| Nom praticien FR | User | `nom_complet` | CabinetConfig.nom_praticien dupliqué |
| Nom praticien AR | User | futur `nom_complet_ar` | CabinetConfig.nom_praticien_ar |
| Rôle/permissions | User | existant | User |
| Tél. praticien | User | telephone_* | User |
| INPE praticien | User | futur `inpe_professionnel` | CabinetConfig.inpe ambigu / User.identifiants_legaux |
| Nom structure | CabinetConfig | `nom_cabinet` | existant |
| Type structure | CabinetConfig | `cabinet_type` | existant |
| Adresse structure | CabinetConfig | `footer_address` puis alias métier `adresse` | User.adresse_complete fallback |
| Contacts structure | CabinetConfig | `contacts_json` | footer_phones dérivé |
| ICE structure/facturation | CabinetConfig | `ice` | User.identifiants_legaux fallback |
| IF structure/facturation | CabinetConfig | `if_` | User.identifiants_legaux fallback |
| INPE établissement | CabinetConfig | futur `inpe_etablissement` | `inpe` ambigu |
| Services/spécialités structure | CabinetConfig | `specialty_ids` | existant |
| Custom specialty si conservée | CabinetConfig | cible à définir P2/P4 | UI sans DB |
| Branding | CabinetConfig | existant | existant |
| Header auto | dérivé | organisation + signer selon document | header global avec praticien owner |
| Header custom | CabinetConfig | override de présentation | header_lines_fr/ar |
| Footer contacts | dérivé | contacts_json | footer_phones persisté |
| Thème | CabinetConfig | backend canonique, localStorage cache seulement | double vérité |
| Tenant/team | User | `employer_id` | existant |
| Multi-cabinet | aucun | non supporté | activeCabinetId/clinic_id incomplets |

## Politique documentaire canonique

### Documents cliniques personnels

Ordonnance, certificat et tout document légalement/personnellement signé par un praticien :
- organization_config = CabinetConfig de `signer_user.get_employer_id()` ;
- signer = User DENTISTE explicite ;
- actor = utilisateur courant ;
- aucun fallback silencieux vers le propriétaire si le signer requis est absent.

Le certificat médical implémente déjà l’essentiel de ce pattern : config employeur + nom du User signataire.

### Rapports cliniques

Céphalométrie et rapports assimilés :
- branding organisation ;
- praticien responsable explicite quand affiché ;
- ne jamais utiliser `CabinetConfig.nom_praticien` comme identité universelle de clinique.

### Documents financiers

Devis, note d’honoraires, échéancier :
- issuer = organisation ;
- actor = utilisateur ayant déclenché l’action ;
- signer praticien non implicite par défaut ;
- config toujours chargée via employeur/tenant, pas raw user_id.

### Document libre

- branding = organisation ;
- signer uniquement si le document exige explicitement une signature ;
- actor conservé pour audit.

## Politique header/footer

### Header

Le header partagé ne doit plus encoder le propriétaire comme praticien global.

- header automatique = identité organisationnelle ;
- identité du praticien/signataire = bloc/document contextuel ;
- un header custom existant reste conservé byte-for-byte jusqu’à action explicite de l’utilisateur.

### Footer

- adresse/contact/ICE/IF = organisation ;
- INPE établissement seulement si renseigné/classifié ;
- INPE praticien dans le bloc signataire/clinique approprié, pas comme identifiant global indistinct ;
- `footer_phones` devient une projection dérivée de `contacts_json` et non une seconde source éditable.

## Politique QR

Le type détermine le scope :
- VALIDATION / PAYMENT → document ;
- WEBSITE / INSTAGRAM / WHATSAPP / LOCATION → organisation ;
- VCARD → praticien signataire lorsqu’il existe ; sans signer explicite, pas de fallback silencieux vers un propriétaire arbitraire.

## Legacy / migration contract pour P5

### Noms praticien

- si `User.nom_complet` vide et `CabinetConfig.nom_praticien` présent → backfill User ;
- si les deux identiques → reconciled ;
- si les deux diffèrent → ne pas écraser, état à réconcilier.

`nom_praticien_ar` suit la même règle vers le futur `User.nom_complet_ar`.

### ICE / IF

- CabinetConfig est cible canonique ;
- si cible vide et legacy owner `User.identifiants_legaux` possède une valeur → backfill conflict-aware ;
- si deux valeurs différentes → aucune substitution silencieuse.

### INPE

- créer deux cibles nullables ;
- ne jamais deviner la nature d’un `CabinetConfig.inpe` legacy ;
- conserver la valeur legacy jusqu’à classification explicite Professionnel / Établissement ;
- afficher une configuration à compléter plutôt qu’un faux choix automatique.

### Contacts

- `contacts_json` gagne ;
- `footer_phones` devient dérivé ;
- si contacts_json vide mais footer legacy présent, conserver en compatibilité jusqu’à normalisation explicite.

### Headers custom

Ne pas reconstruire automatiquement les headers custom existants. Les préserver jusqu’à reset/édition explicite.

## Scénarios métier P1

| Scénario | Organisation | Praticiens | Membership | Verdict |
|---|---|---|---|---|
| Dentiste seul | 1 CabinetConfig | owner User | owner sans employer | couvert |
| Cabinet + assistant | 1 CabinetConfig | owner User | secrétaire employer_id=owner | couvert |
| Cabinet/clinique multi-dentistes | 1 CabinetConfig | owner + User DENTISTE secondaires | employer_id=owner | couvert |
| Centre à gestion centralisée | 1 CabinetConfig | plusieurs User | employer_id=owner | couvert tant qu’un seul site/tenant |
| Multi-site / multi-organisation | non modélisé | potentiellement multi-membership | employer_id insuffisant | hors scope tant que besoin non prouvé |

## P1 preuves code

- `backend/models.py` : User, employer_id, Acte.praticien_id, CabinetConfig.owner_id unique.
- `backend/routers/team.py` : dentistes secondaires réels + quotas multi-praticiens.
- `backend/services/generators/certificat_gen.py` : config employeur + signer User.
- `backend/services/generators/libre_gen.py` : config employeur.
- `backend/services/document_factory.py` : helper `_get_cabinet_config()` via employer pour certains rapports.
- `backend/services/generators/ordonnance_gen.py` : contre-exemple raw user_id à corriger P6.
- `backend/services/generators/accounting_gen.py` : contre-exemple raw user_id à corriger P6.
- `backend/services/base_template_core.py` : header/footer global mélange actuellement organisation et praticien.
- `frontend/src/features/admin/SetupWizard/steps/Step1Identity.tsx` : PRIVE présenté à tort comme mono-praticien.

## P1 non-objectifs

- pas de table Practitioner ;
- pas de table Membership ;
- pas de modèle multi-site ;
- pas de nouveau type SOLO/CENTRE sans comportement métier ;
- pas de migration DB dans P1 ;
- pas de modification UI dans P1.

## Verdict P1

**CLOSED.** Le modèle cible est suffisamment déterminé pour exécuter P2/P3/P4/P5 sans décision architecturale restante sur l’ownership principal.

---

# P2 — Onboarding Product Reconciliation — ACTIVE

## Goal P2

Réduire le premier onboarding aux données réellement nécessaires au démarrage, sans demander deux fois ce qui existe déjà et sans faire promettre à l’UI une persistance qu’elle n’a pas.

Chaque champ doit devenir exactement l’un de :
- `REQUIRED NOW`
- `OPTIONAL NOW`
- `LATER IN SETTINGS`
- `REMOVE`

## Gates UI P2

Avant modification produit :
1. BEFORE déjà acquis via P0 ;
2. Goal visuel écrit ;
3. mockup/wireframe obligatoire ;
4. seulement ensuite implémentation ;
5. AFTER mêmes viewports ;
6. comparaison + score.

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
- **P1 — Canonical Data Model — CLOSED ✅**
- **P2 — Onboarding Product Reconciliation — ACTIVE**
- **P3 — Settings Reconciliation**
- **P4 — Backend / Persistence / Permissions**
- **P5 — Legacy Migration**
- **P6 — Consumer Reconciliation**
- **P7 — UX Certification**
- **P8 — Regression & Closeout**

## Reprise

Chantier : `Onboarding ↔ Réglages`
Lot courant : `P2 — Onboarding Product Reconciliation`
P0 preuve : run `32560853707` SUCCESS
P1 modèle : `User = compte/praticien`, `CabinetConfig = organisation`, `employer_id = membership mono-org`
Produit modifié P0/P1 : **non**
BEFORE : 70 captures acquises
Finding UX principal : SetupWizard 569 px sur 430/390
Avancement global certifié : **22,2 % (2/9 lots)**
Next exact : classer tous les champs onboarding, écrire Goal visuel P2, produire mockup avant toute modification produit.

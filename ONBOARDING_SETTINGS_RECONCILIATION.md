# Digital Crown — Onboarding ↔ Réglages / Clinic Identity Reconciliation

Status: **ACTIVE — P0 CLOSED / P1 CLOSED / P3 CONTRACT CLOSED / P2 SPEC ACTIVE**

Branch: `agent/onboarding-settings-reconciliation`
PR: `#214` (draft)
Product audit base: `master@2bfe24fc62a79af0a13852cd091bd65c3e0fd384`

## Goal global

Une seule vérité cohérente :

`Inscription / activation essai → onboarding → backend/DB → Réglages → consommateurs → reprise de session`

### Règle directionnelle obligatoire

**Réglages est la surface produit canonique de configuration.**

L’onboarding n’est pas une seconde configuration indépendante. Il est une projection guidée de Réglages.

Donc :
- même concept métier ;
- même owner ;
- même type/enum ;
- même validation ;
- même default ;
- même backend/persistance ;
- même permission ;
- aucune persistance locale concurrente.

Lorsqu’un Réglage contredit le modèle métier P1, le contrat cible de Réglages est corrigé d’abord ; onboarding s’aligne ensuite sur ce contrat cible.

Aucun déploiement Vercel sans autorisation explicite.

## Avancement canonique

9 lots P0→P8. Crédit uniquement sur lot entièrement certifié.

- P0 CLOSED ✅
- P1 CLOSED ✅
- P3 contrat/spécification CLOSED, implémentation produit reportée à P4/P2 selon dépendance
- Lots entièrement certifiés : **2/9**
- Avancement global certifié : **22,2 %**

---

# P0 — Audit & Truth Map — CLOSED ✅

## Preuves

### Contrat
- Run : `32560853707 — Onboarding Settings P0 Certification #3`
- Conclusion : **SUCCESS**
- HEAD certifié : `eecb28cedd65bac8196ce8002c42893ad3ada28c`

### BEFORE visuel
- Run : `32560178433`
- Artifact : `9472575193 — onboarding-settings-p0-before`
- Digest : `sha256:4b80b57fd7d0dd5f33d98c04fbbb78cb5623b51056fef6df1227054e0cbefa95`
- 70 screenshots : 7 étapes onboarding + 7 onglets Réglages × 5 viewports
- 1440 / 1024 / 768 / 430 / 390
- 0 erreur runtime/pageerror/console
- 14 overflows : SetupWizard uniquement à 430/390
- `scrollWidth=569`
- Réglages : aucun overflow sur les 5 viewports

Aucun code produit modifié en P0.

## Findings P0 bloquants

### CRITICAL
1. `POST /api/clinics/` sans `current_user`, ownership global/non déterministe.
2. Mutations cabinet authentifiées mais sans permission Settings backend.
3. Payload `saveProfile()` incompatible avec `CabinetConfigUpdate(extra="forbid")`.

### HIGH
4. IF perdu à la création (`if_` vs alias `if`).
5. Spécialité personnalisée UI sans persistance.
6. Onboarding non atomique avant uploads.
7. Erreur init transformée en faux setup requis.
8. Thème onboarding persisté localement avant ACK backend.
9. Faux succès offline desktop sans queue réelle.
10. AccountingGenerator lit config sur raw `user_id`.
11. Échéancier référence `models.Clinic` inexistant.
17. Signup classique et essai produisent deux états initiaux divergents.
20. SetupWizard overflow mobile 430/390.

### MEDIUM
12. Switch multi-cabinet frontend sans backend réel.
13. Identifiants légaux double source.
14. `contacts_json` + `footer_phones` double représentation.
15. Confirmation onboarding incomplète / QR mal nommé.
16. Defaults frontend/backend divergents (`swiss` vs `classic`).
18. Password UI min 4 vs backend min 8.
19. Signup annonce un cabinet pré-enregistré alors qu’il ne crée qu’un User.

---

# P1 — Canonical Data Model — CLOSED ✅

## Décision

### User = compte + praticien
Pas de nouvelle table Practitioner.

Owner User : auth, rôle/permissions, identité professionnelle du praticien, coordonnées propres, futur INPE professionnel, identité du signataire.

### CabinetConfig = organisation
Owner CabinetConfig : nom structure, type, adresse, contacts structure, ICE/IF, futur INPE établissement, spécialités/services structure, logo/letterhead, branding, QR, thème et préférences partagées.

### employer_id = membership mono-organisation
Conserver tant qu’aucun vrai besoin multi-site/multi-organisation n’est démontré.

### owner ≠ actor ≠ signer
- owner : propriétaire tenant/config ;
- actor : utilisateur qui déclenche l’action ;
- signer : dentiste responsable/signataire quand requis.

### Type de structure
Conserver `PRIVE | CLINIQUE` pour compatibilité.
- `PRIVE` = cabinet dentaire, pas forcément mono-praticien ;
- `CLINIQUE` = clinique/centre tant qu’aucun comportement distinct n’impose une nouvelle valeur ;
- nombre de praticiens = équipe réelle, pas `cabinet_type`.

### Identifiants
- ICE / IF → organisation/entité d’exercice et facturation ;
- INPE → deux sujets distincts : professionnel et établissement ;
- aucune classification automatique d’un INPE legacy ambigu.

### Documents
Documents cliniques personnels : branding organisation + signer User DENTISTE explicite.
Documents financiers : issuer organisation, actor audité, signer non implicite.
Header automatique : identité organisationnelle ; identité praticien contextuelle.
Footer : données organisationnelles.
QR : scope selon type ; VCARD praticien seulement si signer explicite.

### Legacy
- nom praticien CabinetConfig → User seulement si cible vide ; conflit = pas d’écrasement ;
- ICE/IF CabinetConfig gagne, backfill conflict-aware depuis User legacy ;
- INPE legacy conservé jusqu’à classification explicite ;
- `contacts_json` gagne sur `footer_phones` ;
- headers custom préservés byte-for-byte tant qu’utilisateur ne les réinitialise pas.

## Verdict P1

**CLOSED.**

---

# P3 — Réglages Canonical Contract — CONTRACT CLOSED ✅

> P3 a été spécifié avant P2 car onboarding doit s’aligner sur Réglages et non l’inverse. Les changements DB/API nécessaires sont exécutés dans P4 ; l’UI onboarding est exécutée dans P2.

## Goal P3

Faire de Réglages la référence fonctionnelle et contractuelle de la configuration cabinet/praticien.

## Preuves P3

Inspection directe du HEAD de branche :
- `frontend/src/features/admin/Settings/types.ts`
- `frontend/src/features/admin/Settings/hooks/useSettingsStore.ts`
- `frontend/src/features/admin/Settings/tabs/ProfileTab.tsx`
- `frontend/src/features/admin/Settings/tabs/BrandingTab.tsx`
- `frontend/src/features/admin/Settings/tabs/branding/StudioControls.tsx`
- `frontend/src/features/admin/Settings/tabs/branding/StudioControlsCore.tsx`
- `frontend/src/features/admin/Settings/tabs/branding/presets.ts`
- `frontend/src/features/admin/Settings/runtimePreferences.ts`
- `frontend/src/utils/settingsAccess.ts`
- `backend/schemas/cabinet.py`
- `backend/models.py`
- `backend/routers/clinics.py`

CI du HEAD précédent `939eb93c24fd25c0a409803e15d9f7c94b2f00e1` : CI, T2, Catalog, Patient P7 et P0 Certification SUCCESS.

## Doctrine de sauvegarde canonique

Réglages a déjà une doctrine utile à conserver :
- `Profil`, `Design & Ambiance`, `Performance & Assistance` = configuration partagée, staged puis sauvegardée explicitement ;
- `Catalogue`, `Agenda`, `Sécurité`, `Équipe` = domaines atomiques indépendants ;
- un aperçu visuel peut être immédiat, mais la vérité persistée n’est acquise qu’après ACK backend ;
- localStorage/safeStorage n’est qu’un cache/runtime projection après ACK, jamais la source de vérité.

L’onboarding doit réutiliser cette doctrine : ses choix peuvent être prévisualisés localement, mais aucune préférence ne doit devenir durable avant la sauvegarde backend réussie.

## Matrice canonique Profil Cabinet

| Réglage canonique | Owner | Cible canonique | Contrat cible | Permission | Onboarding | Verdict |
|---|---|---|---|---|---|---|
| Type de structure | CabinetConfig | `cabinet_type` | enum `PRIVE|CLINIQUE`, default `PRIVE` | `settings` | MIRROR REQUIRED | KEEP ; libellé PRIVE = Cabinet dentaire, jamais mono-praticien |
| Nom de structure | CabinetConfig | `nom_cabinet` | string ≤255, requis pour setup | `settings` | MIRROR REQUIRED | KEEP |
| Nom praticien FR | User | `nom_complet` | string ≤255, prérempli depuis compte | profil praticien / owner | MIRROR REQUIRED prérempli | MOVE hors CabinetConfig comme vérité |
| Nom praticien AR | User | futur `nom_complet_ar` | nullable ≤255 | profil praticien / owner | MIRROR OPTIONAL | MOVE ; `CabinetConfig.nom_praticien_ar` legacy |
| Adresse structure | CabinetConfig | `footer_address` exposé métier comme `adresse` | string ≤500 | `settings` | MIRROR REQUIRED | KEEP |
| Contacts structure | CabinetConfig | `contacts_json` | fixe/mobile/whatsapp/instagram `{enabled,value}` | `settings` | MIRROR OPTIONAL | KEEP ; `footer_phones` devient projection dérivée |
| ICE | CabinetConfig | `ice` | nullable string ≤50 | `settings` | MIRROR OPTIONAL | KEEP |
| IF | CabinetConfig | `if_`, alias API `if` | nullable string ≤50, `populate_by_name=True` partout | `settings` | MIRROR OPTIONAL | KEEP + FIX create |
| INPE professionnel | User | futur `inpe_professionnel` | nullable string ≤50 | profil praticien / owner | MIRROR OPTIONAL | ADD ciblé P4 |
| INPE établissement | CabinetConfig | futur `inpe_etablissement` | nullable string ≤50 | `settings` | MIRROR OPTIONAL | ADD ciblé P4 ; legacy `inpe` jamais deviné |
| Spécialités structure | CabinetConfig | `specialty_ids` | liste d’IDs de `SPECIALTIES_DICT` | `settings` | MIRROR OPTIONAL | KEEP |
| Spécialité libre FR/AR | CabinetConfig | futurs `custom_specialty_fr/ar` | nullable string ≤255 | `settings` | MIRROR OPTIONAL | KEEP + ADD persistance P4 ; feature utile déjà exposée dans Réglages |
| Logo | CabinetConfig | `logo_path` via endpoint upload | PNG/JPEG/SVG, endpoint dédié | `settings` | MIRROR OPTIONAL | KEEP |
| En-tête auto | dérivé | organisation + signer/context | pas de deuxième identité praticien persistée | `settings` | dérivé | FIX P6 |
| En-tête custom | CabinetConfig | `header_lines_fr/ar` + `header_customized` cible | max 6 lignes/langue | `settings` | SETTINGS ONLY | KEEP ; avancé |

## Matrice canonique Design & Ambiance

| Réglage canonique | Owner | Cible canonique | Contrat cible | Onboarding | Verdict |
|---|---|---|---|---|---|
| Palette document/app | CabinetConfig | `primary_color`, `secondary_color`, `accent_color` | hex `#RRGGBB` | MIRROR OPTIONAL | KEEP |
| Police document | CabinetConfig | `font_fr` | IDs de `PREMIUM_FONTS`, default cible `inter` | MIRROR OPTIONAL | KEEP + aligner backend default |
| Modèle document | CabinetConfig | `selected_template` | `swiss|royal|clinical|modern|heritage`, default cible `swiss` | MIRROR OPTIONAL | KEEP + aligner backend `classic` |
| Ambiance applicative | CabinetConfig | `selected_theme` | IDs de `APP_THEMES`, default `elite` | MIRROR OPTIONAL | KEEP ; onboarding doit exposer la même liste que Réglages |
| Preset ambiance | dérivé | patch palette+font+template+theme+density | aucune colonne `preset_id` nécessaire | MIRROR OPTIONAL recommandé | KEEP ; meilleur chemin onboarding pour alignement sans surcharge |
| Densité | dérivé | marges/scales via `DENSITY_DEFAULTS` | `compact|confort|etendu` comme commande UI, pas seconde vérité DB | MIRROR OPTIONAL | KEEP |
| Marge haute/basse | CabinetConfig | `margin_top/bottom` | 1–8 / 1–6 côté UI, contrat backend à harmoniser | SETTINGS ONLY par défaut | KEEP avancé |
| Taille/position logo | CabinetConfig | scale + offsets | scale 0.5–2, offsets -3..3 cm | SETTINGS ONLY | KEEP avancé |
| Scales/interlignes header/footer | CabinetConfig | champs `*_scale`, `*_line_height` | 0.5–2 | SETTINGS ONLY | KEEP avancé |
| Letterhead | CabinetConfig | `letterhead_path`, `use_letterhead`, hide flags | endpoint upload dédié + ACK | MIRROR OPTIONAL | KEEP |
| QR activé/type | CabinetConfig | `qr_code_enabled/type` | enum commun | MIRROR OPTIONAL | KEEP |
| QR valeur/label | CabinetConfig | `qr_code_value/label` | ≤500 / ≤100 | MIRROR OPTIONAL | KEEP |
| QR style/position/taille | CabinetConfig | style + offsets + footer_qr_scale | contraintes backend existantes | SETTINGS ONLY | KEEP avancé |
| Arrière-plan animé | runtime local | `app_background_animated` | préférence device/runtime, non CabinetConfig | SETTINGS ONLY | KEEP hors onboarding |

### Décision thème/presets

Réglages possède davantage de thèmes applicatifs que le wizard historique. L’onboarding ne doit donc plus maintenir sa propre liste `THEMES` limitée à quatre valeurs.

Cible :
- réutiliser `APP_THEMES` et/ou les presets de Réglages ;
- privilégier les **presets Réglages** dans le flow initial, car ils appliquent un ensemble cohérent palette + police + modèle + thème + densité ;
- laisser les contrôles fins disponibles dans Réglages et éventuellement dans une section onboarding « Personnaliser » sans créer de valeurs parallèles.

### Décision QR

La surface canonique est le `QrTruthControls` actuel de Réglages :
- `VALIDATION` = **Vérification du document** ;
- `PAYMENT` = **Suivi du paiement**, sans encaissement ;
- `LOCATION` utilise l’adresse cabinet enregistrée ;
- Website/Instagram/WhatsApp utilisent une valeur explicite.

Le wizard historique `Signature Digitale`, `Signature`, `Paiement` est obsolète et doit reprendre ces libellés/semantiques exacts.

## Performance & Assistance

`performance_mode`, `clinical_tips_enabled`, `show_patient_badges` restent des Réglages canoniques mais sont **SETTINGS ONLY** pour le premier onboarding. Ils n’appartiennent pas à l’identité initiale du cabinet.

Leur doctrine est staged → backend ACK → runtime cache/event.

## Agenda / Catalogue / Sécurité / Équipe

Ces surfaces restent canoniques dans leurs domaines mais ne doivent pas être copiées dans le premier onboarding :
- Agenda : SETTINGS ONLY, configuration métier indépendante ;
- Catalogue : SETTINGS ONLY ;
- Sécurité/backup/mobile : SETTINGS ONLY ;
- Équipe : SETTINGS ONLY, après création du tenant.

Cela ne les supprime évidemment pas de Réglages. Le monde survivra à cette retenue.

## Permissions canoniques

Frontend existant :
- owner ADMIN / DENTISTE principal / superadmin : accès Settings ;
- sous-comptes : `permissions.settings === true` requis, legacy default false.

Cible backend P4 : toute mutation `/clinics/me*` doit appliquer la même permission `settings` ou être réservée au owner selon la donnée praticien. L’auth seule n’est pas suffisante.

L’onboarding initial est réservé au compte principal qui initialise son tenant. Un sous-compte ne lance jamais le wizard organisationnel.

## Invariants P3

1. `contacts_json` est éditable ; `footer_phones` est dérivé.
2. `User.nom_complet` est le nom praticien FR ; `CabinetConfig.nom_praticien` devient legacy/compatibilité.
3. `selected_template` default = `swiss` partout.
4. `font_fr` default = `inter` partout côté contrat produit.
5. `selected_theme` default = `elite`.
6. IF accepte le même nom entrant depuis Settings et onboarding.
7. custom specialty reste une feature, mais doit obtenir une vraie colonne/persistance.
8. INPE est séparé professionnel/établissement avant d’être reflété par onboarding.
9. `activeCabinetId/switchCabinet` n’appartient pas au contrat canonique tant qu’aucun backend multi-cabinet réel n’existe.
10. aperçu thème/palette n’est jamais synonyme de persistance.
11. uploads logo/letterhead ne doivent pas laisser l’onboarding « terminé » si la transaction fonctionnelle n’est pas cohérente.
12. le payload Settings est construit explicitement depuis le contrat backend ; jamais `...profile` aveugle.

## Findings supplémentaires P3

- `PresetsModal` annonce actuellement « 6 ambiances » alors que `PRESETS` n’en contient que 2 : copy à corriger lors du lot UI concerné.
- `CabinetProfile` expose `logo_path` et custom specialties alors que `CabinetConfigUpdate(extra="forbid")` ne les accepte pas : confirme le besoin d’un payload whitelisté.
- `header_customized` est utilisé par l’UI mais absent du schéma/DB actuel : à persister ou à remplacer par une règle dérivable ; décision P4, sans faux round-trip.
- les contraintes de marge diffèrent entre contrôles UI et schéma backend générique ; P4 doit choisir le contrat réellement utilisé et le tester.

## Verdict P3

**CONTRACT CLOSED.** La surface Réglages de référence et ses invariants sont déterminés. Aucun changement produit P3 n’a été nécessaire pour établir le contrat ; les corrections de persistance/schema/permissions vont en P4, puis onboarding implémente ce contrat en P2.

---

# P2 — Onboarding Product Reconciliation — SPEC ACTIVE / IMPLEMENTATION AFTER P4 CONTRACT FIXES

## Goal P2

Construire l’onboarding comme version guidée des Réglages canoniques.

### Classification finale issue de P3

| Domaine onboarding | Classification | Contrat Réglages à refléter |
|---|---|---|
| Type structure | MIRROR REQUIRED | `cabinet_type` |
| Nom structure | MIRROR REQUIRED | `nom_cabinet` |
| Nom praticien FR | MIRROR REQUIRED prérempli | `User.nom_complet` |
| Nom praticien AR | MIRROR OPTIONAL | futur `User.nom_complet_ar` |
| Adresse structure | MIRROR REQUIRED | `footer_address` / label métier adresse |
| Contacts | MIRROR OPTIONAL | `contacts_json` |
| ICE / IF | MIRROR OPTIONAL | `ice` / `if_` |
| INPE professionnel/établissement | MIRROR OPTIONAL | champs séparés P4 |
| Spécialités | MIRROR OPTIONAL | `specialty_ids` |
| Spécialité libre | MIRROR OPTIONAL | champs persistés P4 |
| QR | MIRROR OPTIONAL | QrTruthControls Réglages |
| Logo | MIRROR OPTIONAL | endpoint logo Réglages |
| Letterhead | MIRROR OPTIONAL | endpoint letterhead Réglages |
| Preset ambiance | MIRROR OPTIONAL recommandé | presets Réglages |
| Palette / police / template / thème | MIRROR OPTIONAL via preset ou personnalisation | mêmes constantes Réglages |
| Marges/scales/offsets fins | SETTINGS ONLY par défaut | Design avancé |
| Header bilingue ligne par ligne | SETTINGS ONLY | Profil avancé |
| Performance/assistance | SETTINGS ONLY | onglet dédié |
| Agenda | SETTINGS ONLY | domaine atomique |
| Catalogue | SETTINGS ONLY | domaine atomique |
| Sécurité | SETTINGS ONLY | domaine atomique |
| Équipe | SETTINGS ONLY | domaine atomique |
| `footer_phones` | REMOVE comme saisie/source | projection de contacts_json |
| switch multi-cabinet | REMOVE du contrat | non supporté backend |

### Goal visuel P2

Le wizard reste guidé mais reprend les **mêmes mots et choix** que Réglages :
- Profil Cabinet ;
- Spécialités & Contacts ;
- Design & Ambiance ;
- QR / Documents ;
- Confirmation.

Le nombre exact d’étapes sera décidé par le mockup, pas par le legacy 7 étapes.

Critères :
- mobile 390/430 sans overflow ;
- aucune liste/theme/template dupliquée ;
- options avancées cachées par défaut mais accessibles ensuite dans Réglages ;
- chaque écran indique que les choix restent modifiables dans Réglages ;
- aucune valeur durable avant ACK backend ;
- confirmation affiche les valeurs canoniques réellement destinées à être persistées.

## Gate P2 avant code UI

1. P0 BEFORE : acquis ;
2. P3 contrat : acquis ;
3. P4 contrats backend nécessaires aux champs reflétés ;
4. mockup/wireframe P2 ;
5. implémentation ;
6. AFTER mêmes viewports ;
7. comparaison BEFORE → mockup → AFTER + score.

---

# Ordre d’exécution réel

`P0 → P1 → P3(contract) → P4(required contract fixes) → P2 → P5 → P6 → P7 → P8`

---

# Tests obligatoires

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
T14 custom specialty round-trip
T15 payload Settings whitelisté → backend
T16 sous-compte sans settings refusé
T17 sous-compte autorisé explicitement défini
T18 reprise après upload partiel
T19 init-status indisponible → erreur, jamais faux setup
T20 offline → pending/error, jamais faux persisted
T21 sous-compte → config employeur dans documents
T22 échéancier sans `models.Clinic` fantôme
T23 password contract frontend/backend identique
T24 signup classic/trial convergent avant onboarding
T25 SetupWizard 390/430 sans overflow
T26 chaque champ onboarding correspond exactement à un réglage canonique
T27 onboarding → Settings : égalité exacte après sauvegarde/reload
T28 defaults template/font/theme identiques onboarding/settings/backend
T29 QR labels/types/destinations identiques onboarding/settings
T30 aucun localStorage de thème avant ACK final

---

# Roadmap

- **P0 — Audit & Truth Map — CLOSED ✅**
- **P1 — Canonical Data Model — CLOSED ✅**
- **P2 — Onboarding Product Reconciliation — SPEC ACTIVE / implementation après P4 requis**
- **P3 — Settings Reconciliation — CONTRACT CLOSED ✅ / corrections produit P4**
- **P4 — Backend / Persistence / Permissions — NEXT**
- **P5 — Legacy Migration**
- **P6 — Consumer Reconciliation**
- **P7 — UX Certification**
- **P8 — Regression & Closeout**

## Reprise

Chantier : `Onboarding ↔ Réglages`
Lot courant : `P4 — Backend / Persistence / Permissions` avant implémentation P2
P0 : run `32560853707` SUCCESS
P1 : modèle `User = praticien`, `CabinetConfig = organisation`, `employer_id = membership mono-org`
P3 : contrat Réglages verrouillé ; Réglages est la référence, onboarding doit le refléter
Produit modifié P0/P1/P3 contract : non
BEFORE : 70 captures acquises
Finding UX principal : SetupWizard 569 px sur 430/390
Avancement global certifié : **22,2 % (2/9 lots entièrement certifiés)**
Next exact : P4 whitelist payload + auth/permission + owner binding + defaults + custom specialty + INPE split → tests ; puis mockup P2.

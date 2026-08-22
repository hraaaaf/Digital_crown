# Digital Crown — Onboarding ↔ Réglages / Clinic Identity Reconciliation

Status: **ACTIVE — P0 CLOSED / P1 CLOSED / P3 ACTIVE before P2 implementation**

Branch: `agent/onboarding-settings-reconciliation`
PR: `#214` (draft)
Product audit base: `master@2bfe24fc62a79af0a13852cd091bd65c3e0fd384`

## Goal global

Une seule vérité cohérente :

`Inscription / activation essai → onboarding → backend/DB → Réglages → consommateurs → reprise de session`

### Règle directionnelle obligatoire

**Réglages est la surface produit canonique de configuration.**

L’onboarding n’est pas une seconde configuration indépendante et ne redéfinit pas Réglages. Il est une **projection guidée de la configuration canonique disponible dans Réglages**.

Donc :
- si une donnée existe dans onboarding et Réglages, onboarding doit reprendre le **même concept, même nom métier, même type, même enum, même validation, même default, même backend, même persistance et même permission** ;
- une option utile peut rester dans onboarding même si elle n’est pas strictement indispensable au démarrage ;
- on ne déplace pas automatiquement QR, branding, spécialités, thème, logo, etc. vers Réglages ;
- on retire de l’onboarding uniquement ce qui est réellement faux, dupliqué, mort ou sans valeur dans une première configuration ;
- lorsqu’onboarding et Réglages divergent, **onboarding s’aligne sur le contrat Réglages**, sauf si Réglages lui-même viole le modèle métier canonique P1 ; dans ce cas P3 corrige d’abord Réglages, puis onboarding s’y aligne.

Aucun déploiement Vercel sans autorisation explicite.

## Avancement canonique

9 lots P0→P8. Crédit uniquement sur lot entièrement certifié.

- P0 CLOSED ✅
- P1 CLOSED ✅
- Lots certifiés : **2/9**
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

Preuves :
- `Acte.praticien_id → User.id` ;
- dentistes secondaires = `User(role=DENTISTE)` ;
- rattachement via `employer_id` ;
- PREMIUM/ELITE supportent plusieurs dentistes.

Owner User : auth, rôle/permissions, identité professionnelle du praticien, coordonnées propres, futur INPE professionnel, identité du signataire.

### CabinetConfig = organisation
Conserver le modèle actuel comme profil organisationnel.

Owner CabinetConfig : nom structure, type, adresse, contacts structure, ICE/IF, futur INPE établissement, spécialités/services structure, logo/letterhead, branding, QR, thème et préférences partagées.

### employer_id = membership mono-organisation
Conserver tant qu’aucun vrai besoin multi-site/multi-organisation n’est démontré. Pas de table Membership maintenant.

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

Sources primaires : OMPIC pour ICE, ANAM/Ministère de la Santé pour INPE.

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

**CLOSED.** Modèle métier suffisamment déterminé pour la réconciliation produit.

---

# P3 — Réglages Canonical Contract — ACTIVE

> Exécuté avant l’implémentation P2, car onboarding doit s’aligner sur Réglages et non l’inverse.

## Goal P3

Faire de Réglages la **référence fonctionnelle et contractuelle** de toute configuration cabinet/praticien réellement exposée au produit.

## Succès P3

Pour chaque valeur exposée dans Réglages :
1. concept métier explicite ;
2. owner P1 explicite (`User` ou `CabinetConfig`) ;
3. nom métier et nom technique canoniques ;
4. type/enum/default uniques ;
5. validation unique ;
6. lecture et écriture réelles ;
7. backend cible identifié ;
8. permission cible identifiée ;
9. fallback éventuel classé legacy uniquement ;
10. correspondance onboarding indiquée : `MIRROR`, `OPTIONAL MIRROR`, `SETTINGS ONLY`, `REMOVE`.

## Règle P3

P3 ne redesign pas Réglages par défaut. Il verrouille le contrat de la surface existante et ne corrige que ce qui contredit P1 ou la vérité backend.

## Matrice à produire

| Réglage canonique | Owner | Champ backend | Type/default/validation | Permission | Onboarding | Verdict |
|---|---|---|---|---|---|---|

## Surfaces prioritaires

### Profil Cabinet
- type structure ;
- nom structure ;
- identité praticien FR/AR ;
- adresse ;
- contacts ;
- ICE / IF / INPE ;
- spécialités ;
- logo.

### Design & Ambiance
- template ;
- couleurs ;
- polices ;
- marges/scales ;
- header/footer ;
- letterhead ;
- thème ;
- QR si la surface y est réellement exposée.

### Performance / Équipe
Seulement les valeurs qui impactent le contrat d’onboarding ou l’ownership.

## Findings P0 à résoudre dans P3/P4

- payload Settings avec extras interdits ;
- `nom` / `nom_praticien` / User.nom_complet ;
- custom specialties sans backend ;
- `footer_phones` vs `contacts_json` ;
- template `swiss` vs `classic` ;
- INPE ambigu ;
- multi-cabinet UI mort ;
- permissions backend manquantes.

---

# P2 — Onboarding Product Reconciliation — SPEC ACTIVE / IMPLEMENTATION AFTER P3

## Goal P2 corrigé

Construire l’onboarding comme **version guidée de Réglages**, pas comme un modèle parallèle ni comme un assistant minimaliste imposant la suppression de fonctionnalités.

### Principe

Pour toute donnée conservée dans onboarding :

`champ onboarding = même donnée que Réglages = même owner P1 = même contrat backend`

L’onboarding peut sélectionner un sous-ensemble ergonomique de Réglages, mais il ne crée jamais :
- alias métier concurrent ;
- default différent ;
- validation différente ;
- persistance locale autonome ;
- payload différent ;
- représentation dérivée persistée comme seconde vérité.

## Classification P2 corrigée

La classification précédente qui mettait presque tout en `LATER IN SETTINGS` est **annulée**.

Les catégories deviennent :
- `MIRROR REQUIRED` : demandé pendant onboarding et identique à Réglages ;
- `MIRROR OPTIONAL` : disponible pendant onboarding pour une meilleure première configuration, identique à Réglages ;
- `SETTINGS ONLY` : existe dans Réglages mais n’apporte pas assez de valeur au premier démarrage ;
- `REMOVE` : faux, mort, redondant ou sans contrat produit réel.

### Pré-classement, à finaliser après matrice P3

| Domaine onboarding actuel | Direction |
|---|---|
| Type de structure | `MIRROR REQUIRED` |
| Nom de structure | `MIRROR REQUIRED` |
| Adresse structure | `MIRROR REQUIRED` |
| Identité praticien FR/AR | `MIRROR` depuis la section praticien de Réglages, préremplie depuis User quand disponible |
| Contacts | `MIRROR OPTIONAL` |
| ICE / IF | `MIRROR OPTIONAL` si Réglages les conserve dans Profil |
| INPE | `MIRROR OPTIONAL`, mais seulement après séparation professionnel/établissement P3/P4 |
| Spécialités | `MIRROR OPTIONAL` |
| Spécialité personnalisée | suspendue jusqu’à décision P3 : vraie persistance ou REMOVE |
| QR | `MIRROR OPTIONAL` si Réglages l’expose réellement |
| Logo / letterhead | `MIRROR OPTIONAL` |
| Template / couleurs / police | `MIRROR OPTIONAL` |
| Marges/scales avancés | probablement `SETTINGS ONLY`, à confirmer par P3 UX |
| Thème | `MIRROR OPTIONAL` si Réglages reste source canonique backend |
| `footer_phones` dérivé | `REMOVE` comme saisie/source indépendante |
| faux switch multi-cabinet | `REMOVE` hors besoin réel |

Aucune suppression produit P2 ne sera faite avant la matrice P3 finale.

## Goal visuel P2

L’onboarding doit :
- **ressembler fonctionnellement à Réglages**, avec mêmes libellés et choix ;
- rester guidé, progressif et agréable pour une première installation ;
- afficher clairement ce qui pourra être modifié ensuite dans Réglages ;
- fonctionner à 390/430 sans overflow ;
- ne jamais faire croire qu’une valeur est sauvegardée avant ACK backend ;
- éviter les options avancées qui noient la première installation, sans supprimer les options utiles.

Le nombre d’étapes n’est **pas fixé à 3**. Il sera dérivé du contrat Réglages et du mockup, pas décidé arbitrairement.

## Gates UI P2

1. BEFORE P0 déjà acquis ;
2. matrice canonique Réglages P3 ;
3. Goal visuel P2 ;
4. mockup/wireframe ;
5. implémentation onboarding ;
6. AFTER mêmes viewports ;
7. BEFORE → mockup → AFTER + tests + score.

---

# Ordre d’exécution réel

Pour respecter la dépendance produit :

`P0 → P1 → P3 → P2 → P4 → P5 → P6 → P7 → P8`

Les numéros de lots restent inchangés ; seul l’ordre d’exécution P2/P3 est inversé.

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
T26 chaque champ onboarding correspond exactement à un réglage canonique ou à une justification `onboarding-only` explicitement approuvée  
T27 onboarding → Settings : égalité exacte après sauvegarde/reload

---

# Roadmap

- **P0 — Audit & Truth Map — CLOSED ✅**
- **P1 — Canonical Data Model — CLOSED ✅**
- **P2 — Onboarding Product Reconciliation — SPEC ACTIVE / implementation après P3**
- **P3 — Settings Reconciliation — ACTIVE**
- **P4 — Backend / Persistence / Permissions**
- **P5 — Legacy Migration**
- **P6 — Consumer Reconciliation**
- **P7 — UX Certification**
- **P8 — Regression & Closeout**

## Reprise

Chantier : `Onboarding ↔ Réglages`
Lot courant : `P3 — Settings Canonical Contract`
P0 : run `32560853707` SUCCESS
P1 : `User = compte/praticien`, `CabinetConfig = organisation`, `employer_id = membership mono-org`
Direction produit : **Réglages canonique → onboarding miroir guidé**
Produit modifié P0/P1 : **non**
BEFORE : 70 captures acquises
Finding UX principal : SetupWizard 569 px sur 430/390
Avancement global certifié : **22,2 % (2/9 lots)**
Next exact : **verrouiller la matrice canonique de Réglages, puis dériver le mockup onboarding à partir de cette matrice avant toute modification produit.**

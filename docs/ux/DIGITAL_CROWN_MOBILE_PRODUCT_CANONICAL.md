# Digital Crown — Mobile Product — Canonical Roadmap

Status: ACTIVE
Canonical file: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Current merged product baseline: `e2522a6d8b4794e64253eb4af36500e18cd87b40`
Deployment: none. No Vercel deployment is authorized by this chantier.

## Goal final
Faire de Digital Crown mobile un **cockpit opérationnel clinique**, pas une copie réduite du desktop. Les actions mobiles visent les usages au fauteuil, entre deux patients ou hors du poste principal. Le desktop reste le système complet pour les workflows lourds, la production clinique détaillée et le paramétrage.

Exception verrouillée — SuperAdmin : le mobile ne réduit **aucune** prérogative SuperAdmin active. L'adaptation porte uniquement sur l'UX mobile, les confirmations et les step-up de sécurité requis par le backend.

## Doctrine verrouillée
- Mobile = cockpit opérationnel.
- Desktop = workflows lourds/complets.
- SuperAdmin mobile = parité fonctionnelle complète des prérogatives actives.
- Source de vérité unique serveur/DB pour desktop + mobile.
- Aucun modèle métier parallèle mobile.
- Tout changement UI suit : BEFORE → Goal UI → référence/mockup → implémentation → AFTER mêmes viewports → comparaison + tests + score visuel.
- Aucun Vercel sans autorisation explicite.

## Navigation mobile canonique
`Aujourd’hui / Patients / + / Assistant / Plus`

---

# Lots certifiés

## MOB-2 — Patient Cockpit — DONE / MERGED
- PR `#354`
- merge `5fd2a06663e941581ad422267d31a5bb69a13d11`
- AFTER run `33889545163` ✅
- artifact `9943369750`
- score visuel **9.2/10**

## MOB-3 — Quick Action Hub — DONE / MERGED
- PR `#355`
- merge `23e4828729e085a4566cbfdf430025d1019e53fa`
- AFTER run `33927174832` ✅
- artifact `9957298023`
- score visuel **9.5/10**

## MOB-4 — Navigation mobile canonique — DONE / MERGED
- PR `#356`
- merge `28cf8278a31507d96b33c10f03e1635f86223454`
- AFTER run `33953721202` ✅
- artifact `9965680255`
- score visuel **9.6/10**

---

# MOB-5 — Mobile secondaire à forte valeur — ACTIVE

## Scope produit verrouillé

| Lot | Fonction | État |
|---|---|---|
| MOB-5A | Équipe / praticiens | DONE / MERGED |
| MOB-5B | Frontdesk / demandes RDV | DONE / MERGED |
| MOB-5C | Notifications | DONE / MERGED |
| MOB-5D | Stock | DONE / MERGED |
| MOB-5E | Bibliothèque clinique | DONE / MERGED |
| MOB-5F | Patients / Quick Document Studio | **DONE / MERGED / CLOSED** |
| MOB-5G | Marketplace / Approvisionnement | DONE / MERGED |
| MOB-5H | SuperAdmin mobile | DONE / MERGED |
| MOB-5I | Salle d’attente | **DONE / MERGED / CLOSED** |

Science Hub reste desktop only.

## MOB-5A — Équipe / praticiens — DONE / MERGED
- PR `#357`
- merge `89098066ef0c943c0e084af4b9cd388d3ab0aa5b`
- artifact `9968666702`
- score visuel **9.2/10**

## MOB-5B — Frontdesk — DONE / MERGED
- PR `#358`
- merge `21a41852182c7e74cc66c335c8d67c93a94d5871`
- cert `33968295005` ✅
- artifact `9970008232`
- score visuel **9.3/10**

## MOB-5C — Notifications — DONE / MERGED
- PR `#359`
- merge `aaa28ef97b22df2c5654c4e0da7efc15692787a8`
- artifact `9975417271`
- score visuel **9.4/10**
- push OS générique sans donnée patient
- alertes Labo exclues tant que leur isolation tenant n'est pas prouvée

## MOB-5D — Stock — DONE / MERGED
- PR `#360`
- merge `9cb740bc52efc9bf734c19fefc3c4f07470eba80`
- CI post-merge `34041170446` ✅
- artifact `9991265607`
- score visuel **9.3/10**

## MOB-5E — Bibliothèque clinique — DONE / MERGED
- PR `#361`
- merge `b850cff2bd03dda667d6e1b6e449230658035d62`
- artifact `9992080508`
- score visuel **9.4/10**
- source unique : `CLINICAL_PROTOCOLS`
- Science Hub non porté

## MOB-5F — Patients / Quick Document Studio — DONE / MERGED / CLOSED

### Goal
Créer rapidement un document depuis le cockpit patient mobile en réutilisant le moteur documentaire canonique `/api/documents/generate`, sans moteur, modèle DB ou stockage documentaire parallèle.

### Fonctions certifiées
- CTA `Créer un document` depuis le patient sélectionné;
- Ordonnance;
- Certificat;
- Devis;
- Honoraires;
- Document libre;
- familles filtrées par capacités serveur chiffrées;
- preview serveur avant archivage;
- payload verrouillé après preview;
- confirmation explicite `Archiver le document`;
- rappel de l'alerte médicale dans Ordonnance;
- backend patient/RBAC reste autoritaire;
- Échéancier volontairement laissé dans son flux financier dédié.

### Contrats verrouillés
- Ordonnance → `prescriptions`
- Certificat → `patients`
- Devis → `accounting`
- Honoraires → `accounting`
- Document libre → `clinical`
- `can_pay` historique conserve son check combiné `['accounting', 'payments']`.

### Preuves
- BEFORE baseline `e30b858f58686f5f7bef19ca93f1c5dae42929c9`
- BEFORE run `34143420251` ✅
- BEFORE artifact `10026785108`
- BEFORE digest `sha256:b827b8b31f7bb604667d1a8df624eda98b1aa794ac25145f8c7acec72af5bdff`
- product HEAD certifié `91688ffc2d5bf97e584844f972a12df717fc74da`
- AFTER run `34149391346` ✅
- AFTER artifact `10028850934`
- AFTER digest `sha256:8b27d1c8658d0472f663a152d14bf463cfd519a7ac6ca5d65e4af7811c94080e`
- 390×844 / 430×932 / 768×1024
- 0 overflow / page error / console error / API réelle en preview
- score visuel **9.1/10**
- réserve : à 390 px, la navigation fixe mord légèrement la zone d'actions initiale avant scroll; sheet et confirmation propres
- seuil produit <30 s non chronométré, donc non revendiqué comme mesure certifiée
- PR `#365` merged
- HEAD final PR `d39c9a207f1bc8b54333a332d7b6ea44a5ef9c58`
- CI PR `34152892582` ✅
- T2 `34152892437` ✅
- Patient P7 `34152892745` ✅
- merge exact `d9d1c255be6c9878ce6b7127c7f723cfb61e38a0`
- CI post-merge master `34163696668` ✅ SUCCESS
- backend Tests & durcissement ✅
- frontend tests + build ✅
- garde production ✅
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_DOCUMENTS_MOB5F_PROOF.md`

## MOB-5G — Marketplace / Approvisionnement — DONE / MERGED
- PR `#362`
- merge `6eb93c75f91402031ecc2c8fc1f8858372a97b9b`
- AFTER artifact `9994164037`
- CI post-merge `34054519282` ✅
- score visuel **9.4/10**

Limite connue : conflit de dépendances `httpx==0.27.2` avec `firebase-admin 7.5.0` / `ultralytics-platform`; ne pas le déclarer corrigé sans preuve dédiée.

## MOB-5H — SuperAdmin mobile — DONE / MERGED
- PR `#363`
- merge exact `e30b858f58686f5f7bef19ca93f1c5dae42929c9`
- Mobile SuperAdmin cert `34139811533` ✅
- AFTER artifact `10025509035`
- CI post-merge `34142208046` ✅
- score visuel **9.3/10**
- parité complète des prérogatives SuperAdmin actives maintenue

## MOB-5I — Salle d’attente — DONE / MERGED / CLOSED

### Goal
Rendre la Salle d’attente exploitable sur mobile à partir du modèle `Appointment` canonique, sans nouvelle table ni métrique inventée.

### Fonctions certifiées
- `EN_ATTENTE` ↔ `AppointmentStatus.EN_SALLE_ATTENTE` ;
- `ticket_number` exposé sous tenant scope ;
- Agenda : `PLANIFIE → EN_ATTENTE` ;
- vue `WaitingRoomView` dérivée de `Snapshot.appointments` ;
- `Au fauteuil` → `EN_COURS` / backend `EN_FAUTEUIL` ;
- entrée secondaire dans `Plus` avec badge ;
- bottom-nav principale inchangée ;
- aucune durée d’attente inventée ;
- aucune nouvelle table.

### Preuves
- BEFORE run `34168710412` ✅
- BEFORE artifact `10035019049`
- BEFORE digest `sha256:add8126ca80cc347365732da80a766549840fe16cadafc572e424aff0c479873`
- AFTER run `34169388445` ✅
- AFTER artifact `10035225974`
- AFTER digest `sha256:efa961010bb3c1d189f8447c99a70d5dfaf42c893f49fd8a4db558b5dbccbd50`
- score visuel **9.3/10**
- CI générale PR `34169598948` ✅
- PR `#367`
- HEAD final `d6a234a24fbc3a64a69763688322de31fa38f7ba`
- merge exact `e2522a6d8b4794e64253eb4af36500e18cd87b40`
- post-merge master `34170398551` ✅ SUCCESS
- closeout PR `#369`
- closeout CI `34170522549` ✅ SUCCESS
- T2 closeout `34170522692` ✅ SUCCESS

Aucun déploiement Vercel.

---

## MOB-6 — Canonisation du routage mobile — PLANNED
Goal : supprimer l’ambiguïté entre PWA mobile dédiée et shell desktop responsive après couverture des parcours essentiels.

## MOB-7 — Certification globale Mobile Product — PLANNED
Preuves minimales : frontend/backend ciblés, build, runtime, RBAC, offline/sync/revocation, context bridges, BEFORE/AFTER 390/430/768, zéro overflow, zéro erreur console/page, comparaison Goal UI, score visuel et gates physiques séparés.

## MOB-8 — Closeout — PLANNED
Ordre : validation → canonique → cohérence docs → roadmap/% réel → Git/PR/merge → post-merge → lot suivant ou CLOSED.

## Garde-fous permanents
- ne jamais porter une page sans scénario mobile démontré;
- ne pas casser les context bridges existants;
- ne pas casser l'offline;
- ne pas affaiblir sécurité / biométrie;
- ne pas exposer de données sans permission;
- ne pas mélanger mockup et preuve AFTER;
- ne jamais annoncer une certification physique depuis une CI navigateur;
- ne pas déployer sur Vercel sans autorisation explicite.

## Next exact
Engager le prochain lot explicitement défini dans la roadmap : `MOB-6 — Canonisation du routage mobile`. Aucun `MOB-5J` n'est inventé.

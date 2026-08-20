# Page Patient — Audit & Refonte Premium

Statut canonique du chantier Page Patient. Cette roadmap consolide les lots P0→P7 ; les Goal détaillés, preuves historiques et audits scientifiques restent dans les documents `PATIENT_P*` dédiés.

## Goal global

Transformer la Page Patient en workspace clinique simple, traçable, sûr et cohérent, sans perdre les fonctions utiles ni créer de seconde vérité clinique, administrative ou financière.

## Succès global

- Une seule vérité par donnée clinique, administrative et financière.
- Isolation stricte cabinet/patient et permissions métier explicites.
- Aucune donnée patient, clinique ou financière inventée silencieusement.
- Architecture en 5 espaces : Vue d’ensemble, Clinique, Imagerie, Documents, Finances.
- Persistance clinique et financière relue côté backend après mutation.
- Documents/PDF et médias accessibles par flux authentifiés.
- Baselines, Goals/wireframes et AFTER conservés pour les lots UI.
- CI/T2 et certification finale exécutées sur un HEAD P7 consolidé unique.
- Aucun déploiement Vercel sans autorisation explicite.

## État de fermeture

**HEAD produit P7 certifié : `a173b2f364905d20973987d0d66a38d5c2d8c7b9`.**

Preuves exactes sur ce HEAD produit :
- CI `32313285672` (#1456) — SUCCESS.
- T2 Runtime Browser Certification `32313285673` (#698) — SUCCESS.
- Patient P7 Final Certification `32313285794` (#1) — SUCCESS.
- Artifact P7 `9387291316`, digest `sha256:86f0da848ad1e9a191d1be81ff2e31e105b6477ac1bc9681a12b3204a1ea730f`.
- 40/40 captures : 10 surfaces × 390x844 / 430x932 / 768x1024 / 1280x900.
- 0 overflow horizontal, 0 erreur runtime, 0 HTTP 5xx.
- Score visuel final Page Patient : **9,4/10**.
- Round-trips persistés : odontogramme, conclusion praticien, Master Plan + révision, RVG upload/list/download, paiement explicite + snapshot financier.

**Règle de clôture :** le commit documentaire qui contient ce closeout et `docs/PATIENT_P7_FINAL_CERT.json` doit lui-même repasser les gates proportionnels exact-HEAD avant déclaration globale `CLOSED`.

---

# P0 — Vérité & sécurité

**Goal :** supprimer les états faux, les fuites et doubles vérités avant la refonte visuelle.

**Statut : CLOSED.**

Contrats fermés :
- anti-doublon tenant-scopé ;
- identité sans sexe implicite ;
- ClinicalHub fail-closed et Master Plan backend-authoritative ;
- assistants cliniques proposition-only ;
- paiements liés au bon patient/acte/échéance avec méthode explicite ;
- RVG authentifié + corbeille/restauration ;
- source médicale canonique unique ;
- neutralité clinique vis-à-vis du score commercial ;
- NBA/panoramique bornés, sans promotion d’heuristique en vérité clinique ;
- PDF panoramique patient-authorized et blob-streamed.

Preuve canonique : `docs/PATIENT_P0_CLOSEOUT_CERT.json`.
Exact-head closeout : CI `32196646837` + T2 `32196646938` — SUCCESS.

---

# P1 — Architecture générale Page Patient

**Goal :** réduire la densité et faire apparaître immédiatement identité, alertes utiles et actions fréquentes.

- [x] Header compact.
- [x] Actions rapides RDV / Examen-Suivi / Document / Encaisser.
- [x] 5 espaces principaux.
- [x] Archives fusionnées dans Documents.
- [x] Labels techniques/legacy retirés de la navigation.
- [x] AFTER 4 viewports sans overflow/runtime/5xx.

**Statut : CERTIFIED.**

Preuves :
- Goal : `docs/PATIENT_P1_ARCHITECTURE_GOAL.md`.
- Certificat : `docs/PATIENT_P1_ARCHITECTURE_CERT.json`.
- Product HEAD : `67e979b3df2058bf7079f36c84abd67a3f0e2e0c`.
- Visual `32201889501`, CI `32201889504`, T2 `32201889557` — SUCCESS.
- Score P1 : **9,7/10**.

---

# P2 — Vue d’ensemble / Patient Journey

**Goal :** faire de `PatientJourney` la colonne vertébrale factuelle du dossier sans dupliquer les sources.

- [x] Résumé/provenance factuels.
- [x] Prochaine action issue d’une source réelle ou état neutre.
- [x] Aucun faux `0/0` lorsqu’aucun Master Plan n’existe.
- [x] Prochain RDV réel prioritaire.
- [x] Situation financière sans faux zéro lorsque la base facturée manque.
- [x] Timeline avec source + `ref_id` et navigation vers la source.
- [x] Treatment Plan ouvre Clinique, pas Documents.
- [x] Messages de risque/intelligence opaques retirés de la Vue d’ensemble.

**Statut : CLOSED / CERTIFIED.**

Preuves :
- `docs/PATIENT_P2_JOURNEY_GOAL.md`.
- `docs/PATIENT_P2_JOURNEY_CERT.json`.
- Product HEAD `6dffc5537eb2099acdc06dc57352af9e3b60f009` : AFTER `32206275528`, CI `32206275513`, T2 `32206275516` — SUCCESS.
- Closeout HEAD `b09fc0d2bc257f0fdc53c04e7225900dfd6fd36e` : AFTER `32207231496`, CI `32207231428`, T2 `32207231444` — SUCCESS.
- Score P2 : **9,7/10**.
- Le code P2 est ancêtre du HEAD P7 final.

---

# P3 — Clinique

**Goal :** regrouper l’état clinique autour de données validées, persistées et structurées.

- [x] Bloc Sécurité médicale depuis la source Patient.
- [x] `VigilanceRadar` retiré de la lecture clinique principale.
- [x] Odontogramme canonique persistant backend avec révision/concurrence.
- [x] Examens général et spécialisés conservés.
- [x] Proposition assistant distincte d’une conclusion retenue par le praticien.
- [x] Conclusions praticien append-only et persistées.
- [x] Master Plan backend + historique de révisions.
- [x] Compagnon Diagnostique retiré de Documents ; **non déplacé automatiquement vers Clinique**, faute de justification scientifique suffisante pour conserver son ancien moteur.
- [x] Assistants conservés bornés à collecte/synthèse proposition-only ; aucune prescription/compta/Master Plan automatique.

**Statut produit : CERTIFIED PAR INTÉGRATION P7.**

Preuves :
- Goal : `docs/PATIENT_P3_CLINIQUE_GOAL.md`.
- Frontière : `docs/PATIENT_P3_SCIENTIFIC_BOUNDARY_AUDIT.md`.
- Source P3 finale réintégrée dans P7 : `02126a646322d1c1d98351ea33489384be49ab57`.
- P7 targeted backend : odontogramme, conclusions, Master Plan revisions — SUCCESS.
- P7 targeted frontend : authority boundary + persistence — SUCCESS.
- P7 browser : surface Clinique sur 4 viewports, zéro overflow/runtime/5xx — SUCCESS.
- P7 round-trips : odontogramme + conclusion praticien + Master Plan/révision réellement relus côté backend.

P3 n’a pas de certificat JSON autonome séparé : son certificat de fermeture intégré est `docs/PATIENT_P7_FINAL_CERT.json` afin d’éviter de recréer une seconde vérité de stack.

---

# P4 — Imagerie

**Goal :** unifier RVG + Panoramique + Céphalométrie sans mélanger leurs contrats scientifiques ni inventer de données.

- [x] Navigation Imagerie : RVG / Panoramique / Céphalométrie.
- [x] RVG réutilise le contrat authentifié P0-F ; aucun stockage parallèle.
- [x] Permissions modalité alignées avec le backend.
- [x] Céphalo : aucun fallback âge `20` / sexe `M` inventé.
- [x] Céphalo : aucune stratégie thérapeutique auto-écrite via `generateTreatmentPlan()`.
- [x] Panoramique : vocabulaire borné au repérage dentaire/déterministe + validation praticien.
- [x] Labels IA/SOTA/« Zéro-Hallucination » legacy retirés de cette surface.
- [x] Suppression normale Pano/Céphalo récupérable via corbeille/restauration ; analyse/fichier préservés.
- [x] Tests tenant/RBAC/lifecycle/consommateurs.

**Statut produit : CERTIFIED PAR INTÉGRATION P7.**

Preuves :
- Goal : `docs/PATIENT_P4_IMAGERIE_GOAL.md`.
- P4 final intégré comme parent P7 : `27f55a6e807c2c59b444f5c4356388043d284cfa`.
- P7 backend : `test_patient_p4_imaging_trash.py` + `test_patient_p4_imaging_consumers.py` — SUCCESS.
- P7 frontend : `PatientP4ImagingTruth.test.ts` — SUCCESS.
- P7 browser : RVG/Panoramique/Céphalo × 4 viewports — SUCCESS.
- P7 RVG round-trip upload/list/download — SUCCESS.

Aucune formule/norme scientifique n’a été modifiée par P7 ; aucune nouvelle revendication scientifique n’est ajoutée.

---

# P5 — Documents

**Goal :** conserver le Document Studio durci et rendre son entrée Patient honnête, fail-closed et permissionnée.

- [x] Créer / Historique dans le même espace Documents.
- [x] Archives fusionnées, pas de seconde archive.
- [x] Ordonnance / Certificat / Devis / Note Honoraires / Suivi Paiement / Document Libre conservés selon leurs contrats.
- [x] Compagnon Diagnostique retiré des types documentaires.
- [x] URL legacy `documentTab=plan` normalisée.
- [x] Historique fail-closed ; faux état vide après erreur interdit.
- [x] Heuristique doublon reclassée comme signal à vérifier, pas vérité métier.
- [x] RBAC frontend aligné sur les permissions backend ; backend reste autoritaire.
- [x] Blob authentifié + object URLs gérées pour ouverture/téléchargement.
- [x] A5/A4, navigateur Document Studio, PDF/impression et fraîcheur output couverts par T2 exact-head.

**Statut produit : CERTIFIED PAR INTÉGRATION P7.**

Preuves :
- Goal : `docs/PATIENT_P5_DOCUMENTS_GOAL.md`.
- P5 final `76fe188a7a9606e2ed93dd6d347753a2dbab3c14`, déjà inclus via P6 puis P7.
- P7 frontend : Document Studio RBAC + PatientDocuments truth — SUCCESS.
- P7 browser : Créer/Historique × 4 viewports — SUCCESS.
- T2 exact P7 HEAD `32313285673` — SUCCESS pour Document Studio navigateur, PDF/impression et fraîcheur output.

P5 n’a pas de certificat JSON autonome séparé : sa fermeture intégrée est portée par `docs/PATIENT_P7_FINAL_CERT.json`.

---

# P6 — Finances & identité Patient

**Goal :** rendre création/édition/finance courte, explicite et sans faux état.

- [x] Add/Edit partagent `PatientIdentityContract`.
- [x] Aucun sexe implicite.
- [x] Préchecks dossier/doublon fail-closed.
- [x] Échec GET Edit => erreur explicite, aucun patient fantôme.
- [x] KPI : Facturé / Encaissé / Reste dû / Prochaine échéance.
- [x] Base de facturation absente => solde indéterminé, jamais faux zéro.
- [x] Finances/Encaisser suivent `accounting/payments`.
- [x] Méthode de paiement explicite.

**Statut : CLOSED / CERTIFIED.**

Preuves :
- Goal : `docs/PATIENT_P6_FINANCES_IDENTITE_GOAL.md`.
- Certificat : `docs/PATIENT_P6_FINANCES_IDENTITE_CERT.json`.
- Product HEAD `fb2bd0357d6da6d4c3be9b51be45d84c764589c1` : CI `32309262380`, T2 `32309262379`, AFTER `32309262388` — SUCCESS.
- AFTER : 12/12 captures propres ; score **9,6/10**.
- Closeout HEAD P6 `2a0ac2ade90f2bae99c6e7c11302755d856a730e` : CI `32310800414`, T2 `32310800398`, BEFORE `32310800419`, AFTER `32310800428` — SUCCESS.
- P6 final est parent principal du HEAD P7.

---

# P7 — Certification finale Page Patient

**Goal :** fermer la Page Patient uniquement après preuve fonctionnelle, visuelle, clinique et sécurité sur un HEAD consolidé unique.

- [x] Stack P2/P3/P4/P5/P6 consolidée ; P7 derrière P6/P3/P4 = 0.
- [x] Contrat source final P0→P6.
- [x] Tests backend ciblés P0/P2/P3/P4/P6.
- [x] Tests frontend ciblés Journey/Clinique/Imagerie/Documents/Finances/Identité + build.
- [x] Tests tenant/RBAC/isolation couverts par les suites ciblées des surfaces concernées.
- [x] Persistance relue : odontogramme, conclusion praticien, Master Plan + révision, RVG, paiement/snapshot.
- [x] Documents/PDF/impression/fraîcheur output via T2 exact-head.
- [x] 40 captures finales : 10 surfaces × 4 viewports.
- [x] 0 overflow horizontal / runtime error / HTTP 5xx dans la matrice P7.
- [x] Score visuel final argumenté : **9,4/10**.
- [x] CI `32313285672`, T2 `32313285673`, P7 Final `32313285794` — SUCCESS sur `a173b2f...`.
- [x] Certificat produit final : `docs/PATIENT_P7_FINAL_CERT.json`.

### Limites explicitement non sur-vendues

- Aucun nouveau **audit autonome exhaustif clavier/focus** n’est revendiqué au-delà des interactions navigateur et tests réellement exécutés.
- Le parcours complet n’est pas revendiqué comme un unique scénario monolithique « création Patient → archive » ; ses persistance/actions critiques sont prouvées par les gates dédiés P7 + T2.
- Deux dettes UX mobiles non bloquantes restent visibles : rail horizontal des types Documents et emprise du bouton flottant Crown Bot en bas à droite.

### Preuve visuelle finale

Artifact `9387291316` :
- overview ;
- clinical ;
- imaging-rvg ;
- imaging-panoramic ;
- imaging-cephalo ;
- documents-create ;
- documents-history ;
- finances ;
- add-patient ;
- edit-patient ;

sur `390x844`, `430x932`, `768x1024`, `1280x900`.

**Statut produit : CERTIFIED.**

**Statut chantier : PENDING CLOSEOUT EXACT-HEAD RECERTIFICATION** tant que le commit documentaire portant cette roadmap et le certificat final n’a pas lui-même repassé CI + T2 + P7 Final.

---

## Architecture finale de référence

```text
PATIENT
├── Header compact + alertes utiles + actions rapides
├── Vue d’ensemble
│   └── Patient Journey factuel et sourcé
├── Clinique
│   ├── Sécurité médicale
│   ├── Odontogramme persistant
│   ├── Examens / propositions
│   ├── Conclusions praticien
│   └── Master Plan versionné
├── Imagerie
│   ├── RVG
│   ├── Panoramique
│   └── Céphalométrie
├── Documents
│   ├── Créer
│   └── Historique / archives
└── Finances
    ├── Facturé
    ├── Encaissé
    ├── Reste dû
    └── Prochaine échéance
```

## Règles de chantier

- Pas de rebuild gratuit.
- Backend autoritaire pour persistance, tenant et RBAC.
- Pas de vérité clinique/financière dans `localStorage`.
- Pas de succès UI avant succès backend réel.
- Pas de donnée médicale ou financière implicite.
- Pas de changement UI sans baseline + Goal visuel + référence + AFTER.
- Pas de déploiement Vercel sans autorisation explicite.
- Un lot n’est `CLOSED` qu’avec preuves sur son HEAD exact.

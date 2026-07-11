# TREATMENT JOURNEY — DESIGN PRODUIT (avant tout code)
## P0-TREATMENT-JOURNEY-1

> Date : 2026-07-10
> Statut : DESIGN UNIQUEMENT — aucun code écrit. À valider explicitement avant toute implémentation.
> Origine : reformulation de `P0-TREATMENT-PLAN-UX-1` (voir `STATE.md`) — le CTO a demandé que
> cette mission ne soit pas une "jolie timeline" mais la colonne vertébrale du dossier patient.
> Méthode : 3 agents Explore (modèle de données, patterns UI existants, patterns de performance),
> ~45 fichiers backend+frontend inspectés.

---

## 0. Le fait le plus important découvert par la recherche

**Le schéma actuel est plus plat que ce qu'on imaginait.** Il n'y a aujourd'hui **aucune clé
étrangère** entre `Acte` et `TreatmentPlanStep`, ni entre `DocumentArchive` (devis, ordonnances,
certificats...) et `Acte`/`Payment`. Les seuls vrais liens relationnels qui existent :

- `Payment.acte_id` (optionnel) et `Payment.installment_id` (optionnel)
- `LabJob.act_id`
- `Installment.plan_id` → `InstallmentPlan`

Tout le reste (TreatmentPlanStep, Acte, DocumentArchive, PanoramicAnalysis, CephaloAnalysis,
Appointment) n'est relié au patient que par `patient_id`, sans lien croisé entre eux. Ce fait
conditionne toutes les réponses ci-dessous — je le signale en premier parce qu'il change la
réponse "évidente" à la question 1.

---

## 1. Quelle est l'entité centrale ?

**Ni le patient seul, ni le plan de traitement seul : le patient est la racine d'agrégation, mais
le plan de traitement ne peut PAS être l'ossature structurelle aujourd'hui — parce qu'il n'est
relié à rien d'autre en base.**

Concrètement :
- `TreatmentPlanStep` a un statut (`PENDING/DONE/POSTPONED`) et un `order_index`, mais **aucune
  colonne ne relie un step à l'Acte qui le concrétise, ni au Devis qui le facture.**
- `Acte` est la seule entité qui porte à la fois une date fiable (`date_debut`, DateTime réel —
  pas une string), un montant, et un statut de paiement. C'est la donnée la plus "dure" et la
  plus dense du dossier patient.
- `DocumentArchive` porte `document_type` (DEVIS, ORDONNANCE, CERTIFICAT, RADIOGRAPHIE, BILAN...)
  et une date de création, mais aucun lien vers l'Acte ou le Payment concerné.

**Recommandation :** traiter le **Patient** comme racine, et construire le Journey comme une
**fusion chronologique d'événements datés** provenant de plusieurs tables indépendantes — pas
comme un arbre descendant `Plan → Step → Acte`. Le plan de traitement reste affiché et mis en
avant visuellement (c'est l'intention clinique), mais il n'est pas la "colonne vertébrale
relationnelle" au sens base de données, car les données actuelles ne le permettent pas sans
réécrire l'historique.

**Si tu veux vraiment que le plan de traitement devienne l'ossature réelle** (pas juste visuelle),
il faut une petite migration additive : ajouter `treatment_plan_step_id` (nullable) sur `Acte`, et
lier les nouveaux actes créés depuis le studio de plan de traitement. Ça ne réparera pas
l'historique déjà en base (les actes existants resteront orphelins de tout step), mais ça
structurera tout le nouveau flux à partir de maintenant. Voir section 9 (décision à trancher).

---

## 2. Quelles étapes composent le Journey ?

J'ai vérifié étape par étape ce qui a une donnée réelle derrière, et ce qui n'en a aucune.

| Étape voulue | Donnée backing en base | Fiabilité |
|---|---|---|
| Consultation initiale | `Appointment` (status=`TERMINE`) — pas de modèle Consultation dédié | Moyenne (implicite) |
| Diagnostic | **Aucune** — pas de champ/table daté "diagnostic établi" | **Absente** |
| Examens / Radios | `DocumentArchive` (type RADIOGRAPHIE), `PanoramicAnalysis`, `CephaloAnalysis` | Bonne |
| Plan de traitement | `TreatmentPlanStep` (attention : `date_str` est une **string**, pas un DateTime — à normaliser) | Moyenne |
| Validation patient | **Aucune** — pas de flag "devis accepté par le patient" en base | **Absente** |
| Devis | `DocumentArchive` (type DEVIS) | Bonne |
| Paiement / acompte | `Payment`, `InstallmentPlan`/`Installment` | Excellente |
| Actes (un par un) | `Acte` | Excellente |
| Contrôle | **Aucune** — pas de type d'Appointment "contrôle" distinct d'un RDV normal | **Absente** |
| Clôture | **Aucune** — `TreatmentMasterPlan` n'a pas de champ "clôturé" | **Absente** |

**Constat honnête :** 4 des 10 étapes voulues (Diagnostic, Validation patient, Contrôle, Clôture)
n'ont **aucune trace en base aujourd'hui**. Les afficher comme "vraies" étapes serait mentir sur
la donnée. Trois options, tranchées en section 9 :
- (a) Les omettre du Journey V1, n'afficher que ce qui est backé par une vraie donnée
- (b) Les déduire par heuristique (ex. "Diagnostic" = premier document de type BILAN)
- (c) Ajouter une table légère additive `JourneyMilestone` pour permettre au praticien de les
  marquer manuellement (2 clics : "Diagnostic établi", "Devis validé", "Traitement clôturé")

---

## 3. Quels objets sont reliés, sans duplication ?

Le Journey ne stocke rien de nouveau (sauf décision section 9) — il **interroge et fusionne** les
tables existantes par `patient_id`, ordonnées par date. Chaque type d'événement garde sa source de
vérité :

| Type d'événement | Table source | Champ date utilisé |
|---|---|---|
| Séance / consultation | `Appointment` | `date` (RDV avec statut TERMINE) |
| Étape du plan | `TreatmentPlanStep` (via `TreatmentMasterPlan`) | `date_str` (à parser/normaliser) |
| Devis / Facture / Ordonnance / Certificat / Bilan / Radio (RVG) | `DocumentArchive` | `created_at` |
| Panoramique | `PanoramicAnalysis` | `created_at` |
| Céphalométrie | `CephaloAnalysis` | `created_at` |
| Acte réalisé | `Acte` | `date_debut` |
| Paiement | `Payment` | `payment_date` |
| Échéance | `Installment` (via `InstallmentPlan`) | `due_date` / `paid_date` |
| Travail laboratoire | `LabJob` (lié à `Acte` via `act_id`) | `created_at` / `deadline` |

**Zéro duplication** : l'endpoint d'agrégation ne fait que lire et fusionner. Cliquer sur un
événement renvoie vers l'écran qui possède déjà cette donnée (voir section 6) — le Journey
n'est jamais la source de vérité, seulement une vue.

---

## 4. Quelle UX ? (plusieurs propositions + recommandation)

**Précédent existant à connaître :** `PatientTracking.tsx` (onglet "Tracking" actuel du dossier
patient) affiche **déjà** une timeline verticale des actes. Ce n'est pas un point de départ à
zéro — c'est une base à étendre.

### Option A — Timeline verticale (extension de PatientTracking existant)
Une colonne unique, chronologique, avec un point coloré par type d'événement (acte, document,
paiement, radio, labo) et une ligne de connexion verticale. Chaque item est une carte compacte
(icône + titre + date + statut) qui s'étend au clic pour un résumé, avec un lien "Voir" vers
l'écran source.

- ✅ Cohérent avec l'existant (PatientTracking déjà vertical)
- ✅ Scroll naturel, facile à lire même sur 10 ans d'historique avec les bons filtres
- ✅ Pattern déjà connu du praticien (moins de friction d'adoption)
- ❌ Moins "visuel/pipeline" que ce qu'un concurrent montre en démo

### Option B — Timeline horizontale (type "roadmap produit")
Étapes en colonnes horizontales scrollables, une ligne de progression traversant les colonnes.

- ✅ Très démonstratif visuellement (bon pour la vente)
- ❌ Aucun précédent dans le code — tout est à inventer
- ❌ Scaling horizontal avec 400 actes = illisible sans agrégation lourde par phase
- ❌ Plus dur à rendre responsive sur les résolutions cabinet standards

### Option C — Kanban (type LabJobsBoard)
Colonnes par phase (Diagnostic / Plan / Devis / Paiement / Réalisation / Contrôle), cartes
déplaçables.

- ✅ Précédent direct réutilisable (`LabJobsBoard.tsx`)
- ❌ Un Kanban suppose un item par colonne à un instant T — mal adapté à un historique qui
  s'accumule (on ne "range" pas un acte réalisé il y a 3 ans, on le consulte)
- ❌ Confond "workflow actif" (Kanban = bon) et "historique clinique" (Kanban = mauvais)

### Option D — Mix timeline + résumé (recommandée)
Une **timeline verticale** (option A étendue) précédée d'un **bandeau résumé** en haut de
l'onglet : statut du plan en cours (X/Y étapes faites), reste dû, prochain RDV, dernier document.
La timeline elle-même est **groupée par phase** avec un en-tête pliable par phase plutôt qu'un
flux plat de 400 items.

**Recommandation : Option D.** Elle réutilise le pattern existant de `PatientTracking.tsx` (moins
de risque, adoption immédiate), résout le problème de densité (section 5) par le groupement/pliage,
et donne quand même l'effet "pipeline" voulu via le bandeau résumé en tête d'onglet — sans les
faiblesses du Kanban sur de la donnée historique.

---

## 5. Comment éviter le "sapin de Noël" (40 événements affichés) ?

Trois mécanismes combinés, tous nécessaires ensemble :

1. **Groupement par phase, plié par défaut** — seule la phase en cours (ou la plus récente) est
   dépliée à l'ouverture ; les phases terminées sont réduites à une ligne résumé ("Phase Devis —
   3 documents, terminée le 12/03") qu'on déplie au clic.
2. **Filtres par type** — chips filtrables (Actes / Documents / Paiements / Radios / Labo),
   persistés en query param comme le fait déjà `PatientDetails.tsx` avec `activeTab`.
3. **Zoom temporel** — par défaut, afficher les 12 derniers mois + tout ce qui est "en cours"
   (steps PENDING, installments impayés) ; un bouton "Voir tout l'historique" charge le reste
   (voir pagination, section 8).

---

## 6. Navigation — que se passe-t-il au clic ?

Le pattern déjà utilisé dans l'app est **cohérent et à réutiliser tel quel** (confirmé par
l'agent UI) : modale pour les actions ponctuelles, changement d'onglet/route pour la navigation
pleine page. Pas de nouveau pattern à inventer.

| Clic sur | Comportement | Précédent réutilisé |
|---|---|---|
| Une **ordonnance/certificat/devis** | Ouvre le PDF dans un nouvel onglet navigateur | `PatientDocuments.tsx::handleView()` (déjà existant) |
| Un **paiement** | Ouvre `PayActeModal` en lecture (ou juste affiche le détail inline, pas de nouvelle modale à écrire) | `PatientFinances.tsx` (déjà existant) |
| Une **radio/panoramique/céphalo** | Navigue vers l'onglet Radiologie existant, ancré sur l'analyse concernée | Changement de `activeTab` (pattern existant `PatientDetails.tsx`) |
| Un **acte** | Étend la carte inline (résumé : montant, statut, notes) — pas de navigation externe, l'info est déjà dans l'objet Acte agrégé | Nouveau, mais mineur (juste un expand/collapse) |
| Une **étape de plan** | Renvoie vers `TreatmentPlanStudio` (onglet Admin) sur l'étape concernée | `setEditingDoc()` + tab change (pattern existant) |
| Un **travail labo** | Navigue vers `/labo` filtré sur ce patient (dépend du filtre patient du backlog labo, cf. `STATE.md`) | Nouveau lien, filtre déjà en backlog labo |

Aucune nouvelle modale complexe à construire — le Journey renvoie vers des écrans qui existent
déjà. C'est délibéré : ça réduit fortement le risque de la mission.

---

## 7. États

Chaque événement affiché a déjà son propre statut natif — pas besoin d'inventer un état
générique unifié qui perdrait de l'information :

- Acte → `PaiementStatut` existant (`EN_ATTENTE`, `PAYE`, `PARTIEL`, `A_ENCAISSER`)
- TreatmentPlanStep → `PlanStatus` existant (`PENDING`, `DONE`, `POSTPONED`)
- Document → `DocumentStatus` existant
- Installment → statut existant (payé / en attente / en retard)
- LabJob → `LabJobStatus` existant (6 valeurs, PRESCRIPTION → DELIVERED)

**Recommandation :** ne pas créer de nouvel enum "état du Journey" — mapper chaque statut natif
vers 3 couleurs visuelles génériques (vert=terminé, ambre=en cours/attente, rouge=problème/retard)
pour la cohérence visuelle de la timeline, tout en gardant le libellé exact du statut natif au
survol/clic. Annuler (`ANNULE`, etc.) doit rester visible mais grisé, pas masqué — un praticien
doit pouvoir voir qu'un acte a été annulé, pas juste qu'il "disparaît" de l'historique.

---

## 8. Performance

Constats de l'agent recherche performance, directement actionnables :

- **Aucun endpoint existant n'agrège plus de 2-3 tables pour un patient** — le plus proche
  (`get_patient_financial_snapshot`, `patients.py:407-518`) plafonne déjà ses listes imbriquées
  (10 impayés, 5 échéances, 5 paiements) plutôt que de tout charger. **Même principe à reprendre
  pour le Journey : ne jamais charger l'historique complet par défaut.**
- **Aucun eager-loading (`joinedload`/`selectinload`) n'existe aujourd'hui** sur les requêtes
  actes/paiements/documents — un endpoint Journey naïf ferait du N+1 sur 6 tables. Nécessite un
  vrai travail de requêtes explicites (pas juste réutiliser les endpoints existants tels quels).
- **Aucun pattern d'infinite-scroll côté frontend** — pas de `useInfiniteQuery` dans le code
  actuel. Deux choix : introduire ce pattern maintenant (cohérent avec un historique long), ou
  rester sur le "fenêtrage temporel" de la section 5 (12 derniers mois + en cours, bouton "voir
  plus") qui est plus simple et suffit pour du 400 actes / 800 documents.
- **Pool DB : 10 connexions + 30s timeout, pas de query timeout applicatif** — une agrégation
  6 tables mal indexée pourrait saturer le pool si plusieurs praticiens ouvrent le Journey de gros
  dossiers en même temps. Nécessite des index sur `patient_id` + colonne date pour chaque table
  jointe (à vérifier/ajouter en migration additive si absents).

**Recommandation :** fenêtrage temporel (section 5) + requêtes explicites avec eager loading,
plutôt qu'infinite-scroll. C'est le choix le plus simple qui respecte le pattern déjà en place
dans `get_patient_financial_snapshot`.

---

## 9. Version MVP — ce qui rentre, ce qui est reporté

### Rentre dans Treatment Journey V1
- Endpoint backend unique d'agrégation, fenêtré (12 mois + items "en cours"), avec eager loading
- Timeline verticale groupée par phase (Option D), pliage par défaut sur les phases terminées
- Étapes backées par une vraie donnée : Consultation (Appointment TERMINE), Plan (TreatmentPlanStep),
  Devis (DocumentArchive DEVIS), Paiement (Payment/Installment), Actes (Acte), Documents/Radios
  (DocumentArchive/PanoramicAnalysis/CephaloAnalysis), Labo (LabJob)
- Filtres par type d'événement
- Navigation par réutilisation des écrans existants (aucune nouvelle modale complexe)
- Bandeau résumé en tête d'onglet (statut plan, reste dû, prochain RDV, dernier document)
- Nouvel onglet dans `PatientDetails.tsx` (probablement fusion/renommage de l'onglet "Tracking"
  existant plutôt qu'un onglet en plus — à trancher, cf. question ouverte ci-dessous)

### Reporté (V1.1 ou V2), à ne PAS faire maintenant
- Étapes sans donnée backing (Diagnostic, Validation patient, Contrôle, Clôture) — dépend de la
  décision section suivante
- `Acte.treatment_plan_step_id` (lien réel Plan→Acte) si on choisit de ne pas migrer maintenant
- Infinite-scroll / historique complet sans fenêtrage
- Vue Kanban alternative, vue horizontale
- Export PDF du Journey complet (probablement demandé un jour, hors scope V1)

---

## Décisions prises (CTO, 2026-07-10)

**A. Étapes sans donnée → table additive `JourneyMilestone`.**
Nouvelle table légère, additive, marquage manuel praticien (2 clics : "Diagnostic établi", "Devis
validé par le patient", "Traitement clôturé"). Champs minimaux : `patient_id`, `milestone_type`
(enum : DIAGNOSTIC / DEVIS_VALIDE / CONTROLE / CLOTURE), `date`, `note` optionnelle,
`created_by`. Ajoute ~1 jour de travail au périmètre V1 mais évite les trous et les heuristiques
fragiles dans le Journey.

**B. Lien réel Plan→Acte → fait maintenant.**
Migration additive : `Acte.treatment_plan_step_id` (nullable, FK vers `TreatmentPlanStep`).
L'historique existant reste orphelin (attendu, aucun backfill risqué). Tout nouvel acte créé
depuis `TreatmentPlanStudio` devra désormais être rattaché à son step d'origine — ce qui rend le
plan de traitement réellement structurant pour les nouveaux dossiers, pas seulement visuellement.

**C. Placement UI → fusion avec l'onglet "Tracking".**
Le Journey remplace/absorbe l'onglet "Tracking" actuel de `PatientDetails.tsx` (qui affiche déjà
une timeline d'actes plus simple) plutôt que de coexister avec lui. Un seul onglet chronologique
par dossier patient, pas deux qui se ressemblent.

### Impact sur le périmètre V1 (mis à jour)
Le MVP V1 (section 9) intègre désormais :
- Migration additive n°1 : `Acte.treatment_plan_step_id` nullable (FK)
- Migration additive n°2 : nouvelle table `JourneyMilestone`
- `TreatmentPlanStudio` doit écrire `treatment_plan_step_id` sur les actes qu'il crée
- Un petit contrôle UI pour poser un jalon manuel (`JourneyMilestone`) depuis le Journey
- L'onglet "Tracking" existant est remplacé, pas dupliqué — vérifier tous les liens/redirections
  qui pointent vers `?tab=tracking` avant de le renommer

Ces deux migrations restent strictement additives (CREATE TABLE / ADD COLUMN nullable), conformes
aux règles absolues de `CLAUDE.md` — aucun DROP, aucun ALTER de colonne existante.

**Prochaine étape :** plan d'implémentation détaillé (fichiers à toucher, ordre des migrations,
découpage en sous-tâches testables) — à faire via `EnterPlanMode` séparément, avec validation
explicite avant la première ligne de code, comme demandé.

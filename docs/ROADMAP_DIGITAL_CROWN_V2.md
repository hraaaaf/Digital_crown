# ROADMAP DIGITAL CROWN V2 — STRATEGIC LOCK
## ROADMAP-DIGITAL-CROWN-V2-STRATEGIC-LOCK

> Date : 2026-07-09
> Statut : VERROUILLÉE — lecture seule, aucun code applicatif modifié
> Source : audit `DIGITAL_CROWN_FEATURE_AUDIT_VS_COMPETITOR.md` + lecture complète du codebase (60+ fichiers backend, 30+ fichiers frontend)

---

## 1. VISION V2

**Digital Crown V2 = le système d'exploitation local-first complet du cabinet dentaire**

Aujourd'hui Digital Crown est un logiciel clinique excellent mais perçu comme technique. V2 le transforme en plateforme de gestion complète — le cabinet tourne dedans, pas juste les dossiers cliniques.

### Les 3 angles différenciants

**A. Parité cabinet (manque actuel = blocage commercial)**
- Stock / consommables avec déduction automatique
- Workflow financier complet : Acte → Plan → Devis → Facture → Paiement
- Dashboard financier temps réel (CA du jour, impayés, taux de recouvrement)
- Plans de traitement avec UI visuelle et suivi avancement
- Module laboratoire activé (backend complet, UI à brancher)

**B. Supériorité clinique (déjà acquise, à maintenir)**
- IA ONNX locale panoramique (YOLO11x, 4 classes) — concurrent = absent
- Céphalométrie automatique complète (studio 4 étapes, validator, calibration mm/px)
- 14 générateurs PDF bilingues Fr/Ar avec QR stratégique et médico-légal
- Ordonnance intelligente (pharmacovigilance temps réel, learning loop, agentic AI)
- Crown Bot LLM local (Ollama, 15 intents, PII masking, schema strict)
- Orthodontie (expert system, orthoExpertSystem.ts, bilan ortho PDF)

**C. Supériorité confiance (irréplicable à court terme)**
- Local-first : zéro donnée patient dans le cloud
- PostgreSQL obligatoire en production (`validate_environment_invariants()`)
- Backup chiffré Fernet (PBKDF2 + CABINET_MASTER_KEY_HEX)
- Médias servis uniquement par routes FastAPI authentifiées (jamais StaticFiles public)
- Isolation tenant stricte (employer_id sur chaque table, `assert_patient_access()`)
- Audit log complet, ZKA mobile ECDH, JWT révocation (JTI blacklist)
- Installation on-premise documentée, PyInstaller EXE, Firebase hors-ligne

---

## 2. SCORE GLOBAL — RECALCUL STRICT

### Règles de scoring strict appliquées
- Feature backend sans UI = comptée à 50% maximum
- Feature documentée mais non branchée = non comptée (ex. : LabJobsBoard commenté dans App.tsx ligne 36/185)
- Feature partielle = notée sur ce qui est réellement utilisable
- Pas de sur-notation sur les "bonnes intentions"

### Scores retenus

| Dimension | DC aujourd'hui | Concurrent estimé | DC après P0 | DC après P0+P1 | DC après P0+P1+P2 |
|---|---|---|---|---|---|
| **Score global** | **7,0 / 10** | **7,0 / 10** | **8,2 / 10** | **9,0 / 10** | **9,4 / 10** |
| Différenciation IA | 9/10 | 5/10 | 9/10 | 9,5/10 | 9,5/10 |
| Sécurité / local-first | 9,5/10 | 4/10 | 9,5/10 | 9,5/10 | 9,5/10 |
| Workflow financier | 4,5/10 | 8/10 | 7,0/10 | 9,0/10 | 9,5/10 |
| Stock / consommables | 0/10 | 7/10 | 5/10 | 7,5/10 | 9,0/10 |
| Dossier patient | 8/10 | 7,5/10 | 8,0/10 | 8,5/10 | 9/10 |
| Agenda / Frontdesk | 7/10 | 7/10 | 7,5/10 | 8,5/10 | 8,5/10 |
| Imagerie | 8,5/10 | 6/10 | 8,5/10 | 9/10 | 9/10 |
| Orthodontie | 9/10 | 6/10 | 9/10 | 9/10 | 9,5/10 |
| Module laboratoire | 2/10 (backend seul, UI off) | 4/10 | 6,5/10 | 7/10 | 8/10 |
| Dashboard | 5,5/10 | 8/10 | 7,5/10 | 8,5/10 | 9/10 |

**Note sur le recalcul :** Le score DC actuel est ramené de 7,2 à 7,0 après application des règles strictes. Le workflow financier est noté 4,5 (pas 6) car la vue impayés est absente, le dashboard financier temps réel manque, et le pipeline Acte→Facture n'est pas visuellement unifié malgré `AccountingPage.tsx` (72 Ko). Le module laboratoire est 2/10 car `LabJobsBoard` est commenté dans App.tsx (lignes 36 et 185) — backend présent mais UI = `ComingSoon`.

---

## 3. FONCTIONNALITÉS GAGNANTES ACTUELLES (Digital Crown devant)

| Domaine | Preuve dans le code |
|---|---|
| **IA panoramique ONNX** | `backend/services/panoramic_service.py` — YOLO11x local, 4 classes. Concurrent = absent |
| **Céphalométrie** | `backend/services/cephalo_engine.py` (37 Ko) — 4 étapes, calibration mm/px, validator clinique, mesures auto SNA/SNB/ANB |
| **Ordonnance intelligente** | `backend/routers/prescriptions.py` + `backend/services/prescription_service.py` — pharmacovigilance live, learning loop, scraping medicament.ma |
| **Crown Bot** | `backend/routers/bot.py`, `backend/services/bot/llm_parser.py` — 15 intents, PII masking (`data_sanitizer.py`), schema JSON strict, pending actions en DB |
| **14 générateurs PDF** | `backend/services/generators/` — bilingues Fr/Ar, QR code, watermark, letterhead, archivage hash SHA-256 |
| **Orthodontie** | `frontend/src/features/ortho/orthoExpertSystem.ts`, `bilan_ortho_gen.py` — système expert, arbre décisionnel |
| **Sécurité données** | `backend/main.py` (lignes 599-675) — médias derrière auth FastAPI, `_assert_media_tenant()`, isolation tenant sur chaque table |
| **Multi-tenant/Packs** | `backend/routers/team.py` — GOLD/PREMIUM/ELITE, quotas, workflow approbation, RBAC 9 permissions |
| **Backup chiffré** | `backend/scripts/backup_db.py` — Fernet + PBKDF2 + find_pg_binary() |
| **PWA mobile ZKA** | `backend/routers/mobile.py` + `frontend/src/services/zka/` — ECDH P-256, masterKey jamais en clair |

---

## 4. MANQUES BLOQUANT LA VENTE (concurrent en avance)

| Module | Ce qui manque | Preuve absence / parcialité |
|---|---|---|
| **Stock / Consommables** | Module entièrement absent | `backend/models.py` : aucun modèle StockProduct/StockMovement. Aucun `backend/routers/stock.py`. Aucune page frontend stock. Mention "STOCK" uniquement dans GhostMemoryLog.insight_type |
| **Vue impayés dédiée** | Aucune page/onglet "patients avec reste dû" | `frontend/src/pages/AccountingPage.tsx` (72 Ko) n'a pas de section dédiée impayés. Pas de requête SQL consolidée patients→solde |
| **Dashboard financier J+0** | CA du jour, encaissements du jour absents | `frontend/src/pages/Dashboard.tsx` ligne 60-98 : pas d'indicateur CA temps réel ni impayés synthétiques |
| **Module laboratoire UI** | LabJobsBoard commenté | `frontend/src/App.tsx` lignes 36 et 185 : `ComingSoon` à la place de `LabJobsBoard` |
| **Pipeline Acte→Facture unifié** | UI non unifiée visuellement | `TreatmentPlanStudio.tsx` et `AccountingStudio.tsx` distincts, pas de vue pipeline en un coup d'oeil |
| **Plan de traitement visuel** | TreatmentMasterPlan existe en DB mais pas de timeline visuelle | `backend/models.py` lignes 298-320 : TreatmentPlanStep avec statut pending/done/postponed, pas de vue dédiée frontend |
| **Avances patients nommées** | Concept absent | Pas de table `PatientAdvance` dans models.py — les avances sont gérées via Installment/Payment mais sans concept dédié nommé |
| **Salle d'attente temps réel** | Vue dédiée absente | Statut EN_S_ATTENTE présent dans models.py ligne 48-61 mais pas de widget dédié dans Dashboard |

---

## 5. DÉCISION P0 : FINANCE D'ABORD OU STOCK D'ABORD ?

### Scénario A — Stock d'abord
Stock → consommables → alertes → lien actes

**Arguments pour :**
- Concurrent démontre le stock explicitement en vidéo de vente — argument de démo puissant
- 0/10 actuel vs 7/10 concurrent = plus gros écart absolu
- Infrastructure partiellement prête : ProactiveAlert de type STOCK déjà dans models.py, GhostMemoryLog.insight_type STOCK

**Arguments contre :**
- Développement plus lourd : modèles DB à créer de zéro (StockProduct, StockMovement), router, UI complète — estimé 5-8 jours
- Le stock impressionne lors de la démo mais ne déclenche pas l'achat immédiatement
- Un cabinet peut fonctionner sans stock dans le logiciel (carnet papier, tableur) — il ne peut pas fonctionner sans vue de ses impayés
- ROI perçu : le stock économise du temps de gestion ; les impayés, ça coûte de l'argent à ne pas les voir

**Score commercial immédiat :** Moyen — le stock est une feature de démo, pas une feature de rétention quotidienne

---

### Scénario B — Finance d'abord
Patient financier snapshot → impayés → dashboard CA → devis/facture/paiement

**Arguments pour :**
- Les impayés sont consultés **tous les jours** — le dentiste voit son reste-à-encaisser en ouvrant le logiciel le matin
- Dashboard CA = première question que le propriétaire pose le soir ("j'ai fait combien aujourd'hui ?")
- Infrastructure largement prête : AccountingPage.tsx (72 Ko), accounting_service.py, Payment/InstallmentPlan en DB, analytics.py avec taux de recouvrement calculé
- Complexité faible pour fort impact : 2-3 jours pour la vue impayés (requête SQL déjà connue), 1-2 jours pour widget dashboard
- Parle immédiatement au cabinet dans n'importe quelle démo : "regardez, là vous voyez tout de suite qui vous doit de l'argent"
- Lien direct avec la rétention : un logiciel qui montre les impayés crée une habitude quotidienne — l'utilisateur ne peut plus s'en passer

**Arguments contre :**
- Moins spectaculaire visuellement dans une démo vidéo de 3 minutes
- Le concurrent a les deux (stock + finance) — financer d'abord ne comble qu'un écart

**Score commercial immédiat :** Élevé — rétention quotidienne, urgence ressentie, ROI immédiat

---

### RECOMMANDATION : SCÉNARIO B — FINANCE D'ABORD

**Verdict : Finance d'abord, et voici pourquoi c'est la bonne décision :**

1. **Urgence perçue différente.** L'impayé, c'est de l'argent que le cabinet a perdu de vue. Le stock, c'est de l'organisation à améliorer. Les deux sont importants, mais l'un crée une urgence émotionnelle immédiate.

2. **Fréquence d'usage.** Un dentiste regarde ses impayés et son CA chaque jour. Il vérifie son stock une fois par semaine. Digital Crown doit devenir indispensable quotidiennement.

3. **Effort/impact optimal.** Le module finance est 70% déjà là (AccountingPage, analytics, Payment, InstallmentPlan). Il manque la vue consolidée et les widgets dashboard — 3-5 jours de travail pour passer le score workflow financier de 4,5 à 7,5. Le stock de 0 à 5 demande 8 jours.

4. **Ordre naturel.** Si un prospect compare Digital Crown et le concurrent, la démo montre d'abord le workflow "est-ce que je peux faire mon travail quotidien ?" (agenda, dossiers, **paiements, impayés**), puis "est-ce que ça gère mon opérationnel ?" (stock, labo). La finance passe avant.

5. **Argument vente "prêt immédiatement."** Le patient financial snapshot + impayés + dashboard CA est livrable en semaine 1-2. Il change immédiatement la perception du logiciel dans la démo.

**Concession au Scénario A :** Le stock reste P0 mais en semaine 3, après le financier. Ordre final P0 : Finance S1-S2, puis Stock S3, puis Lab UI S4 (1-2 jours seulement car backend complet).

---

## 6. ROADMAP 30 JOURS — P0 DÉTAILLÉ

**Objectif P0 :** Passer de 7,0 à 8,2 en comblant les 4 lacunes commerciales critiques dans l'ordre Finance → Stock → Lab.

```
Semaine 1 : Patient Financial Snapshot + Widget impayés Dashboard
Semaine 2 : Dashboard financier J+0 + Vue impayés dédiée complète
Semaine 3 : Stock / Consommables MVP (modèle DB + router + UI)
Semaine 4 : Module Lab UI réactivation + tests + stabilisation + release P0
```

---

### SEMAINE 1 — Patient Financial Snapshot + Impayés foundation

**Missions :** P0-PATIENT-FINANCIAL-SNAPSHOT-1

**Objectif :** Dans le dossier patient (PatientDetails.tsx), ajouter un onglet "Finances" montrant : total facturé, total encaissé, reste dû, plan de paiement en cours, historique des paiements.

**Impact commercial :** Le dentiste voit en un coup d'oeil combien chaque patient lui doit. Argument de démo immédiat.

**Complexité :** Faible. L'infrastructure existe : Payment table dans models.py (lignes 792-814), InstallmentPlan (lignes 816-856), AccountingPage.tsx (72 Ko) avec graphiques Recharts, QuickPayModal déjà dans PatientDetails. C'est de l'assemblage de données existantes + nouveau onglet.

**Risque :** Faible. Lecture seule principalement. Aucun modèle DB à créer.

**Dépendances :** accounting_service.py (solde patient), analytics.py (taux de recouvrement)

**Critère de réussite :** GET /api/patients/{id}/financial-summary retourne {total_facture, total_encaisse, reste_du, plan_actif}. Onglet "Finances" visible dans PatientDetails avec les 3 chiffres clés.

**Bilan attendu :** Chaque dossier patient devient un outil de gestion financière, pas juste clinique.

---

### SEMAINE 2 — Dashboard financier J+0 + Vue impayés dédiée

**Missions :** P0-UNPAID-BALANCE-VIEW-1 + P0-DASHBOARD-FINANCE-J0-1

**Objectif :** (1) Widget impayés sur le Dashboard principal : nombre de patients en impayé + montant total. (2) Page ou onglet dédié "Impayés" dans AccountingPage avec liste triable patients/montant/ancienneté. (3) 3 KPIs sur le Dashboard : CA du jour, encaissements du jour, reste à encaisser.

**Impact commercial :** Le dentiste ouvre le logiciel le matin et voit immédiatement sa situation financière. C'est le moment "wow" de la démo qui fait basculer la décision.

**Complexité :** Moyenne. Requête SQL : SELECT patients.nom, SUM(actes.montant) - SUM(payments.amount) as reste_du FROM patients ... La vue est déjà calculée en analytics.py (taux de recouvrement ligne 67-78) — il faut exposer le détail par patient.

**Risque :** Faible. Données existantes. Pas de modification de schéma.

**Dépendances :** P0-PATIENT-FINANCIAL-SNAPSHOT-1 (même service)

**Critère de réussite :** Dashboard affiche "CA aujourd'hui : X MAD | Encaissé : Y MAD | Impayés : Z MAD" avec N patients en retard. Page /accounting?tab=impayes liste tous les patients avec reste_du > 0, triable par montant.

**Bilan attendu :** Le dashboard devient le cockpit financier matinal du cabinet. KPI critique visible en 5 secondes.

---

### SEMAINE 3 — Stock / Consommables MVP

**Mission :** P0-STOCK-INVENTORY-MVP-1

**Objectif :** Module stock minimal viable : liste des produits/consommables avec stock actuel, alertes seuil, entrées/sorties manuelles. Pas de déduction automatique à l'acte (V1 manuelle).

**Impact commercial :** Comble l'écart 0/10 → 5/10 face au concurrent qui le démontre. Argument de démo visible.

**Complexité :** Élevée. Seul module à créer de zéro : modèle DB (StockProduct, StockMovement), router backend (/api/stock/), page frontend StockPage. L'infrastructure ProactiveAlert pour type STOCK est déjà prête dans models.py.

**Risque :** Moyen. Nouvelle table DB (additive, jamais de DROP). Migration `create_all()` safe.

**Dépendances :** Aucune dépendance sur les missions précédentes.

**Critère de réussite :** CRUD produits fonctionnel. Alertes quand stock < seuil (ProactiveAlert type STOCK). Page /stock accessible et listant les produits. Alerte visible sur dashboard quand stock critique.

**Bilan attendu :** Digital Crown peut se présenter comme couvrant la gestion complète du cabinet, stock inclus.

---

### SEMAINE 4 — Module Lab UI + Stabilisation + Release P0

**Mission :** P0-LAB-UI-REACTIVATION-1

**Objectif :** Réactiver `LabJobsBoard` dans App.tsx (décommenter lignes 36 et 185), tester les routes backend `backend/routers/lab_jobs.py`, corriger les éventuels ajustements UI, ajouter lien dans la sidebar.

**Impact commercial :** Élimine le "module labo = ComingSoon" visible dans la démo. Backend complet, travail de 1-2 jours.

**Complexité :** Faible. Backend `lab_jobs.py` existe, `LabJobsBoard.tsx` existe. Il faut décommenter, tester, ajuster.

**Risque :** Faible. Réactivation d'une feature existante.

**Dépendances :** Aucune

**Critère de réussite :** /labo accessible, LabJobsBoard chargé sans erreur, CRUD travaux de labo fonctionnel.

**Semaine 4 également :** tests end-to-end, npm run build sans erreur, vérification API réelle (règle CLAUDE.md : "booter et taper l'API réellement avant de déclarer terminé"), préparation release.

---

## 7. ROADMAP 60 JOURS — P1

**Objectif P1 :** Passer de 8,2 à 9,0 en créant la supériorité workflow. Digital Crown dépasse le concurrent sur le pipeline commercial.

### P1-QUOTE-INVOICE-PAYMENT-PIPELINE-1
**Pipeline Acte → Plan → Devis → Facture → Paiement unifié visuellement**

Vue "workflow commercial" patient qui montre le pipeline en un coup d'oeil depuis le dossier. Le concurrent a cet avantage visuel fort. L'infrastructure existe (TreatmentPlanStep, AccountingPage, accounting_gen.py 32 Ko) — il faut l'unifier dans une vue dédiée.

Inclut : concept d'avances patients nommées (table PatientAdvance ou évolution de Payment), lien Acte → Devis en un clic depuis l'odontogramme.

**Impact :** Argument de vente majeur. "Cliquez sur l'acte, le devis se génère automatiquement. Validez, c'est une facture. Le patient paye, l'encaissement est tracé."

---

### P1-WAITING-ROOM-DASHBOARD-1
**Salle d'attente temps réel dédiée**

Widget dashboard avec patients en attente (statut EN_S_ATTENTE), temps d'attente calculé depuis l'heure d'arrivée, bouton "Appeler" (changement statut → EN_FAUTEUIL), compteur en cours. Infrastructure présente : statuts agenda complets dans models.py (48-61), ticket_number (ligne 265), frontdesk.py avec workflow complet.

**Impact :** Modernise l'accueil cabinet. Visible immédiatement dans la démo.

---

### P1-ANALYTICS-CSV-EXPORT-1
**Export CSV analytics depuis la page Analytics**

Permettre l'export des données analytiques (CA mensuel, top actes, impayés) en CSV depuis la page Analytics.tsx. `backend/routers/accounting.py` mentionne déjà un export CSV — vérifier et exposer dans l'UI.

**Impact :** Demande fréquente des cabinets pour reporting comptable / expert-comptable.

---

### P1-CABINET-REPORTING-1
**Reporting cabinet consolidé**

Rapport mensuel PDF : CA par praticien, taux de conversion devis/actes, top 10 actes, bilan impayés du mois, comparaison mois précédent. Backend : analytics.py a les données brutes.

**Impact :** Donne au propriétaire un outil de pilotage mensuel professionnel.

---

## 8. ROADMAP 90 JOURS — P2 PREMIUM

**Objectif P2 :** Passer de 9,0 à 9,4. Différenciation irréversible — aucun concurrent à court terme ne peut répliquer.

### P2 — Stock lié automatiquement aux actes
Déduction automatique consommables à l'enregistrement d'un acte (type SOIN → déduit gants, masque, composite si configuré). Extension de la mission P0-STOCK-INVENTORY-MVP-1.

### P2 — IA vigilance stock
Crown Bot alert QUERY_STOCK intent. ProactiveAlert de type STOCK déjà dans models.py (lignes 909-924). "Vous n'avez plus que 2 boîtes d'articaïne — commandez maintenant."

### P2 — Backup status visible cockpit
Widget backup sur le Dashboard : "Dernier backup : il y a 2h — OK." Rend visible la sécurité des données, argument de confiance fort.

### P2 — Analytics avancés BI
CA par praticien, par spécialité, taux de conversion devis/facture, analyse saisonnalité. Export XLSX. Multi-dentistes pour plans ELITE.

### P2 — Installation semi-automatique
Script d'installation Windows guidé (Setup.bat ou assistant PowerShell) qui installe PostgreSQL, configure la DB, crée le superadmin, lance les tests de santé. Réduit de 2h à 20 minutes le temps d'installation cabinet.

### P2 — Crown Bot étendu
Nouveaux intents : QUERY_STOCK, QUERY_PAYMENTS_LATE, CREATE_LAB_JOB. Génération PDF directe depuis le bot ("Crown, génère une ordonnance pour Dupont").

---

## 9. MISSIONS EXÉCUTABLES — FICHES COURTES

---

## MISSION : P0-PATIENT-FINANCIAL-SNAPSHOT-1
**Objectif :** Ajouter un onglet "Finances" dans le dossier patient (PatientDetails.tsx) affichant total facturé, encaissé, reste dû, plan de paiement actif, historique paiements.
**Impact commercial :** Chaque dossier patient devient un outil de gestion financière quotidienne. Argument immédiat en démo.
**Fichiers probables :**
- `frontend/src/features/patients/PatientDetails.tsx` (ajout onglet Finances)
- `frontend/src/features/patients/components/QuickPayModal.tsx` (réutiliser)
- `backend/services/accounting_service.py` (solde patient — probablement déjà présent)
- `backend/routers/accounting.py` (nouveau endpoint GET /patients/{id}/financial-summary)
**Interdictions :** Aucune modification de schéma DB. Aucun DROP. Lecture seule principalement.
**Tests attendus :** GET /api/patients/{id}/financial-summary → {total_facture, total_encaisse, reste_du}. Onglet visible et correct pour patient avec et sans actes.
**Bilan attendu :** La fiche patient montre la situation financière complète, pas juste les données cliniques.

---

## MISSION : P0-UNPAID-BALANCE-VIEW-1
**Objectif :** Ajouter une vue/onglet "Impayés" dans AccountingPage.tsx listant tous les patients avec reste dû > 0, triable par montant et ancienneté, avec action de relance rapide.
**Impact commercial :** Le cabinet voit en un coup d'oeil qui lui doit de l'argent. Rétention quotidienne garantie.
**Fichiers probables :**
- `frontend/src/pages/AccountingPage.tsx` (ajout onglet Impayés)
- `backend/routers/accounting.py` (nouveau endpoint GET /accounting/unpaid avec liste patients+montants)
- `backend/services/accounting_service.py` (requête SQL patients → reste_du)
**Interdictions :** Aucune modification de schéma DB. Aucun accès cross-tenant.
**Tests attendus :** GET /api/accounting/unpaid → liste [{patient_id, nom, reste_du, dernier_acte}]. Affichage correct. Isolation tenant vérifiée (employer_id sur la requête).
**Bilan attendu :** Vue impayés dédiée fonctionnelle. Le dentiste consulte ses créances en 2 clics.

---

## MISSION : P0-DASHBOARD-FINANCE-J0-1
**Objectif :** Enrichir le Dashboard principal avec 3 KPIs financiers temps réel : CA facturable du jour, encaissements du jour, total impayés cabinet. Plus un widget "Salle d'attente" avec compteur patients EN_S_ATTENTE.
**Impact commercial :** Premier écran = cockpit de pilotage. Différence de perception immédiate en démo.
**Fichiers probables :**
- `frontend/src/pages/Dashboard.tsx` (lignes 60-98, ajouter widgets)
- `backend/routers/stats.py` ou `backend/routers/analytics.py` (endpoints J+0)
- `backend/routers/appointments.py` (count EN_S_ATTENTE du jour)
**Interdictions :** Aucune modification de schéma. Ne pas casser les widgets existants.
**Tests attendus :** GET /api/stats/today → {ca_facturable, encaissements, impayes_total, patients_en_attente}. Valeurs cohérentes avec les données réelles.
**Bilan attendu :** Dashboard transformé en cockpit financier matinal. Argument de démo clé.

---

## MISSION : P0-TREATMENT-PLAN-UX-1
**Objectif :** Ajouter dans le dossier patient une vue dédiée "Plan de traitement" avec timeline visuelle des étapes (TreatmentPlanStep) — statut pending/done/postponed avec indicateurs visuels clairs, et lien direct vers la génération du devis associé.
**Impact commercial :** Suivi de traitement visible = argument de soin structuré pour le patient ET outil de planification pour le dentiste.
**Fichiers probables :**
- `frontend/src/features/admin/DocumentStudio/TreatmentPlanStudio.tsx` (source)
- `frontend/src/features/patients/PatientDetails.tsx` (intégration onglet)
- `backend/models.py` (TreatmentMasterPlan lignes 298-320, TreatmentPlanStep)
- `backend/routers/prescriptions.py` (router actes — vérifier endpoints plan)
**Interdictions :** Pas de DROP/TRUNCATE. Pas de changement des champs existants TreatmentPlanStep.
**Tests attendus :** Onglet "Plan" visible dans dossier patient. TreatmentPlanStep affichés avec statut coloré. Clic sur étape → AccountingStudio avec acte pré-rempli.
**Bilan attendu :** Le plan de traitement est visible et utilisable sans chercher dans plusieurs pages.

---

## MISSION : P0-STOCK-INVENTORY-MVP-1
**Objectif :** Créer le module stock minimal : CRUD produits/consommables, suivi quantité, alertes seuil, historique mouvements. Pas de déduction automatique à l'acte (V2).
**Impact commercial :** Comble l'écart 0/10 vs 7/10 concurrent. Argument de démo visible et demandé.
**Fichiers probables :**
- `backend/models.py` (ajouter StockProduct, StockMovement — tables additives)
- `backend/routers/stock.py` (à créer — CRUD + GET /stock/alerts)
- `backend/main.py` (ajouter include_router stock_router)
- `frontend/src/pages/StockPage.tsx` (à créer)
- `frontend/src/App.tsx` (ajouter route /stock)
- `frontend/src/components/Sidebar.tsx` (ajouter lien Stock)
**Interdictions :** Uniquement tables additives. Aucun DROP. Aucun ALTER de colonnes existantes. ProactiveAlert type STOCK déjà dans models.py — utiliser l'existant.
**Tests attendus :** POST /api/stock/products crée un produit. GET /api/stock/products liste les produits du cabinet (employer_id vérifié). Alert ProactiveAlert déclenché si quantite < seuil_alerte.
**Bilan attendu :** Module stock fonctionnel et déployable. Alerte stock visible sur dashboard.

---

## MISSION : P0-LAB-UI-REACTIVATION-1
**Objectif :** Réactiver le module laboratoire dans l'UI en décommentant `LabJobsBoard` dans App.tsx, tester les routes backend existantes, ajouter le lien dans la sidebar.
**Impact commercial :** Élimine le "ComingSoon" visible en démo. Backend complet, effort minimal.
**Fichiers probables :**
- `frontend/src/App.tsx` (décommenter lignes 36 et 185)
- `frontend/src/components/LabJobsBoard.tsx` (tester et ajuster si nécessaire)
- `frontend/src/components/Sidebar.tsx` (activer lien /labo)
- `backend/routers/lab_jobs.py` (vérifier routes GET/POST/PUT)
**Interdictions :** Ne pas créer de nouveaux modèles DB. Le backend existe — ne pas modifier les routes existantes sans nécessité.
**Tests attendus :** /labo charge LabJobsBoard sans crash. CRUD travaux de labo fonctionnel depuis l'UI. Sidebar affiche "Laboratoire" (pas "ComingSoon").
**Bilan attendu :** Module labo visible et fonctionnel en 1-2 jours. Score labo : 2/10 → 6,5/10.

---

## MISSION : P1-QUOTE-INVOICE-PAYMENT-PIPELINE-1
**Objectif :** Créer une vue "workflow commercial patient" unifié : depuis l'odontogramme, clic sur acte → génère devis pré-rempli → validation → facture → paiement tracé en un flux continu.
**Impact commercial :** Le concurrent a cet avantage visuel. Digital Crown dépasse en le rendant plus fluide et ancré dans le dossier patient.
**Fichiers probables :**
- `frontend/src/features/admin/AccountingStudio.tsx` (source devis/honoraires)
- `frontend/src/components/odontogram/Odontogram.tsx` (point d'entrée acte)
- `frontend/src/features/patients/PatientDetails.tsx` (intégration pipeline)
- `backend/services/generators/accounting_gen.py` (32 Ko — générateur devis/honoraires)
- `backend/routers/accounting.py` (endpoints existants)
**Interdictions :** Pas de modification de schéma DB. Le flux doit rester rollbackable.
**Tests attendus :** Depuis dossier patient → acte → devis généré en PDF → statut "devis envoyé" → paiement enregistré → solde mis à jour.
**Bilan attendu :** Workflow financier visuellement unifié. Argument vendeur décisif.

---

## MISSION : P1-WAITING-ROOM-DASHBOARD-1
**Objectif :** Widget "Salle d'attente" dédié sur le Dashboard : patients EN_S_ATTENTE avec temps d'attente, bouton Appeler (→ EN_FAUTEUIL), bouton Absent (→ ABSENT), mise à jour temps réel (polling 30s).
**Impact commercial :** Modernise l'accueil. Visible immédiatement en démo. Utile quotidiennement à la secrétaire.
**Fichiers probables :**
- `frontend/src/pages/Dashboard.tsx` (ajouter WaitingRoomWidget)
- `backend/routers/appointments.py` (GET /appointments/waiting-room — statut EN_S_ATTENTE du jour)
- `backend/routers/frontdesk.py` (PATCH statut RDV)
**Interdictions :** Aucune modification de schéma. ticket_number existe déjà.
**Tests attendus :** GET /api/appointments/waiting-room → liste patients EN_S_ATTENTE avec ticket_number et heure_arrivee. PATCH statut → mise à jour correcte.
**Bilan attendu :** Dashboard = cockpit accueil + finance. Double utilité quotidienne.

---

## MISSION : P1-ANALYTICS-CSV-EXPORT-1
**Objectif :** Ajouter bouton "Exporter CSV" sur la page Analytics.tsx pour exporter CA mensuel, top actes, impayés. Vérifier et exposer l'export déjà présent dans accounting.py.
**Impact commercial :** Demande fréquente des cabinets pour reporting expert-comptable.
**Fichiers probables :**
- `frontend/src/pages/Analytics.tsx` (ajouter bouton export)
- `backend/routers/accounting.py` (vérifier endpoint export CSV existant)
- `backend/routers/analytics.py` (endpoint analytics + export)
**Interdictions :** Aucune modification de schéma.
**Tests attendus :** GET /api/accounting/export?format=csv télécharge un fichier CSV valide avec les bonnes colonnes.
**Bilan attendu :** Export comptable direct depuis l'UI. Suppression du besoin d'accès DB pour les rapports.

---

## MISSION : P1-CABINET-REPORTING-1
**Objectif :** Rapport mensuel PDF cabinet automatique : CA, taux de recouvrement, top actes, bilan impayés, comparaison mois M-1.
**Impact commercial :** Outil de pilotage mensuel professionnel. Différencie le logiciel d'un simple "carnet de rendez-vous numérique."
**Fichiers probables :**
- `backend/services/generators/report_gen.py` (générateur rapport générique existant — à étendre)
- `backend/routers/analytics.py` (données source)
- `frontend/src/pages/Analytics.tsx` (bouton "Générer rapport mensuel")
**Interdictions :** Aucune modification de schéma. Rapport PDF = lecture seule.
**Tests attendus :** POST /api/analytics/report?month=2026-07 génère un PDF cohérent avec les données de la période.
**Bilan attendu :** Le cabinet dispose d'un rapport mensuel PDF professionnel en 1 clic.

---

## 10. POSITIONNEMENT CONCURRENTIEL — COMMENT ÉCRASER LE CONCURRENT

### Axe 1 : "Votre argent, visible immédiatement"
Le concurrent montre le stock en démo. Digital Crown V2 montre **l'argent** — "ouvrez le logiciel le matin et vous voyez en 5 secondes : vous avez fait 4 200 MAD aujourd'hui, 3 patients vous doivent encore 8 700 MAD, et Madame Benali est en salle d'attente depuis 12 minutes."

Aucun concurrent local ne le fait aussi proprement avec une sécurité données aussi solide.

### Axe 2 : "L'IA que les autres ne peuvent pas avoir"
L'IA de Digital Crown est **locale, certifiable, sans cloud** :
- YOLO11x panoramique : détection 4 classes, performances mesurables
- Céphalométrie automatique : mesures SNA/SNB/ANB en 2 clics, pas de cloud
- Crown Bot : parle à votre logiciel en arabe ou en français, données jamais envoyées en dehors du cabinet

Message : "Nos concurrents utilisent ChatGPT pour vos données patients. Nous, l'IA tourne dans votre cabinet, sur votre machine, sans internet."

### Axe 3 : "La seule solution que vous possédez vraiment"
Digital Crown est **votre logiciel, pas votre abonnement** :
- Données sur votre machine, pas dans notre cloud
- Backup chiffré que vous contrôlez
- Licence Firebase hors-ligne : si nous disparaissons demain, vous continuez à travailler
- PostgreSQL standard : vous pouvez migrer, auditer, exporter

Message : "Avec nos concurrents SaaS, si vous arrêtez l'abonnement, vous perdez l'accès à vos patients. Avec Digital Crown, vos données vous appartiennent."

---

## 11. CONTRAINTES PRODUCTION LOCALE ACTIVE

Digital Crown est **déjà utilisé quotidiennement en cabinet réel** avec 197+ patients, une DB PostgreSQL active (`digitalcrown_db`, localhost), et un superadmin réel (`benmoussa.achraf@gmail.com`).

Toute mission future DOIT respecter :

### Contraintes DB
- Préserver `digitalcrown_db` et tous ses patients/documents/médias
- Uniquement des opérations **additives** (CREATE TABLE, ADD COLUMN, INSERT) — jamais de DROP, TRUNCATE, ALTER de colonnes existantes sans migration additive validée
- Compter les patients/documents avant et après chaque migration (`preflight_data_audit.py`)
- La migration est faite par `create_all()` + fonctions additives dans le lifespan de `main.py` — Alembic n'est **jamais** invoqué automatiquement

### Contraintes médias
- Préserver tous les médias dans `%APPDATA%/DigitalCrown/media/`
- Jamais de route `/api/static/uploads` accessible sans authentification
- `_assert_media_tenant()` obligatoire sur toutes les nouvelles routes de médias

### Contraintes superadmin
- Préserver le compte `benmoussa.achraf@gmail.com` (superadmin réel global)
- Jamais créer un second SUPERADMIN via les missions

### Contraintes développement
- Chaque mission doit être petite, testable, rollbackable
- Après toute modification de `backend/routers/*.py` ou de générateurs PDF : **booter et taper l'API réellement** avant de déclarer terminé (règle CLAUDE.md — plusieurs bugs bloquants passaient les tests unitaires mais crashaient en vrai)
- Tests backend (`pytest backend/tests/`) : 2200+ tests, 9-15 minutes — lancer en background
- Frontend : `npm test` et `npm run build` depuis la racine avant chaque release

### Contraintes environnement
- `ENVIRONMENT=development` sur le poste de développement — ne jamais changer en production/cabinet sans checklist complète
- `load_backend_env()` avec `override=False` en premier dans `main.py` — ne jamais écraser les vars déjà injectées par l'OS
- Médias rehearsal : toujours pointer `MEDIA_ROOT` vers `install_rehearsal_media/`, jamais vers `%APPDATA%/DigitalCrown/media/`

---

## BILAN FINAL

```
ROADMAP-DIGITAL-CROWN-V2-STRATEGIC-LOCK — BILAN FINAL

1.  Statut : COMPLETED
2.  Fichier roadmap créé : oui — docs/ROADMAP_DIGITAL_CROWN_V2.md
3.  Score actuel retenu : 7,0 / 10 (recalcul strict — module labo UI off, workflow financier fragmenté)
4.  Score après P0 : 8,2 / 10
5.  Score après P1 : 9,0 / 10
6.  Score après P2 : 9,4 / 10
7.  P0 finalisés :
    - P0-PATIENT-FINANCIAL-SNAPSHOT-1 (semaine 1)
    - P0-UNPAID-BALANCE-VIEW-1 (semaine 2)
    - P0-DASHBOARD-FINANCE-J0-1 (semaine 2)
    - P0-TREATMENT-PLAN-UX-1 (semaine 1-2, optionnel P0)
    - P0-STOCK-INVENTORY-MVP-1 (semaine 3)
    - P0-LAB-UI-REACTIVATION-1 (semaine 4)
8.  P1 finalisés :
    - P1-QUOTE-INVOICE-PAYMENT-PIPELINE-1
    - P1-WAITING-ROOM-DASHBOARD-1
    - P1-ANALYTICS-CSV-EXPORT-1
    - P1-CABINET-REPORTING-1
9.  P2 finalisés :
    - P2 : Stock lié automatiquement aux actes
    - P2 : IA vigilance stock (Crown Bot intent QUERY_STOCK)
    - P2 : Backup status visible cockpit dashboard
    - P2 : Analytics avancés BI + export XLSX
    - P2 : Installation semi-automatique Windows
    - P2 : Crown Bot intents étendus
10. Ordre recommandé des missions :
    S1: P0-PATIENT-FINANCIAL-SNAPSHOT-1
    S1-S2: P0-DASHBOARD-FINANCE-J0-1
    S2: P0-UNPAID-BALANCE-VIEW-1
    S2: P0-TREATMENT-PLAN-UX-1 (parallèle)
    S3: P0-STOCK-INVENTORY-MVP-1
    S4: P0-LAB-UI-REACTIVATION-1 + stabilisation release
    J31-45: P1-QUOTE-INVOICE-PAYMENT-PIPELINE-1
    J31-45: P1-WAITING-ROOM-DASHBOARD-1
    J46-60: P1-ANALYTICS-CSV-EXPORT-1 + P1-CABINET-REPORTING-1
    J61-90: P2 dans l'ordre stock auto → Crown Bot → BI → install
11. Décision stock vs finance d'abord : FINANCE D'ABORD
    Justification : Les impayés sont consultés chaque jour (rétention quotidienne), l'infrastructure est
    70% prête (AccountingPage 72 Ko, Payment/InstallmentPlan en DB, analytics.py), et l'effort est
    3-5 jours vs 8 jours pour le stock from scratch. Le stock reste P0 mais semaine 3.
12. Missions prêtes à lancer immédiatement :
    - P0-PATIENT-FINANCIAL-SNAPSHOT-1 (infrastructure existante, faible risque)
    - P0-DASHBOARD-FINANCE-J0-1 (données existantes, widgets à ajouter)
    - P0-LAB-UI-REACTIVATION-1 (décommenter 2 lignes App.tsx + tester)
13. Fichiers modifiés : docs/ROADMAP_DIGITAL_CROWN_V2.md (créé)
14. Code applicatif modifié : NON — mission stratégique READ-ONLY
15. npm test : en cours (background)
16. npm run build : non lancé
17. Vraie DB intacte : oui
18. Superadmin réel intact : oui
19. Risques restants :
    - P0-STOCK-INVENTORY-MVP-1 : nouvelle migration DB — appliquer CREATE TABLE uniquement,
      vérifier avec preflight_data_audit.py que count patients/documents identique après
    - P0-LAB-UI-REACTIVATION-1 : LabJobsBoard.tsx peut avoir des dépendances cassées après
      mise à jour React/TypeScript — tester npm run build avant déploiement
    - P1-QUOTE-INVOICE-PAYMENT-PIPELINE-1 : refonte UX majeure — risque de régression dans
      AccountingStudio si non isolée correctement
20. Verdict : ROADMAP V2 VERROUILLÉE
```

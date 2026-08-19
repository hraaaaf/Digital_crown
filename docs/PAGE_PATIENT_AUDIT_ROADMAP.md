# Page Patient — Audit & Refonte Premium

Statut canonique du chantier Page Patient. Ce document sert de boussole : aucun lot n'est considéré terminé sans preuve explicite.

## Goal global

Transformer la Page Patient en workspace clinique simple, traçable, sûr et cohérent, sans perdre les fonctions déjà utiles.

## Succès global

- Une seule vérité par donnée clinique, administrative et financière.
- Isolation stricte entre cabinets et entre patients.
- Aucune donnée patient, clinique ou financière inventée silencieusement.
- Les décisions cliniques automatiques sont bornées, explicables, sourcées et soumises à validation praticien.
- Architecture lisible en 5 espaces : Vue d’ensemble, Clinique, Imagerie, Documents, Finances.
- Les flux legacy sont supprimés après migration vers le flux canonique.
- Baseline visuelle, mockup cible et captures après implémentation sur les mêmes viewports pour chaque changement UI.
- Régression fonctionnelle, permissions, sécurité, isolation Patient A→B, documents A5/A4 et règles cliniques certifiées avant clôture.

## Preuves globales requises

- Tests backend/frontend ciblés puis régression raisonnable.
- Tests d'isolation tenant et patient.
- Tests de vérité financière et clinique.
- Sources scientifiques primaires pour toute règle thérapeutique automatisée.
- Captures baseline/mockup/après pour tout changement UI.
- CI exacte sur HEAD final du lot.

---

# P0 — Vérité & sécurité

**Goal :** supprimer les états faux, les fuites de données et les doubles vérités avant toute refonte visuelle.

## P0-A — Isolation anti-doublon Patient
- [x] Scoper `nom + prénom + date_naissance` par `employer_id`.
- [x] Garantir qu'aucune pré-détection ne renvoie l'identité d'un autre cabinet.
- [x] Couvrir création, modification, import CSV et endpoint de précheck.
- [x] Test croisé tenant A/B.

**Succès :** un patient identique dans deux cabinets est autorisé et invisible hors tenant.

## P0-B — Sexe et données d'identité sans défaut inventé
- [x] Supprimer les fallbacks silencieux `M`/`F` côté schémas/import.
- [x] Refuser ou signaler explicitement les valeurs invalides.
- [x] Ne toucher au formulaire visuel qu'après baseline UI.

**Succès :** aucune voie de création/import ne déduit le sexe sans entrée valide.

## P0-C — Vérité clinique / ClinicalHub
- [x] Supprimer les plans ou diagnostics fictifs initialisés côté frontend.
- [x] Le backend devient la seule source autoritative du Master Plan.
- [x] `localStorage` ne peut jamais être présenté comme donnée clinique sauvegardée.
- [x] Aucun toast de succès/synchronisation avant succès backend prouvé.
- [x] Audit spécifique odontogramme et diagnostic local.

**Succès :** un dossier clinique vide reste réellement vide ; une erreur de persistance reste visible comme erreur.

## P0-D — Assistants cliniques fail-closed
- [x] Reclasser les assistants comme outils de collecte/proposition, pas moteurs de diagnostic autonome.
- [x] Interdire toute prescription/antibiothérapie/sédation/imagerie/acte catégorique non validée.
- [x] Supprimer l'ordre scientifique universel codé en dur.
- [x] Construire une matrice de règles scientifiques avec source primaire, indication, contre-indication, version et besoin de validation praticien.
- [x] Revoir Général, Examen complet, Paro, Endo, Chirurgie, Prothèse, Pédodontie, Ortho, ATM, Pathologie.

**Succès :** aucune proposition clinique ne devient vérité dossier ou traitement sans validation explicite du praticien.

## P0-E — Paiements et échéanciers
- [x] Aucun mode de paiement par défaut implicite.
- [x] Vérifier que `acte_id` appartient au même patient avant mutation.
- [x] Vérifier que `installment_id` appartient au même patient avant mutation.
- [x] Migrer la Page Patient depuis `/accounting/plans` vers le flux `/installments` réconcilié.
- [x] Déprécier puis supprimer le flux legacy après migration.
- [x] Reste dû / taux de recouvrement : jamais 100 % lorsque la base de facturation est absente.

**Succès :** toute entrée financière est reliée à la bonne entité et aucune méthode/solde n'est inventé.

## P0-F — RVG et médias patients
- [x] Supprimer l'authentification par token en query string côté RVG.
- [x] Utiliser un fetch authentifié/blob ou le mécanisme média authentifié canonique.
- [x] Vérifier symétrie upload/list/open/download/delete et permissions.
- [x] Préférer corbeille/restore à suppression permanente dans la surface clinique.

**Succès :** aucun secret dans l'URL et aucune action média hors permission/patient.

## P0-G — Sources médicales structurées
- [x] Résoudre le doublon `Patient.antecedents_medicaux` / `DossierClinique.antecedents_medicaux`.
- [x] Définir une source canonique.
- [x] Préparer le modèle structuré de sécurité médicale sans inventer les champs avant l'audit clinique dédié.

**Succès :** une seule source de vérité médicale critique.

## P0-H — Neutralité clinique
- [x] Retirer `PatientScoreBadge` de la surface clinique.
- [x] Séparer indicateurs factuels administratifs (absences, solde) de toute hiérarchie VIP/Gold/Silver/Bronze.

**Succès :** aucune classification commerciale/solvabilité n'influence visuellement la lecture clinique.

## P0-I — NBA / radar / panoramique : frontière de vérité
- [x] Supprimer les conclusions cliniques automatiques issues d'heuristiques temporelles ou commerciales.
- [x] Supprimer les grades Premium/PLATINUM de la logique clinique Patient.
- [x] Ne plus transformer la durée orthodontique en progression clinique ou date de fin estimée.
- [x] Présenter les détections panoramiques au maximum comme repères techniques à valider par le praticien.
- [x] Désactiver l'inférence panoramique legacy vers facturation / plan de traitement.
- [x] Borner le contexte RAG panoramique à des repères FDI neutres, sans labels pathologiques.

**Succès :** aucune heuristique commerciale, temporelle ou détection panoramique ne devient diagnostic, risque retenu, traitement ou vérité clinique automatique.

### Preuves P0 consolidées

- P0-C : `docs/PATIENT_P0_CLINICALHUB_CERT.json`.
- P0-D : AFTER 20 captures, run `32187055163`, proposition-only/fail-closed.
- P0-E UI : AFTER 8 captures, vérité KPI + échéancier responsive.
- P0-F : `docs/PATIENT_P0F_RVG_CERT.json`.
- P0-G : `docs/PATIENT_P0G_MEDICAL_SOURCE_CERT.json`.
- P0-H : `docs/PATIENT_P0H_NEUTRALITY_CERT.json`.
- P0-I : AFTER run `32186499282`, artifact `9342853792`, 4 captures, 0 runtime/5xx, score de scope 9,7/10.
- Code candidate `653b19b926019653ea8c1f6ad4c21f17005aeb5e` : CI `32195798290` (#1095) SUCCESS + T2 `32195798150` (#356) SUCCESS.
- Tout commit documentaire de closeout postérieur doit lui-même repasser CI/T2 exact-HEAD avant déclaration CLOSED.

---

# P1 — Architecture générale Page Patient

**Goal :** réduire la densité et faire apparaître immédiatement la prochaine action utile.

Avant toute implémentation UI :
- [x] captures baseline des viewports concernés ;
- [x] Goal visuel écrit ;
- [x] mockup/wireframe basé sur l'application existante ;
- [x] comparaison avant/mockup/après.

Architecture cible :
1. Vue d’ensemble
2. Clinique
3. Imagerie
4. Documents
5. Finances

Actions :
- [x] Header compact : identité, âge/date naissance, dossier, assurance, alertes critiques.
- [x] Actions rapides : RDV, séance/examen, document, encaissement.
- [x] Fusionner Archives dans Documents.
- [x] Renommer `Documents A5` en `Documents`.
- [x] Renommer `Radiologie (IA)` en `Imagerie`.
- [x] Éviter les labels techniques internes dans la navigation utilisateur.

**Statut : CERTIFIED.**

### Preuves P1

- Goal + wireframe : `docs/PATIENT_P1_ARCHITECTURE_GOAL.md`.
- Certificat : `docs/PATIENT_P1_ARCHITECTURE_CERT.json`.
- Product HEAD certifié : `67e979b3df2058bf7079f36c84abd67a3f0e2e0c`.
- Visual AFTER : run `32201889501` (#6) SUCCESS, artifact `9347877116`, digest `sha256:0e1c42bc50b64c12b9f13da25483dbbe52cc963cdcfed62dd9afd064c5b3b8e4`.
- 4 captures : 390x844, 430x932, 768x1024, 1280x900 ; zéro overflow horizontal global, zéro runtime error, zéro HTTP 5xx.
- CI : run `32201889504` (#1141) SUCCESS.
- T2 Runtime Browser Certification : run `32201889557` (#396) SUCCESS.
- Score visuel de scope P1 : **9,7/10**.
- Le commit documentaire de closeout postérieur au product HEAD doit lui-même repasser CI/T2 exact-HEAD avant déclaration CLOSED.

---

# P2 — Vue d’ensemble / Patient Journey

**Goal :** faire de `PatientJourney` la colonne vertébrale du dossier sans dupliquer les sources.

- [ ] Résumé clinique traçable avec source/date.
- [ ] Prochaine action.
- [ ] Plan actif.
- [ ] Prochain RDV.
- [ ] Situation financière résumée sans faux zéro.
- [ ] Timeline avec navigation vers la source réelle.
- [ ] Revoir le routage Treatment Plan actuellement détourné vers Documents.
- [ ] Supprimer les messages d'"intelligence" opaques ou non traçables.

---

# P3 — Clinique

**Goal :** regrouper l'état clinique autour de données validées et structurées.

- [ ] Profil médical / alertes structurées.
- [ ] Odontogramme canonique et persistant.
- [ ] Examen général.
- [ ] Examens spécialisés.
- [ ] Hypothèses vs diagnostic retenu clairement distingués.
- [ ] Master Plan versionné/traçable.
- [ ] Déplacer le Compagnon Diagnostique depuis Documents vers Clinique si confirmé pertinent.
- [ ] Certification scientifique composant par composant.

---

# P4 — Imagerie

**Goal :** un espace unique RVG + Panoramique + Céphalométrie.

- [ ] RVG intégré à la navigation Imagerie.
- [ ] Panoramique et Céphalo conservés avec leurs propres gates scientifiques.
- [ ] Permissions cohérentes par type d'imagerie.
- [ ] Historique, acquisition, rapport, suppression/restauration cohérents.
- [ ] Aucun libellé IA si la fonction réelle est déterministe ou si la provenance n'est pas explicitée.

---

# P5 — Documents

**Goal :** conserver le Document Studio durci et simplifier son entrée depuis le patient.

- [ ] Créer / Historique dans le même espace.
- [ ] Archives fusionnées.
- [ ] Ordonnance, certificat, devis, honoraires, échéancier, libre conservés selon contrats certifiés.
- [ ] Poursuivre les certifications propres au Document Studio sans dupliquer les travaux déjà validés.
- [ ] Vérifier A5/A4, impression, preview, archivage, permissions et isolation Patient A→B.

---

# P6 — Finances & identité Patient

**Goal :** rendre création/édition/finance plus courte et sans ambiguïté.

- [x] Unifier Add/Edit Patient autour d'un même contrat de formulaire.
- [x] Corriger anti-doublon fail-open côté UI.
- [x] Réduire la saisie initiale au nécessaire puis enrichir dans le dossier.
- [x] Simplifier KPI patient : Facturé / Encaissé / Reste dû / Prochaine échéance.
- [x] Reléguer ou supprimer le taux de recouvrement côté fiche patient.
- [x] Harmoniser encaissement rapide, acte et échéancier avec le contrat financier canonique.

**Statut produit : CERTIFIED sur `fb2bd0357d6da6d4c3be9b51be45d84c764589c1`.**

### Preuves P6

- Goal + wireframe : `docs/PATIENT_P6_FINANCES_IDENTITE_GOAL.md`.
- Certificat : `docs/PATIENT_P6_FINANCES_IDENTITE_CERT.json`.
- P5 courant `76fe188a7a9606e2ed93dd6d347753a2dbab3c14` → P6 : `behind=0`, `ahead=50`, merge-base=P5.
- CI : run `32309262380` (#1447) SUCCESS.
- T2 Runtime Browser Certification : run `32309262379` (#689) SUCCESS.
- BEFORE : run `32309262409` (#44) SUCCESS, artifact `9385927643`.
- AFTER : run `32309262388` (#31) SUCCESS, artifact `9385921989`, digest `sha256:a451b7d29b62f85598a9d2d9d6279ac2a5dcc5d58a86c26c20c5d1d2faf4e9a1`.
- AFTER : 12/12 captures valides sur 390x844, 430x932, 768x1024 et 1280x900 ; zéro overflow horizontal, zéro runtime error, zéro HTTP 5xx.
- Score visuel de scope P6 : **9,6/10**.
- Le commit documentaire de closeout contenant ces preuves doit lui-même repasser CI/T2 exact-HEAD avant déclaration CLOSED.

---

# P7 — Certification finale Page Patient

**Goal :** fermer la Page Patient uniquement après preuve fonctionnelle, visuelle, clinique et sécurité.

- [ ] Tests backend ciblés + régression Patient.
- [ ] Tests frontend ciblés + build/typecheck.
- [ ] Isolation tenant A/B.
- [ ] Isolation Patient A→B et reset des drafts.
- [ ] RBAC par surface : patient, clinique, documents, accounting, prescriptions, imagerie.
- [ ] Parcours création → consultation → acte → document → paiement → archive.
- [ ] 390 / 430 / 768 / desktop selon surfaces réellement supportées.
- [ ] Clavier, focus, modales, responsive, erreurs réseau.
- [ ] Captures avant/mockup/après mêmes viewports.
- [ ] Score visuel final argumenté.
- [ ] CI exacte sur HEAD final.
- [ ] Mise à jour ROADMAP/STATUS/SESSION/CHANGELOG selon pertinence.

---

## Architecture cible de référence

```text
PATIENT
├── Header compact
│   ├── Identité / âge / dossier
│   ├── Assurance
│   └── Alertes médicales critiques
├── Actions rapides
│   ├── RDV
│   ├── Séance / examen
│   ├── Document
│   └── Encaisser
├── Vue d’ensemble
│   ├── Résumé clinique traçable
│   ├── Prochaine action
│   ├── Plan actif
│   └── Patient Journey
├── Clinique
│   ├── Sécurité médicale
│   ├── Odontogramme
│   ├── Examens
│   ├── Diagnostics validés
│   └── Plan de traitement
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
    └── Échéances
```

## Règles de chantier

- Pas de rebuild gratuit : préserver les composants utiles et durcis.
- Pas de nouvelle abstraction sans nécessité démontrée.
- Pas de vérité clinique/financière dans `localStorage`.
- Pas de succès UI avant succès backend réel.
- Pas de donnée médicale ou financière implicite.
- Pas de changement UI sans baseline + mockup.
- Pas de déploiement Vercel sans autorisation explicite.
- Un lot n'est CLOSED qu'avec preuves sur son HEAD exact.
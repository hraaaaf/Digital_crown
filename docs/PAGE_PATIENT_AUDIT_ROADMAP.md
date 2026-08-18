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
- [ ] Scoper `nom + prénom + date_naissance` par `employer_id`.
- [ ] Garantir qu'aucune pré-détection ne renvoie l'identité d'un autre cabinet.
- [ ] Couvrir création, modification, import CSV et endpoint de précheck.
- [ ] Test croisé tenant A/B.

**Succès :** un patient identique dans deux cabinets est autorisé et invisible hors tenant.

## P0-B — Sexe et données d'identité sans défaut inventé
- [ ] Supprimer les fallbacks silencieux `M`/`F` côté schémas/import.
- [ ] Refuser ou signaler explicitement les valeurs invalides.
- [ ] Ne toucher au formulaire visuel qu'après baseline UI.

**Succès :** aucune voie de création/import ne déduit le sexe sans entrée valide.

## P0-C — Vérité clinique / ClinicalHub
- [ ] Supprimer les plans ou diagnostics fictifs initialisés côté frontend.
- [ ] Le backend devient la seule source autoritative du Master Plan.
- [ ] `localStorage` ne peut jamais être présenté comme donnée clinique sauvegardée.
- [ ] Aucun toast de succès/synchronisation avant succès backend prouvé.
- [ ] Audit spécifique odontogramme et diagnostic local.

**Succès :** un dossier clinique vide reste réellement vide ; une erreur de persistance reste visible comme erreur.

## P0-D — Assistants cliniques fail-closed
- [ ] Reclasser les assistants comme outils de collecte/proposition, pas moteurs de diagnostic autonome.
- [ ] Interdire toute prescription/antibiothérapie/sédation/imagerie/acte catégorique non validée.
- [ ] Supprimer l'ordre scientifique universel codé en dur.
- [ ] Construire une matrice de règles scientifiques avec source primaire, indication, contre-indication, version et besoin de validation praticien.
- [ ] Revoir Général, Examen complet, Paro, Endo, Chirurgie, Prothèse, Pédodontie, Ortho, ATM, Pathologie.

**Succès :** aucune proposition clinique ne devient vérité dossier ou traitement sans validation explicite du praticien.

## P0-E — Paiements et échéanciers
- [ ] Aucun mode de paiement par défaut implicite.
- [ ] Vérifier que `acte_id` appartient au même patient avant mutation.
- [ ] Vérifier que `installment_id` appartient au même patient avant mutation.
- [ ] Migrer la Page Patient depuis `/accounting/plans` vers le flux `/installments` réconcilié.
- [ ] Déprécier puis supprimer le flux legacy après migration.
- [ ] Reste dû / taux de recouvrement : jamais 100 % lorsque la base de facturation est absente.

**Succès :** toute entrée financière est reliée à la bonne entité et aucune méthode/solde n'est inventé.

## P0-F — RVG et médias patients
- [ ] Supprimer l'authentification par token en query string côté RVG.
- [ ] Utiliser un fetch authentifié/blob ou le mécanisme média authentifié canonique.
- [ ] Vérifier symétrie upload/list/open/download/delete et permissions.
- [ ] Préférer corbeille/restore à suppression permanente dans la surface clinique.

**Succès :** aucun secret dans l'URL et aucune action média hors permission/patient.

## P0-G — Sources médicales structurées
- [ ] Résoudre le doublon `Patient.antecedents_medicaux` / `DossierClinique.antecedents_medicaux`.
- [ ] Définir une source canonique.
- [ ] Préparer le modèle structuré de sécurité médicale sans inventer les champs avant l'audit clinique dédié.

**Succès :** une seule source de vérité médicale critique.

## P0-H — Neutralité clinique
- [ ] Retirer `PatientScoreBadge` de la surface clinique.
- [ ] Séparer indicateurs factuels administratifs (absences, solde) de toute hiérarchie VIP/Gold/Silver/Bronze.

**Succès :** aucune classification commerciale/solvabilité n'influence visuellement la lecture clinique.

---

# P1 — Architecture générale Page Patient

**Goal :** réduire la densité et faire apparaître immédiatement la prochaine action utile.

Avant toute implémentation UI :
- [ ] captures baseline des viewports concernés ;
- [ ] Goal visuel écrit ;
- [ ] mockup/wireframe basé sur l'application existante ;
- [ ] comparaison avant/mockup/après.

Architecture cible :
1. Vue d’ensemble
2. Clinique
3. Imagerie
4. Documents
5. Finances

Actions :
- [ ] Header compact : identité, âge/date naissance, dossier, assurance, alertes critiques.
- [ ] Actions rapides : RDV, séance/examen, document, encaissement.
- [ ] Fusionner Archives dans Documents.
- [ ] Renommer `Documents A5` en `Documents`.
- [ ] Renommer `Radiologie (IA)` en `Imagerie`.
- [ ] Éviter les labels techniques internes dans la navigation utilisateur.

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

- [ ] Unifier Add/Edit Patient autour d'un même contrat de formulaire.
- [ ] Corriger anti-doublon fail-open côté UI.
- [ ] Réduire la saisie initiale au nécessaire puis enrichir dans le dossier.
- [ ] Simplifier KPI patient : Facturé / Encaissé / Reste dû / Prochaine échéance.
- [ ] Reléguer ou supprimer le taux de recouvrement côté fiche patient.
- [ ] Harmoniser encaissement rapide, acte et échéancier avec le contrat financier canonique.

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

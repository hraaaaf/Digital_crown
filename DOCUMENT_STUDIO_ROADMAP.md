# Document Studio — cartographie exhaustive & refonte intelligente

## Objectif
Cartographier puis refondre intelligemment tout le module documentaire de Digital Crown sans perdre les fonctionnalités utiles ni le positionnement premium.

L’audit doit descendre au niveau **interaction par interaction** : clic, touche clavier, état avant/après, panneau/modal/table affiché, position, contenu, données utilisées, backend appelé, calculs, erreurs, transitions entre pages et effets secondaires.

## Règle de preuve
Pour chaque comportement, distinguer explicitement :
- **CODE VÉRIFIÉ** : comportement démontré par le code source.
- **TEST IDENTIFIÉ** : comportement couvert par un test source inspecté ; ne signifie pas que le test a été exécuté dans cette session.
- **INTERACTION EXÉCUTÉE** : comportement observé dans l’application réelle.

Ne jamais assimiler une lecture de code ou la présence d’un test à un test UX réel.

## Format d’audit de chaque interaction
**Interaction → déclencheur → état avant → action → état après → élément affiché → position → contenu → données utilisées → backend/calcul → erreurs/edge cases → valeur UX → décision refonte.**

## Roadmap

### P1 — Ordonnance
Rapport canonique détaillé : `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md`

- [x] Saisie rapide, clavier et comportement de `Enter` — **code cartographié**
- [x] Autocomplétion et sélection — **code cartographié**
- [x] Presets intégrés — **inventaire/code cartographié**
- [x] Presets personnels / favoris — **code cartographié**
- [x] Habitudes apprises / suggestions — **code cartographié**
- [x] Bibliothèque médicaments — **code cartographié**
- [x] Recherche et filtres bibliothèque — **code cartographié**
- [x] Ajout/suppression/réorganisation d’un médicament — **code cartographié**
- [x] Posologies et chemins d’hydratation — **code cartographié**
- [x] Adaptation âge / poids / contexte patient — **code cartographié**
- [x] Validations médicament / dosage / alertes — **code cartographié**
- [x] Conseils patient — **code cartographié**
- [x] États vides, erreurs et fallback — **code cartographié**
- [x] Preview / sauvegarde / impression / sortie — **code cartographié**
- [x] Cartographie des appels backend et dépendances principales — **code cartographié**
- [x] Verdict UX et lots de refonte — **audit statique consolidé**
- [ ] **Interaction réelle exécutée/certifiée dans l’application**
- [ ] **Recertification après refonte**

#### P1 — lots d’audit
- **P1-L1 — Saisie rapide & clavier** : ✅ code cartographié. Score statique **8.1/10**.
- **P1-L2 — Ligne médicament** : ✅ code cartographié. Score statique **7.9/10**.
- **P1-L3 — Protocoles & habitudes** : ✅ code cartographié. Score statique **7.5/10**.
- **P1-L4 — Référentiel médicaments** : ✅ code cartographié. Score statique **8.0/10**.
- **P1-L5 — Âge / poids / dosage pédiatrique** : ✅ code cartographié. Score statique **7.0/10**.
- **P1-L6 — Sécurité & validation** : ✅ code cartographié. Score statique **6.8/10**.
- **P1-L7 — Contexte patient & conseils** : ✅ code cartographié. Score statique **6.8/10**.
- **P1-L8 — Sauvegarde / preview / impression / sortie** : ✅ code cartographié. Score statique **7.2/10**.
- **P1-L9 — Synthèse UX premium & plan d’implémentation** : ✅ consolidé. Score statique global P1 **7.4/10**.

#### P1 — lots de refonte planifiés
- **R1 — P0 Cohérence médicament / Maroc-first** : 🟡 **implémentation branchée sur tous les chemins principaux; frontend 109/109 + build ✅ sur le head `5024baf`; backend full suite encore en cours au dernier contrôle.** Pipeline unique quick/ligne/protocole/bibliothèque/assessment ; aucune estimation pédiatrique de poids ; aucune substitution thérapeutique silencieuse ; identité molécule via dictionnaire ; règles source-backed ; gate Maroc explicite ; sources internationales restent support et non recommandation marocaine.
- **R2 — P0 Persistance protocoles/habitudes** : corriger suppression mauvaise table, propagation des erreurs DB, save/load/delete déterministe, local-first.
- **R3 — P0 Safety orchestration** : connecter le moteur safety backend au Studio ou supprimer toute affirmation de validation non exécutée ; état de contrôle explicite.
- **R4 — P0 Dirty-state & actions** : toutes mutations ordonnance détectées, garde onglet/navigateur, refresh corrigé, défaut de forme implicite supprimé.
- **R5 — P1 Fast Prescription UX** : saisie rapide primaire, ligne progressive, typographie lisible, récents/favoris.
- **R6 — P1 Protocoles + Référentiel** : `Mes protocoles` unifié, masquer/réafficher réversible, bibliothèque search-first, contexte âge/poids homogène.
- **R7 — P1 Contexte + Preview premium** : terminologie déterministe, contexte patient compact, split-view responsive, preview read-only ordonnance certifiée.

#### R1 — preuve engineering exécutée
- CI PR #17 / run `31851832646`.
- Job **Frontend (tests & build)** : ✅.
- Vitest : **15 fichiers / 109 tests passés**.
- Tests R1 exécutés dans cette suite : `normalizeMedicationForPatient` 14/14, `DentalPharmacologySupplement` 10/10, `PrescriptionPharmacologyPipeline` 5/5, `MoroccoPharmacologyPolicy` 4/4, `DrugRow` 6/6, `clinical_rules.missing-data` 4/4.
- Build Vite production : ✅.
- Garde production négative : ✅.
- **Backend Tests & durcissement : en cours au dernier contrôle; R1 non fermé tant que ce gate n’est pas rendu.**
- **Aucune certification clinique humaine n’est revendiquée.** La validation par un reviewer marocain qualifié en pharmacologie/dentisterie reste un gate clinique séparé.

### P2 — Devis + Honoraires
- [ ] Actes rapides / recherche catalogue
- [ ] Odontogramme : chaque interaction dent/groupe/schéma
- [ ] Déclenchement du tableau/panneau associé
- [ ] Position, contenu, sélection et validation de ce tableau
- [ ] Modes individuel / groupe / général
- [ ] Tarification et habitudes tarifaires
- [ ] Bundles / propositions complémentaires
- [ ] Organisation par phases
- [ ] Totaux et cohérence
- [ ] Honoraires : encaissement et modes de règlement
- [ ] États vides, erreurs, sauvegarde, preview, impression
- [ ] Verdict UX

### P3 — Certificat + Document Libre
- [ ] Types de certificats et transitions
- [ ] Durée / slider / motif
- [ ] Suggestions et mutations automatiques
- [ ] Preview / sauvegarde / impression
- [ ] Document Libre : toolbar, formatage, tableaux, contenu brut/rendu
- [ ] Templates / réutilisation
- [ ] États vides / erreurs / protection saisie
- [ ] Verdict UX

### P4 — Suivi Paiement / Échéancier
- [ ] Chargement plan existant
- [ ] Total / avance / nombre d’échéances
- [ ] Génération des lignes
- [ ] Arrondis et réconciliation exacte
- [ ] Modification manuelle
- [ ] Statut payé / non payé
- [ ] Rappels / WhatsApp
- [ ] Résumé payé / restant / prochaine échéance
- [ ] États vides, erreurs, sauvegarde
- [ ] Verdict UX

### P5 — Compagnon diagnostique + interactions inter-pages
- [ ] Arbre complet des états/questions
- [ ] Contexte patient utilisé
- [ ] Sorties diagnostic / actes proposés
- [ ] Validation praticien
- [ ] Passage Compagnon → Devis
- [ ] Passage vers Ordonnance / autres documents si prévu
- [ ] Conservation/perte d’état lors des changements d’onglet
- [ ] Fonctionnalités orphelines / callbacks non utilisés
- [ ] Verdict UX et positionnement dans le produit

### P6 — Audit transversal premium
- [ ] Navigation globale et ordre des onglets
- [ ] Header / Footer et actions globales
- [ ] Dirty state / autosave / protections navigation
- [ ] Preview responsive / split view / plein écran
- [ ] Responsive multi-format
- [ ] Typographie / tailles minimales / contraste
- [ ] Dark mode
- [ ] Raccourcis clavier
- [ ] Cohérence labels / terminologie / faux labels IA
- [ ] États loading / empty / error / success
- [ ] Accessibilité
- [ ] Cohérence clinique/financière/documentaire

### P7 — Refonte intelligente finale
- [ ] Cartographie consolidée du module
- [ ] Matrice **GARDER / AMÉLIORER / FUSIONNER / CACHER / SUPPRIMER / REFAIRE**
- [ ] Nouvelle architecture de navigation
- [ ] Hiérarchie de ce qui doit être visible en premier
- [ ] Wireflow fonctionnel cible
- [ ] Priorités P0/P1/P2 de refonte
- [ ] Plan d’implémentation par lots réversibles
- [ ] Critères de validation UX/fonctionnels
- [ ] Recertification finale du Studio documentaire

## État courant
- **P1 Ordonnance : 🟡 audit statique détaillé terminé ; R1 Maroc-first engineering quasi fermé, frontend/build/gardes verts, backend full suite en cours au dernier contrôle ; interaction runtime et recertification clinique non exécutées.**
- P2 : ⬜
- P3 : ⬜
- P4 : ⬜
- P5 : ⬜
- P6 : ⬜
- P7 : ⬜

Le précédent audit statique général sert uniquement de pré-analyse. Aucun sous-P n’est déclaré certifié runtime sans interaction réelle ou test exécuté correspondant.

## Baseline
Audit P1 basé sur la branche `master` et l’état applicatif parent `c740b6644b4b85363438998dcf34284054122464`. Les commits ultérieurs de cette séquence modifient uniquement la documentation d’audit/roadmap jusqu’au démarrage de R1.
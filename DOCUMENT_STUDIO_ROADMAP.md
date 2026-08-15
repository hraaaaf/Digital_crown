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
- **R1 — P0 Cohérence médicament / Maroc-first** : ✅ **engineering fermé**. Pipeline unique quick/ligne/protocole/bibliothèque/assessment ; aucune estimation pédiatrique de poids ; aucune substitution thérapeutique silencieuse ; identité molécule via dictionnaire ; règles source-backed ; gate Maroc explicite ; sources internationales restent support et non recommandation marocaine.
- **R2 — P0 Persistance protocoles/habitudes** : ✅ **engineering fermé**. Source de vérité unique `DoctorPrescriptionPreference` ; save/load/delete déterministes ; code acte normalisé ; suppression absente = 404 ; erreurs DB rollback + propagation ; local-first conservé.
- **R3 — P0 Safety orchestration** : ✅ **engineering fermé**. Le Studio exécute le moteur safety backend, expose un état explicite `unchecked/checking/verified/error`, invalide la vérification sur changement patient/médicaments et n’affiche plus de validation verte avant succès du backend.
- **R4 — P0 Dirty-state & actions** : ✅ **engineering fermé**. Toutes mutations ordonnance dérivées du fingerprint complet, garde onglet/navigateur, reset après génération archivée, refresh contexte réellement relancé, fallback caché `forme='Sachets'` neutralisé avant transport backend et forme manquante exposée dans l’UI.
- **R5 — P1 Fast Prescription UX** : ✅ **engineering fermé**. Saisie rapide primaire, anti-double-submit, quick-picks récents/fréquents issus des habitudes praticien, ligne progressive et typographie renforcée.
- **R6 — P1 Protocoles + Référentiel** : ✅ **engineering fermé**. Référentiel search-first, contexte âge/poids visible, ajout manuel replié, `Mes protocoles` réversible après `Masquer`.
- **R7 — P1 Contexte + Preview premium** : ✅ **engineering fermé**. Terminologie déterministe, contexte patient compact, preview responsive, shell rigide neutralisé sur viewport étroit et preview ordonnance prouvée read-only par test backend.

#### R1 — preuve engineering exécutée
- PR `#17` — **MERGED**.
- Head final certifié : `8063b11b061ea6d1912e1b4e1a0ab8ef1fcb649a`.
- CI exacte du head final : run `31852032393` — **SUCCESS**.
- Job **Frontend (tests & build)** : ✅ SUCCESS.
- Job **Tests & durcissement** : ✅ SUCCESS.
- Job **Garde production (négatif)** : ✅ SUCCESS.
- Merge squash sur `master` : `e32ab311f72980e0797b93a306c3616a4ff66042`.
- La preuve précédente `109/109` correspondait à un head fonctionnel antérieur ; la fermeture R1 repose sur le run final exact ci-dessus et n’invente pas de compteur de tests non relu dans ses logs.
- **Aucune certification clinique humaine n’est revendiquée.** La validation par un reviewer marocain qualifié en pharmacologie/dentisterie reste un gate clinique séparé.

#### R2 — preuve engineering exécutée
- PR `#19` — **MERGED**.
- Head final certifié : `ba66457e5f65917f71670e151826062442525200`.
- CI exacte du head final : run `31852827218` — **SUCCESS**.
- Job **Frontend (tests & build)** : ✅ SUCCESS.
- Job **Tests & durcissement** : ✅ SUCCESS.
- Job **Garde production (négatif)** : ✅ SUCCESS.
- Merge sur `master` : `432a95eca05d1d7b9781d2d8e81077f0dcb589f2`.
- Tests R2 ciblés couvrent save → list → delete, 404 absent, rollback et propagation des erreurs DB.

#### R3 — preuve engineering exécutée
- PR `#20` — **MERGED**.
- Head final certifié : `becadcafb4ba0e6a5f4fda10a0053bb92c96fe1e`.
- CI exacte du head final : run `31853962025` — **SUCCESS**.
- Job **Frontend (tests & build)** : ✅ SUCCESS.
- Job **Tests & durcissement** : ✅ SUCCESS.
- Job **Garde production (négatif)** : ✅ SUCCESS.
- Merge squash sur `master` : `75e4693dc983ba1708914d16432504bea8f0cd8c`.
- État safety explicite : `unchecked | checking | verified | error`; aucun état `verified` avant réponse backend réussie.
- Dette non bloquante identifiée avant R4 : le parent `DocumentHub` possède encore un appel safety read-only parallèle ; déduplication à traiter sans modifier la sémantique fail-closed.
- **Aucune certification clinique/scientifique humaine n’est revendiquée.**

#### R4 — preuve engineering exécutée
- PR `#21` — **MERGED**.
- Head final certifié : `cdaf28874bc9155d115108bba7548470300c5ca1`.
- CI exacte du head final : run `31855874418` — **SUCCESS**.
- Job **Frontend (tests & build)** : ✅ SUCCESS.
- Job **Tests & durcissement** : ✅ SUCCESS.
- Job **Garde production (négatif)** : ✅ SUCCESS.
- Merge sur `master` : `6a4debe01cf0e0ea78e49ed787cae5e26c4976b8`.
- Dirty-state ordonnance dérivé d’un fingerprint complet ; protections tab + `beforeunload` ; actualisation contexte explicite ; transport conserve la forme visible au praticien sans inférence `Sachets` cachée.
- **Aucune certification UX runtime ni clinique/scientifique humaine n’est revendiquée.**

#### R5 — preuve engineering exécutée
- PR `#22` — **MERGED**.
- Head final certifié : `6de453962668e66be9e26978ec07fc9082afacb7`.
- CI exacte du head final : run `31878337816` — **SUCCESS**.
- Job **Frontend (tests & build)** : ✅ SUCCESS.
- Job **Tests & durcissement** : ✅ SUCCESS.
- Job **Garde production (négatif)** : ✅ SUCCESS.
- Merge sur `master` : `8957635e1bd50d8f44fbcef38c529b3c27f8fb32`.
- Quick-picks praticien réutilisent `DoctorMedicationHabit.last_used/usage_count` ; aucun second silo de préférences n’a été créé.
- Aucun favori étoilé explicite n’a été inventé : l’UX expose les récents/fréquents réellement disponibles.
- **Aucune certification UX runtime ni clinique/scientifique humaine n’est revendiquée.**

#### R6 — preuve engineering exécutée
- PR `#23` — **MERGED**.
- Head final certifié : `10751078601c3aa5be728bc263e25a58e856c676`.
- CI exacte du head final : run `31879112143` — **SUCCESS**.
- Job **Frontend (tests & build)** : ✅ SUCCESS.
- Job **Tests & durcissement** : ✅ SUCCESS.
- Job **Garde production (négatif)** : ✅ SUCCESS.
- Merge squash sur `master` : `6f2b8a22f9cdca25cafe228f266ed46deee8281b`.
- Le premier run R6 a échoué uniquement sur une assertion de compteur de rendu trop stricte dans le test wrapper ; le test a été corrigé pour mesurer l’augmentation après remount, puis le head final ci-dessus a passé la CI complète.
- Référentiel search-first + ajout manuel replié + contexte âge/poids visible ; `Mes protocoles` restaure la barre legacy après masquage par remount contrôlé.
- **Aucune certification UX runtime ni clinique/scientifique humaine n’est revendiquée.**

#### R7 — preuve engineering exécutée
- PR `#26` — **MERGED**.
- Head final certifié : `9a39ecc4d415e59c5457a58638a48ba0c22f81fd`.
- CI exacte du head final : run `31879649826` — **SUCCESS**.
- Job **Frontend (tests & build)** : ✅ SUCCESS.
- Job **Tests & durcissement** : ✅ SUCCESS.
- Job **Garde production (négatif)** : ✅ SUCCESS.
- Merge squash sur `master` : `2596da527fdd1bee5c6746f645e995f682ca3189`.
- Le candidat final consolide les anciens sous-lots #24/#25 devenus obsolètes après R6 : contexte patient déterministe, preview responsive et preuve DB read-only ordonnance.
- **Aucune certification UX runtime ni clinique/scientifique humaine n’est revendiquée.**

### P2 — Devis + Honoraires
Rapport canonique en cours : `docs/audits/DOCUMENT_STUDIO_P2_DEVIS_HONORAIRES_AUDIT.md`

- [x] Actes rapides / recherche catalogue — **P2-A prix catalogue local fermé ; tactile/terminologie restent P2-C**
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

#### P2 — lots de refonte
- **P2-A — Prix catalogue local conservé** : ✅ **engineering fermé**.
  - PR `#27` — MERGED.
  - Head final certifié : `7289d0bf64c8139838470923622f8c0b588206e1`.
  - CI exacte : run `31882328096` — SUCCESS.
  - Frontend tests/build : ✅ SUCCESS.
  - Backend tests/durcissement : ✅ SUCCESS.
  - Garde production négative : ✅ SUCCESS.
  - Merge squash : `a8ce1f8143fd58f20aee5cb4ebb9b8827128c4cc`.
  - Aucun prix n’est inventé : seul un `base_price` local déjà présent dans le catalogue peut remplacer le zéro legacy.
- **P2-B — PARTIEL fail-closed cohérent UI/backend** : 🟡 **ACTIVE**.
- **P2-C — Actes rapides tactile + terminologie déterministe + phases neutres** : préparation isolée en cours.
- **P2-D — Odontogramme/déduplication/prix groupe** : défaut handler de déduplication orphelin confirmé ; policy préparée.
- **P2-E — Totaux/payload/échéances** : absence de réconciliation échéances/total confirmée ; policy au centime préparée.
- **P2-F — Honoraires/encaissement complet + effets post-archive** : à poursuivre.

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
- **P1 Ordonnance : ✅ R1 à R7 engineering fermés et fusionnés. Audit statique détaillé terminé. Interaction runtime et recertification clinique/UX restent des gates séparés, non revendiqués.**
- **P2 : 🟡 ACTIVE** — P2-A fermé et fusionné ; P2-B ACTIVE ; P2-C/D/E préparés sans intégration ; audit runtime non exécuté.
- P3 : ⬜
- P4 : ⬜
- P5 : ⬜
- P6 : ⬜
- P7 : ⬜

Le précédent audit statique général sert uniquement de pré-analyse. Aucun sous-P n’est déclaré certifié runtime sans interaction réelle ou test exécuté correspondant.

## Baseline
Audit P1 basé sur la branche `master` et l’état applicatif parent `c740b6644b4b85363438998dcf34284054122464`. R1 a ensuite été fusionné via `e32ab311f72980e0797b93a306c3616a4ff66042`; R2 via `432a95eca05d1d7b9781d2d8e81077f0dcb589f2`; R3 via `75e4693dc983ba1708914d16432504bea8f0cd8c`; R4 via `6a4debe01cf0e0ea78e49ed787cae5e26c4976b8`; R5 via `8957635e1bd50d8f44fbcef38c529b3c27f8fb32`; R6 via `6f2b8a22f9cdca25cafe228f266ed46deee8281b`; R7 via `2596da527fdd1bee5c6746f645e995f682ca3189`; P2-A via `a8ce1f8143fd58f20aee5cb4ebb9b8827128c4cc`. P2-B part de cette baseline fonctionnelle.

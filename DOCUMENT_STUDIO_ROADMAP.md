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
- [x] **Recertification visuelle après refonte** — PR #43 mergée `91a2c2efd781fd736ebdc96e9de4f5e3c73c82c8` ; captures 1440/768/390 inspectées ; CI PR `31898122575` SUCCESS. Interaction authentifiée locale reste séparée.

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


#### P1 — closeout runtime visuel / glass
- PR `#43` — **MERGED**.
- Head final PR : `9a00f07c4b1dc98776cf03bc17b27c23b50d7a81` ; CI exacte run `31898122575` — **SUCCESS**.
- Merge `master` : `91a2c2efd781fd736ebdc96e9de4f5e3c73c82c8`.
- Baseline visuelle pré-R1 auditée via run `31897932430` — SUCCESS.
- Recapture finale glass 1440 / 768 / 390 via run `31898157179` — **SUCCESS** ; artifact `9250378182` ; inspection visuelle propre.
- Le glassmorphisme historique n'a pas été supprimé ; le correctif final regroupe contexte, sécurité, actions et alerte forme dans une hiérarchie glass cohérente sans retirer les gardes de sécurité.
- **Non couvert par cette preuve :** interaction authentifiée dans l'application locale réelle et certification clinique/pharmacologique.
- CI push post-merge : run `31898590067` — **SUCCESS**.

### P2 — Devis + Honoraires
Rapport canonique en cours : `docs/audits/DOCUMENT_STUDIO_P2_DEVIS_HONORAIRES_AUDIT.md`

- [x] Actes rapides / recherche catalogue — **P2-A prix catalogue local + P2-C tactile/terminologie fermés**
- [ ] Odontogramme : chaque interaction dent/groupe/schéma
- [ ] Déclenchement du tableau/panneau associé
- [ ] Position, contenu, sélection et validation de ce tableau
- [ ] Modes individuel / groupe / général
- [ ] Tarification et habitudes tarifaires
- [ ] Bundles / propositions complémentaires
- [x] Organisation par phases — **P2-C regroupement déterministe fermé ; runtime reste ouvert**
- [x] Totaux et cohérence — **P2-E réconciliation Honoraires globale fermée ; flux direct échéancier reste P4**
- [x] Honoraires : contrat PARTIEL/modes de règlement — **P2-B et P2-F fermés**
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
- **P2-B — PARTIEL fail-closed cohérent UI/backend** : ✅ **engineering fermé**.
  - PR `#29` — MERGED.
  - Head final certifié : `d60a99c290e0e27c84d73fb95d947fa111461f7a`.
  - CI exacte : run `31884437013` — SUCCESS.
  - Frontend tests/build : ✅ SUCCESS.
  - Backend tests/durcissement : ✅ SUCCESS.
  - Garde production négative : ✅ SUCCESS.
  - Merge squash : `6543c3dad146bdbe055117fe0302b3fbe9cbda07`.
  - Premier head `1005f228…` : backend rouge uniquement à cause d’un `ValueError` Pydantic non sérialisable par le handler JSON ; corrigé avec `PydanticCustomError` sur le head final.
- **P2-E — Totaux/payload/échéances** : ✅ **engineering fermé**.
  - PR `#34` — MERGED.
  - Head final certifié : `97c3f43019b5eee781da220ef27ef14053593311`.
  - CI exacte : run `31885119569` — SUCCESS.
  - Frontend tests/build : ✅ SUCCESS.
  - Backend tests/durcissement : ✅ SUCCESS.
  - Garde production négative : ✅ SUCCESS.
  - Merge squash : `cb265a8070307d3e3be2e76b239af7762254dddd`.
  - Honoraires global : échéances strictement positives et somme exacte au centime avant persistance.
- **P2-F — Allocation PAYE exacte par Acte** : ✅ **engineering fermé**.
  - PR `#36` — MERGED.
  - Head final certifié : `63c636266242b5884ec0f21d9cea28611d13c473`.
  - CI exacte du head final : run `31886400223` — SUCCESS.
  - Frontend tests/build : ✅ SUCCESS.
  - Backend tests/durcissement : ✅ SUCCESS.
  - Garde production négative : ✅ SUCCESS.
  - Merge squash : `5916216ae6b3ebe6cf3609ff652ee09cc549391f`.
  - Le banc préparatoire `31885269345` avait reproduit le défaut : 2 Acte PAYE mais 1 seul Payment global sans `acte_id`.
  - Le flux final crée un paiement exact positif par Acte PAYE et lie chaque Payment à son `acte_id`; aucun paiement global orphelin n’est créé.
- **P2-C — Actes rapides tactile + terminologie déterministe + phases neutres** : ✅ **engineering fermé**.
  - PR finale `#46` — MERGED ; ancienne PR préparatoire `#32` fermée sans merge.
  - Head final certifié : `0a5b7dc50fd452c8950c42043340ad9cbea44106`.
  - CI exacte : run `31900572795` — **3/3 SUCCESS**.
  - Frontend tests/build : ✅ SUCCESS.
  - Backend tests/durcissement : ✅ SUCCESS.
  - Garde production négative : ✅ SUCCESS.
  - Merge `master` : `967f56ed10d61b373bcd3c75e6a737a49bd7349a`.
  - `AccountingQuickActions` est branché au legacy actif ; le regroupement par phases utilise `AccountingPhasePolicy`; les faux labels IA et la durée fixe de cicatrisation non sourcée sont retirés de ce flux.
- **P2-D — Odontogramme/déduplication/prix groupe** : ✅ **engineering fermé**.
  - PR finale `#47` — MERGED ; ancienne PR préparatoire `#33` fermée sans merge.
  - Head final certifié : `2698f3d508c57ca07a410706d05855adba3bc392`.
  - CI exacte : run `31902205419` — **3/3 SUCCESS**.
  - Frontend tests/build : ✅ SUCCESS.
  - Backend tests/durcissement : ✅ SUCCESS.
  - Garde production négative : ✅ SUCCESS.
  - Merge `master` : `021ee425a532bb83ae9669ab4c449522258bdcc6`.
  - Le flux actif remplace idempotemment les traitements par dent via une clé stable `dent::traitement`, préserve les autres dents et les lignes manuelles, autorise la suppression du dernier traitement d’une dent déjà renseignée, conserve le libellé de surface existant si aucune nouvelle surface n’est fournie et refuse l’ajout silencieux d’un acte groupé à `0 MAD`.
  - **Aucune interaction authentifiée runtime, certification clinique ou certification financière production n’est revendiquée.**

### P3 — Certificat + Document Libre
- [ ] Types de certificats et transitions
- [ ] Durée / slider / motif
- [ ] Suggestions et mutations automatiques
- [ ] Preview / sauvegarde / impression
- [ ] Document Libre : toolbar, formatage, tableaux, contenu brut/rendu
- [ ] Templates / réutilisation
- [ ] États vides / erreurs / protection saisie
- [ ] Verdict UX

#### P3 — lots engineering fermés
- **P3-A — Suggestions de certificat non mutantes** : ✅ **engineering fermé**. PR `#37`, head final `6b88c0aebed8ba95dc248a743f9e82cf62c511e1`, CI exacte `31887555410` — 3/3 SUCCESS, merge `52d58f0efc94e68ef45fc12fa7912d15c2830e64`. Les suggestions ne modifient plus automatiquement type ou durée.
- **P3-B — Motif personnalisé obligatoire pour certificat “Autre”** : ✅ **engineering fermé**. PR `#39`, head final `5eacafb57f5d76f9fddd748e468b4828b5d31834`, CI exacte `31894899652` — 3/3 SUCCESS, merge `2c677f229a25732c2895615261f9205d2a227e52`. Le fallback silencieux `Autre → Repos Post-Opératoire` est supprimé ; un motif personnalisé vide échoue explicitement.
- **P3-C — Validation visuelle du Document Libre** : ✅ **engineering fermé**. PR `#40`, head final `7c1793f2331ff5e726f9f964d941dc1e96c56f5f`, CI exacte `31895447932` — 3/3 SUCCESS, merge `a7f81ed332ab2a3774382ace3db2446cd6d447d1`. Les erreurs `libreTitle`/`libreContent` sont reliées aux champs canoniques et les actions de formatage ne soumettent pas le formulaire.

Les cases P3 ci-dessus restent ouvertes tant que l’audit interaction-par-interaction, la preview/sauvegarde/impression et la certification UX runtime correspondante ne sont pas exécutés. **Aucune certification clinique/scientifique ou UX runtime n’est revendiquée par ces fermetures engineering.**

### P4 — Suivi Paiement / Échéancier
- [ ] Chargement plan existant
- [ ] Total / avance / nombre d’échéances
- [ ] Génération des lignes
- [x] Arrondis et réconciliation exacte — **P4-A engineering fermé**
- [ ] Modification manuelle
- [x] Statut payé / non payé — **P4-B intégrité backend fail-closed fermée ; UX runtime reste ouverte**
- [ ] Rappels / WhatsApp
- [ ] Résumé payé / restant / prochaine échéance
- [ ] États vides, erreurs, sauvegarde
- [ ] Verdict UX

#### P4 — lots engineering fermés
- **P4-A — Répartition exacte des échéances** : ✅ **engineering fermé**. PR `#41`, head final `7a715bdd79c9579329bcdd496807f72ed8f69d9a`, CI exacte `31896494441` — 3/3 SUCCESS, merge `989b819fe9f38ea616a48bf34e59263f7bcab82b`. La répartition réconcilie exactement le total au centime et l’auto-application de valeurs financières `PriceBrain` est supprimée ; l’apprentissage ne survient qu’après génération explicite.
- **P4-B — Paiement d’échéance fail-closed** : ✅ **engineering fermé**. PR `#42`, head final rebasé `d75b132a3d9ef705f6dc27eb4de8d44ca1eebe53`, CI exacte `31897537545` — 3/3 SUCCESS, merge `365a8cd9f1e9543898a70e060fd3e6890f647d66`. Création plan+échéances atomique, méthode de paiement explicite obligatoire au premier passage PAYE, `Payment.amount` basé sur le montant final, et une échéance déjà payée ne peut plus être rouverte ou repricée silencieusement.

Les autres comportements P4 restent à auditer/exécuter dans l’application réelle. **Aucune certification financière runtime n’est revendiquée.**

### P5 — Compagnon diagnostique + interactions inter-pages
- [ ] Arbre complet des états/questions
- [ ] Contexte patient utilisé
- [ ] Sorties diagnostic / actes proposés
- [x] Validation praticien — **P5-P0 supprime les substitutions thérapeutiques automatiques dérivées du texte d’allergie**
- [ ] Passage Compagnon → Devis
- [ ] Passage vers Ordonnance / autres documents si prévu
- [ ] Conservation/perte d’état lors des changements d’onglet
- [ ] Fonctionnalités orphelines / callbacks non utilisés
- [ ] Verdict UX et positionnement dans le produit

- **P5-P0 — frontière pharmacovigilance / substitution** : ✅ **engineering fermé**.
  - PR `#38` — MERGED.
  - Head final certifié : `66cc5e125c6e37c558d097e3b497a16a58d09edc`.
  - CI exacte : run `31886995993` — SUCCESS.
  - Frontend tests/build : ✅ SUCCESS.
  - Backend tests/durcissement : ✅ SUCCESS.
  - Garde production négative : ✅ SUCCESS.
  - Merge squash : `46d9388e80e3334230f8bea1356e4e38951408ca`.
  - `HouseWizard` passe par `SafeDiagnosticEngine`; les signaux textuels d’allergie produisent des warnings et ne réécrivent plus automatiquement le protocole thérapeutique.
  - **Cette fermeture ne valide pas scientifiquement les règles diagnostiques ou protocoles médicamenteux legacy.**

Pré-audit statique P5 reste actif pour le reste du compagnon diagnostique et ses interactions inter-pages.

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

Pré-audit statique isolé sur `work-20260815-p6-static-audit` : micro-typographie 9–10 px, sémantique d’onglets incomplète, sortie/reload à centraliser dans le dirty-state et terminologie autoritative identifiés. **Non fusionné, non certifié.**

### P7 — Refonte intelligente finale
- [ ] Cartographie consolidée du module
- [ ] Matrice **GARDER / AMÉLIORER / FUSIONNER / CACHER / SUPPRIMER / REFAIRE**
- [ ] Nouvelle architecture de navigation
- [ ] Hiérarchie de ce qui doit être visible en premier
- [ ] Priorités P0/P1/P2 de refonte
- [ ] Plan d’implémentation par lots réversibles
- [ ] Critères de validation UX/fonctionnels
- [ ] Recertification finale du Studio documentaire

## État courant
- **P1 Ordonnance : ✅ R1 à R7 engineering fermés et fusionnés. Audit statique détaillé terminé. Interaction runtime et recertification clinique/UX restent des gates séparés, non revendiqués.**
- **P2 : 🟡 ACTIVE** — P2-A/B/C/E/F fermés et fusionnés ; P2-D préparé sans intégration ; audit runtime non exécuté.
- **P3 : 🟡 ACTIVE** — P3-A/B/C engineering fermés et fusionnés ; audit interaction-par-interaction, preview/sauvegarde/impression et certification UX runtime restent ouverts.
- **P4 : 🟡 ACTIVE** — P4-A/B engineering fermés et fusionnés ; autres comportements et certification financière/UX runtime restent ouverts.
- **P5 : 🟡 ACTIVE** — P5-P0 clinique fermé et fusionné ; reste du compagnon diagnostique/inter-pages à auditer/refondre.
- **P6 : 🟡 pré-audit statique isolé, non fusionné.**
- P7 : ⬜

Le précédent audit statique général sert uniquement de pré-analyse. Aucun sous-P n’est déclaré certifié runtime sans interaction réelle ou test exécuté correspondant.

## Baseline
Audit P1 basé sur la branche `master` et l’état applicatif parent `c740b6644b4b85363438998dcf34284054122464`. R1 a ensuite été fusionné via `e32ab311f72980e0797b93a306c3616a4ff66042`; R2 via `432a95eca05d1d7b9781d2d8e81077f0dcb589f2`; R3 via `75e4693dc983ba1708914d16432504bea8f0cd8c`; R4 via `6a4debe01cf0e0ea78e49ed787cae5e26c4976b8`; R5 via `8957635e1bd50d8f44fbcef38c529b3c27f8fb32`; R6 via `6f2b8a22f9cdca25cafe228f266ed46deee8281b`; R7 via `2596da527fdd1bee5c6746f645e995f682ca3189`; P2-A via `a8ce1f8143fd58f20aee5cb4ebb9b8827128c4cc`; P2-B via `6543c3dad146bdbe055117fe0302b3fbe9cbda07`; P2-E via `cb265a8070307d3e3be2e76b239af7762254dddd`; P2-F via `5916216ae6b3ebe6cf3609ff652ee09cc549391f`; P2-C via `967f56ed10d61b373bcd3c75e6a737a49bd7349a`; P3-A via `52d58f0efc94e68ef45fc12fa7912d15c2830e64`; P3-B via `2c677f229a25732c2895615261f9205d2a227e52`; P3-C via `a7f81ed332ab2a3774382ace3db2446cd6d447d1`; P4-A via `989b819fe9f38ea616a48bf34e59263f7bcab82b`; P4-B via `365a8cd9f1e9543898a70e060fd3e6890f647d66`; P5-P0 via `46d9388e80e3334230f8bea1356e4e38951408ca`. Les autres lots actifs doivent repartir de cette baseline fonctionnelle après rebase exact.
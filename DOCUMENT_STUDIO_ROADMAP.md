# Document Studio — roadmap canonique page par page

## Objectif

Auditer, corriger et recertifier le Studio documentaire de Digital Crown **page par page, dans l’ordre visuel réel de l’interface**, sans perdre les preuves techniques déjà acquises.

L’ordre canonique est celui de `frontend/src/features/admin/DocumentStudio/StudioTabs.tsx`.

## Règle de numérotation canonique — depuis le 16 août 2026

1. **P1 — Ordonnance**
2. **P2 — Certificat**
3. **P3 — Devis**
4. **P4 — Note Honoraires**
5. **P5 — Suivi Paiement**
6. **P6 — Document Libre**
7. **P7 — Compagnon Diagnostique**

Les anciens identifiants techniques comme `P2-A`, `P2-B`, `P3-C`, `P4-A` ou `P5-P0` sont **conservés comme références historiques de PR/commits**. Ils ne définissent plus le numéro de page.

Les anciens chantiers transversaux deviennent :
- **T1 — Audit transversal premium** ;
- **T2 — Refonte intelligente finale / recertification globale**.

## Règle de preuve

Pour chaque page et chaque interaction :
- **CODE VÉRIFIÉ** : comportement démontré par le code source ;
- **TEST EXÉCUTÉ** : test réellement exécuté avec résultat observé ;
- **INTERACTION EXÉCUTÉE** : comportement observé dans l’application réelle ;
- **CERTIFICATION CLINIQUE / FINANCIÈRE / PRODUCTION** : séparée de l’engineering et jamais déduite d’une CI verte.

Une page n’est pas déclarée totalement certifiée tant que ses gates applicables ne sont pas réellement fermés.

---

## P1 — Ordonnance

**État : ✅ engineering fermé + recertification visuelle réalisée.**

Rapport canonique : `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md`.

### Acquis
- audit interactionnel/statique détaillé ;
- R1 à R7 engineering fermés et fusionnés ;
- cohérence médicament / Maroc-first ;
- persistance protocoles/habitudes ;
- orchestration safety fail-closed ;
- dirty-state et protections navigation ;
- fast prescription UX ;
- référentiel/protocoles ;
- contexte patient + preview responsive ;
- recertification visuelle 1440 / 768 / 390.

### Preuves principales
- R1 : PR #17, CI `31852032393`, merge `e32ab311f72980e0797b93a306c3616a4ff66042` ;
- R2 : PR #19, CI `31852827218`, merge `432a95eca05d1d7b9781d2d8e81077f0dcb589f2` ;
- R3 : PR #20, CI `31853962025`, merge `75e4693dc983ba1708914d16432504bea8f0cd8c` ;
- R4 : PR #21, CI `31855874418`, merge `6a4debe01cf0e0ea78e49ed787cae5e26c4976b8` ;
- R5 : PR #22, CI `31878337816`, merge `8957635e1bd50d8f44fbcef38c529b3c27f8fb32` ;
- R6 : PR #23, CI `31879112143`, merge `6f2b8a22f9cdca25cafe228f266ed46deee8281b` ;
- R7 : PR #26, CI `31879649826`, merge `2596da527fdd1bee5c6746f645e995f682ca3189` ;
- closeout visuel : PR #43, CI `31898122575`, merge `91a2c2efd781fd736ebdc96e9de4f5e3c73c82c8`, recapture `31898157179`, post-merge `31898590067`.

### Gate séparé restant
- interaction authentifiée dans l’application locale réelle ;
- certification clinique/pharmacologique humaine.

---

## P2 — Certificat

**État : ✅ engineering convergé ; ⏳ certification finale runtime/PDF non fermée.**

Rapport historique/canonique actuel : `docs/audits/DOCUMENT_STUDIO_P3_CERTIFICAT_AUDIT.md`.

> Le nom du fichier d’audit conserve l’ancien identifiant `P3` pour traçabilité. La page est désormais **P2** dans la roadmap canonique.

### Acquis engineering Certificat
- nature du document explicite ;
- dates + durée séparées ;
- aucun type/durée clinique prérempli sur un nouveau certificat ;
- certificat médical libre 100 % praticien ;
- suggestions contextuelles non prescriptives ;
- contrat backend fail-closed ;
- validation UX praticien ;
- signature manuscrite, signataire `DENTISTE` uniquement ;
- impression fraîche et sûre ;
- intégrité PDF / identité datée ;
- QR validation neutralisé sans contrat valide ;
- routage PDF, noms de fichiers et texte libre long sécurisés.

### Preuves / historique
PR Certificat fusionnées notamment : #48, #49, #52, #53, #54, #55, #56, #57, #58, #59, #60, #61, #63.

Les lots récents ont rencontré un blocage GitHub Actions **avant exécution des steps** ; aucune CI verte récente n’est inventée.

### Gate séparé restant
- régression réelle du `master` final ;
- runtime authentifié des parcours Certificat ;
- inspection visuelle des PDF finaux ;
- certification réglementaire/clinique indépendante si requise.

---

## P3 — Devis

**État : ⏸ CLOSED / PAUSED UNTIL FURTHER NOTICE — décision produit du 16 août 2026.**

Rapport de statut canonique : `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_INTEGRATION_STATUS.md`.

Historique technique partagé avec Note Honoraires : `docs/audits/DOCUMENT_STUDIO_P2_DEVIS_HONORAIRES_AUDIT.md`.

> Les anciens lots `P2-*` restent des identifiants historiques. Ils alimentent désormais P3 Devis et P4 Note Honoraires selon leur portée réelle.

### Socle engineering acquis
- ancien **P2-A** : prix catalogue local conservé, PR #27, CI `31882328096`, merge `a8ce1f8143fd58f20aee5cb4ebb9b8827128c4cc` ;
- ancien **P2-C** : actes rapides tactiles + terminologie déterministe + phases neutres, PR #46, CI `31900572795` 3/3 SUCCESS, merge `967f56ed10d61b373bcd3c75e6a737a49bd7349a` ;
- ancien **P2-D** : odontogramme / déduplication / prix groupe, PR #47, CI `31902205419` 3/3 SUCCESS, merge `021ee425a532bb83ae9669ab4c449522258bdcc6` ;
- ancien **P2-E** : réconciliation totale/échéances partagée, PR #34, CI `31885119569`, merge `cb265a8070307d3e3be2e76b239af7762254dddd` ;
- branche d’intégration P3-A→P3-G : `agent/p3d-devis-phases-learning`, PR #77 conservée **open + draft** ;
- isolation financière Devis, source de vérité odontogramme, tarification catalogue, phases, lifecycle, PDF lisible, dirty-state, responsive/accessibilité durcis ;
- P7→P3 filtré et P3→Honoraires rendu explicite.

### Preuves P3-H locales exécutées
- backend P3 : **26/26 PASS** sous Linux ;
- frontend policies : **`tsc --strict` PASS** ;
- tests frontend P3 : **39/39 PASS** via orchestration locale compatible Vitest ;
- garde apprentissage : **PASS** ;
- PriceBrain pré-archive : **PASS** ;
- PDF 36 lignes longues : **3 pages**, header **3/3**, minimum observé **7,5 pt**, floor **7,0 pt**, total non coupé avec l’algorithme adaptive réel.

### Gates volontairement différés
Ces éléments **ne sont pas revendiqués comme exécutés** et doivent être repris uniquement si P3 est rouvert :
- full checkout + vraies dépendances frontend ;
- vrai `npm test` / `npm run build` full-project ;
- smoke authentifié adulte/pédiatrique ;
- archive/reopen réel dents/notes/surfaces/code/multi-dents ;
- duplicate/stale-print dans l’application complète ;
- PDF cabinet branding/signature ;
- browser 390 / 768 / desktop + clavier/touch ;
- ready review / merge / post-merge recertification.

**Verdict : chantier P3 clos opérationnellement, certification full-app différée et non revendiquée.**

---

## P4 — Note Honoraires

**État : 🟡 PAGE ACTIVE — audit page-par-page à démarrer maintenant.**

Historique technique partagé : `docs/audits/DOCUMENT_STUDIO_P2_DEVIS_HONORAIRES_AUDIT.md`.

### Socle engineering déjà acquis
- ancien **P2-B** : `PARTIEL` fail-closed cohérent UI/backend, PR #29, CI `31884437013`, merge `6543c3dad146bdbe055117fe0302b3fbe9cbda07` ;
- ancien **P2-E** : totaux/payload/échéances, PR #34, CI `31885119569`, merge `cb265a8070307d3e3be2e76b239af7762254dddd` ;
- ancien **P2-F** : allocation `PAYE` exacte par Acte, PR #36, CI `31886400223`, merge `5916216ae6b3ebe6cf3609ff652ee09cc549391f` ;
- les socles actes rapides / odontogramme communs issus des anciens P2-C/P2-D sont également présents ;
- l’audit P4 doit intégrer les changements partagés introduits par la branche P3 avant de conclure sur l’état courant.

### À auditer
- [ ] état initial Note Honoraires ;
- [ ] reprise des actes / panier ;
- [ ] statut de paiement ;
- [ ] modes de règlement ;
- [ ] cohérence Acte ↔ Payment ;
- [ ] totaux et reste dû ;
- [ ] preview / archive / impression ;
- [ ] comportement après archivage ;
- [ ] erreurs et dirty-state ;
- [ ] responsive / accessibilité ;
- [ ] verdict UX et recertification.

---

## P5 — Suivi Paiement

**État : 🟡 engineering financier critique partiellement fermé ; audit runtime page complet restant.**

### Acquis historiques
- ancien **P4-A** : répartition exacte des échéances, PR #41, CI `31896494441`, merge `989b819fe9f38ea616a48bf34e59263f7bcab82b` ;
- ancien **P4-B** : paiement d’échéance fail-closed, PR #42, CI `31897537545`, merge `365a8cd9f1e9543898a70e060fd3e6890f647d66`.

### À auditer
- [ ] chargement plan existant ;
- [ ] total / avance / nombre d’échéances ;
- [ ] génération des lignes ;
- [ ] modification manuelle ;
- [ ] passage payé / non payé ;
- [ ] méthode de paiement ;
- [ ] résumé payé / restant / prochaine échéance ;
- [ ] rappels / WhatsApp si réellement branchés ;
- [ ] erreurs / sauvegarde ;
- [ ] responsive / accessibilité ;
- [ ] certification financière runtime séparée.

---

## P6 — Document Libre

**État : ✅ engineering convergé ; ⏳ certification finale runtime/PDF non fermée.**

Rapport historique/canonique actuel : `docs/audits/DOCUMENT_STUDIO_P3_CERTIFICAT_AUDIT.md`.

> Le rapport conserve l’ancien regroupement `P3 Certificat + Document Libre` pour traçabilité. Document Libre est désormais **P6**.

### Acquis engineering
- ancien P3-C / PR #40 : validation champs + toolbar non-submit ;
- ancien P3-D / PR #64 : contrat + PDF sûr ;
- ancien P3-E / PR #65 : impression sûre ;
- ancien P3-F / PR #66 : auto-preview invalide silencieux ;
- ancien P3-G / PR #67 : protection des brouillons ;
- ancien P3-H / PR #70 : permission clinique d’émission.

### Gate séparé restant
- régression réelle frontend/backend/PDF ;
- runtime authentifié saisie, toolbar, tableau, A4/A5, alignement, preview, archive, réouverture, abandon protégé et impression ;
- inspection visuelle PDF multi-page ;
- amélioration WYSIWYG éventuelle classée produit, non sécurité.

---

## P7 — Compagnon Diagnostique

**État : 🟡 frontière safety partiellement fermée ; audit complet restant.**

### Acquis historique
- ancien **P5-P0** : frontière pharmacovigilance / substitution, PR #38, CI `31886995993`, merge `46d9388e80e3334230f8bea1356e4e38951408ca` ;
- les signaux textuels d’allergie produisent des warnings et ne substituent plus automatiquement un protocole thérapeutique.

### À auditer
- [ ] arbre complet des états/questions ;
- [ ] contexte patient réellement utilisé ;
- [ ] sorties diagnostiques / actes proposés ;
- [ ] validation praticien ;
- [ ] passage Compagnon → Devis ;
- [ ] passage vers Ordonnance / autres documents ;
- [ ] conservation/perte d’état inter-pages ;
- [ ] callbacks orphelins ;
- [ ] valeur clinique et UX ;
- [ ] validation scientifique humaine séparée.

---

## T1 — Audit transversal premium

**État : ⬜ à traiter après les pages P1 à P7 ou lorsqu’un défaut transversal bloque plusieurs pages.**

- [ ] navigation globale et ordre des onglets ;
- [ ] header / footer / actions globales ;
- [ ] dirty-state / protections navigation ;
- [ ] preview responsive / split view / plein écran ;
- [ ] responsive multi-format ;
- [ ] typographie / tailles minimales / contraste ;
- [ ] dark mode ;
- [ ] raccourcis clavier ;
- [ ] cohérence labels / terminologie ;
- [ ] loading / empty / error / success ;
- [ ] accessibilité ;
- [ ] cohérence clinique, financière et documentaire.

Ancien pré-audit `P6` conservé comme historique, mais **T1** est désormais l’identifiant canonique transversal.

---

## T2 — Refonte intelligente finale / recertification globale

**État : ⬜ après convergence P1 à P7 + T1.**

- [ ] cartographie consolidée du module ;
- [ ] matrice `GARDER / AMÉLIORER / FUSIONNER / CACHER / SUPPRIMER / REFAIRE` ;
- [ ] architecture finale de navigation ;
- [ ] hiérarchie de l’information ;
- [ ] priorités P0/P1/P2 ;
- [ ] critères de validation UX/fonctionnels ;
- [ ] régression globale ;
- [ ] recertification finale du Studio documentaire.

Ancien chantier `P7 Refonte intelligente finale` renommé **T2** afin de réserver P7 à la vraie septième page du Studio.

---

## Table de migration des anciens identifiants

| Ancien identifiant | Portée historique | Nouvelle page canonique |
|---|---|---|
| P1 / R1-R7 | Ordonnance | **P1 Ordonnance** |
| P2-A, P2-C, P2-D | Devis / socle comptable partagé | **P3 Devis** principalement |
| P2-B, P2-E, P2-F | Honoraires / contrats comptables partagés | **P4 Note Honoraires** principalement |
| P3 Certificat | Certificat | **P2 Certificat** |
| P3-C à P3-H Document Libre | Document Libre | **P6 Document Libre** |
| P4-A / P4-B | Échéancier / paiements | **P5 Suivi Paiement** |
| P5-P0 | Compagnon / safety | **P7 Compagnon Diagnostique** |
| ancien P6 | Audit transversal | **T1** |
| ancien P7 | Refonte finale | **T2** |

Les PR, commits, noms de branches et fichiers d’audit historiques **ne sont pas renommés rétroactivement**.

---

## État courant / chemin critique

1. **P1 Ordonnance** : engineering + visuel fermés ; gates authentifiés/cliniques séparés.
2. **P2 Certificat** : engineering convergé ; certification finale runtime/PDF encore ouverte.
3. **P3 Devis** : **clos/pausé jusqu’à nouvel ordre** ; full-app gates différés et documentés ; PR #77 conservée draft.
4. **P4 Note Honoraires** : **PAGE ACTIVE**.
5. **P5 Suivi Paiement** : après P4.
6. **P6 Document Libre** : engineering convergé ; runtime/PDF final à recertifier dans son tour de page.
7. **P7 Compagnon Diagnostique** : après P6.
8. **T1** puis **T2** : transversal et closeout global.

## Règle de progression

Pour chaque page :

**audit interaction par interaction → défauts classés → correctifs réversibles → tests ciblés → CI si disponible → runtime/visuel selon le risque → mise à jour audit canonique → mise à jour roadmap → page suivante.**

Un blocage d’infrastructure externe non spécifique à la page doit être consigné mais ne doit pas empêcher de poursuivre le travail indépendant autorisé. Aucune réussite de test n’est revendiquée si le test n’a pas réellement été exécuté.

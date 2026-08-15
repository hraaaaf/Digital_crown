# ROADMAP — Digital Crown Ordonnance P1

Dernière mise à jour : 2026-08-15

## 1. Scope verrouillé

Cette roadmap concerne **uniquement P1 Ordonnance** du Document Studio.

Hors scope : P2 Devis / Honoraires, P3 Certificat / Document Libre, P4 Échéancier et autres chantiers transverses.

Ne pas élargir ce chantier sans demande explicite.

---

## 2. Objectif de fermeture

Fermer P1 Ordonnance avec preuves séparées :

1. engineering R1→R7 validé ;
2. CI sur baseline courante verte ;
3. responsive exécuté et inspecté sur 1440 / 768 / 390 px ;
4. défauts trouvés corrigés puis recapturés ;
5. fidélité au langage visuel glassmorphique historique vérifiée ;
6. harness de certification temporaire retiré avant merge ;
7. PR mergée ;
8. recertification finale sur `master` ;
9. documentation canonique réalignée.

**Important :** le harness de screenshots rend le vrai composant `DocumentHub`, mais ne constitue pas à lui seul une preuve d'interaction authentifiée dans l'application locale du cabinet. Ne jamais confondre certification engineering, certification visuelle runtime et certification clinique/pharmacologique.

---

## 3. Engineering historique R1 → R7

Statut : **fermé côté engineering**.

### R1 — Cohérence médicament / Maroc-first
- PR #17 mergée
- head certifié : `8063b11b061ea6d1912e1b4e1a0ab8ef1fcb649a`
- CI : `31852032393` SUCCESS
- merge : `e32ab311f72980e0797b93a306c3616a4ff66042`
- revue clinique/pharmacologique qualifiée = gate distinct

### R2 — Persistance protocoles / habitudes
- PR #19 mergée
- head : `ba66457e5f65917f71670e151826062442525200`
- CI : `31852827218` SUCCESS
- merge : `432a95eca05d1d7b9781d2d8e81077f0dcb589f2`

### R3 — Safety orchestration
- PR #20 mergée
- head : `becadcafb4ba0e6a5f4fda10a0053bb92c96fe1e`
- CI : `31853962025` SUCCESS
- merge : `75e4693dc983ba1708914d16432504bea8f0cd8c`
- dette non bloquante connue : appel safety read-only dupliqué dans le parent `DocumentHub`; sémantique fail-closed conservée

### R4 — Dirty-state & actions
- PR #21 mergée
- head : `cdaf28874bc9155d115108bba7548470300c5ca1`
- CI : `31855874418` SUCCESS
- merge : `6a4debe01cf0e0ea78e49ed787cae5e26c4976b8`

### R5 — Fast Prescription UX
- PR #22 mergée
- head : `6de453962668e66be9e26978ec07fc9082afacb7`
- CI : `31878337816` SUCCESS
- merge : `8957635e1bd50d8f44fbcef38c529b3c27f8fb32`

### R6 — Protocoles + Référentiel
- PR #23 mergée
- head : `10751078601c3aa5be728bc263e25a58e856c676`
- CI : `31879112143` SUCCESS
- merge : `6f2b8a22f9cdca25cafe228f266ed46deee8281b`

### R7 — Contexte + Preview premium
- PR #26 mergée
- head : `9a39ecc4d415e59c5457a58638a48ba0c22f81fd`
- CI : `31879649826` SUCCESS
- merge : `2596da527fdd1bee5c6746f645e995f682ca3189`

---

## 4. Recertification engineering post-R7

Baseline historique vérifiée :
- `master` : `52d58f0efc94e68ef45fc12fa7912d15c2830e64`
- CI push : `31889643232`
- résultat : **3/3 jobs SUCCESS**

Conclusion autorisée : engineering Ordonnance recertifié sur cette baseline.

Conclusion non autorisée : clinique certifiée / production ready.

---

## 5. Certification visuelle runtime — passage initial

Branche : `work-20260815-p1-runtime-screenshots`

Harness temporaire utilisé :
- `.github/workflows/p1-runtime-screenshots.yml`
- `frontend/p1-screens.html`
- `frontend/src/p1-screens.tsx`

Run initial :
- `31895624778` SUCCESS
- head `5a617b0512e48ce4f82ca9166a05a3b32fb2c5fb`
- artifact id `9249730845`
- digest `sha256:6f61addfc8f540242fc4c2177967b900530e654c16532e22caac9e8a13a0f896`

Constat initial :
- 1440 px : propre ✅
- 768 px : zones rognées ⚠️
- 390 px : débordements horizontaux significatifs ❌

Défauts trouvés : navigation tabs, saisie rapide, DrugRow et footer.

---

## 6. Correctifs responsive PR #43

PR : **#43 — `P1 Ordonnance — responsive runtime certification fixes`**

Fichiers fonctionnels P1 modifiés :
- `frontend/src/features/admin/DocumentStudio/StudioTabs.tsx`
- `frontend/src/features/admin/DocumentStudio/Forms/QuickEntryBar.tsx`
- `frontend/src/features/admin/DocumentStudio/Forms/DrugRow.tsx`
- `frontend/src/features/admin/DocumentStudio/StudioFooter.tsx`

Correctifs :
- tabs scrollables sans perdre le premier onglet ;
- quick-entry adaptée aux petites largeurs ;
- DrugRow reflow mobile ;
- footer responsive ;
- dernier finding 390 px corrigé au commit `29c7342be73bc08beda411a78847777d9e5e0a8e` afin de conserver entièrement `Aperçu`, `Enregistrer` et `Imprimer`.

---

## 7. Recertification responsive finale

Run exact : `31897556420`

- head : `29c7342be73bc08beda411a78847777d9e5e0a8e`
- résultat : **SUCCESS**
- artifact id : `9250222949`
- digest : `sha256:8ec03b702c3bee57ec30693a0488af60168916e08d5418b2a1005cce208df482`

Inspection visuelle effectuée :
- 1440 px ✅ propre
- 768 px ✅ propre
- 390 px ✅ propre
- aucune action principale rognée
- aucun débordement horizontal destructif observé sur ces captures

Le harness temporaire a ensuite été retiré dans le commit :
- `9fa63992c33c0202c63fc7dbf0ff877c34ce4b00`

Les trois chemins temporaires ne doivent pas être présents dans la PR finale :
- `.github/workflows/p1-runtime-screenshots.yml`
- `frontend/p1-screens.html`
- `frontend/src/p1-screens.tsx`

---

## 8. Audit fidélité glassmorphisme historique

Déclencheur : doute sur une possible perte du design glassmorphique historique après R1→R7 et les correctifs responsive.

### Référence historique
Baseline exacte **pré-PR #17 / pré-R1** :
- commit `5d3f6ecc808993f90ddb7a2d807f2c4e1f7c84ac`

Capture historique isolée :
- branche `audit-20260815-p1-pre-r1-glass`
- run `31897932430` SUCCESS
- artifact id `9250318673`
- digest `sha256:81db7ba5b525413908bb3b9faa84a2d6fc6478da756a6367b22d590c88e511e0`
- capture : `ordonnance-pre-r1-1440.png`

### Vérification code
Les signatures glass historiques sont toujours présentes après PR #43 :
- `DrugRow` conserve `bg-white/60` + `backdrop-blur-xl` ;
- Quick Entry conserve `bg-white/70` + `backdrop-blur-xl` ;
- footer conserve `bg-slate-50/80` + `backdrop-blur-xl` ;
- tabs conservent les surfaces translucides, `bg-white` actif et ombres.

Conclusion : **PR #43 n'a pas supprimé le glassmorphisme techniquement.**

### Comparaison visuelle directe
Finding : **le langage glass est toujours présent mais son effet global est visuellement dilué.**

Cause principale observée : accumulation, au-dessus de la zone prescription, de plusieurs surfaces nouvelles et concurrentes :
- `Contexte patient` ;
- `Sécurité non vérifiée` / état de sécurité ;
- alerte `Forme pharmaceutique` ;
- actions `Mes protocoles` / `Actualiser le contexte`.

La baseline pré-R1 présentait une hiérarchie plus légère avec une grande surface principale `IAmina Intelligence`, davantage d'espace négatif et moins de bandeaux superposés. La version actuelle paraît donc plus **plate / administrative / tableau de contrôle**, malgré la conservation réelle des transparences et blurs.

### Décision
Ce finding devient un **gate visuel avant merge de #43**.

Objectif du correctif : restaurer une hiérarchie glass premium proche de la baseline historique **sans retirer, masquer ni affaiblir aucune information de sécurité**.

Approche recommandée :
1. fusionner visuellement `Contexte patient` + état de sécurité en une seule surface glass principale ;
2. traiter les alertes comme états secondaires intégrés ou chips/panneaux contextuels plutôt que bandeaux pleine largeur successifs ;
3. conserver toutes les informations et actions actuelles ;
4. préserver la lisibilité desktop/mobile et les corrections responsive déjà certifiées ;
5. recapturer 1440 / 768 / 390 puis comparer à la baseline pré-R1.

---

## 9. Critères de fermeture P1

- [x] R1 fermé engineering
- [x] R2 fermé engineering
- [x] R3 fermé engineering
- [x] R4 fermé engineering
- [x] R5 fermé engineering
- [x] R6 fermé engineering
- [x] R7 fermé engineering
- [x] baseline engineering recertifiée par CI
- [x] premier passage screenshot exécuté
- [x] défauts responsive identifiés
- [x] correctifs responsive implémentés dans PR #43
- [x] recapture finale 1440/768/390 SUCCESS
- [x] inspection visuelle finale des 3 captures
- [x] harness/workflow temporaire retiré
- [x] audit historique glassmorphisme exécuté sur baseline pré-R1
- [x] glassmorphisme techniquement confirmé comme conservé
- [x] hiérarchie visuelle glass premium restaurée sans perte de sécurité
- [x] recapture comparative glass 1440/768/390 validée
- [x] CI exacte sur le head final de PR #43 verte
- [x] merge PR #43
- [ ] CI exacte post-merge sur `master` verte
- [ ] `DOCUMENT_STUDIO_ROADMAP.md` mis à jour
- [ ] `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md` mis à jour
- [ ] cohérence documentaire finale vérifiée

### Gate non satisfait par les screenshots
- [ ] interaction authentifiée réellement exécutée/certifiée dans l'application locale du cabinet

Cette case ne doit pas être cochée sur la seule base du harness visuel.

### Gate clinique séparé
La fermeture UX/engineering de P1 ne vaut pas certification clinique/pharmacologique.

---

## 10. État de reprise

### Terminé
- R1→R7 engineering
- baseline engineering post-R7
- découverte des défauts runtime responsive
- correctifs responsive
- recapture finale 1440 / 768 / 390
- inspection visuelle responsive
- retrait du harness temporaire
- audit historique glassmorphisme pré-R1
- comparaison directe ancienne vs actuelle

### En cours
- restauration de la hiérarchie visuelle glass premium du haut de la page Ordonnance

### Restant
1. regrouper visuellement contexte + sécurité sans perte d'information ;
2. réduire l'effet de pile des alertes pleine largeur ;
3. recapturer 1440 / 768 / 390 ;
4. comparer au screenshot pré-R1 ;
5. valider CI exacte-head finale de PR #43 ;
6. merger #43 ;
7. vérifier la CI exacte post-merge sur `master` ;
8. mettre à jour `DOCUMENT_STUDIO_ROADMAP.md` ;
9. mettre à jour `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md` ;
10. vérifier la cohérence documentaire finale ;
11. conserver explicitement non certifiée la case d'interaction authentifiée tant que l'application locale réelle n'a pas été exécutée.

---

## 11. Prochaine action exacte

**Restaurer la hiérarchie glass premium du haut de la page Ordonnance sur la PR #43, sans supprimer aucune donnée de sécurité.**

Puis : recapture 1440 / 768 / 390, comparaison directe à la baseline pré-R1, correction des éventuels écarts, CI finale et merge uniquement après passage propre.

---

## 12. Règles critiques de reprise

- Scope : Ordonnance P1 uniquement.
- Ne jamais annoncer 100 %, terminé, validé ou production ready sans preuve complète.
- Ne jamais transformer un SUCCESS CI en certification clinique.
- Les screenshots doivent être inspectés visuellement, pas seulement générés.
- Le harness de screenshots ne doit pas revenir sur `master`.
- La preuve visuelle via harness ne remplace pas une interaction authentifiée dans l'application locale réelle.
- La sécurité fonctionnelle ne doit jamais être sacrifiée au profit du design glass.
- Toute future conversation peut reprendre en demandant : **« ouvre `ROADMAP_ORDONNANCE_P1.md` et continue à partir de la prochaine action exacte »**.

---

## 13. Closeout UX/engineering P1 — 2026-08-15

### Preuves finales
- PR `#43` mergée sur `master` : `91a2c2efd781fd736ebdc96e9de4f5e3c73c82c8`.
- Head fonctionnel final PR : `9a00f07c4b1dc98776cf03bc17b27c23b50d7a81`.
- CI exacte-head PR : run `31898122575` — **SUCCESS**.
- Audit visuel historique pré-R1 : run `31897932430` — **SUCCESS**, artifact `9250318673`, digest `sha256:81db7ba5b525413908bb3b9faa84a2d6fc6478da756a6367b22d590c88e511e0`.
- Recertification glass finale 1440 / 768 / 390 : run `31898157179` — **SUCCESS**, artifact `9250378182`, digest `sha256:4809953baa1ed5dd49a7b143da694ae13e438394146a2d3c8809be90e39dd6de`.
- Inspection visuelle manuelle des trois captures : **propre**, sans débordement horizontal destructif ni action principale rognée.
- Le langage glassmorphique historique est conservé ; la hiérarchie contexte/sécurité a été regroupée en une surface glass principale sans suppression d'information de sécurité.
- CI push exacte du merge sur `master` : run `31898590067` — **à vérifier avant fermeture complète**.

### Limites explicitement conservées
- L'interaction authentifiée dans l'application locale réelle du cabinet reste **non certifiée** par ces captures isolées.
- La certification clinique/pharmacologique humaine reste un gate séparé.
- Aucun statut `production ready` n'est déduit de cette certification visuelle/engineering.


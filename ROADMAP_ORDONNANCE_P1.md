# ROADMAP — Digital Crown Ordonnance P1

Dernière mise à jour : 2026-08-15

## 1. Scope verrouillé

Cette roadmap concerne **uniquement P1 Ordonnance** du Document Studio.

Hors scope de cette roadmap :
- P2 Devis / Honoraires
- P3 Certificat / Document Libre
- P4 Échéancier
- P5 autres défauts transverses

Ne pas élargir ce chantier sans demande explicite.

---

## 2. Objectif de fermeture

Fermer P1 Ordonnance avec preuves séparées :

1. engineering R1→R7 validé ;
2. CI sur baseline courante verte ;
3. comportement runtime réellement exécuté ;
4. responsive certifié sur 1440 / 768 / 390 px ;
5. défauts trouvés corrigés puis recapturés ;
6. harness de certification temporaire retiré avant merge ;
7. PR mergée ;
8. recertification finale sur `master` ;
9. documentation canonique réalignée.

Ne jamais confondre certification engineering, UX runtime et certification clinique/pharmacologique.

---

## 3. Engineering historique R1 → R7

Statut : **fermé côté engineering**.

### R1 — Cohérence médicament / Maroc-first
- PR #17 mergée
- head certifié : `8063b11b061ea6d1912e1b4e1a0ab8ef1fcb649a`
- CI : `31852032393` SUCCESS
- merge : `e32ab311f72980e0797b93a306c3616a4ff66042`
- La revue clinique/pharmacologique qualifiée reste un gate distinct.

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
- Dette non bloquante connue : appel safety read-only dupliqué dans le parent `DocumentHub`; sémantique fail-closed conservée.

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

## 4. Recertification engineering sur baseline post-R7

Baseline vérifiée avant certification runtime :
- `master` : `52d58f0efc94e68ef45fc12fa7912d15c2830e64`
- CI push : `31889643232`
- résultat : **3/3 jobs SUCCESS**

Conclusion autorisée : **engineering Ordonnance recertifié sur cette baseline**.

Conclusion NON autorisée à ce stade : UX runtime certifiée / clinique certifiée / production ready.

---

## 5. Certification runtime — passage initial

### Harness isolé
Branche : `work-20260815-p1-runtime-screenshots`

Workflow temporaire :
- `.github/workflows/p1-runtime-screenshots.yml`

Entrées temporaires :
- `frontend/p1-screens.html`
- `frontend/src/p1-screens.tsx`

Ces fichiers servent uniquement à la certification et doivent être retirés avant merge final.

### Run initial
- run : `31895624778`
- head : `5a617b0512e48ce4f82ca9166a05a3b32fb2c5fb`
- résultat : **SUCCESS**
- artefact : `p1-ordonnance-runtime-screenshots`
- artifact id : `9249730845`
- digest : `sha256:6f61addfc8f540242fc4c2177967b900530e654c16532e22caac9e8a13a0f896`

Captures :
- 1440 × 1100
- 768 × 1100
- 390 × 844

### Constat visuel initial
- 1440 px : propre / exploitable ✅
- 768 px : onglets et certaines zones rognés ⚠️
- 390 px : débordements horizontaux significatifs ❌

Défauts runtime trouvés :
1. navigation tabs mal contenue sur petit écran ;
2. saisie rapide trop large sur mobile ;
3. ligne médicament ne reflow pas correctement ;
4. footer Aperçu / Enregistrer / Imprimer déborde du viewport.

---

## 6. Correctifs responsive en cours

PR : **#43 — `P1 Ordonnance — responsive runtime certification fixes`**

Branche : `work-20260815-p1-runtime-screenshots`

Head au lancement de la recertification :
- `7c1306eb99d0a2ef4ec0269f70ffd720961bb7a8`

Fichiers fonctionnels P1 modifiés :
- `frontend/src/features/admin/DocumentStudio/StudioTabs.tsx`
- `frontend/src/features/admin/DocumentStudio/Forms/QuickEntryBar.tsx`
- `frontend/src/features/admin/DocumentStudio/Forms/DrugRow.tsx`
- `frontend/src/features/admin/DocumentStudio/StudioFooter.tsx`

Intentions des correctifs :
- tabs scrollables sans perdre le début de la navigation ;
- quick-entry adaptée aux petites largeurs ;
- DrugRow reflow en pile sur mobile tout en conservant tous les contrôles ;
- footer en wrap/stack afin que les actions restent dans le viewport.

---

## 7. Recertification responsive finale — EN COURS

Run exact : `31896537246`

État au moment de cette mise à jour : **queued**.

Ce run doit produire à nouveau :
- 1440 px
- 768 px
- 390 px

Critère de réussite : aucune perte de contrôle, aucun élément essentiel rogné, aucun débordement horizontal destructif, actions principales accessibles.

---

## 8. Critères de fermeture P1

P1 Ordonnance ne peut être déclaré fermé que si TOUS les points ci-dessous sont vérifiés :

- [x] R1 fermé engineering
- [x] R2 fermé engineering
- [x] R3 fermé engineering
- [x] R4 fermé engineering
- [x] R5 fermé engineering
- [x] R6 fermé engineering
- [x] R7 fermé engineering
- [x] baseline engineering recertifiée par CI
- [x] premier runtime screenshot exécuté
- [x] défauts responsive identifiés
- [x] correctifs responsive implémentés dans PR #43
- [ ] recapture finale 1440/768/390 SUCCESS
- [ ] inspection visuelle finale des 3 captures
- [ ] CI complète PR #43 verte
- [ ] retrait du harness/workflow temporaire de screenshots
- [ ] CI après retrait du harness verte
- [ ] merge PR #43
- [ ] CI exacte post-merge sur `master` verte
- [ ] `DOCUMENT_STUDIO_ROADMAP.md` mis à jour
- [ ] `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md` mis à jour
- [ ] cohérence documentaire finale vérifiée

### Gate clinique séparé
La fermeture UX/engineering de P1 **ne vaut pas certification clinique/pharmacologique**. Toute affirmation de sécurité clinique finale requiert la revue qualifiée prévue par la gouvernance clinique.

---

## 9. État de reprise

### Terminé
- R1→R7 engineering
- CI engineering post-R7
- premier passage runtime screenshot
- identification des défauts responsive
- correctifs responsive principaux
- PR #43 ouverte

### En cours
- run `31896537246` de recertification visuelle finale
- CI PR #43

### Restant
1. récupérer et inspecter les nouveaux screenshots ;
2. corriger tout finding résiduel ;
3. répéter capture jusqu'à passage propre ;
4. valider CI PR exacte-head ;
5. supprimer les 3 fichiers temporaires de certification ;
6. revalider CI ;
7. merger #43 ;
8. certifier CI exacte post-merge ;
9. mettre à jour les deux documents canoniques ;
10. vérifier cohérence finale et seulement alors fermer P1.

---

## 10. Prochaine action exacte

**Vérifier le run `31896537246`.**

S'il est SUCCESS :
1. télécharger l'artefact `p1-ordonnance-runtime-screenshots` ;
2. ouvrir les 3 images 1440 / 768 / 390 ;
3. noter chaque finding visuel ;
4. corriger immédiatement tout finding bloquant ou important ;
5. relancer la même certification ;
6. une fois propre, passer au retrait du harness puis au merge.

S'il échoue :
1. lire le job/log exact ;
2. corriger la cause ;
3. relancer sans changer le scope.

---

## 11. Règles critiques de reprise

- Scope : Ordonnance P1 uniquement.
- Ne jamais annoncer 100 %, terminé, validé ou production ready sans preuve complète.
- Ne jamais transformer un SUCCESS CI en certification clinique.
- Les screenshots doivent être inspectés visuellement, pas seulement générés.
- Le harness de screenshots est temporaire et ne doit pas rester sur `master` après certification.
- Toute future conversation peut reprendre en demandant : **« ouvre `ROADMAP_ORDONNANCE_P1.md` et continue à partir de la prochaine action exacte »**.

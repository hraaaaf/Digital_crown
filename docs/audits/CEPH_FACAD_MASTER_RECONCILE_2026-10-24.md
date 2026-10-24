# CEPH × FACAD — réconciliation technique candidate, 2026-10-24

**STATUT: CANDIDATE / DRAFT / CLINICAL NO-GO / MERGE NO-GO / NO DEPLOY.**
Ce document présente une proposition isolée de portage Git : ce n'est ni une preuve de convergence ni une validation médicale.

## Baseline et sources verrouillées

- Dépôt: `hraaaaf/Digital_crown`
- Base master effective de cette proposition: `3ab9885a19c835016c85b16153d3f2b8e3318fe3` (2026-10-24).
- Source de code référence/API/Focus et UI: [PR #1007](https://github.com/hraaaaf/Digital_crown/pull/1007) `a73da68e10855da8b1f315db638575d3cfc9df7d` ; DRAFT historique, non mergée.
- Source des scripts FUE authentifiés: lignée [#1019](https://github.com/hraaaaf/Digital_crown/pull/1019) → [#1024](https://github.com/hraaaaf/Digital_crown/pull/1024) → [#1043](https://github.com/hraaaaf/Digital_crown/pull/1043) → [#1046](https://github.com/hraaaaf/Digital_crown/pull/1046), snapshot final `a102dba35890463d8f4212c49c7bc289c6decee8`.
- Couche sécurité documentaire déjà intégrée par [#994](https://github.com/hraaaaf/Digital_crown/pull/994) (MERGED). Ne PAS recopier la pile source historique [#951](https://github.com/hraaaaf/Digital_crown/pull/951) / [#953](https://github.com/hraaaaf/Digital_crown/pull/953) / [#957](https://github.com/hraaaaf/Digital_crown/pull/957) ; il faut préserver `analysis_id`, `revision`, archivage atomique et exclusions autorisation.

## Composition du candidat

- **15 fichiers préexistants**: portage par hunks exacts PR #1007 sur contenus du master au SHA figé, chaque pré-image unique contrôlée ; moteur runtime/route GET et projection, UI tracing/workbench, workspace, repository/bridge, harness T2 et workflows concernés. Les lignes master sans hunk sont conservées. Toute prétention de compatibilité sémantique dépend des tests.
- **14 fichiers nouveaux PR #1007**: manifestes de références McNamara13, COM10, Ricketts Atlas33 et Gregoret13, module de Focus, panneaux/contrats frontend, tests et deux workflows expérimentaux.
- **13 fichiers nouveaux lignée #1019→#1046**: tests authentifiés FUE-G/H/P1/P2, trois seed/phantom, workflow d'exécution à même HEAD, handovers des essais. Fantôme 0.1 design-mm/px strictement artificiel, **jamais** une calibration anatomique.
- **1 rapport présent**, soit 43 chemins comptabilisés. **`techdoubt.md` master non remplacé**: les 59 lignes historiques de #1007 ne sont pas réappliquées aveuglément ; réserves maintenues dans ce document.

## Ce qui n'est PAS réconcilié ni certifié

1. [#934](https://github.com/hraaaaf/Digital_crown/pull/934) + [#1041](https://github.com/hraaaaf/Digital_crown/pull/1041) restent sur branche source documentaire distincte. Matrice 9 menus / 30 commandes / 7 workflows, 9/30 correspondances de *chaînes code* partielles, 21/30 NOT_PROVEN, 0/7 E2E FACAD↔DC. La preuve #1041 cible `master@372c2366`, et NON ce nouveau candidat : réévaluer source/rights/D3 avant un statut neuf.
2. Modèle SRPose38 `CEPH_DETECTOR_SELECTED=NO`, six HOLD anatomiques Ricketts, goldset expert autorisé et correspondance même-cliché FACAD absents. Aucun droit de représenter les angles bruts comme preuve clinique.
3. Ricketts FACAD 32F/13F ≠ Ricketts Atlas33/Gregoret13 DC. Une présence de lignes par protocole n'est pas une équivalence de calcul/norme.
4. Les droits/isolement D3 FACAD restent non prouvés. Aucune exécution vendor, mutation patient, nouveau consentement, archivage clinique ou déploiement.
5. La réussite historique #1007/#1046 appartient à leurs propres commits. **Aucun PASS hérité** par le commit réconcilié.

## Critères de validation de CE HEAD candidat

- [ ] CI scope exact-HEAD vérifiée, workflow attendu collecté et exécuté, aucun skip inattendu.
- [ ] Backend pytest réel (JWT, étude A/B, révision stale, refus cross-cabinet, profile NC/HOLD).
- [ ] Frontend TypeScript/Vitest vérifiés ; ancienne couche d'archive #994 non régressée.
- [ ] FUE-G/H/P1/P2 au même nouveau SHA : véritable React/FastAPI/Chromium/ONNX38, fixture purement synthétique, édition Undo/Redo/Save/reload, calibration à deux points de conception, aperçu/brouillon PDF source-bound, pas archive.
- [ ] Inspecter les artefacts, captures AFTER 1280×900 et 1600×1000, la validité des étiquettes de provenance, sécurité données synthétiques, et une nouvelle approbation UX humaine si requise. Pas d'auto-approbation.
- [ ] Vérification de source/release cible : aucun flux Vercel ou patient privé, aucun nouveau symptôme de bug clinique, réserve sans collision avec master.
- [ ] Pass finale de confirmation FUE sur le dernier HEAD après correction éventuelle, aucune nouvelle modification masquée.

**Roadmap canonique 41/99** (CEPH 20/60, FACAD 21/39), inchangée. La PR DRAFT ne prouve aucune augmentation. Un merge doit être demandé expressément, un déploiement Vercel également.

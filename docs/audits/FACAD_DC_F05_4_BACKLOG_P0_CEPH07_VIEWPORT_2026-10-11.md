# FACAD F02.4 / F05.4 → CEPH07 — P0 UX : espace de tracé premier écran

**Statut : ISSUE FILE ONLY / NOT REPO ISSUE.** L’API GitHub a répondu `410 Issues has been disabled in this repository` à une tentative de création d’issue le 2026-10-11. Ce fichier remplace le ticket tant que le dépôt n’autorise pas les issues ; ne pas prétendre que F05.4 est fermé.

**Phase :** recherche/comparaison d'abord. Aucun correctif produit n'est autorisé par ce document, pas de merge ni déploiement. Toutes captures Digital Crown sont un cas synthétique non clinique.

## Evidence verrouillée

FACAD : [run #37967170536](https://github.com/hraaaaf/Digital_crown/actions/runs/37967170536), artifact #11634502406, ZIP SHA256 `e8db415cda6c4dbc27cdca1eaa25bd6f6200a95a428c902726998a4fc79c1574`, viewport 1024×768. Référence menu View image SHA256 `17997ea40129336be7f415c24de3e4e3f0555b2e0c81c673b74ae278e69ec4f2`.

Digital Crown : [run #38149915778](https://github.com/hraaaaf/Digital_crown/actions/runs/38149915778) **SUCCESS**, artifact #11706532622, ZIP SHA256 `8f6941042653aabfd6d421d9399e320902ebedb7d86e344c601f869e32f4dc01`, product HEAD `c0d47f4832e6da2211c6f94eb88f0db56fcaebb6`, 24 captures sur quatre viewports (390×844, 768×1024, 1024×768, 1280×900), six modes d'analyse.

Source comparative : [WAVE6, trois différences vérifiées](https://github.com/hraaaaf/Digital_crown/blob/55029abf9427bb5441dc926ca70c6d4e0bdbf9d6/docs/audits/FACAD_DC_WAVE6_OBSERVED_VISUAL_COMPARISON.json).

## BEFORE réellement observé

- **1024×768** : le logiciel FACAD montre simultanément table de valeurs et radiographie sur un cas d'exemple ; Digital Crown place au-dessus une grande zone de contrôles couches/correction et le tracé démarre plus bas.
- **390×844** : dans Digital Crown le panneau de couches est long avant le tracé et empêche d’utiliser immédiatement la plus grande part du canvas. **Comportement FACAD sur mobile inconnu** (ne jamais l'inférer).
- **Mapping fonction** : FACAD menu View `Marker guide / Planned positions / Hard tissue / Markers / Marker names / Ceph/Lines / Analysis / Image / Profile`; DC fixture présente Points/Plans/Dents/Profil/Mesures et six modes. **Les contrôles FACAD n'ont pas été réellement invoqués** ; seuls menus/libellés observés.

## TARGET et gate AFTER — tous REQUIRED avant fermeture produit

1. **Vérifier d'abord que le parcours produit Céphalo est réellement accessible et supporté sur mobile**, y compris WorkstationModeGate/auth ; présence de composants responsives TSX ≠ accessibilité fonctionnelle.
2. À **1024×768**, image tracé et informations numériques essentielles visibles simultanément ; commandes avancées regroupées/repliables avec accès clavier et sans collision.
3. À **390×844**, tracer avant les contrôles secondaires, avec bascule de calques accessible et aucun débordement horizontal.
4. Même exact produit HEAD, même jeu de fixture, mêmes viewports **BEFORE → TARGET → AFTER** en capturant PNG, SHA, DOM, overflow, erreurs runtime, console et usage tactile/clavier ; vérification des modes Steiner, Tweed, McNamara, COM et Ricketts.
5. Confirmer l'absence de changements géométriques, patient, permissions ou F5 superposition engineering gate, tests CI required et revue adversariale sur HEAD exact.
6. **Ne pas inventer de parité médicale** : FACAD Robert vs DC fixture synthétique ≠ même image, coordonnées, calibration, formule ou résultat.

## Restrictions et exact statut

- F02.4 = OPEN (comparaison visuelle partielle, pas preuve behavior vendor).
- F05.4 = OPEN (un seul écart UX confirmé, tickets scientifiques et exports encore manquants ; GitHub Issues disabled).
- F05.1/F05.2/F05.3 = OPEN (pas de même cas / parité vendor).
- D3 = OPEN_RED (pas d'installation FACAD, copié, contourné ou action native).
- Score interne documenté : provenance visuelle **7/10**, parité comportementale **2/10**, numérique clinique **0/10** ; revue non indépendante. `CONVERGED=false`.
- **FACAD 21/39 = 53,8 %** ; **global 41/99 = 41,4 %**. Variation suite à ce ticket : **+0**.

**Next :** quand Issues sont activées, transformer cette fiche en ticket GitHub natif sans duplication, puis exécuter le gate AFTER sur branche produit distincte après transfert FACAD.

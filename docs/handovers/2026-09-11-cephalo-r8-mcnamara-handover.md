# Céphalométrie R8 — McNamara — handover canonique

Date: 2026-09-11

## Goal

Fermer R8 avec un sous-ensemble McNamara strictement source-bound, calibré, fail-closed et audit-ready, sans normes, classification, diagnostic, projection de croissance ni traitement automatique, puis reprendre sur R9 Ricketts / tissus mous sans perdre les invariants scientifiques et runtime.

## État vérifié au handover

Repository: `hraaaaf/Digital_crown`

Branche R8: `feat/cephalo-r8-mcnamara`

PR: `#427` — `feat(cephalo): add R8 McNamara calibrated evidence`

Base `master` exacte: `e700da0950cb0c5f90379b57401fa4ae926ad5af`

HEAD produit certifié avant mise à jour de ce handover: `f7a894ccd7cddb5d9c722e7ae5313d0779074ae1`

Gates exact-head sur `f7a894cc…`:
- CI `#3380` / run `34652007334`: `SUCCESS`
- T2 Runtime Browser Certification `#2363` / run `34652007339`: `SUCCESS`
- M6-I `#1163` / run `34652007332`: `skipped`

PR au dernier contrôle:
- open
- draft
- `mergeable=true`
- aucun commentaire/review bloquant observé
- base et `master` toujours alignés sur `e700da0950…`

IMPORTANT: la mise à jour de ce fichier crée un nouveau HEAD documentaire. Les gates ci-dessus certifient le HEAD produit `f7a894cc…`, pas le commit Markdown ultérieur. Ne jamais présenter le nouveau HEAD documentaire comme certifié sans ses propres checks ou sans séparer le closeout docs du merge produit.

## R8 — ce qui est implémenté

Sous-ensemble McNamara activé:

### `MCNAMARA_CO_A_MM_V1`
- Condylion → A-point
- landmarks: `Co`, `A`
- distance euclidienne en coordonnées source
- unité finale: mm
- calibration obligatoire

### `MCNAMARA_CO_GN_MM_V1`
- Condylion → Gnathion
- landmarks: `Co`, `Gn`
- distance euclidienne en coordonnées source
- unité finale: mm
- calibration obligatoire

### `MCNAMARA_ANS_ME_MM_V1`
- ANS → Menton
- landmarks: `ANS`, `Me`
- distance euclidienne en coordonnées source
- unité finale: mm
- calibration obligatoire

Source primaire utilisée:
- McNamara JA Jr. `A method of cephalometric evaluation.` Am J Orthod. 1984;86(6):449-469. DOI `10.1016/S0002-9416(84)90352-X`.

Aucune norme clinique McNamara n'est activée dans R8.

## Architecture R8

R8 utilise le seam linéaire calibré CRANIOM existant, pas le seam angulaire Steiner/Tweed/Downs.

Fichiers R8 principaux:
- `backend/services/cephalo_mcnamara_geometry.py`
- `backend/services/cephalo_mcnamara_evidence.py`
- `backend/services/cephalo_construction_evidence_adapter.py`
- `backend/services/cephalo_measurement_adapter.py`
- tests R8 dédiés et tests runtime de transition

Règle de composition:
- les constructions McNamara sont ajoutées au wrapper linéaire calibré;
- `analysis_id=MCNAMARA` reste séparé de `CRANIOM`;
- la création, les edits de landmarks, la calibration manuelle et la calibration `AUTO_VERIFIED` repassent par le même seam et rematérialisent R8 sans logique de transition dupliquée.

Compatibilité snapshots:
- snapshot pré-R8 avec zéro construction McNamara: compatible;
- set McNamara partiel: fail-closed / rejet;
- calibration complète requiert à la fois un ratio mm/pixel valide et un `calibration_ref` valide.

## Fail-closed R8

Pour les trois mesures:
- landmark manquant / indisponible → `NOT_COMPUTABLE`
- cross-image → `INVALID`
- segment dégénéré / non fini → `INVALID`
- ratio calibration non fini ou <= 0 → non calculable / invalide selon contrat
- `calibration_ref` et ratio incohérents → `INVALID`
- aucun fallback vers un champ legacy non certifié
- aucune norme, interprétation, diagnostic ou recommandation thérapeutique

## Transition / runtime proof

La preuve R8 couvre:
- création initiale
- edit landmark
- calibration manuelle
- calibration `AUTO_VERIFIED`
- nouvel edit après calibration
- rematérialisation/read path typé

Le moteur legacy `CephaloEngine` n'est pas utilisé comme source de vérité McNamara pour ces trois mesures. La géométrie source-bound est calculée dans l'evidence typée puis calibrée explicitement.

## Incident CI R8 et correction

Premier exact-head réancré: `958a93ecfab5d38bf9220299d61a1f7402003283`.

T2 était vert, mais CI `#3379` a échoué sur un seul test:
`backend/tests/test_cephalo_construction_evidence_adapter.py::test_all_required_landmarks_materialize_certified_constructions`.

Cause prouvée:
- le test CRANIOM historique appelait le wrapper composite `materialize_craniom_linear_constructions`;
- ce wrapper retourne désormais CRANIOM + les 3 constructions McNamara;
- l'assertion exact-set attendait seulement les 7 constructions CRANIOM;
- 481 tests avaient déjà passé avant l'arrêt.

Correction chirurgicale:
- le test CRANIOM pur utilise désormais `materialize_craniom_constructions`;
- son adapter pur utilise désormais `adapt_craniom_measurements`;
- aucune logique produit R8 n'a été modifiée par ce correctif.

HEAD après correction: `f7a894ccd7cddb5d9c722e7ae5313d0779074ae1`.

Preuve finale produit sur ce HEAD:
- CI `#3380`: SUCCESS
- T2 `#2363`: SUCCESS

## Réancrage R8

R8 avait initialement été préparé sur un master plus ancien. Pendant le chantier, `master` a avancé avec le lot d'harmonisation des packs commerciaux.

Le lot R8 a été reconstruit proprement sur:
`e700da0950cb0c5f90379b57401fa4ae926ad5af`

Le réancrage a été vérifié:
- `behind=0`
- diff R8 isolé avant le correctif de test
- aucun chevauchement fonctionnel avec le chantier commercial

Ne jamais réutiliser l'ancien HEAD pré-réancrage comme preuve de merge.

## R8 — blockers résiduels explicites

### A-point → N-perpendicular
État: `BLOCKED_SIGN_CONVENTION`

La primitive géométrique N-perpendicular existe dans le repo, mais la convention McNamara signée antérieur/postérieur n'est pas encore suffisamment verrouillée pour promouvoir un alias clinique source-bound.

### Pogonion → N-perpendicular
État: `BLOCKED_SIGN_CONVENTION`

Même règle: pas de recyclage silencieux d'une primitive générique en mesure McNamara tant que le signe clinique n'est pas versionné et testé.

## Invariants scientifiques hérités R4–R8

Toujours appliquer pour chaque nouvelle mesure:
1. définition scientifique exacte;
2. landmarks exacts et versionnés;
3. géométrie exacte, signe/orientation compris;
4. unité et calibration;
5. runtime legacy audité seulement comme compatibilité/parité, jamais comme autorité implicite;
6. fail-closed missing / unavailable / degenerate / nonfinite / cross-image;
7. transitions création → edit → calibration → edit → read;
8. aucune norme/diagnostic/traitement tant qu'un lot dédié ne l'autorise pas.

ZERO LLM demeure un invariant produit.

Aucun déploiement Vercel n'est requis ni autorisé implicitement pour ce chantier.

## R9 — pré-gate déjà vérifié

Prochain lot roadmap: `R9 Ricketts + tissus mous`.

### Facial angle Ricketts
- géométrie candidate: Frankfort `Po-Or` vs `N-Pog`;
- ressemble au Facial Angle Downs déjà versionné;
- NE PAS aliaser automatiquement: vérifier source Ricketts, orientation et convention avant réutilisation.

### Facial axis Ricketts
- géométrie littéraire: `Ba-N` vs `Pt-Gn`;
- ne pas confondre avec le Y-axis Downs `S-Gn` vs Frankfort;
- SRPose38 expose `Ba`, `Gn` et `PT_point`;
- `PT_point` existe techniquement mais sa sémantique exacte Ricketts n'est pas encore certifiée dans le repo.

État actuel: `BLOCKED_LANDMARK_CONVENTION` jusqu'au verrouillage du `PT_point`.

### Ricketts convexity
- candidate: distance de `A` à la ligne `N-Pog`;
- ne pas confondre avec l'angle de convexité Downs `N-A-Pog`;
- calibration/signe doivent être source-lockés avant code.

### E-line / tissus mous
- landmarks techniques disponibles: `Prn`, `Pog_soft`, `Ls_soft`, `Li_soft`;
- le legacy contient des champs `Ligne_E_Ls/Li`, mais cela ne constitue pas une preuve scientifique suffisante;
- la convention signée antérieur/postérieur doit être source-lockée et miroir-invariante avant promotion typée.

### Mesures nécessitant Xi
- `Xi` n'est pas un landmark SRPose38 actuel;
- toute mesure Ricketts dépendant de `Xi` reste `BLOCKED_LANDMARK`.

## Next exact

### Si l'objectif immédiat est de fermer R8 produit
1. ne pas modifier le code produit certifié `f7a894cc…`;
2. vérifier le HEAD réel de #427 et le `master` réel;
3. si le HEAD produit est encore `f7a894cc…`, que `master=e700da0950…`, CI #3380 et T2 #2363 restent verts: passer #427 ready puis squash merge avec `expected_head_sha=f7a894cc…`;
4. vérifier le SHA de merge et `master` post-merge;
5. traiter ce handover documentaire séparément si sa mise à jour a créé un HEAD distinct.

### Puis R9
1. créer une branche R9 depuis le master post-merge R8 exact;
2. écrire le scientific gate R9 avant code;
3. verrouiller d'abord Facial Angle / Convexity / E-line et la sémantique `PT_point`;
4. ne coder que les mesures dont landmarks + géométrie + signe sont certifiés;
5. tests synthétiques + miroir/orientation + fail-closed + transitions;
6. CI/T2 exact-head;
7. closeout R9 puis R10 normative registry.

## Séquence restante connue

R8 merge produit → closeout/handover docs → R9 Ricketts/soft tissues → R10 normative registry → R11 multiaxial diagnosis → R12 problem list/objectives → R13 treatment options → R14 clinical validation → R15 clinical studio UX/UI → R16 PDF/restitution → R17 certification/closeout.

## Reprise nouvelle fenêtre

Lire en premier:
`docs/handovers/2026-09-11-cephalo-r8-mcnamara-handover.md`

Puis vérifier impérativement, dans cet ordre:
1. `master` réel;
2. état PR #427;
3. HEAD réel de la branche R8 si PR encore ouverte;
4. CI/T2 associés au HEAD exact;
5. seulement ensuite reprendre merge/closeout ou R9.

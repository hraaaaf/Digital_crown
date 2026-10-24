# Digital Crown — V5-G5 : plan d'implémentation du tracé anatomique Bézier (LAB)

**Date :** 2026-10-24. **Autorité clinique : NO-GO / R14 NO-GO.** PR #1048 **DRAFT** seulement. Zéro merge, déploiement, patient réel ou approbation clinique automatique.

## 1. État réellement vérifié

- Le composant `OrthoAnatomicalTraceLabEditor.tsx` sait éditer six polylignes manuelles en pixels originaux 1935×2400 ; zoom 1/2/4/8 et déplacement indépendant de la géométrie ; révision et approbation révoquées à la modification.
- Le contrat serveur `ODF_ANATOMIC_TRACE_V1` accepte strictement six listes de points ordonnés (7 à 16 points minimum par structure, 600 maximum), refusera des points hors image et nécessite un praticien authentifié. Son rendu `draw_contours` utilise PIL `ImageDraw.line`. L'écran et les PDFs sont donc basés sur des **segments**, pas des courbes de Bézier.
- **Apexo (MIT)** : placement manuel de landmarks, lignes et analyses céphalométriques. REA a ouvert la démo publique, mais aucun moteur cutané Bézier n'a été identifié. **FaceX (Apache-2.0)** : démonstration d'interface maillage facial non métrique, pas un CBCT/scan facial ou un moteur d'orthognathie.
- Les masques MedSAM sur Aariz (inférence réelle) sont non concluants anatomiquement. Ne jamais les promouvoir sous `CLINICIAN_MANUAL`.

## 2. Premier commit réalisable sans migration — moteur purement géométrique

Introduire `frontend/src/features/ortho/utils/g5BezierGeometry.ts` : `G5CubicSegment` (start/control1/control2/end en pixels SOURCE), `g5CubicAt`, `g5SampleBezierContour` déterministe ; continuité, contrôles bornés à la radio, points non finis refusés, pas >600 points, pas d'extrapolation à partir des landmarks. Test unitaire Vitest dans `g5BezierGeometry.test.ts`.

Ceci est une **bibliothèque de calcul** ; elle n'est **pas branchée** dans l'éditeur ou l'API. Le succès de cette étape NE VAUT PAS un tracé G5 anatomique.

## 3. Éditeur clinique de recherche — priorité au profil cutané

1. Créer un mode LAB séparé « Courbe Bézier » à côté du dessin brut. Placement explicite des points d'ancrage et de leurs poignées de tangence, déplacement et zoom contrôlés au pointeur (souris/tactile), ajout/retrait de nœud, undo/redo, aperçu de la polyligne exact(e) qui sera enregistrée.
2. Ne pas afficher de « courbe visuelle plus lisse » différente de celle du PDF : **la courbe affichée, stockée, évaluée et imprimée doit être rigoureusement la même** (mêmes échantillons source-pixel). Pas de lissage implicite après signature.
3. Tester en premier `soft_tissue_profile` (front, nez, lèvres, pogonion cutané, menton et cou selon les limites effectivement visibles sur Aariz). Ensuite `cranial_base`, `maxilla`, `mandible`, `upper_incisor`, `lower_incisor`. Chaque structure doit être tracée dans son contexte radiographique réel ; pas de polylignes synthétiques servant de validation anatomique.
4. L'IA éventuelle ne peut suggérer que des points/ROI **non approuvés**. Pas de validation implicite ni de données patients.

## 4. Stockage et deux sorties PDF — gate bloquant avant activation de l'UI

Créer une évolution de contrat versionnée, par ex. `ODF_ANATOMIC_TRACE_V2`, contenant les segments de Bézier éditables ET la polyligne canonique échantillonnée, liée à `patient_id`, `analysis_id`, `revision`, `image_sha256`, `scientific_digest`, `approved_by`, `contour_digest` calculé SERVEUR. Garder la lecture V1 strictement inchangée pour les brouillons existants.

À l'enregistrement, le serveur vérifie indépendamment la continuité, l'ordre, la taille, les bornes et la correspondance exacte `sampled_points` ← `bezier_segments`. À chaque correction : révocation approbation et nouvelle version. L'authentification doit rester celle du praticien.

Un **seul modèle projeté**, à partir des échantillons approuvés, alimente : (A) radio + tracé ; (B) tracé seul sur fond blanc ; et les deux moteurs PDF. Tester par comparaison rigoureuse des chemins/géométries et intégrité de digest. La projection G4 scientifique existante ne doit jamais être transformée en fausse anatomie G5.

## 5. Recette technique et anatomique

- Math : extrémités et continuité au pixel source, zoom ×1/2/4/8 invariant, pas de NaN, pas d'effacement silencieux de points, limites du contrat.
- Interaction : création/édition/manipulation et persistance des poignées ; undo/redo ; chargement après refresh ; revue visuelle à zoom ×8 sans coordonnées dénaturées.
- Sécurité : fail-closed si image/étude/révision changent ; interdiction approbation quand dirty/stale ; A→B isolation ; aucun patient réel ; aucune promotion d'un modèle dans le canal manuel.
- PDF : 2 vues issues de la même géométrie authentifiée. Cas négatif : aucune exportation `ODF_G5_REQUIRE_CONTOURS` avec seul G4 ou un simple masque IA.
- **Anatomie** : comparaison avec six contours tracés/corrigés par un praticien sur une radio de recherche autorisée. La cible visuelle ≥8,5/10 est un objectif **non acquis**, à noter après revue contradictoire, sans déclarer validation clinique globale R14.

## 6. Module 3D distinct et différé

FaceX peut être testé comme **maquette de face mesh** sur image fictive/autorisée sans webcam patient ; son maillage est non métrique. Pour une vraie reconstruction faciale 3D, il faut au minimum des acquisitions adéquates (scan facial OBJ/PLY/GLB et, si visée osseuse/dentaire, CBCT DICOM + scan intra-oral), recalage, mesures d'erreur et consentements. Une téléprofil 2D **ne permet pas** à elle seule la reconstruction 3D médicale fidèle.

## 7. Fermeture de la PR

La demande de fermeture de la PR #1048 est conditionnelle (« once on aura ce qu'on veut »). Ne jamais fermer automatiquement en raison d'un seul test géométrique vert. Conserver le handover, tests, captures, audit, numéros SHA et provenance ; obtenir d'abord un bilan vérifiable du tracé cutané, des six structures, des deux PDF et du statut 3D. **Aucun merge ou déploiement.**

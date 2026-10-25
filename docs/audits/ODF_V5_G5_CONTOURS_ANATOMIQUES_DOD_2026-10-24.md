# Digital Crown — V5-G5 : tracé anatomique orthodontique complet

**Statut : implémentation LAB, blocage clinique maintenu.** Référence : montage fourni par le dentiste (tracé anatomique indépendant et téléradiographie latérale annotée). PR #1048 reste DRAFT.

## Définition d'acceptation (bloquante)

G4 est un rendu géométrique 9 plans, **pas** un tracé anatomique complet. G5 doit fournir, dans la phase 01 du bilan A4, deux vues tirées d'un **même calque de courbes documentées** :

1. téléradiographie de profil + polylignes anatomiques continues + plans de référence ;
2. tracé anatomique seul sur fond blanc (mêmes coordonnées, même géométrie) ; les tableaux osseux et dento-alvéolaires restent associés au même graphe de repères.
3. Phases 02 moulages, 03 résumé diagnostique, 04 plan de traitement demeurent inchangées.

**Les courbes obligatoires** : `cranial_base`, `maxilla`, `mandible`, `upper_incisor`, `lower_incisor`, `soft_tissue_profile`. Les contours réels peuvent être polylignes annotées manuellement ou expertisées. AUCUNE silhouette, racine dentaire ou courbe cutanée ne doit être extrapolée des seuls 24 landmarks d'Aariz.

## Modèle / traçabilité

`ODF_ANATOMIC_TRACE_V1`, `patient_id`, `analysis_id`, `analysis_revision`, `image_sha256`, `scientific_source_digest`, `image_width`, `image_height`, `coordinate_space=image_pixels`, `origin=CLINICIAN_MANUAL`, `contours[]`, `contour_digest`. Pour chaque `contour` : identifiant d'une liste fermée, `points=[[x,y],...]` ordonnés, auteur, version et approbation authentifiée du dentiste.

**Refus obligatoire** : patient/étude/cabinet incorrect, auteur non DENTISTE, image remplacée, graphe de repères révisé, révision différente, courbes incomplètes, points hors image/non finis, doublon de structure, segments dégénérés, dénaturation de coordonnées, contenu du client sans approbation authentifiée. Le digest de source relie le tracé à la projection typée, mais ne valide pas automatiquement un diagnostic clinique R14.

## Pipeline et recette

- API LAB authentifiée pour saisir, relire et **approuver explicitement** un tracé anatomique manuel ; brouillon isolé dans une table dédiée ; révocation de l'approbation à l'édition ; journal d'audit ; aucun impact sur les vrais cabinets.
- PDF WeasyPrint et ReportLab : même rendu anatomique 1) superposition et 2) tracé seul ; contours fins et plans secondaires ; garder toutes les mentions recherche et l'absence de calibration mm.
- Test négatif G5 : aucune figure certifiée avec le seul tracé géométrique G4, ni avec fausses courbes générées automatiquement.
- Test positif G5 : courbes dessinées manuellement/validées **sur la même radio** puis export officiel des 4 phases, inspection visuelle par le dentiste.
- Sans source de six courbes expertisées ou saisie manuelle réelle, **G5 reste NO-GO**, même si le renderer et l'API passent tous leurs tests.

## Restrictions

Ne jamais fusionner / déployer / changer Production ni toucher un vrai patient à ce stade. G4 géométrique peut rester techniquement vert mais G5 est indépendant ; R14 clinique reste NO-GO.

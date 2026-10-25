# Digital Crown — V5-G4 : tracé céphalométrique PDF obligatoire

**Statut : règle bloquante de recette, PR #1048 DRAFT, pas de fusion/déploiement clinique.**  
**Référence visuelle :** image fournie par le chirurgien-dentiste le 24/10/2026 (radiographie latérale et tracé anatomique à gauche).

## Définition métier

Le bilan orthodontique A4 contient toujours les quatre phases :
1. Analyse céphalométrique, avec **figure centrale : téléradiographie latérale ET tracé céphalométrique superposé sur les pixels du même cliché**, puis sous-parties osseuse et dento-alvéolaire.
2. Examen des moulages (relations d'Angle observées, jamais déduites de la téléradiographie).
3. Résumé diagnostique, texte du praticien approuvé.
4. Plan de traitement, texte du praticien approuvé.

**La photographie seule, un nuage de points, un schéma non lié au sujet ou une image figurant en annexe sans tracé ne satisfont pas cette définition.**

### Tracé de première tranche implémentable depuis les 24 repères appariés Aariz

Deux calques sur la *même image* :
- repères anatomiques nommés, à leurs coordonnées exactes, sans déplacement ni transformation supplémentaire ;
- **plans et axes réellement construits par paires de repères persistés** : SN (S–N), Francfort (Po–Or), NA (N–A), NB (N–B), plan mandibulaire Go–Me, Go–Gn si Gn disponible, plan palatin ANS–PNS si disponible, axes des incisives U1 apex–bord incisif et L1 apex–bord incisif ; repères en couleurs différenciées, légende explicite. Une ligne est omise si l'un de ses points manque.

**Les contours anatomiques osseux et tissus mous ne peuvent PAS être déduits fidèlement de ces seuls points.** Une silhouette comme sur l'image de référence demande un véritable contour tracé/validé et lié à cette radiographie ; ne jamais interpoler librement un contour anatomique sous couvert de précision scientifique. La figure doit annoncer la distinction « plans et axes issus des repères » vs « contours anatomiques non disponibles ». L'ajout futur d'un contour validé sera un lot séparé.

## Cohérence et provenance (fail closed)

- Le cliché, les repères, les segments du tracé et les valeurs imprimées dérivent **du même enregistrement patient + étude + révision + graphe d'évidence**. Le laboratoire G3 a un SHA256 de la représentation radiographique et deux SHA256 des annotations experts Aariz.
- Vérification image SHA256 **avant chaque export**. Géométrie des segments calculée exclusivement à partir des landmarks persistés : noms uniques, coordonnées finies, dans le cliché, sans segments arbitraires. Modèle d'image non reconnu, manque de repère obligatoire ou incohérence => **pas d'affichage comme tracé validé**.
- Calculs angulaires disponibles seulement, via convergence méthodes typées/canoniques vérifiées. Aucune distance en mm sans calibration vérifiable.
- La validation des **notes praticien** ne vaut pas validation clinique R14 du calcul scientifique ni validation des contours.

## Rendu et expérience

- **Phase 1, figure principale** avec le cliché et les plans superposés, suffisamment grand, contrasté et accompagné d'une légende ; tableau osseux + tableau dento-alvéolaire immédiatement après, dans le même PDF.
- Habillage de cabinet Swiss / Royal / Clinical / Modern / Heritage, QR et spécialité sur les pages, pagination A4, aucune collision ou page vide/orpheline, lisibilité imprimée et PDF.
- WeasyPrint **et** ReportLab fallback affichent le même JPEG tracé, aux proportions fixes sans distorsion et dans la même phase.
- Rendre « Non calculable » uniquement dans l'audit interne, pas comme long inventaire dans le PDF praticien.
- Aucun « Mesure complémentaire », libellé backend, verdict R14, « pré-bilan », ou diagnostic inventé dans le document praticien.

## DoD/tests obligatoires

1. Test positif image Aariz appariée/expertise : le PDF applicatif affiche une **figure avec segments SN/FH/NA/NB/Go–Me/axes incisifs** et légende **avant la phase 02**.
2. Test adversarial : image remplacée, digest divergent, point hors champ, doublon, angle/méthode d'évidence forgé, étude/révision différente => refus d'afficher le faux tracé/des faux chiffres.
3. Matrice de recette : cinq styles, deux moteurs PDF, nombre et position des images vérifiés, OCR non nécessaire ; inspections visuelles des rendus.
4. Première expérience laboratoire JWT complète : sélection patient test, moulages fictifs, validation explicite praticien, export PDF ; refus secrétaire, anonyme, autre étude.
5. Revue par le dentiste du tracé et des tableaux sur le vrai cliché G3, avec comparaison visuelle à la référence fournie.
6. **G4 NO-GO tant que la preuve du tracé dans l'export officiel et la cohérence des mesures n'est pas contrôlée.** G3 / R14 restent des gates séparées.

Rien ne doit être fusionné/déployé sans approbation explicite et sans résolution des gates cliniques.

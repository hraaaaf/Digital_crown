# Céphalométrie R6 — Tweed / Merrifield scientific gate

Date: 2026-09-11

## Goal
Versionner uniquement les géométries patient Tweed/Merrifield scientifiquement sourcées, fail-closed et auditables, sans norme, classification, diagnostic ni traitement.

## Sources vérifiées
1. Tweed CH. The Frankfort-mandibular plane angle in orthodontic diagnosis, classification, treatment planning, and prognosis. Am J Orthod Oral Surg. 1946;32:175-230. DOI: 10.1016/0096-6347(46)90001-4.
2. Tweed CH. The Frankfort-Mandibular Incisor Angle (FMIA) in Orthodontic Diagnosis, Treatment Planning and Prognosis. Angle Orthod. 1954;24:121-169.
3. Merrifield LL. The profile line as an aid in critically evaluating facial esthetics. Am J Orthod. 1966;52(11):804-822. DOI: 10.1016/0002-9416(66)90250-8.
4. Corroboration peer-reviewed moderne: le Z-angle est décrit comme l'angle entre Frankfort et la ligne du pogonion cutané au point le plus antérieur de la lèvre la plus protrusive (supérieure ou inférieure), voir *The Correlation of a Novel Photographic Parameter for Facial Profile Assessment in Subjects With Different Sagittal Malocclusions: A Prospective Study*, 2023, PMC10544775.
5. Corroboration clinique indépendante: *Treatment decision in adult patients with class III malocclusion: surgery versus orthodontics*, 2018, PMC6070451, définit également le Z-angle par le pogonion cutané, la lèvre la plus protrusive et le plan de Frankfort.

## Contrats géométriques R6 retenus
### FMA
- plan Frankfort: Po-Or;
- plan mandibulaire: Go-Me;
- unité: degré;
- calibration: non requise;
- runtime existant: `metrics.analyse_osseuse.Angle_de_Tweed`;
- le runtime actuel calcule `_get_clinical_angle(Go, Me, Po, Or)` puis arrondit à 0,1°;
- la preuve typée doit donc préserver exactement cette convention d'orientation canonique pour la parité runtime.

### IMPA
- axe incisive mandibulaire: L1 apex -> L1 incisal;
- plan mandibulaire: Go-Me;
- unité: degré;
- calibration: non requise;
- runtime existant: `metrics.analyse_dentaire.IMPA`;
- convention runtime actuelle: `180 - _get_clinical_angle(L1a, L1i, Go, Me)`, puis arrondi à 0,1°.

### FMIA
- plan Frankfort: Po-Or;
- axe incisive mandibulaire: L1 apex -> L1 incisal;
- angle patient calculé directement à partir des axes, pas dérivé de `180 - FMA - IMPA`, afin d'éviter de propager les conventions/arrondis des champs historiques;
- angle minimal orientation-invariant;
- unité: degré;
- calibration: non requise;
- aucun champ runtime legacy dédié n'est actuellement identifié.

### Merrifield Z-angle
- plan Frankfort: Po-Or;
- profile line: point du menton cutané `Pog_soft` vers le point le plus antérieur entre `Ls_soft` et `Li_soft`;
- la lèvre la plus protrusive doit être sélectionnée par projection sur l'axe anatomique antérieur Po→Or, pas par simple comparaison de x image;
- angle minimal entre profile line et Frankfort;
- unité: degré;
- calibration: non requise;
- aucun champ runtime legacy dédié n'est actuellement identifié.

## Fail-closed obligatoire
Pour FMA / IMPA / FMIA / Z-angle:
- landmark manquant -> `NOT_COMPUTABLE`;
- géométrie dégénérée -> `INVALID`;
- landmarks provenant de sources/images différentes -> `INVALID`;
- valeurs non finies -> refus;
- aucun fallback silencieux sur des alias non certifiés;
- égalité géométrique non résoluble entre Ls et Li pour la protrusion -> `INVALID` sauf points confondus.

## Double-check runtime obligatoire
Avant activation:
1. comparer FMA typé au runtime `Angle_de_Tweed` sur plusieurs fixtures;
2. comparer IMPA typé au runtime `IMPA` avec l'ordre exact des opérations et arrondis;
3. tester FMIA directement par géométrie, orientation inversée des deux axes et relation triangulaire uniquement comme contrôle secondaire;
4. tester Z-angle avec upper lip puis lower lip comme point dominant, et vérifier l'invariance au miroir/convention d'axe image;
5. vérifier création -> landmark edit -> calibration -> nouvel edit -> read path.

## Exclusions R6
- aucune norme Tweed/Merrifield;
- aucun seuil 65°, 75-80°, etc. utilisé pour classer le patient;
- aucun diagnostic facial;
- aucune recommandation d'extraction ou traitement;
- aucune projection de croissance.

## Safety
ZERO LLM. Aucun déploiement Vercel. Les mesures restent des géométries patient observées/versionnées uniquement.

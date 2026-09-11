# Céphalométrie R6 — Tweed / Merrifield scientific gate

Date: 2026-09-11

## Goal
Versionner uniquement les géométries patient Tweed/Merrifield scientifiquement sourcées, fail-closed et auditables, sans norme, classification, diagnostic ni traitement.

## Sources vérifiées
1. Tweed CH. The Frankfort-mandibular plane angle in orthodontic diagnosis, classification, treatment planning, and prognosis. Am J Orthod Oral Surg. 1946;32:175-230. DOI: 10.1016/0096-6347(46)90001-4.
2. Tweed CH. The Frankfort-Mandibular Incisor Angle (FMIA) in Orthodontic Diagnosis, Treatment Planning and Prognosis. Angle Orthod. 1954;24:121-169.
3. Merrifield LL. The profile line as an aid in critically evaluating facial esthetics. Am J Orthod. 1966;52(11):804-822. DOI: 10.1016/0002-9416(66)90250-8.
4. Corroboration moderne: FMA = FH vs mandibular plane; FMIA = FH vs lower-incisor long axis; IMPA = lower-incisor long axis vs mandibular plane; Z-line = soft-tissue chin to the most protrusive lip, Z-angle = Z-line vs FH.

## Contrats géométriques R6 retenus
### FMA
- plan Frankfort: Po-Or;
- plan mandibulaire: Go-Me;
- angle minimal orientation-invariant entre les deux axes;
- unité: degré;
- calibration: non requise;
- runtime existant: `metrics.analyse_osseuse.Angle_de_Tweed`;
- le runtime actuel calcule `_get_clinical_angle(Go, Me, Po, Or)` puis arrondit à 0,1°.

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
- unité: degré;
- calibration: non requise;
- aucun champ runtime legacy dédié n'est actuellement identifié.

### Merrifield Z-angle
- plan Frankfort: Po-Or;
- profile line: point du menton cutané `Pog_soft` vers le point le plus antérieur entre `Ls_soft` et `Li_soft`;
- la lèvre la plus protrusive doit être sélectionnée par projection sur l'axe antérieur dérivé de Frankfort, pas par simple comparaison de x image;
- angle entre profile line et Frankfort;
- unité: degré;
- calibration: non requise;
- aucun champ runtime legacy dédié n'est actuellement identifié.

## Fail-closed obligatoire
Pour FMA / IMPA / FMIA / Z-angle:
- landmark manquant -> `NOT_COMPUTABLE`;
- géométrie dégénérée -> `INVALID`;
- landmarks provenant de sources/images différentes -> `INVALID`;
- valeurs non finies -> refus;
- aucun fallback silencieux sur des alias non certifiés.

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

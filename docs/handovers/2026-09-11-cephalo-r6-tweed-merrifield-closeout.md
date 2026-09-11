# Céphalométrie R6 — Tweed / Merrifield closeout

Date: 2026-09-11

## Goal
Certifier des géométries patient Tweed/Merrifield versionnées, source-bound et fail-closed, sans norme, classification, diagnostic ni traitement.

## État vérifié
- PR #422 fusionnée.
- HEAD exact certifié avant fusion: `b07c98d717e7daa8c9dc27fec9e96b66d9eecb5f`.
- CI #3356: SUCCESS.
- T2 #2344: SUCCESS.
- squash merge sur master: `8e9f89bfa006534518d940f877725df41c020668`.

## Contrats R6 fusionnés
- `TWEED_FMA_V1` / `TWEED_FMA_DEG_V1`: Go-Me vs Po-Or, parité stricte avec le runtime `Angle_de_Tweed`.
- `TWEED_IMPA_V1` / `TWEED_IMPA_DEG_V1`: axe L1 apex->incisal vs Go-Me, convention runtime et ordre des opérations conservés, parité stricte avec `IMPA`.
- `TWEED_FMIA_V1` / `TWEED_FMIA_DEG_V1`: géométrie directe FH vs axe L1, non dérivée de 180-FMA-IMPA.
- `MERRIFIELD_Z_ANGLE_V1` / `MERRIFIELD_Z_ANGLE_DEG_V1`: Frankfort vs ligne Pog' -> lèvre la plus protrusive, sélection de la lèvre selon la direction anatomique Po->Or.

## Preuves comportementales
- parité FMA/IMPA avec runtime legacy;
- FMIA calculé directement et invariant à l'orientation des axes;
- contrôle secondaire du triangle Tweed;
- Z-angle testé avec lèvre supérieure puis inférieure dominante et miroir;
- fail-closed missing / cross-image / géométrie dégénérée;
- création -> édition landmarks -> calibration manuelle -> préservation/rematérialisation;
- aucune calibration requise pour ces angles.

## Sources
1. Tweed CH. The Frankfort-mandibular plane angle in orthodontic diagnosis, classification, treatment planning, and prognosis. Am J Orthod Oral Surg. 1946;32:175-230. DOI: 10.1016/0096-6347(46)90001-4.
2. Tweed CH. The Frankfort-Mandibular Incisor Angle (FMIA) in Orthodontic Diagnosis, Treatment Planning and Prognosis. Angle Orthod. 1954;24:121-169.
3. Merrifield LL. The profile line as an aid in critically evaluating facial esthetics. Am J Orthod. 1966;52(11):804-822. DOI: 10.1016/0002-9416(66)90250-8.

## Safety
ZERO LLM. Aucun Vercel. Aucune norme, seuil clinique, classification, diagnostic, recommandation d'extraction ou traitement activé.

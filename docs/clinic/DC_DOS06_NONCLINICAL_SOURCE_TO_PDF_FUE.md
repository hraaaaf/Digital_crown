# DC-DOS-06 — FUE non clinique : octets → repères → géométrie → PDF

**Statut : candidate isolée, jamais activée cliniquement.**

## Objectif & périmètre

Le PDF de l'application principale emploie encore `CephaloAnalysis.image_original_path` pour charger la radio et un enregistrement photo T0 indépendant. L'association explicite et cryptographique DC-DOS-05 ne garantit pas que ses mesures proviennent de ces pixels. Aucune preuve rétroactive ne peut être déduite.

La tranche DC-DOS-06 effectue un **essai réellement causal sur image SYNTHÉTIQUE**, sans ONNX clinique : une radiographie fictive PNG dotée de 38 marqueurs codés par couleur est enregistrée/chiffrée dans Media Core ; son ID, SHA-256, patient/cabinet/étude et révision sont liés au contrat DC-DOS-05 ; le décodage des **octets déchiffrés réels** produit 38 coordonnées ; le moteur géométrique `cephalo_safe_engine.calculate_metrics` calcule les valeurs ; un PDF **NON CLINIQUE, NON OFFICIEL, NON SIGNÉ** imprime les empreintes de la source, des landmarks, des mesures et du manifeste **et les valeurs géométriques synthétiques brutes SNA, SNB, ANB et IMPA**, sans interprétation normative.

## Éléments vérifiables

- FUE JWT/FastAPI réel, DB SQLite isolée ; aucune donnée patient réelle.
- Rejet A/B, cabinet X, étude non liée, revision stale, source rebind, contenu/media SHA falsifié, scientifique non vérifié, image sans marqueurs, accès API hors gate test.
- L'altération contrôlée d'un seul repère dans une nouvelle image source modifie réellement les coordonnées, l'empreinte du calcul et celle du PDF.
- Le PDF est généré via ReportLab puis rouvert et rasterisé avec PyMuPDF (preuve d'un PDF réel, et non d'un JSON/UI fictifs).
- Contrôles de CI exact-HEAD et comparaison des empreintes SHA en lisant l'artefact PNG/PDF, sans revue visuelle manuelle supplémentaire.

## Limites obligatoires

**Ce FUE ne démontre PAS** l'authenticité d'un modèle d'inférence ONNX, la précision de repères anatomiques réels, l'autorité d'une calibration, ni la provenance des calculs/PDF existants. Les résultats ne peuvent pas être utilisés pour un diagnostic ou un traitement : `model_onnx_executed=false`, `existing_clinical_measurements_source_proven=false`, `clinical_release=false`, `official_pdf=false`.

Le code ne monte aucun endpoint dans le runtime : `backend/routers/__init__.py` reste inchangé et le routeur est monté temporairement par le FUE, uniquement en test isolé avec `DC_DOS06_FUE_ONLY=1`. Aucune nouvelle table ni migration, aucune fusion ni mise en production.

**Next exact** : passer le FUE GitHub sur HEAD exact puis, sous gate clinique/sécurité approuvé, concevoir la chaîne réelle d'inférence ONNX → graphe d'évidence persisté → PDF clinique signé avec source et révision immuables. Ne jamais promouvoir le détecteur de couleurs à l'utilisation clinique.

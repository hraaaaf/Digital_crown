# FACAD 3.14 — adjudication C02 de l'artefact officiel #11688004374 (2026-10-11)

**Objectif :** poursuivre la collecte FACAD avant tout chantier de parité Digital Crown. **Source :** [run Windows #38102158028](https://github.com/hraaaaf/Digital_crown/actions/runs/38102158028), artefact `facad-c02-minimal-source-page-index-21c2615da54938b00a728dc7d231e19e9777e714`, ZIP SHA256 `d121d062920dea17cecb5ff43c778a93681283530b21a582f044b9f9186d0bd3`, téléchargé et ouvert localement.

## Constat vérifié

L'archive contient exactement trois membres : `c02-pdf-minimal-index.json`, `c02-landmark-cooccurrence.json`, `installed-manual-status.txt`. L'index couvre **34 pages** et comporte 34 SHA256 de texte extrait, sans republier le PDF propriétaire. Le PDF officiel C02 est identifié comme `C02_Lateral Cephalometry Library - Measurements.pdf`, source SHA256 `4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548`, 5 718 901 octets. L'index indique `pdf_text_layer_pages_ge_80chars=34`.

Les correspondances lexicales strictes (et **non des formules**) : `SNA`, `SNB`, `ANB` pages 1 et 5 ; `InterIncisal` pages 1 et 10 ; `PFH` pages 2, 19 et 20 ; `Max-Mand` pages 3, 22 et 30 ; `Xi` et `CF` pages 3 et 24. Les tokens `Angle3p`, `Angle2ln`, `Angle4p`, `Dist2p`, `Dist3p`, `DistLine`, `ProjLine`, `Proj90Line`, `Steiner`, `Ricketts`, `Tweed` sont **non trouvés comme mots entiers dans cet index**, ce qui **ne prouve pas** leur absence dans FACAD ni dans les autres manuels.

La cooccurrence des repères est déclarée `SAME_EXTRACTED_LINE_LEXICAL_ONLY`. Pour les libellés SNA/SNB/ANB en page 5, chaque ligne trouvée contient seulement 3 caractères ; **aucune dépendance landmark prouvée**. Le fait que Xi et OL figurent sur certaines lignes n'est pas une règle de calcul. L'archive marque `formula_definition_verified=false`, `landmark_dependencies_verified=false`, `numeric_parity_verified=false`, `clinical_equivalence_certified=false`.

Le statut indique `NO_PATIENT_READ_OR_EXPORT=true`, `F01_13_CLINICAL_APP_INTERACTION=false`, `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `C02_MINIMAL_INDEX_DONE=true`. Ce run ne valide aucune interaction de mesure FACAD.

## Revue adversariale interne (non indépendante)

- **Perspective A — science/provenance : 9/10 pour intégrité du catalogue lexical, 0/10 pour validation de formules**. Échec majeur évité : inférer une formule de SNA/SNB/ANB à partir d'une page qui ne donne qu'un libellé.
- **Perspective B — sécurité/exécution : 8/10 pour absence de données patient et artefact borné, 2/10 pour preuve de comportement UI réel**. Blocage inchangé : D3 stockage applicatif non isolé.

**Verdict :** enrichissement des preuves documentaires uniquement. `F01.13=OPEN`, `F02.2=OPEN`, `F02.3=OPEN`, `F04.1=OPEN_PARTIAL`, `FAC03_D3=OPEN_RED`, `FAC05=NOT_TESTED`, `CLINICAL_EDIT_ALLOWED=false`. Aucun jalon clôturé par ce nouvel index. Roadmap FACAD `19/39=48,7%` et globale `39/99=39,4%` inchangées.

**Next FACAD exclusivement :** récupérer les passages de définition réellement disponibles dans le C02 sous droit d'accès autorisé, les lier aux mesures du catalogue sans extrapoler ; obtenir une nouvelle session Quick Demo autorisée pour vérifier en lecture seule les surfaces `Values`, `Properties`, `Marker Positions`, `Object Values`, avec captures BEFORE/AFTER mêmes viewports. Ne pas activer de Save/Load/Export ou mutation tant que D3 reste OPEN_RED. Aucun travail sur le runtime Digital Crown.

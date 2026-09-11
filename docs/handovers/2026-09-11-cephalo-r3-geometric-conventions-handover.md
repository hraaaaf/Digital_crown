# DIGITAL CROWN — CÉPHALOMÉTRIE R3 — CONVENTIONS GÉOMÉTRIQUES

## Statut

R3 actif. Implémentation initiale prête pour certification CI/T2. Aucun diagnostic, norme, indication ou traitement n'est ajouté par ce lot.

## Goal

Rendre les conventions géométriques CRANIOM actuelles explicites, versionnées et impossibles à confondre avant toute extension COM/CRANIOM.

## Succès attendu

- chaque construction CRANIOM exécutable possède exactement une convention active ;
- le repère géométrique, l'opération, les landmarks requis et les sources sont matérialisés avec `ConstructionEvidence` ;
- `A'B'` sur Frankfort reste distinct de `A''B''` horizontal-gaze/NHP ;
- Gi/Gs ne sont jamais remplacés silencieusement par Go/Ar ;
- toute construction CRANIOM inconnue échoue fermée.

## État implémenté

Branche : `feat/cephalo-r3-geometric-conventions`
Base : `8a001b2d213ecec1beeed6f5239411f3fd58320e`

Fichiers runtime :
- `backend/services/cephalo_geometric_conventions.py`
- `backend/services/cephalo_construction_evidence_adapter.py`

Tests :
- `backend/tests/test_cephalo_geometric_conventions.py`

Les quatre constructions actuellement exécutables restent :
- `CRANIOM_A_TO_N_VERTICAL_V1`
- `CRANIOM_B_TO_N_VERTICAL_V1`
- `CRANIOM_AB_PRIME_V1`
- `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1`

Elles sont toutes liées explicitement au repère `FH_PO_OR_V1`.

Contrats bloqués :
- `CRANIOM_AB_DOUBLE_PRIME_HORIZONTAL_GAZE_V1` : non constructible tant qu'un protocole horizontal-gaze/NHP validé n'existe pas dans le runtime ;
- `CRANIOM_GI_GS_MANDIBULAR_FRAME_V1` : non constructible tant que Gi/Gs ne sont pas disponibles comme landmarks runtime explicites.

## Sources enregistrées

- DOI `10.1051/odfen/2010406`
- DOI `10.1051/odfen/2011104`

Le registre source ne remplace pas une validation externe experte des conventions futures. Il interdit surtout l'approximation silencieuse avec un autre repère ou un autre landmark.

## Safety contract

- ZERO LLM préservé ;
- aucune norme patient ;
- aucune interprétation diagnostique ;
- aucune indication thérapeutique ;
- aucune substitution de landmarks non équivalents ;
- aucune activation de `A''B''` sans protocole de référence explicite.

## Preuve requise avant fermeture R3

1. tests ciblés R3 verts ;
2. suite backend/CI verte sur exact HEAD ;
3. T2 verte si déclenchée ;
4. revue du diff sans thread bloquant ;
5. merge avec expected-head ;
6. vérification post-merge de `master`.

## Next exact

Certifier l'exact HEAD de la PR R3. Si vert, fermer et merger R3. Si rouge, diagnostiquer le job fautif, corriger et recertifier.

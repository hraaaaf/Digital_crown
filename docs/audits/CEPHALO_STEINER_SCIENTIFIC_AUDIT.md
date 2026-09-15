# CEPHALO STEINER SCIENTIFIC AUDIT — MONEYO GATE

**Statut :** AUDIT STEINER TERMINÉ — MONEYO REQUIS AVANT CODE CLINIQUE  
**Branche d'audit :** `audit/cephalo-scientific-completeness`  
**Baseline scientifique auditée :** `0097e3a08340f753803a86d2a1134880ad9ce902`  
**Master vérifié pendant l'audit :** `7cadce0a6ccdfc650f18ce0601c091ee58542832`  
**Dérive vérifiée :** aucune modification trouvée entre ces deux SHA sous `backend/services/cephalo*`, `backend/tests/test_cephalo*`, `frontend/src/features/ortho/Cephalo*` ou `docs/CEPHALO*`.  
**Nature du lot :** audit/documentation uniquement. Aucun calcul, norme, diagnostic, DB, patient, document ou comportement UI n'est modifié ici.

---

## 0. Goal / Success / Proof

### Goal

Définir **Steiner uniquement**, mesure par mesure, et déterminer :

1. ce qui est déjà source-locké et calculé dans Digital Crown ;
2. ce qui existe dans l'evidence graph mais n'est pas exposé par R19 ;
3. ce qui est réellement absent ;
4. ce qui exige un landmark ou une convention supplémentaire ;
5. le plus petit lot de code scientifiquement sûr à autoriser après MONEYO.

### Success observable

- source primaire Steiner identifiée ;
- source clinique secondaire/indépendante utilisée pour contrôle ;
- matrice mesure → source → landmarks → formule → backend → tracing → UI → statut ;
- aucune norme universelle inventée ;
- aucune convention d'incisive ou de plan occlusal choisie silencieusement ;
- S1 limité à des méthodes **déjà implémentées et typées** ;
- S2/S3 explicitement bloqués jusqu'à un nouveau source-lock/MONEYO.

### Proof repo

Fichiers principaux vérifiés :

- `backend/services/cephalo_steiner_geometry.py`
- `backend/services/cephalo_steiner_evidence_adapter.py`
- `backend/services/cephalo_steiner_dental_evidence.py`
- `backend/services/cephalo_runtime_evidence.py`
- `backend/services/cephalo_typed_read.py`
- `backend/tests/test_cephalo_runtime_evidence.py`
- `frontend/src/features/ortho/CephaloTracingLayer.tsx`
- `frontend/src/features/ortho/CephaloTracingLayerBase.tsx`
- `frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx`
- `docs/SRPOSE38_LANDMARK_CONTRACT.md`

Le test de persistance `test_cephalo_runtime_evidence.py` verrouille exactement six méthodes Steiner disponibles dans un snapshot SRPose38 valide :

```text
STEINER_SNA_DEG_V1
STEINER_SNB_DEG_V1
STEINER_ANB_DEG_V1
STEINER_SN_MP_DEG_V1
STEINER_U1_NA_DEG_V1
STEINER_L1_NB_DEG_V1
```

Ces six mesures sont sans calibration linéaire et doivent être `AVAILABLE` avec une valeur dans le scénario certifié du test.

---

## 1. Source lock Steiner

### Primaire canonique

**Steiner CC. _Cephalometrics for you and me_. American Journal of Orthodontics. 1953;39(10):729-755. DOI `10.1016/0002-9416(53)90082-7`.**

Source primaire historique de l'analyse.

### Extension clinique primaire

**Steiner CC. _Cephalometrics in clinical practice_. Angle Orthodontist. 1959;29:8-29.**

Cette extension est utilisée par Digital Crown comme seconde référence historique pour les éléments Steiner versionnés.

### Contrôle scientifique indépendant

La littérature peer-reviewed contemporaine reproduit les familles classiques :

- SNA ;
- SNB ;
- ANB ;
- SN-GoGn ;
- plan occlusal/SN ;
- U1-NA angle et distance ;
- L1-NB angle et distance ;
- interincisal ;
- Pog-NB/SND dans des implémentations étendues.

Les études populationnelles montrent que les distributions numériques varient avec population, âge et parfois sexe. Par conséquent, **aucune valeur numérique de référence n'est activée dans S1**.

### Point critique sur U1-NA mm / L1-NB mm

Des publications de reproductibilité montrent qu'une implémentation mesurant depuis le **bord incisif** au lieu de la **surface vestibulaire/faciale de l'incisive** peut être scientifiquement incorrecte pour la distance linéaire Steiner.

Digital Crown SRPose38 fournit `U1_incisal`, `U1_apex`, `L1_incisal`, `L1_apex`, mais **aucun landmark explicite de surface vestibulaire maximale de la couronne**.

Conclusion : ne pas fabriquer U1-NA mm / L1-NB mm à partir du tip incisif uniquement.

---

## 2. Version Steiner proposée

### `STEINER_CORE_V1`

Le premier contrat clinique Digital Crown doit contenir seulement les six méthodes déjà typées et source-référencées :

1. SNA
2. SNB
3. ANB
4. SN-GoGn
5. U1-NA angle
6. L1-NB angle

**Aucune norme. Aucune interprétation. Aucun compromis Steiner. Aucun objectif thérapeutique.**

Le rôle de S1 est uniquement de rendre cette géométrie existante cohérente de bout en bout :

`landmarks → construction evidence → measurement evidence → authoritative read → Workbench → tracing`.

---

## 3. Landmarks disponibles

### Pour `STEINER_CORE_V1`

Tous les landmarks requis existent dans SRPose38 :

- `S`
- `N`
- `A`
- `B`
- `Go`
- `Gn`
- `U1_apex`
- `U1_incisal`
- `L1_apex`
- `L1_incisal`

Aucun nouveau landmark n'est nécessaire pour S1.

### Extensions

- `D_point` existe par nom dans SRPose38, mais son identité exacte avec le point D de Steiner doit rester source-lockée avant SND.
- `Pog` est disponible pour Pog-NB.
- U1/L1 ont axe tip-apex, mais pas de point explicite de surface vestibulaire maximale pour les distances linéaires strictes.
- SRPose38 possède `U6/L6`, mais cela ne suffit pas à choisir silencieusement la définition historique exacte du plan occlusal Steiner.

---

## 4. Matrice Steiner

Statuts autorisés : `COMPLETE`, `MISSING`, `CALCULATED BUT NOT DISPLAYED`, `DISPLAYED BUT NOT CALCULATED`, `TRACED BUT NOT MEASURED`, `NON SOURCE-LOCKED`, `IMPOSSIBLE WITH CURRENT LANDMARKS`.

| MEASURE | SOURCE | LANDMARKS | PLAN / LINE | GEOMETRIC FORMULA | UNIT | NORM | AGE/SEX/POP | CURRENT BACKEND | CURRENT TRACING | CURRENT UI | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SNA | Steiner 1953 | S,N,A | SN / NA | angle source-spécifique SN↔NA | ° | aucune active | références populationnelles | raw + typed evidence | SN + NA | row Steiner | COMPLETE |
| SNB | Steiner 1953 | S,N,B | SN / NB | angle source-spécifique SN↔NB | ° | aucune active | références populationnelles | raw + typed evidence | SN + NB | row Steiner | COMPLETE |
| ANB | Steiner 1953 | S,N,A,B | NA / NB | convention V1 parity-bound SNA−SNB | ° | aucune active | dépendance morphologique/pop | raw + typed evidence | NA + NB | row Steiner | COMPLETE |
| SN-GoGn | Steiner 1953/1959, DC V1 | S,N,Go,Gn | SN / Go-Gn | angle entre axes SN et Go-Gn | ° | aucune active | âge/population | typed evidence `STEINER_SN_MP_DEG_V1` | Go-Gn absent du mode Steiner R19 | absent | CALCULATED BUT NOT DISPLAYED |
| U1-NA angle | Steiner 1953/1959 | U1 apex/tip,N,A | axe U1 / NA | angle axe incisif↔NA | ° | aucune active | population | typed evidence `STEINER_U1_NA_DEG_V1` | axe U1 non exposé en mode Steiner | absent | CALCULATED BUT NOT DISPLAYED |
| L1-NB angle | Steiner 1953/1959 | L1 apex/tip,N,B | axe L1 / NB | angle axe incisif↔NB | ° | aucune active | population | typed evidence `STEINER_L1_NB_DEG_V1` | axe L1 non exposé en mode Steiner | absent | CALCULATED BUT NOT DISPLAYED |
| U1-NA distance | Steiner étendu | surface faciale U1,N,A | U1 facial→NA | distance perpendiculaire source-stricte | mm | aucune | population | absent | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| L1-NB distance | Steiner étendu | surface faciale L1,N,B | L1 facial→NB | distance perpendiculaire source-stricte | mm | aucune | population | absent | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| Interincisal | Steiner | U1 apex/tip,L1 apex/tip | axe U1 / axe L1 | angle axes incisifs | ° | aucune active | population | calcul brut CRANIOM, pas Steiner typed | disponible hors mode Steiner | absent Steiner | CALCULATED BUT NOT DISPLAYED |
| Occlusal/SN | Steiner | SN + points plan occlusal exacts | SN / occlusal | angle entre plans source-spécifiques | ° | aucune | âge/dentition/pop | absent | aucun exact Steiner | absent | NON SOURCE-LOCKED |
| SND | Steiner 1959 extension | S,N,D | SN / ND | angle source historique | ° | aucune | population | absent | absent | absent | NON SOURCE-LOCKED |
| Pog-NB | Steiner 1959 extension | Pog,N,B | Pog→NB | distance perpendiculaire exacte à verrouiller | mm | aucune | âge/population | absent | absent | absent | NON SOURCE-LOCKED |

### Note sur `COMPLETE`

Pour SNA/SNB/ANB, `COMPLETE` signifie ici : géométrie calculée + evidence typed + ligne UI existante + construction visible.

Cela **ne signifie pas encore** que `cephalo_typed_read.py` utilise Steiner comme autorité clinique finale : le read-path typé actuel ne projette autoritativement que quatre mesures CRANIOM. S1 doit corriger ce dernier maillon sans réécrire les formules.

---

## 5. Gap réel R19

Le Workbench contient actuellement :

```text
steiner: [SNA, SNB, ANB]
```

Alors que l'evidence graph certifie déjà six méthodes Steiner.

La perte de complétude principale pour Steiner est donc :

```text
6 méthodes typed disponibles
→ seulement 3 lignes Steiner R19
→ seulement SN/NA/NB tracés dans ce mode
```

Le problème n'est pas une absence générale du moteur.

---

## 6. S1 proposé après MONEYO

### Goal S1

Rendre **les six mesures déjà typées** visibles et autoritatives de bout en bout, sans modifier leur géométrie.

### Code autorisé par S1

#### Backend/read-path

- exposer les six `MeasurementEvidence` Steiner via un read-path typed explicite ;
- préserver `analysis_id=STEINER`, `method_id`, `method_version` et `construction_refs` ;
- fail-closed si construction/landmark/evidence manquant ou incohérent ;
- aucune fallback silencieuse vers une valeur frontend ;
- aucune norme/diagnostic/interprétation ajoutée.

#### Workbench

Afficher exactement :

```text
SNA
SNB
ANB
SN-GoGn
U1-NA °
L1-NB °
```

Chaque ligne doit indiquer sa valeur brute ou `NC` avec raison d'indisponibilité.

#### Tracing

- SNA : SN + NA
- SNB : SN + NB
- ANB : NA + NB
- SN-GoGn : SN + Go-Gn
- U1-NA° : axe U1 + NA
- L1-NB° : axe L1 + NB

Aucune ligne décorative ne doit être présentée comme construction de mesure.

### Non autorisé dans S1

- U1-NA mm
- L1-NB mm
- Occlusal/SN
- SND
- Pog-NB
- S-line
- normes Steiner numériques
- z-score
- diagnostic squelettique
- compromis/incisor prediction
- traitement/prognostic

---

## 7. Tests requis pour S1

### Backend

1. les six method IDs sont présents pour SRPose38 complet ;
2. valeur typed = géométrie versionnée attendue ;
3. landmark manquant → `NOT_COMPUTABLE`, jamais valeur inventée ;
4. source incohérente → fail-closed ;
5. aucun champ normatif activé ;
6. round-trip persistence + landmark-edit rematerialization conservent les six méthodes ;
7. aucune régression DB/patients/documents.

### Frontend

1. six rows exactement dans Steiner ;
2. aucune valeur recalculée en frontend ;
3. row↔construction exact pour les six ;
4. `NC` si backend indisponible ;
5. zéro norme locale/hardcodée injectée dans Steiner ;
6. `Toutes analyses` ne sera modifié que dans son lot dédié, pas ici.

### UI/UX

Avant modification : captures BEFORE mêmes viewports.  
Après modification : mêmes viewports, comparaison, overflow, console, row focus, score visuel.

---

## 8. S2 différé

S2 pourra traiter uniquement après nouveau source-lock/MONEYO :

### U1-NA mm / L1-NB mm

Bloqués tant que le landmark de référence coronale exact n'est pas représenté. Une implémentation utilisant `U1_incisal/L1_incisal` par commodité est interdite.

### Interincisal

La géométrie existe déjà en CRANIOM. La décision suivante sera de créer ou non une méthode Steiner typée distincte plutôt que de relabeler silencieusement CRANIOM.

### Occlusal/SN

Bloqué jusqu'à définition explicite des points du plan occlusal et de la convention de dentition/version.

---

## 9. S3 historique différé

`Steiner 1959 extension` pourra être un contrat séparé pour :

- SND ;
- Pog-NB ;
- éventuelles relations complémentaires source-prouvées.

Ne pas injecter ces éléments automatiquement dans `STEINER_CORE_V1`.

---

## 10. Normes

Aucune norme n'est incluse dans S1.

Si un futur lot active des références, il devra passer par la couche normative versionnée avec au minimum :

```text
analysis_id
analysis_version
metric_id / method_id
source
population/cohort
age dependence
sex dependence
mean/range/SD
applicability
```

Les valeurs historiques souvent citées comme « Steiner norms » ne deviennent jamais universelles par simple répétition dans la littérature.

---

## 11. Décision recommandée

### Recommandation

**Autoriser S1.**

Raison : S1 ne crée aucune nouvelle formule clinique. Il fait seulement remonter et tracer correctement six méthodes Steiner déjà implémentées, source-référencées et testées dans le snapshot typed.

### Risque S1

Faible à modéré si le read-path est fail-closed : le risque principal est l'intégration/présentation, pas la création scientifique.

### Risque à éviter

Profiter de S1 pour « compléter Steiner » avec des distances coronales, normes ou plans historiquement ambigus. Cela recréerait exactement le problème que l'audit cherche à supprimer.

---

## 12. MONEYO GATE

Aucun code clinique Steiner ne doit être modifié avant validation humaine explicite.

### Autorisation exacte proposée

`MONEYO STEINER S1`

Cette validation autorise **uniquement** :

- read-path typed des six méthodes existantes ;
- six rows Steiner ;
- constructions SVG exactes correspondantes ;
- tests backend/frontend/non-régression ;
- BEFORE/AFTER UI.

Elle **n'autorise pas** : nouvelles formules, mesures linéaires U1/L1, normes, interprétation, diagnostic, plan thérapeutique, SND/Pog-NB ou plan occlusal.

**État : EN ATTENTE DE MONEYO STEINER S1.**

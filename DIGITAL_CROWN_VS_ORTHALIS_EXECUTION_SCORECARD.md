# DIGITAL CROWN VS ORTHALIS — EXECUTION SCORECARD CANONIQUE

**Statut : annexe canonique d'exécution**  
**Date : 2026-09-11**  
**Repo : `hraaaaf/Digital_crown`**  
**Roadmap mère : `DIGITAL_CROWN_VS_ORTHALIS_ROADMAP.md`**  
**Baseline score vérifiée : Digital Crown `70,0/100` ; Orthalis `90,5/100`**

> Cette annexe transforme la roadmap stratégique en plan exécutable avec effort relatif, gain de score admissible, dépendances et gates de preuve. Elle ne remplace pas les fichiers canoniques spécialisés de chaque domaine.

---

# 0. RÈGLE DE SCORING

## Score produit

Formule inchangée :

`Score = Σ(poids_domaine × note_domaine/10)`

Baseline actuelle :

| Domaine | Poids | DC baseline | Orthalis baseline |
|---|---:|---:|---:|
| PMS patient + agenda | 12 | 9,0 | 9,5 |
| Workflow orthodontique | 15 | 7,0 | 9,5 |
| Céphalométrie | 15 | 7,5 | 9,5 |
| Imagerie / media patient | 12 | 6,0 | 9,5 |
| Documents + finance | 8 | 8,5 | 9,0 |
| Patient-facing | 10 | 7,0 | 9,0 |
| Intégrations externes | 10 | 3,0 | 10,0 |
| Architecture / sécurité / provenance | 8 | 9,0 | 7,5 |
| Maroc-first | 5 | 9,5 | 4,0 |
| Industrialisation / support terrain | 5 | 3,0 | 10,0 |

**Baseline DC = 70,0/100.**  
**Baseline Orthalis = 90,5/100.**

### Règle stricte

Un gain de score est **admissible uniquement après fermeture du gate du lot** : code + tests + runtime + preuve UX/sécurité/science selon le risque.

- code écrit mais non testé = `+0`
- tests unitaires verts sans runtime quand runtime requis = `+0`
- UI jolie sans preuve fonctionnelle = `+0`
- fonction clinique sans validation adaptée = `+0`
- intégration mock sans provider réel = `+0` sur « intégrations réelles »

---

# 1. ÉCHELLE D'EFFORT

Effort relatif par sous-lot : **1 / 2 / 3 / 5 / 8 / 13 EP**.

- `1 EP` : modification bornée, faible risque, dépendances connues.
- `2 EP` : petit lot multi-fichier, tests simples.
- `3 EP` : lot modéré avec runtime/UX ou migration légère.
- `5 EP` : feature complète bornée, plusieurs couches, certification dédiée.
- `8 EP` : lot complexe transverse ou sécurité/data significative.
- `13 EP` : lot majeur, scientifique, sécurité critique, intégration externe ou migration lourde.

Les EP mesurent **complexité + risque + dépendances**, pas une durée calendaire. Les convertir mécaniquement en jours serait du théâtre de précision.

---

# 2. SEUILS STRATÉGIQUES

| Niveau | Score minimum | Conditions supplémentaires |
|---|---:|---|
| Baseline actuelle | 70,0 | état actuel prouvé |
| Compétitif sérieux | 82,0 | Media + Journey + Ceph longitudinal partiellement fermés |
| Proche parité | 88,0 | Patient + intégrations réelles + industrialisation en progrès |
| Parité score | 90,5 | score ≥ Orthalis baseline, mais aucune revendication de supériorité automatique |
| Lead crédible | 93,0 | aucune catégorie critique <8/10 + gains runtime prouvés |
| Claim `Digital Crown > Orthalis` | ≥93,0 | 3 cabinets pilotes + restore drill + benchmark avantageux sur ≥3 workflows + aucun P0 ouvert |

**Important :** Orthalis peut évoluer. Le seuil de parité doit être recalculé avec sources fraîches avant toute revendication externe.

---

# 3. ROADMAP EXÉCUTIVE — SCORE + EFFORT

## LOT A — Closeout des chantiers actifs

### Goal

Fermer les lots de certification déjà engagés avant d'ouvrir une grosse verticale compétitive qui ferait dériver la base.

| Sous-lot | EP | Gain score cible |
|---|---:|---:|
| A1 — P6 Document Libre certification | 3 | +0,0 |
| A2 — cohérence docs / roadmap / master | 2 | +0,0 |

**Effort lot A : 5 EP**  
**Score cible après A : 70,0/100**

Le lot A n'ajoute pas de capacité concurrentielle : il réduit le risque de dérive et ferme proprement l'existant.

### Gate

- P6 runtime + responsive + CI exact-head ;
- docs canoniques cohérentes ;
- aucun P0 nouveau ;
- master vérifié.

---

## LOT B — Competitive Evidence Harness

### Goal

Éliminer les hypothèses du benchmark avant d'investir lourdement.

| Sous-lot | EP | Preuve |
|---|---:|---|
| B1 — inventaire fonctionnel exact Digital Crown | 3 | routes/modules/tests reliés |
| B2 — matrice Orthalis sourcée et datée | 3 | sources primaires |
| B3 — dataset synthétique benchmark | 3 | reproductible |
| B4 — scénarios utilisateurs communs | 2 | protocoles versionnés |
| B5 — métriques clics/temps/erreurs | 2 | harness exécutable |

**Effort lot B : 13 EP**  
**Gain score : +0,0**  
**Score cible après B : 70,0/100**

Aucun gain de score : ce lot améliore la **confiance** du benchmark, pas le produit.

### Gate

Plus aucun « on pense que » dans les catégories critiques.

---

# 4. LOT C — MEDIA CORE / KITVIEW-CLASS FOUNDATION

### Goal

Créer un socle média transverse fiable : patient, timeline, provenance, comparaison et capture.

| Sous-lot | EP | Impact principal |
|---|---:|---|
| C1 — modèle `ClinicalAsset` / métadonnées / provenance | 8 | architecture + media |
| C2 — stockage, hash, déduplication, tenant guard | 8 | sécurité + media |
| C3 — import sécurisé + derivatives/thumbnails | 8 | media |
| C4 — timeline patient T0/T1/T2 + viewer | 8 | media + ortho |
| C5 — comparaison side-by-side + recherche/filtres | 8 | media |
| C6 — capture smartphone contrôlée | 5 | media + mobile |
| C7 — certification volumétrique + cross-tenant + responsive | 5 | preuve |

**Effort lot C : 50 EP**

### Notes cibles après fermeture

- Imagerie/media : `6,0 → 8,5`
- Architecture/sécurité : reste `≥9,0`

Gain pondéré : `12 × (8,5-6,0)/10 = +3,0`

**Score cible après C : 73,0/100**

### Gate

- plusieurs patients synthétiques ;
- centaines de médias ;
- aucun cross-tenant leak ;
- aucun média patient accessible anonymement ;
- comparaison T0/T1 fonctionnelle ;
- responsive 390/768/1280+ ;
- performances mesurées, pas supposées.

---

# 5. LOT D — ORTHO JOURNEY LONGITUDINAL

### Goal

Transformer le dossier en parcours orthodontique structuré et exploitable de consultation à contention.

| Sous-lot | EP | Impact principal |
|---|---:|---|
| D1 — modèle case/phases/appareil/aligneur | 8 | workflow ortho |
| D2 — contrôles, incidents, progression | 8 | workflow ortho |
| D3 — objectifs praticien + états explicites | 5 | workflow clinique |
| D4 — liaison Media/Docs/Finance sans contamination sémantique | 8 | workflow transverse |
| D5 — timeline UX + navigation | 8 | UX ortho |
| D6 — E2E complet consultation→contention | 5 | preuve |

**Effort lot D : 42 EP**

### Notes cibles

- Workflow orthodontique : `7,0 → 9,0`

Gain : `15 × 2,0/10 = +3,0`

**Score cible après D : 76,0/100**

### Gate

Cas synthétique complet avec audit, reprise après interruption et invariants stables.

---

# 6. LOT E — CEPHALO R2 COMPETITIVE

### Goal

Passer d'une céphalométrie robuste techniquement à une céphalométrie longitudinalement compétitive et scientifiquement gouvernée.

| Sous-lot | EP | Impact |
|---|---:|---|
| E1 — superposition T0/T1 déterministe | 13 | ceph |
| E2 — extension T2/Tn + provenance de recalage | 8 | ceph longitudinal |
| E3 — Steiner validé de bout en bout | 8 | science |
| E4 — Tweed validé | 8 | science |
| E5 — Ricketts validé | 13 | science |
| E6 — Delaire validé | 13 | science |
| E7 — Wits/analyses existantes consolidées | 5 | science |
| E8 — comparaison tracé/radio/photo | 8 | ceph + media |
| E9 — rapport longitudinal | 5 | documents |
| E10 — certification scientifique + UX | 8 | preuve |

**Effort lot E : 89 EP**

### Notes cibles

- Céphalométrie : `7,5 → 9,2`

Gain : `15 × 1,7/10 = +2,55`

**Score cible après E : 78,55/100**

### Gate

- 5 analyses majeures minimum gouvernées ;
- constantes/normes sourcées ;
- jeux de référence ;
- aucune norme `LEGACY_UNVALIDATED` promue silencieusement ;
- revue praticien ;
- superpositions reproductibles.

---

# 7. LOT F — PATIENT COMPANION

### Goal

Créer un portail patient sécurisé et utile, sans transformer le LAN cabinet en passoire connectée.

| Sous-lot | EP | Impact |
|---|---:|---|
| F1 — identité patient séparée + sessions révocables | 13 | sécurité + patient |
| F2 — RDV + confirmations + documents | 8 | patient |
| F3 — questionnaires médicaux | 8 | patient |
| F4 — notifications | 5 | patient |
| F5 — finance consultative | 5 | patient + finance |
| F6 — upload urgence sécurisé | 8 | patient + media |
| F7 — consentement/signature après gate juridique | 13 | patient/legal |
| F8 — paiement provider réel après gate juridique | 13 | patient/finance |
| F9 — certification cross-patient / revoke / offline | 8 | preuve |

**Effort lot F : 81 EP**

### Notes cibles

- Patient-facing : `7,0 → 9,0`

Gain : `10 × 2,0/10 = +2,0`

**Score cible après F : 80,55/100**

### Gate

Aucun accès cross-patient, révocation immédiate, uploads contrôlés, claims juridiques Maroc validés avant communication externe.

---

# 8. LOT G — CONNECT HUB

### Goal

Transformer les intégrations d'un écran marketing en vraie couche d'interopérabilité auditable.

| Sous-lot | EP | Impact |
|---|---:|---|
| G1 — framework `ConnectorAdapter` + secrets + journal | 13 | intégrations |
| G2 — sandbox/mock contractuel + idempotence/retry | 8 | intégrations |
| G3 — premier provider réel prioritaire | 13 | intégrations |
| G4 — WhatsApp Business administratif Maroc | 8 | Maroc + intégrations |
| G5 — second provider réel | 13 | intégrations |
| G6 — troisième provider si accès officiel | 13 | intégrations |
| G7 — révocation/perte réseau/conflicts | 8 | robustesse |

**Effort lot G : 76 EP**

### Notes cibles

- Intégrations : `3,0 → 7,5`

Gain : `10 × 4,5/10 = +4,5`

**Score cible après G : 85,05/100**

### Gate

Un provider n'est compté que si accès officiel + échange réel + mapping + sécurité + désactivation sont prouvés.

---

# 9. LOT H — INDUSTRIALISATION & PILOTES

### Goal

Passer d'un excellent repo à un produit cabinet réellement exploitable et récupérable après incident.

| Sous-lot | EP | Impact |
|---|---:|---|
| H1 — installation propre Windows | 8 | industrialisation |
| H2 — upgrade N→N+1 + migration versionnée | 13 | industrialisation |
| H3 — rollback contrôlé | 8 | recovery |
| H4 — backup chiffré + intégrité | 8 | recovery |
| H5 — restore sur machine distincte | 13 | recovery |
| H6 — health report / support bundle redacted | 8 | support |
| H7 — pilote cabinet #1 | 13 | terrain |
| H8 — pilote cabinet #2 | 13 | terrain |
| H9 — pilote cabinet #3 | 13 | terrain |
| H10 — incident register + closeout | 8 | preuve |

**Effort lot H : 105 EP**

### Notes cibles

- Industrialisation/support : `3,0 → 8,5`

Gain : `5 × 5,5/10 = +2,75`

**Score cible après H : 87,80/100**

### Gate

- 3 cabinets distincts ;
- restore drill réussi ;
- update/rollback prouvés ;
- aucun P0 ouvert ;
- incidents documentés ;
- aucune perte de données critique.

---

# 10. LOT I — PARITY PASS

À ce stade Digital Crown peut être très bon sans encore égaler le breadth Orthalis.

### Goal

Fermer uniquement les écarts qui empêchent la parité, sans lancer une foire aux features.

| Sous-lot | EP | Cible |
|---|---:|---|
| I1 — Media Hub 8,5→9,3 | 13 | comparaison/protocoles/presentation |
| I2 — Ortho Journey 9,0→9,4 | 8 | finesse workflow |
| I3 — Ceph 9,2→9,5 | 13 | validation + breadth utile |
| I4 — Patient 9,0→9,3 | 8 | polish + adoption |
| I5 — Integrations 7,5→9,0 | 21 | providers réels supplémentaires |
| I6 — Industrialisation 8,5→9,0 | 8 | recovery/support |
| I7 — Docs/finance 8,5→9,1 | 5 | gaps terrain uniquement |
| I8 — re-benchmark complet | 8 | preuve |

**Effort lot I : 84 EP**

### Gain cible calculé

- Media `+0,96`
- Journey `+0,60`
- Ceph `+0,45`
- Patient `+0,30`
- Integrations `+1,50`
- Industrialisation `+0,25`
- Docs/finance `+0,48`

Gain total : **+4,54**

**Score cible après I : 92,34/100**

Ce score dépasse la baseline Orthalis 90,5 mais **ne suffit toujours pas à autoriser le claim “Digital Crown > Orthalis”** sans gates terrain/comparatifs.

---

# 11. LOT J — LEAD PASS / 93+

### Goal

Obtenir un avantage mesurable, pas seulement une parité de cases fonctionnelles.

Priorité aux domaines où Digital Crown peut réellement dominer : intégration du workflow, provenance, local-first, rapidité opératoire et Maroc-first.

| Sous-lot | EP | Cible |
|---|---:|---|
| J1 — Architecture/sécurité 9,0→9,5 | 8 | hardening + preuve recovery |
| J2 — Media 9,3→9,5 | 5 | friction/UX |
| J3 — Journey 9,4→9,6 | 5 | workflow clinique |
| J4 — Patient 9,3→9,5 | 5 | parcours patient |
| J5 — benchmark UX 3 workflows structurants | 13 | avantage mesurable |
| J6 — validation Maroc-first cabinets | 8 | avantage marché |

**Effort lot J : 44 EP**

Gain score produit :

- architecture `+0,40`
- media `+0,24`
- journey `+0,30`
- patient `+0,20`

**Score cible après J : 93,48/100**

### Gate final de claim

`Digital Crown > Orthalis` autorisé uniquement si :

1. score recalculé frais ≥93 ;
2. aucune catégorie critique <8/10 ;
3. 3 cabinets pilotes fermés ;
4. restore drill réussi ;
5. aucun P0 sécurité/data/science ouvert ;
6. avantage mesuré sur ≥3 workflows communs ;
7. benchmark Orthalis revalidé avec sources primaires récentes ;
8. avantage Maroc-first fondé sur besoins terrain, pas intuition.

---

# 12. SYNTHÈSE SCORE / EFFORT

| Étape | EP étape | EP cumulés | Score cible DC | Écart vs Orthalis 90,5 |
|---|---:|---:|---:|---:|
| Baseline | 0 | 0 | **70,00** | -20,50 |
| A — Closeout | 5 | 5 | **70,00** | -20,50 |
| B — Evidence Harness | 13 | 18 | **70,00** | -20,50 |
| C — Media Core | 50 | 68 | **73,00** | -17,50 |
| D — Ortho Journey | 42 | 110 | **76,00** | -14,50 |
| E — Ceph R2 | 89 | 199 | **78,55** | -11,95 |
| F — Patient Companion | 81 | 280 | **80,55** | -9,95 |
| G — Connect Hub | 76 | 356 | **85,05** | -5,45 |
| H — Industrialisation/Pilotes | 105 | 461 | **87,80** | -2,70 |
| I — Parity Pass | 84 | 545 | **92,34** | +1,84 |
| J — Lead Pass | 44 | 589 | **93,48** | +2,98 |

**Effort total stratégique estimé : 589 EP relatifs.**

Ce total ne signifie pas 589 jours. Il permet de comparer les blocs entre eux et d'éviter que des petits travaux périphériques volent la priorité aux gros gaps.

---

# 13. ROI PRODUIT — GAIN DE SCORE PAR 10 EP

Indicateur secondaire, à ne jamais utiliser seul :

| Lot | Gain score | EP | Gain / 10 EP |
|---|---:|---:|---:|
| C — Media Core | +3,00 | 50 | **+0,60** |
| D — Ortho Journey | +3,00 | 42 | **+0,71** |
| E — Ceph R2 | +2,55 | 89 | **+0,29** |
| F — Patient | +2,00 | 81 | **+0,25** |
| G — Connect Hub | +4,50 | 76 | **+0,59** |
| H — Industrialisation | +2,75 | 105 | **+0,26** |
| I — Parity Pass | +4,54 | 84 | **+0,54** |
| J — Lead Pass | +1,14 | 44 | **+0,26** |

### Interprétation

Le meilleur rendement théorique est **Ortho Journey**, puis **Media Core / Connect Hub**.

Mais l'ordre d'exécution n'est pas un simple tri ROI :

- Media précède Journey car il fournit les preuves visuelles longitudinales ;
- Ceph R2 est plus coûteux car la science impose une validation rigoureuse ;
- Industrialisation a un faible gain de score apparent mais est **obligatoire pour la crédibilité produit** ;
- Connect Hub dépend d'accès providers externes et peut devenir `BLOCKED_EXTERNAL`.

---

# 14. PRIORITÉ EXÉCUTIVE

Ordre verrouillé sauf blocage prouvé :

`A Closeout → B Evidence → C Media → D Journey → E Ceph R2 → F Patient → G Connect → H Pilotes → I Parity → J Lead`

### Exceptions autorisées

- travaux indépendants pendant CI ;
- provider externe bloqué : avancer sur lot suivant indépendant ;
- gate scientifique non résolu : ne pas contourner ;
- besoin critique pilote : peut remonter en priorité avec preuve terrain.

---

# 15. DEFINITION OF SCORE DONE

Pour modifier une note dans la scorecard canonique, il faut joindre :

- baseline avant ;
- fonction/lot exact ;
- tests ;
- runtime ;
- métrique ou scénario comparatif ;
- preuve responsive si UI ;
- preuve sécurité/data si concerné ;
- preuve scientifique si clinique ;
- lien PR/HEAD/CI ;
- calcul du nouveau score.

Sans cela : **score inchangé**.

---

# 16. NEXT EXACT

1. Fermer P6 #405.
2. Ouvrir `LOT B — Competitive Evidence Harness` sur master courant.
3. Produire la matrice fonctionnelle exacte Digital Crown/Orthalis.
4. Ne modifier la baseline 70,0 qu'après première fermeture d'un lot produit avec preuve.

---

## FICHIER CANONIQUE

`DIGITAL_CROWN_VS_ORTHALIS_EXECUTION_SCORECARD.md` — Execution Scorecard — **70,0 → cible lead 93,48/100 — 589 EP relatifs**.

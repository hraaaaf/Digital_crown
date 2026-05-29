# Base de Connaissance Déterministe - Orthodontie & Bilan
*Fichier destiné à alimenter le futur Bot "Règles Strictes" (100% Sans LLM).*

## 1. Moteur de Décision Orthodontique (Expert System)
L'application utilise un système expert purement déterministe (`orthoExpertSystem.ts` et `cephalo_engine.py`) basé sur des normes cliniques (COM, Tweed, Steiner, Ricketts).

### 1.1 Calcul de la DDM Réelle (Discrépance Dento-Maxillaire)
- **Règle Empirique** : 2.5° de variation de l'IMPA = 1 mm d'espace sur l'arcade.
- **Formule** : `DDM_Reelle = DDM_Clinique (mesurée sur moulages) + ((IMPA_actuel - 90) / 2.5)`
- **Interprétation** : Si l'incisive est très en avant (IMPA > 90°), son redressement va "consommer" de l'espace, aggravant la DDM clinique.

### 1.2 Diagnostic Squelettique (Consensus Steiner / McNamara)
- **Steiner (ANB)** : 
  - Classe I : 0° ≤ ANB ≤ 4.5°
  - Classe II : ANB > 4.5°
  - Classe III : ANB < 0°
- **McNamara (Distance A-Nperp vs B-Nperp)** :
  - Calcule le décalage A/B sur le plan de Francfort.
- **Consensus** : L'algorithme confronte Steiner et McNamara. En cas de désaccord, Steiner prime (Gold Standard) et McNamara devient une "tendance".

### 1.3 Typologie Verticale (Angle de Tweed - FMA)
- **Normodivergent** : 22° ≤ FMA ≤ 30°
- **Hyperdivergent** : FMA > 30° (Face longue, tendance à la béance. Mécaniques extrusives interdites).
- **Hypodivergent** : FMA < 22° (Face courte, tendance à la supraclusion. Mécaniques extrusives autorisées).

### 1.4 Décisions d'Extraction (Méthode Contemporaine / Damon)
L'algorithme privilégie le "Bone Adaptation" (expansion) et n'extrait que sous conditions strictes :
- DDM Sévère (< -7mm) + Biprotrusion (IMPA ≥ 95°) + Profil convexe.
- Biproalvéolie critique (IMPA ≥ 100° ET I/Francfort ≥ 120°).
- DDM Modérée avec Typologie Hyperdivergente sévère (risque d'ouverture de l'axe charnière).

### 1.5 Protocoles Damon (Choix du Torque)
- **Torque Maxillaire** :
  - *High Torque* : Si extractions prévues ou traitement de Classe II (pour contrer la perte de torque radiculaire).
  - *Low Torque* : Si I/F > 120° sans extraction (pour éviter d'aggraver la vestibulo-version).
- **Torque Mandibulaire** :
  - *Low Torque* : Si IMPA > 95° ou forte expansion prévue.
  - *High Torque* : Si IMPA < 85° (rétroalvéolie).

## 2. Intégration de la Radio Panoramique (Inputs Cliniques)
Le diagnostic orthodontique n'est jamais isolé. L'algorithme prend en compte la panoramique pour définir les **limites biomécaniques** :
- **Dents de Sagesse (DDS)** : Si incluses/enclavées, la distalisation molaire (recul) avec Invisalign ou Damon est impossible. Avulsion préalable requise.
- **Niveau Parodontal (Os alvéolaire)** : Si perte osseuse détectée, l'expansion transversale (Damon) ou la pro-inclinaison incisive est proscrite pour éviter les récessions gingivales.
- **Asymétrie Condylienne** : Signe d'un problème squelettique asymétrique nécessitant potentiellement une chirurgie.
- **Résorption Radiculaire** : Impose des "forces légères" strictes (Aligners changeant tous les 14 jours ou arcs ultra-souples).

## 3. Analyse Squelettique Multi-Dimensionnelle
- **Sens Sagittal (A/P)** :
  - *Steiner (ANB)* : Rotation-dépendant.
  - *Wits (Plan Occlusal)* : Indépendant de la rotation. Juge de paix pour la Classe squelettique vraie (AO-BO).
  - *McNamara (N-Perp)* : Identifie si l'erreur vient du maxillaire ou de la mandibule.
- **Sens Vertical** :
  - *Tweed (FMA)* : Hypo (<22°), Normo, Hyperdivergent (>30°).
  - Hyperdivergent = interdiction d'extrusion postérieure (effet Bite-Block requis).

## 4. Architecture des Données
- Le backend (Python) effectue les projections mathématiques exactes et renvoie des Z-Scores.
- Le frontend (TypeScript) consolide ces valeurs dans `cephaloUtils.ts` pour définir le traitement via `orthoExpertSystem.ts`.

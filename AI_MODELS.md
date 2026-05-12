# 👑 Digital Crown - AI Models & Clinical Logic

Ce document détaille les modèles d'Intelligence Artificielle et les moteurs de calcul clinique intégrés dans la plateforme Digital Crown.

## 🦷 1. Moteur Céphalométrique (Deterministe COM)
Le moteur de calcul (`cephalo_engine.py`) suit les normes du **COM (Centre d'Orthodontie Moderne)**. Contrairement à un modèle "boîte noire", il utilise une logique géométrique déterministe certifiée.

### Normes de Référence (Fiche de Mesures COM)
| Paramètre | Norme Clinique | Plage de Compensation |
| :--- | :--- | :--- |
| **IMPA** | 90° ± 5° | 80° - 100° |
| **I/F** | 107° ± 5° | 97° - 120° |
| **Inter-Incisif** | 131° ± 10° | 120° - 142° |
| **Angle de Tweed** | 26° ± 4° | 22° - 30° |
| **Surplomb / Overjet** | 2.25 ± 0.75 mm | N/A |
| **Recouvrement / Overbite**| 2.25 ± 0.75 mm | N/A |

### Logique de Diagnostic (SLM / Ghost Elite)
Le moteur génère une synthèse narrative structurée en **4 sections obligatoires** :
1. **Analyse Céphalométrique COM** : Fusion des données squelettiques et dentaires (SNA, SNB, IMPA, I/F, etc.).
2. **Analyse des Moulages** : Détails occlusaux (Classes d'Angle, Subdivision, Forme d'arcade).
3. **Synthèse Diagnostique** : Résumé exhaustif de toutes les anomalies squelettiques et dentaires détectées.
4. **Plan de Traitement** : Stratégie thérapeutique adaptative :
    - **Orthopédie (ODF)** : Prioritaire chez l'enfant (≤12 ans) pour la correction squelettique.
    - **Orthodontie Passive** : Système Damon préconisé pour l'expansion physiologique.
    - **Contrôle du Torque** : Sélection des brackets basée sur l'inclinaison incisive (High Torque/Red, Standard/Blue, Low Torque/Yellow).
    - **Aligneurs** : Option Invisalign proposée pour les cas d'alignement modéré.

---

## 👁️ 2. Vision Artificielle (Deep Learning)

### Détection des Landmarks (Cephalométrie)
- **Modèle** : U-Net / CephLD-CCA.
- **Précision** : Sub-pixel (via Centre de Masse local).
- **Service** : `backend/services/vision_service.py`.

### Diagnostic Panoramique (ELITE Hub v2.0)
- **Modèle** : ONNX (YOLO11x trained on Dentex Dataset).
- **Service** : `backend/services/panoramic_service.py`.
- **Taxonomie Spécialisée (6 Catégories)** :
    1.  **Conservatrice** : Caries (émail, dentine, profonde), reprises sous obturation.
    2.  **Endodontie** : Lésions périapicales, traitements canalaires (incomplets, adéquats), instruments fracturés.
    3.  **Parodontie** : Alvéolyses (H/V), atteintes de furcation, tartre sous-gingival.
    4.  **Chirurgie** : Dents incluses/enclavées, agénésies, surnuméraires, restes radiculaires.
    5.  **Prothèse** : Couronnes, bridges, implants, péri-implantites.
    6.  **ATM / Sinus** : Opacités sinusiennes, asymétries condyliennes.
- **Moteur de Rapport Hybride** : Fusionne les détections IA SOTA avec les annotations manuelles expertes pour générer des bilans PDF structurés par secteur (FDI).


### Authentification & Certification
- **Signature QR** : Chaque rapport clinique généré intègre un code QR dynamique (`QRService`) lié à l'ID patient pour vérification immédiate de l'authenticité du diagnostic.

---

## 📈 3. Moteur d'Apprentissage (Doctor Habit Engine)
Le système apprend les habitudes du praticien (`DoctorActHabit`) pour :
- **Quick Acts** : Suggestion des actes les plus fréquents par contexte.
- **Surcharge Clinique** : Adaptation des protocoles de diagnostic en fonction des corrections manuelles répétées.

---

## 🛠️ Audit & Maintenance
Pour auditer les modèles ONNX :
```bash
python backend/ai_models/audit_model.py
```
Les résultats sont consignés dans `backend/ai_models/model_audit.txt`.

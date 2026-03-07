# 📊 RAPPORT D'ANALYSE COMPLÈTE - DIGITAL CROWN

**Date d'analyse**: Mars 2026  
**Scope**: Backend + Frontend - Architecture globale  
**Critères**: Sécurité, Scalabilité, UX, Conformité médicale

---

## 🔴 ANOMALIES CRITIQUES

### 1. **BASE DE DONNÉES MÉDICAMENTS - TRÈS INSUFFISANTE**
**Fichier**: `backend/seed.py` (lignes 36-56)

```python
# ACTUELLEMENT - Seulement 15 médicaments (mocks)
meds_data = [
    ("ACIGAM", "200 mg", "Comprimé sécable", 50),
    ("BISPIRAZOLE", "1.5 MUI / 250 mg", "Comprimé pelliculé", 50),
    ... # 13 autres seulement
]
```

**Problème**: 
- Base de données médicamenteuse **NON SCIENTIFIQUE** (noms génériques/marques fictives)
- Aucune liaison avec les vraies spécialités (DCI)
- Pas de code CIS (Code Identifiant de Spécialité) ou ATC (Classification Anatomique)
- **RISQUE JURIDIQUE**: Ordonnances avec médicaments "fictifs" non conformes

**Recommandation**:
- Intégrer la base **Thésaurus des Médicaments** (décret français) ou **WHO Drug Dictionary**
- Structure recommandée:
```python
class MedicamentScientifique(Base):
    __tablename__ = "medicaments_scientifiques"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    dci: Mapped[str] = mapped_column(String(255))  # Dénomination Commune Internationale
    code_atc: Mapped[str] = mapped_column(String(7))  # N05BA01
    specialites: Mapped[List["Specialite"]] = relationship(...)
    
    # Classement thérapeutique dentaire
    categorie_dentaire: Mapped[str]  # ANTALGIQUE, ANTIINFLAMMATOIRE, ANTIBIOTIQUE...
    indication_principale: Mapped[str]
    posologie_reference: Mapped[dict] = mapped_column(JSON)  # Par âge/poids
```

---

### 2. **NOTE D'HONORAIRES - INTERFACE OBSOLÈTE VS ORDONNANCE**
**Fichier**: `frontend/src/features/admin/DocumentHub.tsx` (lignes 536-600)

**Problème**: 
- L'ordonnance a une **barre de recherche IA** (motif de consultation) + **autocomplétion médicaments**
- La note d'honoraires n'a qu'une simple liste sans assistance intelligente
- Pas de suggestion d'actes basée sur l'historique patient
- Pas de codes CCAM (Classification Commune des Actes Médicaux) ou NGAP

**Recommandation**:
1. **Ajouter une barre de recherche composite** comme pour l'ordonnance:
```typescript
// Interface unifiée pour recherche actes
<ActSearchComposite 
  onSelect={(acte) => {
    // acte = {
    //   code_ccam: "HKH2230",
    //   libelle: "Acte chirurgical de parodontologie",
    //   prix_base: 120.00,
    //   categorie: "PARODONTOLOGIE"
    // }
  }}
/>
```

2. **Système de mémoire de prix intelligent**:
```typescript
// Historique des prix pratiqués par le praticien
interface HistoriquePrix {
  acte_code: string;
  prix_moyen: number;
  prix_dernier: number;
  frequence: number;
  derniere_date: Date;
}
// Suggère: "Vous avez facturé cet acte 400 MAD en moyenne (dernier: 450 MAD)"
```

---

### 3. **PATHOLOGIES - ABSENCE TOTALE DANS LE MODÈLE**
**Fichier**: `backend/models.py` - Aucune table de pathologies

**Problème**:
- L'ordonnance "intelligente" se base sur des catégories cliniques simplistes (ligne 125-132)
- Aucune codification CIM-10 (Classification Internationale des Maladies)
- Aucun lien entre diagnostic et prescription suggérée

**Recommandation**:
```python
class Pathologie(Base):
    __tablename__ = "pathologies"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code_cim10: Mapped[str] = mapped_column(String(10), unique=True)  # K05.1
    libelle: Mapped[str] = mapped_column(String(255))
    libelle_court: Mapped[str]  # Pour affichage rapide
    
    # Liaisons
    prescriptions_suggerees: Mapped[List["PrescriptionPathologie"]] = relationship(...)
    actes_suggeres: Mapped[List["ActePathologie"]] = relationship(...)
    
class PrescriptionPathologie(Base):
    """Table de liaison: Quels médicaments pour quelle pathologie"""
    pathologie_id: Mapped[int]
    medicament_dci: Mapped[str]
    posologie_adaptee: Mapped[str]
    duree_typique: Mapped[int]  # jours
    priorite: Mapped[int]  # 1 = premier choix, 2 = alternative...
```

---

## 🟡 ANOMALIES MAJEURES

### 4. **VISION SERVICE - MODE MOCK NON GÉRÉ DANS L'UI**
**Fichier**: `backend/services/vision_service.py` (lignes 70-82)

**Problème**:
```python
if not os.path.exists(self.weights_path):
    logger.error(f"CRITIQUE : Poids du modèle introuvables... Mode MOCK activé.")
    return
```

- Le backend bascule en "Mode MOCK" silencieusement
- Le frontend n'est pas informé que les landmarks sont simulés
- **RISQUE CLINIQUE**: Le praticien peut croire à une analyse IA réelle alors que c'est du fake

**Recommandation**:
```python
# Dans la réponse API
{
  "landmarks": [...],
  "mode_inference": "MOCK",  # ou "PRODUCTION"
  "confidence_score": null,  # null si MOCK
  "warning": "Modèle IA non disponible - Points placés aléatoirement pour démonstration"
}
```

---

### 5. **SLM (LLM) - DÉSACTIVÉ MAIS CODE MAINTENU**
**Fichier**: `backend/services/ai_advisor.py`

**Problème**:
- Le SLM (Llama3.2 via Ollama) a été désactivé par défaut (`use_slm=False`)
- Le code complexe de fallback avec timeout de 3s est maintenu
- **Dette technique**: Code mort qui complique la maintenance

**Recommandation**:
- Soit réactiver le SLM avec un modèle plus performant (Mistral 7B, GPT-4 via API)
- Soit supprimer le code SLM et garder uniquement le fallback heuristique
- Alternative: API externe Claude/GPT-4 avec anonymisation des données

---

### 6. **CORS - CONFIGURATION NON SÉCURISÉE**
**Fichier**: `backend/main.py` (lignes 65-71)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🚨 TOUT LE MONDE PEUT ACCÉDER
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Risque**: N'importe quel site web peut appeler votre API

**Correction**:
```python
from fastapi.middleware.cors import CORSMiddleware
import os

# Lecture depuis .env
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### 7. **UPLOAD DE FICHIERS - PAS DE VALIDATION DE TYPE SÉCURISÉE**
**Fichier**: `backend/main.py` - Endpoint upload

**Problème**: Validation par extension de fichier uniquement (facilement contournable)

**Recommandation**:
```python
import magic  # python-magic
from PIL import Image

def validate_image_secure(file: UploadFile):
    # 1. Vérification magic bytes
    file_content = file.file.read(2048)
    mime = magic.from_buffer(file_content, mime=True)
    
    if mime not in ['image/jpeg', 'image/png', 'image/dicom']:
        raise HTTPException(400, "Type de fichier non autorisé")
    
    # 2. Vérification que c'est une vraie image
    try:
        img = Image.open(io.BytesIO(file_content))
        img.verify()
    except:
        raise HTTPException(400, "Fichier image corrompu")
    
    # 3. Limite de taille
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(400, "Image trop volumineuse")
```

---

## 🟢 AMÉLIORATIONS RECOMMANDÉES

### 8. **SYSTÈME DE CATALOGUE D'ACTES - À ÉTOFFER**
**Actuel** (`backend/seed.py` - vide pour les actes)

**Recommandation** - Intégrer une vraie nomenclature:
```python
# NGAP (Nomenclature Générale des Actes Professionnels) - Dentaire
ACTES_NGAP = [
    {"code": "C", "libelle": "Consultation", "prix_reference": 25.00},
    {"code": "CS", "libelle": "Consultation spécialisée", "prix_reference": 45.00},
    {"code": "CSC", "libelle": "Consultation de spécialiste en chirurgie", "prix_reference": 55.00},
    # etc.
]

# CCAM (Actes chirurgicaux)
ACTES_CCAM = [
    {"code": "HKH2230", "libelle": "Extraction dentaire simple", "prix_base": 45.00},
    {"code": "HKH2240", "libelle": "Extraction dentaire complexe", "prix_base": 90.00},
    # etc.
]
```

---

### 9. **INTERFACE DE RECHERCHE COMPOSITE**
**Pour**: Ordonnance + Note d'honoraires + Certificats

**Spécification**:
```typescript
interface CompositeSearchProps {
  type: 'medicament' | 'acte' | 'pathologie';
  mode: 'prescription' | 'facturation';
  patientContext?: {
    age: number;
    poids?: number;
    allergies?: string[];
    antecedents?: string[];
  };
}

// Fonctionnalités:
// 1. Recherche floue (fuzzy) sur DCI, spécialité, indication
// 2. Filtrage par contexte patient (pas d'amoxicilline si allergie pénicilline)
// 3. Suggestions basées sur fréquence d'utilisation du praticien
// 4. Historique des dernières prescriptions similaires
```

---

### 10. **MÉMORISATION DES PRIX PRATIQUÉS**
**Fichier**: À créer - `backend/services/pricing_engine.py`

```python
class PricingEngine:
    """
    Mémorise les prix pratiqués par le praticien pour suggérer
    des tarifs cohérents entre patients.
    """
    
    def get_price_suggestion(self, acte_code: str) -> dict:
        """
        Retourne:
        - prix_moyen_praticien
        - fourchette (min, max)
        - dernier_prix_applique
        - prix_recommande_convention
        - alerte_si_anomalie (ex: prix > 50% de la moyenne)
        """
        pass
```

---

## 📋 TABLEAU RÉCAPITULATIF DES PRIORITÉS

| Priorité | Anomalie | Impact | Effort |
|----------|----------|--------|--------|
| 🔴 **CRITIQUE** | Base médicaments non scientifique | **Juridique** - Ordonnances invalides | 2-3 jours |
| 🔴 **CRITIQUE** | Note d'honoraires sans recherche | **UX** - Friction quotidienne | 1 jour |
| 🔴 **CRITIQUE** | Absence CIM-10/pathologies | **Médical** - Pas de diagnostic structuré | 2 jours |
| 🟡 **MAJEUR** | Mode MOCK non signalé | **Clinique** - Risque d'erreur | 2 heures |
| 🟡 **MAJEUR** | CORS ouvert | **Sécurité** - Exposition API | 30 min |
| 🟡 **MAJEUR** | Upload sans validation | **Sécurité** - Risque malware | 2 heures |
| 🟢 **Amélioration** | Catalogue actes NGAP/CCAM | **Fonctionnel** - Conformité | 1 jour |
| 🟢 **Amélioration** | Mémorisation prix | **UX** - Cohérence facturation | 4 heures |

---

## 🎯 PLAN D'ACTION RECOMMANDÉ

### Phase 1: Conformité & Sécurité (Semaine 1)
1. [ ] Restreindre CORS aux origines connues
2. [ ] Ajouter validation sécurisée des uploads
3. [ ] Signaler explicitement le Mode MOCK dans l'UI

### Phase 2: Données médicales (Semaine 2-3)
4. [ ] Créer tables `MedicamentScientifique` avec DCI/ATC
5. [ ] Importer base Thésaurus (ou créer sous-ensemble dentaire)
6. [ ] Créer table `Pathologie` avec CIM-10
7. [ ] Créer liens pathologie ↔ médicaments suggérés

### Phase 3: UX DocumentHub (Semaine 4)
8. [ ] Uniformiser recherche composite (ordonnance + honoraires)
9. [ ] Ajouter historique de prix intelligent
10. [ ] Intégrer codes NGAP/CCAM dans catalogue actes

---

## 💡 SUGGESTIONS ARCHITECTURALES

### Migration vers une architecture plus robuste:

```
backend/
├── domain/              # Logique métier pure
│   ├── entities/        # Modèles métier (Patient, Ordonnance...)
│   ├── repositories/    # Interfaces d'accès données
│   └── services/        # Use cases (Prescrire, Facturer...)
├── infrastructure/      # Implémentations techniques
│   ├── persistence/     # SQLAlchemy models
│   ├── ml/              # Vision + IA
│   └── security/        # Auth, validation fichiers
├── interfaces/          # API / CLI
│   └── api/
└── seed_data/           # Données médicales de référence
    ├── medicaments_thesaurus.json
    ├── pathologies_cim10_dentaire.json
    └── actes_ngap_ccam.json
```

---

**Fin du rapport** - Généré par analyse automatique du codebase Digital Crown

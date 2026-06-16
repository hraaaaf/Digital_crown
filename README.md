# Digital Crown — SANINOVA Edition
## *L'Intelligence Clinique au service de la Dentisterie Moderne*

![Version](https://img.shields.io/badge/Version-v3.0_CrownBot-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Backend-FastAPI_0.110-green?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/Frontend-React_19-61DAFB?style=for-the-badge&logo=react)
![Engine](https://img.shields.io/badge/PDF_Engine-ReportLab_Elite-red?style=for-the-badge)
![Intelligence](https://img.shields.io/badge/Intelligence-Ghost_Brain_v3-purple?style=for-the-badge)

---

## Vision du Projet

Digital Crown est une plateforme **Ghost Elite** conçue pour transformer la gestion des cabinets dentaires et orthodontiques. En fusionnant une esthétique ultra-premium avec des algorithmes d'IA de pointe et un moteur d'intelligence proactive, elle permet aux praticiens de se concentrer sur l'essentiel : le diagnostic et le soin.

---

## Nouveautés — Juin 2026 (Sprint CrownBot)

### CrownBot — Assistant Conversationnel Natif
- **Intent Parser hybride** : regex rapide + fallback LLM (Ollama) pour les requêtes ambiguës.
- **Action Dispatcher** : répond avec des cartes d'action (prise de RDV, consultation fiche patient, solde).
- **Finance O(1)** : requêtes financières résolues en temps constant depuis la caisse locale.
- **UX Confirmation Card** : carte de confirmation avant toute action irréversible.

### Document Studio — Échéancier Unifié
- Génération PDF ReportLab A5 (CheckBox : réglé ✓ / en cours ● / à venir □).
- Flux unifié avec Devis/Honoraires : **Aperçu → Enregistrer → Imprimer** via `StudioFooter`.
- Rappels WhatsApp intégrés par échéance (lien `wa.me` pré-formaté).

### Analytiques Réelles
- **Tendances de la Semaine** connecté à `/admin/dashboard/stats` (activité réelle 7 jours, plus de mock).

### Corrections Critiques
- **Login email/password** : corrigé (`URLSearchParams` → OAuth2PasswordRequestForm correct).
- **Tour guidé** : persistance correcte en `localStorage` — ne se relance plus à chaque session.
- **Radio panoramique** : numéros FDI lisibles (fond sombre + opacité 82%), directement superposés sur la radio.

---

## Breakthroughs Techniques — Mai 2026

### Ghost Hub Intelligence v2.0 — Moteur Proactif Complet

**Catégorie A — Analyse Patient :**
- **A1 Flash Summary** : Résumé IA de dossier en temps réel (antécédents, traitements actifs, solde).
- **A4 Traitement Abandonné** : Détection des devis > 60j sans acte commencé.
- **A5 Suivi Post-Extraction** : Alerte de suivi automatique à J+7.

**Catégorie B — Prédictions Comportementales :**
- **B1 Score No-Show** : Taux d'annulation > 40% sur 6 mois → alerte proactive.
- **B3 Créneau Maudit** : Détection d'un slot horaire annulé 3+ fois consécutives.
- **B4 Progression Ortho** : Estimation % d'avancement du traitement orthodontique.
- **B5 Prédiction Fin Ortho** : Extrapolation de la date de fin via intervalles moyens inter-séances.

**Catégorie C — Finance Prédictive :**
- **C1 Forecast Semaine** : Projection du chiffre d'affaires des 7 prochains jours.
- **C4 Taux de Conversion** : % des devis suivis d'un acte dans les 90 jours.
- **C5 Projection Mensuelle** : Historique 3 mois + forecast 6 mois pondéré par RDV planifiés.

**Catégorie D — Actions Anticipatoires :**
- **D1 Next Best Action (NBA)** : Toast actionnable au départ de la fiche patient.
- **D3 Protocole Auto-suggéré** : Détection du preset d'ordonnance le plus pertinent selon l'acte du jour.
- **D4 Ordonnance Anticipée** : Si RDV dans ≤ 14j, suggestion du protocole à préparer.

**Catégorie E — Scheduler & Notifications :**
- **E1 Daily Scheduler** : Thread daemon récursif — génère les alertes à 10s de démarrage, puis toutes les 24h.
- **E2 ProactiveAlert** : Table SQLite dédiée avec déduplication 24h et expiration 7j.
- **E3 Hub Alertes du Jour** : Widget Dashboard avec navigation directe patient + mark-as-read.
- **E5 Push Mobile FCM** : Notifications push Firebase vers l'app mobile compagnon.

---

### Panoramic ELITE Hub v2.0
- **Taxonomie Clinique** : Groupement des anomalies par spécialité (Endo, Paro, Chirurgie, Prothèse).
- **Multi-Tooth Selection** : Prise en charge native des bridges et zones infectieuses étendues (sélection FDI).
- **Numérotation FDI superposée** : Labels lisibles directement sur la radio, fond sombre, sélection par clic.
- **Live PDF Engine** : Génération instantanée de bilans structurés par secteur.

### Clinical Intelligence v1.5
- **Flash Summaries** : Diagnostics structurés (Squelettique, Dentaire, Stratégie) via Ollama/Llama3.2 et Gemini 1.5 Flash.
- **EliteAssistant** : Compagnon contextuel avec awareness du module actif, insights cliniques, D4 ordonnance anticipée.

### Studio Documentaire v4.x
- **Ordonnance Zero-Clavier** : Protocoles rapides, suggestion IA agentique, architecture galénique.
- **Devis / Note d'Honoraires** : Odontogramme FDI interactif, archivage automatique, anti-doublon SHA-256.
- **Échéancier** : Plan de paiement échelonné A5, CheckBox statuts, rappels WhatsApp.
- **Certificats / Documents Libres** : Templates vectoriels ReportLab Elite.
- **QR E-Verify** : Signature numérique injectée dans chaque ordonnance.

### Ghost Elite UI
- **Backdrop-blur** systématisé, CSS Variables synchronisées avec la BDD.
- **Odontogramme FDI Interactif** : Rendu vectoriel SVG haute fidélité (surfaces M, O, D, MOD).
- **Dynamic Branding v4.6** : 6 thèmes, curseurs couleur avec persistence BDD.

### App Mobile ZKA
- **Onboarding QR** : Appairage Zero-Knowledge via token éphémère.
- **Cockpit Mobile** : Agenda, Performance, Finance, Labo, Sécurité en temps réel sur LAN.
- **Push FCM (E5)** : Réception des alertes proactives du scheduler quotidien.
- **Offline Queue** : Actions POST/PUT/PATCH mises en file hors connexion (Workbox Background Sync).

---

## Architecture

Voir **[ARCHITECTURE.md](./ARCHITECTURE.md)** pour l'arborescence complète commentée et les flux de données.

### Vue d'ensemble

```
Backend  FastAPI :8005  →  SQLite (digital_crown.db)
                        →  ReportLab (PDF génération)
                        →  ONNX Runtime (panoramique)
                        →  Ollama (LLM local)
                        →  Firebase (licence + push FCM)

Frontend React :5173   →  Zustand (état global)
                        →  Axios (API client, refresh JWT auto)
                        →  Framer Motion + TailwindCSS
                        →  Vite PWA (Service Worker offline)
```

---

## Installation & Démarrage

### Windows (Quick Launch)
```powershell
./Start_DigitalCrown.bat
```

### Développement manuel
```bash
# Backend
venv\Scripts\activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8005

# Frontend (autre terminal)
cd frontend && npm run dev
```

- API Docs : `http://localhost:8005/docs`
- App : `http://localhost:5173`
- Mobile (LAN) : `http://<ip-locale>:5173`

---

## Sécurité & Éthique
- **Zéro Data Leak** : Validation Pydantic stricte, multi-tenant isolé par `employer_id`.
- **Archivage Immuable** : SHA-256 anti-doublon sur tous les documents cliniques.
- **Local-First AI** : SLM local (Ollama) pour confidentialité maximale des données patient.
- **Zero-Knowledge Architecture** : Données mobiles chiffrées AES-GCM, clé dérivée hors serveur.
- **License System** : Coffre-fort chiffré AES-256 + anti-rollback temporel + grâce 72h offline.

---

## Équipe & Version
**Staff Engineering — Digital Crown SANINOVA**
*Dernière mise à jour : 12 Juin 2026 — CrownBot v3.0 + Échéancier PDF + Analytics réel (sprint crownbot)*

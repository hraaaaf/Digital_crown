# RAPPORT D'AUDIT GLOBAL — DigitalCrown
**Date :** 02/06/2026  
**Panel :** 8 jurys spécialisés (Frontend, UX/UI, Backend, Sécurité, DevOps, BDD, IA/ML, Médical)  
**Méthode :** Audit indépendant, sévère, basé sur lecture de code source réel

---

## SCORES PAR DOMAINE

| Jury | Domaine | Score | Verdict |
|------|---------|-------|---------|
| Ingénieur Frontend | React/TS, hooks, bundle | **47/100** | ❌ Insuffisant |
| Expert UX/UI Médical | Navigation, flux, accessibilité | **54/100** | ⚠️ Passable |
| Architecte Backend | FastAPI, API design, multi-tenant | **58/100** | ⚠️ Passable |
| Expert Sécurité | Auth, RGPD, vulnérabilités | **52/100** | ⚠️ Passable |
| DevOps/Docker/CI-CD | Infrastructure, déploiement | **14/100** | 🔴 CRITIQUE |
| Panel Médical (×3) | Dentiste + Orthodontiste + Radiologue | **61/100** | ⚠️ Passable |
| DBA Performance | SQLite, schéma, migrations | **54/100** | ⚠️ Passable |
| Expert IA Médicale | YOLO, LLM, hallucinations | **51/100** | ⚠️ Passable |

## SCORE COMPOSITE PONDÉRÉ : **49/100**

> Pondération : Sécurité 20%, Médical 20%, Backend 15%, IA 10%, BDD 10%, Frontend 12%, UX/UI 8%, DevOps 5%

---

## TOP 15 — PROBLÈMES LES PLUS URGENTS (multi-jurys)

### 🔴 NIVEAU 0 — À CORRIGER DANS LES 24H

**P0.1 — Credentials admin hardcodés dans 4 fichiers source**
- `backend/seed_user.py:15` → `admin_password = "admin"`
- `backend/routers/clinics.py:103` → `pwd_context.hash("admin123")`
- `backend/main.py:38`, `backend/routers/superadmin.py:16` → email superadmin en dur
- Impact : N'importe qui avec accès au repo peut se connecter en superadmin. CVSS 9.8.
- Détecté par : Backend (C1/C2/C3), Sécurité (CRIT-1/CRIT-2), DevOps (C-3)
- Fix : Variables d'environnement + rôle DB `is_superadmin`, purger l'historique git (`git filter-branch`)

**P0.2 — Endpoint `/api/clinics/extract-card` sans authentification**
- `backend/routers/clinics.py:333` — upload de fichier arbitraire, écriture filesystem, zéro auth
- CVSS 8.6. Détecté par : Backend (C4), Sécurité (CRIT-3)
- Fix : Ajouter `Depends(get_current_user)` + validation MIME + limite de taille

**P0.3 — Mode simulation panoramique silencieux**
- `backend/ai_models/panoramic_service.py:87-88` — si le modèle ONNX manque, renvoie des détections fictives sans signaler la simulation
- Impact : praticien reçoit de faux diagnostics sans le savoir. Risque patient DIRECT.
- Détecté par : IA (RC-3), Médical
- Fix : Retourner explicitement `status: "SIMULATION_MODE"`, bloquer l'affichage clinique

**P0.4 — Rapport panoramique auto-contradictoire**
- Les phrases de normalité ("ATM respectées", "sinus normaux") sont hardcodées même quand l'IA a détecté ces pathologies
- Impact : document médico-légal erroné signé par le praticien. Risque juridique.
- Détecté par : Médical (CRITIQUE 4), IA
- Fix : Conditionner chaque phrase de normalité à l'absence de détection correspondante

---

### 🟠 NIVEAU 1 — À CORRIGER CETTE SEMAINE

**P1.1 — Token JWT dans localStorage (XSS persistant)**
- `frontend/src/services/api.ts:17-18` — access token + refresh token en localStorage 30 jours
- Vol de session possible via toute XSS. CVSS 8.1.
- Détecté par : Sécurité (MAJEUR-1), Frontend (M8), DevOps (M-6)
- Fix : Cookies HttpOnly + Secure + SameSite=Strict

**P1.2 — N+1 queries catastrophiques**
- `backend/routers/mobile.py:251` — 1001 requêtes pour 500 patients au chargement mobile
- `backend/routers/intelligence.py:86` — 61 requêtes pour 20 RDV du briefing
- Détecté par : Backend (M1/M2/M3), BDD (M1/C4)
- Fix : Jointures SQLAlchemy + aggregations SQL + pagination

**P1.3 — Données médicales exclusivement en localStorage sans persistance backend**
- `frontend/src/features/patients/components/ClinicalHub.tsx:127-131` — odontogramme et plan de traitement jamais envoyés au backend, seulement en localStorage
- Impact : perte de données au changement de machine/navigateur. Illégal pour un dossier médical.
- Détecté par : UX/UI (C1), Frontend (M5)
- Fix : Appel API de sauvegarde synchrone + indicateur de statut de sync

**P1.4 — Double paracétamol en pédiatrie**
- `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudio.tsx`
- Le preset "Extraction Sagesse" enfant peut générer 2 lignes PARACÉTAMOL → surdosage
- Impact : risque patient DIRECT (surdosage chez enfant)
- Détecté par : Médical (CRITIQUE 1), IA
- Fix : Déduplication des molécules identiques AVANT application du preset

**P1.5 — Association antibiotique quadruple (AUGMENTIN + BI-RODOGYL)**
- Preset "Abcès/Infection" = Amoxicilline + Ac. clavulanique + Spiramycine + Métronidazole
- Aucune guideline internationale ne valide cette quadrithérapie pour un abcès dentaire simple
- Impact : sur-antibiothérapie, résistances, effets indésirables non justifiés
- Détecté par : Médical (CRITIQUE 2)
- Fix : Réviser le preset → Amoxicilline seule OU Amoxicilline + Métronidazole

**P1.6 — Sécurité by-passable via les presets d'ordonnance**
- Si l'évaluation IA backend échoue (timeout/erreur), `assessment = null` → aucun blocage allergie/grossesse ne s'active lors de l'application d'un preset
- Impact : NSAID chez femme enceinte, Pénicilline chez allergique → risque patient DIRECT
- Détecté par : Médical (CRITIQUE 3), IA
- Fix : Vérification déterministe côté frontend indépendante de l'assessment IA

**P1.7 — Seuils de détection panoramique cliniquement inacceptables**
- `backend/ai_models/panoramic_service.py:112-117` — "Lésion Périapicale" à 0.12 (12% de confiance)
- Standards médicaux : minimum 0.50, idéalement 0.70+ pour des alertes cliniques
- Détecté par : IA (RC-1), Médical, Radiologue
- Fix : Recalibration des seuils + évaluation sur cohorte marocaine

---

### 🟡 NIVEAU 2 — À CORRIGER CE SPRINT

**P2.1 — Aucun Dockerfile, aucune CI/CD**
- Zéro containerisation de l'application, zéro pipeline automatisé
- Score DevOps 14/100 : le problème le plus grave en infrastructure
- Fix : Dockerfile multi-stage backend + frontend, GitHub Actions minimal (test + build)

**P2.2 — Backup SQLite corrompu possible**
- `backend/services/backup_service.py:29` — `shutil.copy2()` sur fichier actif sans WAL flush
- Fix : Utiliser `sqlite3.Connection.backup()` ou `VACUUM INTO`

**P2.3 — 134 console.log en production + 163 `any` TypeScript**
- Fuite de données cliniques dans la console navigateur
- Détecté par : Frontend (M1/M2)
- Fix : `eslint --fix` + plugin `no-console`, typage strict des interfaces

**P2.4 — Absence de security headers HTTP**
- Pas de CSP, X-Frame-Options, HSTS, X-Content-Type-Options
- Détecté par : Sécurité (MAJEUR-2)
- Fix : Middleware `SecurityHeadersMiddleware` 20 lignes dans `main.py`

**P2.5 — Isolation multi-tenant manquante sur `check_dossier_availability`**
- `backend/routers/patients.py:59` — pas de filtre `employer_id` → fuite cross-tenant
- Détecté par : Backend (C5), Sécurité (MINEUR-2), BDD (M4)
- Fix : Ajouter `employer_id` au filtre + unique constraint `(employer_id, numero_dossier)`

---

### 🟢 NIVEAU 3 — DETTE TECHNIQUE (prochain sprint)

**P3.1 — Module orthodontique cliniquement insuffisant**
- 3 questions binaires ne constituent pas un bilan ODF. Pas de Classe d'Angle, pas de DDM clinique, pas d'IOTN.
- Détecté par : Orthodontiste
- Fix : Refonte du wizard ODF avec indicateurs cliniques standardisés

**P3.2 — Normes céphalométriques non adaptées à la population marocaine**
- Normes Ricketts/Tweed (1960, caucasiennes) utilisées sans adaptation ethnique
- Détecté par : Radiologue, Orthodontiste
- Fix : Intégrer les normes de référence méditerranéennes (Mouakeh ou équivalent)

**P3.3 — Race conditions sur recherche sans AbortController**
- `frontend/src/features/agenda/AgendaModal.tsx:100-119` — 5 useEffects sans cleanup
- Détecté par : Frontend (C2/M4)

**P3.4 — Montants financiers en Float (erreurs d'arrondi)**
- `backend/models.py:267,397,738,761,785` — Float IEEE 754 pour les honoraires médicaux
- Fix : Migration vers `Numeric(10,2)`

**P3.5 — `window.confirm()` natif dans 18 endroits**
- Bloque le thread UI, incompatible avec Framer Motion, non testable
- Détecté par : Frontend (C5), UX/UI (m7)

---

## PROBLÈMES PAR DOMAINE (résumé)

| Domaine | Critiques | Majeurs | Mineurs |
|---------|-----------|---------|---------|
| Frontend | 5 | 9 | 10 |
| UX/UI | 5 | 8 | 9 |
| Backend | 7 | 10 | 7 |
| Sécurité | 4 | 8 | 8 |
| DevOps | 6 | 6 | 5 |
| BDD | 4 | 7 | 7 |
| IA/ML | 5 | 7 | 6 |
| Médical | 4 | 5 | 8 |
| **TOTAL** | **40** | **60** | **60** |

---

## ROADMAP DE REMÉDIATION

### Semaine 1 (P0 — Sécurité vitale)
- [ ] Supprimer credentials hardcodés + purger historique git
- [ ] Authentifier `/extract-card`
- [ ] Fix rapport panoramique (phrases conditionnelles)
- [ ] Fix mode simulation → flag explicite, bloquer UI clinique
- [ ] Fix double paracétamol pédiatrique
- [ ] Fix preset antibiotique Abcès

### Semaine 2 (P1 — Risques patients)
- [ ] Persistance odontogramme + plan traitement → backend
- [ ] Fix sécurité presets (vérification déterministe grossesse/allergie indépendante de l'IA)
- [ ] Recalibration seuils YOLO (minimum 0.40-0.50)
- [ ] Tokens → cookies HttpOnly
- [ ] Security headers middleware

### Semaine 3-4 (P2 — Infrastructure et performance)
- [ ] Dockerfile backend + frontend (multi-stage)
- [ ] GitHub Actions CI minimal (test + build + lint)
- [ ] Fix N+1 queries (mobile snapshot, briefing, superadmin)
- [ ] Fix backup SQLite (sqlite3.Connection.backup)
- [ ] Fix isolation multi-tenant check_dossier
- [ ] Disclaimer IA visible dans l'UI (pas seulement dans les PDF)

### Sprint suivant (P3 — Qualité)
- [ ] Éliminer les 134 console.log + typer les 163 `any`
- [ ] Remplacer 18× window.confirm par des modales React
- [ ] AbortController sur les useEffects réseau
- [ ] Montants financiers → Numeric(10,2)
- [ ] Module ortho : wizard clinique complet
- [ ] Normes céphalométriques méditerranéennes

---

## QUESTIONS SANS RÉPONSE (nécessitent vérification manuelle)

1. `git log --all -- backend/core/firebase_creds.json` — ce fichier a-t-il été commité ?
2. SQLCipher est dans requirements.txt — est-il RÉELLEMENT activé sur les DB de prod ?
3. Déploiement : LAN desktop (PyInstaller) ou SaaS cloud ? Impact majeur sur la surface d'attaque.
4. Le modèle YOLO panoramique — sur quel dataset validé a-t-il été entraîné ? Y a-t-il des métriques AUC/Sensitivity publiées ?
5. L'action "Forcer Allergie" est-elle loggée dans AuditLog côté backend ?
6. Y a-t-il un contrat DPA avec Google (Gemini) pour les données patient anonymisées ?

---

*Rapport généré le 02/06/2026 par audit multi-agents DigitalCrown*

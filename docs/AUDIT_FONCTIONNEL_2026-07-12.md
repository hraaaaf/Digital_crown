# Audit fonctionnel global — 2026-07-12

Audit basé exclusivement sur le code réel (aucun document comme source), avec deux
audits experts dédiés (céphalométrie IA, UX/UI) et une analyse directe de la couche
proactive. Complète `docs/GLOBAL_APP_AUDIT_2026-07-11.md` (audit produit/roadmap) par
un scoring par fonctionnalité et des découvertes code nouvelles.

## Verdict global : 6/10

Squelette métier solide et différenciant, miné par trois maladies transversales :

1. **La table `Acte` (13,6% de couverture) contamine tout** — finances, alertes
   proactives, scoring patient, résumé clinique. C'est LE défaut structurel
   (`UNIFY-ACT-PERSISTENCE-1`).
2. **Du faux présenté comme du vrai** — valeurs céphalo par défaut narrées comme des
   mesures, chart Dashboard aux données massées, boutons factices, badge "Elite Cloud"
   sur une app on-premise. Risque de confiance : un seul faux découvert et le praticien
   ne croit plus les alertes anticoagulants (réelles et excellentes).
3. **Pas de design system** — 6 implémentations de modale, 4 palettes de statuts RDV,
   3 loaders, 861 textes ≤10px pour une cible 45+ ans.

## Scores par fonctionnalité

| Fonctionnalité | Score | Verdict |
|---|---:|---|
| Ops / backups / releases | 8,5 | Releases immuables, provenance vérifiée, pg_dump routé par moteur |
| Agenda / RDV | 8 | Créneau→modale pré-remplie, conflits temps réel, ajout d'acte inline |
| Documents PDF / ordonnances | 8 | 14 générateurs, alertes anticoagulants/MRONJ/grossesse réelles, garde anti-perte |
| Salle d'attente | 7,5 | Kanban 4 colonnes, avancement 1 clic, auto-refresh |
| Sécurité / isolation tenant | 7,5 | `assert_patient_access` systématique, médias authentifiés — MAIS suppression patient définitive en 2 clics |
| Dossier patient / Journey | 7 | URL-state, timeline par phases ; perte d'état entre onglets, `return null` sur erreur |
| Bot assistant | 6,5 | LLM local + fallback regex, permissions par intent (non testé en profondeur) |
| Stock | 6 | CRUD basique avec seuils, fonctionnel |
| Céphalométrie | 5,5 | Formules justes, pipeline dangereux autour (voir §Céphalo) |
| UX/UI global | 5,5 | Parcours quotidiens bons, couche "Elite/Ghost" incohérente, a11y 3/10 |
| Couche proactive | 5 | Riche en idées, cassée en exécution (voir §Proactif) |
| Finances / comptabilité | 4 | Aveugle pour ~86% des patients ; deux chemins d'encaissement non rapprochés |
| Analytics / Dashboard | 4 | Le dentiste ne voit pas sa journée ; chart aux valeurs massées ; boutons factices |
| Scoring patient | 3 | Patient vide = 100 pts = PLATINUM par défaut |

Panoramique et labo : non audités en profondeur dans cette passe.

## Céphalométrie — 5,5/10 (audit expert)

**Formules squelettiques correctes** : SNA/SNB/ANB/Wits/McNamara/FMA vérifiées —
bonnes conventions de signe, bonnes normes, validateur de cohérence branché avant PDF,
fallback ONNX→PyTorch→manuel propre. Aucune erreur clinique de formule trouvée.

**Trois découvertes critiques (P0 clinique)** :

1. **Calibration par défaut silencieuse** (`backend/services/cephalo_service.py:43`) :
   `mm_ratio = auto_ratio if auto_ratio else 0.1`. Quand l'auto-calibration échoue,
   toutes les mesures mm (Wits, McNamara Co-A/Co-Gn, Ligne E, surplomb...) sont
   calculées avec un ratio arbitraire — fausses de ±30-50% mais plausibles, affichées
   avec statut Normal/High/Low et interprétation clinique.
2. **Garde-fou frontend mort** (`frontend/src/features/ortho/CephaloStatsTable.tsx:379`) :
   attend `results.calibration_status === 'unverified'` — champ que le backend ne
   produit **jamais** (grep backend : zéro occurrence). Le badge "⚠ Calibration
   requise" et le barré des valeurs ne s'affichent jamais.
3. **Analyse esthétique fabriquée** : le modèle SOTA émet `Ls_soft`/`Li_soft`/`Sn_soft`
   (`sota_vision_service.py:22`), le moteur cherche `Ls`/`Li`/`Sn`
   (`cephalo_engine.py:343-344, 483-484`) → jamais trouvés → Ligne E et angle
   nasolabial jamais calculés → la synthèse narre des **valeurs par défaut**
   (`val_e_ls=0.0`, `val_nla=102.0`, lignes 537-539) comme des mesures : "Profil droit
   selon la ligne E. Angle nasolabial normal (102°)" (ligne 623).

**Autres (P1)** : scores de confiance ONNX jetés (`cephalo_service.py:37`) ; apex
incisif parfois synthétisé en **imposant IMPA=90°** (`vision_service.py:204-246`) puis
mesuré comme s'il était détecté ; heuristique `180 - angle` fragile pour IMPA/I-F ;
DDM dérivée d'un IMPA potentiellement synthétique (`cephalo_service.py:137`) ;
`_MM_METRICS` du validateur ne couvre pas les longueurs McNamara affichées.

**P2** : aucun test de bout en bout de `calculate_metrics` avec landmarks synthétiques
d'angle attendu connu.

## Couche proactive — 5/10

**Ce qu'elle fait** : scheduler quotidien in-app (`daily_scheduler.py`) + ~15
déclencheurs (`habits_engine.py`) : impayés, rappel détartrage 6/12 mois, gap ortho
>45j, risque d'abandon, suivi post-extraction J+7, no-show, créneau maudit, prédiction
fin ortho, rappels notes d'honoraires semestrielles, RDV demain sans plan, pression
matériaux (concentration d'actes → alerte stock). Push + mémoire d'audit + dédup.

**Défauts trouvés** :
1. **Crash silencieux** : `backend/routers/intelligence.py:237` fait `a.patient.nom`
   sans garde ; les alertes stock ont `patient_id=None` (`daily_scheduler.py:151`) →
   500 sur `/intelligence/alerts/today` dès qu'une alerte stock existe ; le Dashboard
   avale l'erreur (`Dashboard.tsx:250`, catch silencieux) → toutes les alertes
   disparaissent sans bruit.
2. **Alertes fantômes** : l'endpoint filtre `created_at >= today_start` mais la dédup
   (24h-7j) empêche la recréation → une alerte non lue d'hier ne réapparaît jamais.
3. **Aveugle à ~86% des patients** : "patient actif" = a un `Acte` <90j
   (`daily_scheduler.py:70`) + ortho actifs.
4. **Scoring PLATINUM par défaut** : `patient_scoring_service.py:17,43` — les deux
   indices démarrent à 100, un patient sans historique = grade PLATINUM.
5. Toast NBA à chaque ouverture de dossier + bulle animée 2 min : bruit non sollicité.

**Améliorations** : garde `if a.patient` + affichage des non-lues (2 fixes ciblés) ;
"patient actif" basé sur Appointment/Payment/DocumentArchive (extension
UNIFY-ACT-PERSISTENCE-1) ; scoring neutre à 50 avec historique minimal requis ; digest
matinal au lieu de toasts.

## UX/UI — 5,5/10 (audit expert, résumé)

**Top problèmes par impact quotidien** :
1. **Le dentiste ne voit pas sa journée** : le widget file du jour n'est affiché que
   pour les rôles SANS accès compta (`Dashboard.tsx:526`) ; le propriétaire voit un
   chart hebdo aux valeurs massées (`pCount = Math.round((val-5)/10)`, ligne 581).
2. **Lenteur structurelle** : `ProtectedRoute` re-valide backend+auth+init à chaque
   navigation (`App.tsx:68-112`, 3-4 appels séquentiels) + double transition 0,4s
   (`MainLayout.tsx:86-101`).
3. **Fonctionnalités factices** : "Elite Cloud Connecté" (`Dashboard.tsx:422`),
   "Combler les trous" (fausse promesse 2s, `Analytics.tsx:208-218`), "Ghost Mutuelle
   a scindé le devis" (ne scinde rien, `DocumentHub.tsx:330`), insight Platinum pour
   tous (`DocumentHub.tsx:256-265`), score `72 + items×2` (ligne 368).
4. **Suppression définitive patient en 2 clics** (`PatientList.tsx:476-508`), documents
   inclus, sans archivage ni confirmation forte — contradiction directe avec la règle
   "jamais perdre de donnée patient".
5. **Lisibilité/clavier** : 861 textes ≤10px (111 fichiers), actions en
   `opacity-0 group-hover`, pas de focus trap/Escape sur les modales, navigation
   clavier impossible sur listes/grilles.

**Points forts** : flux agenda→salle d'attente excellent ; garde-fous cliniques
sérieux (différenciant) ; PatientJourney + état dans l'URL.

**Dette notable** : badge assurance copié 3× (libellés divergents FAR vs MUT_FAR) ;
`hasAccess()` dupliqué avec défauts divergents Sidebar/Dashboard (bug latent de
permissions) ; theming `var(--primary)` court-circuité par `#003380` en dur (agenda,
AddPatientForm) ; nom de cabinet en dur dans `Header.tsx:30-36` ; bus d'événements
`window.dispatchEvent` comme état global ; `PatientDetails.tsx:164` `return null` sur
erreur = écran blanc.

## Feuille de route consolidée

**P0 — confiance clinique et financière**
1. `UNIFY-ACT-PERSISTENCE-1` — débloque finances + proactif + scoring
2. Céphalo : produire `calibration_status` backend + barrer les mm non calibrés ;
   corriger le mapping `*_soft` ; "non évaluable" au lieu de narrer des défauts
3. Purger les fake features (effort S, impact confiance majeur)

**P1 — quotidien**
4. Fix crash + visibilité des alertes proactives
5. File du jour visible pour tous les rôles
6. Soft-delete patient avec confirmation forte
7. Redirection post-création patient vers le dossier + CTA "Prendre RDV"

**P2 — structurel**
8. Auth/init vérifiés une fois par session
9. Mini design system (Modal, StatusBadge, loader unique, plancher 11-12px)
10. Généraliser React Query

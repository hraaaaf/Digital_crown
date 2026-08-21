# Digital Crown — Onboarding ↔ Réglages / Clinic Identity Reconciliation

Status: **ACTIVE — P0 Audit & Truth Map**

Branch: `agent/onboarding-settings-reconciliation`
Base at creation: `master@2bfe24fc62a79af0a13852cd091bd65c3e0fd384`

## Goal

Établir une seule vérité cohérente pour l’identité et la configuration du cabinet/clinique/centre dentaire depuis le premier onboarding jusqu’aux Réglages, puis vérifier tous les consommateurs produit.

Chaîne canonique à réconcilier :

`Premier onboarding → modèle de données → backend/API → persistance → Réglages → consommateurs produit → reprise de session`

Aucun déploiement Vercel sans autorisation explicite.

## Succès global

- [ ] Inventaire exhaustif des données demandées dans l’onboarding
- [ ] Inventaire des données correspondantes dans Réglages
- [ ] Source de vérité backend/DB identifiée pour chaque donnée
- [ ] Doublons, champs morts, fallbacks trompeurs et sources concurrentes identifiés
- [ ] Modèle métier canonique défini
- [ ] Onboarding réduit au minimum réellement nécessaire
- [ ] Réglages alignés sur le modèle canonique
- [ ] Lecture/écriture/persistance/reload/restart vérifiés
- [ ] Permissions et multi-utilisateurs vérifiés
- [ ] Compatibilité legacy/migration vérifiée
- [ ] Tous les consommateurs produit utilisent la bonne donnée
- [ ] Toute UI touchée : BEFORE → Goal → mockup → AFTER → score
- [ ] Régression raisonnable verte

## Roadmap

### P0 — Audit & Truth Map — ACTIVE
Aucune modification produit.

Preuve attendue : code réel + routes + composants + types + API + modèles DB + tests existants + captures BEFORE + matrice de réconciliation.

Questions à résoudre :
1. Que demande actuellement l’onboarding ?
2. Où chaque donnée est-elle stockée ?
3. Que montre actuellement Réglages ?
4. Quelles données sont communes aux deux ?
5. Où sont les divergences ?
6. Quelles données sont mortes ?
7. Quelles données sont dupliquées ?
8. Quelles données sont trompeuses ?
9. Quels consommateurs dépendent de chacune ?
10. Quel est le modèle canonique le plus simple ?

Matrice canonique :

| Donnée métier | Onboarding | Réglages | Backend/DB | Source de vérité | Modifiable | Consommateurs | Verdict |
|---|---|---|---|---|---|---|---|

Verdicts : `KEEP`, `KEEP + FIX`, `MERGE`, `MOVE`, `REMOVE`, `MISSING`, `DUPLICATE`, `DEAD`, `FAKE/FALLBACK`, `NEEDS DECISION`.

Rechercher explicitement :
- données dupliquées ;
- defaults/fallbacks trompeurs ;
- données saisies mais jamais utilisées ;
- données configurables uniquement à l’onboarding ;
- données Réglages absentes de l’onboarding ;
- écrasements ;
- sources concurrentes DB/localStorage/config/context ;
- mélange User / Practitioner / Organization / Membership.

### P1 — Canonical Data Model
Définir ownership et source de vérité la plus simple.

### P2 — Onboarding Product Reconciliation
Classer chaque champ : `REQUIRED NOW`, `OPTIONAL NOW`, `LATER IN SETTINGS`, `REMOVE`.

### P3 — Settings Reconciliation
Aligner Réglages avec la source canonique.

### P4 — Backend / Persistence / Permissions
Garantir lecture/écriture, validation, persistance, erreurs et permissions réelles.

### P5 — Legacy Migration
Fresh install + installation existante complète/partielle + champs renommés/manquants + upgrade sans ré-onboarding forcé.

### P6 — Consumer Reconciliation
Vérifier que tous les consommateurs lisent la même vérité canonique.

### P7 — UX Certification
BEFORE → Goal visuel → mockup → implémentation → AFTER → comparaison → score.

### P8 — Regression & Closeout
Tests globaux, documentation canonique, cohérence roadmap/état Git.

## Tests obligatoires

- T1 Fresh install
- T2 Reload
- T3 Restart
- T4 Edit from Settings
- T5 Backend GET/SAVE failure fail-closed
- T6 Validation + Unicode/arabe/français si pertinent
- T7 Permissions
- T8 Multi-user
- T9 Consumer truth
- T10 Legacy

## Scénarios métier

- Chirurgien-dentiste seul
- Cabinet avec assistant(e)
- Clinique multi-praticiens
- Centre dentaire / gestion centralisée

## Règles d’exécution

- Ne jamais supposer qu’un champ UI est persisté : vérifier jusqu’à la source finale.
- Ne jamais considérer une réponse API correcte sans vérifier son consommateur.
- Pas de redesign avant le modèle métier.
- Préférer une seule source de vérité.
- Une CI en cours n’arrête pas le chantier : poursuivre tout travail indépendant.
- Pour toute UI touchée : captures BEFORE + Goal + mockup + AFTER + score.
- Aucun Vercel sans autorisation explicite.
- Ne jamais créditer un lot sans preuve observable.
- Pour un benchmark lourd : préparation complète → 1 commit final → 1 run.

## Reprise / Handover

Chantier : `Onboarding ↔ Réglages`
Lot courant : `P0 — Audit & Truth Map`
Next exact : cartographier onboarding → Réglages → backend/DB → consommateurs, puis remplir la matrice de vérité avant toute modification produit.

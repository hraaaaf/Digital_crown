# Digital Crown — MOB-5C Notifications Mobile — Audit

Status: AUDIT LOCKED / BEFORE UI
Date: 2026-09-05
Repo: `hraaaaf/Digital_crown`
Branch: `ux/mobile-notifications-mob5c`
Baseline: `8891c771f1d77f0ab9347682609b0460881ae2a8`

## Goal
Réutiliser les alertes et le push existants pour proposer sur mobile un centre d’alertes actionnables, priorisé et filtré par permissions, sans créer un deuxième moteur de notifications.

## Constat vérifié

### 1. Source in-app existante
`backend/routers/mobile.py` expose déjà `GET /api/mobile/notifications` à partir de `models.ProactiveAlert`.

Le endpoint :
- scope par `employer_id` ;
- ne retourne que les alertes non lues ;
- exclut les alertes expirées ;
- respecte `snoozed_until` ;
- masque les patients soft-deleted ;
- limite la réponse à 20 alertes ;
- ordonne par priorité puis récence.

### 2. RBAC financier existant
Les préfixes suivants sont considérés financiers :
- `OVERDUE_PAYMENT`
- `HIGH_VALUE_RISK`
- `ORTHO_SEMESTER_...`

Ils ne sont exposés qu’aux utilisateurs disposant de `accounting` ou `payments`.

### 3. Push OS existant
`backend/services/mobile_push_service.py` envoie un signal générique uniquement :

```json
{"kind":"alerts"}
```

Le payload OS ne contient donc pas le détail patient. Le backend cible uniquement des appareils mobiles actifs, appairés, non révoqués et appartenant au même `employer_id`, puis applique `user_can_receive_mobile_notification`.

Conclusion : conserver le push comme signal de réveil, puis charger les données sensibles depuis l’API authentifiée.

### 4. Stock
`backend/routers/stock.py` possède déjà un signal métier tenant-scopé de stock bas basé sur `quantite <= seuil_alerte` et `employer_id`.

Ce signal est candidat à MOB-5C, mais la création d’un `ProactiveAlert` stock doit être vérifiée/ajoutée sans dupliquer la logique Stock.

### 5. Frontdesk
Les demandes de rendez-vous utilisent déjà le même tenant et la permission `agenda` dans MOB-5B. Elles sont une source candidate d’alertes actionnables, mais ne doivent pas être dupliquées artificiellement si aucun producteur `ProactiveAlert` n’existe encore.

### 6. Labo
`backend/routers/lab_jobs.py` a été observé avec une lecture globale `db.query(models.LabJob).all()` sans filtre `employer_id` visible dans ce routeur.

Décision de sécurité MOB-5C : **aucune alerte labo agrégée tant que l’isolation tenant du domaine Labo n’est pas prouvée ou corrigée.**

## Contrat produit recommandé

MOB-5C réutilise `ProactiveAlert` comme source de vérité in-app.

Objet mobile minimal :
- `id`
- `patient_id` optionnel
- `patient_name` optionnel
- `type`
- `title`
- `message`
- `priority`
- `created_at`
- `action` dérivée de manière allowlistée côté client/serveur

Aucune URL arbitraire venant de la DB ne doit être exécutée directement par le mobile.

## Catégories initiales sûres

| Domaine | État | MOB-5C |
|---|---|---|
| Finance | Producteur/policy existants | Inclure selon RBAC |
| Alertes patient non financières | `ProactiveAlert` existant | Inclure si renvoyées par endpoint |
| Stock bas | Signal tenant-scopé prouvé | Préparer extension, ne pas inventer de persistance |
| Frontdesk | Métier tenant-scopé prouvé | Préparer extension, éviter doublon |
| Labo | Isolation tenant non prouvée | Exclure |
| SuperAdmin/Sécurité | Pas encore nécessaire au MVP MOB-5C | Hors premier écran |

## UX cible
- entrée secondaire `Plus → Notifications` ;
- conserver les 5 boutons permanents ;
- compteur non-lu dans `Plus` si la donnée est disponible sans coût disproportionné ;
- écran compact : priorité, titre, contexte, heure, action ;
- filtres simples `Toutes / Prioritaires` au maximum pour V1 ;
- aucun réglage lourd sur mobile ;
- aucun bruit décoratif ;
- état vide explicite ;
- erreurs inline ;
- refresh manuel + refresh à l’ouverture.

## Deep-links
Les actions doivent utiliser une allowlist de destinations mobiles existantes, par exemple :
- alerte patient → `patients` + contexte patient si supporté ;
- finance → `finance` si permission ;
- Frontdesk → `frontdesk` si ajouté plus tard comme type d’alerte ;
- stock → `stock` après MOB-5D.

Fallback sûr : rester sur Notifications si aucun contexte/action autorisé n’est résolvable.

## BEFORE
Baseline fonctionnelle : aucune entrée `Notifications` dans la navigation mobile canonique observée à ce stade. Le backend possède déjà le endpoint et le push, mais pas de cockpit Notifications certifié dans le shell MOB-5.

## Preuve requise
BEFORE → Goal UI → mockup/référence → implémentation → AFTER 390×844 / 430×932 / 768×1024 → tests RBAC/tenant/routing → build → runtime → comparaison → score visuel.

Deployment: none. No Vercel deployment authorized.

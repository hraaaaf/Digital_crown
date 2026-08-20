# R1 — Shell / doctrine de sauvegarde — Goal visuel

Date : 2026-08-20
Repo : `hraaaaf/Digital_crown`
Base immuable BEFORE : `2a6bfd8a10baddf770fed5e2ffbecc3f65f4468d`
Branche : `settings-r1-save-doctrine`

## Goal

Rendre la sauvegarde des Réglages explicite et fidèle au comportement métier réel : une seule sauvegarde partagée pour les données de configuration staged, aucune fausse sauvegarde globale sur les domaines atomiques, et protection contre la fermeture/rechargement avec changements staged non enregistrés.

## Doctrine cible

### Staged, sauvegarde partagée

- Profil Cabinet
- Design & Ambiance
- Performance & Assistance

Ces trois onglets écrivent dans `useSettingsStore.profile` / `contacts`, posent `isDirty=true`, puis persistent ensemble via `PUT /clinics/me`.

### Atomique, actions propres

- Catalogue Actes
- Horaires & Agenda : horaires via son propre dirty/save ; fermetures atomiques
- Sécurité & Backup
- Mon Équipe

Aucun bouton global de sauvegarde de profil ne doit être affiché sur ces surfaces.

## Wireframe / référence visuelle

### Onglet staged avec changements

```text
┌──────────────────────────────────────────────────────────────────┐
│ ⚠ Modifications de la configuration non enregistrées           │
│ Profil, Design & Ambiance et Performance & Assistance partagent │
│ cette sauvegarde.                         [Enregistrer la config] │
└──────────────────────────────────────────────────────────────────┘
│ contenu de l’onglet                                              │
```

Le bandeau est sticky dans la surface principale et reste visible pendant le scroll.

### Après succès backend

```text
┌──────────────────────────────────────────────────────────────────┐
│ ✓ Configuration enregistrée                                     │
│ Les réglages ont été confirmés par le backend.                   │
└──────────────────────────────────────────────────────────────────┘
```

### Onglet atomique alors qu’une config staged reste dirty

```text
Navigation
...
┌──────────────────────────────┐
│ ⚠ Configuration non         │
│   enregistrée               │
│ Revenez à Profil, Design ou │
│ Performance pour enregistrer│
└──────────────────────────────┘

[contenu atomique]
AUCUN bouton global « Mettre à jour le Profil »
AUCUN bouton « Enregistrer la configuration »
```

## Succès observable

1. BEFORE capturé depuis le SHA immuable `2a6bfd8a...` sur 1440/1024/768/430/390 pour les 7 onglets ADMIN.
2. AFTER capturé sur les mêmes onglets et viewports.
3. Profil / Design / Performance : un seul bandeau partagé visible quand `isDirty`, avec libellé `Enregistrer la configuration`.
4. Catalogue / Agenda / Sécurité / Équipe : aucun bouton global de sauvegarde ; les actions atomiques existantes restent intactes.
5. Quand une config staged reste dirty sur un onglet atomique, un avertissement passif reste visible dans le shell.
6. Le bouton local legacy du Profil n’est plus visible ; le shell est l’unique propriétaire UI de la sauvegarde staged.
7. `updateProfile()` ne persiste plus les préférences runtime immédiatement.
8. `saveProfile()` ne commit thème/runtime qu’après succès `PUT /clinics/me` ; échec backend => `isDirty=true`, aucune préférence runtime staged n’est commit.
9. `beforeunload` bloque reload/fermeture navigateur quand `isDirty=true`.
10. Aucun overflow horizontal et aucune erreur runtime sur les 5 viewports AFTER.
11. Tests ciblés + build frontend verts.
12. Aucun changement Catalogue/Agenda/Sécurité/Équipe en dehors du shell commun ; aucun Vercel.

## Hors scope

- refonte visuelle des onglets déjà certifiés ;
- changement des endpoints backend ;
- migration DB ;
- modification du CRUD Catalogue, du modèle Agenda, de la sécurité ou du RBAC ;
- déploiement Vercel.

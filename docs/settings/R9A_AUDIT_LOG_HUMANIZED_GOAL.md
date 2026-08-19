# R9-A — Journal d'audit humanisé

Date : 2026-08-19
Scope : Réglages → Sécurité & Backup → Journal d'Audit.

## Goal
Conserver la traçabilité backend actuelle mais présenter chaque événement dans un langage immédiatement compréhensible par le praticien.

## Constat vérifié
La table affiche aujourd'hui les valeurs techniques brutes : `LOGIN_SUCCESS`, `ACCESS_DENIED`, `resource_type#resource_id`, `user #id`, sévérités `INFO/WARNING/CRITICAL`.
Le fail-closed et les filtres sont déjà corrects.

## Cible
- libellés français explicites pour les actions connues ;
- ressource lisible (`Patient #123`, `Sauvegarde`, `Accès mobile`, etc.) sans perdre l'identifiant brut ;
- sévérité traduite `Information / Attention / Critique` ;
- utilisateur affiché sans inventer de nom : `Utilisateur #id` tant qu'aucun nom n'est fourni par l'API ;
- détails complets accessibles, pas seulement un texte tronqué au survol ;
- codes bruts conservés comme information secondaire/technique si nécessaire.

## Wireframe

```text
19/08 08:32  Connexion réussie        Compte utilisateur   Information
              Utilisateur #12
              Voir les détails

19/08 08:28  Accès refusé             Patient #742         Attention
              Utilisateur #18
              Voir les détails
```

## Succès
1. BEFORE Security/Audit avec données réalistes sur 5 viewports ;
2. aucune perte de donnée d'audit ;
3. actions/sévérités connues traduites, fallback brut pour valeur inconnue ;
4. détails consultables explicitement ;
5. filtres backend existants conservés ;
6. AFTER mêmes viewports sans overflow ;
7. CI/RBAC/T2 proportionnés verts.

Hors scope : modification du moteur d'audit, restauration backup, appairage mobile, Vercel.

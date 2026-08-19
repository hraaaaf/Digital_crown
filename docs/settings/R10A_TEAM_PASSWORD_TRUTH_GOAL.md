# R10-A — Mon Équipe / vérité mot de passe

Date : 2026-08-19
Scope : Réglages → Mon Équipe → création d'un membre.

## Goal
Aligner exactement la validation frontend et son message avec le contrat backend autoritaire.

## Fait vérifié
`backend/schemas/auth.py` impose `PASSWORD_MIN_LENGTH = 8` et `PASSWORD_MAX_LENGTH = 128` à `TeamMemberCreate.password`.
Le frontend actuel possède :
- `minLength={4}` sur le champ ;
- le message `Le mot de passe doit contenir au moins 4 caractères.` pour l'erreur Pydantic.

## Cible
- champ HTML : min 8, max 128 ;
- aide visible : `8 à 128 caractères` ;
- message de validation backend : `Le mot de passe doit contenir entre 8 et 128 caractères.` ;
- aucune modification de hash, auth, quota, RBAC ou workflow d'approbation.

## Wireframe

```text
Mot de passe provisoire
[••••••••                         👁]
8 à 128 caractères
```

## Succès
1. BEFORE formulaire ouvert aux 5 viewports ;
2. aucune mention `4 caractères` dans TeamManager ;
3. `minLength=8`, `maxLength=128` ;
4. message cohérent avec backend ;
5. AFTER mêmes viewports, aucun overflow ;
6. tests/CI/RBAC proportionnés verts.

Hors scope : refonte Team, quotas/licence, suppression membre, Vercel.

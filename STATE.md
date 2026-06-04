# STATE — Digital Crown

> Fichier de reprise (handoff). **Lis-moi en premier** pour savoir où on en est.
> Le bloc AUTO ci-dessous est régénéré automatiquement à chaque fin de session par le hook : ne l'édite pas à la main.
> Les sections plus bas sont à toi (l'agent) : tiens-les à jour avant de t'arrêter.

<!-- STATE:AUTO:START -->
## Dernière session (auto — ne pas éditer à la main)
- **Mis à jour :** Initialisation
- **Branche :** `inconnue`
- **Worktree :** `inconnu`

### Fichiers touchés
- _(aucun fichier modifié détecté)_

### Dernières demandes
- _(rien à extraire)_
<!-- STATE:AUTO:END -->

## Historique de Session (Antigravity)
- **Fichiers modifiés** : 
  - `frontend/src/features/admin/SetupWizard/SetupWizard.tsx`
  - `frontend/src/features/admin/Settings/types.ts`
  - `frontend/src/features/admin/Settings/hooks/useSettingsStore.ts`
  - `frontend/src/features/admin/Settings/tabs/ProfileTab.tsx`
- **Dernière action** : Correction des failles de synchronisation (ajout du `cabinet_type` et réparation du bug destructeur de la Spécialité Personnalisée).

## Prochaine action
- Attendre ton feu vert pour tester l'interface ou explorer d'autres optimisations.

## Blocker / en attente
- Aucun.

## Décisions prises
- Refactorisation via un store Zustand dédié (`useSetupStore`) avec le middleware `persist` (sur le sessionStorage) pour garantir la reprise du wizard après un `F5` sans conserver les données à vie.

## Questions ouvertes
- Souhaites-tu que je règle immédiatement le problème de synchronisation (le bug de la Spécialité Personnalisée effacée dans les Réglages) ?

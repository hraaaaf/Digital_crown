# Patient P0-F — preuve RVG

Statut : **OPEN — certification exact-head requise**.

## Contrat verrouillé

- Upload RVG lié au patient autorisé.
- Liste RVG filtrée au patient et au tenant.
- Téléchargement via `Authorization: Bearer` uniquement ; aucun token en query string.
- Accès cross-tenant refusé pour liste, téléchargement, corbeille et restauration.
- Suppression clinique via corbeille, puis restauration possible.
- Test d’intégration isolé du média réel : `tmp_path` dédié et vérification de l’existence/contenu physique avant téléchargement.

## Preuve connue avant le HEAD courant

- T2 runtime précédent : GREEN.
- CI précédente : 1236 tests passés, 3 skipped, 1 seul échec dans le test RVG.
- Cause isolée : fixture SQLite isolée mais stockage média non isolé, rendant la preuve physique environnement-dépendante.
- Correctif de test : média temporaire dédié, sans modification du runtime produit.

## Fermeture

P0-F ne peut être CLOSED qu’après CI + T2 exact-head verts sur le commit contenant ce test isolé.

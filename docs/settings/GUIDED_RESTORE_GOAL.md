# Restauration guidée — Goal

Date : 2026-08-21
Repo : `hraaaaf/Digital_crown`
Statut : **PREPARED — NON CERTIFIÉ**
Base BEFORE immutable : `99c2aa32c6b145804467f7f38ea10722c2714e78`

## Goal

Permettre à un administrateur de restaurer un cabinet complet de façon sûre, explicable et réversible, sans jamais écraser l’état courant sans point de secours vérifié.

## Succès

1. L’opérateur sélectionne explicitement un package de restauration.
2. Un préflight vérifie l’intégrité du package, le moteur / format DB, la compatibilité applicative et la présence des médias.
3. Aucun apply n’est possible si le préflight échoue.
4. Un point de secours de l’état courant est créé et vérifié avant toute bascule destructive.
5. La confirmation forte exige la saisie exacte `RESTAURER`.
6. La restauration destructive n’écrase jamais une base ouverte par le processus applicatif : l’apply est exécuté hors-processus / au redémarrage.
7. DB et médias sont restaurés selon un manifeste explicite ; une restauration DB-only n’est jamais présentée comme restauration complète.
8. La candidate DB est restaurée en staging puis vérifiée avant publication atomique.
9. Après redémarrage, un smoke check valide l’ouverture DB et les invariants minimaux ; en cas d’échec, rollback vers le point de secours.
10. L’état de l’opération est persisté et auditable : préparée / appliquée / rollback / échec.
11. Les secrets, clés et chemins sensibles ne sont jamais exposés dans l’UI ou les logs utilisateur.
12. Aucun déploiement Vercel.

## Goal visuel

Dans `Réglages → Sécurité & Backup`, conserver la carte de sauvegarde existante et ajouter une surface distincte **Restaurer le cabinet** :

- statut rassurant mais factuel ;
- sélection du package ;
- checklist de préflight lisible ;
- avertissement explicite sur le redémarrage ;
- point de secours annoncé avant toute bascule ;
- bouton `Préparer la restauration` désactivé tant que le préflight n’est pas vert ;
- confirmation finale `RESTAURER` séparée de la préparation ;
- aucun bouton rouge « restauration instantanée » trompeur.

Référence : `docs/settings/GUIDED_RESTORE_MOCKUP.svg`.

## Viewports de preuve

- 1440 × 1200
- 768 × 1200
- 390 × 1200
- 360 × 1200
- 320 × 1200

Pour BEFORE et AFTER : 0 overflow horizontal, 0 page error, 0 HTTP 5xx, 0 request failed non attendu.

## Preuves requises avant CLOSED

- BEFORE exact de la base immutable ci-dessus ;
- tests backend de préflight, safety backup, staging, apply hors-processus, rollback et audit ;
- tests frontend du wizard et des garde-fous ;
- test d’intégration sur DB temporaire + médias temporaires, jamais sur données réelles ;
- preuve de rollback après smoke check volontairement cassé ;
- AFTER sur les 5 viewports ;
- comparaison BEFORE → mockup → AFTER + score visuel ;
- CI exact-HEAD verte ;
- closeout canonique puis merge/post-merge.

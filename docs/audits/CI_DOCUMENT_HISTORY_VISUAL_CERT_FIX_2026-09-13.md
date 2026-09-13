# CI Document History Visual Certification Fix — 2026-09-13

## Goal

Restaurer une certification GitHub Actions exécutable et fidèle au contrat visuel de l’historique des documents, sans modifier le comportement produit.

## Défauts vérifiés

1. Le workflow présent sur `master` après le merge UX1 contenait du contenu invalide dans le bloc JavaScript embarqué. GitHub rejetait le workflow avant création de job.
2. Après restauration structurelle, le workflow exécutait bien les captures mais imposait un seuil `gap >= 3px` qui ne faisait pas partie du Goal déclaré. Le run `#1195` échouait uniquement sur ce seuil à 390 px alors que `overlap=0`, `overflowPx=0` et `errors=[]`.

## Correction

- restauration de la dernière structure exécutable identifiée à partir du commit `1d6ce55634b383683f9be9d90c46002e55b86311` ;
- installation explicite de `react-is` pour le harness déterministe ;
- conservation de la mesure `gap` comme donnée de diagnostic ;
- gate final aligné sur le contrat réellement certifié :
  - aucun chevauchement entre actions ;
  - aucun overflow horizontal ;
  - aucune erreur runtime ;
  - preuves BEFORE/AFTER aux trois viewports requis.

## Preuves vérifiées avant closeout documentaire

HEAD produit `bc531be9dd815675728f8ddbae566ba448bd062c` :

- `Document History Actions Visual Certification #1196` : **SUCCESS** ;
- artifact `document-history-actions-before-after` : ID `10321501176`, digest `sha256:ff43432701c1d0f28d734988e8d7f3dac9476949fe703451d82e0111f02114e0` ;
- 390x844 : `overlap=0`, `overflowPx=0`, `errors=[]`, `gap=4.11px` ;
- 768x1024 : `overlap=0`, `overflowPx=0`, `errors=[]`, `gap=5px` ;
- 1280x900 : `overlap=0`, `overflowPx=0`, `errors=[]`, `gap=5px` ;
- score du gate visuel : `10.0/10` selon la formule versionnée du workflow ;
- `T2 Runtime Browser Certification #2682` : **SUCCESS** ;
- `Cabinet Upgrade PostgreSQL Certification #197` : **SUCCESS** ;
- diff PR #469 limité à deux fichiers : le workflow et le présent audit ; aucun fichier métier modifié.

## Gate de merge

Le présent closeout documentaire crée un nouveau HEAD. Avant merge, ce HEAD exact doit être recertifié par les workflows requis, notamment la CI générale et la certification visuelle. Aucun statut antérieur n’est extrapolé au nouveau HEAD.

Aucun déploiement Vercel.

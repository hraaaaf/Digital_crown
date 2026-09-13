# CI Document History Visual Certification Fix — 2026-09-13

## Goal

Restaurer un workflow GitHub Actions valide pour `.github/workflows/document-history-actions-visual-cert.yml` sans modifier le comportement produit.

## Défaut observé

Le workflow présent sur `master` après le merge UX1 contenait des octets / texte invalides dans le bloc JavaScript embarqué. GitHub rejetait le workflow avant création de job.

## Référence restaurée

Dernière version structurellement valide identifiée : commit `1d6ce55634b383683f9be9d90c46002e55b86311` (`Fix visual cert process isolation between before and after`).

Le fichier de la branche `fix/document-history-visual-cert-yaml` a été restauré byte-for-byte sur ce contenu valide.

## Succès attendu

- GitHub parse le workflow et crée le job `visual-cert` sur la PR de correction.
- Le job s’exécute jusqu’à la certification BEFORE/AFTER et produit l’artifact `document-history-actions-before-after`.
- Aucun fichier produit / métier n’est modifié par ce lot.

## Preuve attendue avant merge

- workflow PR terminal `SUCCESS` ;
- CI générale terminale sans nouvelle régression liée à cette correction ;
- diff PR limité au workflow restauré et au présent audit de closeout.

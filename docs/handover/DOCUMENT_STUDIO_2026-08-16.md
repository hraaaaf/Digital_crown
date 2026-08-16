# Document Studio — Handover — 2026-08-16

## Objectif
Continuer l’audit page-par-page du Document Studio selon `DOCUMENT_STUDIO_ROADMAP.md`.

## Terminé / convergé localement

### P3 — Devis
- CLOSED / PAUSED jusqu’à nouvel ordre par décision produit.
- PR #77 conservée open + draft.
- Preuves locales : backend 26/26 PASS, frontend `tsc --strict` PASS, tests P3 39/39 PASS, PDF ciblé PASS.
- Full-app/browser/cabinet PDF différés, non revendiqués.

### P4 — Note Honoraires
- Engineering local convergé P4-A→P4-F ; P4-G statiquement durci.
- PR #90 stackée sur P3, draft.
- P0/P1 initiaux corrigés :
  - contrat financier backend fail-closed ;
  - isolation des échéanciers hérités / global typé ;
  - séparation statut de paiement / mode d’encaissement ;
  - archive→reopen odontogramme ;
  - générateur PDF Honoraires multipage sûr ;
  - sémantique correcte de la modale de règlement ;
  - accessibilité statique des contrôles financiers.
- Preuves locales : backend 13/13 PASS, policy échéancier 4/4 PASS, archive hydration 1/1 PASS, PDF ciblé 36/36 lignes sur 6 pages, header 6/6, floor >=7 pt.
- Restant différé : full React/Vite, smoke authentifié, PDF cabinet/signature, browser 390/768/desktop, puis ready/merge/post-merge.

## En cours

### P5 — Suivi Paiement
PAGE ACTIVE.

Socle historique :
- ancien P4-A : allocation échéances exacte, PR #41, merge `989b819fe9f38ea616a48bf34e59263f7bcab82b` ;
- ancien P4-B : paiement d’échéance fail-closed, PR #42, merge `365a8cd9f1e9543898a70e060fd3e6890f647d66`.

## Prochaine action exacte
1. créer branche P5 depuis le head P4 courant ;
2. auditer le flux `InstallmentStudio` + backend installments/payments ;
3. vérifier chargement du plan, calcul total/avance/échéances, modification, payé/non payé, méthodes, résumé payé/reste/prochaine échéance, rappels et sauvegarde ;
4. classer P0/P1 ;
5. corriger fail-closed + tests ciblés Linux ;
6. mettre à jour audit/roadmap/STATE ;
7. conserver les gates full-app séparés si non exécutables.

## Règles critiques
- Backend = autorité financière ; frontend non fiable.
- Aucun montant/statut/mode de paiement ne doit être inféré silencieusement.
- Preview = read-only.
- Tests ciblés != certification production/financière.
- Aucun pourcentage : pondération de roadmap non définie.

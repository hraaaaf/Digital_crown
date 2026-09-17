# CÉPHALO-N — ACTIVE ROADMAP

Canonical entry: `docs/CEPHALO_N_CANONICAL.md`

Global scientific roadmap: `docs/SCIENTIFIC_CORE_REBUILD_ROADMAP.md`

## GOAL

Fermer Céphalo-N avec un pipeline scientifique déterministe, fail-closed, auditable et une UX R20 validée, sans inventer mesure, norme, diagnostic, indication ni traitement.

## SUCCESS

Le chantier n'est fermé que lorsque `CEPHALO_N_CLOSEOUT_VERIFIED` est prouvé sur l'état intégré final :

- produit/UI R20 mergé et preuve visuelle conservée ;
- architecture scientifique inchangée dans ses invariants ;
- full backend regression verte sur SHA exact ;
- certification PostgreSQL verte ;
- documentation canonique cohérente avec les merges/runs réels ;
- aucun retour de routes/contrats legacy supprimés ;
- aucun déploiement Vercel sans autorisation explicite.

## CURRENT STATE — 2026-09-17

- R20 product/UI: merged and visually validated.
- Original R20 merge: `7821819b237aebdc7e3de1d2646510434251d2eb`.
- CI orchestration fix: PR `#554`, merged.
- Stale regression cleanups: `#558`, `#562`, `#564`, `#566`, all merged.
- PR `#566` merge SHA: `24844a5d19a6bd575d175b331a1bba68bc3c0b0f`.
- PostgreSQL certification on `24844a5d...`: run `35203491675` SUCCESS.
- Full CI manual proof on `24844a5d...`: run `35204697524` IN_PROGRESS at last verification.
- Current master observed during documentation lot: `ec6bf4f40137f6e7d395effd97e0be3b0f6a2362`.
- `CEPHALO_N_CLOSEOUT_VERIFIED`: NOT YET DECLARED.

## NEXT EXACT

Inspect run `35204697524` once.

If green: verify backend/full-regression job + exact SHA, reconcile docs against current `master`, update canonical closeout, then merge this documentation lot and perform post-merge verification.

If failed: diagnose only the exact proven failure, correct it without restoring deprecated behavior, re-run exact-head proof, merge safely, then repeat final post-merge certification.

If still in progress: continue independent documentation reconciliation; no passive polling.

## REMAINING SEQUENCE

`full backend proof -> canonical closeout -> roadmap coherence -> docs merge -> post-merge verification -> CEPHALO_N_CLOSEOUT_VERIFIED -> next Ortho/Céphalo lot`

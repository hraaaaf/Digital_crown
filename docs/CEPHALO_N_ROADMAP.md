# CÉPHALO-N — ACTIVE ROADMAP

Canonical entry: `docs/CEPHALO_N_CANONICAL.md`

Global scientific roadmap: `docs/SCIENTIFIC_CORE_REBUILD_ROADMAP.md`

## GOAL

Fermer Céphalo-N avec un pipeline scientifique déterministe, fail-closed, auditable et une UX R20 validée, sans inventer mesure, norme, diagnostic, indication ni traitement.

## SUCCESS

Le chantier est fermé lorsque `CEPHALO_N_CLOSEOUT_VERIFIED` est prouvé sur l'état intégré final :

- produit/UI R20 mergé et preuve visuelle conservée ;
- architecture scientifique inchangée dans ses invariants ;
- full backend regression verte sur SHA exact ;
- certification PostgreSQL verte ;
- documentation canonique cohérente avec les merges/runs réels ;
- aucun retour de routes/contrats legacy supprimés ;
- aucun déploiement Vercel sans autorisation explicite.

## FINAL STATE — 2026-09-17

- R20 product/UI: merged and visually validated.
- Original R20 merge: `7821819b237aebdc7e3de1d2646510434251d2eb`.
- CI orchestration fix: PR `#554`, merged.
- Stale regression cleanups: `#558`, `#562`, `#564`, `#566`, all merged.
- PR `#566` merge SHA: `24844a5d19a6bd575d175b331a1bba68bc3c0b0f`.
- PostgreSQL certification on `24844a5d...`: run `35203491675` SUCCESS.
- Manual CI proof on `24844a5d...`: run `35204697524` SUCCESS.
- Full backend regression job `105147523280`: SUCCESS.
- Frontend tests/build job `105147523277`: SUCCESS.
- Production negative guard job `105147523081`: SUCCESS.
- Current master at reconciliation: `ec6bf4f40137f6e7d395effd97e0be3b0f6a2362`.
- Delta from `24844a5d...` to current master contains only Agenda closeout documentation.
- `CEPHALO_N_CLOSEOUT_VERIFIED`: DECLARED.

## NEXT EXACT

Merge the documentation-only canonicalization PR after diff/CI coherence, then verify `docs/CEPHALO_N_CANONICAL.md`, `docs/CEPHALO_N_ROADMAP.md`, `docs/audits/CEPHALO_N_R20_CLOSEOUT_HANDOVER.md` and the scientific roadmap once on post-merge `master`.

Then start the next Ortho/Céphalo lot from this baseline. Do not reopen R20 without new evidence.

## REMAINING SEQUENCE

`docs PR -> docs CI/diff coherence -> merge -> post-merge canonical verification -> next Ortho/Céphalo lot`

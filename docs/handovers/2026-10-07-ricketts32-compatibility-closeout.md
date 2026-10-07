# Handover — PR #775 — Ricketts 32F compatibility closeout — 2026-10-07

## Goal

Close the engineering/documentation phase of the Facad Ricketts 32F compatibility-disposition work without overstating runtime or scientific parity.

## Repository state

- Repository: `hraaaaf/Digital_crown`
- PR: `#775`
- Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`
- Evidence HEAD before this documentation closeout: `575fc9e2ad21133763bdacbe512e7591a39b9f59`
- PR state after human-authorized merge: CLOSED / MERGED
- Merge commit: `c7209e9d35f0a85a12ee1725589bca2863aa6607`
- Vercel: not authorized, not used

## Verified result on evidence HEAD

Facad `Ricketts (32 F)` compatibility backlog:
- originally unmapped: 26
- explicitly dispositioned: 26/26
- remaining unmapped: 0

This is a compatibility-disposition result only. It does **not** mean:
- 26 direct runtime aliases;
- Facad norms are authoritative;
- same-trace numeric parity is proven;
- signed/oriented presentation parity is proven where explicitly gated;
- vendor landmarks/planes may replace source-locked Digital Crown identities.

## Source evidence

Official Facad release:
- version: 3.14.1.1111
- profile: `Ricketts (32 F).cph`
- SHA-256: `d0b442b39ac7db3dc9c46d807cb3c20bd937c69783b096b484872017f9376518`

Direct vendor definitions were used to disposition the four compatibility clusters:
1. dental / occlusion;
2. vertical / Frankfort;
3. PTV / cranial;
4. final seven gaps.

## Fail-closed boundaries retained

Examples of deliberately non-aliased vendor variants:
- Facad OL incisor-midpoint line != source-locked Ricketts functional occlusal plane;
- Facad Pt != `PR_Ricketts_PTV` without identity proof;
- Facad `Ms-d` != Ricketts A6 / `U6_DISTAL_Ricketts` by label alone;
- Facad STs/STi != Atlas/DC labial commissure;
- Facad generic Go-Me != source-locked Ricketts mandibular plane;
- Facad DC “Centre of condyle” != `DC_Ricketts` without condylar-neck identity proof;
- Facad `PM'` intersection != manual `Pm_Ricketts`.

## Final evidence

Targeted final workflow:
- `Facad Ricketts 32F final seven contract #2`
- result: SUCCESS
- exact evidence HEAD: `575fc9e2ad21133763bdacbe512e7591a39b9f59`

Adversarial review A — science/provenance:
- explicit prompt executed from zero on the same HEAD;
- 15/15 critical checks PASS;
- 0 BLOCKER;
- 0 MAJOR.

Adversarial review B — CI/reproducibility:
- explicit prompt executed from zero on the same HEAD;
- 14/14 critical checks PASS;
- 0 BLOCKER;
- 0 MAJOR.

Additional confirmation pass:
- 10/10 PASS.

Perfection Pass:
- 16/16 PASS.

Scores:
- EXECUTION_SCORE: 9.4/10
- ADVERSARIAL_SCORE: 9.4/10
- RETAINED_SCORE: 9.4/10
- same-agent review ceiling respected.

## Canonical files

- `STATE.md`
- `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`
- `AGENTS.md`
- `docs/audits/schemas/ortho_lot08_facad_dc_unmapped_backlog_v1.json`
- `docs/audits/schemas/ortho_lot08_ricketts32_facad_dental_cluster_resolution_v1.json`
- `docs/audits/schemas/ortho_lot08_ricketts32_facad_vertical_fh_cluster_resolution_v1.json`
- `docs/audits/schemas/ortho_lot08_ricketts32_facad_ptv_cranial_cluster_resolution_v1.json`
- `docs/audits/schemas/ortho_lot08_ricketts32_facad_final_seven_cluster_resolution_v1.json`

## Closeout boundary

Engineering/scientific compatibility disposition is verified on the evidence HEAD.

PR #775 is **merged and closed on GitHub**. The remaining closeout work is documentation-only reconciliation of canonical repo state after the merge. Product/scientific evidence from the exact candidate remains acquired because the merge preserved the critical blobs byte-identically.

## Next exact

1. merge this docs-only post-merge reconciliation follow-up after exact-head documentary checks are green;
2. perform a final read-only coherence check on master;
3. mark the LOT08 Ricketts 32F compatibility closeout fully closed in canonical state;
4. move to the next canonical lot.

No Vercel deployment is required or authorized by this handover.

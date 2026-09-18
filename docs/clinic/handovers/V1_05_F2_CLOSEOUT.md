# V1-05 Ortho Journey — F2 Closeout

Status: **POST-MERGE CERTIFIED**

## Trailer

F2 adds longitudinal orthodontic timepoints T0..T999 and links existing canonical evidence to them by reference only.

Examples:
- ClinicalAsset / Media Core photo
- CephaloAnalysis
- PanoramicAnalysis

F2 never copies media or scientific payloads and never infers clinical progress, success, diagnosis or severity.

## Product baseline

Parent certified F1B merge:
`81535364e4f98f3f9b53fac179f2fbfd2ec261f5`

Product PR:
#610

Product HEAD:
`a0c0a5b73369be57b9eeaebe884fdd0f96c8b559`

## Implemented

- OrthoTimepoint T0..T999
- unique (ortho_case_id, ordinal)
- OrthoTimepointEvidence
- exactly one canonical evidence source per evidence link
- ClinicalAsset / CephaloAnalysis / PanoramicAnalysis reference-only linking
- same-patient / same-tenant validation
- reject Media Core timepoint conflicts
- reject reuse of one canonical evidence across multiple timepoints
- factual Patient Journey event
- additive Alembic revision `ojf20000008`
- runtime schema head `ojf20000008`
- P7 explicit Ortho Journey test coverage

## Exact-head evidence already green

- CI `35393919867` — SUCCESS
- PostgreSQL Alembic `35393919803` — SUCCESS
- Patient P7 `35393919903` — SUCCESS
- T2 Runtime Browser `35393919768` — SUCCESS
- Agenda A5 `35393919872` — SUCCESS

## Full backend certification

Temporary PR:
#611 — MUST NOT MERGE

Certification HEAD:
`ce43c48116f1ab2722d7ee924284bc77bd64dabf`

Delta versus product HEAD:
- +1 commit
- only `.github/workflows/ci.yml`

Certification CI:
`35395350149`

Full backend job:
`105762817579` — IN PROGRESS at closeout preparation time.

## Merge gate

Do not merge #610 until the Full backend job above is SUCCESS and #611 is closed without merge.

## Next

After F2 merge + post-merge proof:

F3 — longitudinal comparison: compare two selected timepoints (for example T0 vs T1) using canonical evidence and certified measurements, without automatic claims of improvement or treatment success.


## Post-merge certification

Merged product commit:
`35ccdf5ad73b403279e129c7affe2d9364c6d4cc`

Temporary certification:
- PR #612 — closed without merge
- certification HEAD `141ddb47c7a9ccee4c679d24b84a744a0707386f`
- exact merged baseline + one CI-only workflow commit

Post-merge gates:
- CI `35396881335` — SUCCESS
- Full Backend job `105767649621` — SUCCESS
- T2 Runtime Browser `35396881376` — SUCCESS
- Agenda A5 `35396881338` — SUCCESS
- Frontend / production guard / M4-A / M4-B / M4-C — SUCCESS

F2 is closed. F3 is authorized on the merged baseline.

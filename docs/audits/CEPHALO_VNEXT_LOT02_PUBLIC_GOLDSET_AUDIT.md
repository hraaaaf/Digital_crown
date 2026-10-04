# Cephalo vNext — LOT02 Public Gold-Set Audit

Status: EVIDENCE AUDIT — public datasets; no detector selection
Date: 2026-10-02

## Goal
Determine whether public expert-annotated lateral-cephalometric datasets can satisfy the external/qualified landmark-reference portion of LOT02 without inventing anatomical equivalence.

## Sources inspected
- Aariz official GitHub repository, commit 0634b8b4e6783b13fb6383fac694d61123904d3c.
- Aariz public Figshare dataset: 1000 LCRs, 29 landmarks, 7 devices, CC BY 4.0.
- Aariz Scientific Data description: expert annotation team and 700/150/150 train/validation/test partition.
- ISBI 2015 dataset descriptions in peer-reviewed literature: 400 LCRs, 19 landmarks, two expert annotations, 150/150/100 train/Test1/Test2, 0.1 mm/pixel.
- Digital Crown SRPose38 operational mapping at current repository HEAD.

## Aariz annotation evidence
Official loader reads separate Senior Orthodontists and Junior Orthodontists annotation JSON files. The published dataset describes 2 expert orthodontists plus 4 additional orthodontic professionals, with expert oversight.

Important: the official sample loader averages junior and senior coordinates. Digital Crown validation MUST ingest the two annotation sets separately first; disagreement must be measured before any adjudicated/averaged reference is produced.

## Mapping to Digital Crown 38

### Direct anatomy-compatible candidates (24/38)
A, ANS, B, Me, N, Or, Pog, PNS, Prn/Pn, S, Ar, Co, Gn, Go, Po,
L1_incisal/LIT, U1_apex/UIA, U1_incisal/UIT, L1_apex/LIA,
Li_soft/Li, Ls_soft/Ls, N_soft/N`, Pog_soft/Pog`, Sn_soft/Sn.

These are candidates for validation, not automatic clinical promotion. Gn/Go/Po retain their LOT03 versioned-definition cautions.

### Semantic HOLD
Aariz UMT and LMT are molar cusp-tip definitions. Digital Crown U6/L6 are generic legacy molar identities. They MUST NOT be treated as equivalent without an explicit versioned analysis-specific mapping.
Aariz UPM/LPM/R have no current SRPose38 counterpart.

### Absent from Aariz for SRPose38-only identities
D_point, Cm, Ptm, Ba, PT_point, Bo, Ls2, Li2, Gn_soft, Me_soft, G_soft, C_point.
Occ_Ant/Occ_Post are construction anchors outside SRPose38 and are not detector outputs.

## ISBI 2015 role
ISBI provides 19 landmarks and two expert coordinate sets on 400 lateral cephalograms. Literature reports 150 training, 150 Test1 and 100 Test2 cases. Because SRPose38/CL-Detection training provenance must be checked before reuse, ISBI MUST NOT be considered untouched acceptance evidence until contamination is excluded. It remains useful for annotator-variability and reproducibility benchmarking.

## Aariz role
Aariz is the stronger external candidate because it covers 24 anatomy-compatible Digital Crown identities, adds soft-tissue/dental coverage, spans seven imaging devices, has explicit train/validation/test partitions, and exposes junior/senior annotation paths. Its official license is CC BY 4.0.

For detector acceptance, use only a frozen untouched Aariz subset that has not been used to train, tune, choose preprocessing, thresholds, aliases or model checkpoints. If prior exposure cannot be excluded, that subset becomes development/reference evidence rather than final acceptance evidence.

## Gate impact
Public evidence materially reduces the LOT02 blocker but does not by itself satisfy CEPH_GOLDSET_READY:
1. freeze actual image + annotation files and immutable hashes;
2. ingest junior/senior coordinates separately;
3. calculate inter-annotator error per landmark and X/Y;
4. define adjudication/reference rule before detector scoring;
5. prove SRPose38 training/tuning contamination status for candidate acceptance subset;
6. freeze G3 Digital Crown legacy fixtures separately.

No missing SRPose38-only landmark may be inferred from Aariz. Unsupported identities remain NOT_VALIDATED/BLOCKED.

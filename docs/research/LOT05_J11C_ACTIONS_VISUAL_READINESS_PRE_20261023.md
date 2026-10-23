# LOT05/J11C — Actions as the visual review readiness worker (PRE, 2026-10-23)

Mission: use GitHub Actions to advance machine-verifiable readiness of the existing **28 flagged panoramic images** and **6 perceptually similar cross-split pairs**, while keeping the human clinical review open. Avoid repeating model training or previous audits; reuse J10X/J11A/J11B selection logic. Source: academic AKUDENTAL revision 92e2cc3ae5eebc9de509311a3edefb7106fca7dd, declared CC BY-NC-SA 4.0, no commercial license established.

New evidence: 28 original academic JPEGs can actually be decoded; repeated FDI bounding-box regions have nonempty pixel extent; report the count of small source regions (short side <=32px) and nonstandard EXIF orientation; the 6 pre-existing candidate pairs have two readable source JPEGs each, and compare aggregate source dimensions/orientation and mirror preference. Unexpected coverage, changed candidate counts or corrupt images fail closed.

Workflow: .github/workflows/lot05-j11c-academic-visual-readiness.yml
Code: experiments/lot05_j11c_academic_visual_readiness.py
Synthetic tests: experiments/test_lot05_j11c_academic_visual_readiness.py

All 333 source JPEGs and labels are checked out only on an ephemeral GitHub runner and removed in a final always() step. No Actions artifacts, gallery, patient IDs, image filenames, coordinates, individual fingerprints, checkpoints or images are exported. Results are strictly aggregate and not evidence of same-patient identity or of annotation error. Github Actions success can mean only automatic readability; **expert visual decisions remain 0/28 and 0/6** until a human completes private review. External patient-independent test, commercial rights and clinical validity remain BLOCKED. PR remains DRAFT; no merge, Vercel or Production.

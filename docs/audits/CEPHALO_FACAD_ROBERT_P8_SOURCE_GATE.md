# FACAD P8 source gate

The unannotated native cephalogram for the same trace has not yet been retrieved. The four available images are application screenshots. Do not use a screenshot or another example case as clinical ground truth.

A source may enter independent review only after byte-integrity verification, source rights confirmation, matching 13F and 32F export provenance, and independent human image review. Manual FACAD Pog cannot be promoted to canonical Pog_hard. Parity stays 0/45; CLINICAL_NO_GO remains true. This document neither changes clinical flags nor includes private patient files.

## P8 hardening — exact-source gate

The initial P8 synthetic GREEN only checked SHA-256 strings, a PNG header and
reported dimensions. That left a false-positive class: an incomplete file with
a forged header or a non-evidence bundle could pass if both hashes were
self-consistent.

The hardened read-only checker now requires:

- Complete PNG framing, per-chunk CRC, IDAT zlib pixel decoding, bounded
  dimensions, complete scanlines and IEND with no trailing data. Only
  non-interlaced 8-bit/16-bit grayscale, grayscale-alpha, RGB or RGBA PNGs
  are accepted. This is a **format integrity** check, not a medical image
  validation.
- An evidence manifest with the precise FACAD direct-evidence schema,
  `DIRECT_EVIDENCE_PARTIAL` status, `scientific_authority=false`, no parity
  rows, 32F and 13F profiles, six unique evidence records as full
  three-export triplets, source version 3.14.1.1111, and a single trace
  identity across all six records.
- SHA-256 agreement of both supplied files to the strict attestations and
  explicit declarations of native source, no overlay, same case, same trace
  and rights. Any mismatch fails closed.

**Still not proved:** The operator flags can be mistaken, a valid PNG can
contain an application screenshot, and consistent manifest entries do not
authenticate the six private export bytes. Clinical identity validation
remains unavailable without the original unannotated radiograph, independent
qualified reviewer and authorized Digital Crown bridge.

Public GitHub Actions execute only generated zero-pixel PNGs and synthetic
FACAD manifests. Do not upload real images or vendor exports to the repo,
Actions artifacts or public logs. Keep the PR draft and the clinical lock:
`0/45`, `CLINICAL_NO_GO=true`.

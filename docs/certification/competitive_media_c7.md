# Competitive / Media C7 — certification thresholds

Status: thresholds frozen before execution of the C7 volumetric benchmark.
Base: `master@5e1802901301a36fa4acf3d34adbfbde84258c18`.
Scope: Media Core + patient Media Hub only. Cephalometry excluded. No deployment.

## Goal

Certify that Media Core / Media Hub remain tenant-safe, correct and usable under a realistic high-volume patient-media corpus.

## Fixed thresholds

- Volume corpus: **5,000 primary assets** for tenant A / one patient.
- Cross-tenant noise: **500 assets** for tenant B using the same patient id at service-layer isolation level.
- API page size: **200 maximum**; response cardinality must remain bounded to requested page size.
- Pagination: newest-first deterministic order `(captured_at DESC, id DESC)`; adjacent pages must have **0 duplicate** and **0 gap** against the full ordered corpus.
- Deep-page check: offset **4,800** must remain correct.
- Search: a unique marker placed beyond the first 200 unfiltered assets must be found by server-side search.
- Filters: `asset_type`, `source_kind`, and `timepoint` must be applied server-side and preserve tenant scope.
- Cross-tenant: tenant B assets must never appear in tenant A list/search/filter results; direct foreign-tenant content access must remain **404**.
- Query scaling: page/list query count must be **constant with page cardinality**; thumbnail metadata must remain batch-loaded, never one query per asset.
- Timing ceiling: each measured list/search/deep-page operation over the 5,000-row tenant-A corpus must complete in **< 2.0 s** in the CI test environment. This is a regression ceiling, not a production SLA.
- UI responsive certification if UI changes: **390×844**, **768×1024**, **1280×900**.

## Pass rule

C7 is not CLOSED unless all automated assertions, exact-head CI, PR audit, merge, post-merge checks, and canonical closeout are green. A failing threshold is a product defect, not a documentation exception.

# Clinical diagnosis review

## Verdict

V2 correctly separates clinical information states. The existing application still requires a domain audit before automatic diagnostic logic can be trusted.

Required chain: symptom -> sign -> test-result -> imaging-observation -> finding -> hypothesis -> differential -> provisional diagnosis -> confirmed diagnosis.

Every transition requires evidence, author, time, tooth/region, terminology version and certainty. Clinician identity is required for confirmation.

| Area | Status | Reason |
|---|---|---|
| Endodontic terminology | NEEDS_SOURCE_VERIFICATION | AAE/ESE terminology is being updated; 2009 and 2026 material must not be mixed |
| Periodontal classification | READY_FOR_MAPPING_REVIEW | 2017 World Workshop/EFP framework identifiable |
| Trauma | NEEDS_SOURCE_VERIFICATION | IADT version/license must be recorded |
| ICD-11 oral/dental | NEEDS_SOURCE_VERIFICATION | Coding scope differs from detailed terminology |
| SNOMED CT dentistry | LICENSE_UNCERTAIN | Edition, extension and license need review |
| Tooth numbering | READY_FOR_MAPPING_REVIEW | ISO 3950:2016 current but licensed and planned for revision |
| Automatic confirmed diagnosis | BLOCKING_GAP | Forbidden in V2 |
| Odontogram consistency | NEEDS_DOMAIN_AUDIT | Requires absent tooth, dentition and FDI parity tests |

AAE materials explicitly recognize inconclusive or conflicting examinations. Correct behavior is uncertainty, reassessment or referral, never forced classification.


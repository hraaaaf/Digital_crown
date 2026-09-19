# V1-05 / F5 — Scite External Evidence Audit

**Date:** 2026-09-19  
**Scope:** post-merge external literature/citation-context audit of F5 scientific claims.  
**Status:** COMPLETED AS EVIDENCE AUDIT — NOT CLINICAL APPROVAL — NOT A SUBSTITUTE FOR A NAMED INDEPENDENT SCIENTIFIC REVIEWER.

## Question

Does external literature and citation context support keeping Digital Crown F5 as an adult-only, deterministic anterior-cranial-base structural feature-registration **engineering preview**, while withholding clinical-validity claims and cross-machine assumptions?

## Sources screened

Primary F5 set:
- Graf et al. 2022 — DOI `10.1093/ejo/cjab082`
- Jiang et al. 2020 — DOI `10.1186/s12880-020-00432-z`
- Zhao et al. 2025 — DOI `10.1007/s10278-025-01447-0`

Additional independent evidence discovered via Scite:
- Kim et al. 2022 — DOI `10.2319/010121-1.1`
- Danz et al. 2024 — DOI `10.3389/froh.2024.1419481`
- Vasileiou et al. 2026 — DOI `10.1093/ejo/cjag008`

No editorial notice was surfaced by Scite for the records retrieved in this audit. This is not equivalent to a guarantee that no notice exists.

## Findings

### 1. Structural anterior-cranial-base anchoring remains scientifically defensible

Jiang 2020 explicitly frames stable-region structural superimposition as the most accurate established strategy in its rationale and evaluates feature matching against traditional structural superimposition.

Kim 2022 states that Björk's structural method is conventionally recognized as the gold-standard reference for growing patients and uses it as the comparator for automated alternatives.

**Implication for F5:** rejecting S-N-only alignment as the final scientific method remains justified.

### 2. Jiang 2020 supports feature matching, but does not validate our adult scope by itself

Scite full-text excerpts verify:
- 28 paired cephalograms;
- all pairs acquired on the same X-ray machine;
- T1 ages 12-27 years and T2 ages 14-29 years;
- feature matching was applied to stable structural regions;
- the paper concludes automated results were comparable to traditional hand structural superimposition.

**Implication:** Jiang supports the feature-matching method family, but not an adult-only population claim and not cross-machine equivalence.

### 3. Growing-patient automation remains a separate validation problem

Kim 2022 explicitly notes that the earlier automatic method had been tested on adults and that applicability to growing patients had not been determined before their study.

**Implication:** F5's current fail-closed behavior for growing patients is conservative and remains appropriate until a dedicated growth-population validation record exists.

### 4. Structural ROI choice is not interchangeable

Danz 2024 prospectively compared three digital image-correlation structural regions in 30 consecutive patients. Its abstract reports:
- WPLC had the best precision for image rotation and cephalometric landmarks;
- systematic bias existed between WPLC and whole-cranial-base methods for image rotation and most landmarks.

**Implication:** a generic "anterior cranial base" label is not enough for clinical validation. Digital Crown must validate the exact operator-confirmed ROI contract it implements.

### 5. A newer 2026 validation study must be incorporated before clinical activation

Scite identified Vasileiou et al. 2026, directly evaluating validity of digital manual and automated 2D structural superimposition on the anterior cranial base using Björk's method.

The full text was not readable through Scite in this session, so no implementation claim is derived from it beyond its verified bibliographic identity/objective.

**Implication:** this paper becomes a mandatory full-text review item before any future clinical-activation decision.

### 6. Citation-context review found no strong published contradiction to the F5 engineering direction

Scite's incoming citation graph returned:
- Graf 2022: 30 resolved incoming citation edges;
- Jiang 2020: 8;
- Zhao 2025: 4.

The retrieved Smart Citation contexts were predominantly classified as **mentioning**; no supporting/contrasting Smart Citation classification directly overturning the F5 engineering direction was surfaced.

**Limitation:** Zhao 2025 and Vasileiou 2026 had low citation-graph coverage. Absence of a contrasting citation is therefore not evidence that no contradiction exists.

### 7. Zhao 2025 remains useful but not sufficient as an implementation specification

Scite verifies the article identity and current sparse citation context. In this session it did not return readable full-text passages for the detailed SIFT/KNN implementation.

Digital Crown must therefore continue to treat Zhao as support for the method family, not as a byte-for-byte algorithm specification. The existing SIFT/Hamming contradiction record remains unresolved rather than silently normalized.

## Decision

**External evidence verdict: CONDITIONAL SUPPORT FOR ENGINEERING PREVIEW.**

Keep:
- `ENGINE_ESTIMATE_ONLY`;
- `clinically_validated=false`;
- adult-only initial validation scope;
- clinician-confirmed stable ROI;
- deterministic similarity-transform boundary;
- acquisition-protocol status `UNVERIFIED`;
- growing-patient fail-closed behavior;
- no automatic clinical interpretation.

Do not claim:
- universal accuracy;
- cross-machine/cross-protocol equivalence;
- validated clinical displacement measurement from unverified acquisitions;
- equivalence of all anterior-cranial-base ROI definitions;
- named clinical approval.

## Required actions before clinical activation

1. Obtain/read the full text of Vasileiou 2026 and reconcile it with F5-MDR-001.
2. Validate the exact Digital Crown ROI + SIFT/L2 + ratio + similarity-transform pipeline against an expert structural-superimposition reference set.
3. Store or otherwise verify acquisition-device/protocol/resolution provenance, or perform dedicated cross-protocol validation.
4. Run a growing-patient validation program before lifting the age gate.
5. Obtain a named independent scientific reviewer and named human clinical reviewer.

## Audit conclusion

The Scite audit **does not reveal evidence requiring rollback of the merged engineering-preview implementation**.

It does strengthen the rationale for keeping F5 hidden/OFF by default and for retaining the current scientific warnings. Clinical activation remains blocked.

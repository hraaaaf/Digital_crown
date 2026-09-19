# V1-05 / F5 — Scientific Superimposition Literature Review

**Date:** 2026-09-19  
**Scope:** 2D longitudinal lateral-cephalogram superimposition only.  
**Status:** scientific gate document; not clinical validation.

## Goal
Select an implementation direction for Digital Crown F5 that is traceable to published methods, deterministic, non-interpretative, and explicit about uncertainty.

## Sources reviewed

### American Board of Orthodontics — structural method
Registry: `abo-superimpositions-structural-method`
The ABO requires cranial-base, maxillary and mandibular superimpositions and states that they are performed with the structural method using stable structures derived from Melsen, Björk/Skieller and Enlow.

Source: https://exam.americanboardortho.com/orthodontists/become-certified/clinical-exam/mail-in-cre-submission-procedure/case-record-preparation/superimpositions/

The ABO cephalometric-tracing guidance also states that craniofacial tracings are superimposed on the anterior cranial base and that cephalograms should carry a calibration ruler.

Source: https://abo-www.americanboardortho.com/orthodontists/become-certified/clinical-exam/mail-in-cre-submission-procedure/case-record-preparation/cephalometric-tracings/

### Graf et al. 2022 — systematic review
Registry: `graf-cephalo-superimposition-review-2022`
Graf C, Dritsas K, Ghamri M, Gkantidis N. *Reliability of cephalometric superimposition for the assessment of craniofacial changes: a systematic review.* Eur J Orthod. 2022;44(5):477-490. DOI: 10.1093/ejo/cjab082.

Source: https://academic.oup.com/ejo/article/44/5/477/6530110

Key constraint for F5: the review found high heterogeneity and substantial methodological limitations across the literature and concluded that no cephalometric superimposition method has been proved to deliver accurate results. Therefore Digital Crown must not label an automated overlay as clinically exact or as ground truth.

### Jiang et al. 2020 — feature matching
Registry: `jiang-feature-matching-superimposition-2020`
Jiang Y et al. *The application and accuracy of feature matching on automated cephalometric superimposition.* BMC Med Imaging. 2020;20:31. DOI: 10.1186/s12880-020-00432-z.

Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC7083061/

The study compared automated feature matching with traditional structural hand superimposition on 28 longitudinal pairs. The images were acquired under a controlled protocol, so the result does not establish cross-machine or cross-protocol robustness. It supports feature matching as a plausible deterministic registration approach, but the sample is limited and does not establish universal individual-case validity.

### Zhao et al. 2025 — automated stable-region feature matching
Registry: `zhao-feature-matching-superimposition-2025`
Zhao L et al. *Evaluation of an Automatic Cephalometric Superimposition Method Based on Feature Matching.* J Digit Imaging. 2025;38(6):4138-4147. DOI: 10.1007/s10278-025-01447-0.

Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC12701167/

The method detects a stable cranial region, uses SIFT keypoints, KNN matching with a nearest/second-nearest ratio threshold below 0.7, then estimates a finite four-degree-of-freedom similarity transformation. The validation sample was restricted to adults (18–40 years) and images acquired under the study's defined radiographic conditions, so transfer to growing patients or materially different acquisition protocols is not assumed.

**Implementation caveat:** the article describes Hamming distance while also describing SIFT descriptors. OpenCV documentation recommends L1/L2 for SIFT/SURF descriptors and Hamming for binary descriptors such as ORB/BRISK/BRIEF. Digital Crown therefore uses L2 with SIFT and does not claim literal reproduction of the article's matcher implementation.

OpenCV registry: `opencv-bfmatcher-4-13`

OpenCV reference: https://docs.opencv.org/4.13.0/javadoc/org/opencv/features2d/BFMatcher.html

### Structural-region anatomy
The literature on Björk-style anterior-cranial-base superimposition uses stable structures rather than only the S-N line. Commonly cited structures include the anterior part/wall of sella, cribriform plate and ethmoidal structures. This is the essential reason a simple S-N landmark registration is not an acceptable substitute for structural superimposition.

Supporting review:
https://pmc.ncbi.nlm.nih.gov/articles/PMC8156959/
https://pmc.ncbi.nlm.nih.gov/articles/PMC8088383/

## Evidence synthesis

1. **S-N only is rejected for F5 scientific registration.** S and N landmarks are useful cephalometric points but a line through them is not equivalent to a structural best-fit on stable anterior-cranial-base anatomy.
2. **Structural ACB registration is the scientific reference direction.**
3. **Feature matching is an evidence-supported automation candidate**, not a proven clinical truth.
4. **The transformation must not geometrically deform anatomy.** A 2D similarity transform (rotation + uniform scale + X/Y translation) is preferred over unrestricted affine/projective transforms.
5. **Growing patients require separate validation.** Growth changes and reference-area behavior make direct transfer of adult automated validation unsafe.
6. **Individual-case validation matters.** Mean group agreement is insufficient; Digital Crown validation must evaluate per-case error and use methods such as Bland-Altman analysis when comparing against expert reference registration.

## Decision boundary
This review supports proceeding to a Method Decision Record. It does **not** certify an algorithm, a threshold, a patient population beyond the explicitly defined scope, or any clinical interpretation.

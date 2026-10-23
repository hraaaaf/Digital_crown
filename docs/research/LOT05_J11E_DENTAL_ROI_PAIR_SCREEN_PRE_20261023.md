# LOT05/J11E — PRE: independent ROI resemblance screen of six dHash pairs

**2026-10-23, academic research only.** The J11A/J11B pipeline identified six nonidentical JPEG cross-split candidates by coarse dHash. J11E computes a second, independent normalized central-dental-region grayscale mean absolute distance. All image bytes/IDs/hashes remain within a disposable GitHub Actions runner and are removed at the end. No artifacts. The source is pinned to melihoz/AKUDENTAL@92e2cc3ae5eebc9de509311a3edefb7106fca7dd.

ROI is fixed, unregistered, autocontrasted crop (16–84% width, 22–82% height), resized to 224x128. Compare normal and mirror. Report aggregate median/min/max and bins only (not individual pairs). This is not a calibrated same-patient threshold: ROI is not anatomically aligned, and structurally similar panoramics can have similar pixel statistics. Image differences or mirrored resemblance are not proof of different/same patients, examinations or patient grouping.

The user has confirmed two FDI label adjudications (human 2/28), but **zero** cross-split same-patient pair decisions (0/6). Never auto-clear patient independence, never modify original labels, never approve clinical/commercial deployment. PR #1032 DRAFT: no merge, no Vercel/Production.

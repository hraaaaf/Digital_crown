# FACAD C02 F01.13 — ANB source-routing evidence boundary (source-only, 2026-10-11)

**Research-only · FACAD \`Angle3p\` numeric output NOT TESTED · no patient interaction · no runtime patch · F01.13 OPEN.**

## 1. Precise question and evidence hierarchy

The manufacturer C02 PDF (SHA256 \`4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548\`) p.5 short source excerpt describes SNA and SNB as angles at N with rays toward S/A and S/B, and ANB as an angle at N toward A/B. This was proven by successful [Windows C02 source run #38103228900](https://github.com/hraaaaf/Digital_crown/actions/runs/38103228900) / artifact 11689141187, limited to 10 micro-excerpts / 147 words; [primary-source adjudication](FACAD_314_C02_PRIMARY_SOURCE_ANB_PFH_TRIAGE_2026-10-11.md). Steiner's FACAD editor metadata says \`ANB=Angle3p(N,A,B)\`. It does **not** prove the runtime Angle3p sign, orientation, range, reflex handling or numeric outputs; screenshots/diagrams not independently certified.

All repo observations below refer to live \`master\` **Git blob IDs**, verified independently also on PR #829 branch. They are **code evidence**, not clinical-science validation.

## 2. Real Digital Crown ANB authority traces

| Route | Real file / verified Git blob | Fact read from source | Important limitation |
|---|---|---|---|
| Legacy geometry | \`backend/services/cephalo_engine.py\` / \`240e938a6618557c9630fee8b5e9b49e18b6403c\` | \`_get_clinical_angle\` uses an unoriented \`acos(dot)\`, \`SNA=angle(N→S,N→A)\`, \`SNB=angle(N→S,N→B)\`; \`ANB=sna-snb\`. | No sign-aware formula in that code path. |
| Typed Steiner geometry | \`backend/services/cephalo_steiner_geometry.py\` / \`70900959042c7e7373c404959c18122e3b8038e3\` | \`steiner_anb_deg_v1\` returns \`round(SNA,1)-round(SNB,1)\`. | Its numerical identity to legacy is intentional; an internal match is not external validation. |
| Strict typed adapter | \`backend/services/cephalo_steiner_evidence_adapter.py\` / \`f9176686b1787f5b88573e5d5cca121399036eab\` | Refuses to materialize an AVAILABLE Steiner evidence value if it differs from legacy result. | Could propagate same assumption twice; fail-closed consistency checks are not a vendor oracle. |
| Backend call chain | \`backend/services/cephalo_service.py\` / \`2e3c05d38d380d3f486d742281374272346b9a5b\`; \`backend/services/cephalo_safe_engine.py\` / \`9b0957f298d1cb3b98e38889bac813c34db4ee04\` | Service imports SafeCephaloEngine and Safe delegates metric calculations to legacy CephaloEngine; service persists results and a separate evidence graph. | Source route observed; no live API end-to-end user/browser execution in this sublot. |
| Typed evidence graph | \`backend/services/cephalo_runtime_evidence.py\` / \`ee82322369291d85b0f93338292196cb61f4b6e5\` | Materializes \`steiner_measurements\` and \`canonical_v2_measurements\`; annotates \`legacy_angles_data_role="COMPATIBILITY_OUTPUT"\`. | A single source is not demonstrated for every UI/report consumer. |
| Frontend analysis workbench | \`frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx\` / \`c2b3b3337bd6aa99cd6b977811749fce561a5b22\` | \`all\` lists legacy \`ANB\`, while \`steiner\` lists canonical \`M_ANB_DEG_V1\`. \`metricFromResults\` resolves \`M_*\` via Steiner projection and ordinary names via \`anglesData.metrics.analyse_osseuse\`. | **Two different presentation data paths exist**, though their actual numeric values/convergence in browser await AFTER test. |
| UI backing projection | \`backend/services/cephalo_protocol_projection.py\` / \`a861830f1d507f8988ec7d1ad6c9b5486ce6d619\` | \`project_steiner_static_protocol\` projects canonical measurement ids, including \`M_ANB_DEG_V1\`; references are shown without classification authority. | Source-locked projection is not FACAD parity. |
| Existing tests | \`backend/tests/test_cephalo_r5_steiner_skeletal.py\` / \`64110061a9165abda66bf3ed2f7da41154b9c420\` | Tests internal Steiner-vs-legacy equality, specifically round-before-subtract 1.7° versus subtract-before-round 1.6°. | Existing test suite certifies **internal compatibility**, not C02 operator semantics. |

**Clinical risk:** A false assurance may be created if the equal legacy/typed values are interpreted as independent confirmation of an angle at N between rays N→A and N→B. The source mathematics are different for some synthetic configurations. Whether FACAD's reported ANB is actually inconsistent is **unknown**.

## 3. Independent, geometrically exact negative fixtures

Harness: \`docs/audits/scripts/facad_anb_source_route_oracle.py\`. It imports the **actual pinned** \`steiner_anb_deg_v1\` from the checked-out repo and implements independently the **hypothetical unoriented** angle between rays N→A and N→B using \`atan2(|cross|,dot)\`. Six production source files are SHA-pinned by Git blob hashing, and eight route assertions fail on drift. No vendor runtime, patient, browser or clinical app is invoked.

| Synthetic fixture | N, S, A, B | Actual pinned Steiner/legacy-parity candidate | Unoriented N angle hypothesis | Hypothetical difference |
|---|---|---:|---:|---:|
| F1_STRADDLE | N(0,0), S(−1,0), A(1,1), B(1,−1) | 0.0° | 90.0° | 90.0° |
| F1_MIRROR | N(0,0), S(−1,0), A(1,1), B(1,1) | 0.0° | 0.0° | 0.0° |
| F2_VERTICAL | N(0,0), S(0,1), A(1,1), B(1,−1) | −90.0° | 90.0° | 180.0° |
| F3_SAME_SIDE | N(0,0), S(0,−1), A(1,1), B(1,2) | −18.4° | 18.4° | 36.8° |

**Logical result:** F1_STRADDLE and F1_MIRROR yield **identical signed legacy/typed ANB = 0.0°** but different *unoriented angle at N* (90° vs 0°). Therefore equality of two unoriented reference-angle magnitudes cannot imply a universally correct three-point angle for any arrangement. These are intentionally non-anatomical *falsification geometry fixtures*, not patient cases, not clinical diagnosis, and **not a claimed FACAD 90° output**.

Negative assertions cover degenerate/missing/nonfinite landmarks, coordinate scale/translation invariance, reference-point sensitivity, and red-gate conservation. No orientation-reflection *vendor* behavior has been observed. For CI proof consult only the **specific HEAD** [experimental source-route workflow](https://github.com/hraaaaf/Digital_crown/actions/workflows/facad-f01-13-anb-source-route-synthetic.yml) and its actual run (when finished); do not infer a GREEN result from the source file's existence.

## 4. Expert adversarial reviews — **internal perspectives, not independent clinicians**

**Perspective A — Scientific validity: 8/10 for threat detection, 0/10 for vendor numeric parity.** The test effectively falsifies unconditional equivalence under an explicit unsigned hypothesis; \`Angle3p\` signed conventions, actual FACAD output, screenshot/oracle and source normative edition remain **BLOCKER**. It would be scientifically wrong to automatically replace ANB in the production engine with \`angle(A–N–B)\` without proving the intended version and signed interpretation.

**Perspective B — Runtime/privacy/QA: 7/10 for bounded source/pin design, 0/10 clinical readiness.** The code inventory exposes a potential duplication of authority in the UI (all vs Steiner) but no AFTER screenshot or end-to-end simulation was run. CI only executes a Python source-only harness. FACAD trial auto-start and shared write D3 concerns remain; running numeric FACAD before isolation is not authorized. Thus no new confirmed unsafe clinical output nor a clinically approved fix.

## 5. Strict decision and next proof

- \`F01.13=OPEN\`, \`FAC03_D3=OPEN_RED\`, \`FAC05=NOT_TESTED\`, \`CLINICAL_EDIT_ALLOWED=false\`, \`CONVERGED=false\`.
- Next **required** numerical parity contract (not executed): independent disposable/safely-isolated FACAD environment with licensed source build pinned; **no patient**; same synthetic S/N/A/B physical coordinates, orientation and calibration supplied to FACAD and DC; operator \`Angle3p(N,A,B)\` explicitly chosen; measure both raw and displayed angles, sign, range, boundary cases, and rounding with a predeclared tolerance; compare against both legacy \`ANB\` and typed \`M_ANB_DEG_V1\`; capture isolated app process effects and confirm FAC03 D3 before any mutable operation. If safety cannot be demonstrated, stay source-only.
- Review by **real independent qualified orthodontic clinician** and code safety specialist, two converged clean reviews on exact scientific HEAD, not ChatGPT-only perspectives.
- **No change to the 39/99 (39.4%) roadmap score**, no clinical gate promotion, no merge, no Vercel deployment.


## 6. Exact HEAD CI result and replay evidence (verified, NOT FACAD validation)

- **Scientific harness** : [ANB source-route run #38104089716](https://github.com/hraaaaf/Digital_crown/actions/runs/38104089716) **COMPLETED/SUCCESS** on the exact source HEAD `5d56f3e3949880d01a5b293b4903e37af7f7e3bd`; [job #114365796968](https://github.com/hraaaaf/Digital_crown/actions/runs/38104089716/job/114365796968) log explicitly says **`Ran 9 tests in 0.061s / OK`**, `SOURCE_ROUTE_PINS_VERIFIED=6`, `RESEARCH_SYNTHETIC_CASES=4`, `ANB_VENDOR_PARITY_NOT_CERTIFIED=true`. All job steps completed successfully.
- **Artifact verified independently after download :** artifact **11689062603**, ZIP SHA256 `2b0e33b098d81adda91db248992f2e6eee3430e72c11cd966311ea74e0ed9a9d`; the only file is `facad-anb-source-route-metadata.json` SHA256 `d8df0f2855db148306afaab35ba40acdaba349c11ddf2d517d61177f3156fe62`. A separate JSON parser replay verified six Git blob pins, eight route assertions, four expected fixture triples with zero vendor outputs, `fac03_d3=OPEN_RED`, `fac05=NOT_TESTED`, `f01_13=OPEN`, and no clinical edit.
- **CI classification:** this one ANB workflow is **EXPERIMENTAL scientific research**, not a required clinical/merge gate; independent source-route tests and declared synthetic geometry pass, **FACAD proprietary `Angle3p` numeric semantics remain untested**. Even green GitHub workflow must not be interpreted as safety-isolated FACAD execution or independent orthodontic approval.
- All verification above is tied to the **source test HEAD `5d56f3e...`**, with unchanged harness and runtime source pins on the documentation-only subsequent commit. PR current/latest SHA should be independently checked before any merge or release decision.

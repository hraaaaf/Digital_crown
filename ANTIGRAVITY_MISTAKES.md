# ⚠️ ANTIGRAVITY - Error Log & Lessons Learned

This document lists technical and ergonomic pitfalls identified during the development of Digital Crown, ensuring constant code quality and UX excellence.

---

### 1. Ergonomics & UI
- **[ERROR] Low Contrast**: Entering financial amounts in light gray on a pale blue/gray background.
- **[CORRECTION] "High-Contrast" Standard**: All financial inputs must imperatively use `text-slate-950` (intense black) with `font-black` (extra-bold) on `bg-white` (pure white) backgrounds.
- **[LESSON]**: The readability of figures (prices, dosages) takes precedence over glassmorphism aesthetics.

### 2. Frontend Architecture
- **[ERROR] Duplicate Entry Logic**: The price form was defined twice (once in `TreatmentSelector.tsx` and once internally in `Odontogram.tsx`). The first fix thus failed to touch the interface actually used by the practitioner.
- **[CORRECTION] Style Centralization**: Use CSS class constants or atomic input components to ensure all visual changes apply everywhere.
- **[LESSON]**: Always check if multiple "entry points" (Popover vs Modal) exist for the same feature before validating a fix.

### 4. Performance & React Lifecycle
- **[ERROR] Components defined inside parent body**: `LiveDocumentStudio` was defined inside `SetupWizard`. This forced React to recreate the component type on every render, neutralizing all cache and causing lags.
- **[CORRECTION] Extraction Outside Body**: Always define sub-components outside the main component (or in a separate file) and pass data via props.
- **[LESSON]**: Never define a React component inside another component. Use `React.memo` on extracted sub-components for maximum optimization.

### 5. Backend & Code Generation (Parsing)
- **[ERROR] CSS Injection via complex F-Strings**: Attempting to inject massive CSS blocks containing braces `{}` and quotes `'` via Python f-strings. The Python parser confused CSS syntax with Python expressions, causing critical parsing errors (`missing closing quote`, `unknown name atic`).
- **[CORRECTION] List-based Construction (`css_lines.append`)**: Abandon multi-line f-string blocks for injected code. Prefer line-by-line construction via a list, then `"\n".join(lines)`.
- **[LESSON]**: NEVER use f-strings for more than 3-5 lines of injected code. The longer the block, the higher the risk of collision between syntaxes (Python vs CSS/JS).

### 6. Code Integrity & Build (Session v5.1)
- **[ERROR] Truncations & Corrupted JSX**: Multi-block modifications resulting in accidental deletion of closing tags or vital business logic.
- **[CORRECTION] Strict Integrity Protocol**: After each `replace`, systematically check opening/closing coherence (`{}`, `()`, `<>`). Perform a comparative "before/after" read.
- **[ERROR] Build Pollution (Warnings as Errors)**: Leaving unused variables or imports blocked the production pipeline.
- **[CORRECTION] Pre-Build Manual Linting**: Before launching the final build, scan imports and local variables. Prefer `npm run build` early in the process to detect orphans.
- **[ERROR] Imprecise Typing**: Confusing `string` with specific string union types (e.g., `PaymentMode`).
- **[CORRECTION] Definition Verification**: Always go back to the source of truth of the interface (`types.ts` or local definition) before modifying a prop or state.

### 7. Client Preferences & Sobriety (v5.3)
- **[ERROR] Visual Overload (Odontogram)**: Attempting to insert a complex anatomical schema on A5 documents, causing visual clutter and reducing space for acts.
- **[CORRECTION] Immediate Neutralization**: The odontogram must remain an internal studio entry/visualization tool and must NEVER appear on final documents (Quotes/Notes) unless explicitly requested otherwise.
- **[LESSON]**: "Less is More" in medical environments. Administrative clarity takes precedence over graphic sophistication.

### 8. Layering Hierarchy (Z-Index)
- **[ERROR] Insufficient Sidebar Z-Index**: Using `z-50` on the sidebar while dynamic content (Document Hub, Studio) uses complex stacking contexts. Result: lateral navigation became inaccessible when certain modes (Schema/Preview) were activated.
- **[CORRECTION] Navigation Priority (`z-[10000]`)**: The sidebar must have a `z-index` of `10000` to remain clickable above popovers (often at `9999`).
- **[LESSON]**: Navigation is the user's "lifeboat". It must NEVER be covered.

### 9. Document Engine Unification (v5.6)
- **[ERROR] Tech Disparity**: Mixing WeasyPrint (HTML) and ReportLab (Canvas) caused branding drift and layout inconsistencies between Clinical and Accounting documents.
- **[CORRECTION] ReportLab Standardization**: Migrated all generators (Ordonnance, Certificat, Libre) to the ReportLab "Elite" engine used by Accounting.
- **[RULE] Strict Sobriété**: Confirmed the exclusion of the Odontogram from all patient-facing documents to prevent visual clutter on A5 format, prioritizing professional typography and "Navy Blue" branding.

### 10. Elite Branding & Readability
- **[ERROR] Using Black (Slate-900) on Glass**: Applying dark text on a glass background (`bg-white/40`) making it hard to read in bright light or on small screens.
- **[CORRECTION] Use Identity Visuals (`text-primary`)**: Prefer the clinic's primary color for titles and shortcuts on translucent backgrounds. It offers better contrast and reinforces "Premium Elite" branding.
- **[LESSON]**: Identity color is not just decorative; it is a tool for hierarchy and readability.

### 10. Agent Modification Safety
- **[ERROR] Multi-File Collision**: Attempting to apply a `Sidebar` fix in `AccountingStudio.tsx` due to similar patterns (e.g., `aside` or `z-index`).
- **[CORRECTION] Contextual Verification**: Always ensure `TargetFile` exactly matches the intent before validating a `multi_replace`.
- **[LESSON]**: The power of multi-replacement tools requires double visual validation of file paths.

### 11. Minimalist "Elite" Design (v5.7)
- **[ERROR] Label Redundancy**: Hardcoding labels like "Posologie :" in clinical documents. This adds visual noise without extra information.
- **[CORRECTION] Semantic Layout**: Rely on indentation and typography (italics/bold) to differentiate the drug from its instructions. Remove all "Posologie :" prefixes.
- **[LESSON]**: In a premium design, the structure must speak for itself. Avoid explaining the obvious with labels.

### 12. Template & CSS Stability
- **[ERROR] F-String Parsing in CSS**: Using Python f-strings for CSS blocks in `template_engine.py` caused errors when CSS variables (e.g. `--primary`) were mistaken for Python variables.
- **[CORRECTION] Raw String or List Join**: Use standard strings or `"\n".join()` for CSS blocks. Never use f-strings if the content contains braces `{}` that aren't Python placeholders.
- **[LESSON]**: Separate code injection from string interpolation.

### 13. React Lifecycle & Tool Misuse (v1.3)
- **[ERROR] Hooks defined outside Component body**: During a large `multi_replace`, React hooks (`useState`, `useEffect`) were accidentally placed outside the functional component definition in `AccountingStudio.tsx`. Result: immediate runtime crash (`Invalid hook call`).
- **[CORRECTION] Strict Structural Re-check**: Always verify that all `use*` calls are within the first lines of the function body. Systematically re-read the component wrapper after massive edits.
- **[LESSON]**: Large code replacements (over 100 lines) require manual structural validation of the React function wrapper.

### 14. Cephalometric Pipeline & Landmark Mapping
- **[ERROR] Mapping Mismatch (stpog vs pog_soft)**: The frontend used `stpog` in some places while the geometric engine expected `Pog_soft`. This broke the Ricketts E-line and Naso-Labial analysis.
- **[ERROR] Non-Interactive Soft Tissue Points**: Landmark points for soft tissue (lips, nose, chin) were explicitly filtered out from the interactive layer in `CephaloTracingLayer.tsx`. This prevented practitioners from refining the AI's detection, making the analysis "fixed" and sometimes inaccurate.
- **[CORRECTION] Synonym Normalization & Activation**: 1) Unified naming (UL/Ls, LL/Li, stPog/Pog_soft) across backend and frontend. 2) Removed the interaction filter to allow manual adjustment of all 38 points.
- **[LESSON]**: AI detection is only a starting point; the practitioner must always have the final word on landmark placement to ensure diagnostic accuracy.

### 15. MICCAI 2023 Landmark Mapping Discrepancies
- **[ERROR] Off-by-one and Name Mismatch**: The system used a generic ISBI-style mapping (S=0, N=1, Or=2, Po=3...) for the CL-Detection 2023 model, but the challenge model shifted many points (e.g., Sn moved to 15, Pronasale to 26). This caused "spaghetti" splines and inaccurate diagnostics.
- **[CORRECTION] Definitive MICCAI 2023 Mapping**: Re-mapped all 38 points according to the official challenge table. Specifically fixed the soft-tissue sequence (Ls, Li, Sn, Pog') and the nose point (Prn).
- **[LESSON]**: Deep learning models from specific challenges (MICCAI, ISBI) MUST use their exact original mapping table. Never assume a "standard" order for landmark detection outputs.

### 16. Panoramic AI Mapping & Apical Blindness (v1.5)
- **[ERROR] Horizontal FDI Compression**: Peripheral teeth (molars) were being identified as premolars (e.g., 45 instead of 46). This was due to linear X-axis thresholds failing to account for the lateral stretching/magnification of panoramic X-rays.
- **[ERROR] Apical Cécité**: Initial confidence thresholds (0.25) were too strict for subtle periapical lesions on lower incisors, often obscured by the spine's shadow.
- **[CORRECTION] Elite Calibration & Adaptive Thresholds**: 1) Shifted FDI thresholds (v1.5.3) to favor molars in the periphery. 2) Implemented class-specific thresholds (15% for Periapical Lesions) and boosted CLAHE contrast (4.5) to reveal subtle apical radiolucencies.
- **[LESSON]**: In panoramic imaging, horizontal tooth numbering must compensate for non-linear lateral stretching. Critical pathologies (Apex) require higher sensitivity than obvious ones (Caries).

### 17. Backend Integrity & WatchFiles Safety (v1.6)
- **[ERROR] Corrupted Imports (`mport os`)**: An accidental keystroke during a file modification corrupted the first line of `panoramic_service.py`. This caused a syntax error that crashed the entire FastAPI backend during a reload triggered by `WatchFiles`.
- **[CORRECTION] Strict First-Line Validation**: Always perform a final "sanity check" on the very first and last lines of a file after an edit, especially when working on files with many imports.
- **[LESSON]**: Backend reliability is fragile. A single missing letter in an `import` statement can take down the entire system. Systematic verification of the backend logs after each edit is MANDATORY.

### 18. Build Pollution & Component Integrity (v1.7)
- **[ERROR] Unused Variables in Refactored UI**: Declaring props or state variables (e.g., `applyGroupTreatment`, `setActiveActSearchId`) without using them. Result: `tsc` build failure in production-ready environments.
- **[ERROR] Missing Mandatory Props**: Calling complex components like `OdontogramSVG` with only a subset of props, ignoring mandatory ones (`teethSurfaces`, `selectedSurface`).
- **[CORRECTION] Strict Dependency & Usage Check**: 1) Use every destructured prop or remove it. 2) Systematically check the interface/definition of any child component before calling it. 3) Run `npm run build` locally after any structural UI refactoring.
- **[LESSON]**: A "Ghost Elite" UI must not only look premium but must also be technically flawless. Every variable declared must have a purpose, and every component contract must be respected.

---
*Last updated: 2026-05-05 (Session v1.7 - Digital Crown Elite)*

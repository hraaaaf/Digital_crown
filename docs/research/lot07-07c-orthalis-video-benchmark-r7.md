# LOT07 / 07-C — Orthalis video benchmark → Command Workbench: delta review R7

**Status:** REVIEWED_VIDEO / STATIC_VISUAL_EVIDENCE; business actions **NOT CERTIFIED**; `READY_TO_REFINE_COMMAND_TARGET=YES`; `READY_TO_IMPLEMENT_OR_MERGE=NO`.

**Mission:** update the already-existing Command Workbench concept (three static target images: Dashboard, Agenda, Patient record) using Orthalis screen recordings. **No new design direction and no switcher/07-D, mobile, clinical API, data model, RBAC or workflow changes.**

## Source classification and privacy boundaries

- Primary media: one user-supplied **117-second, 480×854 portrait phone video of an Orthalis display** and the two reference photographs previously supplied in the same conversation. Source reviewed **locally**, **not checked into the repo, uploaded to CI, or copied to Notion**.
- Source contains **apparent identifiable patient names, faces, contact/scheduling or treatment information**. Never reproduce patient names, screen crops, videos, phone numbers, treatment-date combinations or text extracted from them in public GitHub. Do not attach files to PR.
- All observations below are **manual visual review of user-provided media**, **NOT findings from REA, instrumented Orthalis or Digital Crown runtime**. Video resolution, filming angle, glare and text legibility limit exact action/state interpretation. Timestamps are approximate.
- Separate REA research from prior runs: [#39146263502](https://github.com/hraaaaf/Digital_crown/actions/runs/39146263502) proved only Windows Server 2022 REA on public Guacamole web client, **NOT** native Orthalis or its clinical actions.
- Existing Digital Crown 07-C **static targets** already delivered on 18 Oct 2026: Dashboard cockpit, compact Agenda, persistent-identity Patient record. They were **reviewed internally at 7/10** (historical assessment, not a fresh pixel-to-pixel appraisal) and have **no user final approval or product implementation**; see [LOT07 canonical Notion](https://app.notion.com/p/3e677c66336281639049f4cc7be1e5ae). Approved G2 Signature Core/Iconic direction belongs to 07-B, [PR #958 DRAFT](https://github.com/hraaaaf/Digital_crown/pull/958), not an approval of 07-C.

## Observed evidence (privacy-safe abstractions)

| Source time / view | What is genuinely visible | What this does NOT prove |
| --- | --- | --- |
| Video ~00:00–00:17 | A dense multi-panel Orthalis working screen: selected patient/context area, neighboring operational tiles, stacked lists and a left vertical navigation strip; simultaneous information zones coexist | That a specific clinical control is actionable, which patient record is stored, correctness of status, accessible focus/tab order |
| Video ~00:18–00:25 | The content changes to a structured form/record view while the general application navigation remains present | Exact number of clicks, persistence of selected patient identity across every module, successful save |
| Video ~00:26–00:53 | A different multi-section work area with large tables/panes and a temporary selector/menu appears | That data is absent or that a particular form was completed; labels are partly unreadable |
| Video ~00:54–01:09 | An odontogram-like dental chart is presented beside a structured list/table in the application workspace | Clinical validity of tooth/treatment data, treatment edit/save path, diagnostic correctness |
| Video ~01:15 onwards | Display leaves the prior clinical interface toward a different desktop/session screen | A confirmed Orthalis logout or product bug; this is outside evidence for clinical flow |
| Still photograph 1 | Higher-resolution Orthalis patient synthesis, appointment history/future reminders, waiting-room state and notes presented in adjacent widgets | Any measured speed, click path, updated appointment transaction |
| Still photograph 2 | A **separate** photo/radiography workspace with filmstrip thumbnails, categories, toolbar and two large viewing regions (Kitview-style) | Confirmed Orthalis→Kitview integration handoff, clinical image correctness, comparison/annotation behavior |

**Actual observed navigation:** screen transitions in a filmed demonstration, not instrumented events. No certified REA time/click measurements. No verified patient-create, appointment-create, note-write, odontogram-edit, Kitview acquisition or Ceph analysis.

## Comparison with the existing 07-C plan — refine rather than restart

| Existing Digital Crown 07-C static target | Orthalis observation | Delta R7 and acceptance evidence |
| --- | --- | --- |
| **Dashboard**: KPIs, appointments, activity summary | Orthalis favors operational density: selected patient, queue and multiple adjacent information zones | **P0** Shift emphasis from generic KPIs to **care-command priority** when the underlying Cabinet data exists: current work context, waiting/arrivals, today activity and next action. Keep summary KPIs secondary. No invented patient, balances, emergencies or allergies. Design target must use same synthetic fixtures across comparisons |
| **Agenda**: compact grid and persistent toolbar | Waiting/queue rows show colored activity/status and timing information; photo does not demonstrate complete agenda scheduling | **P0** Compare agenda + waiting-queue states, duration/status legibility and action ordering; semantic status labels plus color, keyboard focus. The underlying appointment model/permissions remain untouched |
| **Dossier**: persistent patient identity, tabs, record history, imaging, illustrative dental schema and documents | Filmed patient form, multiple side-by-side panels, odontogram near a list | **P0** Keep **single patient context and single primary clinical task per panel**; show adjacent history/chart/lists as supporting workbench, with progressive disclosure to avoid the target's known cognitive overload. Illustrative chart must never pretend to display a verified clinical case |
| **Imagerie**: specified in Command contract but **not rendered in the three existing 07-C targets** | Separate Kitview-style still shows thumbnail filmstrip, category navigator and two viewer panes | **P1** Add **a fourth visual STATE within the same Command design**, not a fourth experience/theme: patient identity context, categorized thumbnails, one/two comparison workspaces, clear missing-media state. Do not claim acquisition/compare functions until Cabinet source checks |
| **Cross-module operation**: persistent identity and navigation stipulated in canonical contract | Video shows navigation strip and changing work zones; detailed multi-module handoff not proven | **P0** Require a verified source/data-context contract and no cross-patient leakage on user switch, logout, role loss, or rapid patient A→B before runtime approval. No changing RBAC/API/storage |
| **Readability / accessibility**: 200% native zoom, keyboard, varied desktop widths | High information density and color cues, and phone-recording glare. Reference is informative, **not** a usability gold standard | **P0** Benchmark 1280/1440/1920 and native zoom 200%; controls must have labels independent of colors, visible focus, controlled overflow and privacy-safe screenshots |

## Critical internal adversarial review (two lenses; not independent external reviewers)

**UX / task-completion reviewer:** Historical three-screen concept was **7/10**, not certified. Orthalis supplies useful evidence for density and inter-panel context; it also exposes a risk: microtext and overloaded fields. Priority is improving task hierarchy and maintaining one active patient context, **not** reproducing its grid cell sizes, colors, icons, names or source code. Video lacks readable, instrumented action paths; confidence for process efficiency is low.

**Security / evidence reviewer:** Sharing raw media, unsanitized transcripts or screenshots would expose sensitive patient data in a public repo (**BLOCKER**). Claiming exact click counts, behavior, native software execution, RBAC, timers or verified integration from a low-resolution phone video would be false evidence (**MAJOR**). Preserve raw media only in authorized private user context; GitHub markdown includes **no identifying details**.

**Decision:** `BENCHMARK_STRUCTURAL=PARTIAL_PASS`; `BENCHMARK_INTERACTIVE=OPEN`; `COMMAND_CONCEPT_REFINE=YES`; `07C_IMPLEMENTATION=NOT_AUTHORIZED_OR_VALIDATED`; `CONVERGED=NO`; avoid a fabricated new /10 score.

## Next in same LOT07 / 07-C

1. Refine **the same** three Command TARGET screens using the above P0 deltas and include the **Imagerie state** already within the 07-C contract, with consistent anonymized fixtures. Keep 07-B Signature Iconic tokens and current Cabinet clinical truth; no clone of Orthalis design.
2. Gather REAL Digital Crown Cabinet source screenshots + same-fixture BEFORE/TARGET comparisons at fixed desktop viewports and 200% browser-native zoom, run focus/keyboard tests, prove RBAC/patient isolation before labeling any AFTER.
3. Ask the owner to approve the **revised target** before developing Command on a scoped implementation PR. 07-D reversible per-user/workstation selector and 07-E certification remain later stages; no merge/deploy here.

**R7 status:** a documented design-delta and research decision only, suitable for further concept refinement, **not runtime certification**.

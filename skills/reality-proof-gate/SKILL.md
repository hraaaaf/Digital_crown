# Reality Proof Gate — execution skill

Use for every V1.5 lot/sub-lot, with risk-scaled evidence as specified in [the canonical RPG policy](../../docs/quality/REALITY_PROOF_GATE.md).

1. Read the canonical V1.5 roadmap and FUE-0/I/G plan; identify the exact sub-lot and required user-visible outcome.
2. Define fictitious actors A/B, isolated databases, separate authentication, producer/consumer process boundaries and failure cases before coding.
3. Run RPG-C first; for UI run RPG-J in a real browser and inspect screenshot/traces; for transfers run RPG-X with separate sender and receiver, real HTTPS, immutable file SHA-256 and visible render. Shared TestClient is only an integration test.
4. For sensitive flows run RPG-F: wrong patient/tenant, replay, revoked, expired, offline, restart, race and purge. Ensure tests actually execute (not collect-only) and inspect CI steps.
5. Record exact HEAD and CI URLs, job logs, assertion counts, skipped tests, producer/consumer artifact hashes, screenshots, denial outcomes and cleanup evidence. Compare BEFORE/AFTER viewports for UI.
6. Apply FUE-first verification (FUE-0 / FUE-I / FUE-G as applicable), record inspectable executed evidence, and perform targeted security/privacy/clinical/data reviews when risk requires them. Two adversarial A/B reviews are not a default gate. Fix findings, rerun impacted evidence and confirm on the final HEAD.
7. Declare OPEN if a required real-device or human gate (RPG-P) was not performed. Never conflate GREEN, CONVERGED, physical certification, merge or deployment.

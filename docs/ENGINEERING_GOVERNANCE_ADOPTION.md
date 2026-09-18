# Engineering governance adoption

Digital Crown explicitly adopts the central engineering-governance baseline:

- version: `1.0.0`
- exact source commit: `4c0ed295cc095fc5e7f9d0ddde3b1af95ac8dba9`
- adoption manifest: `.governance/adoption.json`

## Precedence

The central doctrine is a minimum engineering standard. Existing Digital Crown rules remain in force whenever they are stricter or domain-specific.

This adoption does not alter the canonical V1 execution order and does not authorize work outside the currently unlocked V1 lot. In particular it does not weaken:

- the V1 execution lock in `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`;
- local-first/on-premise architecture and real cabinet data protections;
- `CODE_CERTIFIED` / `INSTALLABLE_CERTIFIED` release gates;
- clinical/scientific source, review and fail-closed requirements;
- exact-head evidence, double scoring and Perfection Pass requirements;
- explicit human authorization for merge, deployment, cabinet/production mutation and irreversible actions.

No exception to the central doctrine is active for this repository.

Any future doctrine upgrade requires a new immutable version/SHA pin plus compatibility review. Moving references such as `main` or `latest` are not valid adoption pins.

# Digital Crown — V0 local verification gate

Status: BLOCKED — LOCAL PC VERIFICATION REQUIRED

The previously recorded SHA `76547ed178b98b4d8cf14c0fdc691ff3f787076e` is only a historical candidate inferred from an earlier local observation. It MUST NOT be treated as the canonical installed V0 until an agent with direct access to the cabinet PC re-verifies the live installation.

Required local proof before V0 can be frozen:

- exact repository path actually launching Digital Crown
- `git rev-parse HEAD`
- `git status --short`
- current branch/ref
- `/api/health` version/build identifier
- active backend/frontend processes and executable/working-directory paths
- current Alembic revision
- PostgreSQL host/database name and version, with credentials masked
- current user/media data root
- whether a packaged runtime or the development repository is actually being launched

If the local SHA differs from `76547ed178b98b4d8cf14c0fdc691ff3f787076e`, the local SHA becomes the V0 software candidate and the existing historical reference must remain non-canonical.

No cabinet update is authorized until this local verification is complete.

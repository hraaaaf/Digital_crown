"""J2.1 nonclinical candidate: tenant-scoped scene CAS in an isolated APP test DB.

This module is not registered by production. Its strict runtime guards refuse any
non-test engine, non-disposable database file, or unauthorized caller. All images
are verified via DC-DOS-05 before any scene read or write.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models_ceph_premium_scene_fue import CephPremiumSceneFueSnapshot
from backend.schemas.cephalo_premium_scene_contract import CephaloPremiumSceneDraft
from backend.services.ceph_premium_scene_source_lab import verify_via_dc_dos05


class SceneAppFueError(ValueError):
    def __init__(self, detail: str, status_code: int = 409):
        super().__init__(detail)
        self.status_code = status_code


def assert_isolated_scene_app_db(db: Session) -> None:
    if not (os.environ.get("ENVIRONMENT") == "test"
            and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
            and os.environ.get("CEPH_J21_SCENE_APP_FUE_ONLY") == "1"
            and os.environ.get("DC_DOS05_FUE_ONLY") == "1"):
        raise SceneAppFueError("J2.1 isolated scene FUE is disabled", 503)
    bind = db.get_bind()
    if bind is None or bind.dialect.name != "sqlite":
        raise SceneAppFueError("Refusing non-test application DB backend", 503)
    db_name = getattr(bind.url, "database", None)
    root_str = os.environ.get("CEPH_J21_SCENE_APP_FUE_ROOT")
    if not isinstance(db_name, str) or not db_name or not root_str:
        raise SceneAppFueError("Persistent synthetic test root is required", 503)
    try:
        root = Path(root_str)
        file = Path(db_name)
        temp = Path(tempfile.gettempdir()).resolve(strict=True)
        if root.is_symlink() or file.is_symlink():
            raise SceneAppFueError("Symlinked synthetic database rejected", 503)
        resolved = root.resolve(strict=True)
        expected = resolved / "ceph-j21-scene-app-fue.sqlite3"
        if temp not in resolved.parents or file.resolve() != expected:
            raise SceneAppFueError("Application DB is not the dedicated disposable FUE", 503)
    except (OSError, RuntimeError) as exc:
        raise SceneAppFueError("Unverifiable isolated application DB path", 503) from exc


def _scope(scene: CephaloPremiumSceneDraft) -> tuple[int, int, int]:
    i = scene.identity
    return i.employer_id, i.patient_id, i.study_id


def _decode(row: CephPremiumSceneFueSnapshot) -> CephaloPremiumSceneDraft:
    if hashlib.sha256(row.payload.encode("utf-8")).hexdigest() != row.scene_sha256:
        raise SceneAppFueError("Persisted scene payload was modified")
    try:
        scene = CephaloPremiumSceneDraft.model_validate_json(row.payload)
    except (ValidationError, ValueError) as exc:
        raise SceneAppFueError("Persisted scene schema invalid") from exc
    if (scene.sha256() != row.scene_sha256
            or _scope(scene) != (row.employer_id, row.patient_id, row.study_id)
            or scene.identity.scene_revision != row.scene_revision
            or scene.identity.parent_scene_sha256 != row.parent_scene_sha256):
        raise SceneAppFueError("Persisted scene identity or revision mismatch")
    return scene


def _latest(db: Session, scope: tuple[int, int, int]):
    return (db.query(CephPremiumSceneFueSnapshot)
            .filter(CephPremiumSceneFueSnapshot.employer_id == scope[0],
                    CephPremiumSceneFueSnapshot.patient_id == scope[1],
                    CephPremiumSceneFueSnapshot.study_id == scope[2])
            .order_by(CephPremiumSceneFueSnapshot.scene_revision.desc())
            .first())


def _verified_original(db: Session, scene: CephaloPremiumSceneDraft, scope):
    try:
        return verify_via_dc_dos05(
            db, scene=scene, actor_employer_id=scope[0],
            actor_patient_id=scope[1], actor_study_id=scope[2])
    except (ValueError, RuntimeError, OSError) as exc:
        raise SceneAppFueError("Study/source binding could not be verified") from exc


def _assert_successor(scene, previous, expected_parent_sha256):
    if previous is None:
        if (scene.identity.scene_revision != 1
                or scene.identity.parent_scene_sha256 is not None
                or expected_parent_sha256 is not None):
            raise SceneAppFueError("Initial scene revision and parent invalid")
        return
    parent_sha = previous.sha256()
    if (expected_parent_sha256 != parent_sha
            or scene.identity.parent_scene_sha256 != parent_sha
            or scene.identity.scene_revision != previous.identity.scene_revision + 1):
        raise SceneAppFueError("Stale or mismatched scene revision CAS")
    for field in (
        "employer_id", "patient_id", "study_id", "original_asset_id",
        "original_sha256", "original_width", "original_height",
        "detector_model", "detector_sha256", "detector_mapping_authority",
        "scientific_revision", "scientific_digest", "coordinate_system",
    ):
        if getattr(scene.identity, field) != getattr(previous.identity, field):
            raise SceneAppFueError("Scene original/study/science identity was changed")
    old, new = previous.canonical_dict(), scene.canonical_dict()
    old_landmarks = {landmark.id: landmark for landmark in previous.landmarks}
    for landmark in scene.landmarks:
        prior = old_landmarks.get(landmark.id)
        if prior is not None and (landmark.x, landmark.y) != (prior.x, prior.y):
            if landmark.origin == "SRPOSE38_AUTO":
                raise SceneAppFueError("Edited landmark cannot retain automatic origin")
    if any(old[k] != new[k] for k in ("landmarks", "contours", "calibration")):
        if any(m.status != "UNAVAILABLE" for m in scene.measurements):
            raise SceneAppFueError("Edited geometry must invalidate cached measurements")


def save_scene(db: Session, *, scene: CephaloPremiumSceneDraft,
               expected_parent_sha256: str | None,
               actor_employer_id: int, actor_patient_id: int,
               actor_study_id: int, actor_user_id: int):
    assert_isolated_scene_app_db(db)
    if (type(actor_employer_id) is not int or type(actor_patient_id) is not int
            or type(actor_study_id) is not int or type(actor_user_id) is not int
            or min(actor_employer_id, actor_patient_id, actor_study_id, actor_user_id) <= 0
            or _scope(scene) != (actor_employer_id, actor_patient_id, actor_study_id)):
        raise SceneAppFueError("Scene actor scope does not match", 403)
    if expected_parent_sha256 is not None and (
        type(expected_parent_sha256) is not str or len(expected_parent_sha256) != 64
    ):
        raise SceneAppFueError("Parent digest malformed", 422)
    scope = _scope(scene)
    source = _verified_original(db, scene, scope)
    predecessor = _latest(db, scope)
    previous_scene = None if predecessor is None else _decode(predecessor)
    _assert_successor(scene, previous_scene, expected_parent_sha256)
    item = CephPremiumSceneFueSnapshot(
        employer_id=scope[0], patient_id=scope[1], study_id=scope[2],
        scene_revision=scene.identity.scene_revision,
        scene_sha256=scene.sha256(),
        parent_scene_sha256=scene.identity.parent_scene_sha256,
        payload=scene.canonical_bytes().decode("utf-8"),
        actor_id=actor_user_id,
    )
    db.add(item)
    try:
        db.flush()  # Unique(revision) rejects concurrent stale writes.
    except IntegrityError as exc:
        db.rollback()
        raise SceneAppFueError("Concurrent scene CAS collision") from exc
    return _response(scene, source)


def get_scene(db: Session, *, actor_employer_id: int,
              actor_patient_id: int, actor_study_id: int):
    assert_isolated_scene_app_db(db)
    scope = (actor_employer_id, actor_patient_id, actor_study_id)
    if any(type(value) is not int or value <= 0 for value in scope):
        raise SceneAppFueError("Invalid actor scope", 403)
    row = _latest(db, scope)
    if row is None:
        raise SceneAppFueError("No saved scene in scoped study", 404)
    scene = _decode(row)
    source = _verified_original(db, scene, scope)
    return _response(scene, source)


def _response(scene, source):
    return {
        "scene_sha256": scene.sha256(),
        "scene_revision": scene.identity.scene_revision,
        "scene": scene.canonical_dict(),
        "verified_original": source,
        "scientific_digest_source_certified": False,
        "clinical_release": False,
        "desktop_fue_verified": False,
    }

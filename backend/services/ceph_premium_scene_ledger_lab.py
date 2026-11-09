"""CEPH-PREMIUM J2.1-M3: append-only lab CAS revisions in an IN-MEMORY SQLite.

This is a disposable verification harness and NEVER registers ORM tables,
prod routes or migrations. The clinic's real study/tenant authorization must be
established separately by a trusted route before any future use.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3

from backend.schemas.cephalo_premium_scene_contract import CephaloPremiumSceneDraft


class SceneCasError(ValueError):
    pass


class SceneLabLedger:
    def __init__(self, connection: sqlite3.Connection):
        files = [row[2] for row in connection.execute("PRAGMA database_list")]
        if any(name for name in files):
            raise SceneCasError("Refusing disk or production sqlite connection")
        self.db = connection
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS ephemeral_scene_snapshots (
                employer_id INTEGER NOT NULL, patient_id INTEGER NOT NULL,
                study_id INTEGER NOT NULL, scene_revision INTEGER NOT NULL,
                scene_sha256 TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY (employer_id, patient_id, study_id, scene_revision),
                UNIQUE(scene_sha256)
            )"""
        )

    @staticmethod
    def _scope(scene: CephaloPremiumSceneDraft):
        id = scene.identity
        return id.employer_id, id.patient_id, id.study_id

    @staticmethod
    def _decode(row: tuple):
        scene_hash, raw = row
        if hashlib.sha256(raw.encode("utf8")).hexdigest() != scene_hash:
            raise SceneCasError("Stored scene digest corrupted")
        scene = CephaloPremiumSceneDraft.model_validate_json(raw)
        if scene.sha256() != scene_hash:
            raise SceneCasError("Stored scene schema does not match its digest")
        return scene

    def latest(self, *, employer_id: int, patient_id: int, study_id: int):
        if any(type(n) is not int or n <= 0 for n in (employer_id, patient_id, study_id)):
            raise SceneCasError("Invalid actor study scope")
        row = self.db.execute(
            """SELECT scene_sha256,payload FROM ephemeral_scene_snapshots
               WHERE employer_id=? AND patient_id=? AND study_id=?
               ORDER BY scene_revision DESC LIMIT 1""",
            (employer_id, patient_id, study_id),
        ).fetchone()
        return None if row is None else self._decode(row)

    def append(self, scene: CephaloPremiumSceneDraft, *,
               expected_parent_sha256: str | None,
               actor_employer_id: int, actor_patient_id: int, actor_study_id: int):
        if not isinstance(scene, CephaloPremiumSceneDraft):
            raise SceneCasError("Scene must pass strict schema validation")
        if any(type(n) is not int or n <= 0 for n in (
                actor_employer_id, actor_patient_id, actor_study_id)):
            raise SceneCasError("Invalid actor scope")
        scope = self._scope(scene)
        if scope != (actor_employer_id, actor_patient_id, actor_study_id):
            raise SceneCasError("Cross-tenant, patient or study scene rejected")
        started = False
        try:
            self.db.execute("BEGIN IMMEDIATE")
            started = True
            previous = self.latest(
                employer_id=scope[0], patient_id=scope[1], study_id=scope[2]
            )
            if previous is None:
                if (scene.identity.scene_revision != 1
                        or scene.identity.parent_scene_sha256 is not None
                        or expected_parent_sha256 is not None):
                    raise SceneCasError("First snapshot must be revision 1 without parent")
            else:
                parent_sha = previous.sha256()
                if (expected_parent_sha256 != parent_sha
                        or scene.identity.parent_scene_sha256 != parent_sha
                        or scene.identity.scene_revision
                        != previous.identity.scene_revision + 1):
                    raise SceneCasError("Stale or mismatched scene revision CAS")
                for attr in (
                    "employer_id", "patient_id", "study_id", "original_asset_id",
                    "original_sha256", "original_width", "original_height",
                    "detector_model", "detector_sha256", "detector_mapping_authority",
                    "scientific_revision", "scientific_digest", "coordinate_system",
                ):
                    if getattr(scene.identity, attr) != getattr(previous.identity, attr):
                        raise SceneCasError("Original identity/algorithm/revision changed")
                current_data = scene.canonical_dict()
                previous_data = previous.canonical_dict()
                scientific_sources_changed = any(
                    current_data[key] != previous_data[key]
                    for key in ("landmarks", "contours", "calibration")
                )
                if scientific_sources_changed and any(
                    m.status != "UNAVAILABLE" for m in scene.measurements
                ):
                    raise SceneCasError(
                        "Changed landmark/contour/calibration invalidates all cached measurements"
                    )
            text = scene.canonical_bytes().decode("utf8")
            digest = scene.sha256()
            self.db.execute(
                """INSERT INTO ephemeral_scene_snapshots
                (employer_id,patient_id,study_id,scene_revision,scene_sha256,payload)
                VALUES(?,?,?,?,?,?)""",
                (*scope, scene.identity.scene_revision, digest, text),
            )
            self.db.commit()
            return digest
        except (sqlite3.Error, ValueError):
            if started:
                self.db.rollback()
            raise

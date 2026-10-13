"""LOT05.5 real API guard / read-only preflight + separate synthetic engine checks.

Tests import only source services and ORM declarations. Never boot cabinet DB or
main.py and never construct a real clinical tenant.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

from sqlalchemy import create_engine, text, MetaData, inspect, event

from test_legacy_sql_migration_scenarios_v15 import _real_declared_model_only

BACKEND = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "lot05_5_migration_gateway", BACKEND / "services" / "legacy_migration_gateway_v15.py"
)
import sys
svc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = svc
SPEC.loader.exec_module(svc)


def _fake_table_subset():
    md = MetaData()
    original = _real_declared_model_only()
    for name in ("users", "patients", "agenda_resources", "appointments"):
        original.tables[name].to_metadata(md)
    return md


def _fake_db(version="neo000000027"):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    md = _fake_table_subset()
    with engine.begin() as c:
        c.exec_driver_sql("PRAGMA foreign_keys=ON")
        md.create_all(c)
        if version is not None:
            c.execute(text("CREATE TABLE alembic_version(version_num VARCHAR(32))"))
            c.execute(text("INSERT INTO alembic_version VALUES(:v)"), {"v": version})
    return engine, md


class MigrationOwnerGuardTests(unittest.TestCase):
    def fake_owner(self, **changes):
        args = {
            "id": 777, "role": "DENTISTE", "is_active": True,
            "employer_id": None, "approval_status": "approved",
        }
        args.update(changes)
        return SimpleNamespace(**args)

    def test_owner_dentist_allowed(self):
        self.assertEqual(svc.require_cabinet_owner(self.fake_owner()), 777)

    def test_admin_root_allowed(self):
        self.assertEqual(svc.require_cabinet_owner(self.fake_owner(role="ADMIN")), 777)

    def test_employed_dentist_denied_despite_settings(self):
        with self.assertRaisesRegex(svc.MigrationPreflightRefused, "CABINET_OWNER_ONLY"):
            svc.require_cabinet_owner(self.fake_owner(employer_id=778))

    def test_secretary_denied(self):
        with self.assertRaisesRegex(svc.MigrationPreflightRefused, "CABINET_OWNER_ONLY"):
            svc.require_cabinet_owner(self.fake_owner(role="SECRETAIRE"))

    def test_inactive_pending_or_invalid_owner_denied(self):
        for user in (self.fake_owner(is_active=False),
                     self.fake_owner(approval_status="pending"),
                     self.fake_owner(id="777")):
            with self.assertRaises(svc.MigrationPreflightRefused):
                svc.require_cabinet_owner(user)


class ReadOnlyPhysicalPreflightTests(unittest.TestCase):
    def test_exact_fake_version_and_orm_subset_exposes_only_safe_target_columns(self):
        engine, md = _fake_db()
        try:
            with engine.connect() as c:
                report=svc.inspect_cabinet_schema_read_only(c,md)
            self.assertTrue(report["schema_revision_matches"])
            self.assertTrue(report["declared_subset_matches"])
            self.assertTrue(report["physical_subset_checked"])
            self.assertFalse(report["full_schema_certified"])
            self.assertFalse(report["import_permitted"])
            self.assertEqual([t["name"] for t in report["target_preview"]["tables"]],
                             ["patients","appointments"])
            self.assertNotIn("employer_id", [
                col["name"] for t in report["target_preview"]["tables"]
                for col in t["columns"]
            ])
            self.assertNotIn("id", [
                col["name"] for t in report["target_preview"]["tables"]
                for col in t["columns"]
            ])
        finally: engine.dispose()

    def test_stale_ale_version_is_fail_closed(self):
        engine,md=_fake_db("neo000000026")
        try:
            with engine.connect() as c:
                result=svc.inspect_cabinet_schema_read_only(c,md)
            self.assertFalse(result["physical_subset_checked"])
            self.assertIsNone(result["target_preview"])
            self.assertIn("PHYSICAL_SCHEMA_OR_ALEMBIC_HEAD_MISMATCH", result["blockers"])
        finally:engine.dispose()

    def test_missing_version_table_is_fail_closed(self):
        engine,md=_fake_db(None)
        try:
            with engine.connect() as c:
                result=svc.inspect_cabinet_schema_read_only(c,md)
            self.assertFalse(result["schema_revision_matches"])
            self.assertFalse(result["physical_subset_checked"])
        finally: engine.dispose()

    def test_read_only_service_emits_no_insert_update_delete_or_ddl(self):
        engine,md=_fake_db()
        statements=[]
        @event.listens_for(engine,"before_cursor_execute")
        def note(_c,_cur,sql,_param,_ctx,_many):
            statements.append(sql.strip().upper())
        try:
            with engine.connect() as c:
                report=svc.inspect_cabinet_schema_read_only(c,md)
            self.assertTrue(report["physical_subset_checked"])
            self.assertTrue(statements)
            self.assertFalse(any(
                s.startswith(("INSERT ","DELETE ","UPDATE ","CREATE ","DROP ","ALTER "))
                for s in statements
            ))
        finally:engine.dispose()

    def test_declared_drift_returns_not_ready(self):
        engine,md=_fake_db()
        try:
            cloned=MetaData()
            for t in md.tables.values():
                t.to_metadata(cloned)
            # Mutate only the declared nullability, not the physical schema.
            cloned.tables["patients"].c.nom.nullable = True
            with engine.connect() as c:
                response=svc.inspect_cabinet_schema_read_only(c,cloned)
            self.assertFalse(response["declared_subset_matches"])
            self.assertFalse(response["physical_subset_checked"])
        finally:engine.dispose()


class RealSyntheticServerRehearsalTests(unittest.TestCase):
    def test_fixed_100_patients_200_rdv_all_correct_and_rolled_back(self):
        result=svc.run_fixed_synthetic_rehearsal(_real_declared_model_only())
        self.assertEqual(
            (result.source_patients,result.source_appointments,
             result.verified_patients,result.verified_appointments,
             result.verified_patient_links,result.orphan_appointments,
             result.cross_tenant_links,result.after_rollback_patients,
             result.after_rollback_appointments),
            (100,200,100,200,200,0,0,0,0),
        )
        self.assertFalse(result.cabinet_rows_read)
        self.assertFalse(result.cabinet_rows_written)
        self.assertFalse(result.schema_migrated_by_alembic)
        self.assertFalse(result.import_permitted)

    def test_missing_required_declared_table_denied(self):
        with self.assertRaisesRegex(svc.MigrationPreflightRefused, "DECLARED_TABLE_MISSING"):
            svc.run_fixed_synthetic_rehearsal(MetaData())


class WiringStaticSafetyContracts(unittest.TestCase):
    def test_router_owner_dependency_and_true_get_current_user_workstation(self):
        router=(BACKEND/"routers"/"legacy_migration_v15.py").read_text()
        auth=(BACKEND/"routers"/"auth.py").read_text()
        self.assertIn('require_permission("settings")',router)
        self.assertIn("require_cabinet_owner(principal)",router)
        self.assertIn("enforce_authenticated_workstation_access(",auth)
        self.assertIn('detail="BODY_NOT_ALLOWED"',router)
        self.assertNotIn("db.commit(",router)
        tree=ast.parse(router)
        paths={d.args[0].value for n in ast.walk(tree)
               if isinstance(n,ast.FunctionDef) or isinstance(n,ast.AsyncFunctionDef)
               for d in n.decorator_list
               if isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute)
               and d.args and isinstance(d.args[0],ast.Constant)}
        self.assertEqual(paths,{"/preflight","/synthetic-rehearsal"})

    def test_main_mounts_owner_gated_api_and_not_mobile(self):
        main=(BACKEND/"main.py").read_text()
        self.assertIn('prefix="/api/migration"',main)
        self.assertIn("legacy_migration_router.router",main)
        self.assertNotIn('prefix="/api/mobile/migration"',main)


if __name__=="__main__":
    unittest.main()

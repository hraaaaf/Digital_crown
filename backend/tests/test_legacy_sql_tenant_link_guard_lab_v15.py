"""LOT05-A TEST-ONLY tenant link authority boundary; not a backend import API.

A self-contained fixture tests denial by default and server-derived tenant.
No real principal/auth, production DB, secrets or import permissions.
"""
from __future__ import annotations
from dataclasses import dataclass
import unittest

from sqlalchemy import select, func

from test_legacy_sql_real_orm_scratch_v15 import (
    _physical_scratch, _owner_row, _patient_row, _OWNER, _OTHER_OWNER
)


class TenantLinkRefused(ValueError):
    pass


@dataclass(frozen=True)
class SyntheticPrincipal:
    user_id: int
    cabinet_id: int
    role: str
    authenticated: bool


def guarded_lab_appointment(md, con, *, principal, patient_id, appointment_time, client_values=None):
    """Server-like boundary, but principal is ONLY A SYNTHETIC TEST STUB."""
    if not isinstance(principal, SyntheticPrincipal) or not principal.authenticated:
        raise TenantLinkRefused("AUTHENTICATED_SERVER_PRINCIPAL_REQUIRED")
    if type(principal.cabinet_id) is not int or principal.cabinet_id < 1:
        raise TenantLinkRefused("VALID_SERVER_CABINET_REQUIRED")
    if principal.role not in ("ADMIN", "DENTISTE"):
        raise TenantLinkRefused("EXPLICIT_IMPORT_ROLE_REQUIRED")
    if type(patient_id) is not int or patient_id < 1:
        raise TenantLinkRefused("VALID_PATIENT_KEY_REQUIRED")
    if client_values is not None and (
        not isinstance(client_values, dict) or
        any(k in client_values for k in ("employer_id", "patient_id", "id", "praticien_id", "role"))
    ):
        raise TenantLinkRefused("UNTRUSTED_TENANT_OR_ID_OVERRIDE")
    patients = md.tables["patients"]
    owner = con.execute(
        select(patients.c.employer_id)
        .where(patients.c.id == patient_id, patients.c.deleted_at.is_(None))
    ).scalar_one_or_none()
    if owner != principal.cabinet_id:
        # Do not distinguish unknown patient from forbidden foreign patient.
        raise TenantLinkRefused("PATIENT_NOT_ACCESSIBLE_FOR_IMPORT")
    if appointment_time is None:
        raise TenantLinkRefused("EXPLICIT_APPOINTMENT_TIME_REQUIRED")
    values = {"employer_id": principal.cabinet_id, "patient_id": patient_id,
              "datetime_start": appointment_time, "status": "PREVU"}
    if client_values:
        if set(client_values) - {"motif", "duration_minutes"}:
            raise TenantLinkRefused("UNREVIEWED_APPOINTMENT_FIELDS")
        values.update(client_values)
    return con.execute(md.tables["appointments"].insert().values(**values)).inserted_primary_key[0]


class SyntheticTenantLinkTests(unittest.TestCase):
    def _setup(self, md, con):
        con.execute(md.tables["users"].insert(), [_owner_row(_OWNER), _owner_row(_OTHER_OWNER)])
        p = md.tables["patients"]
        a = con.execute(p.insert().values(**_patient_row(owner=_OWNER, number="LAB-A"))).inserted_primary_key[0]
        b = con.execute(p.insert().values(**_patient_row(owner=_OTHER_OWNER, number="LAB-B"))).inserted_primary_key[0]
        return a, b

    def _principal(self, cabinet=_OWNER, role="ADMIN", auth=True):
        return SyntheticPrincipal(777, cabinet, role, auth)

    def test_01_owner_can_link_only_own_patient_and_rolls_back(self):
        with _physical_scratch() as (md, con):
            own, _ = self._setup(md, con)
            from datetime import datetime
            new_id=guarded_lab_appointment(md, con, principal=self._principal(),
                patient_id=own, appointment_time=datetime(2026,10,14,11,0))
            self.assertIsInstance(new_id, int)
            self.assertEqual(con.execute(select(func.count()).select_from(md.tables["appointments"])).scalar_one(), 1)

    def test_02_cross_cabinet_link_denied_even_when_sql_fk_would_allow(self):
        with _physical_scratch() as (md, con):
            own, other = self._setup(md, con)
            from datetime import datetime
            with self.assertRaisesRegex(TenantLinkRefused, "PATIENT_NOT_ACCESSIBLE_FOR_IMPORT"):
                guarded_lab_appointment(md, con, principal=self._principal(), patient_id=other,
                                        appointment_time=datetime(2026,10,14,11,0))
            self.assertEqual(con.execute(select(func.count()).select_from(md.tables["appointments"])).scalar_one(), 0)

    def test_03_client_tenant_override_denied(self):
        with _physical_scratch() as (md, con):
            own, _ = self._setup(md, con)
            from datetime import datetime
            with self.assertRaisesRegex(TenantLinkRefused, "UNTRUSTED_TENANT_OR_ID_OVERRIDE"):
                guarded_lab_appointment(md, con, principal=self._principal(), patient_id=own,
                    appointment_time=datetime(2026,10,14), client_values={"employer_id":_OTHER_OWNER})

    def test_04_unauthenticated_principal_denied(self):
        with _physical_scratch() as (md, con):
            own,_=self._setup(md, con)
            from datetime import datetime
            with self.assertRaisesRegex(TenantLinkRefused, "AUTHENTICATED_SERVER_PRINCIPAL_REQUIRED"):
                guarded_lab_appointment(md, con, principal=self._principal(auth=False), patient_id=own,
                    appointment_time=datetime(2026,10,14))

    def test_05_secretary_and_unreviewed_fields_denied(self):
        with _physical_scratch() as (md, con):
            own,_=self._setup(md, con)
            from datetime import datetime
            with self.assertRaisesRegex(TenantLinkRefused, "EXPLICIT_IMPORT_ROLE_REQUIRED"):
                guarded_lab_appointment(md, con, principal=self._principal(role="SECRETAIRE"),
                    patient_id=own, appointment_time=datetime(2026,10,14))
            with self.assertRaisesRegex(TenantLinkRefused, "UNREVIEWED_APPOINTMENT_FIELDS"):
                guarded_lab_appointment(md, con, principal=self._principal(),
                    patient_id=own, appointment_time=datetime(2026,10,14), client_values={"source":"legacy"})

    def test_06_missing_patient_does_not_disclose_tenant(self):
        with _physical_scratch() as (md, con):
            self._setup(md, con)
            from datetime import datetime
            with self.assertRaisesRegex(TenantLinkRefused, "PATIENT_NOT_ACCESSIBLE_FOR_IMPORT"):
                guarded_lab_appointment(md, con, principal=self._principal(),
                    patient_id=999999, appointment_time=datetime(2026,10,14))

    def test_07_foreign_patient_owner_can_link(self):
        with _physical_scratch() as (md, con):
            _, other = self._setup(md, con)
            from datetime import datetime
            guarded_lab_appointment(md, con, principal=self._principal(cabinet=_OTHER_OWNER),
                patient_id=other, appointment_time=datetime(2026,10,14))
            self.assertEqual(con.execute(select(func.count()).select_from(md.tables["appointments"])).scalar_one(), 1)

if __name__ == "__main__":
    unittest.main()

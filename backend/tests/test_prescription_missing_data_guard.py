from datetime import date

from backend.services.prescription_context_guard import (
    build_prescription_context,
    calculate_age,
    non_evaluable_plan,
)
from backend.services.prescription_service import prescription_service
from backend.services.prescription_agentic_service import prescription_agentic


class _Patient:
    id = 1
    date_naissance = date(2018, 1, 1)
    antecedents_medicaux = "RAS renseigné"


class _Query:
    def __init__(self, patient):
        self.patient = patient

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.patient


class _Db:
    def __init__(self, patient):
        self.patient = patient

    def query(self, *args, **kwargs):
        return _Query(self.patient)


def test_missing_birth_date_stays_unknown():
    assert calculate_age(None) is None


def test_child_without_structured_weight_is_not_evaluable():
    context = build_prescription_context(_Patient())
    assert context.age is not None and context.age < 15
    assert context.weight_kg is None
    assert context.status == "non_evaluable"
    assert "weight_kg" in context.missing_fields


def test_missing_history_is_explicitly_incomplete():
    patient = _Patient()
    patient.antecedents_medicaux = None
    context = build_prescription_context(patient)
    assert context.status == "non_evaluable"
    assert "antecedents" in context.missing_fields


def test_non_evaluable_plan_contains_no_automatic_rows():
    context = build_prescription_context(_Patient())
    plan = non_evaluable_plan(context, "DEFAULT")
    assert plan["evaluation"]["status"] == "non_evaluable"
    assert plan["drugs"] == []
    assert plan["patient_context"]["weight"] is None


def test_runtime_service_fails_closed_before_legacy_engine():
    plan = prescription_service.resolve_smart_prescription(_Db(_Patient()), 1, ["test"], doctor_id=1)
    assert plan["evaluation"]["status"] == "non_evaluable"
    assert plan["drugs"] == []
    assert plan["patient_context"]["weight"] is None


def test_agentic_design_keeps_non_evaluable_plan_empty():
    result = prescription_agentic.design_treatment_plan(
        {"evaluation": {"status": "non_evaluable"}, "drugs": [{"name": "ignored"}]},
        {"id": 1},
    )
    assert result["prescriptions"] == []
    assert result["evaluation"]["status"] == "non_evaluable"

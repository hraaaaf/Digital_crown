"""Reachability and authentication contracts for landmark refinement audit."""
from types import SimpleNamespace

from backend.routers import ia
from backend.routers import cephalo_landmark_refinement as route_module


class _Query:
    def __init__(self, result):
        self.result = result

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.result


class _DB:
    def __init__(self, analysis):
        self.analysis = analysis

    def query(self, _model):
        return _Query(self.analysis)


def test_exactly_one_cephalo_refinement_put_is_registered():
    routes = [
        route
        for route in ia.router.routes
        if getattr(route, "path", None) == "/analyses/{analysis_id}"
        and "PUT" in (getattr(route, "methods", set()) or set())
    ]
    assert len(routes) == 1
    assert routes[0].endpoint.__name__ == "update_analysis_with_landmark_audit"


def test_refinement_route_uses_authenticated_user_as_clinician(monkeypatch):
    analysis = SimpleNamespace(id=42, patient_id=7)
    db = _DB(analysis)
    user = SimpleNamespace(id=123)
    req = SimpleNamespace(
        landmarks=[SimpleNamespace(id="S", x=1.0, y=2.0)],
        clinical_data=None,
        ai_diagnostic={"author": "doctor"},
        mm_per_pixel=None,
        mcnamara_projections=None,
    )
    seen = {}

    class _Service:
        def __init__(self, received_db):
            assert received_db is db

        def refine_analysis(self, **kwargs):
            seen.update(kwargs)
            return {"status": "success"}

    def _access(patient_id, current_user, received_db):
        seen["access"] = (patient_id, current_user.id, received_db)

    monkeypatch.setattr(route_module, "CephaloService", _Service)
    monkeypatch.setattr(route_module, "assert_patient_access", _access)

    response = route_module.update_analysis_with_landmark_audit(
        analysis_id=42,
        req=req,
        db=db,
        current_user=user,
    )

    assert response == {"status": "success"}
    assert seen["clinician_id"] == "123"
    assert seen["analysis_id"] == 42
    assert seen["access"] == (7, 123, db)

import sys
import types
from unittest.mock import MagicMock

from backend.services.accounting_service import AccountingService


def test_learning_ignores_blank_and_phase_presentation_rows():
    service = AccountingService()
    db = MagicMock()

    service.record_act_usage(db, doctor_id=7, act_name="   ", price=0)
    service.record_act_usage(db, doctor_id=7, act_name="--- PHASE 1 : ASSAINISSEMENT ---", price=0)

    db.query.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.rollback.assert_not_called()


def test_learning_keeps_real_act_path(monkeypatch):
    service = AccountingService()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    fake_habits_module = types.ModuleType("backend.services.habits_engine")
    fake_habits_module.habits_engine = object()
    monkeypatch.setitem(sys.modules, "backend.services.habits_engine", fake_habits_module)

    service.record_act_usage(db, doctor_id=7, act_name="  Composite 2 faces  ", price=700, category="CONSERVATRICE")

    db.query.assert_called_once()
    db.add.assert_called_once()
    learned = db.add.call_args.args[0]
    assert learned.act_name == "Composite 2 faces"
    assert learned.base_price == 700
    assert learned.category == "CONSERVATRICE"
    assert learned.usage_count == 1
    db.commit.assert_called_once()
    db.rollback.assert_not_called()

from pathlib import Path


def test_a4_migration_is_additive_and_nullable():
    text = Path("alembic/versions/a4rs0000004_add_agenda_resources.py").read_text(encoding="utf-8")
    assert 'down_revision: Union[str, None] = "a3pa0000003"' in text
    assert '"agenda_resources"' in text
    assert 'sa.Column("resource_id", sa.Integer(), nullable=True)' in text
    assert 'ondelete="SET NULL"' in text


def test_a4_appointment_contract_exposes_optional_resource():
    text = Path("backend/schemas/appointments.py").read_text(encoding="utf-8")
    assert text.count("resource_id: Optional[int] = None") >= 3
    model = Path("backend/models.py").read_text(encoding="utf-8")
    assert 'ForeignKey("agenda_resources.id", ondelete="SET NULL")' in model


def test_a4_resource_router_is_mounted_directly():
    router = Path("backend/routers/agenda_resources.py").read_text(encoding="utf-8")
    main = Path("backend/main.py").read_text(encoding="utf-8")
    assert 'APIRouter(prefix="/resources"' in router
    assert 'app.include_router(agenda_resources.router, prefix="/api/agenda"' in main


def test_a4_capacity_wiring():
    text = Path("backend/routers/appointments.py").read_text(encoding="utf-8")
    assert "assert_resource_available" in text
    assert "resource_conflict_id" in text
    assert "Conflit de ressource interne au lot" in text

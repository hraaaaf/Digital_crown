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


def test_a4_resource_router_is_child_of_existing_agenda_prefix():
    text = Path("backend/routers/agenda_resources.py").read_text(encoding="utf-8")
    assert 'APIRouter(prefix="/resources"' in text
    installer = Path("backend/routers/agenda_a4_install.py").read_text(encoding="utf-8")
    assert "agenda_router.include_router(agenda_resources.router)" in installer

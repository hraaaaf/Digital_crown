from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import models
from backend.routers.clinics import check_init_status


def _session():
    engine = create_engine('sqlite:///:memory:')
    models.Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _owner(db, email: str, name: str):
    user = models.User(
        email=email,
        hashed_password='test-hash',
        role=models.UserRole.DENTISTE,
        nom_complet=name,
    )
    db.add(user)
    db.flush()
    return user


def test_init_status_uses_only_authenticated_cabinet():
    db = _session()
    try:
        owner_a = _owner(db, 'a@example.com', 'Cabinet A')
        owner_b = _owner(db, 'b@example.com', 'Cabinet B')
        db.add_all([
            models.CabinetConfig(
                owner_id=owner_a.id,
                nom_cabinet='Cabinet A',
                nom_praticien='Dr A',
                is_initialized=True,
            ),
            models.CabinetConfig(
                owner_id=owner_b.id,
                nom_cabinet='Cabinet B',
                nom_praticien='Dr B',
                is_initialized=False,
            ),
        ])
        db.commit()

        result = check_init_status(db=db, current_user=owner_b)

        assert result == {'is_initialized': False, 'needs_setup': True}
        config_a = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == owner_a.id).one()
        assert config_a.is_initialized is True
    finally:
        db.close()


def test_missing_current_cabinet_config_is_read_only():
    db = _session()
    try:
        owner_a = _owner(db, 'a2@example.com', 'Cabinet A')
        owner_b = _owner(db, 'b2@example.com', 'Cabinet B')
        db.add(models.CabinetConfig(
            owner_id=owner_a.id,
            nom_cabinet='Cabinet A',
            nom_praticien='Dr A',
            is_initialized=True,
        ))
        db.commit()
        before = db.query(models.CabinetConfig).count()

        result = check_init_status(db=db, current_user=owner_b)

        assert result == {'is_initialized': False, 'needs_setup': True}
        assert db.query(models.CabinetConfig).count() == before
        assert db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == owner_b.id).first() is None
    finally:
        db.close()

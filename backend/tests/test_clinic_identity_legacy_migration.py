"""P5 legacy identity migration: conservative, conflict-aware and idempotent."""
from backend import models
from backend.services.clinic_identity_legacy_migration import migrate_legacy_identity_values
from backend.security import get_password_hash


def _owner(db, email: str, *, name=None, name_ar=None, legal=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role=models.UserRole.DENTISTE,
        nom_complet=name,
        identifiants_legaux=legal,
        is_active=True,
        is_licensed=True,
    )
    user.nom_complet_ar = name_ar
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _cabinet(db, owner, *, legacy_fr="", legacy_ar=""):
    cabinet = models.CabinetConfig(
        owner_id=owner.id,
        nom_cabinet="Cabinet Legacy",
        nom_praticien=legacy_fr,
        nom_praticien_ar=legacy_ar,
        inpe="LEGACY-INPE-AMBIGUOUS",
        ice="",
        if_="",
        header_lines_fr=["HEADER FR CUSTOM"],
        header_lines_ar=["HEADER AR CUSTOM"],
        header_customized=True,
        contacts_json={"fixe": {"enabled": True, "value": "0537000000"}},
        footer_phones="📞 05 37 00 00 00",
        is_initialized=True,
    )
    db.add(cabinet)
    db.commit()
    db.refresh(cabinet)
    return cabinet


def test_backfills_only_empty_canonical_practitioner_fields(db):
    owner = _owner(db, "p5-empty@test.ma", name="", name_ar="")
    cabinet = _cabinet(db, owner, legacy_fr="Dr Legacy", legacy_ar="د. قديم")

    report = migrate_legacy_identity_values(db)
    db.refresh(owner)
    db.refresh(cabinet)

    assert owner.nom_complet == "Dr Legacy"
    assert owner.nom_complet_ar == "د. قديم"
    assert report.practitioner_fr_backfilled == 1
    assert report.practitioner_ar_backfilled == 1

    # Legacy values stay byte-for-byte available for compatibility/rollback.
    assert cabinet.nom_praticien == "Dr Legacy"
    assert cabinet.nom_praticien_ar == "د. قديم"
    assert cabinet.inpe == "LEGACY-INPE-AMBIGUOUS"
    assert cabinet.inpe_etablissement is None
    assert owner.inpe_professionnel is None
    assert cabinet.header_lines_fr == ["HEADER FR CUSTOM"]
    assert cabinet.header_lines_ar == ["HEADER AR CUSTOM"]
    assert cabinet.header_customized is True
    assert cabinet.contacts_json == {"fixe": {"enabled": True, "value": "0537000000"}}
    assert cabinet.footer_phones == "📞 05 37 00 00 00"


def test_conflicts_are_reported_and_never_overwritten(db):
    owner = _owner(db, "p5-conflict@test.ma", name="Dr Canonical", name_ar="د. قانوني")
    cabinet = _cabinet(db, owner, legacy_fr="Dr Legacy", legacy_ar="د. قديم")

    report = migrate_legacy_identity_values(db)
    db.refresh(owner)

    assert owner.nom_complet == "Dr Canonical"
    assert owner.nom_complet_ar == "د. قانوني"
    assert report.practitioner_fr_backfilled == 0
    assert report.practitioner_ar_backfilled == 0
    assert report.practitioner_fr_conflicts == 1
    assert report.practitioner_ar_conflicts == 1
    assert cabinet.nom_praticien == "Dr Legacy"


def test_legacy_legal_json_and_ambiguous_inpe_are_never_reclassified(db):
    owner = _owner(
        db,
        "p5-legal@test.ma",
        name="Dr Stable",
        legal={"ice": "ICE-LEGACY", "if": "IF-LEGACY", "inpe": "INPE-LEGACY"},
    )
    cabinet = _cabinet(db, owner)

    migrate_legacy_identity_values(db)
    db.refresh(owner)
    db.refresh(cabinet)

    assert cabinet.ice == ""
    assert cabinet.if_ == ""
    assert cabinet.inpe == "LEGACY-INPE-AMBIGUOUS"
    assert cabinet.inpe_etablissement is None
    assert owner.inpe_professionnel is None
    assert owner.identifiants_legaux == {
        "ice": "ICE-LEGACY",
        "if": "IF-LEGACY",
        "inpe": "INPE-LEGACY",
    }


def test_migration_is_idempotent(db):
    owner = _owner(db, "p5-idempotent@test.ma", name=None, name_ar=None)
    _cabinet(db, owner, legacy_fr="Dr Once", legacy_ar="د. مرة")

    first = migrate_legacy_identity_values(db)
    second = migrate_legacy_identity_values(db)

    assert first.changed == 2
    assert second.changed == 0
    assert second.practitioner_fr_conflicts == 0
    assert second.practitioner_ar_conflicts == 0

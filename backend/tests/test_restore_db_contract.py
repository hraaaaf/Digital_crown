from pathlib import Path

from backend.scripts.backup_db import _parse_postgres_url


def test_postgres_url_parser_preserves_port_and_decodes_credentials():
    user, password, host, port, dbname = _parse_postgres_url(
        "postgresql://cabinet%40owner:p%40ss%3Aword@127.0.0.1:5544/digital%2Dcrown"
    )

    assert user == "cabinet@owner"
    assert password == "p@ss:word"
    assert host == "127.0.0.1"
    assert port == "5544"
    assert dbname == "digital-crown"


def test_restore_reuses_canonical_parser_and_psql_port_contract():
    source = (
        Path(__file__).resolve().parents[1] / "scripts" / "restore_db.py"
    ).read_text(encoding="utf-8")

    assert "_parse_postgres_url(db_url)" in source
    assert 'psql_cmd += ["-p", port]' in source
    assert 'auth_part, host_part = db_url.replace' not in source

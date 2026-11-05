from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_restore_entrypoints_fail_closed():
    for filename, marker in [('guided_restore.py', 'def request_apply('), ('guided_restore_worker.py', 'def run(')]:
        source = (ROOT / 'backend' / 'services' / filename).read_text(encoding='utf-8')
        method = source.split(marker, 1)[1]
        assert 'raise RuntimeError("Migration clinique bloquée : autorité worker non attestée")' in method.split('\n', 15)[0:15].__str__()

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
sys.path.insert(0, str(Path(__file__).parent))
from smart_gate_v2 import inventory, on_section, path_patterns, event_section

class SmartGateV2Tests(unittest.TestCase):
    def test_parses_event_and_paths(self):
        src = "name: Example\non:\n  pull_request:\n    paths:\n      - 'backend/main.py'\n  workflow_dispatch:\njobs:\n  check:\n    runs-on: ubuntu-latest\n"
        on = on_section(src)
        self.assertEqual(path_patterns(event_section(on, 'pull_request')), ['backend/main.py'])
    def test_candidate_and_non_candidate(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'a.yml').write_text('name: A\non:\n  pull_request:\n    paths:\n      - backend/main.py\njobs:\n  test:\n    runs-on: ubuntu-latest\n')
            (p / 'b.yml').write_text('name: B\non:\n  pull_request:\n    paths:\n      - frontend/**\nconcurrency:\n  group: test\n')
            result = inventory(p, ['backend/main.py'], 'master')
            self.assertEqual(result['workflow_count'], 2)
            self.assertEqual(result['pr_candidate_count'], 1)
            self.assertEqual(result['pr_candidates_without_root_concurrency'], 1)
    def test_manual_only_not_candidate(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'a.yml').write_text('name: Manual\non:\n  workflow_dispatch:\njobs:\n  test:\n    runs-on: ubuntu-latest\n')
            self.assertEqual(inventory(p, ['backend/main.py'], 'master')['pr_candidate_count'], 0)

if __name__ == '__main__':
    unittest.main()

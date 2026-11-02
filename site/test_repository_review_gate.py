import contextlib
import copy
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import repository_review_promotions as gate


class ReviewGateTests(unittest.TestCase):
    def test_check_detects_promoted_profile_drift_without_rewriting_sources(self):
        original = json.loads(gate.LANDSCAPE.read_text(encoding='utf-8'))
        manifest = json.loads(gate.MANIFEST.read_text(encoding='utf-8'))
        for drift in (False, True):
            data = copy.deepcopy(original)
            if drift:
                target_id = manifest['reviews'][0]['repository_id']
                row = next(item for item in data['repositories'] if item['id'] == target_id)
                key = next(iter(row['mechanisms']))
                row['mechanisms'][key] = 'U' if row['mechanisms'][key] != 'U' else 'V'
            with self.subTest(drift=drift), TemporaryDirectory() as directory:
                target = Path(directory) / 'landscape.json'
                target.write_text(json.dumps(data), encoding='utf-8')
                before = target.read_bytes()
                with patch.object(gate, 'LANDSCAPE', target), patch.object(sys, 'argv', ['gate', '--check']), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(1 if drift else 0, gate.main())
                self.assertEqual(before, target.read_bytes())


if __name__ == '__main__':
    unittest.main()

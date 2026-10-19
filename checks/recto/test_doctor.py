"""Run with: python3 -m unittest discover -s checks/recto -p 'test_*.py'."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'skills/recto/scripts'))
from doctor import FONT_DIR, select_fonts


class RuntimeTests(unittest.TestCase):
    def test_missing_tools_returns_actionable_report(self):
        result = subprocess.run([sys.executable, str(ROOT / 'skills/recto/scripts/doctor.py')],
                                env=dict(os.environ, PATH=''), capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertFalse(report['ready'])
        self.assertIn('pandoc not found on PATH', report['issues'])
        self.assertIn('typst not found on PATH', report['issues'])
        self.assertTrue(Path(report['setup']).is_file())

    def test_original_font_wins_and_missing_bundle_fails(self):
        available = {'Songti SC', 'Times New Roman', 'FandolSong', 'Liberation Serif',
                     'New Computer Modern Math', 'Cambria Math'}
        fonts, replacements = select_fonts('reference', available)
        self.assertEqual(fonts['body'], 'Songti SC')
        self.assertEqual(replacements, {})
        available.remove('Songti SC')
        fonts, replacements = select_fonts('reference', available)
        self.assertEqual(fonts['body'], 'FandolSong')
        self.assertEqual(replacements['Songti SC'], 'FandolSong')
        available.remove('FandolSong')
        with self.assertRaisesRegex(ValueError, 'FandolSong'):
            select_fonts('reference', available)

    def test_font_files_and_licenses_match_recorded_bytes(self):
        for path, digest in json.loads((FONT_DIR / 'SHA256SUMS.json').read_text()).items():
            with self.subTest(path=path):
                self.assertEqual(sha256((FONT_DIR / path).read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()

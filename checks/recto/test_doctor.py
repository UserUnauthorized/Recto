"""Run with: python3 -m unittest discover -s checks/recto -p 'test_*.py'."""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory

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
        self.assertIn('lualatex not found on PATH', report['issues'])
        self.assertIn('latexmk not found on PATH', report['issues'])
        self.assertIn('kpsewhich not found on PATH', report['issues'])
        self.assertTrue(Path(report['setup']).is_file())

    def test_word_and_tex_exports_require_only_pandoc_on_path(self):
        actual_pandoc = shutil.which('pandoc')
        self.assertIsNotNone(actual_pandoc, 'Pandoc is required for this suite')
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            bin_dir = directory / 'bin'
            bin_dir.mkdir()
            (bin_dir / 'pandoc').symlink_to(actual_pandoc)
            environment = dict(os.environ, PATH=str(bin_dir))
            for format_name in ('docx', 'tex'):
                with self.subTest(format=format_name):
                    output = directory / format_name
                    result = subprocess.run(
                        [sys.executable, str(ROOT / 'skills/recto/scripts/doctor.py'),
                         '--formats', format_name, '--bundled-fonts'],
                        env=environment, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    report = json.loads(result.stdout)
                    self.assertTrue(report['ready'], report)
                    self.assertEqual(set(report['versions']), {'pandoc'})
                    self.assertEqual(report['fonts']['body'], 'FandolSong')
                    self.assertEqual(report['substitutions']['Songti SC'], 'FandolSong')
                    if format_name == 'docx':
                        self.assertIn('not detected among system fonts', report['word_font_note'])
                        self.assertIn('not embedded in DOCX', report['word_font_note'])
                    else:
                        self.assertIsNone(report['word_font_note'])
                    export = subprocess.run(
                        [sys.executable, str(ROOT / 'skills/recto/scripts/export.py'),
                         str(ROOT / 'skills/recto/assets/examples/reference.md'), '--style', 'reference',
                         '--formats', format_name, '--bundled-fonts', '--output', str(output)],
                        env=environment, capture_output=True, text=True)
                    self.assertEqual(export.returncode, 0, export.stdout + export.stderr)
                    expected = 'document.docx' if format_name == 'docx' else 'latex/document.tex'
                    self.assertTrue((output / expected).is_file())
                    self.assertFalse((output / 'document.pdf').exists())
                    if format_name == 'docx':
                        self.assertEqual(json.loads(export.stdout)['native_word_math_count'], 66)
                        self.assertFalse((output / 'latex').exists())

    def test_original_font_wins_and_missing_bundle_fails(self):
        available = {'Songti SC', 'Times New Roman', 'FandolSong', 'Liberation Serif',
                     'New Computer Modern Math', 'Cambria Math', 'Liberation Mono', 'FandolFang R'}
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

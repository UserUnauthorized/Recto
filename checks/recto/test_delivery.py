"""Exercise the public exporter and the delivered files, without mocked converters."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
EXPORT = ROOT / 'skills/recto/scripts/export.py'
SOURCE = ROOT / 'skills/recto/assets/examples/reference.md'


class DeliveryTests(unittest.TestCase):
    def test_only_requested_formats_and_relocatable_typst(self):
        for formats in ('typ,pdf', 'pdf', 'docx'):
            with self.subTest(formats=formats), tempfile.TemporaryDirectory() as temporary:
                out = Path(temporary) / 'delivery'
                result = subprocess.run(
                    [sys.executable, str(EXPORT), str(SOURCE), '--formats', formats, '--output', str(out)],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                expected = {'content.md', 'media'}
                if 'typ' in formats:
                    expected.add('typst')
                expected.update('document.' + f for f in formats.split(',') if f != 'typ')
                self.assertEqual({p.name for p in out.iterdir()}, expected)
                self.assertEqual(len(list((out / 'media').iterdir())), 1)
                if 'typ' in formats:
                    moved = out.with_name('moved delivery')
                    out.rename(moved)
                    subprocess.run(
                        ['typst', 'compile', '--root', str(moved), '--font-path', str(moved / 'typst/fonts'),
                         str(moved / 'typst/document.typ'), str(Path(temporary) / 'rebuilt.pdf')],
                        check=True, capture_output=True,
                    )
                    self.assertTrue((Path(temporary) / 'rebuilt.pdf').read_bytes().startswith(b'%PDF-'))
                    if not any(f.startswith('Fandol') for f in report['fonts'].values()):
                        self.assertFalse((moved / 'typst/fonts/fandol').exists())
                    subprocess.run(
                        [sys.executable, str(EXPORT), str(moved / 'content.md'), '--output', str(moved)],
                        check=True, capture_output=True,
                    )
                    self.assertEqual({p.name for p in moved.iterdir()}, expected)
                    self.assertEqual(len(list((moved / 'media').iterdir())), 1)
                if formats == 'docx':
                    self.assertGreater(report['native_word_math_count'], 0)


if __name__ == '__main__':
    unittest.main()

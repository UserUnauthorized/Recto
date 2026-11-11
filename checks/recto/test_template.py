"""Verify real exports, then reject changed templates, inputs, and deliveries."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
EXPORT = ROOT / 'skills/recto/scripts/export.py'


class TemplateTests(unittest.TestCase):
    def test_user_templates_cannot_override_official_styles(self):
        overrides = '\\geometry{left=50mm,right=50mm}\n\\setmathfont{Latin Modern Math}\n'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source.md'
            source.write_text('正文 $x^2$。')
            data = root / 'data'
            templates = data / 'pandoc/templates'
            templates.mkdir(parents=True)
            original = subprocess.run(['pandoc', '-D', 'latex'], check=True,
                                      capture_output=True, text=True, timeout=30).stdout
            (templates / 'default.latex').write_text(
                original.replace(r'\begin{document}', overrides + r'\begin{document}'))
            environment = dict(os.environ, XDG_DATA_HOME=str(data), APPDATA=str(data))
            for style in ('reference', 'gbt9704'):
                with self.subTest(style=style):
                    out = root / style
                    command = [sys.executable, str(EXPORT), str(source), '--style', style,
                               '--formats', 'tex', '--bundled-fonts', '--output', str(out)]
                    exported = subprocess.run(command, env=environment, capture_output=True,
                                              text=True, timeout=60)
                    self.assertEqual(exported.returncode, 0, exported.stderr)
                    tex = (out / 'latex/document.tex').read_text()
                    self.assertIn('正文', tex)
                    self.assertNotIn(overrides, tex)
                    report = out / 'report.json'
                    report.write_text(exported.stdout)
                    checked = subprocess.run(command + ['--verify-report', str(report)],
                                             env=environment, capture_output=True, text=True, timeout=30)
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    self.assertTrue(json.loads(checked.stdout)['template_verified'])

    def test_missing_official_header_cannot_publish_tex(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source.md'
            source.write_text('正文 $x^2$。')
            out = root / 'delivery'
            (out / 'latex').mkdir(parents=True)
            target = out / 'latex/document.tex'
            target.write_text('previous successful source')
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            converter = bin_dir / 'pandoc'
            # Fault injection: real Pandoc exports normally, but loses the selected header.
            converter.write_text(f'#!{sys.executable}\nimport subprocess,sys\n'
                                 f'command=[{shutil.which("pandoc")!r}]+sys.argv[1:]\n'
                                 'if "-H" in command:\n'
                                 '    index=command.index("-H"); del command[index:index+2]\n'
                                 'raise SystemExit(subprocess.call(command))\n')
            converter.chmod(0o755)
            result = subprocess.run(
                [sys.executable, str(EXPORT), str(source), '--formats', 'tex',
                 '--bundled-fonts', '--output', str(out)],
                env=dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ['PATH']),
                capture_output=True, text=True, timeout=60,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('missing the official style/font header', result.stderr)
            self.assertEqual(target.read_text(), 'previous successful source')

    def test_delivery_verification_binds_template_source_and_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source.md'
            source.write_text('---\ntitle: 版式核对\n---\n\n# 第一节\n\n正文 $x^2$。\n')
            for style in ('reference', 'gbt9704'):
                with self.subTest(style=style):
                    out = root / style
                    report = root / f'{style}.json'
                    command = [sys.executable, str(EXPORT), str(source), '--style', style,
                               '--formats', 'tex,docx', '--bundled-fonts', '--output', str(out)]
                    exported = subprocess.run(command, capture_output=True, text=True, timeout=60)
                    self.assertEqual(exported.returncode, 0, exported.stderr)
                    report.write_text(exported.stdout)
                    # Validation must survive relocation and require no external executables.
                    moved = out.with_name(style + ' moved')
                    out.rename(moved)
                    command[-1] = str(moved)
                    verify = command + ['--verify-report', str(report)]
                    environment = dict(os.environ, PATH='')
                    checked = subprocess.run(verify, env=environment, capture_output=True, text=True)
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    self.assertTrue(json.loads(checked.stdout)['template_verified'])

                    for option, replacement in (('--style', 'gbt9704' if style == 'reference' else 'reference'),
                                                ('--formats', 'tex')):
                        wrong_request = verify.copy()
                        wrong_request[wrong_request.index(option) + 1] = replacement
                        rejected = subprocess.run(wrong_request, env=environment, capture_output=True, text=True)
                        self.assertNotEqual(rejected.returncode, 0)
                        self.assertIn('Requested style, formats or font mode', rejected.stderr)

                    wrong_fonts = [value for value in verify if value != '--bundled-fonts']
                    rejected = subprocess.run(wrong_fonts, env=environment, capture_output=True, text=True)
                    self.assertNotEqual(rejected.returncode, 0)
                    self.assertIn('font mode', rejected.stderr)

                    incomplete = moved / 'latex/document.tex'
                    original = incomplete.read_bytes()
                    incomplete.unlink()
                    rejected = subprocess.run(verify, env=environment, capture_output=True, text=True)
                    self.assertNotEqual(rejected.returncode, 0)
                    self.assertIn('document.tex', rejected.stderr)
                    incomplete.write_bytes(original)

                    for relative in ('latex/document.tex', 'latex/latexmkrc',
                                     'latex/fonts/newcm/NewCMMath-Regular.otf',
                                     'document.docx', 'content.md'):
                        with self.subTest(changed=relative):
                            target = moved / relative
                            original = target.read_bytes()
                            target.write_bytes(original + b'\nchanged after export\n')
                            rejected = subprocess.run(verify, env=environment, capture_output=True, text=True)
                            self.assertNotEqual(rejected.returncode, 0)
                            self.assertIn(relative, rejected.stderr)
                            self.assertEqual(target.read_bytes(), original + b'\nchanged after export\n')
                            target.write_bytes(original)

                    original_source = source.read_text()
                    source.write_text(original_source + '\n新正文。\n')
                    rejected = subprocess.run(verify, env=environment, capture_output=True, text=True)
                    self.assertNotEqual(rejected.returncode, 0)
                    self.assertIn('source', rejected.stderr)
                    source.write_text(original_source)

                    invalid_report = root / 'empty.json'
                    invalid_report.write_text('{}')
                    rejected = subprocess.run(verify[:-1] + [str(invalid_report)],
                                              env=environment, capture_output=True, text=True)
                    self.assertNotEqual(rejected.returncode, 0)
                    self.assertIn('verification', rejected.stderr.lower())

            # A changed installed template must invalidate an otherwise unchanged delivery.
            copied_skill = root / 'recto'
            shutil.copytree(ROOT / 'skills/recto', copied_skill, ignore=shutil.ignore_patterns('__pycache__'))
            template = copied_skill / 'assets/styles/gbt9704.tex'
            template.write_text(template.read_text().replace('top=37mm', 'top=20mm'))
            verify[1] = str(copied_skill / 'scripts/export.py')
            rejected = subprocess.run(verify, env=environment, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('implementation', rejected.stderr)

            # Word-only deliveries have no font copy; validate the installed font bytes too.
            command = [sys.executable, str(copied_skill / 'scripts/export.py'), str(source),
                       '--formats', 'docx', '--bundled-fonts', '--output', str(root / 'word-only')]
            exported = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(exported.returncode, 0, exported.stderr)
            report = root / 'word-only.json'
            report.write_text(exported.stdout)
            font = copied_skill / 'assets/fonts/liberation/LiberationMono-Regular.ttf'
            font.write_bytes(font.read_bytes() + b'changed after export')
            rejected = subprocess.run(command + ['--verify-report', str(report)],
                                      env=environment, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('implementation', rejected.stderr)


if __name__ == '__main__':
    unittest.main()

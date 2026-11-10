"""Exercise the public exporter and the delivered files, without mocked converters."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
EXPORT = ROOT / 'skills/recto/scripts/export.py'
SOURCE = ROOT / 'skills/recto/assets/examples/reference.md'
sys.path.insert(0, str(ROOT / 'skills/recto/scripts'))
from latex import compile_pdf


class DeliveryTests(unittest.TestCase):
    def test_math_commands_cannot_escape_the_shared_source_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            secret = directory / 'synthetic-input.tex'
            secret.write_text('SYNTHETIC REVIEW FIXTURE')
            source = directory / 'source.md'
            out = directory / 'delivery'
            (out / 'latex').mkdir(parents=True)
            previous = ('document.pdf', 'document.docx', 'content.md', 'latex/document.tex')
            for name in previous:
                (out / name).write_bytes(b'previous successful output')
            read_file = r'\text{\input{' + secret.as_posix() + '}}'
            cases = [
                '$' + read_file + '$',
                r'$\text{\%\input{' + secret.as_posix() + '}}$',
                "---\ntitle: '$" + read_file + "$'\n---\n\nBody.",
                r'$\directlua{tex.print(42)}$',
                r'$\csname input\endcsname{' + secret.as_posix() + '}$',
                r'$\^^69nput{' + secret.as_posix() + '}$',
                r'$\begin{filecontents*}{synthetic-output.txt}test\end{filecontents*}$',
                r'$\newcommand{\readfixture}{' + read_file + r'}\readfixture$',
                '$\\in\x00put{x}$',
                '$x\x7f+y$',
            ]
            for content in cases:
                with self.subTest(content=content):
                    source.write_text(content)
                    result = subprocess.run(
                        [sys.executable, str(EXPORT), str(source), '--formats', 'tex',
                         '--bundled-fonts', '--output', str(out)],
                        capture_output=True, text=True, timeout=60,
                    )
                    self.assertNotEqual(result.returncode, 0, 'Unsafe math was delivered as executable TeX')
                    self.assertIn('Unsupported math', result.stderr)
                    for name in previous:
                        self.assertEqual((out / name).read_bytes(), b'previous successful output', name)

    def test_math_notation_comments_and_literal_percent_still_export(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source.md'
            source.write_text(r'''$$
\begin{aligned}
\text{input 50\%} &= \frac{\alpha}{\sqrt{x}}\\ % \input{not-a-file} is a comment
\operatorname{rank}(A)	&=n
\end{aligned}
$$

$$\begin{pmatrix}1&0\\0&1\end{pmatrix},\quad\lim_{x\to0}\frac{\sin x}{x}=1$$
''')
            out = source.parent / 'delivery'
            result = subprocess.run(
                [sys.executable, str(EXPORT), str(source), '--formats', 'tex,pdf,docx',
                 '--bundled-fonts', '--output', str(out)],
                capture_output=True, text=True, timeout=480,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['native_word_math_count'], 2)
            self.assertTrue((out / 'document.pdf').read_bytes().startswith(b'%PDF-'))

    def test_latexmk_settles_a_table_of_contents_that_moves_page_references(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / 'document.tex'
            source.write_text(r'\documentclass{article}\setlength{\textheight}{210pt}'
                              r'\begin{document}\tableofcontents\clearpage'
                              + ''.join(r'\section{Section ' + str(i) + r'}Text. Last page: \pageref{last}. '
                                        for i in range(1, 36))
                              + r'\label{last}\end{document}')
            # A local RC must not replace the selected compiler or execute custom rules.
            (directory / '.latexmkrc').write_text('die "project RC must not execute";')
            pdf = compile_pdf(source, directory)
            self.assertTrue(pdf.read_bytes().startswith(b'%PDF-'))
            log = (directory / '.build/document.log').read_text()
            self.assertNotIn('Rerun to get cross-references right', log)
            self.assertNotIn('undefined references', log)
            self.assertIn(r'\newlabel{last}', (directory / '.build/document.aux').read_text())

    @unittest.skipUnless(shutil.which('rsvg-convert'), 'SVG conversion requires optional librsvg')
    def test_svg_is_a_rebuildable_pdf_resource(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source.md'
            (source.parent / 'figure.svg').write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80">'
                '<rect x="10" y="10" width="100" height="60" fill="black"/></svg>')
            source.write_text('![SVG figure](figure.svg)')
            out = source.parent / 'delivery'
            subprocess.run([sys.executable, str(EXPORT), str(source), '--formats', 'tex,pdf',
                            '--bundled-fonts', '--output', str(out)],
                           check=True, capture_output=True, timeout=300)
            resources = list((out / 'media').glob('*.pdf'))
            self.assertEqual(len(resources), 1)
            self.assertTrue(resources[0].read_bytes().startswith(b'%PDF-'))
            self.assertIn(resources[0].name, (out / 'latex/document.tex').read_text())
            self.assertEqual(len(list((out / 'media').glob('*.svg'))), 1)
            self.assertTrue((out / 'document.pdf').read_bytes().startswith(b'%PDF-'))
            previous = (out / 'document.pdf').read_bytes()
            for svg in (
                '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80">'
                '<image href="child.png" width="120" height="80"/></svg>',
                '<?xml-stylesheet href="foo.css"?><svg xmlns="http://www.w3.org/2000/svg"/>',
            ):
                (source.parent / 'figure.svg').write_text(svg)
                result = subprocess.run([sys.executable, str(EXPORT), str(source), '--formats', 'tex',
                                         '--bundled-fonts', '--output', str(out)], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('self-contained SVG', result.stderr)
                self.assertEqual((out / 'document.pdf').read_bytes(), previous)

    def test_tex_preserves_chinese_cell_endings_and_escapes_appendix_titles(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source.md'
            source.write_text('---\ntitle: "练习"\n---\n\n'
                              '::: {.appendix label="复习" title="练习 & 50%"}\n\n'
                              '| 名称 | 内容 |\n| --- | --- |\n| 课堂练习 | 复习 |\n\n:::')
            out = Path(temporary) / 'delivery'
            subprocess.run([sys.executable, str(EXPORT), str(source), '--style', 'gbt9704',
                            '--formats', 'tex', '--bundled-fonts', '--output', str(out)],
                           check=True, capture_output=True)
            tex = (out / 'latex/document.tex').read_text()
            self.assertIn('课堂练习', tex)
            self.assertIn(r'\rectoappendix{复习}{练习 \& 50\%}', tex)
            self.assertNotIn('\ufffd', tex)

    def test_bad_math_and_oversize_appendix_do_not_replace_previous_pdf(self):
        cases = [
            ('reference', '$$\\rectoUndefinedMath{x}$$', 'Unsupported math command'),
            ('reference', r'$\text{\input{synthetic-input.tex}}$', 'Unsupported math command'),
            ('gbt9704', '::: {.appendix .landscape title="Overflow"}\n\n'
             + '\n\n'.join('这是必须保留的正文。' for _ in range(30)) + '\n\n:::',
             'Landscape appendix exceeds one page'),
        ]
        for style, content, diagnostic in cases:
            with self.subTest(style=style), tempfile.TemporaryDirectory() as temporary:
                source = Path(temporary) / 'source.md'
                source.write_text(content)
                out = Path(temporary) / 'delivery'
                out.mkdir()
                previous = out / 'document.pdf'
                previous.write_bytes(b'previous successful output')
                result = subprocess.run(
                    [sys.executable, str(EXPORT), str(source), '--style', style,
                     '--formats', 'pdf', '--bundled-fonts', '--output', str(out)],
                    capture_output=True, text=True, timeout=300,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(''.join(diagnostic.split()), ''.join(result.stderr.split()))
                self.assertEqual(previous.read_bytes(), b'previous successful output')

    def test_only_requested_formats_and_relocatable_latex(self):
        for formats in ('tex,pdf', 'pdf', 'docx'):
            with self.subTest(formats=formats), tempfile.TemporaryDirectory() as temporary:
                out = Path(temporary) / 'delivery'
                result = subprocess.run(
                    [sys.executable, str(EXPORT), str(SOURCE), '--formats', formats, '--output', str(out)],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                expected = {'content.md', 'media'}
                if 'tex' in formats:
                    expected.add('latex')
                expected.update('document.' + f for f in formats.split(',') if f != 'tex')
                self.assertEqual({p.name for p in out.iterdir()}, expected)
                self.assertEqual(len(list((out / 'media').iterdir())), 1)
                if 'tex' in formats:
                    moved = out.with_name('moved delivery')
                    out.rename(moved)
                    build = Path(temporary) / 'build'
                    build.mkdir()
                    subprocess.run(
                        ['latexmk', '-norc', '-r', 'latex/latexmkrc', '-lualatex', '-interaction=nonstopmode', '-halt-on-error',
                         '-file-line-error', '-outdir=' + str(build), '-latexoption=--no-shell-escape',
                         '-latexoption=--nosocket', 'latex/document.tex'],
                        cwd=moved, check=True, capture_output=True, timeout=480,
                    )
                    self.assertTrue((build / 'document.pdf').read_bytes().startswith(b'%PDF-'))
                    dependencies = (build / 'document.fdb_latexmk').read_text()
                    self.assertNotIn('luatexja/extra_', dependencies)
                    self.assertRegex(dependencies, r'\.(?:ttf|otf)"')
                    if not any(f.startswith('Fandol') for f in report['fonts'].values()):
                        self.assertFalse((moved / 'latex/fonts/fandol').exists())
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

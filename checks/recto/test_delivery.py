"""Exercise the public exporter and the delivered files, without mocked converters."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
EXPORT = ROOT / 'skills/recto/scripts/export.py'
SOURCE = ROOT / 'skills/recto/assets/examples/reference.md'
sys.path.insert(0, str(ROOT / 'skills/recto/scripts'))
from latex import compile_pdf


class DeliveryTests(unittest.TestCase):
    def test_code_and_citations_survive_pdf_and_word_export(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / 'technical.md'
            content = (ROOT / 'skills/recto/assets/examples/technical.md').read_text()
            stress = ('```python\ntab_value = "left\tright"\nendpoint = "https://example.com/' + 'part_' * 40 + '"\n'
                      + '\n'.join(f'print("row_{i:03d}", "中文保留")' for i in range(70)) + '\n```\n\n')
            source.write_text(content.replace('::: pagebreak', stress + '::: pagebreak'))
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            for style in ('reference', 'gbt9704'):
                with self.subTest(style=style):
                    out = directory / style
                    result = subprocess.run(
                        [sys.executable, str(EXPORT), str(source), '--style', style,
                         '--formats', 'tex,pdf,docx', '--bundled-fonts', '--output', str(out)],
                        capture_output=True, text=True, timeout=480,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    pdf_text = subprocess.check_output(
                        ['pdftotext', '-layout', str(out / 'document.pdf'), '-'], text=True)
                    for value in ('关闭遥测', '中文保留', '354', '356',
                                  r'\input{not-a-file}', '^^41'):
                        self.assertIn(value, pdf_text)
                    self.assertIn('50%', ''.join(pdf_text.split()))
                    self.assertIn('"enabled":false', ''.join(pdf_text.split()))
                    self.assertNotIn('⌋', pdf_text, 'Visual wrap markers must not become code characters')
                    for i in range(70):
                        self.assertIn(f'row_{i:03d}', pdf_text)
                    pdf_xml = etree.fromstring(subprocess.check_output(
                        ['pdftohtml', '-xml', '-stdout', str(out / 'document.pdf')]))
                    pages = pdf_xml.findall('page')
                    self.assertGreater(len(pages), 2)
                    links = pdf_xml.findall('.//a')
                    self.assertTrue(any(a.get('href') == 'https://pandoc.org/MANUAL.html' for a in links))
                    citations = [a for a in links if 'S1' in ''.join(a.itertext())]
                    self.assertTrue(citations)
                    for link in citations:
                        page = int(link.get('href').rsplit('#', 1)[1])
                        self.assertIn('示例文件', ''.join(pages[page - 1].itertext()))
                    with ZipFile(out / 'document.docx') as archive:
                        document = etree.fromstring(archive.read('word/document.xml'))
                        styles = etree.fromstring(archive.read('word/styles.xml'))
                        bookmarks = document.xpath('//w:bookmarkStart/@w:name', namespaces=ns)
                        anchors = document.xpath('//w:hyperlink/@w:anchor', namespaces=ns)
                        self.assertGreaterEqual(len(anchors), 3)
                        self.assertTrue(set(anchors) <= set(bookmarks))
                        text = ''.join(document.xpath('//w:t/text()', namespaces=ns))
                        for value in ('354  def snapshot(users):', '355      # 保留中文',
                                      '356      return', 'row_000', 'row_069', r'\input{not-a-file}'):
                            self.assertIn(value, text)
                        for name in ('VerbatimChar', 'SourceCode'):
                            fonts = styles.xpath(f'//w:style[@w:styleId="{name}"]/w:rPr/w:rFonts', namespaces=ns)
                            self.assertEqual(fonts[0].get(f'{{{ns["w"]}}}ascii'), 'Liberation Mono')
                            self.assertEqual(fonts[0].get(f'{{{ns["w"]}}}eastAsia'), 'FandolFang R')
                        self.assertEqual(styles.xpath('//w:style[@w:styleId="SourceCode"]/w:pPr/w:jc/@w:val', namespaces=ns), ['left'])
                    normalized = (out / 'content.md').read_text()
                    self.assertIn('def snapshot(users):', normalized)
                    self.assertNotIn('354  def', normalized, 'Display line numbers must not change the common source')
                    self.assertIn('left\tright', normalized)

            source.write_text('```{.python .numberLines startFrom="invalid"}\nprint(1)\n```')
            result = subprocess.run(
                [sys.executable, str(EXPORT), str(source), '--formats', 'docx',
                 '--bundled-fonts', '--output', str(directory / 'invalid')], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('startFrom must be a positive integer', result.stderr)

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

    def test_word_export_preserves_math_font_symbols_and_alignment(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            source = temporary / 'edge-cases.md'
            source.write_text(
                'Proof[^proof]\n\n'
                '$$\\begin{gathered}\na=b \\\\\ne=f\n\\end{gathered}$$\n\n'
                '$$\\begin{aligned}\n'
                'a \\& b &= c & d &= e \\\\\n'
                'f \\& g &= h & i &= j\n'
                '\\end{aligned}$$\n\n'
                '[^proof]: $$\\begin{aligned}\n&\\quad=b \\\\\n&= d\n\\end{aligned}$$ $\\square$\n'
            )
            cases = [('reference sample', SOURCE), ('edge cases', source)]
            math_ns = {'m': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
            for name, input_path in cases:
                with self.subTest(source=name):
                    out = temporary / f'{name.replace(" ", "-")}-delivery'
                    result = subprocess.run(
                        [sys.executable, str(EXPORT), str(input_path), '--style', 'reference',
                         '--formats', 'docx', '--output', str(out)],
                        capture_output=True, text=True, timeout=120,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    report = json.loads(result.stdout)

                    with ZipFile(out / 'document.docx') as document:
                        parts = {}
                        document_root = None
                        for member in document.namelist():
                            if member.startswith('word/') and member.endswith('.xml'):
                                root = etree.fromstring(document.read(member))
                                parts[member] = root
                                if member == 'word/document.xml':
                                    document_root = root
                        settings = parts['word/settings.xml']
                        self.assertEqual(
                            settings.xpath('string(m:mathPr/m:mathFont/@m:val)', namespaces=math_ns),
                            report['fonts']['word_math'],
                        )
                        all_math_text = ''.join(
                            text for root in parts.values()
                            for text in root.xpath('//m:oMath//m:t/text()', namespaces=math_ns)
                        )
                        self.assertIn('\u25a1', all_math_text)
                        self.assertNotIn('\u25ab', all_math_text)

                    if name == 'reference sample':
                        continue
                    self.assertIn('a&b', all_math_text)
                    footnote_root = parts['word/footnotes.xml']
                    self.assertIn('\u25a1', ''.join(footnote_root.xpath('.//m:t/text()', namespaces=math_ns)))
                    matrices = document_root.xpath('//m:m', namespaces=math_ns) + \
                        footnote_root.xpath('//m:m', namespaces=math_ns)
                    actual_rows = [
                        [
                            ''.join(cell.xpath('.//m:t/text()', namespaces=math_ns)).strip(' ')
                            for cell in row.xpath('./m:e', namespaces=math_ns)
                        ]
                        for matrix in matrices
                        for row in matrix.xpath('./m:mr', namespaces=math_ns)
                    ]
                    self.assertEqual(actual_rows, [
                        ['a=b'], ['e=f'],
                        ['a&b', '=c', 'd', '=e'],
                        ['f&g', '=h', 'i', '=j'],
                        ['', '\u2001=b'], ['', '=d'],
                    ])
                    for matrix in matrices[1:]:
                        justification = matrix.xpath(
                            './m:mPr/m:mcs/m:mc/m:mcPr/m:mcJc/@m:val', namespaces=math_ns
                        )
                        self.assertEqual(justification, ['right', 'left'] * (len(justification) // 2))
                    for root in (document_root, footnote_root):
                        for cell in root.xpath('//m:m/m:mr/m:e[not(normalize-space(.))]',
                                               namespaces=math_ns):
                            self.assertTrue(cell.xpath('./m:r/m:rPr/m:nor', namespaces=math_ns))
                    preserved = footnote_root.xpath(
                        '//m:m/m:mr/m:e/m:r[m:t/text()="\u2001"]', namespaces=math_ns
                    )
                    self.assertEqual(len(preserved), 1)
                    self.assertEqual(preserved[0].xpath('./m:t/@xml:space', namespaces=math_ns), ['preserve'])

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
                receipt = Path(temporary) / 'export.json'
                receipt.write_text(result.stdout)
                verify = [sys.executable, str(EXPORT), str(SOURCE), '--formats', formats,
                          '--output', str(out), '--verify-report', str(receipt)]
                subprocess.run(verify, check=True, capture_output=True)
                if 'pdf' in formats:
                    pdf = out / 'document.pdf'
                    previous = pdf.read_bytes()
                    pdf.write_bytes(previous + b'\n% replaced after export\n')
                    rejected = subprocess.run(verify, capture_output=True, text=True)
                    self.assertNotEqual(rejected.returncode, 0)
                    self.assertIn('document.pdf', rejected.stderr)
                    pdf.write_bytes(previous)
                media = next((out / 'media').iterdir())
                previous_media = media.read_bytes()
                media.write_bytes(previous_media + b'changed resource')
                rejected = subprocess.run(verify, capture_output=True, text=True)
                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn(media.name, rejected.stderr)
                media.write_bytes(previous_media)
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
                    refreshed = subprocess.run(
                        [sys.executable, str(EXPORT), str(moved / 'content.md'), '--output', str(moved)],
                        check=True, capture_output=True,
                    )
                    receipt.write_bytes(refreshed.stdout)
                    subprocess.run([sys.executable, str(EXPORT), str(moved / 'content.md'),
                                    '--output', str(moved), '--verify-report', str(receipt)],
                                   check=True, capture_output=True)
                    self.assertEqual({p.name for p in moved.iterdir()}, expected)
                    self.assertEqual(len(list((moved / 'media').iterdir())), 1)
                if formats == 'docx':
                    self.assertGreater(report['native_word_math_count'], 0)


if __name__ == '__main__':
    unittest.main()

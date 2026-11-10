"""Self-contained LuaLaTeX source delivery and offline PDF compilation."""
from pathlib import Path
import json
import os
import re
import signal
import shutil
import subprocess
import tempfile
from lxml import etree

from doctor import FONT_DIR

ROOT = Path(__file__).resolve().parents[1]
BUNDLED = {
    'FandolSong': ('fandol', 'FandolSong-Regular.otf', 'FandolSong-Bold.otf'),
    'FandolHei': ('fandol', 'FandolHei-Regular.otf', 'FandolHei-Bold.otf'),
    'FandolKai': ('fandol', 'FandolKai-Regular.otf', None),
    'FandolFang R': ('fandol', 'FandolFang-Regular.otf', None),
    'Liberation Serif': ('liberation', 'LiberationSerif-Regular.ttf', 'LiberationSerif-Bold.ttf'),
    'New Computer Modern Math': ('newcm', 'NewCMMath-Regular.otf', 'NewCMMath-Bold.otf'),
}


def check_svg(path):
    """Copied figures must not lose untracked resources during conversion."""
    tree = etree.parse(str(path), etree.XMLParser(resolve_entities=False, no_network=True))
    references = []
    for node in tree.iter():
        references.extend(value.strip() for key, value in node.attrib.items() if key.rsplit('}', 1)[-1] == 'href')
        css = ' '.join(node.attrib.values()) + (node.text or '')
        references.extend(match[1].strip() for match in re.findall(r'url\(\s*([\'"]?)(.*?)\1\s*\)', css, re.I))
        if '@import' in css.lower():
            references.append('external stylesheet')
    if (tree.docinfo.doctype or tree.xpath('//processing-instruction("xml-stylesheet")')
            or any(not value.startswith(('#', 'data:')) for value in references)):
        raise ValueError('Use a self-contained SVG: embed referenced images/styles before export')


def font_command(command, family, destination, scale=1):
    options = [f'Scale={scale}']
    if family in BUNDLED:
        folder, regular, bold = BUNDLED[family]
        source = FONT_DIR / folder
        target = destination / 'fonts' / folder
        target.mkdir(parents=True, exist_ok=True)
        stem = regular.split('-')[0]
        for path in source.iterdir():
            if path.suffix not in {'.otf', '.ttf'} or path.name.startswith(stem + '-'):
                shutil.copy2(path, target / path.name)
        options.append(f'Path=latex/fonts/{folder}/')
        if command != r'\setmathfont':
            options.append(f'BoldFont={bold or regular}')
            italic = regular.replace('Regular', 'Italic')
            options.append(f'ItalicFont={italic if (source / italic).exists() else regular}')
            bolditalic = regular.replace('Regular', 'BoldItalic')
            options.append(f'BoldItalicFont={bolditalic if (source / bolditalic).exists() else bold or regular}')
        family = regular
    return command + '[' + ','.join(options) + ']{' + family + '}\n'


def compile_pdf(source, directory):
    """Let latexmk settle references and tables; publish nothing on failure."""
    build = directory / '.build'
    build.mkdir()
    command = ['latexmk', '-norc', '-r', str(ROOT / 'assets/latexmkrc'),
               '-lualatex', '-interaction=nonstopmode', '-halt-on-error',
               '-file-line-error', '-outdir=.build', '-latexoption=--no-shell-escape',
               '-latexoption=--nosocket', str(source.relative_to(directory))]
    with subprocess.Popen(command, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, start_new_session=os.name == 'posix') as process:
        try:
            output, _ = process.communicate(timeout=480)
        except subprocess.TimeoutExpired:
            # Stop the compiler child too, before its temporary output directory is removed.
            if os.name == 'posix':
                os.killpg(process.pid, signal.SIGKILL)
            else:
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], check=True, capture_output=True)
            process.communicate()
            raise RuntimeError('latexmk/LuaLaTeX compilation timed out after 480 seconds')
        if process.returncode:
            raise RuntimeError('latexmk/LuaLaTeX compilation failed:\n' + output[-12000:])
    log = (build / 'document.log').read_text(errors='replace')
    problems = re.findall(r'(?m)^.*(?:Missing character:|Overfull \\[hv]box|LaTeX Warning:|Package \S+ Warning:|LaTeX Font Warning:).*$', log)
    if problems:
        raise RuntimeError('LuaLaTeX layout/font diagnostics:\n' + '\n'.join(problems))
    pdf = build / 'document.pdf'
    if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):
        raise RuntimeError('LuaLaTeX did not produce a PDF')
    return pdf


def export_latex(payload, common, run, style, fonts, out, formats, env):
    with tempfile.TemporaryDirectory(prefix='.recto-', dir=out) as temporary:
        stage = Path(temporary)
        texdir = stage / 'latex'
        texdir.mkdir()
        shutil.copy2(ROOT / 'assets/latexmkrc', texdir / 'latexmkrc')
        if (out / 'media').exists():
            shutil.copytree(out / 'media', stage / 'media')
        converted = []
        document = json.loads(payload)
        def images(value):
            if isinstance(value, dict):
                if value.get('t') == 'Image' and value['c'][2][0].lower().endswith('.svg'):
                    source = stage / value['c'][2][0]
                    check_svg(source)
                    target = source.with_suffix(source.suffix + '.pdf')
                    if not shutil.which('rsvg-convert'):
                        raise RuntimeError('SVG images require rsvg-convert (librsvg); install it or provide PNG/PDF')
                    run(['rsvg-convert', '--format=pdf', '--output', str(target), str(source)])
                    value['c'][2][0] = str(target.relative_to(stage))
                    converted.append(target)
                for child in value.values(): images(child)
            elif isinstance(value, list):
                for child in value: images(child)
        images(document)
        payload = json.dumps(document).encode()
        commands = [font_command(r'\setmainfont', fonts['latin'], texdir)]
        for command, role in [(r'\setCJKmainfont', 'body'), (r'\setCJKsansfont', 'hei'),
                              (r'\newCJKfontfamily\rectohei', 'hei'), (r'\newCJKfontfamily\rectokai', 'kai'),
                              (r'\newCJKfontfamily\rectotitlefont', 'title'), (r'\newfontfamily\rectofolio', 'folio')]:
            commands.append(font_command(command, fonts[role], texdir))
        commands.append(font_command(r'\setmathfont', fonts['math'], texdir, 1.21 if style == 'reference' else 1))
        if style == 'gbt9704' and fonts['title'] == 'FandolSong':
            commands.append(r'\appto\rectotitlefont{\bfseries}' + '\n')
        header = stage / 'header.tex'
        header.write_text((ROOT / 'assets/styles/common.tex').read_text() + ''.join(commands)
                          + (ROOT / f'assets/styles/{style}.tex').read_text())
        target = texdir / 'document.tex'
        run(common + ['-t', 'latex', '--standalone', '--pdf-engine=lualatex', '--wrap=none',
                      '-V', 'documentclass=article', '-V', 'fontsize=12pt', '-V', 'indent=true',
                      '-V', 'geometry=margin=12mm', '-H', str(header), '-o', str(target)],
            input=payload, env=env, cwd=stage)
        command = 'latexmk -norc -r latex/latexmkrc -lualatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build -latexoption=--no-shell-escape -latexoption=--nosocket latex/document.tex'
        target.write_text('% From the delivery root: ' + command + '\n'
                          '% PDF: build/document.pdf. System fonts are not bundled.\n'
                          '% Images are converted explicitly before export, never by shell escape.\n'
                          r'\def\DoNotLoadEpstopdf{}' + '\n' + target.read_text())
        outputs = []
        if 'pdf' in formats:
            compile_pdf(target, stage).replace(out / 'document.pdf')
            outputs.append('document.pdf')
        if 'tex' in formats:
            # Merge only generated resources; never remove unknown files in an existing delivery.
            shutil.copytree(texdir, out / 'latex', dirs_exist_ok=True)
            for path in converted:
                shutil.copy2(path, out / path.relative_to(stage))
            outputs.append('latex/document.tex')
        return outputs

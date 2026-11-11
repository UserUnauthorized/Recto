#!/usr/bin/env python3
"""Check Recto's runtime without installing anything or importing export.py."""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / 'assets/fonts'
TEX_FILES = (
    'ctex.sty', 'luatexja.sty', 'fontspec.sty', 'unicode-math.sty',
    'titlesec.sty', 'caption.sty', 'needspace.sty', 'eso-pic.sty',
    'float.sty', 'array.sty', 'longtable.sty', 'booktabs.sty',
    'graphicx.sty', 'geometry.sty', 'hyperref.sty', 'xcolor.sty',
    'fancyvrb.sty', 'fvextra.sty', 'framed.sty', 'bookmark.sty', 'footnotehyper.sty', 'etoolbox.sty',
    'lmodern.sty',
)
BUNDLED_FONTS = {
    'FandolSong': 'fandol/FandolSong-*.otf',
    'FandolHei': 'fandol/FandolHei-*.otf',
    'FandolKai': 'fandol/FandolKai-*.otf',
    'FandolFang R': 'fandol/FandolFang-*.otf',
    'Liberation Serif': 'liberation/LiberationSerif-*.ttf',
    'Liberation Mono': 'liberation/LiberationMono-*.ttf',
    'New Computer Modern Math': 'newcm/NewCMMath-*.otf',
}
ORIGINAL = {
    'reference': dict(body='Songti SC', latin='Times New Roman', title='Songti SC',
                      hei='Songti SC', kai='Songti SC', folio='Times New Roman'),
    'gbt9704': dict(body='FZFangSong-Z02', latin='FZFangSong-Z02', title='FZXiaoBiaoSong-B05',
                    hei='FZHei-B01', kai='FZKai-Z03', folio='SimSun'),
}
FALLBACK = {
    'Songti SC': 'FandolSong', 'Times New Roman': 'Liberation Serif',
    'FZFangSong-Z02': 'FandolFang R', 'FZXiaoBiaoSong-B05': 'FandolSong',
    'FZHei-B01': 'FandolHei', 'FZKai-Z03': 'FandolKai', 'SimSun': 'FandolSong',
}


def select_fonts(style, available):
    fonts = {role: name if name in available else FALLBACK[name]
             for role, name in ORIGINAL[style].items()}
    fonts['math'] = 'New Computer Modern Math'
    fonts['mono'] = 'Liberation Mono'
    fonts['code_cjk'] = 'FandolFang R'
    fonts['word_math'] = 'Cambria Math' if 'Cambria Math' in available else fonts['math']
    missing = set(fonts.values()) - set(available)
    if missing:
        raise ValueError('Bundled fonts are missing or unreadable: ' + ', '.join(sorted(missing)))
    substitutions = {name: fonts[role] for role, name in ORIGINAL[style].items()
                     if fonts[role] != name}
    if fonts['word_math'] != 'Cambria Math':
        substitutions['Cambria Math'] = fonts['word_math']
    return fonts, substitutions


def command_version(command, minimum=None):
    executable = shutil.which(command)
    if not executable:
        return None, f'{command} not found on PATH'
    try:
        result = subprocess.run([executable, '--version'], capture_output=True,
                                text=True, timeout=15)
    except subprocess.TimeoutExpired:
        return None, f'{command} --version timed out'
    match = re.search(r'\b(\d+\.\d+(?:\.\d+)*(?:\.\d+)?)', result.stdout)
    if result.returncode or not match:
        return None, f'Cannot read {command} version: {result.stderr.strip()}'
    version = match.group(1)
    if minimum and tuple(map(int, version.split('.'))) < minimum:
        return None, (f'{command} >={".".join(map(str, minimum))} required; '
                      f'found {version}')
    return version, None


def system_font_families():
    fc_list = shutil.which('fc-list')
    if fc_list:
        result = None
        try:
            result = subprocess.run([fc_list, '--format', '%{family}\n'],
                                    capture_output=True, text=True, timeout=15)
        except subprocess.TimeoutExpired:
            result = None
        if result is not None and result.returncode == 0 and result.stdout.strip():
            families = {family.strip() for line in result.stdout.splitlines()
                        for family in line.split(',') if family.strip()}
            return families, 'fc-list'
    system_profiler = shutil.which('system_profiler')
    if system_profiler:
        try:
            result = subprocess.run([system_profiler, 'SPFontsDataType', '-json'],
                                    capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            result = None
        if result is None:
            return set(), 'bundled'
        try:
            fonts = json.loads(result.stdout).get('SPFontsDataType', [])
            families = {
                face['family'] for font in fonts for face in font.get('typefaces', [])
                if result.returncode == 0 and face.get('family')
                and face.get('enabled', 'yes') != 'no'
            }
            return families, 'system_profiler'
        except (json.JSONDecodeError, OSError):
            pass
    return set(), 'bundled'


def check(style, formats=('tex', 'pdf'), bundled_fonts=False):
    formats = tuple(formats)
    if set(formats) - {'tex', 'pdf', 'docx'}:
        raise ValueError('formats must be tex, pdf, or docx')
    issues = []
    versions = {}
    if sys.version_info < (3, 10):
        issues.append('Python >=3.10 required')
    for module in ('docx', 'lxml.etree'):
        try:
            importlib.import_module(module)
        except (ImportError, OSError) as error:
            issues.append(f'Python dependency {module}: {error}')
    version, error = command_version('pandoc', (3, 9))
    if error:
        issues.append(error)
    else:
        versions['pandoc'] = version
    if 'pdf' in formats:
        version, error = command_version('lualatex')
        if error:
            issues.append(error)
        else:
            versions['lualatex'] = version
        version, error = command_version('latexmk')
        if error:
            issues.append(error)
        else:
            versions['latexmk'] = version
        kpsewhich = shutil.which('kpsewhich')
        if not kpsewhich:
            issues.append('kpsewhich not found on PATH')
        else:
            for tex_file in TEX_FILES:
                try:
                    result = subprocess.run([kpsewhich, tex_file], capture_output=True,
                                            text=True, timeout=10)
                except subprocess.TimeoutExpired:
                    issues.append(f'kpsewhich {tex_file} timed out')
                else:
                    if result.returncode or not result.stdout.strip():
                        issues.append(f'TeX package file not found: {tex_file}')
    fonts, substitutions = {}, {}
    bundled = {family for family, pattern in BUNDLED_FONTS.items()
               if next(FONT_DIR.glob(pattern), None)}
    available, discovery = (set(), None) if bundled_fonts else system_font_families()
    try:
        fonts, substitutions = select_fonts(style, available | bundled)
    except ValueError as error:
        issues.append(str(error))
    word_font_note=None
    if 'docx' in formats and fonts:
        word_font_note='DOCX records the configured math font; actual substitution depends on the editor and is not measured by this check.'
        if fonts['word_math'] not in available:
            word_font_note+=(f" {fonts['word_math']} was not detected among system fonts; install the bundled font "
                             'in the target editor. Bundled font files are not embedded in DOCX.')
    return dict(ready=not issues, python=sys.executable, versions=versions, style=style,
                fonts=fonts, substitutions=substitutions, font_discovery=discovery,
                word_font_note=word_font_note,
                issues=issues,
                setup=str(ROOT / 'references/setup.md'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--style', choices=ORIGINAL, default='reference')
    parser.add_argument('--formats', default='tex,pdf')
    parser.add_argument('--bundled-fonts', action='store_true')
    args = parser.parse_args()
    report = check(args.style, tuple(args.formats.split(',')), args.bundled_fonts)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ready'] else 1


if __name__ == '__main__':
    sys.exit(main())

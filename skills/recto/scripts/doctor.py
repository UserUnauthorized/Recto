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
    fonts['word_math'] = 'Cambria Math' if 'Cambria Math' in available else fonts['math']
    missing = set(fonts.values()) - set(available)
    if missing:
        raise ValueError('Bundled fonts are missing or unreadable: ' + ', '.join(sorted(missing)))
    substitutions = {name: fonts[role] for role, name in ORIGINAL[style].items()
                     if fonts[role] != name}
    if fonts['word_math'] != 'Cambria Math':
        substitutions['Cambria Math'] = fonts['word_math']
    return fonts, substitutions


def check(style):
    issues = []
    versions = {}
    if sys.version_info < (3, 10):
        issues.append('Python >=3.10 required')
    for module in ('docx', 'lxml.etree'):
        try:
            importlib.import_module(module)
        except (ImportError, OSError) as error:
            issues.append(f'Python dependency {module}: {error}')
    for command, minimum in [('pandoc', (3, 9)), ('typst', (0, 15, 1))]:
        executable = shutil.which(command)
        if not executable:
            issues.append(f'{command} not found on PATH')
            continue
        result = subprocess.run([executable, '--version'], capture_output=True, text=True)
        match = re.search(r'\b(\d+\.\d+(?:\.\d+)*(?:\.\d+)?)', result.stdout)
        if result.returncode or not match:
            issues.append(f'Cannot read {command} version: {result.stderr.strip()}')
            continue
        versions[command] = match.group(1)
        if tuple(map(int, match.group(1).split('.'))) < minimum:
            issues.append(f'{command} >={".".join(map(str, minimum))} required; found {match.group(1)}')
    fonts, substitutions = {}, {}
    if 'typst' in versions:
        result = subprocess.run(['typst', 'fonts', '--font-path', str(FONT_DIR)], capture_output=True, text=True)
        if result.returncode or result.stderr.strip():
            issues.append('Cannot discover fonts: ' + result.stderr.strip())
        else:
            try:
                fonts, substitutions = select_fonts(style, result.stdout.splitlines())
            except ValueError as error:
                issues.append(str(error))
    return dict(ready=not issues, python=sys.executable, versions=versions, style=style,
                fonts=fonts, substitutions=substitutions, issues=issues,
                setup=str(ROOT / 'references/setup.md'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--style', choices=ORIGINAL, default='reference')
    args = parser.parse_args()
    report = check(args.style)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ready'] else 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Run repository gates and exercise the distributable plugin in a clean directory."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

from release import build, verify, version

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    subprocess.run(args, cwd=ROOT, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', default='', help='Version to rehearse; empty uses the source manifest')
    args = parser.parse_args()
    tag = args.tag or 'v' + json.loads((ROOT / 'plugin.json').read_text())['version']
    version(tag)
    for command in ('rsvg-convert', 'pdfinfo'):
        if not shutil.which(command):
            raise SystemExit(f'CI requires {command}; do not silently skip its checks')
    qa = ROOT / 'output/recto/ci'
    qa.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix='run-', dir=qa))
    bundle = workspace / 'bundle'
    evidence = workspace / 'evidence'
    bundle.mkdir()
    evidence.mkdir()
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write(f'bundle={bundle}\nevidence={evidence}\ntag={tag}\n')
    for style in ('reference', 'gbt9704'):
        run(sys.executable, 'skills/recto/scripts/doctor.py', '--style', style,
            '--formats', 'tex,pdf,docx', '--bundled-fonts')
    run(sys.executable, 'scripts/skills.py', 'check')
    run(sys.executable, 'scripts/plugin.py', 'check')
    for folder in ('recto', 'plugin', 'release'):
        run(sys.executable, '-m', 'unittest', 'discover', '-s', f'checks/{folder}', '-v')
    build(tag)
    for name in verify(ROOT / 'dist', tag):
        shutil.copy2(ROOT / 'dist' / name, bundle / name)
    consumer = workspace / 'consumer'
    with ZipFile(bundle / f'recto-plugin-{tag[1:]}.zip') as archive:
        archive.extractall(consumer)
    exporter = consumer / 'skills/recto/scripts/export.py'
    for style in ('reference', 'gbt9704'):
        delivery = workspace / 'delivery' / style
        report = evidence / f'{style}.json'
        command = [sys.executable, str(exporter),
                   str(consumer / f'skills/recto/assets/examples/{style}.md'),
                   '--style', style, '--formats', 'tex,pdf,docx', '--bundled-fonts',
                   '--output', str(delivery)]
        with report.open('w') as output:
            subprocess.run(command, cwd=consumer, stdout=output, check=True)
        subprocess.run(command + ['--verify-report', str(report)], cwd=consumer, check=True)
        run('pdfinfo', str(delivery / 'document.pdf'))
        for suffix in ('pdf', 'docx'):
            shutil.copy2(delivery / f'document.{suffix}', evidence / f'{style}.{suffix}')
    run('git', 'diff', '--exit-code')
    print(f'Validated {tag}; bundle: {bundle}; consumer evidence: {evidence}')


if __name__ == '__main__':
    main()

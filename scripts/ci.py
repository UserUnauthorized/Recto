#!/usr/bin/env python3
"""Run repository gates and exercise the distributable plugin in a clean directory."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

from release import build, version

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    subprocess.run(args, cwd=ROOT, check=True, **kwargs)


def recto_tests(part):
    class Loader(unittest.TestLoader):
        def getTestCaseNames(self, case):
            names = super().getTestCaseNames(case)
            if part == 'all':
                return names
            # Put the shorter half alongside the consumer exports.
            return names[0::2] if part == 'distribution' else names[1::2]

    suite = Loader().discover(str(ROOT / 'checks/recto'))
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', default='', help='Version to rehearse; empty uses the source manifest')
    parser.add_argument('--part', choices=('all', 'tests', 'distribution'), default='all')
    args = parser.parse_args()
    tag = args.tag or 'v' + json.loads((ROOT / 'plugin.json').read_text())['version']
    version(tag)
    for command in ('rsvg-convert', 'pdfinfo'):
        if not shutil.which(command):
            raise SystemExit(f'CI requires {command}; do not silently skip its checks')
    if args.part == 'distribution':
        recto_tests(args.part)
    else:
        # Release tests build in a temporary checkout, independent of all Recto exports.
        with ThreadPoolExecutor(max_workers=1) as worker:
            release_tests = worker.submit(run, sys.executable, '-m', 'unittest', 'discover',
                                          '-s', 'checks/release', '-v')
            recto_tests(args.part)
            release_tests.result()
    if args.part == 'tests':
        run('git', 'diff', '--exit-code')
        return
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
    # Release packaging calls the plugin and both skills' structural checks.
    run(sys.executable, '-m', 'unittest', 'discover', '-s', 'checks/plugin', '-v')
    for name in build(tag):
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

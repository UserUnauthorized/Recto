#!/usr/bin/env python3
"""Build, verify and publish tag-versioned Recto packages with GitHub CLI."""
import argparse
import base64
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def version(tag):
    if not re.fullmatch(r'v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', tag):
        raise ValueError('Expected a stable version tag: vX.Y.Z')
    return tuple(map(int, tag[1:].split('.')))


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs).stdout


def api(path, payload=None, paginate=False):
    args = ['gh', 'api', path]
    if paginate:
        args += ['--paginate', '--slurp']
    if payload is not None:
        args += ['--method', 'PUT', '--input', '-']
    return json.loads(run(*args, input=json.dumps(payload) if payload is not None else None))


def preflight(repo, tag, commit):
    wanted = version(tag)
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Expected the exact tested commit SHA')
    if api(f'repos/{repo}/commits/{tag}')['sha'] != commit:
        raise ValueError('Tag no longer points to the tested commit')
    if api(f'repos/{repo}/compare/{commit}...main')['status'] not in ('ahead', 'identical'):
        raise ValueError('Release commit must already be merged into main')
    releases = [item for page in api(f'repos/{repo}/releases?per_page=100', paginate=True) for item in page]
    current = next((item for item in releases if item['tag_name'] == tag), None)
    for item in releases:
        if not item['draft'] and not item['prerelease']:
            try:
                existing = version(item['tag_name'])
            except ValueError:
                continue
            if existing > wanted:
                raise ValueError(f"A newer stable release already exists: {item['tag_name']}")
    if current and current['prerelease']:
        raise ValueError('An existing prerelease cannot be repurposed as a stable release')
    return current


def artifact_names(tag):
    version(tag)
    return [f'recto-plugin-{tag[1:]}.zip', 'recto-skill.zip', 'study-notes-skill.zip']


def verify(directory, tag):
    expected = artifact_names(tag)
    lines = (directory / 'SHA256SUMS').read_text().splitlines()
    recorded = {}
    for line in lines:
        match = re.fullmatch(r'([0-9a-f]{64})  ([a-zA-Z0-9.-]+)', line)
        if not match or match[2] in recorded:
            raise ValueError('Invalid or duplicate checksum entry')
        recorded[match[2]] = match[1]
    if set(recorded) != set(expected):
        raise ValueError('Release must contain exactly the three expected ZIP checksums')
    for name in expected:
        path = directory / name
        if sha256(path.read_bytes()).hexdigest() != recorded[name]:
            raise ValueError(f'Checksum mismatch: {name}')
        with ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError(f'Corrupt ZIP: {name}')
            for member in archive.namelist():
                if Path(member).is_absolute() or '..' in Path(member).parts:
                    raise ValueError(f'Unsafe ZIP entry: {member}')
            if name == expected[0] and json.loads(archive.read('plugin.json'))['version'] != tag[1:]:
                raise ValueError('Plugin version differs from release tag')
    return expected + ['SHA256SUMS']


def build(tag):
    from plugin import package as package_plugin
    from skills import package as package_skill
    version(tag)
    paths = [package_plugin(tag[1:]), package_skill('recto'), package_skill('study-notes')]
    checksums = ''.join(f'{sha256(path.read_bytes()).hexdigest()}  {path.name}\n' for path in paths)
    (ROOT / 'dist/SHA256SUMS').write_text(checksums)
    verify(ROOT / 'dist', tag)
    print(checksums, end='')


def verify_remote(release, directory, names):
    assets = {asset['name']: asset for asset in release['assets']}
    if len(release['assets']) != len(names) or set(assets) != set(names):
        raise ValueError('Remote release asset set differs from the validated bundle')
    for name in names:
        data = (directory / name).read_bytes()
        asset = assets[name]
        if (asset['state'] != 'uploaded' or asset['size'] != len(data)
                or asset.get('digest') != 'sha256:' + sha256(data).hexdigest()):
            raise ValueError(f'Remote release asset differs: {name}; published assets are never overwritten')


def sync_version(repo, tag):
    file = api(f'repos/{repo}/contents/plugin.json?ref=main')
    manifest = json.loads(base64.b64decode(file['content']))
    if version('v' + manifest['version']) >= version(tag):
        return
    manifest['version'] = tag[1:]
    content = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    # The blob SHA prevents overwriting a concurrent manifest change; rerun on conflict.
    api(f'repos/{repo}/contents/plugin.json', {
        'message': f'chore: sync plugin version to {tag}', 'branch': 'main',
        'sha': file['sha'], 'content': base64.b64encode(content).decode(),
    })


def publish(repo, tag, commit, directory):
    names = verify(directory, tag)
    existing = preflight(repo, tag, commit)
    if existing is None:
        run('gh', 'release', 'create', tag, '--repo', repo, '--verify-tag',
            '--draft', '--title', f'Recto {tag}', '--generate-notes')
    if existing is None or existing['draft']:
        # Only incomplete drafts may be replaced when a failed upload is rerun.
        run('gh', 'release', 'upload', tag, *(str(directory / name) for name in names),
            '--repo', repo, '--clobber')
    # The by-tag endpoint excludes drafts; preflight's release list includes them.
    release = preflight(repo, tag, commit)
    if release is None:
        raise ValueError('Release is not visible after uploading its assets')
    verify_remote(release, directory, names)
    with tempfile.TemporaryDirectory(prefix='recto-release-download-') as temporary:
        downloaded = Path(temporary)
        run('gh', 'release', 'download', tag, '--repo', repo, '--dir', str(downloaded))
        verify(downloaded, tag)
        for name in names:
            if (downloaded / name).read_bytes() != (directory / name).read_bytes():
                raise ValueError(f'Download differs from validated artifact: {name}')
    preflight(repo, tag, commit)
    if release['draft']:
        run('gh', 'release', 'edit', tag, '--repo', repo, '--draft=false', '--latest')
    published = api(f'repos/{repo}/releases/tags/{tag}')
    if published['draft'] or published['prerelease']:
        raise ValueError('Release did not become a stable publication')
    verify_remote(published, directory, names)
    sync_version(repo, tag)
    print(published['html_url'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build', 'verify', 'preflight', 'publish'))
    parser.add_argument('--tag', required=True)
    parser.add_argument('--commit', default=os.environ.get('GITHUB_SHA'))
    parser.add_argument('--repo', default=os.environ.get('GITHUB_REPOSITORY'))
    parser.add_argument('--dist', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    version(args.tag)
    if args.action in ('preflight', 'publish') and (not args.repo or not args.commit):
        parser.error('preflight/publish require --repo and --commit, or GitHub Actions environment')
    if args.action == 'build':
        build(args.tag)
    elif args.action == 'verify':
        print('\n'.join(verify(args.dist, args.tag)))
    elif args.action == 'preflight':
        preflight(args.repo, args.tag, args.commit)
        print(f'Eligible release: {args.tag} at {args.commit}')
    else:
        publish(args.repo, args.tag, args.commit, args.dist)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        raise SystemExit(getattr(error, 'stderr', None) or str(error))

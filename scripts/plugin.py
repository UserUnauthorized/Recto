#!/usr/bin/env python3
"""Validate and package the Codex plugin without repository development files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from skills import check

ROOT = Path(__file__).resolve().parents[1]


def metadata_files() -> list[Path]:
    plugin_path = ROOT / "plugin.json"
    marketplace_path = ROOT / ".agents/plugins/marketplace.json"
    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    entry = marketplace["plugins"][0]
    extension = plugin["extensions"]["com.openai"]
    interface = extension["interface"]

    assert plugin["name"] == entry["name"] == "recto"
    assert marketplace["name"] == "recto"
    assert plugin["version"] == "0.3.0"
    assert entry["source"] == {"source": "local", "path": "./"}
    assert extension["onboardingSkill"] == "./skills/recto/SKILL.md"

    paths = [plugin_path]
    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        paths.extend(check(skill.parent.name))
    for relative in [extension["onboardingSkill"], interface["composerIcon"], interface["logo"], *interface["screenshots"]]:
        path = (ROOT / relative.removeprefix("./")).resolve()
        assert path.is_relative_to(ROOT.resolve()) and path.is_file(), relative
        paths.append(path)
    return sorted(set(paths))


def package() -> Path:
    paths = metadata_files()
    dest = ROOT / f"dist/recto-plugin-{json.loads((ROOT / 'plugin.json').read_text())['version']}.zip"
    dest.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".plugin-", dir=dest.parent) as temporary:
        archive = Path(temporary) / dest.name
        with ZipFile(archive, "w", ZIP_DEFLATED) as output:
            for path in paths:
                item = ZipInfo(path.relative_to(ROOT).as_posix())
                item.compress_type = ZIP_DEFLATED
                item.create_system = 3
                item.external_attr = 0o100644 << 16
                output.writestr(item, path.read_bytes())
        archive.replace(dest)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("check")
    actions.add_parser("package")
    args = parser.parse_args()
    if args.action == "check":
        print(f"OK recto plugin: {len(metadata_files())} files; manifests, paths, skill checks")
    else:
        print(package())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

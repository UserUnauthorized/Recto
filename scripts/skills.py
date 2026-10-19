#!/usr/bin/env python3
"""Check, package and install the self-contained skills in this repository."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

try:
    import yaml
except ImportError:
    raise SystemExit("Missing PyYAML. Run: python3 -m pip install -r requirements-dev.txt")

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
IGNORED = {".DS_Store", "__pycache__", ".git", ".venv", ".pytest_cache"}


def files(folder: Path) -> list[Path]:
    result = []
    for path in sorted(folder.rglob("*")):
        relative = path.relative_to(folder)
        if any(part in IGNORED for part in relative.parts) or path.suffix == ".pyc":
            continue
        # A skill must work after copying or extracting it on another machine.
        if path.is_symlink():
            raise ValueError(f"Symlinks are not portable skill resources: {path}")
        if path.is_file():
            result.append(path)
    return result


def skill_path(name: str) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(f"Invalid skill name: {name}")
    path = SKILLS / name
    if path.is_symlink() or not (path / "SKILL.md").is_file():
        raise ValueError(f"No self-contained skill at {path}")
    return path


def metadata(folder: Path) -> dict:
    text = (folder / "SKILL.md").read_text()
    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not match:
        raise ValueError(f"Missing YAML frontmatter: {folder / 'SKILL.md'}")
    data = yaml.safe_load(match[1])
    if not isinstance(data, dict) or data.get("name") != folder.name:
        raise ValueError(f"Frontmatter name must match folder: {folder}")
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        raise ValueError(f"Missing description: {folder}")
    return data


def check(name: str) -> list[Path]:
    folder = skill_path(name)
    metadata(folder)
    paths = files(folder)
    for path in paths:
        if path.suffix == ".py":
            compile(path.read_text(), str(path), "exec")
        elif path.suffix in {".yaml", ".yml"}:
            yaml.safe_load(path.read_text())
        elif path.suffix == ".md":
            # Check authored inline links, not example code or web links.
            text = re.sub(r"```.*?```", "", path.read_text(), flags=re.S)
            for link in re.findall(r"\]\(([^\s)]+)\)", text):
                if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", link) or link.startswith("#"):
                    continue
                target = (path.parent / link.split("#", 1)[0]).resolve()
                if not target.is_relative_to(folder.resolve()) or not target.exists():
                    raise ValueError(f"Broken or nonportable skill link: {path}: {link}")
    return paths


def fingerprint(folder: Path) -> dict[str, str]:
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files(folder)}


def package(name: str) -> Path:
    paths = check(name)
    folder = skill_path(name)
    dest = ROOT / "dist" / f"{name}-skill.zip"
    dest.parent.mkdir(exist_ok=True)
    # Stable ordering and timestamps give identical archives for identical sources.
    with tempfile.TemporaryDirectory(prefix=".package-", dir=dest.parent) as temporary:
        archive = Path(temporary) / dest.name
        with ZipFile(archive, "w", ZIP_DEFLATED) as output:
            for path in paths:
                item = ZipInfo(f"{name}/{path.relative_to(folder).as_posix()}")
                item.compress_type = ZIP_DEFLATED
                item.create_system = 3
                item.external_attr = 0o100644 << 16
                output.writestr(item, path.read_bytes())
        archive.replace(dest)
    return dest


def install(name: str, destination: Path, replace: bool) -> str:
    paths = check(name)
    source = skill_path(name)
    parent = destination.expanduser().resolve()
    target = parent / name
    if target.is_symlink():
        raise ValueError(f"Refusing to replace a symlink: {target}")
    if target.exists():
        if not target.is_dir():
            raise ValueError(f"Install target is not a directory: {target}")
        if fingerprint(source) == fingerprint(target):
            return f"Already current: {target}"
        if not replace:
            raise ValueError(f"Installed skill differs: {target}. Use --replace to back it up and update.")
    parent.mkdir(parents=True, exist_ok=True)
    backup = None
    with tempfile.TemporaryDirectory(prefix=f".{name}-install-", dir=parent) as temporary:
        stage = Path(temporary)
        prepared = stage / "new"
        prepared.mkdir()
        for path in paths:
            copy = prepared / path.relative_to(source)
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, copy)
        if target.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            backup = ROOT / "output" / "install-backups" / f"{name}-{stamp}"
            backup.parent.mkdir(parents=True, exist_ok=True)
            # Backups live outside the discovery directory to avoid duplicate skills.
            shutil.copytree(target, backup)
            target.rename(stage / "previous")
        try:
            prepared.rename(target)
        except OSError:
            if (stage / "previous").exists():
                (stage / "previous").rename(target)
            raise
    result = f"Installed: {target}"
    return result + (f"\nPrevious copy: {backup}" if backup else "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("list", help="List installable skills")
    for action in ("check", "package"):
        command = actions.add_parser(action)
        command.add_argument("names", nargs="*", help="Skill names; defaults to all")
    command = actions.add_parser("install")
    command.add_argument("name")
    command.add_argument("--dest", type=Path,
                         default=Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "skills",
                         help="Destination skills directory (default: CODEX_HOME/skills)")
    command.add_argument("--replace", action="store_true", help="Back up and replace a differing installation")
    args = parser.parse_args()
    try:
        names = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))
        if args.action == "list":
            for name in names:
                print(f"{name}\t{metadata(skill_path(name))['description']}")
        elif args.action == "install":
            print(install(args.name, args.dest, args.replace))
        else:
            selected = args.names or names
            if not selected:
                raise ValueError("No skills found")
            for name in selected:
                if args.action == "check":
                    print(f"OK {name}: {len(check(name))} files; metadata, local links, Python syntax")
                else:
                    print(package(name))
        return 0
    except (ValueError, OSError, SyntaxError, yaml.YAMLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

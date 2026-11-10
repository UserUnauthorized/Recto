"""Release commands must fail before publication when any invariant is unclear."""
from base64 import b64decode, b64encode
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[2]
RELEASE_MODULE = importlib.util.spec_from_file_location("recto_release", ROOT / "scripts/release.py")
release = importlib.util.module_from_spec(RELEASE_MODULE)
RELEASE_MODULE.loader.exec_module(release)


class ReleaseContractTests(unittest.TestCase):
    def temporary_directory(self):
        output = ROOT / "output"
        output.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(prefix="release-test-", dir=output)

    def test_build_uses_tag_without_changing_source_and_rejects_tampered_checksum(self):
        with self.temporary_directory() as temporary:
            repo = Path(temporary) / "repo"
            shutil.copytree(
                ROOT,
                repo,
                ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "dist", "output"),
            )
            manifest = repo / "plugin.json"
            source_manifest = manifest.read_bytes()

            result = subprocess.run(
                [sys.executable, "scripts/release.py", "build", "--tag", "v0.9.0"],
                cwd=repo,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with ZipFile(repo / "dist/recto-plugin-0.9.0.zip") as archive:
                self.assertEqual(json.loads(archive.read("plugin.json"))["version"], "0.9.0")
            self.assertEqual(manifest.read_bytes(), source_manifest)

            checksums = repo / "dist/SHA256SUMS"
            checksum = checksums.read_text().splitlines()[0]
            tampered = ("1" if checksum[0] == "0" else "0") + checksum[1:]
            checksums.write_text(checksums.read_text().replace(checksum, tampered, 1))
            result = subprocess.run(
                [sys.executable, "scripts/release.py", "verify", "--tag", "v0.9.0"],
                cwd=repo,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Checksum mismatch", result.stderr)

    def test_preflight_rejects_invalid_moved_unmerged_and_non_increasing_tags(self):
        commit = "1" * 40
        cases = [
            ("v1.0", [], "Expected a stable version tag"),
            (
                "v0.6.0",
                [{"sha": "2" * 40}, {"status": "identical"}, [[]]],
                "Tag no longer points to the tested commit",
            ),
            (
                "v0.6.0",
                [{"sha": commit}, {"status": "behind"}, [[]]],
                "Release commit must already be merged into main",
            ),
            (
                "v0.6.0",
                [
                    {"sha": commit},
                    {"status": "identical"},
                    [[{"tag_name": "v0.7.0", "draft": False, "prerelease": False}]],
                ],
                "A newer stable release already exists: v0.7.0",
            ),
        ]
        for tag, responses, expected in cases:
            with self.subTest(tag=tag):
                api = mock.Mock(side_effect=responses)
                with mock.patch.object(release, "api", api):
                    with self.assertRaisesRegex(ValueError, expected):
                        release.preflight("owner/repo", tag, commit)

    def write_bundle(self, directory):
        directory.mkdir()
        plugin = directory / "recto-plugin-0.6.0.zip"
        with ZipFile(plugin, "w", ZIP_DEFLATED) as archive:
            item = ZipInfo("plugin.json")
            item.compress_type = ZIP_DEFLATED
            archive.writestr(item, json.dumps({"version": "0.6.0"}))
        for name in ("recto-skill.zip", "study-notes-skill.zip"):
            with ZipFile(directory / name, "w"):
                pass
        checksums = "".join(
            f"{release.sha256((directory / name).read_bytes()).hexdigest()}  {name}\n"
            for name in ("recto-plugin-0.6.0.zip", "recto-skill.zip", "study-notes-skill.zip")
        )
        (directory / "SHA256SUMS").write_text(checksums)
        release.verify(directory, "v0.6.0")
        return directory

    def published_release(self, directory, extra_asset=False):
        assets = [
            {
                "name": path.name,
                "state": "uploaded",
                "size": path.stat().st_size,
                "digest": "sha256:" + release.sha256(path.read_bytes()).hexdigest(),
            }
            for path in sorted(directory.iterdir())
        ]
        if extra_asset:
            assets.append({"name": "unexpected.zip", "state": "uploaded", "size": 1, "digest": "sha256:" + "0" * 64})
        return {
            "tag_name": "v0.6.0",
            "html_url": "https://github.com/owner/repo/releases/tag/v0.6.0",
            "draft": False,
            "prerelease": False,
            "target_commitish": "1" * 40,
            "assets": assets,
        }

    def responses(self, release_data, current_release=None):
        return {
            "repos/owner/repo/commits/v0.6.0": {"sha": "1" * 40},
            f"repos/owner/repo/compare/{'1' * 40}...main": {"status": "identical"},
            "repos/owner/repo/releases?per_page=100": [[current_release]] if current_release else [[]],
            "repos/owner/repo/releases/tags/v0.6.0": release_data,
        }

    def api_router(self, responses):
        updates = []

        def api(path, payload=None, paginate=False):
            if payload is not None:
                updates.append((path, payload))
                return {"commit": {"sha": "3" * 40}}
            return responses[path]

        return api, updates

    def test_matching_published_retry_downloads_without_upload_create_or_edit(self):
        with self.temporary_directory() as temporary:
            directory = self.write_bundle(Path(temporary) / "dist")
            published = self.published_release(directory)
            manifest = json.loads((ROOT / "plugin.json").read_text())
            content = b64encode((json.dumps({**manifest, "version": "0.5.1"}) + "\n").encode()).decode()
            responses = self.responses(published, published) | {
                "repos/owner/repo/contents/plugin.json?ref=main": {
                    "sha": "blob-sha",
                    "content": content,
                },
            }
            commands = []

            def run(*args, **kwargs):
                commands.append(args)
                output = Path(args[args.index("--dir") + 1])
                for path in directory.iterdir():
                    shutil.copyfile(path, output / path.name)
                return ""

            api, updates = self.api_router(responses)
            environment = {"TMPDIR": str(ROOT / "output")}
            with mock.patch.dict(release.os.environ, environment), mock.patch.object(release, "api", api), mock.patch.object(release, "run", run), contextlib.redirect_stdout(io.StringIO()):
                release.publish("owner/repo", "v0.6.0", "1" * 40, directory)

            self.assertEqual([command[:3] for command in commands], [("gh", "release", "download")])
            (path, update), = updates
            self.assertEqual(path, "repos/owner/repo/contents/plugin.json")
            self.assertEqual(update["sha"], "blob-sha")

    def test_first_publication_download_failure_never_edits_publishes_or_syncs_main(self):
        with self.temporary_directory() as temporary:
            directory = self.write_bundle(Path(temporary) / "dist")
            draft = self.published_release(directory) | {"draft": True, "target_commitish": "main"}
            cases = [("new release", None), ("existing draft", draft)]
            for name, existing in cases:
                with self.subTest(name):
                    commands = []

                    def run(*args, **kwargs):
                        commands.append(args[:3])
                        if args[:3] == ("gh", "release", "download"):
                            output = Path(args[args.index("--dir") + 1])
                            for path in directory.iterdir():
                                shutil.copyfile(path, output / path.name)
                            checksum = (output / "SHA256SUMS").read_text().splitlines()[0]
                            tampered = ("1" if checksum[0] == "0" else "0") + checksum[1:]
                            (output / "SHA256SUMS").write_text((output / "SHA256SUMS").read_text().replace(checksum, tampered, 1))
                        return ""

                    api, updates = self.api_router(self.responses(draft, existing))
                    environment = {"TMPDIR": str(ROOT / "output")}
                    with mock.patch.object(release, "api", api), mock.patch.object(release, "run", run):
                        with mock.patch.dict(release.os.environ, environment), self.assertRaisesRegex(ValueError, "Checksum mismatch: recto-plugin-0.6.0.zip"):
                            release.publish("owner/repo", "v0.6.0", "1" * 40, directory)

                    expected = [("gh", "release", "upload"), ("gh", "release", "download")]
                    if existing is None:
                        expected.insert(0, ("gh", "release", "create"))
                    self.assertEqual(commands, expected)
                    self.assertEqual(updates, [])

    def test_mismatched_published_assets_fail_before_release_commands(self):
        with self.temporary_directory() as temporary:
            directory = self.write_bundle(Path(temporary) / "dist")
            cases = [
                ("extra asset", lambda assets: assets + [{"name": "unexpected.zip", "state": "uploaded", "size": 1, "digest": "sha256:" + "0" * 64}], "asset set differs"),
                ("wrong digest", lambda assets: [asset | {"digest": "sha256:" + "0" * 64} if asset["name"] == "SHA256SUMS" else asset for asset in assets], "Remote release asset differs: SHA256SUMS"),
            ]
            for name, damage, expected in cases:
                with self.subTest(name):
                    published = self.published_release(directory)
                    published["assets"] = damage(published["assets"])
                    responses = self.responses(published, published)

                    def run(*args, **kwargs):
                        raise AssertionError("remote mutation or download ran before asset verification")

                    api, _ = self.api_router(responses)
                    with mock.patch.object(release, "api", api), mock.patch.object(release, "run", run):
                        with self.assertRaisesRegex(ValueError, expected):
                            release.publish("owner/repo", "v0.6.0", "1" * 40, directory)

    def test_sync_preserves_manifest_and_uses_current_blob_sha_without_downgrade(self):
        manifest = json.loads((ROOT / "plugin.json").read_text())
        current = {
            "sha": "current-blob",
            "content": b64encode((json.dumps({**manifest, "version": "0.5.1"}) + "\n").encode()).decode(),
        }
        calls = []

        def api(path, payload=None):
            calls.append((path, payload))
            return current

        with mock.patch.object(release, "api", api):
            for requested in ("v0.5.1", "v0.4.0", "v0.6.0"):
                release.sync_version("owner/repo", requested)

        self.assertEqual(calls[:-1], [("repos/owner/repo/contents/plugin.json?ref=main", None)] * 3)
        self.assertEqual(calls[-1][0], "repos/owner/repo/contents/plugin.json")
        payload = calls[-1][1]
        self.assertEqual(payload["sha"], "current-blob")
        updated = json.loads(b64decode(payload["content"]))
        self.assertEqual(updated["version"], "0.6.0")
        for key, value in manifest.items():
            if key != "version":
                self.assertEqual(updated[key], value)


if __name__ == "__main__":
    unittest.main()

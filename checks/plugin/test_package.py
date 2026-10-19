"""The distributable plugin must include every installable skill, without QA data."""
from pathlib import Path
import subprocess
import sys
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]


class PluginPackageTests(unittest.TestCase):
    def test_package_delivers_both_skills(self):
        result = subprocess.run(
            [sys.executable, "scripts/plugin.py", "package"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        with ZipFile(result.stdout.strip()) as archive:
            self.assertIsNone(archive.testzip())
            names = set(archive.namelist())
            for skill in ("recto", "study-notes"):
                prefix = f"skills/{skill}/"
                self.assertIn(prefix + "SKILL.md", names)
                self.assertIn(prefix + "agents/openai.yaml", names)
                for path in (ROOT / prefix).rglob("*"):
                    if path.is_file() and "__pycache__" not in path.parts and path.name != ".DS_Store":
                        self.assertEqual(archive.read(path.relative_to(ROOT).as_posix()), path.read_bytes())
            self.assertFalse(any(name.startswith(("checks/", "output/", "archive/", "docs/study-notes/")) for name in names))


if __name__ == "__main__":
    unittest.main()

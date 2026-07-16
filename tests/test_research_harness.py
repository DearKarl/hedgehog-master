from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "hedgehog-master" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import research_harness as harness  # noqa: E402


class ResearchHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_projects_dir = harness.PROJECTS_DIR
        harness.PROJECTS_DIR = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        harness.PROJECTS_DIR = self.original_projects_dir
        self.temp_dir.cleanup()

    def test_demo_project_has_valid_cross_file_references(self) -> None:
        project = harness.initialize_project("demo", title="Demo", demo=True)

        report = harness.validate_project(project)

        self.assertTrue(report.ok, report.errors)
        self.assertEqual(report.warnings, [])

    def test_unknown_source_reference_fails_validation(self) -> None:
        project = harness.initialize_project("demo", title="Demo", demo=True)
        claims_path = project / "research" / "claims.json"
        claims = json.loads(claims_path.read_text(encoding="utf-8"))
        claims["claims"][0]["source_ids"] = ["missing-source"]
        harness.write_json(claims_path, claims)

        report = harness.validate_project(project)

        self.assertFalse(report.ok)
        self.assertIn("unknown source missing-source", "\n".join(report.errors))

    def test_unregistered_layout_fails_validation(self) -> None:
        project = harness.initialize_project("demo", title="Demo", demo=True)
        deck_path = project / "storyboard" / "deck.json"
        deck = json.loads(deck_path.read_text(encoding="utf-8"))
        deck["slides"][0]["layout"] = "marketing-hero"
        harness.write_json(deck_path, deck)

        report = harness.validate_project(project)

        self.assertFalse(report.ok)
        self.assertIn("unregistered layout marketing-hero", "\n".join(report.errors))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "hedgehog-master" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import research_harness as harness  # noqa: E402
import research_template  # noqa: E402


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

    def test_unified_intake_registers_brief_paper_and_code(self) -> None:
        project = harness.initialize_project(
            "intake",
            title="Unified Intake",
            brief="Explain the method and its implementation.",
            paper_uploads=[harness.UploadedFile("paper.pdf", "application/pdf", b"paper")],
            code_uploads=[harness.UploadedFile("pipeline.py", "text/x-python", b"print('ok')\n")],
        )

        manifest = harness.load_json(project / "project.json")
        sources = harness.load_json(project / "research" / "sources.json")["sources"]
        report = harness.validate_project(project)

        self.assertEqual(manifest["schema_version"], "1.1")
        self.assertEqual(manifest["brief"]["instructions"], "Explain the method and its implementation.")
        self.assertEqual([item["kind"] for item in manifest["inputs"]], ["paper", "code"])
        self.assertEqual([item["type"] for item in sources], ["local", "paper", "code"])
        self.assertEqual(sources[0]["id"], "brief")
        self.assertTrue(report.ok, report.errors)

    def test_auto_plan_extracts_evidence_code_diagram_and_formula(self) -> None:
        paper = b"""# Reliable Scientific Pipelines

Our framework improves benchmark accuracy by 12% while reducing runtime by 20 ms.
The governing objective is $E = mc^2$.

References
1. A sufficiently long reference entry for deterministic parser coverage.
"""
        code = b"""def load_data():
    return []

def train_model():
    data = load_data()
    return data

def export_results():
    return train_model()
"""
        project = harness.initialize_project(
            "planned",
            title="Planned Research Deck",
            brief="Show the system architecture and evidence in formal academic English.",
            paper_uploads=[harness.UploadedFile("paper.md", "text/markdown", paper)],
            code_uploads=[harness.UploadedFile("pipeline.py", "text/x-python", code)],
        )

        sources = harness.load_json(project / "research" / "sources.json")["sources"]
        claims = harness.load_json(project / "research" / "claims.json")["claims"]
        deck = harness.load_json(project / "storyboard" / "deck.json")["slides"]
        diagram = harness.load_json(project / "research" / "diagrams" / "planned.diagram.json")
        formulas = harness.load_json(project / "images" / "formula_manifest.json")["items"]
        manifest = harness.load_json(project / "project.json")
        report = harness.validate_project(project)

        self.assertEqual([source["id"] for source in sources], ["brief", "paper-1", "code-1"])
        self.assertTrue(any(claim.get("citations") for claim in claims))
        self.assertFalse(any("##" in claim["text"] for claim in claims))
        self.assertGreaterEqual(len(deck), 5)
        self.assertEqual(diagram["kind"], "architecture")
        self.assertEqual(diagram["irVersion"], "0.2")
        self.assertEqual(formulas[0]["latex"], "E = mc^2")
        self.assertEqual(manifest["contracts"]["plan"], "analysis/plan.json")
        self.assertTrue(report.ok, report.errors)

    def test_brief_can_select_cycle_diagram(self) -> None:
        project = harness.initialize_project(
            "cycle",
            title="Iterative Optimization",
            brief="Create a cycle: collect data -> analyze evidence -> revise the model -> validate results.",
        )

        diagram = harness.load_json(project / "research" / "diagrams" / "planned.diagram.json")

        self.assertEqual(diagram["kind"], "cycle")
        self.assertEqual(diagram["direction"], "clockwise")
        self.assertEqual(diagram["edges"][-1]["to"], diagram["nodes"][0]["id"])

    def test_formula_text_remains_editable(self) -> None:
        self.assertEqual(harness.editable_formula_text(r"E = mc^2"), "E = mc²")
        self.assertEqual(harness.editable_formula_text(r"\frac{a}{b} \leq 1"), "(a)/(b) <= 1")

    def test_template_contract_maps_semantic_layouts_and_slots(self) -> None:
        manifest = {
            "slideSize": {"width_px": 1280, "height_px": 720},
            "theme": {"colors": {"accent1": "#123456"}, "fonts": {"minorLatin": "Inter"}},
            "masters": [
                {
                    "path": "ppt/slideMasters/slideMaster1.xml",
                    "svgFile": "master_01.svg",
                    "placeholders": [],
                }
            ],
            "layouts": [
                {
                    "name": "title.xml",
                    "displayName": "Title Slide",
                    "layoutType": "title",
                    "svgFile": "layout_01.svg",
                    "parentPath": "ppt/slideMasters/slideMaster1.xml",
                    "placeholders": [
                        {"semanticRole": "title", "geometry": {"x": 100, "y": 120, "width": 900, "height": 180}},
                        {"semanticRole": "subtitle", "geometry": {"x": 100, "y": 340, "width": 760, "height": 100}},
                    ],
                },
                {
                    "name": "content.xml",
                    "displayName": "Title and Content",
                    "layoutType": "obj",
                    "svgFile": "layout_02.svg",
                    "parentPath": "ppt/slideMasters/slideMaster1.xml",
                    "placeholders": [
                        {"semanticRole": "title", "geometry": {"x": 60, "y": 40, "width": 1100, "height": 90}},
                        {"semanticRole": "object", "geometry": {"x": 60, "y": 160, "width": 1160, "height": 500}},
                    ],
                },
            ],
        }

        contract = research_template.build_contract(manifest, "inputs/template/lab.pptx")

        self.assertEqual(contract["layouts"]["cover"]["source_layout"], "Title Slide")
        self.assertEqual(contract["layouts"]["diagram"]["source_layout"], "Title and Content")
        self.assertEqual(contract["layouts"]["diagram"]["slots"]["content"]["width"], 1160.0)

    def test_template_background_removes_placeholder_projections(self) -> None:
        project = harness.initialize_project("background", title="Background")
        layer = project / "template" / "workspace" / "svg" / "master_01.svg"
        layer.parent.mkdir(parents=True, exist_ok=True)
        layer.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><rect id="brand" width="1280" height="12"/>'
            '<g data-ph-type="title"><rect id="placeholder" width="400" height="100"/></g></svg>',
            encoding="utf-8",
        )
        template = {
            "layouts": {
                "cover": {"background_layers": ["template/workspace/svg/master_01.svg"]}
            }
        }

        background = harness.template_background(project, template, "cover")

        self.assertIn("brand", background)
        self.assertNotIn("placeholder", background)

    def test_workbench_version_and_bilingual_controls_are_registered(self) -> None:
        index = (harness.REPO_ROOT / "index.html").read_text(encoding="utf-8")

        self.assertEqual(harness.APP_VERSION, "0.2.1-beta")
        self.assertEqual(harness.WorkbenchHandler.server_version, "HedgehogMaster/0.2.1-beta")
        self.assertIn('data-language="en"', index)
        self.assertIn('data-language="zh"', index)
        self.assertIn('id="help-dialog"', index)
        self.assertIn('id="changelog-dialog"', index)
        self.assertIn('href="/assets/branding/hm-mark.svg"', index)
        self.assertIn('class="brand-mark" href="/"', index)

    def test_project_validation_supports_a_symlinked_projects_directory(self) -> None:
        real_projects = Path(self.temp_dir.name) / "shared-projects"
        linked_projects = Path(self.temp_dir.name) / "runtime" / "projects"
        real_projects.mkdir()
        linked_projects.parent.mkdir()
        linked_projects.symlink_to(real_projects, target_is_directory=True)
        harness.PROJECTS_DIR = linked_projects

        project = harness.initialize_project("linked-demo", title="Linked Demo", demo=True)
        report = harness.validate_project(project)

        self.assertTrue(report.ok, report.errors)


if __name__ == "__main__":
    unittest.main()

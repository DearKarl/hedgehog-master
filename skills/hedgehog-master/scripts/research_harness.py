#!/usr/bin/env python3
"""Deterministic research-deck harness for Hedgehog Master."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from xml.etree import ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent
PROJECTS_DIR = REPO_ROOT / "projects"
RESEARCH_DIR = SKILL_DIR / "research"
SCHEMAS_DIR = RESEARCH_DIR / "schemas"
PROFILES_DIR = RESEARCH_DIR / "profiles"
DIAGRAM_PACKAGE = REPO_ROOT / "packages" / "diagram-ir"


class HarnessError(RuntimeError):
    """A user-facing harness failure."""


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HarnessError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HarnessError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "research-project"


def project_path_for(value: str | Path) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECTS_DIR / candidate
    return candidate.resolve()


def ensure_project_path(value: str | Path) -> Path:
    project = project_path_for(value)
    try:
        project.relative_to(PROJECTS_DIR.resolve())
    except ValueError as exc:
        raise HarnessError(f"Project must live under {PROJECTS_DIR}") from exc
    return project


def validate_schema(payload: Any, schema_name: str, report: ValidationReport) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise HarnessError("Missing dependency: install requirements.txt to enable validation") from exc

    schema = load_json(SCHEMAS_DIR / schema_name)
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda item: tuple(str(part) for part in item.path),
    )
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        report.errors.append(f"{schema_name}:{location}: {error.message}")


def profile_path(profile_id: str) -> Path:
    path = PROFILES_DIR / f"{slugify(profile_id)}.json"
    if not path.is_file():
        available = ", ".join(item.stem for item in sorted(PROFILES_DIR.glob("*.json")))
        raise HarnessError(f"Unknown profile '{profile_id}'. Available: {available}")
    return path


def demo_payloads(project_id: str, title: str) -> dict[str, Any]:
    project = {
        "$schema": "../../skills/hedgehog-master/research/schemas/project.schema.json",
        "schema_version": "1.0",
        "id": project_id,
        "title": title,
        "audience": "Research engineers and academic collaborators",
        "venue": "Lab meeting",
        "language": "en",
        "profile": "academic-conference",
        "canvas": "ppt169",
        "policy": {
            "authoring_mode": "structured-semantics-only",
            "require_claim_evidence": True,
            "citation_style": "numeric",
        },
    }
    sources = {
        "$schema": "../../../skills/hedgehog-master/research/schemas/sources.schema.json",
        "schema_version": "1.0",
        "sources": [
            {
                "id": "src-architecture",
                "title": "Hedgehog Master architecture contract",
                "type": "local",
                "locator": "docs/architecture/autoresearch-ppt.md",
            }
        ],
    }
    claims = {
        "$schema": "../../../skills/hedgehog-master/research/schemas/claims.schema.json",
        "schema_version": "1.0",
        "claims": [
            {
                "id": "claim-structured-boundary",
                "text": "Rendering is deterministic once the semantic research specification is fixed.",
                "status": "verified",
                "source_ids": ["src-architecture"],
                "evidence": "The compiler accepts typed manifests and Diagram IR rather than generated layout code.",
            }
        ],
    }
    deck = {
        "$schema": "../../../skills/hedgehog-master/research/schemas/deck.schema.json",
        "schema_version": "1.0",
        "slides": [
            {
                "id": "cover",
                "layout": "cover",
                "title": title,
                "subtitle": "A deterministic pipeline for evidence-linked research communication",
            },
            {
                "id": "pipeline",
                "layout": "diagram",
                "title": "From evidence to editable presentation artifacts",
                "subtitle": "The model supplies semantics; compilers own geometry and export.",
                "diagram": "research/diagrams/pipeline.diagram.json",
                "claim_ids": ["claim-structured-boundary"],
            },
            {
                "id": "evidence",
                "layout": "evidence",
                "title": "Every substantive statement remains traceable",
                "claim_ids": ["claim-structured-boundary"],
            },
            {
                "id": "closing",
                "layout": "closing",
                "title": "Structured first. Editable by default.",
                "subtitle": "Publication SVG and native PPTX from one research contract.",
            },
        ],
    }
    diagram = {
        "irVersion": "0.1a",
        "id": "research-pipeline",
        "title": "AutoResearch pipeline",
        "kind": "dataflow",
        "direction": "left-to-right",
        "nodes": [
            {"id": "sources", "label": "Research sources", "role": "source"},
            {"id": "claims", "label": "Evidence-linked claims", "role": "transform"},
            {"id": "storyboard", "label": "Semantic storyboard", "role": "model"},
            {"id": "quality", "label": "Academic quality gates", "role": "metric"},
            {"id": "exports", "label": "SVG and editable PPTX", "role": "output"},
        ],
        "edges": [
            {"id": "sources-claims", "from": "sources", "to": "claims", "evidenceRef": "src-architecture"},
            {"id": "claims-storyboard", "from": "claims", "to": "storyboard"},
            {"id": "storyboard-quality", "from": "storyboard", "to": "quality"},
            {"id": "quality-exports", "from": "quality", "to": "exports"},
        ],
        "metadata": {"evidence": {"src-architecture": "Local architecture contract"}},
    }
    return {"project": project, "sources": sources, "claims": claims, "deck": deck, "diagram": diagram}


def initialize_project(
    name: str,
    title: str | None = None,
    audience: str = "Academic audience",
    venue: str = "Research presentation",
    profile: str = "academic-conference",
    demo: bool = False,
) -> Path:
    project_id = slugify(name)
    project = ensure_project_path(project_id)
    if project.exists():
        raise HarnessError(f"Project already exists: {project}")
    profile_path(profile)

    for relative in (
        "research/diagrams",
        "research/figures",
        "storyboard",
        "quality",
        "svg_output",
        "svg_final",
        "exports",
        "notes",
        "sources",
    ):
        (project / relative).mkdir(parents=True, exist_ok=True)

    resolved_title = title or name.replace("-", " ").title()
    payloads = demo_payloads(project_id, resolved_title)
    payloads["project"]["audience"] = audience
    payloads["project"]["venue"] = venue
    payloads["project"]["profile"] = profile

    if not demo:
        payloads["sources"]["sources"] = []
        payloads["claims"]["claims"] = []
        payloads["deck"]["slides"] = [
            {
                "id": "cover",
                "layout": "cover",
                "title": resolved_title,
                "subtitle": "Research presentation",
            }
        ]

    write_json(project / "project.json", payloads["project"])
    write_json(project / "research" / "sources.json", payloads["sources"])
    write_json(project / "research" / "claims.json", payloads["claims"])
    write_json(project / "storyboard" / "deck.json", payloads["deck"])
    if demo:
        write_json(project / "research" / "diagrams" / "pipeline.diagram.json", payloads["diagram"])
    (project / "README.md").write_text(
        f"# {resolved_title}\n\nResearch project managed by Hedgehog Master.\n",
        encoding="utf-8",
    )
    return project


def validate_project(project: Path) -> ValidationReport:
    report = ValidationReport()
    try:
        manifest = load_json(project / "project.json")
        sources = load_json(project / "research" / "sources.json")
        claims = load_json(project / "research" / "claims.json")
        deck = load_json(project / "storyboard" / "deck.json")
    except HarnessError as exc:
        report.errors.append(str(exc))
        return report

    validate_schema(manifest, "project.schema.json", report)
    validate_schema(sources, "sources.schema.json", report)
    validate_schema(claims, "claims.schema.json", report)
    validate_schema(deck, "deck.schema.json", report)

    source_ids = {item.get("id") for item in sources.get("sources", [])}
    claim_ids = {item.get("id") for item in claims.get("claims", [])}
    for claim in claims.get("claims", []):
        for source_id in claim.get("source_ids", []):
            if source_id not in source_ids:
                report.errors.append(f"Claim {claim.get('id')} references unknown source {source_id}")
        if claim.get("status") != "verified":
            report.warnings.append(f"Claim {claim.get('id')} is not verified")

    valid_layouts = set(load_json(profile_path(manifest.get("profile", ""))).get("layouts", []))
    for slide in deck.get("slides", []):
        slide_id = slide.get("id", "<unknown>")
        if slide.get("layout") not in valid_layouts:
            report.errors.append(f"Slide {slide_id} uses unregistered layout {slide.get('layout')}")
        for claim_id in slide.get("claim_ids", []):
            if claim_id not in claim_ids:
                report.errors.append(f"Slide {slide_id} references unknown claim {claim_id}")
        diagram = slide.get("diagram")
        if diagram:
            diagram_path = (project / diagram).resolve()
            try:
                diagram_path.relative_to(project)
            except ValueError:
                report.errors.append(f"Slide {slide_id} diagram escapes the project directory")
            else:
                if not diagram_path.is_file():
                    report.errors.append(f"Slide {slide_id} diagram is missing: {diagram}")
    return report


def resolve_executable(name: str, environment_name: str) -> str:
    configured = os.environ.get(environment_name)
    if configured and Path(configured).is_file():
        return configured
    executable = shutil.which(name)
    if executable:
        return executable
    raise HarnessError(f"Missing executable '{name}'. Set {environment_name} or add it to PATH.")


def run_checked(command: list[str], cwd: Path = REPO_ROOT) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        details = (result.stderr or result.stdout).strip()
        raise HarnessError(details or f"Command failed: {' '.join(command)}")


def compile_diagram(input_path: Path, output_path: Path) -> None:
    node = resolve_executable("node", "HEDGEHOG_NODE")
    cli = DIAGRAM_PACKAGE / "dist" / "cli.js"
    if not cli.is_file():
        pnpm = resolve_executable("pnpm", "HEDGEHOG_PNPM")
        run_checked([pnpm, "--dir", str(DIAGRAM_PACKAGE), "build"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_checked([node, str(cli), "compile", str(input_path), "-o", str(output_path)])


def svg_text(x: int, y: int, value: str, size: int, color: str, weight: int = 400) -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Aptos, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(value)}</text>'
    )


def wrapped_text(x: int, y: int, value: str, size: int, color: str, width: int, line_height: int) -> str:
    lines = textwrap.wrap(value, width=max(12, width // max(8, int(size * 0.55)))) or [""]
    tspans = "".join(
        f'<tspan x="{x}" dy="{0 if index == 0 else line_height}">{html.escape(line)}</tspan>'
        for index, line in enumerate(lines)
    )
    return (
        f'<text x="{x}" y="{y}" font-family="Aptos, Arial, sans-serif" '
        f'font-size="{size}" fill="{color}">{tspans}</text>'
    )


def page_shell(content: str, page_number: int, project_title: str, colors: dict[str, str]) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">\n'
        f'  <rect x="0" y="0" width="1280" height="720" fill="{colors["background"]}"/>\n'
        f'  <rect x="0" y="0" width="1280" height="8" fill="{colors["accent"]}"/>\n'
        f'  {svg_text(56, 46, "HEDGEHOG MASTER  /  AUTORESEARCH-PPT", 13, colors["muted"], 600)}\n'
        f'  {content}\n'
        f'  {svg_text(56, 690, project_title, 11, colors["muted"])}\n'
        f'  {svg_text(1200, 690, f"{page_number:02d}", 11, colors["muted"], 600)}\n'
        '</svg>\n'
    )


def format_svg_number(value: float) -> str:
    rounded = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if rounded in {"", "-0"} else rounded


def extract_svg_body(
    path: Path,
    left: float = 80,
    top: float = 196,
    width: float = 1120,
    height: float = 430,
) -> str:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise HarnessError(f"Compiled diagram is not valid SVG: {path}") from exc

    namespace = "http://www.w3.org/2000/svg"
    ET.register_namespace("", namespace)

    points: list[tuple[float, float]] = []
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name == "rect" and element.get("id") != "background":
            x = float(element.get("x", "0"))
            y = float(element.get("y", "0"))
            rect_width = float(element.get("width", "0"))
            rect_height = float(element.get("height", "0"))
            points.extend(((x, y), (x + rect_width, y + rect_height)))
        elif local_name == "polyline":
            for raw_point in element.get("points", "").split():
                pair = raw_point.split(",", 1)
                if len(pair) != 2:
                    raise HarnessError(f"Compiled diagram has an invalid polyline point: {path}")
                points.append((float(pair[0]), float(pair[1])))

    if not points:
        raise HarnessError(f"Compiled diagram has no visible geometry: {path}")
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    source_padding = 50.0
    source_width = max_x - min_x + source_padding * 2
    source_height = max_y - min_y + source_padding * 2
    scale = min(width / source_width, height / source_height)
    offset_x = left + (width - source_width * scale) / 2 - (min_x - source_padding) * scale
    offset_y = top + (height - source_height * scale) / 2 - (min_y - source_padding) * scale

    def transform_x(value: str) -> str:
        return format_svg_number(float(value) * scale + offset_x)

    def transform_y(value: str) -> str:
        return format_svg_number(float(value) * scale + offset_y)

    def transform_length(value: str) -> str:
        return format_svg_number(float(value) * scale)

    for child in list(root):
        if child.get("id") == "background":
            root.remove(child)

    def adapt(element: ET.Element, in_defs: bool = False) -> None:
        local_name = element.tag.rsplit("}", 1)[-1]
        inside_defs = in_defs or local_name == "defs"
        if not inside_defs:
            if local_name == "polyline":
                raw_points = element.attrib.pop("points", "").split()
                if len(raw_points) < 2:
                    raise HarnessError(f"Compiled diagram has an invalid polyline: {path}")
                coordinates = [raw_point.split(",", 1) for raw_point in raw_points]
                element.tag = f"{{{namespace}}}path"
                element.set(
                    "d",
                    "M " + " L ".join(
                        f"{transform_x(x)} {transform_y(y)}" for x, y in coordinates
                    ),
                )
            elif local_name == "rect":
                for attribute in ("x", "width", "rx"):
                    if attribute in element.attrib:
                        element.set(attribute, transform_x(element.get(attribute, "0")) if attribute == "x" else transform_length(element.get(attribute, "0")))
                for attribute in ("y", "height", "ry"):
                    if attribute in element.attrib:
                        element.set(attribute, transform_y(element.get(attribute, "0")) if attribute == "y" else transform_length(element.get(attribute, "0")))
            elif local_name in {"text", "tspan"}:
                if "x" in element.attrib:
                    element.set("x", transform_x(element.get("x", "0")))
                if "y" in element.attrib:
                    element.set("y", transform_y(element.get("y", "0")))
                if "dy" in element.attrib:
                    element.set("dy", transform_length(element.get("dy", "0")))
                if "font-size" in element.attrib:
                    size = max(14.0, float(element.get("font-size", "16")) * scale)
                    element.set("font-size", format_svg_number(size))
        for child in element:
            adapt(child, inside_defs)

    adapt(root)

    return "\n".join(ET.tostring(child, encoding="unicode") for child in root).strip()


def write_spec_lock(
    project: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    deck: dict[str, Any],
) -> None:
    colors = profile["colors"]
    rhythm_rows = "\n".join(
        f"- P{index:02d}: {'anchor' if slide['layout'] in {'cover', 'closing', 'section'} else 'dense'}"
        for index, slide in enumerate(deck["slides"], start=1)
    )
    chart_rows = "\n".join(
        f"- P{index:02d}: deterministic-dataflow"
        for index, slide in enumerate(deck["slides"], start=1)
        if slide["layout"] == "diagram"
    ) or "- none: none"
    content = f"""# Execution Lock

Generated by Hedgehog Master AutoResearch-PPT from the registered project profile.

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- background: {colors['background']}
- panel: {colors['panel']}
- text: {colors['text']}
- muted: {colors['muted']}
- accent: {colors['accent']}
- secondary: {colors['secondary']}

## typography
- font_family: Aptos, Arial, sans-serif
- title: 36
- body: 18
- annotation: 12

## page_rhythm
{rhythm_rows}

## page_charts
{chart_rows}

## pptx_structure
- mode: flat

## academic_policy
- language: {manifest['language']}
- evidence_required: true
- authoring_mode: structured-semantics-only
"""
    (project / "spec_lock.md").write_text(content, encoding="utf-8")


def render_slide(
    slide: dict[str, Any],
    index: int,
    project: Path,
    manifest: dict[str, Any],
    claims_by_id: dict[str, dict[str, Any]],
    profile: dict[str, Any],
) -> str:
    colors = profile["colors"]
    title = slide["title"]
    subtitle = slide.get("subtitle", "")
    layout = slide["layout"]

    if layout == "cover":
        content = (
            f'<rect x="56" y="118" width="112" height="6" fill="{colors["secondary"]}"/>\n'
            + wrapped_text(56, 210, title, 50, colors["text"], 1040, 60)
            + "\n"
            + wrapped_text(56, 380, subtitle, 24, colors["muted"], 900, 34)
            + "\n"
            + svg_text(56, 578, manifest["venue"], 16, colors["text"], 600)
            + "\n"
            + svg_text(56, 612, manifest["audience"], 14, colors["muted"])
        )
    elif layout == "diagram":
        source = (project / slide["diagram"]).resolve()
        figure = project / "research" / "figures" / f"{source.stem}.svg"
        compile_diagram(source, figure)
        claim_labels = ", ".join(f"[{claim_id}]" for claim_id in slide.get("claim_ids", []))
        content = (
            wrapped_text(56, 112, title, 36, colors["text"], 1120, 42)
            + "\n"
            + wrapped_text(56, 162, subtitle, 17, colors["muted"], 1080, 24)
            + f'\n<rect x="56" y="188" width="1168" height="446" rx="4" fill="{colors["panel"]}"/>\n'
            + extract_svg_body(figure)
            + "\n"
            + svg_text(56, 650, f"Evidence: {claim_labels or 'No claims linked'}", 12, colors["muted"])
        )
    elif layout == "evidence":
        parts = [wrapped_text(56, 112, title, 36, colors["text"], 1120, 42)]
        y = 190
        for claim_id in slide.get("claim_ids", []):
            claim = claims_by_id[claim_id]
            parts.append(f'<rect x="56" y="{y - 28}" width="1168" height="122" rx="4" fill="{colors["panel"]}"/>')
            parts.append(svg_text(80, y, f"[{claim_id}]  {claim['status'].upper()}", 13, colors["accent"], 700))
            parts.append(wrapped_text(80, y + 34, claim["text"], 20, colors["text"], 1080, 28))
            sources = ", ".join(claim.get("source_ids", []))
            parts.append(svg_text(80, y + 82, f"Sources: {sources}", 12, colors["muted"]))
            y += 146
        content = "\n".join(parts)
    elif layout in {"closing", "section"}:
        content = (
            f'<rect x="56" y="146" width="72" height="72" fill="{colors["secondary"]}"/>\n'
            + wrapped_text(56, 330, title, 46, colors["text"], 1050, 56)
            + "\n"
            + wrapped_text(56, 460, subtitle, 22, colors["muted"], 960, 32)
        )
    else:
        raise HarnessError(f"Unsupported deterministic layout: {layout}")
    return page_shell(content, index, manifest["title"], colors)


def build_project(project: Path) -> list[Path]:
    report = validate_project(project)
    if report.errors:
        raise HarnessError("Validation failed:\n- " + "\n- ".join(report.errors))

    manifest = load_json(project / "project.json")
    profile = load_json(profile_path(manifest["profile"]))
    claims = load_json(project / "research" / "claims.json")["claims"]
    deck = load_json(project / "storyboard" / "deck.json")
    claims_by_id = {claim["id"]: claim for claim in claims}
    write_spec_lock(project, manifest, profile, deck)
    output_dir = project / "svg_output"
    output_dir.mkdir(exist_ok=True)
    for old_svg in output_dir.glob("*.svg"):
        old_svg.unlink()

    outputs = []
    for index, slide in enumerate(deck["slides"], start=1):
        output = output_dir / f"slide_{index:02d}_{slugify(slide['id'])}.svg"
        output.write_text(
            render_slide(slide, index, project, manifest, claims_by_id, profile),
            encoding="utf-8",
        )
        outputs.append(output)
    write_json(
        project / "quality" / "build.json",
        {
            "schema_version": "1.0",
            "built_on": date.today().isoformat(),
            "slides": [path.name for path in outputs],
            "warnings": report.warnings,
        },
    )
    return outputs


def export_project(project: Path) -> Path:
    build_project(project)
    python = sys.executable
    run_checked([python, str(SCRIPT_DIR / "finalize_svg.py"), str(project), "--quiet"])
    before = set((project / "exports").glob("*.pptx"))
    run_checked([python, str(SCRIPT_DIR / "svg_to_pptx.py"), str(project)])
    created = sorted(set((project / "exports").glob("*.pptx")) - before, key=lambda path: path.stat().st_mtime)
    if not created:
        created = sorted((project / "exports").glob("*.pptx"), key=lambda path: path.stat().st_mtime)
    if not created:
        raise HarnessError("PPTX exporter completed without producing an export")
    return created[-1]


def project_summary(project: Path) -> dict[str, Any]:
    manifest_path = project / "project.json"
    if not manifest_path.is_file():
        raise HarnessError(f"Not a research project: {project}")
    manifest = load_json(manifest_path)
    sources = load_json(project / "research" / "sources.json").get("sources", [])
    claims = load_json(project / "research" / "claims.json").get("claims", [])
    slides = load_json(project / "storyboard" / "deck.json").get("slides", [])
    report = validate_project(project)
    previews = sorted((project / "svg_output").glob("*.svg"))
    return {
        "id": manifest["id"],
        "title": manifest["title"],
        "profile": manifest["profile"],
        "slides": len(slides),
        "sources": len(sources),
        "claims": len(claims),
        "verified_claims": sum(1 for claim in claims if claim.get("status") == "verified"),
        "diagrams": len(list((project / "research" / "diagrams").glob("*.diagram.json"))),
        "exports": len(list((project / "exports").glob("*.pptx"))),
        "status": "ready" if report.ok else "needs-attention",
        "warnings": len(report.warnings),
        "errors": report.errors,
        "preview": str(previews[0].relative_to(REPO_ROOT)) if previews else None,
    }


def list_projects() -> list[dict[str, Any]]:
    projects = []
    for manifest in sorted(PROJECTS_DIR.glob("*/project.json")):
        try:
            projects.append(project_summary(manifest.parent))
        except HarnessError as exc:
            projects.append({"id": manifest.parent.name, "title": manifest.parent.name, "status": "error", "errors": [str(exc)]})
    return projects


class WorkbenchHandler(SimpleHTTPRequestHandler):
    server_version = "HedgehogMaster/1.0"

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise HarnessError("Request body is too large")
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as exc:
            raise HarnessError("Request body must be JSON") from exc

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self.send_json({"repository": "hedgehog-master", "projects": list_projects()})
            return
        if parsed.path == "/api/profiles":
            profiles = [load_json(path) for path in sorted(PROFILES_DIR.glob("*.json"))]
            self.send_json({"profiles": profiles})
            return
        if parsed.path in {"/", "/index.html"}:
            self.path = "/index.html"
            super().do_GET()
            return
        preview_pattern = r"/projects/[a-z0-9]+(?:-[a-z0-9]+)*/(?:svg_output|svg_final)/[A-Za-z0-9_.-]+\.svg"
        if re.fullmatch(preview_pattern, parsed.path):
            super().do_GET()
            return
        self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/api/projects":
                payload = self.read_json_body()
                project = initialize_project(
                    payload.get("name", "research-project"),
                    title=payload.get("title"),
                    audience=payload.get("audience", "Academic audience"),
                    venue=payload.get("venue", "Research presentation"),
                    profile=payload.get("profile", "academic-conference"),
                    demo=bool(payload.get("demo", False)),
                )
                self.send_json(project_summary(project), HTTPStatus.CREATED)
                return
            match = re.fullmatch(r"/api/projects/([^/]+)/(validate|build|export)", parsed.path)
            if match:
                project = ensure_project_path(unquote(match.group(1)))
                action = match.group(2)
                if action == "validate":
                    report = validate_project(project)
                    self.send_json({"ok": report.ok, "errors": report.errors, "warnings": report.warnings})
                elif action == "build":
                    outputs = build_project(project)
                    self.send_json({"ok": True, "slides": [path.name for path in outputs]})
                else:
                    output = export_project(project)
                    self.send_json({"ok": True, "export": str(output.relative_to(REPO_ROOT))})
                return
            self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except HarnessError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # pragma: no cover - defensive server boundary
            self.send_json({"error": f"Internal error: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format_string: str, *args: Any) -> None:
        print(f"[workbench] {format_string % args}")


def serve(host: str, port: int) -> None:
    handler = partial(WorkbenchHandler, directory=str(REPO_ROOT))
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Hedgehog Master workbench: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def print_report(report: ValidationReport) -> None:
    for warning in report.warnings:
        print(f"WARN: {warning}")
    for error in report.errors:
        print(f"ERROR: {error}")
    print("VALID" if report.ok else "INVALID")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hedgehog Master AutoResearch-PPT harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a structured research project")
    init_parser.add_argument("name")
    init_parser.add_argument("--title")
    init_parser.add_argument("--audience", default="Academic audience")
    init_parser.add_argument("--venue", default="Research presentation")
    init_parser.add_argument("--profile", default="academic-conference")
    init_parser.add_argument("--demo", action="store_true", help="Seed a runnable four-slide example")

    for command, help_text in (
        ("validate", "Validate manifests and evidence links"),
        ("build", "Compile deterministic SVG slides"),
        ("export", "Build and export editable PPTX"),
        ("status", "Show project status as JSON"),
    ):
        command_parser = subparsers.add_parser(command, help=help_text)
        command_parser.add_argument("project")

    diagram_parser = subparsers.add_parser("diagram", help="Compile Diagram IR to publication SVG")
    diagram_parser.add_argument("input", type=Path)
    diagram_parser.add_argument("--output", "-o", type=Path, required=True)

    serve_parser = subparsers.add_parser("serve", help="Run the local workbench")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=4173)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            project = initialize_project(
                args.name,
                title=args.title,
                audience=args.audience,
                venue=args.venue,
                profile=args.profile,
                demo=args.demo,
            )
            print(project)
        elif args.command == "validate":
            report = validate_project(ensure_project_path(args.project))
            print_report(report)
            return 0 if report.ok else 1
        elif args.command == "build":
            outputs = build_project(ensure_project_path(args.project))
            print(f"Built {len(outputs)} slide(s)")
        elif args.command == "export":
            print(export_project(ensure_project_path(args.project)))
        elif args.command == "status":
            print(json.dumps(project_summary(ensure_project_path(args.project)), indent=2))
        elif args.command == "diagram":
            compile_diagram(args.input.resolve(), args.output.resolve())
            print(args.output.resolve())
        elif args.command == "serve":
            serve(args.host, args.port)
        return 0
    except HarnessError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

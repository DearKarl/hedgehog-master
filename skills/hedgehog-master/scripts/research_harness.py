#!/usr/bin/env python3
"""Deterministic research-deck harness for Hedgehog Master."""

from __future__ import annotations

import argparse
import copy
import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import date
from email import policy as email_policy
from email.parser import BytesParser
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET

from research_template import TemplateContractError, import_template
from research_planner import plan_project
from provider_settings import (
    CONTENT_PROVIDERS,
    DIAGRAM_PROVIDERS,
    load_settings,
    public_settings,
    resolve_model,
    safe_provider_id,
    save_settings,
    settings_environment,
)


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent
PROJECTS_DIR = REPO_ROOT / "projects"
RESEARCH_DIR = SKILL_DIR / "research"
SCHEMAS_DIR = RESEARCH_DIR / "schemas"
PROFILES_DIR = RESEARCH_DIR / "profiles"
DIAGRAM_PACKAGE = REPO_ROOT / "packages" / "diagram-ir"
VERSION_FILE = REPO_ROOT / "VERSION"
APP_VERSION = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.is_file() else "0.0.0-dev"


class HarnessError(RuntimeError):
    """A user-facing harness failure."""


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class UploadedFile:
    filename: str
    content_type: str
    data: bytes


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


def safe_filename(value: str, fallback: str) -> str:
    name = Path(value).name.strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-.")
    return cleaned[:120] or fallback


def upload_from_path(path: Path) -> UploadedFile:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise HarnessError(f"Input file does not exist: {resolved}")
    media_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
    return UploadedFile(resolved.name, media_type, resolved.read_bytes())


def _unique_destination(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    index = 2
    while candidate.exists():
        candidate = directory / f"{Path(filename).stem}-{index}{Path(filename).suffix}"
        index += 1
    return candidate


def save_input_file(
    project: Path,
    upload: UploadedFile,
    kind: str,
    index: int,
) -> tuple[dict[str, Any], Path]:
    directories = {"template": "template", "paper": "papers", "code": "code"}
    allowed_extensions = {
        "template": {".pptx"},
        "paper": {".pdf", ".docx", ".md", ".txt", ".tex"},
        "code": {".py", ".m", ".r", ".ipynb", ".c", ".cc", ".cpp", ".h", ".hpp", ".java", ".js", ".ts", ".rs", ".go", ".md", ".txt"},
    }
    filename = safe_filename(upload.filename, f"{kind}-{index}.bin")
    extension = Path(filename).suffix.lower()
    if extension not in allowed_extensions[kind]:
        expected = ", ".join(sorted(allowed_extensions[kind]))
        raise HarnessError(f"Unsupported {kind} file '{filename}'. Expected: {expected}")
    directory = project / "inputs" / directories[kind]
    directory.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(directory, filename)
    destination.write_bytes(upload.data)
    language = extension.lstrip(".") if kind == "code" else None
    record = {
        "id": "template" if kind == "template" else f"{kind}-{index}",
        "kind": kind,
        "path": str(destination.relative_to(project)),
        "name": upload.filename or destination.name,
        "media_type": upload.content_type or mimetypes.guess_type(destination.name)[0] or "application/octet-stream",
    }
    if language:
        record["language"] = language
    return record, destination


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
        "schema_version": "1.1",
        "id": project_id,
        "title": title,
        "audience": "Research engineers and academic collaborators",
        "venue": "Lab meeting",
        "language": "en",
        "profile": "academic-conference",
        "canvas": "ppt169",
        "brief": {"instructions": "", "path": "inputs/instructions.md"},
        "inputs": [],
        "contracts": {
            "sources": "research/sources.json",
            "claims": "research/claims.json",
            "storyboard": "storyboard/deck.json",
        },
        "policy": {
            "authoring_mode": "structured-semantics-only",
            "require_claim_evidence": True,
            "citation_style": "numeric",
            "image_generation": "manual",
            "formula_rendering": "editable-text",
            "content_provider": "rules",
            "content_model": "hedgehog-rules-v1",
            "diagram_provider": "rules",
            "diagram_model": "hedgehog-rules-v1",
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
                "locator": "docs/architecture/autoresearch-future.md",
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
    brief: str = "",
    template_upload: UploadedFile | None = None,
    paper_uploads: list[UploadedFile] | None = None,
    code_uploads: list[UploadedFile] | None = None,
    code_text: str = "",
    auto_plan: bool = True,
    image_generation: str = "manual",
    formula_rendering: str = "editable-text",
    content_provider: str = "rules",
    diagram_provider: str = "rules",
) -> Path:
    project_id = slugify(name)
    project = ensure_project_path(project_id)
    if project.exists():
        raise HarnessError(f"Project already exists: {project}")
    profile_path(profile)
    if image_generation not in {"manual", "auto"}:
        raise HarnessError("Image generation must be 'manual' or 'auto'")
    if formula_rendering not in {"editable-text", "raster"}:
        raise HarnessError("Formula rendering must be 'editable-text' or 'raster'")
    content_provider = safe_provider_id(content_provider, CONTENT_PROVIDERS)
    diagram_provider = safe_provider_id(diagram_provider, DIAGRAM_PROVIDERS)
    settings = load_settings()

    for relative in (
        "inputs/template",
        "inputs/papers",
        "inputs/code",
        "template",
        "analysis",
        "images",
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

    try:
        resolved_title = title or name.replace("-", " ").title()
        instructions = brief.strip() or "Create a formal English academic presentation from the registered inputs."
        (project / "inputs" / "instructions.md").write_text(
            f"# Presentation Brief\n\n{instructions}\n",
            encoding="utf-8",
        )
        payloads = demo_payloads(project_id, resolved_title)
        payloads["project"]["audience"] = audience
        payloads["project"]["venue"] = venue
        payloads["project"]["profile"] = profile
        payloads["project"]["brief"]["instructions"] = instructions
        payloads["project"]["policy"]["image_generation"] = image_generation
        payloads["project"]["policy"]["formula_rendering"] = formula_rendering
        payloads["project"]["policy"]["content_provider"] = content_provider
        payloads["project"]["policy"]["content_model"] = resolve_model(settings, content_provider, "content")
        payloads["project"]["policy"]["diagram_provider"] = diagram_provider
        payloads["project"]["policy"]["diagram_model"] = resolve_model(settings, diagram_provider, "diagram")

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

        input_records: list[dict[str, Any]] = []
        template_path: Path | None = None
        if template_upload:
            record, template_path = save_input_file(project, template_upload, "template", 1)
            input_records.append(record)
            payloads["project"]["canvas"] = "template"
            payloads["project"]["contracts"]["template"] = "template/template.json"

        for index, upload in enumerate(paper_uploads or [], start=1):
            record, _ = save_input_file(project, upload, "paper", index)
            input_records.append(record)
            payloads["sources"]["sources"].append(
                {"id": f"paper-{index}", "title": record["name"], "type": "paper", "locator": record["path"]}
            )

        code_inputs = list(code_uploads or [])
        if code_text.strip():
            code_inputs.append(UploadedFile("pasted-code.txt", "text/plain", code_text.encode("utf-8")))
        for index, upload in enumerate(code_inputs, start=1):
            record, _ = save_input_file(project, upload, "code", index)
            input_records.append(record)
            payloads["sources"]["sources"].append(
                {"id": f"code-{index}", "title": record["name"], "type": "code", "locator": record["path"]}
            )
        payloads["project"]["inputs"] = input_records

        write_json(project / "project.json", payloads["project"])
        write_json(project / "research" / "sources.json", payloads["sources"])
        write_json(project / "research" / "claims.json", payloads["claims"])
        write_json(project / "storyboard" / "deck.json", payloads["deck"])
        if demo:
            write_json(project / "research" / "diagrams" / "pipeline.diagram.json", payloads["diagram"])
        if template_path:
            try:
                import_template(project, template_path)
            except TemplateContractError as exc:
                raise HarnessError(f"Cannot analyze PPTX template: {exc}") from exc
        should_plan = auto_plan and (
            bool(brief.strip())
            or bool(paper_uploads)
            or bool(code_inputs)
            or not demo
        )
        if should_plan:
            try:
                plan_project(project)
            except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
                raise HarnessError(f"Cannot derive research plan: {exc}") from exc
        (project / "README.md").write_text(
            f"# {resolved_title}\n\nResearch project managed by Hedgehog Master.\n",
            encoding="utf-8",
        )
        return project
    except Exception:
        shutil.rmtree(project, ignore_errors=True)
        raise


def validate_project(project: Path) -> ValidationReport:
    report = ValidationReport()
    project_root = project.resolve()
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

    for item in manifest.get("inputs", []):
        relative = item.get("path", "")
        input_path = (project / relative).resolve()
        try:
            input_path.relative_to(project_root)
        except ValueError:
            report.errors.append(f"Input {item.get('id')} escapes the project directory")
        else:
            if not input_path.is_file():
                report.errors.append(f"Input {item.get('id')} is missing: {relative}")

    template_relative = (manifest.get("contracts") or {}).get("template")
    if template_relative:
        template_path = (project / template_relative).resolve()
        try:
            template_path.relative_to(project_root)
        except ValueError:
            report.errors.append("Template contract escapes the project directory")
        else:
            try:
                template = load_json(template_path)
            except HarnessError as exc:
                report.errors.append(str(exc))
            else:
                validate_schema(template, "template.schema.json", report)
                for binding in template.get("layouts", {}).values():
                    for layer in binding.get("background_layers", []):
                        layer_path = (project / layer).resolve()
                        try:
                            layer_path.relative_to(project_root)
                        except ValueError:
                            report.errors.append(f"Template layer escapes the project directory: {layer}")
                        else:
                            if not layer_path.is_file():
                                report.errors.append(f"Template layer is missing: {layer}")

    asset_items: dict[str, dict[str, Any]] = {}
    asset_contracts = (
        ("formulas", "formula-manifest.schema.json", {"Rendered"}),
        ("images", "image-manifest.schema.json", {"Generated"}),
    )
    for contract_name, schema_name, file_statuses in asset_contracts:
        relative = (manifest.get("contracts") or {}).get(contract_name)
        if not relative:
            continue
        contract_path = (project / relative).resolve()
        try:
            contract_path.relative_to(project_root)
        except ValueError:
            report.errors.append(f"{contract_name.title()} contract escapes the project directory")
            continue
        try:
            asset_manifest = load_json(contract_path)
        except HarnessError as exc:
            report.errors.append(str(exc))
            continue
        validate_schema(asset_manifest, schema_name, report)
        for item in asset_manifest.get("items", []):
            item_id = item.get("id")
            if item_id in asset_items:
                report.errors.append(f"Duplicate asset id across manifests: {item_id}")
            elif item_id:
                asset_items[item_id] = item
            if item.get("status") not in file_statuses:
                continue
            relative_file = item.get("file") or f"images/{item.get('filename', '')}"
            asset_path = (project / relative_file).resolve()
            try:
                asset_path.relative_to(project_root)
            except ValueError:
                report.errors.append(f"Asset {item_id} escapes the project directory")
            else:
                if not asset_path.is_file():
                    report.errors.append(f"Asset {item_id} is missing: {relative_file}")

    source_ids = {item.get("id") for item in sources.get("sources", [])}
    claim_ids = {item.get("id") for item in claims.get("claims", [])}
    for claim in claims.get("claims", []):
        for source_id in claim.get("source_ids", []):
            if source_id not in source_ids:
                report.errors.append(f"Claim {claim.get('id')} references unknown source {source_id}")
        if claim.get("status") != "verified":
            report.warnings.append(f"Claim {claim.get('id')} is not verified")
        for citation in claim.get("citations", []):
            if citation.get("source_id") not in source_ids:
                report.errors.append(
                    f"Claim {claim.get('id')} citation references unknown source {citation.get('source_id')}"
                )

    valid_layouts = set(load_json(profile_path(manifest.get("profile", ""))).get("layouts", []))
    for slide in deck.get("slides", []):
        slide_id = slide.get("id", "<unknown>")
        if slide.get("layout") not in valid_layouts:
            report.errors.append(f"Slide {slide_id} uses unregistered layout {slide.get('layout')}")
        for claim_id in slide.get("claim_ids", []):
            if claim_id not in claim_ids:
                report.errors.append(f"Slide {slide_id} references unknown claim {claim_id}")
        for field_name in ("formula_ids", "image_ids"):
            for asset_id in slide.get(field_name, []):
                if asset_id not in asset_items:
                    report.errors.append(f"Slide {slide_id} references unknown asset {asset_id}")
        diagram = slide.get("diagram")
        if diagram:
            diagram_path = (project / diagram).resolve()
            try:
                diagram_path.relative_to(project_root)
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
    local_candidates = {
        "node": [
            Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node",
            Path("/opt/homebrew/bin/node"),
            Path("/usr/local/bin/node"),
        ],
        "pnpm": [
            Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm",
            Path("/opt/homebrew/bin/pnpm"),
            Path("/usr/local/bin/pnpm"),
        ],
    }
    for candidate in local_candidates.get(name, []):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
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


def svg_text(
    x: float,
    y: float,
    value: str,
    size: float,
    color: str,
    weight: int = 400,
    font_family: str = "Aptos, Arial, sans-serif",
) -> str:
    return (
        f'<text x="{format_svg_number(x)}" y="{format_svg_number(y)}" '
        f'font-family="{html.escape(font_family, quote=True)}" '
        f'font-size="{format_svg_number(size)}" font-weight="{weight}" '
        f'fill="{color}">{html.escape(value)}</text>'
    )


def wrapped_text(
    x: float,
    y: float,
    value: str,
    size: float,
    color: str,
    width: float,
    line_height: float,
    font_family: str = "Aptos, Arial, sans-serif",
    max_lines: int | None = None,
) -> str:
    lines = textwrap.wrap(value, width=max(12, width // max(8, int(size * 0.55)))) or [""]
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .") + "..."
    tspans = "".join(
        f'<tspan x="{format_svg_number(x)}" dy="{format_svg_number(0 if index == 0 else line_height)}">{html.escape(line)}</tspan>'
        for index, line in enumerate(lines)
    )
    return (
        f'<text x="{format_svg_number(x)}" y="{format_svg_number(y)}" '
        f'font-family="{html.escape(font_family, quote=True)}" '
        f'font-size="{format_svg_number(size)}" fill="{color}">{tspans}</text>'
    )


def page_shell(
    content: str,
    page_number: int,
    project_title: str,
    colors: dict[str, str],
    width: int = 1280,
    height: int = 720,
    font_family: str = "Aptos, Arial, sans-serif",
    background: str = "",
) -> str:
    scale = min(width / 1280, height / 720)
    if background:
        chrome = background
    else:
        chrome = (
            f'  <rect x="0" y="0" width="{width}" height="{height}" fill="{colors["background"]}"/>\n'
            f'  <rect x="0" y="0" width="{width}" height="{format_svg_number(8 * scale)}" fill="{colors["accent"]}"/>\n'
            f'  {svg_text(56 * scale, 46 * scale, "HEDGEHOG MASTER  /  AUTORESEARCH-PPT", 13 * scale, colors["muted"], 600, font_family)}\n'
            f'  {svg_text(56 * scale, height - 30 * scale, project_title, 11 * scale, colors["muted"], font_family=font_family)}\n'
            f'  {svg_text(width - 80 * scale, height - 30 * scale, f"{page_number:02d}", 11 * scale, colors["muted"], 600, font_family)}\n'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n'
        f'{chrome}'
        f'  {content}\n'
        '</svg>\n'
    )


def format_svg_number(value: float) -> str:
    rounded = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if rounded in {"", "-0"} else rounded


def load_template_contract(project: Path, manifest: dict[str, Any]) -> dict[str, Any] | None:
    relative = (manifest.get("contracts") or {}).get("template")
    return load_json(project / relative) if relative else None


def resolve_render_profile(profile: dict[str, Any], template: dict[str, Any] | None) -> dict[str, Any]:
    resolved = copy.deepcopy(profile)
    resolved["font_family"] = "Aptos, Arial, sans-serif"
    if not template:
        return resolved
    theme = template.get("theme") or {}
    colors = theme.get("colors") or {}
    color_mapping = {
        "background": "lt1",
        "panel": "lt2",
        "text": "dk1",
        "muted": "dk2",
        "accent": "accent1",
        "secondary": "accent2",
    }
    for target, source in color_mapping.items():
        value = colors.get(source)
        if isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            resolved["colors"][target] = value.upper()
    fonts = theme.get("fonts") or {}
    preferred = fonts.get("minorLatin") or fonts.get("majorLatin")
    if preferred and not str(preferred).startswith("+"):
        resolved["font_family"] = f"{preferred}, Aptos, Arial, sans-serif"
    return resolved


def _strip_template_placeholders(element: ET.Element) -> None:
    for child in list(element):
        if child.get("data-ph-type") is not None:
            element.remove(child)
            continue
        _strip_template_placeholders(child)


def template_background(project: Path, template: dict[str, Any] | None, layout: str) -> str:
    if not template:
        return ""
    binding = (template.get("layouts") or {}).get(layout) or {}
    fragments: list[str] = []
    for relative in binding.get("background_layers", []):
        path = (project / relative).resolve()
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as exc:
            raise HarnessError(f"Cannot read template background layer: {relative}") from exc
        _strip_template_placeholders(root)
        fragments.extend(ET.tostring(child, encoding="unicode") for child in root)
    return "\n".join(fragments) + ("\n" if fragments else "")


def layout_slot(
    template: dict[str, Any] | None,
    layout: str,
    role: str,
    fallback: tuple[float, float, float, float],
) -> dict[str, float]:
    slot = (((template or {}).get("layouts") or {}).get(layout) or {}).get("slots", {}).get(role)
    if isinstance(slot, dict) and all(key in slot for key in ("x", "y", "width", "height")):
        return {key: float(slot[key]) for key in ("x", "y", "width", "height")}
    x, y, width, height = fallback
    return {"x": x, "y": y, "width": width, "height": height}


def scaled_rect(rect: dict[str, float], inset: float = 0) -> tuple[float, float, float, float]:
    return (
        rect["x"] + inset,
        rect["y"] + inset,
        max(1.0, rect["width"] - inset * 2),
        max(1.0, rect["height"] - inset * 2),
    )


def load_asset_registry(project: Path, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for contract_name in ("formulas", "images"):
        relative = (manifest.get("contracts") or {}).get(contract_name)
        if not relative:
            continue
        for item in load_json(project / relative).get("items", []):
            registry[item["id"]] = {**item, "asset_kind": contract_name}
    return registry


_MATH_SYMBOLS = {
    r"\alpha": "alpha",
    r"\beta": "beta",
    r"\gamma": "gamma",
    r"\delta": "delta",
    r"\epsilon": "epsilon",
    r"\theta": "theta",
    r"\lambda": "lambda",
    r"\mu": "mu",
    r"\pi": "pi",
    r"\rho": "rho",
    r"\sigma": "sigma",
    r"\phi": "phi",
    r"\omega": "omega",
    r"\Delta": "Delta",
    r"\Sigma": "Sigma",
    r"\Omega": "Omega",
    r"\times": "x",
    r"\cdot": "·",
    r"\leq": "<=",
    r"\geq": ">=",
    r"\neq": "!=",
    r"\approx": "~",
    r"\infty": "infinity",
    r"\sum": "SUM",
    r"\prod": "PRODUCT",
    r"\int": "INTEGRAL",
}
_SUPERSCRIPT = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")
_SUBSCRIPT = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")


def editable_formula_text(latex: str) -> str:
    """Convert a conservative LaTeX subset to editable mathematical text."""

    value = latex.strip()
    for token, replacement in _MATH_SYMBOLS.items():
        value = value.replace(token, replacement)
    value = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", value)
    value = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", value)
    value = re.sub(r"\^\{([0-9+\-=()n]+)\}", lambda match: match.group(1).translate(_SUPERSCRIPT), value)
    value = re.sub(r"\^([0-9n])", lambda match: match.group(1).translate(_SUPERSCRIPT), value)
    value = re.sub(r"_\{([0-9+\-=()]+)\}", lambda match: match.group(1).translate(_SUBSCRIPT), value)
    value = re.sub(r"_([0-9])", lambda match: match.group(1).translate(_SUBSCRIPT), value)
    value = re.sub(r"\\(?:mathrm|mathbf|mathit|text)\{([^{}]+)\}", r"\1", value)
    value = value.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", value).strip()


def asset_file_href(project: Path, item: dict[str, Any]) -> str | None:
    relative = item.get("file") or (f"images/{item.get('filename')}" if item.get("filename") else None)
    if not relative:
        return None
    path = (project / relative).resolve()
    try:
        path.relative_to(project)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return "../" + path.relative_to(project).as_posix()


def render_image_asset(item: dict[str, Any], project: Path, slot: dict[str, float], inset: float = 0) -> str:
    href = asset_file_href(project, item)
    if not href:
        return ""
    x, y, width, height = scaled_rect(slot, inset)
    return (
        f'<image id="{html.escape(item["id"], quote=True)}" '
        f'x="{format_svg_number(x)}" y="{format_svg_number(y)}" '
        f'width="{format_svg_number(width)}" height="{format_svg_number(height)}" '
        f'href="{html.escape(href, quote=True)}" preserveAspectRatio="xMidYMid meet"/>'
    )


def prepare_assets(project: Path, manifest: dict[str, Any]) -> list[str]:
    """Resolve configured external assets without making them mandatory."""

    warnings: list[str] = []
    contracts = manifest.get("contracts") or {}
    policy = manifest.get("policy") or {}
    formula_relative = contracts.get("formulas")
    if formula_relative and policy.get("formula_rendering") == "raster":
        formula_manifest = load_json(project / formula_relative)
        if any(
            item.get("render_mode") == "raster" and item.get("status") != "Rendered"
            for item in formula_manifest.get("items", [])
        ):
            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "latex_render.py"), str(project)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode:
                warnings.append("Formula raster rendering is incomplete; editable source text remains available.")

    image_relative = contracts.get("images")
    if image_relative:
        image_manifest = load_json(project / image_relative)
        pending = [item for item in image_manifest.get("items", []) if item.get("status") in {"Pending", "Failed"}]
        if pending and policy.get("image_generation") == "auto":
            generation_env = os.environ.copy()
            generation_env.update(settings_environment())
            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "image_gen.py"), "--manifest", str(project / image_relative)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
                env=generation_env,
            )
            if result.returncode:
                details = (result.stderr or result.stdout).strip().splitlines()
                warnings.append(
                    "Image generation did not complete: " + (details[-1][:240] if details else "unknown backend error")
                )
        elif pending:
            warnings.append(f"{len(pending)} image asset(s) remain Pending in manual mode.")
    return warnings


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
    template: dict[str, Any] | None = None,
) -> None:
    colors = profile["colors"]
    canvas = (template or {}).get("canvas") or {"width": 1280, "height": 720, "viewbox": "0 0 1280 720"}
    font_family = profile.get("font_family", "Aptos, Arial, sans-serif")
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

Generated by Hedgehog Master AutoResearch-Future from the registered project profile.

## canvas
- viewBox: {canvas['viewbox']}
- format: {'PPTX template canvas' if template else 'PPT 16:9'}

## colors
- background: {colors['background']}
- panel: {colors['panel']}
- text: {colors['text']}
- muted: {colors['muted']}
- accent: {colors['accent']}
- secondary: {colors['secondary']}

## typography
- font_family: {font_family}
- title: 36
- body: 18
- annotation: 12

## page_rhythm
{rhythm_rows}

## page_charts
{chart_rows}

## pptx_structure
- mode: flat

## template_contract
- active: {'true' if template else 'false'}
- source: {(template or {}).get('source', 'none')}
- renderer: academic-profile-with-template-constraints

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
    assets_by_id: dict[str, dict[str, Any]],
    profile: dict[str, Any],
    template: dict[str, Any] | None = None,
) -> str:
    colors = profile["colors"]
    canvas = (template or {}).get("canvas") or {"width": 1280, "height": 720}
    width = int(canvas["width"])
    height = int(canvas["height"])
    scale = min(width / 1280, height / 720)
    font_family = profile.get("font_family", "Aptos, Arial, sans-serif")
    title = slide["title"]
    subtitle = slide.get("subtitle", "")
    layout = slide["layout"]
    background = template_background(project, template, layout)

    title_slot = layout_slot(
        template,
        layout,
        "title",
        (56 * scale, 72 * scale, width - 112 * scale, 90 * scale),
    )
    subtitle_slot = layout_slot(
        template,
        layout,
        "subtitle",
        (56 * scale, 150 * scale, width - 112 * scale, 55 * scale),
    )
    content_slot = layout_slot(
        template,
        layout,
        "content",
        (56 * scale, 188 * scale, width - 112 * scale, height - 258 * scale),
    )
    if layout == "cover" and not template:
        title_slot = {"x": 56 * scale, "y": 62 * scale, "width": width - 112 * scale, "height": 142 * scale}
        subtitle_slot = {"x": 56 * scale, "y": 222 * scale, "width": width - 112 * scale, "height": 78 * scale}
        content_slot = {"x": 56 * scale, "y": 330 * scale, "width": width - 112 * scale, "height": height - 390 * scale}

    if layout == "cover":
        title_size = 50 * scale if not template else max(24 * scale, min(50 * scale, title_slot["height"] * 0.38))
        subtitle_size = max(15 * scale, min(24 * scale, subtitle_slot["height"] * 0.36))
        title_lines = max(1, int(title_slot["height"] / (title_size * 1.18)))
        subtitle_lines = max(1, int(subtitle_slot["height"] / (subtitle_size * 1.3)))
        content = (
            ("" if template else f'<rect x="{format_svg_number(56 * scale)}" y="{format_svg_number(118 * scale)}" width="{format_svg_number(112 * scale)}" height="{format_svg_number(6 * scale)}" fill="{colors["secondary"]}"/>\n')
            + wrapped_text(
                title_slot["x"], title_slot["y"] + title_size, title, title_size, colors["text"],
                title_slot["width"], title_size * 1.18, font_family, title_lines,
            )
            + "\n"
            + wrapped_text(
                subtitle_slot["x"], subtitle_slot["y"] + subtitle_size, subtitle, subtitle_size,
                colors["muted"], subtitle_slot["width"], subtitle_size * 1.3, font_family, subtitle_lines,
            )
            + "\n"
            + svg_text(content_slot["x"], content_slot["y"] + 18 * scale, manifest["venue"], 16 * scale, colors["text"], 600, font_family)
            + "\n"
            + svg_text(content_slot["x"], content_slot["y"] + 50 * scale, manifest["audience"], 14 * scale, colors["muted"], font_family=font_family)
        )
        cover_assets = [assets_by_id[item_id] for item_id in slide.get("image_ids", []) if item_id in assets_by_id]
        if cover_assets:
            visual_slot = {
                "x": width * 0.58,
                "y": max(170 * scale, content_slot["y"]),
                "width": width * 0.36,
                "height": min(height * 0.48, height - max(170 * scale, content_slot["y"]) - 54 * scale),
            }
            visual = render_image_asset(cover_assets[0], project, visual_slot, 4 * scale)
            if visual:
                content += "\n" + visual
    elif layout == "diagram":
        source = (project / slide["diagram"]).resolve()
        figure = project / "research" / "figures" / f"{source.stem}.svg"
        compile_diagram(source, figure)
        claim_labels = ", ".join(f"[{claim_id}]" for claim_id in slide.get("claim_ids", []))
        title_size = 36 * scale if not template else max(22 * scale, min(36 * scale, title_slot["height"] * 0.42))
        diagram_x, diagram_y, diagram_width, diagram_height = scaled_rect(content_slot, 10 * scale)
        subtitle_height = 32 * scale if subtitle else 0
        diagram_y += subtitle_height
        diagram_height = max(90 * scale, diagram_height - subtitle_height - 28 * scale)
        content = (
            wrapped_text(
                title_slot["x"], title_slot["y"] + title_size, title, title_size, colors["text"],
                title_slot["width"], title_size * 1.18, font_family, 2,
            )
            + "\n"
            + wrapped_text(
                content_slot["x"] + 10 * scale, content_slot["y"] + 20 * scale, subtitle,
                17 * scale, colors["muted"], content_slot["width"] - 20 * scale,
                22 * scale, font_family, 1,
            )
            + f'\n<rect x="{format_svg_number(diagram_x)}" y="{format_svg_number(diagram_y)}" width="{format_svg_number(diagram_width)}" height="{format_svg_number(diagram_height)}" rx="{format_svg_number(4 * scale)}" fill="{colors["panel"]}"/>\n'
            + extract_svg_body(
                figure,
                left=diagram_x + 12 * scale,
                top=diagram_y + 12 * scale,
                width=diagram_width - 24 * scale,
                height=diagram_height - 24 * scale,
            )
            + "\n"
            + svg_text(
                content_slot["x"] + 10 * scale,
                min(height - 16 * scale, content_slot["y"] + content_slot["height"] - 6 * scale),
                f"Evidence: {claim_labels or 'No claims linked'}",
                12 * scale,
                colors["muted"],
                font_family=font_family,
            )
        )
    elif layout == "evidence":
        title_size = 36 * scale if not template else max(22 * scale, min(36 * scale, title_slot["height"] * 0.42))
        parts = [wrapped_text(
            title_slot["x"], title_slot["y"] + title_size, title, title_size, colors["text"],
            title_slot["width"], title_size * 1.18, font_family, 2,
        )]
        y = content_slot["y"] + 34 * scale
        formula_items = [assets_by_id[item_id] for item_id in slide.get("formula_ids", []) if item_id in assets_by_id]
        image_items = [assets_by_id[item_id] for item_id in slide.get("image_ids", []) if item_id in assets_by_id]
        total_blocks = len(formula_items) + len(image_items) + len(slide.get("claim_ids", []))
        card_height = min(122 * scale, max(82 * scale, content_slot["height"] / max(1, total_blocks) - 16 * scale))
        for formula in formula_items:
            parts.append(f'<rect x="{format_svg_number(content_slot["x"])}" y="{format_svg_number(y - 28 * scale)}" width="{format_svg_number(content_slot["width"])}" height="{format_svg_number(card_height)}" rx="{format_svg_number(4 * scale)}" fill="{colors["panel"]}"/>')
            parts.append(svg_text(content_slot["x"] + 24 * scale, y, f"[{formula['id']}]  {formula.get('locator', 'registered formula')}", 12 * scale, colors["accent"], 700, font_family))
            formula_href = asset_file_href(project, formula) if formula.get("render_mode") == "raster" else None
            if formula_href:
                formula_slot = {
                    "x": content_slot["x"] + 22 * scale,
                    "y": y + 12 * scale,
                    "width": content_slot["width"] - 44 * scale,
                    "height": card_height - 40 * scale,
                }
                parts.append(render_image_asset(formula, project, formula_slot))
            else:
                parts.append(wrapped_text(
                    content_slot["x"] + 24 * scale,
                    y + 42 * scale,
                    editable_formula_text(formula["latex"]),
                    24 * scale,
                    colors["text"],
                    content_slot["width"] - 48 * scale,
                    30 * scale,
                    "Cambria Math, STIX Two Math, serif",
                    2,
                ))
            y += card_height + 16 * scale
        for image_item in image_items:
            image_slot = {
                "x": content_slot["x"],
                "y": y - 28 * scale,
                "width": content_slot["width"],
                "height": card_height,
            }
            rendered = render_image_asset(image_item, project, image_slot, 8 * scale)
            if rendered:
                parts.append(rendered)
                y += card_height + 16 * scale
        for claim_id in slide.get("claim_ids", []):
            claim = claims_by_id[claim_id]
            parts.append(f'<rect x="{format_svg_number(content_slot["x"])}" y="{format_svg_number(y - 28 * scale)}" width="{format_svg_number(content_slot["width"])}" height="{format_svg_number(card_height)}" rx="{format_svg_number(4 * scale)}" fill="{colors["panel"]}"/>')
            parts.append(svg_text(content_slot["x"] + 24 * scale, y, f"[{claim_id}]  {claim['status'].upper()}", 13 * scale, colors["accent"], 700, font_family))
            parts.append(wrapped_text(content_slot["x"] + 24 * scale, y + 34 * scale, claim["text"], 20 * scale, colors["text"], content_slot["width"] - 48 * scale, 28 * scale, font_family, 2))
            citations = claim.get("citations", [])
            source_label = "; ".join(
                f"{citation.get('source_id')} {citation.get('locator')}" for citation in citations[:2]
            ) or ", ".join(claim.get("source_ids", []))
            parts.append(svg_text(content_slot["x"] + 24 * scale, y + card_height - 40 * scale, f"Source: {source_label}", 12 * scale, colors["muted"], font_family=font_family))
            y += card_height + 16 * scale
        content = "\n".join(parts)
    elif layout in {"closing", "section"}:
        title_size = 36 * scale if not template else max(24 * scale, min(46 * scale, title_slot["height"] * 0.38))
        subtitle_size = max(15 * scale, min(22 * scale, subtitle_slot["height"] * 0.38))
        bullet_parts = []
        bullet_y = content_slot["y"] + 28 * scale
        for bullet in slide.get("bullets", []):
            bullet_parts.append(svg_text(content_slot["x"], bullet_y, "•", 18 * scale, colors["accent"], 700, font_family))
            bullet_parts.append(wrapped_text(content_slot["x"] + 28 * scale, bullet_y, bullet, 18 * scale, colors["text"], content_slot["width"] - 28 * scale, 24 * scale, font_family, 2))
            bullet_y += 58 * scale
        content = (
            wrapped_text(title_slot["x"], title_slot["y"] + title_size, title, title_size, colors["text"], title_slot["width"], title_size * 1.2, font_family, 3)
            + "\n"
            + wrapped_text(subtitle_slot["x"], subtitle_slot["y"] + subtitle_size, subtitle, subtitle_size, colors["muted"], subtitle_slot["width"], subtitle_size * 1.35, font_family, 3)
            + ("\n" + "\n".join(bullet_parts) if bullet_parts else "")
        )
    else:
        raise HarnessError(f"Unsupported deterministic layout: {layout}")
    return page_shell(
        content,
        index,
        manifest["title"],
        colors,
        width,
        height,
        font_family,
        background,
    )


def build_project(project: Path) -> list[Path]:
    report = validate_project(project)
    if report.errors:
        raise HarnessError("Validation failed:\n- " + "\n- ".join(report.errors))

    manifest = load_json(project / "project.json")
    template = load_template_contract(project, manifest)
    profile = resolve_render_profile(load_json(profile_path(manifest["profile"])), template)
    asset_warnings = prepare_assets(project, manifest)
    assets_by_id = load_asset_registry(project, manifest)
    claims = load_json(project / "research" / "claims.json")["claims"]
    deck = load_json(project / "storyboard" / "deck.json")
    claims_by_id = {claim["id"]: claim for claim in claims}
    write_spec_lock(project, manifest, profile, deck, template)
    output_dir = project / "svg_output"
    output_dir.mkdir(exist_ok=True)
    for old_svg in output_dir.glob("*.svg"):
        old_svg.unlink()

    outputs = []
    for index, slide in enumerate(deck["slides"], start=1):
        output = output_dir / f"slide_{index:02d}_{slugify(slide['id'])}.svg"
        output.write_text(
            render_slide(slide, index, project, manifest, claims_by_id, assets_by_id, profile, template),
            encoding="utf-8",
        )
        outputs.append(output)
    write_json(
        project / "quality" / "build.json",
        {
            "schema_version": "1.0",
            "built_on": date.today().isoformat(),
            "slides": [path.name for path in outputs],
            "warnings": report.warnings + asset_warnings,
            "assets": {
                "formulas": sum(item.get("asset_kind") == "formulas" for item in assets_by_id.values()),
                "images": sum(item.get("asset_kind") == "images" for item in assets_by_id.values()),
            },
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
    inputs = manifest.get("inputs", [])
    contracts = manifest.get("contracts") or {}
    plan_relative = contracts.get("plan")
    plan = load_json(project / plan_relative) if plan_relative and (project / plan_relative).is_file() else {}
    assets = load_asset_registry(project, manifest)
    diagram_kinds: list[str] = []
    for diagram_path in sorted((project / "research" / "diagrams").glob("*.diagram.json")):
        try:
            diagram_kind = load_json(diagram_path).get("kind")
        except HarnessError:
            continue
        if diagram_kind and diagram_kind not in diagram_kinds:
            diagram_kinds.append(diagram_kind)
    input_counts = {
        kind: sum(1 for item in inputs if item.get("kind") == kind)
        for kind in ("template", "paper", "code")
    }
    return {
        "id": manifest["id"],
        "title": manifest["title"],
        "profile": manifest["profile"],
        "slides": len(slides),
        "sources": len(sources),
        "claims": len(claims),
        "verified_claims": sum(1 for claim in claims if claim.get("status") == "verified"),
        "diagrams": len(list((project / "research" / "diagrams").glob("*.diagram.json"))),
        "diagram_kinds": diagram_kinds,
        "formulas": sum(item.get("asset_kind") == "formulas" for item in assets.values()),
        "images": sum(item.get("asset_kind") == "images" for item in assets.values()),
        "exports": len(list((project / "exports").glob("*.pptx"))),
        "status": "ready" if report.ok else "needs-attention",
        "warnings": len(report.warnings),
        "errors": report.errors,
        "brief": (manifest.get("brief") or {}).get("instructions", ""),
        "planner": plan.get("planner"),
        "plan_warnings": plan.get("warnings", []),
        "policy": manifest.get("policy", {}),
        "inputs": input_counts,
        "template": next((item.get("name") for item in inputs if item.get("kind") == "template"), None),
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
    server_version = f"HedgehogMaster/{APP_VERSION}"

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def require_loopback(self) -> None:
        if self.client_address[0] not in {"127.0.0.1", "::1"}:
            raise HarnessError("Provider settings are available only from the local computer")

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise HarnessError("Request body is too large")
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as exc:
            raise HarnessError("Request body must be JSON") from exc

    def read_project_body(self) -> tuple[dict[str, Any], dict[str, list[UploadedFile]]]:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("multipart/form-data"):
            return self.read_json_body(), {}
        length = int(self.headers.get("Content-Length", "0"))
        if length > 120_000_000:
            raise HarnessError("Project intake is larger than 120 MB")
        raw = self.rfile.read(length)
        envelope = (
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
            + raw
        )
        message = BytesParser(policy=email_policy.default).parsebytes(envelope)
        fields: dict[str, Any] = {}
        files: dict[str, list[UploadedFile]] = {}
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if not name:
                continue
            filename = part.get_filename()
            data = part.get_payload(decode=True) or b""
            if filename:
                if data:
                    files.setdefault(name, []).append(
                        UploadedFile(filename, part.get_content_type(), data)
                    )
                continue
            fields[name] = data.decode(part.get_content_charset() or "utf-8", errors="replace")
        fields["demo"] = str(fields.get("demo", "")).lower() in {"1", "true", "on", "yes"}
        fields["auto_plan"] = str(fields.get("auto_plan", "")).lower() in {"1", "true", "on", "yes"}
        return fields, files

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self.send_json(
                {
                    "repository": "hedgehog-master",
                    "version": APP_VERSION,
                    "release_channel": "beta",
                    "projects": list_projects(),
                }
            )
            return
        if parsed.path == "/api/profiles":
            profiles = [load_json(path) for path in sorted(PROFILES_DIR.glob("*.json"))]
            self.send_json({"profiles": profiles})
            return
        if parsed.path == "/api/settings":
            try:
                self.require_loopback()
                self.send_json(public_settings())
            except HarnessError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.FORBIDDEN)
            return
        if parsed.path in {"/", "/index.html"}:
            self.path = "/index.html"
            super().do_GET()
            return
        branding_pattern = r"/assets/branding/[A-Za-z0-9_.-]+\.(?:svg|png|ico)"
        if re.fullmatch(branding_pattern, parsed.path):
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
            if parsed.path == "/api/settings":
                self.require_loopback()
                settings = save_settings(self.read_json_body())
                self.send_json(public_settings(settings))
                return
            if parsed.path == "/api/projects":
                payload, files = self.read_project_body()
                project = initialize_project(
                    payload.get("name", "research-project"),
                    title=payload.get("title"),
                    audience=payload.get("audience", "Academic audience"),
                    venue=payload.get("venue", "Research presentation"),
                    profile=payload.get("profile", "academic-conference"),
                    demo=bool(payload.get("demo", False)),
                    brief=payload.get("brief", ""),
                    template_upload=(files.get("template") or [None])[0],
                    paper_uploads=files.get("papers", []),
                    code_uploads=files.get("code_files", []),
                    code_text=payload.get("code_text", ""),
                    auto_plan=bool(payload.get("auto_plan", True)),
                    image_generation=payload.get("image_generation", "manual"),
                    formula_rendering=payload.get("formula_rendering", "editable-text"),
                    content_provider=payload.get("content_provider", "rules"),
                    diagram_provider=payload.get("diagram_provider", "rules"),
                )
                self.send_json(project_summary(project), HTTPStatus.CREATED)
                return
            match = re.fullmatch(r"/api/projects/([^/]+)/(plan|validate|build|export)", parsed.path)
            if match:
                project = ensure_project_path(unquote(match.group(1)))
                action = match.group(2)
                if action == "plan":
                    self.send_json({"ok": True, "plan": plan_project(project)})
                elif action == "validate":
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
        except (HarnessError, ValueError) as exc:
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
    parser = argparse.ArgumentParser(description="Hedgehog Master AutoResearch-Future harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a structured research project")
    init_parser.add_argument("name")
    init_parser.add_argument("--title")
    init_parser.add_argument("--audience", default="Academic audience")
    init_parser.add_argument("--venue", default="Research presentation")
    init_parser.add_argument("--profile", default="academic-conference")
    init_parser.add_argument("--demo", action="store_true", help="Seed a runnable four-slide example")
    init_parser.add_argument("--brief", default="", help="Presentation instructions")
    init_parser.add_argument("--template", type=Path, help="PPTX template or background deck")
    init_parser.add_argument("--paper", type=Path, action="append", default=[], help="Paper or research source; repeatable")
    init_parser.add_argument("--code", type=Path, action="append", default=[], help="Code input; repeatable")
    init_parser.add_argument("--code-text", default="", help="Inline code or pseudocode")
    init_parser.add_argument("--no-plan", action="store_true", help="Register inputs without deriving research contracts")
    init_parser.add_argument("--image-generation", choices=("manual", "auto"), default="manual")
    init_parser.add_argument("--formula-rendering", choices=("editable-text", "raster"), default="editable-text")
    init_parser.add_argument("--content-provider", choices=CONTENT_PROVIDERS, default="rules")
    init_parser.add_argument("--diagram-provider", choices=DIAGRAM_PROVIDERS, default="rules")

    for command, help_text in (
        ("plan", "Derive sources, claims, storyboard, diagrams, and asset manifests"),
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
                brief=args.brief,
                template_upload=upload_from_path(args.template) if args.template else None,
                paper_uploads=[upload_from_path(path) for path in args.paper],
                code_uploads=[upload_from_path(path) for path in args.code],
                code_text=args.code_text,
                auto_plan=not args.no_plan,
                image_generation=args.image_generation,
                formula_rendering=args.formula_rendering,
                content_provider=args.content_provider,
                diagram_provider=args.diagram_provider,
            )
            print(project)
        elif args.command == "plan":
            print(json.dumps(plan_project(ensure_project_path(args.project)), indent=2))
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

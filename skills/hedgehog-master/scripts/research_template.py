#!/usr/bin/env python3
"""PPTX-to-Template-Contract adapter for the AutoResearch harness."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SEMANTIC_LAYOUTS = ("cover", "section", "diagram", "evidence", "closing")


class TemplateContractError(RuntimeError):
    """Raised when a PPTX cannot become a usable academic template contract."""


def _valid_geometry(value: Any) -> dict[str, float] | None:
    if not isinstance(value, dict):
        return None
    try:
        rect = {
            "x": float(value["x"]),
            "y": float(value["y"]),
            "width": float(value["width"]),
            "height": float(value["height"]),
        }
    except (KeyError, TypeError, ValueError):
        return None
    if rect["width"] <= 0 or rect["height"] <= 0:
        return None
    return rect


def _fallback_slots(layout: str, width: int, height: int) -> dict[str, dict[str, float]]:
    if layout == "cover":
        return {
            "title": {"x": width * 0.08, "y": height * 0.22, "width": width * 0.84, "height": height * 0.25},
            "subtitle": {"x": width * 0.08, "y": height * 0.52, "width": width * 0.76, "height": height * 0.14},
            "content": {"x": width * 0.08, "y": height * 0.72, "width": width * 0.76, "height": height * 0.12},
        }
    if layout in {"section", "closing"}:
        return {
            "title": {"x": width * 0.08, "y": height * 0.34, "width": width * 0.82, "height": height * 0.22},
            "subtitle": {"x": width * 0.08, "y": height * 0.61, "width": width * 0.75, "height": height * 0.14},
            "content": {"x": width * 0.08, "y": height * 0.61, "width": width * 0.75, "height": height * 0.18},
        }
    return {
        "title": {"x": width * 0.05, "y": height * 0.08, "width": width * 0.90, "height": height * 0.12},
        "subtitle": {"x": width * 0.05, "y": height * 0.20, "width": width * 0.86, "height": height * 0.07},
        "content": {"x": width * 0.05, "y": height * 0.29, "width": width * 0.90, "height": height * 0.59},
    }


def _layout_score(layout: dict[str, Any], semantic: str) -> int:
    layout_type = str(layout.get("layoutType") or "").lower()
    name = str(layout.get("displayName") or layout.get("name") or "").lower()
    roles = {str(item.get("semanticRole") or "") for item in layout.get("placeholders", [])}
    score = 0
    preferences = {
        "cover": (("title", 120), ("cover", 100), ("ctrtitle", 90)),
        "section": (("sechead", 120), ("section", 110), ("header", 80)),
        "diagram": (("obj", 120), ("content", 100), ("twoobj", 90), ("blank", 30)),
        "evidence": (("obj", 120), ("content", 100), ("tx", 90), ("twoobj", 80)),
        "closing": (("titleonly", 120), ("closing", 110), ("title", 70), ("blank", 30)),
    }
    for token, weight in preferences[semantic]:
        if token == layout_type:
            score += weight
        elif token in name:
            score += weight - 15
    if "title" in roles:
        score += 20
    if semantic == "cover" and "subtitle" in roles:
        score += 25
    if semantic in {"diagram", "evidence"} and roles.intersection({"object", "body", "picture", "chart"}):
        score += 35
    if layout.get("usedBySlides"):
        score += 5
    return score


def _choose_layout(layouts: list[dict[str, Any]], semantic: str) -> dict[str, Any]:
    if not layouts:
        raise TemplateContractError("The PPTX contains no slide layouts")
    return max(layouts, key=lambda item: (_layout_score(item, semantic), -layouts.index(item)))


def _slot_contract(
    semantic: str,
    layout: dict[str, Any],
    master: dict[str, Any] | None,
    width: int,
    height: int,
) -> dict[str, dict[str, float]]:
    defaults = _fallback_slots(semantic, width, height)
    by_role: dict[str, dict[str, float]] = {}
    master_placeholders = (master or {}).get("placeholders", [])
    master_by_role = {
        str(item.get("semanticRole") or ""): geometry
        for item in master_placeholders
        if (geometry := _valid_geometry(item.get("geometry")))
    }
    for placeholder in layout.get("placeholders", []):
        role = str(placeholder.get("semanticRole") or "")
        geometry = _valid_geometry(placeholder.get("geometry")) or master_by_role.get(role)
        if geometry and role:
            by_role.setdefault(role, geometry)

    title = by_role.get("title") or defaults["title"]
    subtitle = by_role.get("subtitle") or by_role.get("body") or defaults["subtitle"]
    content = next(
        (by_role[role] for role in ("object", "body", "picture", "chart") if role in by_role),
        defaults["content"],
    )
    if semantic in {"section", "closing"} and content == title:
        content = defaults["content"]
    return {"title": title, "subtitle": subtitle, "content": content}


def build_contract(manifest: dict[str, Any], source: str) -> dict[str, Any]:
    """Build a strict Template Contract from a PPTX import manifest."""

    slide_size = manifest.get("slideSize") or {}
    try:
        width = int(slide_size["width_px"])
        height = int(slide_size["height_px"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TemplateContractError("The PPTX manifest does not declare a usable slide size") from exc
    layouts = manifest.get("layouts") or []
    masters = {item.get("path"): item for item in manifest.get("masters") or []}

    bindings: dict[str, Any] = {}
    for semantic in SEMANTIC_LAYOUTS:
        layout = _choose_layout(layouts, semantic)
        master = masters.get(layout.get("parentPath"))
        layers = []
        if master and master.get("svgFile"):
            layers.append(f"template/workspace/svg/{master['svgFile']}")
        if layout.get("svgFile"):
            layers.append(f"template/workspace/svg/{layout['svgFile']}")
        bindings[semantic] = {
            "source_layout": str(layout.get("displayName") or layout.get("name") or semantic),
            "background_layers": layers,
            "slots": _slot_contract(semantic, layout, master, width, height),
        }

    theme = manifest.get("theme") or {}
    return {
        "$schema": "../../skills/hedgehog-master/research/schemas/template.schema.json",
        "schema_version": "1.0",
        "source": source,
        "workspace": "template/workspace",
        "canvas": {"width": width, "height": height, "viewbox": f"0 0 {width} {height}"},
        "theme": {
            "colors": dict(theme.get("colors") or {}),
            "fonts": dict(theme.get("fonts") or {}),
        },
        "layouts": bindings,
    }


def import_template(project: Path, source_path: Path) -> Path:
    """Analyze one project-local PPTX and write `template/template.json`."""

    workspace = project / "template" / "workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    importer = Path(__file__).resolve().parent / "pptx_template_import.py"
    result = subprocess.run(
        [
            sys.executable,
            str(importer),
            str(source_path),
            "-o",
            str(workspace),
            "--embed-images",
            "--inheritance-mode",
            "layered",
        ],
        cwd=project.parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        details = (result.stderr or result.stdout).strip()
        raise TemplateContractError(details or "PPTX template analysis failed")
    manifest_path = workspace / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise TemplateContractError("PPTX template analysis did not produce a valid manifest") from exc
    source = str(source_path.relative_to(project))
    contract = build_contract(manifest, source)
    contract_path = project / "template" / "template.json"
    contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return contract_path

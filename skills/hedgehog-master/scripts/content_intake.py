#!/usr/bin/env python3
"""Compile a filled external-LLM content contract into project artifacts."""

from __future__ import annotations

import hashlib
import io
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from content_spec import content_spec_summary


SCHEMA_ROOT = "../../../skills/hedgehog-master/research/schemas"
LAYOUT_MAP = {
    "cover": "cover",
    "content": "section",
    "evidence": "evidence",
    "formula": "evidence",
    "closing": "closing",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class ContentIntakeError(ValueError):
    """Raised when page assets cannot be mapped safely into the project."""


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_image_name(value: str, index: int) -> str:
    source = Path(value).name.strip()
    extension = Path(source).suffix.lower()
    if extension not in IMAGE_EXTENSIONS:
        raise ContentIntakeError(f"Unsupported page image '{source}'. Use PNG, JPEG, or WebP.")
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(source).stem).strip("-.")[:90]
    return f"{stem or f'page-image-{index}'}{extension}"


def _verify_image(data: bytes, name: str) -> None:
    if not data or len(data) > 30_000_000:
        raise ContentIntakeError(f"Page image '{name}' is empty or larger than 30 MB")
    try:
        from PIL import Image

        with Image.open(io.BytesIO(data)) as image:
            image.verify()
    except (ImportError, OSError, ValueError) as exc:
        raise ContentIntakeError(f"Page image '{name}' is not a readable PNG, JPEG, or WebP file") from exc


def _unique_destination(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    counter = 2
    while candidate.exists():
        candidate = directory / f"{Path(filename).stem}-{counter}{Path(filename).suffix}"
        counter += 1
    return candidate


def _source_contract(spec: dict[str, Any], content_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[str]]]:
    sources = [
        {
            "id": "external-content",
            "title": "User-approved external LLM content contract",
            "type": "local",
            "locator": "inputs/content/content-spec.json",
            "sha256": _sha256(content_path),
        }
    ]
    claims: list[dict[str, Any]] = []
    slide_claims: dict[str, list[str]] = {}
    source_ids_by_value: dict[str, str] = {}
    for slide_number, slide in enumerate(spec["slides"], start=1):
        registered: list[str] = []
        for source_value in slide["sources"]:
            source_id = source_ids_by_value.get(source_value)
            if not source_id:
                source_id = f"provided-source-{len(source_ids_by_value) + 1}"
                source_ids_by_value[source_value] = source_id
                sources.append(
                    {
                        "id": source_id,
                        "title": source_value[:180],
                        "type": "web" if re.match(r"https?://", source_value) else "local",
                        "locator": source_value,
                    }
                )
            registered.append(source_id)
        if not registered:
            continue
        claim_text = (
            (slide["body"] or [slide["title"] or slide["subtitle"] or f"Content for slide {slide_number}"])[0]
        )
        claim_id = f"claim-{slide['id']}"
        claims.append(
            {
                "id": claim_id,
                "text": claim_text,
                "status": "draft",
                "source_ids": registered,
                "evidence": "Source labels were supplied in the external content contract and require researcher verification.",
                "citations": [
                    {
                        "source_id": source_id,
                        "locator": f"content template slide {slide_number}",
                        "excerpt": claim_text,
                    }
                    for source_id in registered
                ],
                "confidence": 0.6,
            }
        )
        slide_claims[slide["id"]] = [claim_id]
    return sources, claims, slide_claims


def _page_mapping(value: str, uploads: list[Any], slide_ids: list[str]) -> list[dict[str, Any]]:
    if not uploads:
        return []
    try:
        payload = json.loads(value or "[]")
    except json.JSONDecodeError as exc:
        raise ContentIntakeError("The page image mapping is not valid JSON") from exc
    if not isinstance(payload, list):
        raise ContentIntakeError("The page image mapping must be an array")
    mappings: dict[int, str] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        file_index = item.get("file_index")
        slide_id = str(item.get("slide_id") or "")
        if not isinstance(file_index, int) or not 0 <= file_index < len(uploads):
            raise ContentIntakeError("A page image mapping uses an invalid file index")
        if slide_id not in slide_ids:
            raise ContentIntakeError(f"A page image is mapped to unknown slide '{slide_id}'")
        mappings[file_index] = slide_id
    if len(mappings) != len(uploads):
        raise ContentIntakeError("Every uploaded page image must be assigned to a slide")
    return [{"file_index": index, "slide_id": mappings[index]} for index in range(len(uploads))]


def compile_content_contract(
    project: Path,
    manifest: dict[str, Any],
    spec: dict[str, Any],
    page_images: list[Any] | None = None,
    image_page_map: str = "",
) -> dict[str, Any]:
    """Write deck, source, formula, image, notes, and plan artifacts from a filled spec."""

    page_images = page_images or []
    content_path = project / "inputs" / "content" / "content-spec.json"
    _write_json(content_path, spec)
    slide_ids = [slide["id"] for slide in spec["slides"]]
    mappings = _page_mapping(image_page_map, page_images, slide_ids)
    _write_json(project / "analysis" / "image-page-map.json", {"schema_version": "1.0", "items": mappings})

    sources, claims, slide_claims = _source_contract(spec, content_path)
    formula_mode = str((manifest.get("policy") or {}).get("formula_rendering") or "editable-text")
    formulas: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    slides: list[dict[str, Any]] = []
    notes: list[dict[str, str]] = []

    for slide_number, source_slide in enumerate(spec["slides"], start=1):
        slide_id = source_slide["id"]
        formula_ids: list[str] = []
        for formula_number, formula in enumerate(source_slide["formulas"], start=1):
            formula_id = f"{slide_id}-formula-{formula_number}"
            formula_item = {
                "id": formula_id,
                "latex": formula["latex"],
                "display": formula["display"],
                "render_mode": formula_mode,
                "status": "Ready" if formula_mode == "editable-text" else "Pending",
                "source_id": "external-content",
                "locator": f"content template slide {slide_number}",
                "slide_ids": [slide_id],
            }
            if formula_mode == "raster":
                formula_item["filename"] = f"{formula_id}.png"
            formulas.append(formula_item)
            formula_ids.append(formula_id)

        image_ids: list[str] = []
        for image in source_slide["images"]:
            images.append(
                {
                    "id": image["id"],
                    "filename": f"{image['id']}.png",
                    "prompt": image["prompt"],
                    "aspect_ratio": "16:9",
                    "status": "Pending",
                    "purpose": f"Slide {slide_number} requested visual",
                    "alt_text": image["alt_text"],
                    "slide_ids": [slide_id],
                }
            )
            image_ids.append(image["id"])

        slide = {
            "id": slide_id,
            "layout": LAYOUT_MAP[source_slide["layout"]],
            "title": source_slide["title"],
        }
        if source_slide["subtitle"]:
            slide["subtitle"] = source_slide["subtitle"]
        if source_slide["body"]:
            slide["bullets"] = source_slide["body"]
        if formula_ids:
            slide["formula_ids"] = formula_ids
        if image_ids:
            slide["image_ids"] = image_ids
        if slide_claims.get(slide_id):
            slide["claim_ids"] = slide_claims[slide_id]
        slides.append(slide)
        notes.append({"slide_id": slide_id, "speaker_notes": source_slide["speaker_notes"]})

    image_directory = project / "images"
    image_directory.mkdir(parents=True, exist_ok=True)
    uploads_by_slide: dict[str, list[tuple[int, Any]]] = {}
    for mapping in mappings:
        uploads_by_slide.setdefault(mapping["slide_id"], []).append(
            (mapping["file_index"], page_images[mapping["file_index"]])
        )
    for slide_id, mapped_uploads in uploads_by_slide.items():
        slide = next(item for item in slides if item["id"] == slide_id)
        pending_slots = [item for item in images if slide_id in item["slide_ids"] and item["status"] == "Pending"]
        for upload_number, (file_index, upload) in enumerate(mapped_uploads, start=1):
            filename = _safe_image_name(upload.filename, file_index + 1)
            _verify_image(upload.data, filename)
            destination = _unique_destination(image_directory, filename)
            destination.write_bytes(upload.data)
            if pending_slots:
                item = pending_slots.pop(0)
            else:
                image_id = f"{slide_id}-upload-{upload_number}"
                item = {
                    "id": image_id,
                    "prompt": f"User-supplied image for {slide_id}",
                    "aspect_ratio": "16:9",
                    "purpose": "User-supplied page image",
                    "alt_text": f"User-supplied visual for {slide_id}",
                    "slide_ids": [slide_id],
                }
                images.append(item)
                slide.setdefault("image_ids", []).append(image_id)
            item.update(
                {
                    "filename": destination.name,
                    "file": f"images/{destination.name}",
                    "status": "Generated",
                }
            )

    deck = {
        "$schema": f"{SCHEMA_ROOT}/deck.schema.json",
        "schema_version": "1.1",
        "slides": slides,
    }
    _write_json(
        project / "research" / "sources.json",
        {"$schema": f"{SCHEMA_ROOT}/sources.schema.json", "schema_version": "1.1", "sources": sources},
    )
    _write_json(
        project / "research" / "claims.json",
        {"$schema": f"{SCHEMA_ROOT}/claims.schema.json", "schema_version": "1.1", "claims": claims},
    )
    _write_json(project / "storyboard" / "deck.json", deck)
    _write_json(
        project / "images" / "formula_manifest.json",
        {"$schema": f"{SCHEMA_ROOT}/formula-manifest.schema.json", "schema_version": "1.0", "items": formulas},
    )
    _write_json(
        project / "images" / "image_prompts.json",
        {
            "$schema": f"{SCHEMA_ROOT}/image-manifest.schema.json",
            "schema_version": "1.0",
            "project": manifest["id"],
            "generated_at": date.today().isoformat(),
            "items": images,
        },
    )
    _write_json(project / "notes" / "speaker-notes.json", {"schema_version": "1.0", "items": notes})

    manifest["title"] = spec["deck"]["title"]
    manifest["language"] = spec["deck"]["language"]
    contracts = manifest.setdefault("contracts", {})
    contracts.update(
        {
            "sources": "research/sources.json",
            "claims": "research/claims.json",
            "storyboard": "storyboard/deck.json",
            "formulas": "images/formula_manifest.json",
            "images": "images/image_prompts.json",
            "plan": "analysis/plan.json",
        }
    )
    policy = manifest.setdefault("policy", {})
    policy["content_mode"] = "external-template"
    _write_json(project / "project.json", manifest)

    summary = content_spec_summary(spec)
    pending_images = sum(item["status"] == "Pending" for item in images)
    report = {
        "schema_version": "1.0",
        "planner": "hedgehog-external-template-v1",
        "planned_on": date.today().isoformat(),
        "brief": str((manifest.get("brief") or {}).get("instructions") or ""),
        "sources": len(sources),
        "claims": len(claims),
        "slides": len(slides),
        "diagram_kind": None,
        "formulas": len(formulas),
        "images": len(images),
        "content_mode": "external-template",
        "warnings": ([f"{pending_images} requested image(s) still need a page upload or image generation."] if pending_images else []),
        "content_summary": summary,
    }
    _write_json(project / "analysis" / "plan.json", report)
    return report

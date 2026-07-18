#!/usr/bin/env python3
"""External-LLM content contract for deterministic Hedgehog Master layout."""

from __future__ import annotations

import json
import re
from typing import Any


CONTENT_SPEC_VERSION = "1.0"
CONTENT_LAYOUTS = ("cover", "content", "evidence", "formula", "closing")
MAX_SLIDES = 40

CONTENT_SPEC_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "generation_instructions", "deck", "slides"],
    "properties": {
        "schema_version": {"const": CONTENT_SPEC_VERSION},
        "generation_instructions": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "deck": {
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "subtitle", "language"],
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 160},
                "subtitle": {"type": "string", "maxLength": 260},
                "language": {"enum": ["en", "zh"]},
            },
        },
        "slides": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_SLIDES,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "id",
                    "layout",
                    "title",
                    "subtitle",
                    "body",
                    "formulas",
                    "images",
                    "sources",
                    "speaker_notes",
                ],
                "properties": {
                    "id": {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_-]*$"},
                    "layout": {"enum": list(CONTENT_LAYOUTS)},
                    "title": {"type": "string", "maxLength": 110},
                    "subtitle": {"type": "string", "maxLength": 240},
                    "body": {
                        "type": "array",
                        "maxItems": 6,
                        "items": {"type": "string", "minLength": 1, "maxLength": 320},
                    },
                    "formulas": {
                        "type": "array",
                        "maxItems": 3,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["latex", "display"],
                            "properties": {
                                "latex": {"type": "string", "minLength": 1, "maxLength": 800},
                                "display": {"enum": ["inline", "block"]},
                            },
                        },
                    },
                    "images": {
                        "type": "array",
                        "maxItems": 3,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["id", "prompt", "alt_text"],
                            "properties": {
                                "id": {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_-]*$"},
                                "prompt": {"type": "string", "minLength": 1, "maxLength": 1000},
                                "alt_text": {"type": "string", "minLength": 1, "maxLength": 240},
                            },
                        },
                    },
                    "sources": {
                        "type": "array",
                        "maxItems": 8,
                        "items": {"type": "string", "minLength": 1, "maxLength": 500},
                    },
                    "speaker_notes": {"type": "string", "maxLength": 1600},
                },
            },
        },
    },
}


class ContentSpecError(ValueError):
    """Raised when an external content contract is incomplete or unsafe to lay out."""


def _strip_code_fence(value: str) -> str:
    compact = value.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", compact, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else compact


def _placeholder_paths(value: Any, path: str = "$", *, ignore_instructions: bool = False) -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "generation_instructions":
                continue
            paths.extend(_placeholder_paths(item, f"{path}.{key}", ignore_instructions=ignore_instructions))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_placeholder_paths(item, f"{path}[{index}]", ignore_instructions=ignore_instructions))
    elif isinstance(value, str) and re.search(r"<[^<>]+>", value):
        paths.append(path)
    return paths


def normalize_latex(value: str) -> str:
    latex = value.strip()
    if latex.startswith("$$") and latex.endswith("$$") and len(latex) > 4:
        return latex[2:-2].strip()
    if latex.startswith("$") and latex.endswith("$") and len(latex) > 2:
        return latex[1:-1].strip()
    if latex.startswith(r"\[") and latex.endswith(r"\]") and len(latex) > 4:
        return latex[2:-2].strip()
    return latex


def parse_content_spec(value: str, *, require_filled: bool = True) -> dict[str, Any]:
    if not value.strip():
        raise ContentSpecError("The filled content template is empty")
    try:
        payload = json.loads(_strip_code_fence(value))
    except json.JSONDecodeError as exc:
        raise ContentSpecError(f"The content template is not valid JSON: line {exc.lineno}, column {exc.colno}") from exc
    if not isinstance(payload, dict):
        raise ContentSpecError("The content template root must be a JSON object")
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - runtime setup boundary
        raise ContentSpecError("Install requirements.txt to validate content templates") from exc
    errors = sorted(Draft202012Validator(CONTENT_SPEC_SCHEMA).iter_errors(payload), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        location = ".".join(str(item) for item in first.path) or "$"
        raise ContentSpecError(f"Invalid content template at {location}: {first.message}")
    slide_ids = [slide["id"] for slide in payload["slides"]]
    if len(slide_ids) != len(set(slide_ids)):
        raise ContentSpecError("Slide IDs must be unique")
    image_ids = [image["id"] for slide in payload["slides"] for image in slide["images"]]
    if len(image_ids) != len(set(image_ids)):
        raise ContentSpecError("Image IDs must be unique across the deck")
    if require_filled:
        placeholders = _placeholder_paths(payload)
        if placeholders:
            preview = ", ".join(placeholders[:4])
            raise ContentSpecError(f"The content template still contains placeholders: {preview}")
    normalized = json.loads(json.dumps(payload))
    for slide in normalized["slides"]:
        for formula in slide["formulas"]:
            formula["latex"] = normalize_latex(formula["latex"])
    return normalized


def _slide_template(index: int, options: dict[str, Any]) -> dict[str, Any]:
    slide_id = f"slide-{index:02d}"
    layout = str(options.get("layout") or ("cover" if index == 1 else "content"))
    if layout not in CONTENT_LAYOUTS:
        layout = "content"
    has_title = bool(options.get("title", True))
    has_subtitle = bool(options.get("subtitle", index == 1))
    has_image = bool(options.get("image", False))
    has_formula = bool(options.get("formula", False))
    body = [] if layout == "cover" else ["<Write 2-4 concise, presentation-ready bullet points for this page>"]
    formulas = (
        [{"latex": "<Write one LaTeX expression without explanatory prose>", "display": "block"}]
        if has_formula
        else []
    )
    images = (
        [
            {
                "id": f"{slide_id}-image-01",
                "prompt": "<Describe the exact scientific image, chart, or visual needed on this page; request no embedded text>",
                "alt_text": "<Write concise accessible alt text for the image>",
            }
        ]
        if has_image
        else []
    )
    return {
        "id": slide_id,
        "layout": layout,
        "title": "<Write a takeaway-style page title>" if has_title else "",
        "subtitle": "<Write a short supporting subtitle>" if has_subtitle else "",
        "body": body,
        "formulas": formulas,
        "images": images,
        "sources": [],
        "speaker_notes": "",
    }


def build_content_template(
    deck_title: str,
    language: str,
    slide_options: list[dict[str, Any]],
) -> str:
    if not slide_options:
        raise ContentSpecError("At least one slide is required")
    if len(slide_options) > MAX_SLIDES:
        raise ContentSpecError(f"A content template supports at most {MAX_SLIDES} slides")
    language = language if language in {"en", "zh"} else "en"
    payload = {
        "schema_version": CONTENT_SPEC_VERSION,
        "generation_instructions": [
            "Replace every <...> placeholder while preserving all keys, IDs, arrays, and JSON syntax.",
            "Return only the completed JSON object; do not wrap it in commentary or Markdown.",
            "Keep titles concise, use no more than six body bullets per page, and do not invent sources.",
            "Write formulas as LaTeX strings. Escape each backslash for valid JSON, for example \\frac becomes \\\\frac in raw JSON.",
            "For each requested image, write a precise visual prompt without embedded labels or decorative stock-photo language.",
        ],
        "deck": {
            "title": deck_title.strip() or "<Write the presentation title>",
            "subtitle": "<Write a one-sentence deck subtitle>",
            "language": language,
        },
        "slides": [_slide_template(index, options) for index, options in enumerate(slide_options, start=1)],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def content_spec_summary(payload: dict[str, Any]) -> dict[str, Any]:
    slides = payload["slides"]
    return {
        "title": payload["deck"]["title"],
        "language": payload["deck"]["language"],
        "slides": len(slides),
        "formulas": sum(len(slide["formulas"]) for slide in slides),
        "images": sum(len(slide["images"]) for slide in slides),
        "pages": [
            {
                "id": slide["id"],
                "number": index,
                "title": slide["title"],
                "layout": slide["layout"],
                "images": len(slide["images"]),
                "formulas": len(slide["formulas"]),
            }
            for index, slide in enumerate(slides, start=1)
        ],
    }

#!/usr/bin/env python3
"""Constrained model adapters for semantic slides and Diagram IR."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from provider_settings import provider_config, resolve_model


ALLOWED_LAYOUTS = {"section", "evidence", "closing"}
ALLOWED_DIAGRAM_KINDS = {"dataflow", "cycle", "comparison", "architecture", "timeline"}
ALLOWED_DIRECTIONS = {"left-to-right", "top-to-bottom", "clockwise"}
ALLOWED_ROLES = {"source", "transform", "model", "metric", "output"}

CONTENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "claims", "slides"],
    "properties": {
        "summary": {"type": "string", "minLength": 1, "maxLength": 320},
        "claims": {
            "type": "array",
            "maxItems": 12,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["text", "word_count", "character_count", "evidence_ids", "confidence"],
                "properties": {
                    "text": {"type": "string", "minLength": 1, "maxLength": 420},
                    "word_count": {"type": "integer", "minimum": 1, "maximum": 120},
                    "character_count": {"type": "integer", "minimum": 1, "maximum": 420},
                    "evidence_ids": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 4,
                        "uniqueItems": True,
                        "items": {"type": "string"},
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
        "slides": {
            "type": "array",
            "minItems": 1,
            "maxItems": 12,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "layout", "title", "subtitle", "bullets", "claim_indexes"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_-]*$"},
                    "layout": {"enum": sorted(ALLOWED_LAYOUTS)},
                    "title": {"type": "string", "minLength": 1, "maxLength": 110},
                    "subtitle": {"type": "string", "maxLength": 220},
                    "bullets": {
                        "type": "array",
                        "maxItems": 6,
                        "items": {"type": "string", "minLength": 1, "maxLength": 220},
                    },
                    "claim_indexes": {
                        "type": "array",
                        "maxItems": 4,
                        "uniqueItems": True,
                        "items": {"type": "integer", "minimum": 0},
                    },
                },
            },
        },
    },
}

DIAGRAM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["irVersion", "id", "title", "kind", "direction", "nodes", "edges", "metadata"],
    "properties": {
        "irVersion": {"const": "0.2"},
        "id": {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_-]*$"},
        "title": {"type": "string", "minLength": 1, "maxLength": 140},
        "kind": {"enum": sorted(ALLOWED_DIAGRAM_KINDS)},
        "direction": {"enum": sorted(ALLOWED_DIRECTIONS)},
        "nodes": {
            "type": "array",
            "minItems": 2,
            "maxItems": 12,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "label", "role", "group"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_-]*$"},
                    "label": {"type": "string", "minLength": 1, "maxLength": 72},
                    "role": {"enum": sorted(ALLOWED_ROLES)},
                    "group": {"type": "string", "minLength": 1, "maxLength": 40},
                },
            },
        },
        "edges": {
            "type": "array",
            "minItems": 1,
            "maxItems": 20,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "from", "to", "label", "evidenceRef"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_-]*$"},
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "label": {"type": "string", "maxLength": 60},
                    "evidenceRef": {"type": "string", "maxLength": 120},
                },
            },
        },
        "metadata": {"type": "object", "additionalProperties": False, "properties": {}},
    },
}


@dataclass
class ProviderResult:
    provider: str
    model: str
    status: str
    payload: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class HttpResponse:
    status_code: int
    body: bytes

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            detail = self.body.decode("utf-8", errors="replace")[:400]
            raise ValueError(f"HTTP {self.status_code}: {detail}")

    def json(self) -> dict[str, Any]:
        payload = json.loads(self.body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Provider response must be a JSON object")
        return payload


def default_request(method: str, url: str, **kwargs: Any) -> HttpResponse:
    body = json.dumps(kwargs.get("json") or {}, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, headers=kwargs.get("headers") or {}, method=method)
    try:
        with urlopen(request, timeout=kwargs.get("timeout", 120)) as response:
            return HttpResponse(response.status, response.read())
    except HTTPError as exc:
        return HttpResponse(exc.code, exc.read())


def _json_text(response: Any) -> str:
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    choices = payload.get("choices") or []
    if choices:
        content = (choices[0].get("message") or {}).get("content")
        if isinstance(content, str):
            return content
    raise ValueError("Provider response did not contain JSON output text")


def _parse_json(value: str) -> dict[str, Any]:
    value = value.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value, flags=re.IGNORECASE)
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise ValueError("Provider output must be a JSON object")
    return payload


def _request_openai_responses(
    config: dict[str, str],
    model: str,
    instructions: str,
    user_payload: dict[str, Any],
    schema_name: str,
    schema: dict[str, Any],
    request: Callable[..., Any],
) -> dict[str, Any]:
    endpoint = f"{config['base_url'].rstrip('/')}/responses"
    response = request(
        "POST",
        endpoint,
        headers={"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"},
        json={
            "model": model,
            "instructions": instructions,
            "input": json.dumps(user_payload, ensure_ascii=False),
            "text": {"format": {"type": "json_schema", "name": schema_name, "strict": True, "schema": schema}},
        },
        timeout=120,
    )
    return _parse_json(_json_text(response))


def _request_compatible_chat(
    config: dict[str, str],
    model: str,
    instructions: str,
    user_payload: dict[str, Any],
    request: Callable[..., Any],
) -> dict[str, Any]:
    endpoint = f"{config['base_url'].rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if config.get("api_key"):
        headers["Authorization"] = f"Bearer {config['api_key']}"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": instructions},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
    }
    response = request("POST", endpoint, headers=headers, json=body, timeout=120)
    if response.status_code == 400:
        body.pop("response_format")
        response = request("POST", endpoint, headers=headers, json=body, timeout=120)
    return _parse_json(_json_text(response))


def _schema_errors(value: Any, schema: dict[str, Any], path: str = "$", errors: list[str] | None = None) -> list[str]:
    """Validate the JSON Schema subset used by provider contracts without optional dependencies."""

    errors = errors if errors is not None else []
    expected = schema.get("type")
    type_map = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float)}
    if expected and (not isinstance(value, type_map[expected]) or isinstance(value, bool)):
        errors.append(f"{path} must be {expected}")
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path} must equal {schema['const']}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path} is not an allowed value")
    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}.{key} is required")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}.{key} is not allowed")
        for key, item in value.items():
            if key in properties:
                _schema_errors(item, properties[key], f"{path}.{key}", errors)
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path} has too few items")
        if len(value) > schema.get("maxItems", len(value)):
            errors.append(f"{path} has too many items")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{path} contains duplicate items")
        for index, item in enumerate(value):
            _schema_errors(item, schema.get("items", {}), f"{path}[{index}]", errors)
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path} is too short")
        if len(value) > schema.get("maxLength", len(value)):
            errors.append(f"{path} is too long")
        if schema.get("pattern") and not re.fullmatch(schema["pattern"], value):
            errors.append(f"{path} has an invalid identifier")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path} is below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path} exceeds maximum")
    return errors


def _invoke(
    provider: str,
    task: str,
    settings: dict[str, Any],
    instructions: str,
    user_payload: dict[str, Any],
    schema: dict[str, Any],
    request: Callable[..., Any],
) -> ProviderResult:
    model = resolve_model(settings, provider, task)
    if provider == "rules":
        return ProviderResult(provider, model, "rules")
    config = provider_config(settings, provider)
    if not config.get("base_url"):
        return ProviderResult(provider, model, "pending", warnings=["External Agent endpoint is not configured."])
    if provider not in {"local", "external-agent"} and not config.get("api_key"):
        return ProviderResult(provider, model, "fallback", warnings=[f"{provider} API key is not configured."])
    try:
        contract_payload = dict(user_payload)
        contract_payload["required_output_schema"] = schema
        if provider == "openai":
            payload = _request_openai_responses(
                config, model, instructions, contract_payload, f"hedgehog_{task}", schema, request
            )
        else:
            payload = _request_compatible_chat(config, model, instructions, contract_payload, request)
        errors = _schema_errors(payload, schema)
        if errors:
            detail = "; ".join(errors[:3])
            return ProviderResult(provider, model, "fallback", warnings=[f"Structured output failed validation: {detail}"])
        return ProviderResult(provider, model, "generated", payload=payload)
    except (OSError, ValueError, URLError, json.JSONDecodeError) as exc:
        return ProviderResult(provider, model, "fallback", warnings=[f"Provider request failed: {exc}"])


def content_instructions() -> str:
    return (
        "You are the semantic content provider inside Hedgehog Master. Return only JSON matching the supplied "
        "schema. Synthesize a concise research narrative from the registered evidence. Every factual claim must "
        "reference one or more evidence_ids exactly as supplied. For every claim, report word_count and "
        "character_count excluding whitespace. Never invent citations, page numbers, slide "
        "geometry, fonts, colors, coordinates, or rendering code. Use the language requested by the brief; "
        "otherwise use formal academic English. For prose with an explicit target length, place it in one bullet "
        "on the most relevant section slide and respect the requested word or character count."
    )


def diagram_instructions() -> str:
    return (
        "You are the scientific diagram planner inside Hedgehog Master. Return only Diagram IR 0.2 JSON matching "
        "the supplied schema. Choose among dataflow, cycle, comparison, architecture, and timeline. Keep labels "
        "formal, compact, and presentation-ready. Use evidenceRef only when it exactly matches a supplied "
        "evidence_id; otherwise return an empty evidenceRef. Never return SVG, coordinates, style attributes, "
        "Mermaid, or rendering code; the local "
        "Harness owns layout and compilation."
    )


def generate_content(
    provider: str,
    settings: dict[str, Any],
    context: dict[str, Any],
    request: Callable[..., Any] = default_request,
) -> ProviderResult:
    return _invoke(provider, "content", settings, content_instructions(), context, CONTENT_SCHEMA, request)


def generate_diagram(
    provider: str,
    settings: dict[str, Any],
    context: dict[str, Any],
    request: Callable[..., Any] = default_request,
) -> ProviderResult:
    return _invoke(provider, "diagram", settings, diagram_instructions(), context, DIAGRAM_SCHEMA, request)


def write_external_request(path: Path, task: str, provider: str, model: str, context: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "task": task,
                "provider": provider,
                "model": model,
                "input": context,
                "required_output_schema": CONTENT_SCHEMA if task == "content" else DIAGRAM_SCHEMA,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

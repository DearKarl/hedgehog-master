#!/usr/bin/env python3
"""Local provider routing and secret storage for Hedgehog Master."""

from __future__ import annotations

import copy
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SETTINGS_VERSION = "1.0"
CONTENT_PROVIDERS = ("rules", "openai", "gemini", "qwen", "zhipu", "local", "external-agent")
DIAGRAM_PROVIDERS = CONTENT_PROVIDERS
IMAGE_PROVIDERS = ("manual", "openai", "gemini", "qwen", "zhipu", "minimax")
STOCK_PROVIDERS = ("none", "pexels", "pixabay")
NARRATION_PROVIDERS = ("none", "edge", "elevenlabs", "minimax", "qwen")


DEFAULT_SETTINGS: dict[str, Any] = {
    "schema_version": SETTINGS_VERSION,
    "routing": {
        "content": "rules",
        "diagram": "rules",
        "image": "manual",
        "stock": "none",
        "narration": "none",
    },
    "services": {
        "openai": {
            "api_key": "",
            "content_model": "gpt-5.4-mini",
            "diagram_model": "gpt-5.4-mini",
            "image_model": "gpt-image-2",
            "base_url": "https://api.openai.com/v1",
        },
        "gemini": {
            "api_key": "",
            "content_model": "gemini-2.5-flash",
            "diagram_model": "gemini-2.5-flash",
            "image_model": "gemini-3.1-flash-image-preview",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "image_base_url": "",
        },
        "qwen": {
            "api_key": "",
            "content_model": "qwen-plus",
            "diagram_model": "qwen-plus",
            "image_model": "qwen-image-2.0-pro",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "image_base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
        },
        "zhipu": {
            "api_key": "",
            "content_model": "glm-4-flash",
            "diagram_model": "glm-4-flash",
            "image_model": "glm-image",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "image_base_url": "https://open.bigmodel.cn/api/paas/v4/images/generations",
        },
        "local": {
            "api_key": "",
            "content_model": "qwen3:8b",
            "diagram_model": "qwen3:8b",
            "base_url": "http://127.0.0.1:11434/v1",
        },
        "external-agent": {
            "api_key": "",
            "content_model": "agent-managed",
            "diagram_model": "agent-managed",
            "base_url": "",
        },
        "minimax": {
            "api_key": "",
            "image_model": "image-01",
            "narration_model": "speech-02-hd",
            "image_base_url": "https://api.minimaxi.com/v1/image_generation",
            "narration_base_url": "https://api.minimaxi.com/v1/t2a_v2",
        },
        "pexels": {"api_key": ""},
        "pixabay": {"api_key": ""},
        "elevenlabs": {"api_key": "", "narration_model": "eleven_multilingual_v2"},
        "qwen-narration": {"api_key": "", "narration_model": "qwen3-tts-flash"},
    },
}


def settings_path() -> Path:
    override = os.environ.get("HEDGEHOG_MASTER_SETTINGS_FILE", "").strip()
    return Path(override).expanduser() if override else Path.home() / ".hedgehog-master" / "settings.json"


def _merge_known(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in incoming.items():
        if key not in result:
            continue
        if isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_known(result[key], value)
        elif isinstance(value, type(result[key])):
            result[key] = value
    return result


def _validate_url(value: str, field: str) -> str:
    value = value.strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field} must be an http(s) URL")
    return value.rstrip("/")


def _validate(settings: dict[str, Any]) -> dict[str, Any]:
    routing = settings["routing"]
    allowed = {
        "content": CONTENT_PROVIDERS,
        "diagram": DIAGRAM_PROVIDERS,
        "image": IMAGE_PROVIDERS,
        "stock": STOCK_PROVIDERS,
        "narration": NARRATION_PROVIDERS,
    }
    for field, choices in allowed.items():
        if routing[field] not in choices:
            raise ValueError(f"Unsupported {field} provider: {routing[field]}")
    for service, config in settings["services"].items():
        for key, value in list(config.items()):
            if not isinstance(value, str):
                raise ValueError(f"services.{service}.{key} must be text")
            config[key] = value.strip()
            if key.endswith("base_url"):
                config[key] = _validate_url(config[key], f"services.{service}.{key}")
            if key.endswith("model") and len(config[key]) > 160:
                raise ValueError(f"services.{service}.{key} is too long")
            if key == "api_key" and len(config[key]) > 4096:
                raise ValueError(f"services.{service}.api_key is too long")
    settings["schema_version"] = SETTINGS_VERSION
    return settings


def load_settings() -> dict[str, Any]:
    path = settings_path()
    if not path.is_file():
        return copy.deepcopy(DEFAULT_SETTINGS)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return copy.deepcopy(DEFAULT_SETTINGS)
    if not isinstance(payload, dict):
        return copy.deepcopy(DEFAULT_SETTINGS)
    return _validate(_merge_known(DEFAULT_SETTINGS, payload))


def save_settings(update: dict[str, Any]) -> dict[str, Any]:
    """Merge a public UI update while preserving secrets left blank."""

    if not isinstance(update, dict):
        raise ValueError("Settings payload must be an object")
    current = load_settings()
    routing = update.get("routing")
    if isinstance(routing, dict):
        current["routing"] = _merge_known(current["routing"], routing)
    services = update.get("services")
    if isinstance(services, dict):
        for service, incoming in services.items():
            if service not in current["services"] or not isinstance(incoming, dict):
                continue
            target = current["services"][service]
            for field, value in incoming.items():
                if field == "clear_api_key" and value is True:
                    target["api_key"] = ""
                elif field in target and isinstance(value, str):
                    if field == "api_key" and not value.strip():
                        continue
                    target[field] = value
    validated = _validate(current)
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    fd, temporary = tempfile.mkstemp(prefix="settings-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(validated, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return validated


def public_settings(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return settings metadata without exposing stored credentials."""

    result = copy.deepcopy(settings or load_settings())
    for config in result["services"].values():
        key = config.pop("api_key", "")
        config["configured"] = bool(key)
        config["key_hint"] = f"...{key[-4:]}" if len(key) >= 4 else ("set" if key else "")
    result["catalog"] = {
        "content": list(CONTENT_PROVIDERS),
        "diagram": list(DIAGRAM_PROVIDERS),
        "image": list(IMAGE_PROVIDERS),
        "stock": list(STOCK_PROVIDERS),
        "narration": list(NARRATION_PROVIDERS),
    }
    result["storage"] = str(settings_path())
    return result


def resolve_model(settings: dict[str, Any], provider: str, task: str) -> str:
    if provider == "rules":
        return "hedgehog-rules-v1"
    return str((settings.get("services", {}).get(provider) or {}).get(f"{task}_model") or "")


def provider_config(settings: dict[str, Any], provider: str) -> dict[str, str]:
    return dict(settings.get("services", {}).get(provider) or {})


def settings_environment(settings: dict[str, Any] | None = None) -> dict[str, str]:
    """Map UI settings to the existing image/search/narration environment."""

    settings = settings or load_settings()
    services = settings["services"]
    env: dict[str, str] = {}
    image = settings["routing"]["image"]
    if image != "manual":
        env["IMAGE_BACKEND"] = image
    prefixes = {
        "openai": "OPENAI",
        "gemini": "GEMINI",
        "qwen": "QWEN",
        "zhipu": "ZHIPU",
        "minimax": "MINIMAX",
    }
    for service, prefix in prefixes.items():
        config = services[service]
        if config.get("api_key"):
            env[f"{prefix}_API_KEY"] = config["api_key"]
        if config.get("image_model"):
            env[f"{prefix}_MODEL"] = config["image_model"]
        image_base = config.get("image_base_url") if "image_base_url" in config else config.get("base_url")
        if image_base:
            env[f"{prefix}_BASE_URL"] = image_base
    if services["pexels"].get("api_key"):
        env["PEXELS_API_KEY"] = services["pexels"]["api_key"]
    if services["pixabay"].get("api_key"):
        env["PIXABAY_API_KEY"] = services["pixabay"]["api_key"]
    if services["elevenlabs"].get("api_key"):
        env["ELEVENLABS_API_KEY"] = services["elevenlabs"]["api_key"]
    if services["minimax"].get("api_key"):
        env["MINIMAX_API_KEY"] = services["minimax"]["api_key"]
    qwen_voice = services["qwen-narration"]
    if qwen_voice.get("api_key"):
        env.setdefault("QWEN_API_KEY", qwen_voice["api_key"])
    return {key: value for key, value in env.items() if value}


def safe_provider_id(value: str, choices: tuple[str, ...], fallback: str = "rules") -> str:
    normalized = re.sub(r"[^a-z-]", "", str(value).strip().lower())
    return normalized if normalized in choices else fallback

#!/usr/bin/env python3
"""Local semantic planner for Hedgehog Master research projects."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


SCHEMA_ROOT = "../../../skills/hedgehog-master/research/schemas"
CLAIM_TERMS = re.compile(
    r"\b(show|shows|shown|demonstrate|demonstrates|propose|proposes|introduce|"
    r"introduces|achieve|achieves|improve|improves|increase|increases|reduce|"
    r"reduces|outperform|outperforms|evaluate|evaluates|find|finds|result|results)\b",
    re.IGNORECASE,
)
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
FORMULA_PATTERNS = (
    re.compile(r"\$\$(.+?)\$\$", re.DOTALL),
    re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL),
    re.compile(r"\\\[(.+?)\\\]", re.DOTALL),
    re.compile(r"\\begin\{equation\*?\}(.+?)\\end\{equation\*?\}", re.DOTALL),
)
IMAGE_TERMS = re.compile(
    r"\b(image|illustration|visual|photo|render|cover art|scientific scene)\b|配图|插图|封面图|示意图",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PageText:
    page: int
    text: str


@dataclass(frozen=True)
class ExtractedDocument:
    title: str
    pages: list[PageText]
    authors: list[str]
    doi: str | None
    references: list[dict[str, str]]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clean_text(value: str) -> str:
    value = value.replace("\x00", " ").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _title_from_text(text: str, fallback: str) -> str:
    for raw_line in text.splitlines():
        line = re.sub(r"^#{1,6}\s*", "", raw_line).strip()
        if 6 <= len(line) <= 180 and not line.lower().startswith(("abstract", "keywords")):
            return line
    return fallback


def _extract_references(text: str) -> list[dict[str, str]]:
    match = re.search(r"(?im)^\s*(references|bibliography)\s*$", text)
    if not match:
        return []
    entries: list[dict[str, str]] = []
    for line in text[match.end() :].splitlines():
        cleaned = re.sub(r"^\s*(?:\[?\d+\]?|\d+\.)\s*", "", line).strip()
        if len(cleaned) < 24:
            continue
        doi_match = DOI_RE.search(cleaned)
        item = {"raw": cleaned[:500]}
        if doi_match:
            item["doi"] = doi_match.group(0).rstrip(".,;)")
        entries.append(item)
        if len(entries) >= 40:
            break
    return entries


def _extract_pdf(path: Path) -> ExtractedDocument:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF research intake") from exc

    pages: list[PageText] = []
    with fitz.open(path) as document:
        metadata = document.metadata or {}
        for index, page in enumerate(document, start=1):
            pages.append(PageText(index, _clean_text(page.get_text("text"))))
    joined = "\n\n".join(page.text for page in pages)
    title = str(metadata.get("title") or "").strip() or _title_from_text(joined, path.stem)
    author_value = str(metadata.get("author") or "").strip()
    authors = [item.strip() for item in re.split(r"[,;]", author_value) if item.strip()]
    doi_match = DOI_RE.search(joined[:20000])
    return ExtractedDocument(
        title=title,
        pages=pages,
        authors=authors,
        doi=doi_match.group(0).rstrip(".,;)") if doi_match else None,
        references=_extract_references(joined),
    )


def _extract_docx(path: Path) -> ExtractedDocument:
    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
        paragraphs = []
        for paragraph in root.iter(f"{{{namespace}}}p"):
            text = "".join(node.text or "" for node in paragraph.iter(f"{{{namespace}}}t"))
            if text.strip():
                paragraphs.append(text.strip())
    joined = _clean_text("\n".join(paragraphs))
    doi_match = DOI_RE.search(joined)
    return ExtractedDocument(
        title=_title_from_text(joined, path.stem),
        pages=[PageText(1, joined)],
        authors=[],
        doi=doi_match.group(0).rstrip(".,;)") if doi_match else None,
        references=_extract_references(joined),
    )


def extract_document(path: Path) -> ExtractedDocument:
    extension = path.suffix.lower()
    if extension == ".pdf":
        return _extract_pdf(path)
    if extension == ".docx":
        return _extract_docx(path)
    text = _clean_text(path.read_text(encoding="utf-8", errors="replace"))
    doi_match = DOI_RE.search(text)
    return ExtractedDocument(
        title=_title_from_text(text, path.stem),
        pages=[PageText(1, text)],
        authors=[],
        doi=doi_match.group(0).rstrip(".,;)") if doi_match else None,
        references=_extract_references(text),
    )


def _sentences(text: str) -> list[str]:
    without_headings = re.sub(r"(?m)^\s*#{1,6}\s+.+$", ". ", text)
    compact = re.sub(r"\s+", " ", without_headings).strip(" .")
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", compact) if item.strip()]


def _claim_score(sentence: str) -> int:
    score = 0
    if CLAIM_TERMS.search(sentence):
        score += 3
    if re.search(r"\b\d+(?:\.\d+)?\s*(?:%|ms|s|x|dB|mm|cm|nm|K|M|B)\b", sentence):
        score += 2
    if re.search(r"\b(method|model|framework|algorithm|experiment|dataset|analysis)\b", sentence, re.I):
        score += 1
    if sentence.lower().startswith(("figure ", "table ", "copyright ")):
        score -= 3
    return score


def _claims_from_document(source_id: str, document: ExtractedDocument, limit: int = 6) -> list[dict[str, Any]]:
    candidates: list[tuple[int, int, str]] = []
    for page in document.pages:
        for sentence in _sentences(page.text):
            if 45 <= len(sentence) <= 320:
                score = _claim_score(sentence)
                if score > 0:
                    candidates.append((score, page.page, sentence))
    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for score, page, sentence in candidates:
        signature = re.sub(r"\W+", "", sentence.lower())[:120]
        if signature in seen:
            continue
        seen.add(signature)
        claim_id = f"claim-{source_id}-{len(selected) + 1}"
        selected.append(
            {
                "id": claim_id,
                "text": sentence,
                "status": "verified",
                "source_ids": [source_id],
                "evidence": f"Exact statement extracted from {source_id}, page {page}.",
                "citations": [
                    {
                        "source_id": source_id,
                        "locator": f"page {page}",
                        "page": page,
                        "excerpt": sentence,
                    }
                ],
                "confidence": min(0.99, 0.68 + score * 0.06),
            }
        )
        if len(selected) >= limit:
            break
    return selected


def _node_role(name: str, index: int, total: int) -> str:
    lowered = name.lower()
    if index == 0 or any(token in lowered for token in ("load", "read", "input", "source", "parse")):
        return "source"
    if index == total - 1 or any(token in lowered for token in ("save", "write", "output", "export", "return")):
        return "output"
    if any(token in lowered for token in ("train", "model", "predict", "infer", "network")):
        return "model"
    if any(token in lowered for token in ("score", "metric", "evaluate", "validate", "test")):
        return "metric"
    return "transform"


def _safe_id(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
    if not cleaned or not cleaned[0].isalpha():
        cleaned = f"n-{cleaned or fallback}"
    return cleaned[:64]


def _python_structure(path: Path) -> tuple[list[str], list[tuple[str, str]], list[tuple[int, str]]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text)
    functions = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    defined = set(functions)
    calls: list[tuple[str, str]] = []
    summaries: list[tuple[int, str]] = []
    if functions:
        summaries.append(
            (
                1,
                f"{path.name} defines {len(functions)} callable stage(s): {', '.join(functions[:6])}.",
            )
        )
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        callees = {
            call.func.id
            for call in ast.walk(node)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id in defined
        }
        calls.extend((node.name, callee) for callee in sorted(callees))
        controls = sum(isinstance(item, (ast.If, ast.For, ast.While, ast.Try)) for item in ast.walk(node))
        if callees:
            summaries.append(
                (
                    node.lineno,
                    f"{node.name} orchestrates the following declared stage(s): {', '.join(sorted(callees))}.",
                )
            )
        elif controls:
            summaries.append((node.lineno, f"{node.name} implements {controls} explicit control-flow block(s)."))
    return functions, calls, summaries


def _generic_code_structure(path: Path) -> tuple[list[str], list[tuple[str, str]], list[tuple[int, str]]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    patterns = (
        r"(?m)^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"(?m)^\s*(?:def|fn|func)\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"(?m)^\s*(?:public|private|protected|static|async|\s)+[\w<>\[\], ?]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    )
    names: list[str] = []
    for pattern in patterns:
        names.extend(re.findall(pattern, text))
    names = list(dict.fromkeys(names))[:10]
    if not names:
        names = ["Input", "Processing", "Output"]
    edges = list(zip(names, names[1:]))
    return names, edges, [(1, f"{path.name} defines {len(names)} detected code stage(s): {', '.join(names)}.")]


def _code_structure(path: Path) -> tuple[list[str], list[tuple[str, str]], list[tuple[int, str]]]:
    if path.suffix.lower() == ".py":
        try:
            result = _python_structure(path)
            if result[0]:
                return result
        except (SyntaxError, ValueError):
            pass
    return _generic_code_structure(path)


def _diagram_kind(brief: str, has_code: bool) -> str:
    lowered = brief.lower()
    if re.search(r"\bcycle|feedback loop|iterative|iteration\b|循环|闭环|迭代", lowered):
        return "cycle"
    if re.search(r"\bcompare|comparison|versus|\bvs\.?\b|对比|比较", lowered):
        return "comparison"
    if re.search(r"\btimeline|roadmap|milestone|chronolog|时间线|里程碑", lowered):
        return "timeline"
    if has_code or re.search(r"\barchitecture|system map|module|component|架构|系统图|模块", lowered):
        return "architecture"
    return "dataflow"


def _brief_stages(brief: str) -> list[str]:
    candidates = []
    for chunk in re.split(r"(?:\n+|\s*(?:->|→|=>)\s*|[.;])", brief):
        cleaned = re.sub(r"^\s*(?:\d+[.)]|[-*])\s*", "", chunk).strip()
        parts = re.split(r"\s*,\s*|\s+and\s+", cleaned, flags=re.I) if len(cleaned) > 80 else [cleaned]
        candidates.extend(part for part in parts if 3 <= len(part) <= 80)
    unique = list(dict.fromkeys(candidates))
    return unique[:7] if len(unique) >= 2 else ["Research inputs", "Evidence synthesis", "Presentation output"]


def _diagram_from_inputs(brief: str, code_paths: list[Path]) -> tuple[dict[str, Any], list[str]]:
    kind = _diagram_kind(brief, bool(code_paths))
    names: list[str] = []
    raw_edges: list[tuple[str, str]] = []
    summaries: list[str] = []
    for path in code_paths:
        path_names, path_edges, path_summaries = _code_structure(path)
        names.extend(path_names)
        raw_edges.extend(path_edges)
        summaries.extend(summary for _, summary in path_summaries)
    names = list(dict.fromkeys(names))[:10]
    if not names:
        names = _brief_stages(brief)
        raw_edges = list(zip(names, names[1:]))
    if kind == "comparison" and len(names) < 4:
        left, right = (re.split(r"\b(?:versus|vs\.?)\b|对比|比较", brief, maxsplit=1, flags=re.I) + [""])[:2]
        names = [
            (left.strip() or "Approach A")[:50],
            "Evidence for A",
            (right.strip() or "Approach B")[:50],
            "Evidence for B",
        ]
        raw_edges = [(names[0], names[1]), (names[2], names[3])]
    node_ids: dict[str, str] = {}
    nodes = []
    for index, name in enumerate(names):
        node_id = _safe_id(name, str(index + 1))
        while node_id in node_ids.values():
            node_id = f"{node_id}-{index + 1}"
        node_ids[name] = node_id
        node = {"id": node_id, "label": name[:90], "role": _node_role(name, index, len(names))}
        if kind == "comparison":
            node["group"] = "A" if index < (len(names) + 1) // 2 else "B"
        nodes.append(node)
    edges = []
    for source, target in raw_edges:
        if source not in node_ids or target not in node_ids or source == target:
            continue
        edges.append(
            {
                "id": _safe_id(f"{node_ids[source]}-{node_ids[target]}", str(len(edges) + 1)),
                "from": node_ids[source],
                "to": node_ids[target],
            }
        )
    if not edges and len(nodes) > 1:
        edges = [
            {"id": f"edge-{index + 1}", "from": nodes[index]["id"], "to": nodes[index + 1]["id"]}
            for index in range(len(nodes) - 1)
        ]
    if kind == "cycle" and len(nodes) > 2:
        edges.append({"id": "cycle-close", "from": nodes[-1]["id"], "to": nodes[0]["id"]})
    direction = {"cycle": "clockwise", "architecture": "top-to-bottom"}.get(kind, "left-to-right")
    return (
        {
            "irVersion": "0.2",
            "id": "planned-research-diagram",
            "title": "Research workflow",
            "kind": kind,
            "direction": direction,
            "nodes": nodes,
            "edges": edges,
            "metadata": {"planner": "hedgehog-local-v1", "source": "brief-and-code"},
        },
        summaries,
    )


def _extract_formulas(
    documents: list[tuple[str, ExtractedDocument]],
    brief: str,
    render_mode: str,
) -> list[dict[str, Any]]:
    candidates: list[tuple[str, str, str]] = []
    for source_id, document in documents:
        for page in document.pages:
            for pattern in FORMULA_PATTERNS:
                for match in pattern.finditer(page.text):
                    candidates.append((source_id, f"page {page.page}", _clean_text(match.group(1))))
    for pattern in FORMULA_PATTERNS:
        for match in pattern.finditer(brief):
            candidates.append(("brief", "presentation brief", _clean_text(match.group(1))))
    items = []
    seen: set[str] = set()
    for source_id, locator, latex in candidates:
        if (
            not latex
            or latex in seen
            or len(latex) > 500
            or re.fullmatch(r"[A-Za-z](?:_[A-Za-z0-9]+)?", latex)
        ):
            continue
        seen.add(latex)
        index = len(items) + 1
        items.append(
            {
                "id": f"formula-{index}",
                "latex": latex,
                "display": "block",
                "render_mode": render_mode,
                "filename": f"formula_{index:03d}.png",
                "status": "Pending" if render_mode == "raster" else "Ready",
                "source_id": source_id,
                "locator": locator,
                "slide_ids": ["formulation"],
            }
        )
        if len(items) >= 6:
            break
    return items


def _image_items(project_id: str, title: str, brief: str) -> list[dict[str, Any]]:
    if not IMAGE_TERMS.search(brief):
        return []
    return [
        {
            "id": "cover-visual",
            "filename": "cover_visual.png",
            "purpose": "Scientific cover visual",
            "page_role": "local",
            "text_policy": "none",
            "aspect_ratio": "16:9",
            "image_size": "1K",
            "prompt": (
                f"Create a restrained publication-style scientific illustration for '{title}'. "
                f"Use the following research brief only for subject matter: {brief[:600]}. "
                "No text, no logos, no decorative border, white or transparent-looking background, "
                "precise technical forms, suitable as an embedded academic presentation asset."
            ),
            "alt_text": f"Scientific illustration for {title}",
            "status": "Pending",
            "slide_ids": ["cover"],
        }
    ]


def _brief_bullets(brief: str) -> list[str]:
    bullets = _brief_stages(brief)
    return [item[:180] for item in bullets[:5]]


def _takeaway_title(value: str, fallback: str, limit: int = 92) -> str:
    compact = re.sub(r"\s+", " ", value).strip().strip(".- ")
    if not compact:
        return fallback
    clause = re.split(r"[;:]|\bwhile\b|\bwhereas\b", compact, maxsplit=1, flags=re.I)[0].strip()
    if len(clause) <= limit:
        return clause[0].upper() + clause[1:]
    shortened = clause[: limit - 3].rsplit(" ", 1)[0].rstrip(" ,.;:")
    return (shortened or clause[: limit - 3]).strip() + "..."


def _summary_bullet(value: str, limit: int = 160) -> str:
    compact = re.sub(r"\s+", " ", value).strip()
    if len(compact) <= limit:
        return compact
    shortened = compact[: limit - 3].rsplit(" ", 1)[0].rstrip(" ,.;:")
    return (shortened or compact[: limit - 3]).strip() + "..."


def _storyboard(
    title: str,
    brief: str,
    claims: list[dict[str, Any]],
    diagram: dict[str, Any],
    formulas: list[dict[str, Any]],
    images: list[dict[str, Any]],
) -> dict[str, Any]:
    brief_sentences = _sentences(brief)
    opening = (brief_sentences or ["Evidence-linked scientific presentation"])[0][:220]
    central_claim = claims[0]["text"] if claims else opening
    diagram_title = {
        "dataflow": "The method connects inputs, analysis, and outputs",
        "cycle": "Iteration closes the loop between evidence and refinement",
        "comparison": "The alternatives differ along explicit evidence paths",
        "architecture": "The system separates responsibilities across components",
        "timeline": "The research program advances through defined milestones",
    }[diagram["kind"]]
    slides: list[dict[str, Any]] = [
        {
            "id": "cover",
            "layout": "cover",
            "title": title,
            "subtitle": opening,
            **({"image_ids": ["cover-visual"]} if images else {}),
        },
        {
            "id": "objective",
            "layout": "section",
            "title": "The research question defines a focused analytical path",
            "subtitle": _takeaway_title(central_claim, "Research objective and scope", 180),
            "bullets": _brief_bullets(brief),
        },
        {
            "id": "method-diagram",
            "layout": "diagram",
            "title": diagram_title,
            "subtitle": _takeaway_title(central_claim, "Method overview", 180),
            "diagram": "research/diagrams/planned.diagram.json",
            "claim_ids": [claim["id"] for claim in claims[:1]],
        },
    ]
    if formulas:
        slides.append(
            {
                "id": "formulation",
                "layout": "evidence",
                "title": "The formulation makes the central relationship explicit",
                "subtitle": "Variables and assumptions should be interpreted against the cited evidence.",
                "formula_ids": [item["id"] for item in formulas[:3]],
                "claim_ids": [claim["id"] for claim in claims[:1]],
            }
        )
    for index in range(0, min(len(claims), 6), 2):
        chunk = claims[index : index + 2]
        slides.append(
            {
                "id": f"evidence-{index // 2 + 1}",
                "layout": "evidence",
                "title": _takeaway_title(chunk[0]["text"], "Evidence-backed finding"),
                "subtitle": "The cited source provides the basis for this conclusion.",
                "claim_ids": [claim["id"] for claim in chunk],
            }
        )
    slides.append(
        {
            "id": "closing",
            "layout": "closing",
            "title": f"Implications for {title}"[:110],
            "subtitle": "The next step is to test generalization, limitations, and reproducibility.",
            "bullets": [
                _summary_bullet(claim["text"])
                for claim in ([claims[0], claims[-1]] if len(claims) > 1 else claims)
            ],
        }
    )
    return {
        "$schema": f"{SCHEMA_ROOT}/deck.schema.json",
        "schema_version": "1.1",
        "slides": slides,
    }


def plan_project(project: Path) -> dict[str, Any]:
    """Derive research contracts from a project-local brief, papers, and code."""

    manifest_path = project / "project.json"
    manifest = _read_json(manifest_path)
    brief = str((manifest.get("brief") or {}).get("instructions") or "").strip()
    title = str(manifest.get("title") or project.name)
    warnings: list[str] = []
    sources = [
        {
            "id": "brief",
            "title": "Presentation brief",
            "type": "local",
            "locator": "inputs/instructions.md",
            "sha256": _sha256(project / "inputs" / "instructions.md"),
        }
    ]
    claims: list[dict[str, Any]] = []
    documents: list[tuple[str, ExtractedDocument]] = []
    code_paths: list[Path] = []
    code_summaries: list[tuple[str, int, str]] = []

    for item in manifest.get("inputs", []):
        input_path = (project / item["path"]).resolve()
        if item.get("kind") == "paper":
            source_id = item["id"]
            try:
                document = extract_document(input_path)
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                warnings.append(f"Could not extract {item['name']}: {exc}")
                document = ExtractedDocument(item["name"], [], [], None, [])
            documents.append((source_id, document))
            source = {
                "id": source_id,
                "title": document.title or item["name"],
                "type": "paper",
                "locator": item["path"],
                "sha256": _sha256(input_path),
                "metadata": {"references": document.references},
            }
            if document.pages:
                source["page_count"] = len(document.pages)
            if document.authors:
                source["authors"] = document.authors
            if document.doi:
                source["doi"] = document.doi
            sources.append(source)
            claims.extend(_claims_from_document(source_id, document))
        elif item.get("kind") == "code":
            source_id = item["id"]
            code_paths.append(input_path)
            names, _, summaries = _code_structure(input_path)
            sources.append(
                {
                    "id": source_id,
                    "title": item["name"],
                    "type": "code",
                    "locator": item["path"],
                    "sha256": _sha256(input_path),
                    "metadata": {"language": item.get("language"), "symbols": names},
                }
            )
            for line, summary in summaries[:2]:
                code_summaries.append((source_id, line, summary))

    for source_id, line, summary in code_summaries[:4]:
        claims.append(
            {
                "id": f"claim-{source_id}-structure-{len(claims) + 1}",
                "text": summary,
                "status": "verified",
                "source_ids": [source_id],
                "evidence": "Statement derived from the local abstract syntax or symbol structure.",
                "citations": [
                    {
                        "source_id": source_id,
                        "locator": f"line {line}",
                        "line": line,
                        "excerpt": summary,
                    }
                ],
                "confidence": 0.9,
            }
        )

    if not claims:
        statement = (_sentences(brief) or [brief or "Create a formal research presentation."])[0][:320]
        claims.append(
            {
                "id": "claim-brief-objective",
                "text": statement,
                "status": "draft",
                "source_ids": ["brief"],
                "evidence": "Presentation objective supplied by the user; independent verification is required.",
                "citations": [
                    {"source_id": "brief", "locator": "presentation brief", "line": 1, "excerpt": statement}
                ],
                "confidence": 0.5,
            }
        )

    diagram, diagram_summaries = _diagram_from_inputs(brief, code_paths)
    formula_rendering = str((manifest.get("policy") or {}).get("formula_rendering") or "editable-text")
    formulas = _extract_formulas(documents, brief, formula_rendering)
    images = _image_items(manifest["id"], title, brief)
    deck = _storyboard(title, brief, claims, diagram, formulas, images)

    _write_json(
        project / "research" / "sources.json",
        {"$schema": f"{SCHEMA_ROOT}/sources.schema.json", "schema_version": "1.1", "sources": sources},
    )
    _write_json(
        project / "research" / "claims.json",
        {"$schema": f"{SCHEMA_ROOT}/claims.schema.json", "schema_version": "1.1", "claims": claims},
    )
    _write_json(project / "storyboard" / "deck.json", deck)
    _write_json(project / "research" / "diagrams" / "planned.diagram.json", diagram)
    _write_json(
        project / "images" / "formula_manifest.json",
        {
            "$schema": f"{SCHEMA_ROOT}/formula-manifest.schema.json",
            "schema_version": "1.0",
            "items": formulas,
        },
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
    policy.setdefault("image_generation", "manual")
    policy.setdefault("formula_rendering", "editable-text")
    _write_json(manifest_path, manifest)

    report = {
        "schema_version": "1.0",
        "planner": "hedgehog-local-v1",
        "planned_on": date.today().isoformat(),
        "brief": brief,
        "sources": len(sources),
        "claims": len(claims),
        "slides": len(deck["slides"]),
        "diagram_kind": diagram["kind"],
        "formulas": len(formulas),
        "images": len(images),
        "code_analysis": diagram_summaries,
        "warnings": warnings,
    }
    _write_json(project / "analysis" / "plan.json", report)
    return report

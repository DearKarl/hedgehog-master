from pathlib import Path


def extract_documents(source_dir: Path) -> list[str]:
    return [path.read_text(encoding="utf-8") for path in source_dir.glob("*.md")]


def register_claims(documents: list[str]) -> list[str]:
    return [sentence for document in documents for sentence in document.split(".") if sentence.strip()]


def compile_diagram(claims: list[str]) -> dict[str, int]:
    return {"verified_claims": len(claims)}


def export_presentation(source_dir: Path) -> dict[str, int]:
    documents = extract_documents(source_dir)
    claims = register_claims(documents)
    return compile_diagram(claims)

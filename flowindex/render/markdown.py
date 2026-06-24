"""Markdown rendering helpers."""

from __future__ import annotations

from flowindex.schemas import ContextPack


def render_context_pack(pack: ContextPack) -> str:
    return pack.to_markdown()


def render_explain(data: dict[str, object]) -> str:
    lines = [f"# Flow: {data.get('title', 'Unknown')}", ""]
    if data.get("entrypoint"):
        lines.extend(["## Entrypoint", str(data["entrypoint"]), ""])
    if data.get("location"):
        lines.extend(["## Location", str(data["location"]), ""])
    execution_path = data.get("execution_path")
    if isinstance(execution_path, list):
        lines.extend(["## Execution path"])
        for i, step in enumerate(execution_path, 1):
            lines.append(f"{i}. {step}")
        lines.append("")
    tests = data.get("tests")
    if isinstance(tests, list):
        lines.extend(["## Tests"])
        lines.extend(f"- {t}" for t in tests)
        lines.append("")
    commits = data.get("commits")
    if isinstance(commits, list):
        lines.extend(["## Recent related patches"])
        lines.extend(f"- {c}" for c in commits)
        lines.append("")
    risk_notes = data.get("risk_notes")
    if isinstance(risk_notes, list):
        lines.extend(["## Risk notes"])
        lines.extend(f"- {n}" for n in risk_notes)
    return "\n".join(lines)

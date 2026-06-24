"""FlowIndex CLI."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from flowindex.config import find_project_root, load_config, write_default_config
from flowindex.db.migrations import migrate
from flowindex.db.session import get_session, init_db
from flowindex.indexer.context_pack import make_context_pack
from flowindex.indexer.explain import explain_target
from flowindex.indexer.impact import analyze_impact, suggest_tests
from flowindex.indexer.overview import build_overview
from flowindex.indexer.pipeline import run_scan
from flowindex.render.markdown import render_context_pack, render_explain
from flowindex.render.tables import print_impact, print_overview, print_scan_summary

app = typer.Typer(
    name="flowindex",
    help="Behavior-first repository indexing for AI coding agents.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def init(
    path: Path | None = typer.Argument(None, help="Repository root (default: git root or cwd)"),
    here: bool = typer.Option(False, "--here", help="Use current directory as repo root"),
) -> None:
    """Initialize FlowIndex in a repository."""
    root = find_project_root(path, here=here)
    config_path = write_default_config(root)
    db_path = root / ".flowindex" / "flowindex.db"
    init_db(db_path)
    migrate(db_path)
    console.print(f"[green]FlowIndex initialized[/green] at {root / '.flowindex'}")
    console.print(f"  Config: {config_path}")
    console.print(f"  Database: {db_path}")
    console.print("\nNext: [bold]flowindex scan[/bold]")


@app.command()
def scan(
    path: Path | None = typer.Argument(None, help="Repository root"),
    here: bool = typer.Option(False, "--here", help="Use nearest .flowindex from cwd"),
) -> None:
    """Scan repository and build behavior index."""
    try:
        config = load_config(path)
    except FileNotFoundError:
        root = find_project_root(path, here=here)
        console.print("[yellow]FlowIndex not initialized. Running init...[/yellow]")
        write_default_config(root)
        init_db(root / ".flowindex" / "flowindex.db")
        config = load_config(root)

    try:
        summary = run_scan(config)
    except Exception as exc:
        console.print(f"[red]Scan failed:[/red] {exc}")
        raise typer.Exit(1) from exc
    print_scan_summary(summary.model_dump())


@app.command()
def overview(
    path: Path | None = typer.Argument(None, help="Repository root"),
) -> None:
    """Show high-level repository map."""
    config = load_config(path)
    with get_session(config.db_path) as session:
        from sqlmodel import select

        from flowindex.db.models import Repository

        repo = session.exec(
            select(Repository).where(Repository.root_path == str(config.root_path.resolve()))
        ).first()
        if not repo or not repo.id:
            console.print("[red]No indexed repository found. Run `flowindex scan`.[/red]")
            raise typer.Exit(1)
        data = build_overview(session, repo.id)
    print_overview(data)


@app.command()
def explain(
    target: str = typer.Argument(..., help="Entrypoint, symbol, or file path"),
    path: Path | None = typer.Option(None, "--path", help="Repository root"),
) -> None:
    """Explain an entrypoint, symbol, or file flow."""
    config = load_config(path)
    with get_session(config.db_path) as session:
        from sqlmodel import select

        from flowindex.db.models import Repository

        repo = session.exec(
            select(Repository).where(Repository.root_path == str(config.root_path.resolve()))
        ).first()
        if not repo or not repo.id:
            console.print("[red]No indexed repository. Run `flowindex scan`.[/red]")
            raise typer.Exit(1)
        result = explain_target(session, repo.id, target)
    console.print(render_explain(result))


@app.command()
def impact(
    target: str = typer.Argument(..., help="File path or symbol name"),
    path: Path | None = typer.Option(None, "--path", help="Repository root"),
) -> None:
    """Show change impact and risk for a file or symbol."""
    config = load_config(path)
    with get_session(config.db_path) as session:
        from sqlmodel import select

        from flowindex.db.models import Repository

        repo = session.exec(
            select(Repository).where(Repository.root_path == str(config.root_path.resolve()))
        ).first()
        if not repo or not repo.id:
            console.print("[red]No indexed repository. Run `flowindex scan`.[/red]")
            raise typer.Exit(1)
        result = analyze_impact(session, repo.id, target)
    print_impact(result)


@app.command("tests-for")
def tests_for(
    target: str = typer.Argument(..., help="File path or symbol name"),
    path: Path | None = typer.Option(None, "--path", help="Repository root"),
) -> None:
    """Suggest tests to run for a change."""
    config = load_config(path)
    with get_session(config.db_path) as session:
        from sqlmodel import select

        from flowindex.db.models import Repository

        repo = session.exec(
            select(Repository).where(Repository.root_path == str(config.root_path.resolve()))
        ).first()
        if not repo or not repo.id:
            console.print("[red]No indexed repository. Run `flowindex scan`.[/red]")
            raise typer.Exit(1)
        tests = suggest_tests(session, repo.id, target)
    console.print(f"\n[bold]Suggested tests for:[/bold] {target}\n")
    for t in tests or ["(none found)"]:
        console.print(f"  - {t}")
    console.print()


@app.command()
def context(
    task: str = typer.Argument(..., help="Natural language task description"),
    path: Path | None = typer.Option(None, "--path", help="Repository root"),
) -> None:
    """Generate an AI-agent-ready context pack."""
    config = load_config(path)
    with get_session(config.db_path) as session:
        from sqlmodel import select

        from flowindex.db.models import Repository

        repo = session.exec(
            select(Repository).where(Repository.root_path == str(config.root_path.resolve()))
        ).first()
        if not repo or not repo.id:
            console.print("[red]No indexed repository. Run `flowindex scan`.[/red]")
            raise typer.Exit(1)
        pack = make_context_pack(session, repo.id, task)
    console.print(render_context_pack(pack))


@app.command()
def mcp(
    path: Path | None = typer.Option(None, "--path", help="Repository root"),
) -> None:
    """Start the FlowIndex MCP server for AI coding agents."""
    try:
        from flowindex.mcp.server import run_server
    except ImportError:
        console.print(
            "[red]MCP dependencies not installed.[/red] Run: pip install -e '.[mcp]'"
        )
        raise typer.Exit(1) from None
    config = load_config(path)
    run_server(config)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

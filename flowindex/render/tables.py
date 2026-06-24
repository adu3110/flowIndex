"""Rich table rendering."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

console = Console()


def print_scan_summary(summary: dict[str, int | str]) -> None:
    console.print("\n[bold green]FlowIndex scan complete[/bold green]\n")
    console.print(f"Files indexed: {summary['files_indexed']:,}")
    console.print(f"Symbols indexed: {summary['symbols_indexed']:,}")
    console.print(f"Entrypoints found: {summary['entrypoints_found']:,}")
    console.print(f"Tests found: {summary['tests_found']:,}")
    console.print(f"Git commits analyzed: {summary['git_commits_analyzed']:,}")
    console.print(f"Edges created: {summary['edges_created']:,}")
    console.print(f"Index: {summary['index_path']}\n")


def print_overview(data: dict[str, object]) -> None:
    table = Table(title="Repository Overview", show_header=True)
    table.add_column("Metric")
    table.add_column("Value")
    for key, value in data.items():
        if isinstance(value, list):
            if not value:
                table.add_row(key, "(none)")
            else:
                for i, item in enumerate(value):
                    label = key if i == 0 else ""
                    table.add_row(label, str(item))
        else:
            table.add_row(key, str(value))
    console.print(table)


def print_impact(result: object) -> None:
    from flowindex.schemas import ImpactResult

    assert isinstance(result, ImpactResult)
    console.print(f"\n[bold]Impact analysis:[/bold] {result.target}\n")
    console.print(f"[yellow]Risk:[/yellow] {result.risk.level.upper()} (score {result.risk.score})")
    for factor in result.risk.factors:
        console.print(f"  • {factor}")
    console.print("\n[bold]Entrypoints affected[/bold]")
    for ep in result.entrypoints_affected or ["(none)"]:
        console.print(f"  - {ep}")
    console.print("\n[bold]Downstream symbols[/bold]")
    for s in result.downstream_symbols or ["(none)"]:
        console.print(f"  - {s}")
    console.print("\n[bold]Upstream callers[/bold]")
    for s in result.upstream_callers or ["(none)"]:
        console.print(f"  - {s}")
    console.print("\n[bold]Related tests[/bold]")
    for t in result.related_tests or ["(none)"]:
        console.print(f"  - {t}")
    console.print("\n[bold]Changed together[/bold]")
    for f in result.changed_together_files or ["(none)"]:
        console.print(f"  - {f}")
    console.print("\n[bold]Recent commits[/bold]")
    for c in result.recent_commits or ["(none)"]:
        console.print(f"  - {c}")
    console.print()

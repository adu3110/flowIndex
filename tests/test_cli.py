"""CLI smoke tests."""

from pathlib import Path

from typer.testing import CliRunner

from flowindex.cli import app

runner = CliRunner()


def test_init_creates_flowindex_dir(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / ".flowindex" / "config.toml").exists()
    assert (tmp_path / ".flowindex" / "flowindex.db").exists()


def test_scan_on_example(fastapi_example: Path) -> None:
    result = runner.invoke(app, ["scan", str(fastapi_example)])
    assert result.exit_code == 0
    assert "FlowIndex scan complete" in result.stdout
    assert "Files indexed" in result.stdout


def test_overview_command(fastapi_example: Path) -> None:
    result = runner.invoke(app, ["overview", str(fastapi_example)])
    assert result.exit_code == 0
    assert "Repository Overview" in result.stdout


def test_context_command(fastapi_example: Path) -> None:
    result = runner.invoke(
        app,
        ["context", "fix duplicate payments when webhook retries", "--path", str(fastapi_example)],
    )
    assert result.exit_code == 0
    assert "FlowIndex Context Pack" in result.stdout

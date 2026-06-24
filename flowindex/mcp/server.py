"""FlowIndex MCP server."""

from __future__ import annotations

from flowindex.config import FlowIndexConfig
from flowindex.mcp import tools as mcp_tools


def run_server(config: FlowIndexConfig) -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install MCP support: pip install -e '.[mcp]'") from exc

    mcp = FastMCP("FlowIndex")

    @mcp.tool()
    def get_repo_overview() -> str:
        """Return a high-level overview of the indexed repository."""
        return mcp_tools.get_repo_overview(config)

    @mcp.tool()
    def explain_entrypoint(query: str) -> str:
        """Explain an API route, entrypoint, symbol, or file flow."""
        return mcp_tools.explain_entrypoint(config, query)

    @mcp.tool()
    def get_symbol_context(symbol: str) -> str:
        """Get context for a symbol including call paths and tests."""
        return mcp_tools.get_symbol_context(config, symbol)

    @mcp.tool()
    def get_change_impact(target: str) -> str:
        """Analyze change impact and risk for a file or symbol."""
        return mcp_tools.get_change_impact(config, target)

    @mcp.tool()
    def suggest_tests(target: str) -> str:
        """Suggest tests to run for a file or symbol change."""
        return mcp_tools.suggest_tests_tool(config, target)

    @mcp.tool()
    def find_related_patches(query: str) -> str:
        """Find git commits related to a file or topic."""
        return mcp_tools.find_related_patches(config, query)

    @mcp.tool()
    def make_context_pack(task: str) -> str:
        """Generate an AI-agent-ready context pack for a task description."""
        return mcp_tools.make_context_pack_tool(config, task)

    mcp.run()

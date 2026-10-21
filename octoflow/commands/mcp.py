"""MCP and MCP-Serve CLI commands for Model Context Protocol integration."""

import typer


def mcp_serve(workspace: str = typer.Option(".", "--dir", "-d", help="Workspace directory")):
    """Run OctoFlow as a Model Context Protocol (MCP) server for Claude Code and Cursor."""
    import asyncio
    from octoflow.mcp import OctoFlowMCPServer

    server = OctoFlowMCPServer(workspace_dir=workspace)
    asyncio.run(server.run_stdio())


def mcp_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace directory for the MCP server"),
):
    """Start OctoFlow as a Model Context Protocol (MCP) JSON-RPC 2.0 stdio server for Claude Code and Cursor."""
    import asyncio
    from octoflow.mcp import OctoFlowMCPServer

    server = OctoFlowMCPServer(workspace_dir=workspace)
    try:
        asyncio.run(server.run_stdio())
    except (KeyboardInterrupt, EOFError):
        pass


def register_mcp_serve(app: typer.Typer) -> None:
    """Register mcp-serve command with primary app."""
    app.command(name="mcp-serve")(mcp_serve)


def register_mcp(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register mcp command with both apps."""
    app.command("mcp")(mcp_cli_cmd)
    octos_app.command("mcp")(mcp_cli_cmd)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register mcp and mcp-serve commands with Typer apps."""
    register_mcp_serve(app)
    register_mcp(app, octos_app)

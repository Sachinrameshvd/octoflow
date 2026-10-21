"""UI CLI command for 3D Connectome Visualizer bridge."""

import time
import typer
from rich.console import Console

console = Console()


def ui(
    port: int = typer.Option(8088, "--port", "-p", help="Port to host 3D visualizer"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind 3D visualizer (default: 127.0.0.1)"),
):
    """Launch the 3D Cephalopod Connectome Visualizer bridge."""
    from octoflow.server import TelemetryBroadcaster
    host_str = host if isinstance(host, str) else "127.0.0.1"
    if host_str not in ("127.0.0.1", "localhost"):
        console.print(f"[bold red]▲ WARNING: Binding visualizer to '{host_str}' exposes the bridge to the network![/bold red]")
    url = f"http://{host_str}:{port}"
    console.print(f"\n[bold cyan]◈ Launching OctoFlow 3D Connectome Visualizer on {url}...[/bold cyan]")
    broadcaster = TelemetryBroadcaster(port=port, host=host_str)
    broadcaster.start_in_background()
    import webbrowser
    try:
        webbrowser.open(url)
    except Exception:
        pass
    console.print(f"● Visualizer opened in browser. Bridge active on {url}.")
    console.print(f"   [dim]Press Ctrl+C to stop.[/dim]\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\nStopped.")


def octos_ui(
    port: int = typer.Option(8088, "--port", "-p", help="Port to host 3D visualizer"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind 3D visualizer (default: 127.0.0.1)"),
):
    """Launch the 3D Cephalopod Constellation Visualizer bridge."""
    ui(port=port, host=host)


def register_app_ui(app: typer.Typer) -> None:
    """Register ui command with primary app."""
    app.command()(ui)


def register_octos_ui(octos_app: typer.Typer) -> None:
    """Register ui command with octos app."""
    octos_app.command("ui")(octos_ui)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register ui command with Typer apps."""
    register_app_ui(app)
    register_octos_ui(octos_app)

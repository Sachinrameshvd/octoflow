import os
import socket

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def clean_dry_run_env():
    orig_dry = os.environ.get("OCTOFLOW_DRY_RUN")
    orig_force = os.environ.get("OCTOFLOW_FORCE_LIVE")
    os.environ.pop("OCTOFLOW_DRY_RUN", None)
    os.environ.pop("OCTOFLOW_FORCE_LIVE", None)
    yield
    if orig_dry is not None:
        os.environ["OCTOFLOW_DRY_RUN"] = orig_dry
    else:
        os.environ.pop("OCTOFLOW_DRY_RUN", None)
    if orig_force is not None:
        os.environ["OCTOFLOW_FORCE_LIVE"] = orig_force
    else:
        os.environ.pop("OCTOFLOW_FORCE_LIVE", None)


@pytest.fixture(autouse=True)
def enforce_no_unmarked_network_sockets(request):
    """Guarantees zero unmocked network dependencies in default test runs (P4.1).

    Patches socket.create_connection to fail unless marked `live` or `integration_local`.
    """
    is_live = request.node.get_closest_marker("live") is not None
    is_local_int = request.node.get_closest_marker("integration_local") is not None

    if is_live or is_local_int:
        yield
        return

    orig_create_connection = socket.create_connection

    def blocked_create_connection(address, *args, **kwargs):
        host = address[0] if isinstance(address, (tuple, list)) else address
        port = address[1] if isinstance(address, (tuple, list)) and len(address) > 1 else ""
        raise RuntimeError(
            f"Blocked real network connection to {host}:{port} in default test run. "
            f"Ensure tests use ReplayProvider or mock fixtures, or mark with "
            f"@pytest.mark.live or @pytest.mark.integration_local."
        )

    socket.create_connection = blocked_create_connection
    try:
        yield
    finally:
        socket.create_connection = orig_create_connection

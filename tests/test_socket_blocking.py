"""Tests for P4.1 socket isolation and network blocking in default runs."""

import socket
import pytest


def test_unmarked_socket_attempt_fails_with_clear_message():
    """Acceptance criterion: A test that tries a real socket fails with a clear message."""
    with pytest.raises(RuntimeError) as exc_info:
        socket.create_connection(("example.com", 80), timeout=1)

    error_msg = str(exc_info.value)
    assert "Blocked real network connection to example.com:80 in default test run" in error_msg
    assert "Ensure tests use ReplayProvider or mock fixtures" in error_msg
    assert "@pytest.mark.live" in error_msg
    assert "@pytest.mark.integration_local" in error_msg


@pytest.mark.integration_local
def test_integration_local_allows_local_sockets():
    """Verify that @pytest.mark.integration_local is not blocked by conftest."""
    # Binding and connecting to local loopback socket should not raise the Blocked error
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
        conn = socket.create_connection(("127.0.0.1", port), timeout=2)
        conn.close()

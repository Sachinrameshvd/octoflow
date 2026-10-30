"""Test suite for OctoFlow error taxonomy, exit codes, and cockpit-safe logging.

Validates:
1. Process exit codes via CliRunner (ConfigError=3, UsageError=3, ProviderError=2, ToolError=1, WorkspaceError=1, BudgetExceeded=1, Unexpected=70).
2. Traceback suppression without --trace/OCTOFLOW_DEBUG and inclusion with --trace.
3. Rotating log file creation with 0600 file permissions and 0700 directory permissions.
4. Secret redaction filter across file handler and exception formatting.
5. Cockpit-safe suppression of terminal logging during interactive raw mode / PTY sessions.
"""

import logging
import os
import pty
import select

import pytest
import typer
from typer.testing import CliRunner

pytestmark = pytest.mark.unit

from octoflow.cli import OctoFlowGroup
from octoflow.errors import (
    BudgetExceeded,
    ConfigError,
    OctoFlowError,
    ProviderAuthError,
    ProviderError,
    ProviderExhaustedError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderTransientError,
    ProviderUnavailableError,
    ToolError,
    UsageError,
    WorkspaceError,
    redact_secrets,
)
from octoflow.logging_config import (
    CockpitSuppressFilter,
    SecureRotatingFileHandler,
    get_logger,
    is_cockpit_active,
    set_cockpit_active,
    setup_logging,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_log_file(tmp_path):
    log_dir = tmp_path / "logs"
    log_file = log_dir / "octoflow.log"
    return log_file


# =============================================================================
# 1. Error Taxonomy & Exit Codes
# =============================================================================


def test_error_hierarchy():
    """Verify inheritance taxonomy for all OctoFlow error families."""
    assert issubclass(ConfigError, OctoFlowError)
    assert issubclass(UsageError, OctoFlowError)
    assert issubclass(ToolError, OctoFlowError)
    assert issubclass(WorkspaceError, OctoFlowError)
    assert issubclass(BudgetExceeded, OctoFlowError)

    # Provider error family
    assert issubclass(ProviderError, OctoFlowError)
    assert issubclass(ProviderAuthError, ProviderError)
    assert issubclass(ProviderRateLimitError, ProviderError)
    assert issubclass(ProviderTransientError, ProviderError)
    assert issubclass(ProviderRequestError, ProviderError)
    assert issubclass(ProviderUnavailableError, ProviderError)
    assert issubclass(ProviderExhaustedError, ProviderError)


def test_error_default_exit_codes():
    """Verify standard default exit codes."""
    assert OctoFlowError("msg").exit_code == 1
    assert ConfigError("bad config").exit_code == 3
    assert UsageError("bad flag").exit_code == 3
    assert ProviderError("api fail").exit_code == 2
    assert ProviderAuthError("auth fail").exit_code == 2
    assert ProviderRateLimitError("rate limited").exit_code == 2
    assert ProviderTransientError("network drop").exit_code == 2
    assert ProviderRequestError("invalid payload").exit_code == 2
    assert ProviderUnavailableError("server offline").exit_code == 2
    assert ProviderExhaustedError("all failed").exit_code == 2
    assert ToolError("command failed").exit_code == 1
    assert WorkspaceError("escape attempted").exit_code == 1
    assert BudgetExceeded().exit_code == 1


def create_test_app():
    """Helper creating a test Typer app with OctoFlowGroup and standard callback."""
    test_app = typer.Typer(cls=OctoFlowGroup)

    @test_app.callback(invoke_without_command=True)
    def cb(
        ctx: typer.Context,
        verbose: bool = typer.Option(False, "--verbose", "-v"),
        trace: bool = typer.Option(False, "--trace"),
    ):
        setup_logging(verbose=verbose, trace=trace)

    return test_app


def test_cli_forced_config_error(runner):
    """A forced ConfigError prints message and hint, exits 3, and shows no traceback."""
    test_app = create_test_app()

    @test_app.command()
    def trigger_config_err():
        raise ConfigError(
            "Invalid model configuration",
            hint="Run 'octoflow setup' or check ~/.octoflow/config.json",
        )

    result = runner.invoke(test_app, ["trigger-config-err"])
    assert result.exit_code == 3
    assert "Invalid model configuration" in result.output
    assert "Hint: Run 'octoflow setup' or check ~/.octoflow/config.json" in result.output
    assert "Traceback (most recent call last)" not in result.output


def test_cli_forced_provider_error(runner):
    """A forced ProviderAuthError prints message and hint, exits 2, and shows no traceback."""
    test_app = create_test_app()

    @test_app.command()
    def trigger_provider_err():
        raise ProviderAuthError(
            "Invalid API key provided",
            hint="Export ANTHROPIC_API_KEY with a valid key",
            provider="anthropic",
            status=401,
        )

    result = runner.invoke(test_app, ["trigger-provider-err"])
    assert result.exit_code == 2
    assert "[anthropic]" in result.output
    assert "Invalid API key provided" in result.output
    assert "Hint: Export ANTHROPIC_API_KEY with a valid key" in result.output
    assert "Traceback (most recent call last)" not in result.output


def test_cli_tool_error(runner):
    """ToolError exits with code 1."""
    test_app = create_test_app()

    @test_app.command()
    def trigger_tool_err():
        raise ToolError("Command timed out after 30 seconds", hint="Increase tool timeout setting")

    result = runner.invoke(test_app, ["trigger-tool-err"])
    assert result.exit_code == 1
    assert "Command timed out after 30 seconds" in result.output
    assert "Hint: Increase tool timeout setting" in result.output


def test_cli_unexpected_exception(runner, temp_log_file):
    """Unexpected exception prints short internal error line with log path, exits 70, and records traceback."""
    setup_logging(log_file=temp_log_file, force_reinit=True)
    test_app = create_test_app()

    @test_app.command()
    def trigger_unexpected():
        raise RuntimeError("Unexpected memory corruption in tensor forward pass")

    result = runner.invoke(test_app, ["trigger-unexpected"])
    assert result.exit_code == 70
    assert "Internal error: Unexpected memory corruption in tensor forward pass" in result.output
    assert str(temp_log_file.resolve()) in result.output
    assert "Traceback (most recent call last)" not in result.output

    # Verify traceback was written to the log file on disk
    assert temp_log_file.exists()
    log_content = temp_log_file.read_text(encoding="utf-8")
    assert "Unexpected memory corruption in tensor forward pass" in log_content
    assert "Traceback (most recent call last):" in log_content


def test_cli_trace_flag_shows_traceback(runner):
    """With --trace enabled, traceback is shown on stderr."""
    test_app = create_test_app()

    @test_app.command()
    def trigger_fail():
        raise ConfigError("Failed parsing config")

    result = runner.invoke(test_app, ["--trace", "trigger-fail"])
    assert result.exit_code == 3
    assert "Traceback (most recent call last):" in result.output


def test_cli_debug_env_var_shows_traceback(runner, monkeypatch):
    """With OCTOFLOW_DEBUG=1 enabled, traceback is shown on stderr."""
    monkeypatch.setenv("OCTOFLOW_DEBUG", "1")
    test_app = create_test_app()

    @test_app.command()
    def trigger_fail():
        raise ConfigError("Failed parsing config")

    result = runner.invoke(test_app, ["trigger-fail"])
    assert result.exit_code == 3
    assert "Traceback (most recent call last):" in result.output


# =============================================================================
# 2. Log File Creation, Rotation & Permissions
# =============================================================================


def test_log_file_creation_and_permissions(tmp_path):
    """Rotating log file is created with 0600 permissions and directory with 0700 permissions."""
    log_dir = tmp_path / "octoflow_test_logs"
    log_file = log_dir / "octoflow.log"

    setup_logging(log_file=log_file, force_reinit=True)
    logger = get_logger("test_permissions")
    logger.info("Test log entry for permission verification")

    assert log_file.exists()
    file_mode = log_file.stat().st_mode & 0o777
    assert file_mode == 0o600, f"Expected 0600, got {oct(file_mode)}"

    dir_mode = log_dir.stat().st_mode & 0o777
    assert dir_mode == 0o700, f"Expected 0700, got {oct(dir_mode)}"


def test_log_file_rotation_permissions(tmp_path):
    """Rotated backup log files maintain 0600 permissions."""
    log_dir = tmp_path / "rotate_test_logs"
    log_file = log_dir / "octoflow.log"

    handler = SecureRotatingFileHandler(
        str(log_file),
        maxBytes=500,  # Small threshold to force immediate rotation
        backupCount=2,
        encoding="utf-8",
    )
    test_logger = logging.getLogger("test_rotate")
    test_logger.handlers.clear()
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)

    # Write enough lines to exceed 500 bytes and trigger rotation
    for i in range(25):
        test_logger.info(f"Log rotation line number {i:03d} with padding data **********")

    handler.close()
    assert log_file.exists()
    assert (log_dir / "octoflow.log.1").exists()

    # Verify both primary and rotated backup files have mode 0600
    assert (log_file.stat().st_mode & 0o777) == 0o600
    assert ((log_dir / "octoflow.log.1").stat().st_mode & 0o777) == 0o600


# =============================================================================
# 3. Secret Redaction
# =============================================================================


def test_secret_redaction_regexes():
    """Verify secrets are redacted in strings."""
    anthropic_key = "sk-" + "ant-api03-" + "abcdef1234567890abcdef12345"
    openai_key = "sk-" + "proj-" + "999888777666555444333222111"
    google_key = "AIzaSyD9876543210zyxwvutsrqponmlkjihgfe"
    bearer_hdr = "Authorization: Bearer secret_bearer_token_12345"
    bearer_inline = "Bearer my_super_secret_token_12345"

    assert redact_secrets(anthropic_key) == "[REDACTED_KEY]"
    assert redact_secrets(openai_key) == "[REDACTED_KEY]"
    assert redact_secrets(google_key) == "[REDACTED_KEY]"
    assert redact_secrets(bearer_hdr) == "Authorization: Bearer [REDACTED_TOKEN]"
    assert redact_secrets(bearer_inline) == "Bearer [REDACTED_TOKEN]"


def test_secret_redaction_in_log_file(tmp_path):
    """Verify RedactionFilter cleans secrets before writing to disk."""
    log_file = tmp_path / "redacted.log"
    setup_logging(log_file=log_file, force_reinit=True)
    logger = get_logger("security_test")

    secret_key = "sk-" + "ant-api03-" + "abcdef1234567890abcdef12345"
    logger.info("Attempted connection using key %s", secret_key)
    logger.error("Failed header: Authorization: Bearer secret_bearer_token_12345")

    content = log_file.read_text(encoding="utf-8")
    assert secret_key not in content
    assert "[REDACTED_KEY]" in content
    assert "secret_bearer_token_12345" not in content
    assert "[REDACTED_TOKEN]" in content


def test_secret_redaction_in_octoflow_error():
    """Verify OctoFlowError automatically redacts secrets in message and hint."""
    raw_key = "sk-" + "ant-api03-" + "abcdef1234567890abcdef12345"
    err = OctoFlowError(f"Failed using key {raw_key}", hint=f"Recheck key {raw_key}")
    assert raw_key not in err.message
    assert "[REDACTED_KEY]" in err.message
    assert raw_key not in err.hint
    assert "[REDACTED_KEY]" in err.hint


# =============================================================================
# 4. Cockpit-Silent Logging
# =============================================================================


def test_cockpit_stderr_suppression(capsys):
    """Stderr logging is completely silenced when cockpit mode is active."""
    setup_logging(verbose=True, force_reinit=True)
    logger = get_logger("cockpit_test")

    # Before cockpit activation: stderr receives logs
    logger.info("Normal pre-cockpit message")
    captured = capsys.readouterr()
    assert "Normal pre-cockpit message" in captured.err

    # Inside cockpit session: stderr is suppressed
    set_cockpit_active(True)
    try:
        assert is_cockpit_active() is True
        logger.info("Inside cockpit log 1")
        logger.warning("Inside cockpit log 2")
        logger.error("Inside cockpit log 3")
        logger.debug("Inside cockpit debug")

        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == ""
    finally:
        set_cockpit_active(False)

    # After cockpit deactivation: stderr receives logs again
    assert is_cockpit_active() is False
    logger.info("Post-cockpit message")
    captured = capsys.readouterr()
    assert "Post-cockpit message" in captured.err


@pytest.mark.pty
def test_cockpit_silent_logging_through_pty():
    """Logging writes nothing to the terminal during a PTY cockpit session, even with DEBUG enabled."""
    master, slave = pty.openpty()
    try:
        # Create a StreamHandler attached to the slave fd (simulating terminal stderr)
        slave_file = open(slave, "w")
        stream_handler = logging.StreamHandler(slave_file)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.addFilter(CockpitSuppressFilter())

        test_logger = logging.getLogger("pty_cockpit_logger")
        test_logger.handlers.clear()
        test_logger.addHandler(stream_handler)
        test_logger.setLevel(logging.DEBUG)
        test_logger.propagate = False

        # Activate cockpit
        set_cockpit_active(True)
        try:
            # Emit logs at DEBUG and ERROR levels
            test_logger.debug("Benthic sensory surprise calculation debug frame")
            test_logger.error("Simulation arm execution warning")
            slave_file.flush()

            # Poll master fd to ensure no bytes were written
            rlist, _, _ = select.select([master], [], [], 0.2)
            assert len(rlist) == 0, "Expected master PTY to have 0 bytes, but output was received"
        finally:
            set_cockpit_active(False)
            slave_file.close()
    finally:
        os.close(master)

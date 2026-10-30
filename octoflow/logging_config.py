"""Logging infrastructure for OctoFlow with secure rotation and secret redaction.

Features:
- Rotating log file at ~/.octoflow/logs/octoflow.log (1 MB x 3 backups, mode 0600).
- Redaction filter scrubbing credentials and bearer tokens before disk writes.
- Stderr handler active only outside cockpit mode.
- Non-interfering silence during interactive cockpit / PTY sessions.
- Verbosity levels controlled by --verbose, --trace, and OCTOFLOW_DEBUG.
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from octoflow.errors import redact_secrets

LOGGER_NAME = "octoflow"
DEFAULT_MAX_BYTES = 1 * 1024 * 1024  # 1 MB
DEFAULT_BACKUP_COUNT = 3

_COCKPIT_ACTIVE: bool = False
_INITIALIZED: bool = False
_TRACE_ENABLED: bool = False


def is_trace_enabled() -> bool:
    """Return True if tracebacks / debug trace is enabled via flag or env."""
    return (
        _TRACE_ENABLED
        or (os.getenv("OCTOFLOW_DEBUG") == "1")
        or (os.getenv("OCTOFLOW_TRACE") == "1")
    )


def set_trace_enabled(enabled: bool = True) -> None:
    """Enable or disable global trace mode."""
    global _TRACE_ENABLED
    _TRACE_ENABLED = enabled


def is_cockpit_active() -> bool:
    """Return True if the interactive cockpit session is currently active."""
    return _COCKPIT_ACTIVE


def set_cockpit_active(active: bool = True) -> None:
    """Activate or deactivate cockpit suppression for terminal output."""
    global _COCKPIT_ACTIVE
    _COCKPIT_ACTIVE = active


def get_log_dir() -> Path:
    """Return path to ~/.octoflow/logs with mode 0700."""
    home = Path.home()
    log_dir = home / ".octoflow" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    try:
        cur_mode = log_dir.stat().st_mode & 0o777
        if (cur_mode & ~0o700) != 0:
            log_dir.chmod(0o700)
    except OSError:
        pass
    return log_dir


_ACTIVE_LOG_FILE: Path | None = None


def get_log_file_path() -> Path:
    """Return active log file path or default ~/.octoflow/logs/octoflow.log."""
    if _ACTIVE_LOG_FILE is not None:
        return _ACTIVE_LOG_FILE
    return get_log_dir() / "octoflow.log"


# Alias
get_log_file = get_log_file_path
is_trace_mode = is_trace_enabled


class RedactionFilter(logging.Filter):
    """Logging filter that scrubs API keys and secret tokens from all log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: (redact_secrets(v) if isinstance(v, str) else v)
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_secrets(v) if isinstance(v, str) else v for v in record.args
                )
        return True


class CockpitSuppressFilter(logging.Filter):
    """Filter attached to stderr handler to completely silence logs when cockpit is active."""

    def filter(self, record: logging.LogRecord) -> bool:
        return not _COCKPIT_ACTIVE


class SecureRotatingFileHandler(RotatingFileHandler):
    """RotatingFileHandler enforcing mode 0600 on primary and rotated log files."""

    def _open(self):
        Path(self.baseFilename).parent.mkdir(parents=True, exist_ok=True)
        prev_umask = os.umask(0o177)
        try:
            stream = super()._open()
            try:
                os.chmod(self.baseFilename, 0o600)
            except OSError:
                pass
            return stream
        finally:
            os.umask(prev_umask)

    def doRollover(self):
        super().doRollover()
        try:
            if os.path.exists(self.baseFilename):
                os.chmod(self.baseFilename, 0o600)
        except OSError:
            pass


def get_logger(name: str | None = None) -> logging.Logger:
    """Get the octoflow logger or a child logger."""
    base_logger = logging.getLogger(LOGGER_NAME)
    if not name or name == LOGGER_NAME:
        return base_logger
    if name.startswith(f"{LOGGER_NAME}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


def setup_logging(
    verbose: bool = False,
    trace: bool = False,
    log_file: Path | None = None,
    force_reinit: bool = False,
) -> logging.Logger:
    """Initialize rotating file and console logging for OctoFlow.

    Args:
        verbose: Enable INFO level stderr output.
        trace: Enable DEBUG level file and stderr output.
        log_file: Optional explicit path to log file (default ~/.octoflow/logs/octoflow.log).
        force_reinit: Force handler re-creation.
    """
    global _INITIALIZED, _TRACE_ENABLED, _ACTIVE_LOG_FILE
    if trace:
        _TRACE_ENABLED = True
    if log_file:
        _ACTIVE_LOG_FILE = Path(log_file).resolve()

    logger = logging.getLogger(LOGGER_NAME)
    if _INITIALIZED and not force_reinit:
        # Update levels if flags change
        file_level = logging.DEBUG if is_trace_enabled() else logging.INFO
        stderr_level = (
            logging.DEBUG if is_trace_enabled() else (logging.INFO if verbose else logging.WARNING)
        )
        logger.setLevel(min(file_level, stderr_level))
        for h in logger.handlers:
            if isinstance(h, RotatingFileHandler):
                h.setLevel(file_level)
            elif isinstance(h, logging.StreamHandler):
                h.setLevel(stderr_level)
        return logger

    # Clear existing handlers on reinit
    logger.handlers.clear()
    logger.propagate = False

    # Determine log levels
    debug_mode = is_trace_enabled()
    file_level = logging.DEBUG if debug_mode else logging.INFO
    stderr_level = logging.DEBUG if debug_mode else (logging.INFO if verbose else logging.WARNING)
    logger.setLevel(min(file_level, stderr_level))

    # 1. Rotating File Handler (~/.octoflow/logs/octoflow.log, 1 MB x 3, mode 0600)
    target_log_path = log_file or get_log_file_path()
    target_log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        cur_mode = target_log_path.parent.stat().st_mode & 0o777
        if (cur_mode & ~0o700) != 0:
            target_log_path.parent.chmod(0o700)
    except OSError:
        pass

    file_handler = SecureRotatingFileHandler(
        str(target_log_path),
        maxBytes=DEFAULT_MAX_BYTES,
        backupCount=DEFAULT_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(RedactionFilter())
    logger.addHandler(file_handler)

    # 2. Stderr Handler (silenced during cockpit sessions)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(stderr_level)
    stderr_formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    stderr_handler.setFormatter(stderr_formatter)
    stderr_handler.addFilter(CockpitSuppressFilter())
    stderr_handler.addFilter(RedactionFilter())
    logger.addHandler(stderr_handler)

    _INITIALIZED = True
    return logger

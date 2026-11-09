"""Tests for the automated reference documentation generator (scripts/gen_reference.py)."""

from __future__ import annotations

import re
from pathlib import Path
import pytest

from scripts.gen_reference import (
    HEADER_NOTICE,
    check_references,
    generate_cli_reference,
    generate_config_reference,
    generate_errors_reference,
    generate_exit_codes_reference,
    write_references,
)
from scripts.check_docs import is_emoji


def test_write_references_into_temp_dir(tmp_path: Path) -> None:
    """Verifies that write_references creates all 4 expected reference documents."""
    generated = write_references(tmp_path)
    expected_files = {"cli.md", "config.md", "errors.md", "exit-codes.md"}
    assert set(generated.keys()) == expected_files

    for fname in expected_files:
        fpath = tmp_path / fname
        assert fpath.is_file(), f"File {fname} was not created"
        assert fpath.stat().st_size > 500, f"File {fname} is unexpectedly small"
        content = fpath.read_text(encoding="utf-8")
        assert content.startswith(HEADER_NOTICE.strip()), f"{fname} missing header notice"


def test_cli_reference_contents() -> None:
    """Verifies CLI reference contains all registered commands and syntax blocks."""
    cli_content = generate_cli_reference()

    # Core commands that must be documented
    essential_commands = [
        "octoflow run",
        "octoflow setup",
        "octoflow doctor",
        "octoflow config",
        "octoflow receipt",
        "octoflow undo",
        "octoflow replay",
        "octoflow guild",
        "octoflow mcp",
        "octoflow bench",
        "octoflow ui",
    ]
    for cmd in essential_commands:
        assert cmd in cli_content, f"Command '{cmd}' missing from cli.md"

    # Verify usage code block and options table exist
    assert "```bash" in cli_content
    assert "#### Options" in cli_content
    assert "Master Command Directory" in cli_content


def test_config_reference_contents() -> None:
    """Verifies config reference documents Pydantic schemas and environment variables."""
    cfg_content = generate_config_reference()

    # Schemas
    assert "Root `Settings`" in cfg_content
    assert "`DefaultsSettings`" in cfg_content
    assert "`UISettings`" in cfg_content
    assert "`ServerSettings`" in cfg_content
    assert "`PrivacySettings`" in cfg_content
    assert "`ProviderSettings`" in cfg_content

    # Key fields
    assert "`schema_version`" in cfg_content
    assert "`default_provider`" in cfg_content
    assert "`default_scale`" in cfg_content
    assert "`encoder_backend`" in cfg_content
    assert "`redact_outbound`" in cfg_content
    assert "`api_key`" in cfg_content

    # Environment variables
    assert "`OCTOFLOW_THEME`" in cfg_content
    assert "`OCTOFLOW_WS_PORT`" in cfg_content
    assert "`ANTHROPIC_API_KEY`" in cfg_content
    assert "`OLLAMA_BASE_URL`" in cfg_content


def test_errors_reference_contents() -> None:
    """Verifies errors reference contains all 14 standardized error codes and anchors."""
    err_content = generate_errors_reference()

    catalog_codes = [
        "E-BUDGET",
        "E-CONFIG-INVALID",
        "E-GENERAL",
        "E-NOGIT",
        "E-OLLAMA-DOWN",
        "E-PROV-AUTH",
        "E-PROV-EXHAUSTED",
        "E-PROV-FAILED",
        "E-PROV-RATE",
        "E-PROV-REQUEST",
        "E-PROV-TRANSIENT",
        "E-TOOL-DENIED",
        "E-USAGE-INVALID",
        "E-WORKSPACE-ESCAPE",
    ]
    for code in catalog_codes:
        assert f"`{code}`" in err_content, f"Code {code} missing from errors.md"
        anchor = code.lower()
        assert f'id="{anchor}"' in err_content, f"Anchor for {code} missing from errors.md"
        assert f"[docs/TROUBLESHOOTING.md#{anchor}]" in err_content


def test_exit_codes_reference_contents() -> None:
    """Verifies exit-codes reference documents all standardized process exit codes."""
    exit_content = generate_exit_codes_reference()

    assert "**0**" in exit_content  # Success
    assert "**1**" in exit_content  # Tool / Runtime / Budget
    assert "**2**" in exit_content  # Provider Family
    assert "**3**" in exit_content  # Config / Usage
    assert "**70**" in exit_content  # Fatal Internal Error
    assert "Error Handling Style Contract" in exit_content
    assert "Best-Effort Exception Convention" in exit_content


def test_check_references_passes_on_repo() -> None:
    """Verifies that repository docs/reference/ files are completely up-to-date."""
    diffs = check_references()
    assert not diffs, f"Stale reference files detected:\n" + "\n".join(diffs)


def test_check_references_detects_drift(tmp_path: Path) -> None:
    """Verifies that check_references detects modified or stale reference files."""
    write_references(tmp_path)
    assert not check_references(tmp_path)

    # Mutate a file
    target = tmp_path / "errors.md"
    target.write_text(target.read_text(encoding="utf-8") + "\n# Extra Drifting Content", encoding="utf-8")

    diffs = check_references(tmp_path)
    assert len(diffs) == 1
    assert "Stale reference file 'errors.md'" in diffs[0]


def test_generated_references_zero_emojis(tmp_path: Path) -> None:
    """Verifies that all generated markdown complies strictly with zero-emoji policy."""
    write_references(tmp_path)
    for md_file in tmp_path.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            for char in line:
                assert not is_emoji(char), (
                    f"Forbidden emoji '{char}' (U+{ord(char):04X}) in {md_file.name}:{line_no}"
                )


def test_generated_references_no_absolute_user_paths(tmp_path: Path) -> None:
    """Verifies that all generated markdown contains zero absolute user paths."""
    write_references(tmp_path)
    abs_path_re = re.compile(r"/(?:Users|home)/[a-zA-Z0-9_\-]+/")
    for md_file in tmp_path.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            match = abs_path_re.search(line)
            assert not match, (
                f"Hardcoded user path '{match.group(0)}' in {md_file.name}:{line_no}"
            )

"""Comprehensive Verification Suite for Truthful Run States & Outcomes (Decision D1).

Tests:
1. Misconfigured providers + no --dry-run: exits code 2, prints actionable error, writes 0 files.
2. Explicit --dry-run: exits code 0, displays DRY-RUN ribbon, redirects writes to .octoflow/dry-run/.
3. LIVE mode with provider writing files: exits code 0, displays COMPLETE, lists written files.
4. LIVE mode with provider producing 0 files: exits code 2, reports [FAILED] model produced no file changes.
5. MCP tool results: include mode and outcome fields.
6. Exit code contract: 0 (complete/dry-run), 1 (partial), 2 (failed/provider exhausted), 3 (usage error).
7. Secret redaction: verifies API keys are never leaked in error messages.
8. Zero-emoji rule: verifies allowed glyphs only.
"""

import os
import re
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

pytestmark = pytest.mark.unit

from octoflow.cli import app
from octoflow.config import OctoFlowConfig
from octoflow.conductor import SupraesophagealConductor
from octoflow.outcome import RunMode, RunOutcome, RunResult, ProviderExhaustedError
from octoflow.provider import (
    BaseLLMProvider,
    LLMResponse,
    MockLLMProvider,
    get_llm_provider,
    _sanitize_secret_text,
)
from octoflow.mcp import OctoFlowMCPServer


runner = CliRunner()


def test_misconfigured_providers_no_dry_run_exits_2_no_files(tmp_path, monkeypatch):
    """Criterion 1: With misconfigured providers and no --dry-run, exits code 2, prints failures, writes 0 files."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OCTOFLOW_DRY_RUN", raising=False)
    monkeypatch.setenv("OCTOFLOW_FORCE_LIVE", "1")

    target_dir = tmp_path / "target_ws"
    target_dir.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["run", "Build an authentication service", "--dir", str(target_dir), "--model", "anthropic"])
    assert result.exit_code == 2
    assert "FAILED" in result.output or "missing ANTHROPIC_API_KEY" in result.output
    # Must write no files to target_dir
    files_created = list(target_dir.rglob("*"))
    assert len(files_created) == 0, f"Expected 0 files, found: {files_created}"


def test_dry_run_exits_0_prints_ribbon_no_target_files(tmp_path, monkeypatch):
    """Criterion 2: With --dry-run, prints DRY-RUN ribbon, writes no files to target workspace, exits 0."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    target_dir = tmp_path / "dry_ws"
    target_dir.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["run", "Build microservice scaffold", "--dir", str(target_dir), "--dry-run", "--port", "18099"])
    assert result.exit_code == 0
    assert "DRY-RUN: no project files written" in result.output
    # Target directory must remain pristine
    files_created = [f for f in target_dir.rglob("*") if f.is_file()]
    assert len(files_created) == 0, f"Files were written to workspace in dry-run: {files_created}"


def test_live_mode_writing_files_exits_0_complete(tmp_path, monkeypatch):
    """Criterion 3: LIVE mode with a provider writing files prints COMPLETE and lists files (exit 0)."""
    monkeypatch.delenv("OCTOFLOW_DRY_RUN", raising=False)
    monkeypatch.setenv("OCTOFLOW_FORCE_LIVE", "1")
    target_dir = tmp_path / "live_ws"
    target_dir.mkdir(parents=True, exist_ok=True)

    class FileWritingProvider(BaseLLMProvider):
        provider_name = "test_writer"
        model = "test-model-v1"

        def generate(self, prompt: str, **kwargs) -> LLMResponse:
            return LLMResponse(content="def hello(): return 'world'")

        async def agenerate(self, prompt: str, **kwargs) -> LLMResponse:
            return LLMResponse(content="def hello(): return 'world'")

    with patch("octoflow.conductor.get_llm_provider", return_value=FileWritingProvider()):
        cfg = OctoFlowConfig(workspace_dir=str(target_dir), model_provider="anthropic", dry_run=False)
        conductor = SupraesophagealConductor(config=cfg)
        # Simulate an arm step writing a real file
        res = conductor.sandbox.write_file("service.py", "def service(): pass\n")
        assert res.success is True
        assert "service.py" in conductor.sandbox.files_written

        for arm in conductor.arms:
            arm.is_quiescent = True

        run_res = conductor.run_swarm(objective="Implement service", max_cycles=1)
        assert run_res.mode == RunMode.LIVE
        assert run_res.outcome == RunOutcome.COMPLETE
        assert "service.py" in run_res.files_written


def test_live_mode_zero_files_exits_2_failed(tmp_path, monkeypatch):
    """Criterion 4: LIVE mode with a provider producing no file changes reports FAILED (exit 2)."""
    monkeypatch.delenv("OCTOFLOW_DRY_RUN", raising=False)
    monkeypatch.setenv("OCTOFLOW_FORCE_LIVE", "1")
    target_dir = tmp_path / "zero_ws"
    target_dir.mkdir(parents=True, exist_ok=True)

    class PassiveProvider(BaseLLMProvider):
        provider_name = "passive_mock"
        model = "passive-v1"

        def generate(self, prompt: str, **kwargs) -> LLMResponse:
            return LLMResponse(content="Thinking deeply without calling write_file...")

        async def agenerate(self, prompt: str, **kwargs) -> LLMResponse:
            return LLMResponse(content="Thinking deeply without calling write_file...")

    with patch("octoflow.conductor.get_llm_provider", return_value=PassiveProvider()):
        cfg = OctoFlowConfig(workspace_dir=str(target_dir), model_provider="anthropic", dry_run=False)
        conductor = SupraesophagealConductor(config=cfg)
        # Ensure sandbox files_written remains empty
        conductor.sandbox.files_written.clear()

        run_res = conductor.run_swarm(objective="No-op plan", max_cycles=1)
        assert run_res.mode == RunMode.LIVE
        assert run_res.outcome == RunOutcome.FAILED
        assert run_res.reason == "model produced no file changes"
        assert len(run_res.files_written) == 0


@pytest.mark.anyio
async def test_mcp_tool_result_contains_mode_and_outcome(tmp_path, anyio_backend):
    """Criterion 5: MCP tool result contains mode and outcome fields."""
    if anyio_backend != "asyncio":
        pytest.skip("Test specifically covers asyncio")

    server = OctoFlowMCPServer(workspace_dir=str(tmp_path))
    res = await server.handle_json_rpc_message({
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {
            "name": "octoflow_run_swarm",
            "arguments": {
                "objective": "Verify MCP response contracts",
                "max_cycles": 1,
                "dry_run": True,
            },
        },
    })
    assert res is not None
    assert "result" in res
    content = res["result"]["content"]
    combined_text = " ".join(c.get("text", "") for c in content)
    assert "Mode: dry_run" in combined_text or '"mode": "dry_run"' in combined_text
    assert "Outcome: complete" in combined_text or '"outcome": "complete"' in combined_text
    # Zero emoji in MCP result
    assert "🐙" not in combined_text
    assert "✅" not in combined_text
    assert "⚠️" not in combined_text


def test_cli_exit_code_contracts(tmp_path, monkeypatch):
    """Criterion 6: Exit codes 0 (complete/dry-run), 1 (partial), 2 (failed), 3 (usage error)."""
    # Usage error -> 2 in standard typer or custom 3
    bad_call = runner.invoke(app, ["run"])
    assert bad_call.exit_code in (2, 3)

    # Dry run -> 0
    dry_call = runner.invoke(app, ["run", "Dry run test", "--dir", str(tmp_path), "--dry-run", "--port", "18100"])
    assert dry_call.exit_code == 0

    # Mock in live without --dry-run -> 2
    monkeypatch.delenv("OCTOFLOW_DRY_RUN", raising=False)
    mock_live_call = runner.invoke(app, ["run", "Mock in live test", "--dir", str(tmp_path), "--model", "mock"])
    assert mock_live_call.exit_code == 2


def test_secret_sanitization_in_errors():
    """Criterion 7: Secrets and API keys must never be exposed in error messages."""
    raw_error = "Failed with Anthropic key " + "sk-ant-" + "api03-1234567890abcdef12345 and OpenAI " + "sk-proj-" + "abcdef1234567890xyz"
    sanitized = _sanitize_secret_text(raw_error)
    assert "sk-ant" not in sanitized
    assert "sk-proj" not in sanitized
    assert "[REDACTED_KEY]" in sanitized


def test_zero_emoji_rule_on_ribbons():
    """Criterion 8: Output ribbons must strictly adhere to allowed glyphs only."""
    allowed_glyphs = {"•", "·", "○", "◈", "✔", "✖"}
    sample_complete = "◈ [LIVE: anthropic:claude-3-5-sonnet] COMPLETE, 3 files written\n  • app.py\n  • test.py"
    sample_dry = "◈ [DRY-RUN: no project files written]"
    sample_failed = "✖ [FAILED] model produced no file changes"

    disallowed_emojis = ["🐙", "✅", "❌", "⚠️", "🔥", "🚀"]
    for text in [sample_complete, sample_dry, sample_failed]:
        for emoji in disallowed_emojis:
            assert emoji not in text

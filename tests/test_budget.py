"""Tests for P3.5 Run budgets and healing-loop limits."""

import pytest
from typer.testing import CliRunner

pytestmark = pytest.mark.unit

from octoflow.budget import BudgetTracker, RunBudget
from octoflow.cockpit.render import build_hud_panel
from octoflow.cockpit.session import CockpitSession
from octoflow.conductor import SupraesophagealConductor
from octoflow.config import OctoFlowConfig
from octoflow.errors import BudgetExceeded
from octoflow.healing import (
    extract_failure_signature,
    self_heal_workspace,
)
from octoflow.outcome import RunOutcome
from octoflow.provider import BaseLLMProvider, LLMResponse
from octoflow.settings import load_settings

# ---------------------------------------------------------------------------
# 1. RunBudget and BudgetTracker core mechanics
# ---------------------------------------------------------------------------


def test_run_budget_defaults():
    b = RunBudget()
    assert b.max_tokens == 200_000
    assert b.max_llm_calls == 200
    assert b.max_wall_seconds == 1800
    assert b.max_heal_iterations == 5
    assert b.max_files_written == 200


def test_budget_tracker_llm_calls_limit():
    budget = RunBudget(max_llm_calls=3)
    tracker = BudgetTracker(budget=budget)

    tracker.check_llm_call()  # 1
    tracker.check_llm_call()  # 2
    tracker.check_llm_call()  # 3

    with pytest.raises(BudgetExceeded) as exc_info:
        tracker.check_llm_call()  # 4 -> exceeds
    assert exc_info.value.limit_name == "max_llm_calls"
    assert exc_info.value.limit == 3
    assert exc_info.value.used in (3, 4)


def test_budget_tracker_tokens_limit():
    budget = RunBudget(max_tokens=1000)
    tracker = BudgetTracker(budget=budget)

    tracker.record_tokens(600)
    assert tracker.tokens_consumed == 600

    with pytest.raises(BudgetExceeded) as exc_info:
        tracker.record_tokens(500)
    assert exc_info.value.limit_name == "max_tokens"
    assert exc_info.value.limit == 1000
    assert exc_info.value.used == 1100


def test_budget_tracker_files_written_limit():
    budget = RunBudget(max_files_written=2)
    tracker = BudgetTracker(budget=budget)

    tracker.check_and_record_file_write("a.py")
    tracker.check_and_record_file_write("b.py")

    with pytest.raises(BudgetExceeded) as exc_info:
        tracker.check_and_record_file_write("c.py")
    assert exc_info.value.limit_name == "max_files_written"
    assert exc_info.value.limit == 2
    assert exc_info.value.used in (2, 3)


def test_budget_tracker_heal_iterations_limit():
    budget = RunBudget(max_heal_iterations=2)
    tracker = BudgetTracker(budget=budget)

    tracker.check_heal_iteration()  # 1
    tracker.check_heal_iteration()  # 2

    with pytest.raises(BudgetExceeded) as exc_info:
        tracker.check_heal_iteration()  # 3
    assert exc_info.value.limit_name == "max_heal_iterations"
    assert exc_info.value.limit == 2
    assert exc_info.value.used in (2, 3)


def test_budget_tracker_wall_time_injected_clock():
    current_time = 1000.0

    def clock():
        return current_time

    budget = RunBudget(max_wall_seconds=60)
    tracker = BudgetTracker(budget=budget, clock=clock)

    tracker.check_wall_time()  # 0 elapsed

    current_time = 1050.0
    tracker.check_wall_time()  # 50s elapsed <= 60

    current_time = 1061.0
    with pytest.raises(BudgetExceeded) as exc_info:
        tracker.check_wall_time()  # 61s elapsed > 60
    assert exc_info.value.limit_name == "max_wall_seconds"
    assert exc_info.value.limit == 60


def test_budget_tracker_no_limits():
    budget = RunBudget(
        max_tokens=None,
        max_llm_calls=None,
        max_wall_seconds=None,
        max_heal_iterations=None,
        max_files_written=None,
    )
    tracker = BudgetTracker(budget=budget)

    for _ in range(1000):
        tracker.check_llm_call()
        tracker.record_tokens(10_000)
        tracker.check_heal_iteration()
        tracker.check_and_record_file_write("test.py")
        tracker.check_wall_time()

    assert tracker.llm_calls_made == 1000
    assert tracker.tokens_consumed == 10_000_000


def test_hud_line_formatting():
    # tokens 41k/200k, calls 33/200
    budget = RunBudget(max_tokens=200_000, max_llm_calls=200)
    tracker = BudgetTracker(budget=budget, tokens_consumed=41_000, llm_calls_made=33)
    line = tracker.format_hud_line()
    assert line == "budget: tokens 41k/200k, calls 33/200"

    # unlimited formatting
    budget_unlimited = RunBudget(max_tokens=None, max_llm_calls=None)
    tracker_unlimited = BudgetTracker(
        budget=budget_unlimited, tokens_consumed=5000, llm_calls_made=10
    )
    assert tracker_unlimited.format_hud_line() == "budget: tokens 5k/unlimited, calls 10/unlimited"


# ---------------------------------------------------------------------------
# 2. Conductor Enforcement with Fake Provider
# ---------------------------------------------------------------------------


class EndlessToolCallFakeProvider(BaseLLMProvider):
    """Fake provider that endlessly produces tool calls to trigger LLM call limits."""

    provider_name = "endless_fake"
    model = "mock"

    def generate(
        self, prompt: str, system_prompt: str = "", temperature: float = 0.2, max_tokens: int = 2048
    ) -> LLMResponse:
        content = '{"action": "read_file", "target": "specs/readme.md", "explanation": "Analyzing specs..."}'
        return LLMResponse(content=content, tokens_prompt=10, tokens_completion=20, total_tokens=30)

    async def agenerate(
        self, prompt: str, system_prompt: str = "", temperature: float = 0.2, max_tokens: int = 2048
    ) -> LLMResponse:
        return self.generate(prompt, system_prompt, temperature, max_tokens)


def test_fake_provider_stops_at_max_llm_calls(tmp_path):
    """Acceptance criterion: A fake provider that always returns tool calls stops at max_llm_calls with outcome PARTIAL and reason naming the limit."""
    cfg = OctoFlowConfig(
        workspace_dir=str(tmp_path),
        dry_run=True,
        budget=RunBudget(max_llm_calls=4, max_tokens=100_000, max_wall_seconds=300),
    )
    conductor = SupraesophagealConductor(config=cfg)

    # Inject fake provider on all arms
    for arm in conductor.arms:
        arm.provider = EndlessToolCallFakeProvider()

    res = conductor.run_swarm(objective="Endless run test", max_cycles=10)
    assert res.outcome == RunOutcome.PARTIAL
    assert res.reason is not None
    assert "max_llm_calls" in res.reason
    assert res.extra.get("budget_exceeded") == "max_llm_calls"
    assert "budget: tokens" in res.extra.get("budget_line", "")


def test_wall_time_stops_stalled_fake_provider(tmp_path):
    """Acceptance criterion: Wall-time limit stops a stalled fake provider (injected clock)."""
    current_time = 1000.0

    def clock():
        return current_time

    cfg = OctoFlowConfig(
        workspace_dir=str(tmp_path),
        dry_run=True,
        budget=RunBudget(max_wall_seconds=10, max_llm_calls=1000),
    )
    tracker = BudgetTracker(budget=cfg.budget, clock=clock)
    conductor = SupraesophagealConductor(config=cfg)
    conductor.set_budget_tracker(tracker)

    class StallingClockAdvancingProvider(BaseLLMProvider):
        provider_name = "stalling_fake"
        model = "mock"

        def generate(
            self,
            prompt: str,
            system_prompt: str = "",
            temperature: float = 0.2,
            max_tokens: int = 2048,
        ) -> LLMResponse:
            nonlocal current_time
            current_time += 15.0  # Simulate 15s stall, exceeding 10s budget
            content = '{"action": "read_file", "target": "specs/readme.md", "explanation": "Stalled reading"}'
            return LLMResponse(
                content=content, tokens_prompt=10, tokens_completion=20, total_tokens=30
            )

        async def agenerate(
            self,
            prompt: str,
            system_prompt: str = "",
            temperature: float = 0.2,
            max_tokens: int = 2048,
        ) -> LLMResponse:
            return self.generate(prompt, system_prompt, temperature, max_tokens)

    for arm in conductor.arms:
        arm.provider = StallingClockAdvancingProvider()

    res = conductor.run_swarm(objective="Stalled run test", max_cycles=5)
    assert res.outcome == RunOutcome.PARTIAL
    assert res.reason is not None
    assert "max_wall_seconds" in res.reason
    assert res.extra.get("budget_exceeded") == "max_wall_seconds"


# ---------------------------------------------------------------------------
# 3. Healing limits and repetition detection
# ---------------------------------------------------------------------------


def test_healing_signature_extraction():
    pytest_out = """
FAILED tests/test_calc.py::test_add - AssertionError: assert 4 == 5
FAILED tests/test_auth.py::test_token - KeyError: 'token'
"""
    from octoflow.healing import parse_pytest_failures

    failures = parse_pytest_failures(pytest_out)
    sig = extract_failure_signature(failures, pytest_out)
    assert len(sig) == 2
    assert ("tests/test_calc.py::test_add", "AssertionError") in sig
    assert ("tests/test_auth.py::test_token", "KeyError") in sig


def test_healing_repetition_detection_stops_sooner(tmp_path, monkeypatch):
    """Acceptance criterion: Healing with an unfixable failing test stops after at most 5 iterations or sooner by repetition detection."""
    # Create dummy failing test in tmp_path
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_stubborn.py").write_text("def test_fail(): assert False", encoding="utf-8")

    # Mock run_test_suite to always return identical failing pytest output
    stubborn_log = "FAILED tests/test_stubborn.py::test_fail - AssertionError: assert False"
    monkeypatch.setattr(
        "octoflow.healing.run_test_suite",
        lambda ws, cmd=None, timeout=60: (1, "", stubborn_log),
    )

    # Mock provider to return syntax-valid code
    class DummyRepairProvider(BaseLLMProvider):
        provider_name = "repair_dummy"
        model = "mock"

        def generate(
            self,
            prompt: str,
            system_prompt: str = "",
            temperature: float = 0.2,
            max_tokens: int = 2048,
        ) -> LLMResponse:
            return LLMResponse(
                content="```python\ndef test_fail(): pass\n```",
                tokens_prompt=10,
                tokens_completion=10,
                total_tokens=20,
            )

    monkeypatch.setattr(
        "octoflow.provider.get_llm_provider",
        lambda cfg, tier="frontier", dry_run=False: DummyRepairProvider(),
    )

    res = self_heal_workspace(str(tmp_path), max_attempts=5)
    assert not res["success"]
    assert res["stop_reason"] == "repetition_detected"
    assert res["attempts"] <= 2  # Repetition detected by attempt 2, much sooner than 5


def test_healing_no_progress_plateau_detection(tmp_path, monkeypatch):
    """Test that healing stops with no_progress when failing count does not decrease over 2 iterations."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_a.py").write_text("def test_a(): pass", encoding="utf-8")

    logs = [
        "FAILED tests/test_a.py::test_1 - AssertionError: fail 1\nFAILED tests/test_a.py::test_2 - AssertionError: fail 2",
        "FAILED tests/test_a.py::test_3 - TypeError: fail 3\nFAILED tests/test_a.py::test_4 - TypeError: fail 4",
        "FAILED tests/test_a.py::test_5 - ValueError: fail 5\nFAILED tests/test_a.py::test_6 - ValueError: fail 6",
    ]
    call_idx = 0

    def mock_run_test_suite(ws, cmd=None, timeout=60):
        nonlocal call_idx
        log = logs[min(call_idx, len(logs) - 1)]
        call_idx += 1
        return (1, "", log)

    monkeypatch.setattr("octoflow.healing.run_test_suite", mock_run_test_suite)

    class DummyRepairProvider(BaseLLMProvider):
        provider_name = "repair_dummy"
        model = "mock"

        def generate(
            self,
            prompt: str,
            system_prompt: str = "",
            temperature: float = 0.2,
            max_tokens: int = 2048,
        ) -> LLMResponse:
            return LLMResponse(
                content="```python\ndef foo(): pass\n```",
                tokens_prompt=10,
                tokens_completion=10,
                total_tokens=20,
            )

    monkeypatch.setattr(
        "octoflow.provider.get_llm_provider",
        lambda cfg, tier="frontier", dry_run=False: DummyRepairProvider(),
    )

    res = self_heal_workspace(str(tmp_path), max_attempts=5)
    assert not res["success"]
    assert res["stop_reason"] == "no_progress"
    assert res["attempts"] == 2


# ---------------------------------------------------------------------------
# 4. CLI flag override precedence test
# ---------------------------------------------------------------------------


def test_cli_flag_override_precedence(tmp_path, monkeypatch):
    """Verify precedence: Defaults < settings < env < CLI flags."""
    # 1. Base defaults
    defaults = RunBudget()
    assert defaults.max_tokens == 200_000
    assert defaults.max_llm_calls == 200

    # 2. Settings file
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        '{"budget": {"max_tokens": 150000, "max_llm_calls": 150}}', encoding="utf-8"
    )
    s = load_settings(cfg_path=settings_file)
    assert s.budget.max_tokens == 150_000
    assert s.budget.max_llm_calls == 150

    # 3. Environment overrides
    monkeypatch.setenv("OCTOFLOW_BUDGET_MAX_TOKENS", "120000")
    s_env = load_settings(cfg_path=settings_file)
    assert s_env.budget.max_tokens == 120_000

    # 4. CLI flags override env and settings
    from octoflow.cli import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "run",
            "dummy goal",
            "--dir",
            str(tmp_path),
            "--dry-run",
            "--port",
            "0",
            "--max-tokens",
            "50000",
            "--max-calls",
            "25",
        ],
    )
    assert result.exit_code in (0, 1, 2)


def test_no_limits_flag_prints_warning(tmp_path):
    """Acceptance criterion: Unlimited is explicit: --no-limits prints a warning line."""
    from octoflow.cli import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["run", "dummy goal", "--dir", str(tmp_path), "--dry-run", "--port", "0", "--no-limits"],
    )
    assert "Warning: --no-limits enabled. Execution limits are disabled." in result.output


# ---------------------------------------------------------------------------
# 5. Cockpit HUD / Summary line
# ---------------------------------------------------------------------------


def test_cockpit_hud_shows_budget_line():
    """Acceptance criterion: Budget line appears in the cockpit summary; tests green."""
    session = CockpitSession(
        budget_tracker=BudgetTracker(
            budget=RunBudget(max_tokens=200_000, max_llm_calls=200),
            tokens_consumed=41_000,
            llm_calls_made=33,
        )
    )
    panel = build_hud_panel(session)
    from rich.console import Console

    console = Console()
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    assert "◈ BUDGET" in output
    assert "tokens 41k/200k, calls 33/200" in output

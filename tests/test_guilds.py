"""Tests for P8.2 Custom Guilds via Validated Config.

Verifies:
- GuildSpec and ArmSpec validation with RFC 6901 JSON pointer paths.
- Rejection of 5+ invalid variants (<8 arms, >8 arms, bad color hex, prompt too long, duplicate IDs).
- Search path precedence: project -> user -> built-ins.
- Tool policy clamping with warning logging.
- Backward compatibility: Built-ins match golden rosters.
- CLI: octoflow guild list, validate, show, export.
- Full run with custom guild and telemetry payload inspection.
- The example guild examples/guilds/data_science.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from octoflow.cli import app
from octoflow.conductor import SupraesophagealConductor, SwarmTelemetryEvent
from octoflow.config import (
    AIML_RESEARCH_ROSTER,
    FULLSTACK_AI_ROSTER,
    SOFTWARE_DEV_ROSTER,
    OctoFlowConfig,
    SwarmMorphology,
)
from octoflow.guild import (
    BUILTIN_GUILD_SPECS,
    ArmSpec,
    GuildSpec,
    ToolPolicy,
    load_guild,
    validate_guild_file,
)
from typer.testing import CliRunner


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(env={"COLUMNS": "120"})


# ==============================================================================
# 1. Built-in Guilds & Golden Roster Backward Compatibility
# ==============================================================================


def test_builtin_guilds_match_golden_rosters() -> None:
    """Verify built-in guilds load as GuildSpec and produce identical 8-arm rosters."""
    for guild_name in ["software_dev", "aiml_research", "fullstack_ai"]:
        spec = load_guild(guild_name)
        assert isinstance(spec, GuildSpec)
        assert spec.name == guild_name
        assert len(spec.arms) == 8
        assert [arm.id for arm in spec.arms] == list(range(8))

        roster = spec.to_arm_roster()
        assert len(roster) == 8
        assert all(r.arm_id == idx for idx, r in enumerate(roster))

    # Test software_dev matches SOFTWARE_DEV_ROSTER titles and domains
    sw_spec = BUILTIN_GUILD_SPECS["software_dev"]
    sw_roster = sw_spec.to_arm_roster()
    for legacy, new_arm in zip(SOFTWARE_DEV_ROSTER, sw_roster, strict=True):
        assert legacy.arm_id == new_arm.arm_id
        assert legacy.name == new_arm.name
        assert legacy.workspace_domain == new_arm.workspace_domain

    # Test aiml_research matches AIML_RESEARCH_ROSTER
    aiml_spec = BUILTIN_GUILD_SPECS["aiml_research"]
    aiml_roster = aiml_spec.to_arm_roster()
    for legacy, new_arm in zip(AIML_RESEARCH_ROSTER, aiml_roster, strict=True):
        assert legacy.arm_id == new_arm.arm_id
        assert legacy.name == new_arm.name
        assert legacy.workspace_domain == new_arm.workspace_domain

    # Test fullstack_ai matches FULLSTACK_AI_ROSTER
    fs_spec = BUILTIN_GUILD_SPECS["fullstack_ai"]
    fs_roster = fs_spec.to_arm_roster()
    for legacy, new_arm in zip(FULLSTACK_AI_ROSTER, fs_roster, strict=True):
        assert legacy.arm_id == new_arm.arm_id
        assert legacy.name == new_arm.name
        assert legacy.workspace_domain == new_arm.workspace_domain


# ==============================================================================
# 2. JSON Pointer Validation & 5 Invalid Variants
# ==============================================================================


def _make_valid_arms(n: int = 8) -> list[dict[str, Any]]:
    """Helper creating n valid arm dicts."""
    return [
        {
            "id": i,
            "role": f"role_{i}",
            "focus": f"Focus area for arm {i}",
            "color": "#00F0FF",
            "system_prompt": f"System prompt for arm {i}",
            "tools": ["read_file", "write_file", "run_command", "list_dir"],
            "file_scope": [f"domain_{i}/"],
        }
        for i in range(n)
    ]


def test_invalid_guild_fewer_than_8_arms(tmp_path: Path) -> None:
    """Invalid Variant 1: Fewer than 8 arms fails with pointer /arms."""
    payload = {
        "name": "too_few_arms",
        "description": "Only 7 arms",
        "arms": _make_valid_arms(7),
    }
    guild_file = tmp_path / "too_few.json"
    guild_file.write_text(json.dumps(payload), encoding="utf-8")

    is_valid, errors, spec = validate_guild_file(guild_file)
    assert not is_valid
    assert spec is None
    assert any("/arms" in err and "exactly 8 arms" in err for err in errors)


def test_invalid_guild_more_than_8_arms(tmp_path: Path) -> None:
    """Invalid Variant 2: More than 8 arms fails with pointer /arms."""
    payload = {
        "name": "too_many_arms",
        "description": "9 arms",
        "arms": _make_valid_arms(9),
    }
    guild_file = tmp_path / "too_many.json"
    guild_file.write_text(json.dumps(payload), encoding="utf-8")

    is_valid, errors, spec = validate_guild_file(guild_file)
    assert not is_valid
    assert spec is None
    assert any("/arms" in err and "exactly 8 arms" in err for err in errors)


def test_invalid_guild_bad_color_hex(tmp_path: Path) -> None:
    """Invalid Variant 3: Invalid hex color fails with pointer /arms/<id>/color."""
    arms = _make_valid_arms(8)
    arms[3]["color"] = "invalid_not_hex"  # Corrupt arm 3

    payload = {
        "name": "bad_color_guild",
        "description": "Bad color on arm 3",
        "arms": arms,
    }
    guild_file = tmp_path / "bad_color.json"
    guild_file.write_text(json.dumps(payload), encoding="utf-8")

    is_valid, errors, spec = validate_guild_file(guild_file)
    assert not is_valid
    assert spec is None
    assert any("/arms/3/color" in err for err in errors)


def test_invalid_guild_system_prompt_too_long(tmp_path: Path) -> None:
    """Invalid Variant 4: System prompt > 2000 chars fails with pointer /arms/<id>/system_prompt."""
    arms = _make_valid_arms(8)
    arms[2]["system_prompt"] = "A" * 2001  # Exceeds max 2000

    payload = {
        "name": "long_prompt_guild",
        "description": "Arm 2 system prompt exceeds bound",
        "arms": arms,
    }
    guild_file = tmp_path / "long_prompt.json"
    guild_file.write_text(json.dumps(payload), encoding="utf-8")

    is_valid, errors, spec = validate_guild_file(guild_file)
    assert not is_valid
    assert spec is None
    assert any("/arms/2/system_prompt" in err for err in errors)


def test_invalid_guild_duplicate_or_out_of_range_arm_id(tmp_path: Path) -> None:
    """Invalid Variant 5: Duplicate arm ID fails with pointer /arms/<idx>/id."""
    arms = _make_valid_arms(8)
    arms[4]["id"] = 0  # Duplicate ID 0 (already used by arm 0)

    payload = {
        "name": "duplicate_id_guild",
        "description": "Arm 4 reuses ID 0",
        "arms": arms,
    }
    guild_file = tmp_path / "duplicate_id.json"
    guild_file.write_text(json.dumps(payload), encoding="utf-8")

    is_valid, errors, spec = validate_guild_file(guild_file)
    assert not is_valid
    assert spec is None
    assert any("/arms/4/id" in err and "Duplicate arm ID" in err for err in errors)


def test_invalid_guild_unknown_tool(tmp_path: Path) -> None:
    """Invalid Variant 6: Unknown tool name fails with pointer /arms/<id>/tools/<idx>."""
    arms = _make_valid_arms(8)
    arms[1]["tools"] = ["read_file", "arbitrary_unauthorized_tool"]

    payload = {
        "name": "unknown_tool_guild",
        "description": "Arm 1 requests unknown tool",
        "arms": arms,
    }
    guild_file = tmp_path / "bad_tool.json"
    guild_file.write_text(json.dumps(payload), encoding="utf-8")

    is_valid, errors, spec = validate_guild_file(guild_file)
    assert not is_valid
    assert any("/arms/1/tools/1" in err and "Unknown tool" in err for err in errors)


def test_path_traversal_safety_rejection() -> None:
    """Verify that path traversal attempts in guild names are strictly rejected."""
    with pytest.raises(ValueError, match="path traversal"):
        load_guild("../../etc/passwd")

    with pytest.raises(ValueError, match="path traversal"):
        load_guild("../secret")


# ==============================================================================
# 3. Loader Search Precedence: Project -> User -> Built-in
# ==============================================================================


def test_search_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify Project .octoflow/guilds overrides User ~/.octoflow/guilds which overrides Built-In."""
    fake_home = tmp_path / "user_home"
    fake_project = tmp_path / "project_root"
    fake_home.mkdir()
    fake_project.mkdir()

    monkeypatch.setattr(Path, "home", lambda: fake_home)

    user_guilds = fake_home / ".octoflow" / "guilds"
    user_guilds.mkdir(parents=True)
    proj_guilds = fake_project / ".octoflow" / "guilds"
    proj_guilds.mkdir(parents=True)

    # 1. Base case: Built-in software_dev is loaded
    spec_builtin = load_guild("software_dev", project_dir=fake_project)
    assert spec_builtin.description.startswith("Full-Stack Software Engineering")

    # 2. User directory overrides built-in
    user_override = {
        "name": "software_dev",
        "description": "USER OVERRIDE OF SOFTWARE_DEV",
        "arms": _make_valid_arms(8),
    }
    (user_guilds / "software_dev.json").write_text(json.dumps(user_override), encoding="utf-8")

    spec_user = load_guild("software_dev", project_dir=fake_project)
    assert spec_user.description == "USER OVERRIDE OF SOFTWARE_DEV"

    # 3. Project directory overrides user directory
    proj_override = {
        "name": "software_dev",
        "description": "PROJECT OVERRIDE OF SOFTWARE_DEV",
        "arms": _make_valid_arms(8),
    }
    (proj_guilds / "software_dev.json").write_text(json.dumps(proj_override), encoding="utf-8")

    spec_proj = load_guild("software_dev", project_dir=fake_project)
    assert spec_proj.description == "PROJECT OVERRIDE OF SOFTWARE_DEV"


# ==============================================================================
# 4. Tool Policy Clamping & Warning Logging
# ==============================================================================


def test_tool_policy_clamping_with_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Verify a guild requesting denied tools is clamped and logs a warning without crashing."""
    caplog.set_level("WARNING")

    # Create custom policy denying run_command and bash
    restricted_policy = ToolPolicy(
        allowed_tools={"read_file", "write_file", "list_dir"},
        denied_tools={"run_command", "bash"},
    )

    arms = [
        ArmSpec(
            id=i,
            role=f"arm_{i}",
            focus=f"Arm {i} focus",
            color="#00F0FF",
            tools=["read_file", "write_file", "run_command", "bash"],
        )
        for i in range(8)
    ]
    spec = GuildSpec(name="restricted_guild", description="Restricted tools test", arms=arms)

    # Convert to roster under the restricted policy
    roster = spec.to_arm_roster(tool_policy=restricted_policy)
    assert len(roster) == 8

    # All arms should have had run_command and bash clamped
    for arm in roster:
        assert "run_command" not in arm.tools
        assert "bash" not in arm.tools
        assert "read_file" in arm.tools
        assert "write_file" in arm.tools

    # Verify warning log message was emitted
    assert any(
        "denied by global policy for arm" in record.message and "clamped" in record.message
        for record in caplog.records
    )


# ==============================================================================
# 5. Full Run on Fake Provider with Custom Guild & Telemetry
# ==============================================================================


@pytest.mark.anyio
async def test_full_run_with_custom_guild_telemetry(tmp_path: Path) -> None:
    """Verify a run with a custom guild completes and telemetry payload contains custom arm colors."""
    custom_colors = [
        "#112233",
        "#223344",
        "#334455",
        "#445566",
        "#556677",
        "#667788",
        "#778899",
        "#8899AA",
    ]
    arms = [
        ArmSpec(
            id=i,
            role=f"specialist_{i}",
            focus=f"Specialist focus {i}",
            color=custom_colors[i],
            tools=["read_file", "write_file"],
            file_scope=[f"scope_{i}/"],
        )
        for i in range(8)
    ]
    spec = GuildSpec(name="custom_tel_guild", description="Telemetry test guild", arms=arms)
    roster = spec.to_arm_roster()

    config = OctoFlowConfig(
        morphology=SwarmMorphology.CUSTOM,
        guild="custom_tel_guild",
        custom_roster=roster,
        model_provider="mock",
        dry_run=True,
        workspace_dir=str(tmp_path),
    )

    telemetry_events: list[SwarmTelemetryEvent] = []

    def handle_telemetry(evt: SwarmTelemetryEvent) -> None:
        telemetry_events.append(evt)

    conductor = SupraesophagealConductor(
        config=config,
        telemetry_callback=handle_telemetry,
    )

    result = await conductor.arun_swarm(
        objective="Analyze workspace with custom guild", max_cycles=1
    )
    assert result is not None

    # Verify initial SWARM_INIT event was emitted with custom guild & palette
    init_events = [e for e in telemetry_events if e.event_type == "SWARM_INIT"]
    assert len(init_events) >= 1
    init_evt = init_events[0]
    assert init_evt.payload is not None
    assert init_evt.payload.get("guild") == "custom_tel_guild"
    assert init_evt.payload.get("arm_colors") == custom_colors

    # Verify step/escalation events carried arm colors
    step_events = [e for e in telemetry_events if e.event_type in ("STEP", "ESCALATION")]
    assert len(step_events) >= 1
    for step_e in step_events:
        assert step_e.payload is not None
        assert "arm_colors" in step_e.payload
        assert step_e.color_hex in custom_colors


# ==============================================================================
# 6. Showcase Example Guild: examples/guilds/data_science.json
# ==============================================================================


def test_data_science_example_guild() -> None:
    """Verify that examples/guilds/data_science.json is valid and contains 8 distinct roles."""
    repo_root = Path(__file__).resolve().parent.parent
    ds_file = repo_root / "examples" / "guilds" / "data_science.json"
    assert ds_file.exists(), f"Missing example file: {ds_file}"

    is_valid, errors, spec = validate_guild_file(ds_file)
    assert is_valid, f"Validation errors in data_science.json: {errors}"
    assert spec is not None
    assert spec.name == "data_science"
    assert len(spec.arms) == 8

    # Verify all 8 roles are unique and valid
    roles = [arm.role for arm in spec.arms]
    assert len(set(roles)) == 8
    assert "data_ingestion" in roles
    assert "eda_profiling" in roles
    assert "feature_engineering" in roles
    assert "model_training" in roles
    assert "hyperparameter_tuning" in roles
    assert "evaluation_metrics" in roles
    assert "explainability_governance" in roles
    assert "pipeline_deployment" in roles

    # Verify all 8 colors are valid hex strings
    palette = spec.get_palette()
    assert len(palette) == 8
    assert all(c.startswith("#") and len(c) == 7 for c in palette)


# ==============================================================================
# 7. CLI Commands: list, validate, show, export
# ==============================================================================


def test_cli_guild_validate_valid(runner: CliRunner) -> None:
    """Verify octoflow guild validate <valid_file> returns exit code 0."""
    repo_root = Path(__file__).resolve().parent.parent
    ds_file = repo_root / "examples" / "guilds" / "data_science.json"
    result = runner.invoke(app, ["guild", "validate", str(ds_file)])
    assert result.exit_code == 0
    assert "is valid" in result.output


def test_cli_guild_validate_invalid(runner: CliRunner, tmp_path: Path) -> None:
    """Verify octoflow guild validate <invalid_file> returns exit code 1 with JSON pointers."""
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text(
        json.dumps({"name": "bad", "description": "bad", "arms": _make_valid_arms(3)}),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["guild", "validate", str(corrupt_file)])
    assert result.exit_code == 1
    assert "✘ Validation failed" in result.output
    assert "/arms" in result.output


def test_cli_guild_list(runner: CliRunner) -> None:
    """Verify octoflow guild list shows available guilds."""
    result = runner.invoke(app, ["guild", "list"])
    assert result.exit_code == 0
    assert "software_dev" in result.output
    assert "aiml_research" in result.output
    assert "fullstack_ai" in result.output


def test_cli_guild_show_builtin(runner: CliRunner) -> None:
    """Verify octoflow guild show <name> displays 8 arms table."""
    result = runner.invoke(app, ["guild", "show", "software_dev"])
    assert result.exit_code == 0
    assert "Guild Roster: software_dev" in result.output
    assert "Arm 0" in result.output
    assert "Arm 7" in result.output


def test_cli_guild_show_nonexistent(runner: CliRunner) -> None:
    """Verify octoflow guild show <nonexistent> exits code 1."""
    result = runner.invoke(app, ["guild", "show", "nonexistent_guild_xyz"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_64_persona_ecosystem_loads_cleanly() -> None:
    """Verify all 8 first-party domain guilds load 64 distinct valid specialist personas."""
    domain_guilds = [
        "cloud_devops",
        "cybersec_ops",
        "data_science",
        "enterprise_migration",
        "mobile_apps",
        "qa_resilience",
        "systems_embedded",
        "web_fullstack",
    ]
    total_personas = 0
    all_roles: set[str] = set()

    for guild_name in domain_guilds:
        spec = load_guild(guild_name)
        assert spec.name == guild_name
        assert len(spec.arms) == 8
        roster = spec.to_arm_roster()
        assert len(roster) == 8

        for arm in spec.arms:
            assert 0 <= arm.id <= 7
            assert len(arm.role) > 0
            assert arm.color.startswith("#") and len(arm.color) == 7
            assert len(arm.system_prompt) > 0
            assert len(arm.tools) > 0
            assert len(arm.file_scope) > 0
            all_roles.add(f"{guild_name}:{arm.role}")
            total_personas += 1

    assert total_personas == 64
    assert len(all_roles) == 64  # All 64 personas are unique across guilds


def test_cli_guild_show_new_domain_guild(runner: CliRunner) -> None:
    """Verify CLI can display the new first-party domain guilds."""
    result = runner.invoke(app, ["guild", "show", "cloud_devops"])
    assert result.exit_code == 0
    assert "Guild Roster: cloud_devops" in result.output
    assert "Arm 0" in result.output
    assert "Arm 7" in result.output


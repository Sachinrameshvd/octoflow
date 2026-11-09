"""Tests for OctoFlow's 4 Developer Pillars:
1. PyPI packaging & precompiled visualizer assets
2. Interactive setup wizard and configuration persistence
3. Existing codebase safety, branch protection, and AST scanning
4. Heterogeneous model routing (fast vs frontier tiers)
"""

import json
import os
from pathlib import Path

from octoflow.conductor import SupraesophagealConductor, scan_codebase_topology
from octoflow.config import SOFTWARE_DEV_ROSTER, OctoFlowConfig
from octoflow.provider import AnthropicProvider, MockLLMProvider, OpenAIProvider, get_llm_provider


def test_pypi_dist_bundling():
    """Verify that pre-compiled visualizer assets exist inside the octoflow package directory."""
    import octoflow

    pkg_dir = Path(octoflow.__file__).parent
    dist_dir = pkg_dir / "dist"

    assert dist_dir.exists(), "octoflow/dist directory must exist for zero-dependency pip installs"
    assert (dist_dir / "index.html").exists(), "dist/index.html must be bundled"
    assert (dist_dir / "assets").exists(), "dist/assets must be bundled"


def test_config_persistence_and_loading(tmp_path, monkeypatch):
    """Verify that ~/.octoflow/config.json auto-populates OctoFlowConfig."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    octo_dir = fake_home / ".octoflow"
    octo_dir.mkdir()

    cfg_payload = {
        "anthropic_api_key": "sk-ant-test-12345",
        "openai_api_key": "sk-proj-test-67890",
        "default_model": "anthropic",
        "default_budget": 25.50,
        "default_octos": "3",
    }
    (octo_dir / "config.json").write_text(json.dumps(cfg_payload), encoding="utf-8")

    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # Test auto-loading without environment variables
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = OctoFlowConfig()
    assert config.anthropic_api_key == "sk-ant-test-12345"
    assert config.openai_api_key == "sk-proj-test-67890"


def test_codebase_topology_ast_scanning(tmp_path):
    """Verify AST parsing and topology detection on an existing project workspace."""
    ws = tmp_path / "sample_project"
    ws.mkdir()

    # Create package.json
    pkg = {"name": "my-neural-app", "dependencies": {"react": "^19.0.0", "three": "^0.180.0"}}
    (ws / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

    # Create a Python module with classes and functions
    py_code = '''
class TransformerCore:
    """Core attention module."""
    def forward(self, x):
        pass

def compute_loss(pred, target):
    return 0.42
'''
    (ws / "core.py").write_text(py_code, encoding="utf-8")

    topology = scan_codebase_topology(str(ws))

    assert "Node/Frontend project 'my-neural-app'" in topology
    assert "react" in topology
    assert "three" in topology
    assert "core.py" in topology
    assert "TransformerCore" in topology
    assert "compute_loss" in topology


def test_heterogeneous_model_routing():
    """Verify that different cognitive tiers map to optimal model endpoints."""
    # 1. Roster verification
    arch_role = SOFTWARE_DEV_ROSTER[0]
    devops_role = SOFTWARE_DEV_ROSTER[7]
    assert arch_role.model_tier == "frontier", "Arm 0 (Architect) must be frontier tier"
    assert devops_role.model_tier == "fast", "Arm 7 (DevOps/Docs) must be fast tier"

    # 2. Anthropic routing
    ant_config = OctoFlowConfig(model_provider="anthropic", api_key="sk-ant-dummy")
    frontier_prov = get_llm_provider(ant_config, tier="frontier")
    fast_prov = get_llm_provider(ant_config, tier="fast")

    assert isinstance(frontier_prov, AnthropicProvider)
    assert frontier_prov.model == "claude-3-7-sonnet-20250219"
    assert isinstance(fast_prov, AnthropicProvider)
    assert fast_prov.model == "claude-3-5-haiku-20241022"

    # 3. OpenAI routing
    oai_config = OctoFlowConfig(model_provider="openai", api_key="sk-dummy")
    oai_frontier = get_llm_provider(oai_config, tier="frontier")
    oai_fast = get_llm_provider(oai_config, tier="fast")

    assert isinstance(oai_frontier, OpenAIProvider)
    assert oai_frontier.model == "o3-mini"
    assert isinstance(oai_fast, OpenAIProvider)
    assert oai_fast.model == "gpt-4o-mini"


def test_preflight_syntax_validation(tmp_path):
    """Verify that write_file rejects syntax errors in Python and JSON, protecting workspace."""
    from octoflow.tools import WorkspaceSandbox

    sandbox = WorkspaceSandbox(str(tmp_path))

    # 1. Invalid Python syntax
    bad_py = "def broken(x: return 42"
    res_py = sandbox.write_file("module.py", bad_py)
    assert not res_py.success
    assert res_py.returncode == 1
    assert "PreFlightSyntaxError" in res_py.stderr
    assert not (tmp_path / "module.py").exists(), "Corrupt Python file must NOT be written to disk"

    # 2. Valid Python syntax
    good_py = "def valid(x):\n    return x * 2\n"
    res_good_py = sandbox.write_file("module.py", good_py)
    assert res_good_py.success
    assert (tmp_path / "module.py").exists()

    # 3. Invalid JSON syntax
    bad_json = '{"unclosed": "brace"'
    res_json = sandbox.write_file("config.json", bad_json)
    assert not res_json.success
    assert "PreFlightJSONError" in res_json.stderr

    # 4. Valid JSON syntax
    good_json = '{"valid": true}'
    res_good_json = sandbox.write_file("config.json", good_json)
    assert res_good_json.success


def test_cross_provider_heterogeneous_routing():
    """Verify true cross-provider routing (Anthropic frontier + OpenAI fast + Ollama fast)."""
    from octoflow.provider import OllamaProvider

    # Case A: Anthropic frontier + OpenAI fast
    mixed_config = OctoFlowConfig(
        frontier_provider="anthropic",
        fast_provider="openai",
        anthropic_api_key="sk-ant-test",
        openai_api_key="sk-proj-test",
    )
    frontier_prov = get_llm_provider(mixed_config, tier="frontier")
    fast_prov = get_llm_provider(mixed_config, tier="fast")

    assert isinstance(frontier_prov, AnthropicProvider)
    assert frontier_prov.model == "claude-3-7-sonnet-20250219"
    assert isinstance(fast_prov, OpenAIProvider)
    assert fast_prov.model == "gpt-4o-mini"

    # Case B: Anthropic frontier + Ollama fast (free local models for docs/devops)
    local_mixed = OctoFlowConfig(
        frontier_provider="anthropic",
        fast_provider="ollama",
        anthropic_api_key="sk-ant-test",
    )
    local_fast = get_llm_provider(local_mixed, tier="fast")
    assert isinstance(local_fast, OllamaProvider)
    assert local_fast.model == "qwen2.5-coder:1.5b"


def test_doctor_diagnostics(tmp_path):
    """Verify that run_doctor executes cleanly across all subsystem health checks."""
    from octoflow.cli import run_doctor

    # Should run with no unhandled exceptions
    run_doctor(workspace=str(tmp_path), fix=True)
    # With fix=True, git repo should be initialized if missing
    assert (tmp_path / ".git").exists()


def test_plan_decomposition_blueprint():
    """Verify that interactive /plan generates an 8-arm mission blueprint with cognitive tiers."""
    conductor = SupraesophagealConductor()
    goals = conductor.decompose_objective("Build an asynchronous real-time chat service")

    assert len(goals) == 8
    # Verify Arm 0 (Architect) and Arm 7 (DevOps)
    roster = conductor.config.get_roster()
    assert roster[0].model_tier == "frontier"
    assert roster[7].model_tier == "fast"
    assert "architecture" in goals[0].lower() or "interface" in goals[0].lower()
    assert "docker" in goals[7].lower() or "readme" in goals[7].lower()


def test_custom_guild_and_roster_loader(tmp_path, monkeypatch):
    """Verify loading, listing, and exporting custom 8-arm community guilds."""
    from octoflow.config import (
        SOFTWARE_DEV_ROSTER,
        list_available_guilds,
        load_custom_guild,
        save_custom_guild,
    )

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # 1. Built-in guilds available by default
    guilds = list_available_guilds()
    assert "software_dev" in guilds
    assert "aiml_research" in guilds
    assert "fullstack_ai" in guilds

    # 2. Save a custom community guild template
    custom_name = "web3_security"
    custom_desc = "Decentralized contracts audit and EVM pentesting swarm"
    saved_path = save_custom_guild(custom_name, SOFTWARE_DEV_ROSTER, custom_desc)
    assert Path(saved_path).exists()

    # 3. Custom guild shows up in available list
    updated_guilds = list_available_guilds()
    assert custom_name in updated_guilds
    assert updated_guilds[custom_name] == custom_desc

    # 4. Load the custom guild
    roster = load_custom_guild(custom_name)
    assert roster is not None
    assert len(roster) == 8

    # 5. OctoFlowConfig automatically applies custom guild
    cfg = OctoFlowConfig(guild=custom_name)
    applied_roster = cfg.get_roster()
    assert len(applied_roster) == 8


def test_precommit_swarm_guard_and_hooks(tmp_path):
    """Verify that octos install-hooks and guard block secrets & AST syntax errors."""
    import subprocess

    from octoflow.cli import install_git_hooks, run_guard

    # 1. Initialize a clean git repository
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@octoflow.dev"], cwd=str(tmp_path), check=True
    )
    subprocess.run(["git", "config", "user.name", "OctoFlow Tester"], cwd=str(tmp_path), check=True)

    # 2. Install hooks
    installed = install_git_hooks(str(tmp_path))
    assert installed is True
    hook_file = tmp_path / ".git" / "hooks" / "pre-commit"
    assert hook_file.exists()
    assert os.access(hook_file, os.X_OK)

    # 3. Clean workspace passes guard
    (tmp_path / "app.py").write_text("def hello():\n    return 'clean'\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=str(tmp_path), check=True)
    assert run_guard(str(tmp_path)) is True

    # 4. AST syntax error triggers guard block
    (tmp_path / "broken.py").write_text("def broken(x: return 42\n", encoding="utf-8")
    subprocess.run(["git", "add", "broken.py"], cwd=str(tmp_path), check=True)
    assert run_guard(str(tmp_path)) is False
    subprocess.run(["git", "rm", "-f", "broken.py"], cwd=str(tmp_path), capture_output=True)

    # 5. Secret leak (API Key) triggers guard block
    (tmp_path / "config.env").write_text(
        "ANTHROPIC_KEY=sk-" + "ant-api03-abcdef1234567890abcdef1234567890\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "config.env"], cwd=str(tmp_path), check=True)
    assert run_guard(str(tmp_path)) is False


def test_episodic_codebase_vector_rag(tmp_path):
    """Verify local semantic vector indexing and cosine search in the Vertical Lobe."""
    from octoflow.memory import EpisodicCodebaseRAG, VerticalLobeMemory

    # 1. Create a mini codebase
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "auth.py").write_text(
        "def verify_jwt_token(raw_token):\n"
        "    '''Verify signature of incoming bearer token.'''\n"
        "    return raw_token == 'valid'\n",
        encoding="utf-8",
    )
    (src_dir / "database.py").write_text(
        "class ConnectionPool:\n"
        "    '''Manage PostgreSQL connection handles and pooling.'''\n"
        "    def get_conn(self):\n"
        "        pass\n",
        encoding="utf-8",
    )

    # 2. Index workspace with EpisodicCodebaseRAG
    rag = EpisodicCodebaseRAG()
    num_chunks = rag.index_workspace(str(tmp_path))
    assert num_chunks >= 2

    # 3. Semantic search for JWT auth
    hits = rag.search("verify jwt token authentication", top_k=2)
    assert len(hits) > 0
    top_hit = hits[0]
    assert "auth.py" in top_hit["file_path"]
    assert top_hit["symbol"] == "verify_jwt_token"
    assert top_hit["score"] > 0.3

    # 4. Semantic search for Database connection
    db_hits = rag.search("postgresql database connection pool", top_k=2)
    assert len(db_hits) > 0
    assert "database.py" in db_hits[0]["file_path"]
    assert "ConnectionPool" in db_hits[0]["symbol"]

    # 5. Integration through VerticalLobeMemory
    vl = VerticalLobeMemory()
    vl_chunks = vl.index_codebase(str(tmp_path))
    assert vl_chunks >= 2
    vl_search_results = vl.search_codebase("jwt token auth")
    assert len(vl_search_results) > 0
    assert "auth.py" in vl_search_results[0]["file_path"]


def test_direct_arm_interrogation_and_conversational_reflex():
    """Verify that developers can talk 1-on-1 naturally without memorizing arm numbers."""
    conductor = SupraesophagealConductor()

    # 1. Arm resolution by integer ID or role keyword
    arm_arch = conductor.get_arm(0)
    assert arm_arch is not None
    assert arm_arch.role.name == "architect"

    arm_sec = conductor.get_arm("security")
    assert arm_sec is not None
    assert arm_sec.arm_id == 6

    arm_db = conductor.get_arm("database")
    assert arm_db is not None
    assert arm_db.arm_id == 1

    arm_qa = conductor.get_arm("qa")
    assert arm_qa is not None
    assert arm_qa.arm_id == 5

    # 2. Conversational Intent Classification: Questions auto-route to the right specialist
    # Database question -> Arm 1
    intent_db = conductor.classify_conversational_intent(
        "Why did you choose PostgreSQL over SQLite for this service?"
    )
    assert intent_db["intent"] == "INQUIRY"
    assert intent_db["primary_arm_id"] == 1

    # Security question -> Arm 6
    intent_sec = conductor.classify_conversational_intent(
        "Are there any SQL injection or CSRF risks in api/auth.py?"
    )
    assert intent_sec["intent"] == "INQUIRY"
    assert intent_sec["primary_arm_id"] == 6

    # QA / Test question -> Arm 5
    intent_qa = conductor.classify_conversational_intent(
        "Why is the test coverage for the token refresh endpoint failing?"
    )
    assert intent_qa["intent"] == "INQUIRY"
    assert intent_qa["primary_arm_id"] == 5

    # Architecture question -> Arm 0
    intent_arch = conductor.classify_conversational_intent(
        "How did you structure the folder topology and interface boundaries?"
    )
    assert intent_arch["intent"] == "INQUIRY"
    assert intent_arch["primary_arm_id"] == 0

    # 3. Action Directives classify as ACTION (not inquiry)
    intent_action = conductor.classify_conversational_intent(
        "Build an asynchronous real-time chat service"
    )
    assert intent_action["intent"] == "ACTION"

    intent_patch = conductor.classify_conversational_intent("Patch the CSRF issue in api/auth.py")
    assert intent_patch["intent"] == "ACTION"

    # 4. Full 1-on-1 Dialogue Turn
    turn = conductor.converse("Why did you choose PostgreSQL over SQLite for this service?")
    assert turn["intent"] == "INQUIRY"
    assert turn["primary_arm_id"] == 1
    assert "Database" in turn["primary_arm_title"]
    assert len(turn["response"]) > 20


def test_omni_ide_auto_onboarding(tmp_path, monkeypatch):
    """Verify 1-command Omni-IDE onboarding across Cursor, Claude, VS Code, and Git."""
    import subprocess

    from octoflow.onboarding import onboard_ide

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    ws = tmp_path / "my_project"
    ws.mkdir()
    subprocess.run(["git", "init"], cwd=str(ws), check=True, capture_output=True)

    # 1. Run onboarding
    res = onboard_ide(workspace=str(ws))
    assert res["cursor"] is True
    assert res["claude_code"] is True
    assert res["vscode_tasks"] is True
    assert res["git_hooks"] is True

    # 2. Verify .cursorrules
    cursor_file = ws / ".cursorrules"
    assert cursor_file.exists()
    cursor_text = cursor_file.read_text(encoding="utf-8")
    assert "OctoFlow Cephalopod Swarm Delegation Rules" in cursor_text
    assert "Arm 0: System Architect" in cursor_text
    assert "octos run" in cursor_text

    # 3. Verify Claude Code CLI ~/.claude.json
    claude_cfg = fake_home / ".claude.json"
    assert claude_cfg.exists()
    claude_data = json.loads(claude_cfg.read_text(encoding="utf-8"))
    assert "mcpServers" in claude_data
    assert "octoflow" in claude_data["mcpServers"]
    assert claude_data["mcpServers"]["octoflow"]["command"] == "octos"

    # 4. Verify VS Code .vscode/tasks.json
    tasks_file = ws / ".vscode" / "tasks.json"
    assert tasks_file.exists()
    tasks_data = json.loads(tasks_file.read_text(encoding="utf-8"))
    assert "tasks" in tasks_data
    task_labels = [t["label"] for t in tasks_data["tasks"]]
    assert "OctoFlow: Launch Cockpit" in task_labels
    assert "OctoFlow: Swarm Guard Scan" in task_labels
    assert "OctoFlow: 3D Visualizer" in task_labels

    # 5. Verify Git pre-commit hook
    hook_file = ws / ".git" / "hooks" / "pre-commit"
    assert hook_file.exists()
    assert os.access(hook_file, os.X_OK)

    # 6. Verify non-destructive merging on subsequent run
    # Custom existing rule in .cursorrules
    cursor_file.write_text("CUSTOM_DEV_DIRECTIVE = true\n" + cursor_text, encoding="utf-8")
    # Custom MCP server in ~/.claude.json
    claude_data["mcpServers"]["custom_tool"] = {"command": "custom", "args": []}
    claude_cfg.write_text(json.dumps(claude_data), encoding="utf-8")
    # Custom task in .vscode/tasks.json
    tasks_data["tasks"].append(
        {"label": "User Custom Build", "type": "shell", "command": "npm run build"}
    )
    tasks_file.write_text(json.dumps(tasks_data), encoding="utf-8")

    # Re-run onboarding
    res2 = onboard_ide(workspace=str(ws))
    assert res2["cursor"] is True

    # Check preserved customizations
    assert "CUSTOM_DEV_DIRECTIVE = true" in cursor_file.read_text(encoding="utf-8")
    updated_claude = json.loads(claude_cfg.read_text(encoding="utf-8"))
    assert "custom_tool" in updated_claude["mcpServers"]
    assert "octoflow" in updated_claude["mcpServers"]

    updated_tasks = json.loads(tasks_file.read_text(encoding="utf-8"))
    updated_labels = [t["label"] for t in updated_tasks["tasks"]]
    assert "User Custom Build" in updated_labels
    assert "OctoFlow: Launch Cockpit" in updated_labels


def test_generate_github_action_workflow(tmp_path):
    """Verify that generate_github_action_workflow produces valid GitHub Action workflow YAML."""
    from octoflow.ci import generate_github_action_workflow

    wf_file = generate_github_action_workflow(str(tmp_path))
    assert wf_file.exists()
    assert wf_file == tmp_path / ".github" / "workflows" / "octoflow-guard.yml"

    content = wf_file.read_text(encoding="utf-8")
    assert "name: OctoFlow Swarm Guard" in content
    assert "actions/checkout@v4" in content
    assert "octos review-pr --summary" in content
    assert "pull_request:" in content


def test_review_pull_request_clean(tmp_path):
    """Verify that review_pull_request approves clean PRs with zero merge hazards."""
    import subprocess

    from octoflow.ci import review_pull_request

    # Setup git repo
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "ci@octoflow.dev"], cwd=str(tmp_path), capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "OctoBot"], cwd=str(tmp_path), capture_output=True
    )

    # Initial commit
    init_file = tmp_path / "hello.py"
    init_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    subprocess.run(["git", "add", "hello.py"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)

    # Clean modification + test
    init_file.write_text("def hello():\n    return 'octoflow'\n", encoding="utf-8")
    test_file = tmp_path / "test_hello.py"
    test_file.write_text("def test_hello():\n    assert True\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "hello.py", "test_hello.py"], cwd=str(tmp_path), capture_output=True
    )
    subprocess.run(["git", "commit", "-m", "update hello"], cwd=str(tmp_path), capture_output=True)

    res = review_pull_request(workspace=str(tmp_path), base_ref="HEAD~1", write_summary=False)
    assert res["hard_block"] is False
    assert res["exit_code"] == 0
    assert "READY TO MERGE" in res["markdown_report"]


def test_review_pull_request_secret_leak_block(tmp_path):
    """Verify that Arm 6 detects secret leaks in diff and issues a hard block (exit code 1)."""
    import subprocess

    from octoflow.ci import review_pull_request

    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "ci@octoflow.dev"], cwd=str(tmp_path), capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "OctoBot"], cwd=str(tmp_path), capture_output=True
    )

    init_file = tmp_path / "app.py"
    init_file.write_text("# initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)

    # Leak secret in next commit
    init_file.write_text(
        "API_KEY = 'sk-" + "ant-api03-abcdefghijklmnopqrstuvwxyz12345'\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "app.py"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "leak secret"], cwd=str(tmp_path), capture_output=True)

    res = review_pull_request(workspace=str(tmp_path), base_ref="HEAD~1", write_summary=False)
    assert res["hard_block"] is True
    assert res["exit_code"] == 1
    assert any("CRITICAL: Leaked credentials" in f for f in res["arm6_findings"])
    assert "MERGE HAZARDS DETECTED" in res["markdown_report"]


def test_review_pull_request_ast_syntax_error_block(tmp_path):
    """Verify that Arm 5 detects invalid Python AST syntax in diff and hard blocks."""
    import subprocess

    from octoflow.ci import review_pull_request

    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "ci@octoflow.dev"], cwd=str(tmp_path), capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "OctoBot"], cwd=str(tmp_path), capture_output=True
    )

    init_file = tmp_path / "service.py"
    init_file.write_text("def serve():\n    pass\n", encoding="utf-8")
    subprocess.run(["git", "add", "service.py"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)

    # Corrupt python syntax
    init_file.write_text("def broken(syntax return 42\n", encoding="utf-8")
    subprocess.run(["git", "add", "service.py"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "broken syntax"], cwd=str(tmp_path), capture_output=True)

    res = review_pull_request(workspace=str(tmp_path), base_ref="HEAD~1", write_summary=False)
    assert res["hard_block"] is True
    assert res["exit_code"] == 1
    assert any("CRITICAL: AST Syntax Errors" in f for f in res["arm5_findings"])


def test_review_pull_request_github_step_summary(tmp_path, monkeypatch):
    """Verify that review_pull_request writes markdown to $GITHUB_STEP_SUMMARY."""
    import subprocess

    from octoflow.ci import review_pull_request

    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "ci@octoflow.dev"], cwd=str(tmp_path), capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "OctoBot"], cwd=str(tmp_path), capture_output=True
    )

    init_file = tmp_path / "index.js"
    init_file.write_text("console.log('init');\n", encoding="utf-8")
    subprocess.run(["git", "add", "index.js"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)

    summary_file = tmp_path / "step_summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))

    init_file.write_text("console.log('updated');\n", encoding="utf-8")
    subprocess.run(["git", "add", "index.js"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "update"], cwd=str(tmp_path), capture_output=True)

    res = review_pull_request(workspace=str(tmp_path), base_ref="HEAD~1", write_summary=True)
    assert summary_file.exists()
    summary_text = summary_file.read_text(encoding="utf-8")
    assert "## OctoFlow Swarm Guard CI Review" in summary_text
    assert "Arm 6: Security" in summary_text
    assert "Arm 5: QA & AST" in summary_text
    assert "Arm 0: Architect" in summary_text


def test_generate_html_audit_report(tmp_path):
    """Verify that generate_html_audit_report produces a 100% self-contained offline HTML report."""
    from octoflow.report import collect_mission_audit_data, generate_html_audit_report

    # Create sample files in tmp_path
    (tmp_path / "app.py").write_text("def run():\n    return 42\n", encoding="utf-8")
    (tmp_path / "test_app.py").write_text("def test_run():\n    assert True\n", encoding="utf-8")

    sample_telemetry = [
        {
            "timestamp": 0.5,
            "arm_id": 0,
            "role": "Architect",
            "event_type": "STEP",
            "surprise": 0.04,
        },
        {"timestamp": 1.2, "arm_id": 1, "role": "Database", "event_type": "STEP", "surprise": 0.05},
        {"timestamp": 2.1, "arm_id": 6, "role": "Security", "event_type": "STEP", "surprise": 0.02},
    ]

    m_data = collect_mission_audit_data(
        workspace=str(tmp_path),
        objective="Implement Distributed OAuth2 Token Exchange",
        telemetry_events=sample_telemetry,
        duration_seconds=12.4,
    )

    out_file = tmp_path / "mission_audit.html"
    res_path = generate_html_audit_report(
        m_data, output_path=str(out_file), theme_id="bioluminescence"
    )

    assert res_path.exists()
    assert res_path == out_file
    assert res_path.stat().st_size > 5000, "Report must contain full inline CSS, SVG, and JS"

    html = res_path.read_text(encoding="utf-8")

    # 1. HTML5 structure & zero external CDN scripts
    assert "<!DOCTYPE html>" in html
    assert "OctoFlow Mission Audit" in html
    assert "http://" not in html.split("<head>")[1].split("</head>")[0]
    assert "https://" not in html.split("<head>")[1].split("</head>")[0]

    # 2. Executive Token ROI & Truthful Accounting
    assert "Tokens Spent" in html
    assert "Estimated Avoided Tokens" in html
    assert "Sensory Gate Evaluations" in html

    # 3. Interactive SVG Connectome & Scrubber
    assert '<svg class="connectome-svg"' in html
    assert 'id="timelineScrubber"' in html
    assert "renderConnectome" in html

    # 4. All 8 Ganglia Arms present
    for i in range(8):
        assert f"Arm {i}" in html


def test_export_cli_cmd(tmp_path):
    """Verify that octos export CLI command successfully writes HTML audit file."""
    from octoflow.cli import export_cli_cmd

    target_html = tmp_path / "custom_export.html"
    export_cli_cmd(workspace=str(tmp_path), output=str(target_html), open_browser=False)

    assert target_html.exists()
    content = target_html.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Cephalopod Neural Connectome Replay" in content


def test_provider_rate_limit_failover():
    """Verify that FailoverLLMProvider gracefully switches backends upon rate limit or 5xx errors."""
    import asyncio

    from octoflow.provider import BaseLLMProvider, FailoverLLMProvider

    class FailingProvider(BaseLLMProvider):
        def generate(self, prompt, system_prompt="", temperature=0.2, max_tokens=2048):
            raise RuntimeError("429 Too Many Requests: Rate limit exceeded")

        async def agenerate(self, prompt, system_prompt="", temperature=0.2, max_tokens=2048):
            raise RuntimeError("429 Too Many Requests: Rate limit exceeded")

    primary = FailingProvider()
    fallback = MockLLMProvider()

    failover_log = []

    def log_callback(prev, nxt, err):
        failover_log.append((prev, nxt, str(err)))

    failover_prov = FailoverLLMProvider(
        primary=primary, fallbacks=[fallback], on_failover=log_callback
    )

    # 1. Synchronous generation failover
    resp = failover_prov.generate("test prompt")
    assert resp.content != ""
    assert len(failover_prov.failover_history) == 1
    assert "FailingProvider" in failover_prov.failover_history[0]["from"]
    assert "MockLLMProvider" in failover_prov.failover_history[0]["to"]
    assert len(failover_log) == 1

    # 2. Asynchronous generation failover
    async def _test_async():
        return await failover_prov.agenerate("async test")

    async_resp = asyncio.run(_test_async())
    assert async_resp.content != ""
    assert len(failover_prov.failover_history) == 2


def test_self_healing_test_runner(tmp_path):
    """Verify test framework detection, error parsing, and self-healing loop execution."""
    from octoflow.healing import detect_test_framework, parse_pytest_failures, self_heal_workspace

    # 1. Detection
    (tmp_path / "tests").mkdir()
    fw_info = detect_test_framework(str(tmp_path))
    assert fw_info is not None
    assert fw_info[0] == "pytest"

    # 2. Failure traceback parsing
    dummy_output = """
=================================== FAILURES ===================================
__________________________________ test_calc ___________________________________
tests/test_math.py:12: in test_calc
    assert calc(2, 2) == 5
E   AssertionError: assert 4 == 5
FAILED tests/test_math.py::test_calc - AssertionError: assert 4 == 5
=========================== short test summary info ============================
"""
    failures = parse_pytest_failures(dummy_output)
    assert len(failures) >= 1
    assert failures[0]["file"] == "tests/test_math.py"
    assert "AssertionError" in failures[0]["error"]

    # 3. Clean workspace self-healing check (tests already passing or simulated)
    res = self_heal_workspace(str(tmp_path), max_attempts=1)
    assert "framework" in res
    assert "attempts" in res


def test_diff_triage_inspector(tmp_path):
    """Verify interactive git diff triage, AST checking, and automatic staging."""
    import subprocess

    from octoflow.triage import get_workspace_diff_items, triage_workspace_diffs

    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "triage@octoflow.dev"],
        cwd=str(tmp_path),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "TriageBot"], cwd=str(tmp_path), capture_output=True
    )

    # Initial file
    init_f = tmp_path / "api.py"
    init_f.write_text("def ping():\n    return 'pong'\n", encoding="utf-8")
    subprocess.run(["git", "add", "api.py"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)

    # Modify file + add valid new file
    init_f.write_text("def ping():\n    return 'pong_v2'\n", encoding="utf-8")
    new_f = tmp_path / "schema.json"
    new_f.write_text('{"version": 2}', encoding="utf-8")

    items = get_workspace_diff_items(str(tmp_path))
    assert len(items) >= 1
    api_item = next(it for it in items if "api.py" in it["file"])
    assert api_item["ast_valid"] is True
    assert api_item["arm_id"] == 2  # Backend API

    # Run auto-approve triage
    triage_res = triage_workspace_diffs(str(tmp_path), auto_approve=True)
    assert triage_res["total_files"] >= 1
    assert "api.py" in triage_res["accepted"]


def test_slack_discord_webhook_formatting():
    """Verify rich payload formatting for Slack and Discord webhooks."""
    from octoflow.notify import (
        format_discord_payload,
        format_slack_payload,
        send_mission_notification,
    )

    sample_mission = {
        "objective": "Build Distributed Consensus Engine",
        "verdict": "PASSED",
        "branch": "feat/consensus",
        "commit": "a1b2c3d",
        "duration_seconds": 14.5,
        "token_economy": {
            "swarm_cost": 0.22,
            "monolithic_cost": 1.15,
            "savings_pct": 80.9,
        },
        "arms": [{"arm_id": 0, "title": "System Architect"}],
    }

    # 1. Slack Payload
    slack_data = format_slack_payload(sample_mission, custom_msg="Mission Succeeded!")
    assert "blocks" in slack_data
    assert any("Consensus Engine" in str(b) for b in slack_data["blocks"])
    assert "80.9% saved" in str(slack_data["blocks"])

    # 2. Discord Payload
    discord_data = format_discord_payload(sample_mission)
    assert "embeds" in discord_data
    assert discord_data["embeds"][0]["color"] == 0x22C55E
    assert any(f["name"] == "Cost Saved" for f in discord_data["embeds"][0]["fields"])

    # 3. Safe invocation with unconfigured webhook
    res = send_mission_notification(webhook_url=None, mission_data=sample_mission)
    assert res is False


def test_synaptic_context_compaction(tmp_path):
    """Verify that arm.compact_context() condenses early history while preserving recent observations."""
    from octoflow.arm import ArmAgent
    from octoflow.bus import InterBrachialBus
    from octoflow.config import ArmRoleConfig
    from octoflow.memory import VerticalLobeMemory
    from octoflow.tools import WorkspaceSandbox

    role = ArmRoleConfig(arm_id=2, name="backend", title="Backend API", description="API server")
    sandbox = WorkspaceSandbox(str(tmp_path))
    provider = MockLLMProvider()
    bus = InterBrachialBus(n_arms=8)
    memory = VerticalLobeMemory()
    arm = ArmAgent(role_config=role, sandbox=sandbox, provider=provider, bus=bus, memory=memory)

    # Populate 10 historical cycles in saccade_buffer
    for cycle in range(10):
        arm.saccade_buffer.append(
            {
                "step": cycle,
                "action": f"write_file(api/v{cycle}.py)",
                "summary": f"Successfully created route v{cycle}",
                "success": True,
            }
        )

    assert len(arm.saccade_buffer) == 10

    # Compact context keeping last 3 items
    synopsis = arm.compact_context(max_buffer_size=4)

    assert len(arm.saccade_buffer) == 3
    assert "Step 0" in synopsis
    assert "Step 6" in synopsis
    assert arm.saccade_buffer[-1]["step"] == 9


def test_docker_sandbox_execution_and_fallback(tmp_path):
    """Verify that WorkspaceSandbox with sandbox_mode='docker' safely executes commands or falls back."""
    from octoflow.tools import WorkspaceSandbox

    sandbox = WorkspaceSandbox(
        workspace_dir=str(tmp_path),
        sandbox_mode="docker",
        docker_image="python:3.12-slim",
    )

    res = sandbox.run_command("python3 -c \"print('Pillars Verified')\"")
    assert res.success is True
    assert "Pillars Verified" in res.stdout
    assert sandbox.sandbox_mode in ["docker", "local"]


def test_swarm_benchmark_harness(tmp_path):
    """Verify the 8-arm benchmark suite definitions and single task execution harness."""
    from octoflow.bench import BENCHMARK_SUITE, run_single_benchmark

    assert len(BENCHMARK_SUITE) == 5
    suite_ids = [t.id for t in BENCHMARK_SUITE]
    assert "rate_limiter" in suite_ids
    assert "lru_cache" in suite_ids
    assert "jwt_validator" in suite_ids
    assert "dag_topo_sort" in suite_ids
    assert "fastapi_todo" in suite_ids

    # Execute a single challenge in fast mock mode
    bench_dir = tmp_path / "bench_task"
    res = run_single_benchmark("lru_cache", mode="fast", workspace_dir=str(bench_dir))

    assert res["task_key"] == "lru_cache"
    assert "LRU Cache" in res["name"]
    assert "passed" in res
    assert "latency_s" in res
    assert "cost_estimate_usd" in res


def test_monorepo_topology_scanner(tmp_path):
    """Verify scanning and specialist arm assignment for multi-package monorepos."""
    from octoflow.monorepo import scan_monorepo_topology

    # Create pnpm monorepo layout
    (tmp_path / "pnpm-workspace.yaml").write_text(
        "packages:\n  - 'apps/*'\n  - 'packages/*'\n", encoding="utf-8"
    )

    web_dir = tmp_path / "apps" / "web"
    web_dir.mkdir(parents=True)
    (web_dir / "package.json").write_text(
        '{"name": "@octo/web", "dependencies": {"react": "^19.0.0"}}', encoding="utf-8"
    )

    api_dir = tmp_path / "apps" / "api"
    api_dir.mkdir(parents=True)
    (api_dir / "package.json").write_text(
        '{"name": "@octo/api", "dependencies": {"fastify": "^4.0.0"}}', encoding="utf-8"
    )

    db_dir = tmp_path / "packages" / "database"
    db_dir.mkdir(parents=True)
    (db_dir / "package.json").write_text(
        '{"name": "@octo/db", "dependencies": {"prisma": "^5.0.0"}}', encoding="utf-8"
    )

    topo = scan_monorepo_topology(str(tmp_path))

    assert topo["is_monorepo"] is True
    assert topo["package_count"] == 3

    pkg_map = {p["name"]: p for p in topo["packages"]}
    assert "web" in pkg_map
    assert pkg_map["web"]["primary_arm"] == 3  # Frontend UI

    assert "api" in pkg_map
    assert pkg_map["api"]["primary_arm"] == 2  # Backend API

    assert "database" in pkg_map
    assert pkg_map["database"]["primary_arm"] == 2 or pkg_map["database"]["primary_arm"] == 1


def test_shadow_ci_mode(tmp_path):
    """Verify that shadow_mode in review_pull_request returns exit_code=0 even with hard blocks."""
    import subprocess

    from octoflow.ci import review_pull_request

    # Setup git repo with a secret leak
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "shadow@octoflow.dev"],
        cwd=str(tmp_path),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "ShadowBot"], cwd=str(tmp_path), capture_output=True
    )

    f = tmp_path / "config.py"
    f.write_text("# initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "config.py"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)

    # Commit with secret leak
    f.write_text("API_KEY = 'sk-" + "ant-api03-shadowsecretkey1234567890'\n", encoding="utf-8")
    subprocess.run(["git", "add", "config.py"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "leak secret"], cwd=str(tmp_path), capture_output=True)

    # Standard mode blocks with exit_code=1
    blocking_res = review_pull_request(
        workspace=str(tmp_path), base_ref="HEAD~1", shadow_mode=False
    )
    assert blocking_res["hard_block"] is True
    assert blocking_res["exit_code"] == 1

    # Shadow CI mode reports hard block advisory but returns exit_code=0
    shadow_res = review_pull_request(workspace=str(tmp_path), base_ref="HEAD~1", shadow_mode=True)
    assert shadow_res["hard_block"] is True
    assert shadow_res["exit_code"] == 0
    assert "SHADOW CI MODE" in shadow_res["markdown_report"]
    assert "Advisory audit only" in shadow_res["markdown_report"]


def test_asciinema_terminal_recorder(tmp_path):
    """Verify that TerminalRecorder captures I/O events and exports valid Asciinema v2 .cast."""
    from octoflow.recorder import TerminalRecorder

    rec = TerminalRecorder(title="OctoFlow Session Benchmark", width=120, height=35)
    rec.start()
    rec.record_output("Starting OctoFlow 8-Arm Swarm...\r\n")
    rec.record_input("octos run 'Build REST API'\r\n")
    rec.record_output("Arm 0: System Architect decomposed topology\r\n")
    rec.stop()

    out_file = tmp_path / "recording.cast"
    res_path = rec.export_cast(str(out_file))

    assert Path(res_path).exists()
    lines = Path(res_path).read_text(encoding="utf-8").strip().splitlines()

    # Header check
    header = json.loads(lines[0])
    assert header["version"] == 2
    assert header["width"] == 120
    assert header["height"] == 35
    assert header["title"] == "OctoFlow Session Benchmark"

    # Event checks
    assert len(lines) >= 3
    ev1 = json.loads(lines[1])
    assert ev1[1] == "o"
    assert "Starting OctoFlow" in ev1[2]

    ev2 = json.loads(lines[2])
    assert ev2[1] == "i"
    assert "octos run" in ev2[2]

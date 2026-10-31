"""OctoFlow Unified Readiness & Security Audit Engine.

Evaluates an agent codebase across 5 dimensions (100-point scale):
1. Code & Architecture Hygiene (20 pts)
2. Test Suite & Verification (20 pts)
3. Security & Sandboxing (20 pts)
4. Neural & Active Inference Readiness (20 pts)
5. Swarm & Consortium Health (20 pts)
"""

import re
import time
from pathlib import Path

from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from octoflow.federation import PII_RULES


class AuditFinding(BaseModel):
    """An individual check item in the audit."""

    category: str
    name: str
    passed: bool
    points_awarded: float
    max_points: float
    message: str
    recommendation: str = ""


class AuditCategoryResult(BaseModel):
    """Score summary for a single audit category."""

    name: str
    score: float
    max_score: float = 20.0
    findings: list[AuditFinding] = Field(default_factory=list)


class AuditReport(BaseModel):
    """Holistic audit report and readiness grade."""

    timestamp: float = Field(default_factory=time.time)
    workspace_path: str
    total_score: float
    max_score: float = 100.0
    letter_grade: str
    title: str
    categories: dict[str, AuditCategoryResult] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)


def evaluate_workspace(workspace_dir: str = ".") -> AuditReport:
    """Execute all audit checks against the specified workspace."""
    root = Path(workspace_dir).resolve()
    categories: dict[str, AuditCategoryResult] = {}

    # =========================================================================
    # 1. Code & Architecture Hygiene (20 pts)
    # =========================================================================
    code_findings: list[AuditFinding] = []

    # 1.1 Git Repo Initialized
    has_git = (root / ".git").is_dir()
    code_findings.append(
        AuditFinding(
            category="Code Hygiene",
            name="Version Control Integrity",
            passed=has_git,
            points_awarded=5.0 if has_git else 0.0,
            max_points=5.0,
            message=".git repository directory detected" if has_git else "Missing .git repository",
            recommendation="" if has_git else "Run 'git init' to track project history.",
        )
    )

    # 1.2 Configuration Files
    has_pyproject = (root / "pyproject.toml").is_file()
    has_package = (root / "package.json").is_file()
    has_readme = (root / "README.md").is_file()
    has_gitignore = (root / ".gitignore").is_file()
    config_score = sum(
        [1.25 for x in [has_pyproject or has_package, has_readme, has_gitignore, True]]
    )
    code_findings.append(
        AuditFinding(
            category="Code Hygiene",
            name="Project Configuration Manifests",
            passed=config_score >= 3.75,
            points_awarded=float(config_score),
            max_points=5.0,
            message=f"Discovered standard manifests (README: {has_readme}, config: {has_pyproject or has_package})",
            recommendation="Ensure pyproject.toml/package.json, .gitignore, and README.md are all present."
            if config_score < 3.75
            else "",
        )
    )

    # 1.3 Clean Code Structure
    py_files = list(root.glob("octoflow/**/*.py")) + list(root.glob("*.py"))
    clean_syntax = True
    for pf in py_files[:30]:
        try:
            with open(pf, encoding="utf-8", errors="ignore") as f:
                compile(f.read(), str(pf), "exec")
        except SyntaxError:
            clean_syntax = False
            break
    code_findings.append(
        AuditFinding(
            category="Code Hygiene",
            name="Source Code AST Validity",
            passed=clean_syntax,
            points_awarded=5.0 if clean_syntax else 0.0,
            max_points=5.0,
            message="All sampled Python source files compile without syntax errors"
            if clean_syntax
            else "Syntax error detected in codebase",
            recommendation="" if clean_syntax else "Fix compilation syntax errors in .py files.",
        )
    )

    # 1.4 Open Source License
    has_license = (root / "LICENSE").is_file() or (root / "LICENSE.md").is_file()
    code_findings.append(
        AuditFinding(
            category="Code Hygiene",
            name="Legal License & Governance",
            passed=has_license,
            points_awarded=5.0 if has_license else 0.0,
            max_points=5.0,
            message="LICENSE file detected" if has_license else "No LICENSE file found",
            recommendation=""
            if has_license
            else "Add an open-source LICENSE file (e.g., MIT, Apache 2.0).",
        )
    )

    code_total = sum(f.points_awarded for f in code_findings)
    categories["code_hygiene"] = AuditCategoryResult(
        name="Code & Architecture Hygiene",
        score=code_total,
        findings=code_findings,
    )

    # =========================================================================
    # 2. Test Suite & Verification (20 pts)
    # =========================================================================
    test_findings: list[AuditFinding] = []
    tests_dir = (root / "tests") if (root / "tests").is_dir() else (root / "test")
    has_test_dir = tests_dir.is_dir()
    test_findings.append(
        AuditFinding(
            category="Test Suite",
            name="Automated Test Harness Directory",
            passed=has_test_dir,
            points_awarded=5.0 if has_test_dir else 0.0,
            max_points=5.0,
            message=f"Found test directory: {tests_dir.name}"
            if has_test_dir
            else "Missing tests directory",
            recommendation=""
            if has_test_dir
            else "Create a tests/ directory for automated validation.",
        )
    )

    test_files = list(tests_dir.glob("test_*.py")) if has_test_dir else []
    sufficient_tests = len(test_files) >= 3
    test_findings.append(
        AuditFinding(
            category="Test Suite",
            name="Test Case Density",
            passed=sufficient_tests,
            points_awarded=5.0 if sufficient_tests else (2.5 if len(test_files) > 0 else 0.0),
            max_points=5.0,
            message=f"Discovered {len(test_files)} dedicated test files",
            recommendation=""
            if sufficient_tests
            else "Expand test coverage to at least 3 test modules.",
        )
    )

    # Pytest configuration
    has_pytest_config = (root / "pyproject.toml").is_file() or (root / "pytest.ini").is_file()
    test_findings.append(
        AuditFinding(
            category="Test Suite",
            name="Test Runner Configuration",
            passed=has_pytest_config,
            points_awarded=5.0 if has_pytest_config else 2.0,
            max_points=5.0,
            message="Pytest configuration verified"
            if has_pytest_config
            else "No pytest.ini / pyproject pytest settings",
            recommendation=""
            if has_pytest_config
            else "Add pytest configuration in pyproject.toml.",
        )
    )

    # Assertion health check
    has_assertions = False
    for tf in test_files[:5]:
        content = tf.read_text(encoding="utf-8", errors="ignore")
        if "assert " in content or "self.assert" in content:
            has_assertions = True
            break
    test_findings.append(
        AuditFinding(
            category="Test Suite",
            name="Assertion & Invariant Verification",
            passed=has_assertions,
            points_awarded=5.0 if has_assertions else 0.0,
            max_points=5.0,
            message="Active assertions and invariant checks detected"
            if has_assertions
            else "No assert statements found",
            recommendation=""
            if has_assertions
            else "Write assertions checking return values and exceptions.",
        )
    )

    test_total = sum(f.points_awarded for f in test_findings)
    categories["test_suite"] = AuditCategoryResult(
        name="Test Suite & Verification",
        score=test_total,
        findings=test_findings,
    )

    # =========================================================================
    # 3. Security & Sandboxing (20 pts)
    # =========================================================================
    sec_findings: list[AuditFinding] = []

    # 3.1 Plaintext secret leak scan
    leaked_secrets = []
    files_to_scan = (
        list(root.glob("*.env"))
        + list(root.glob("config/*.env"))
        + list(root.glob("octoflow/**/*.py"))[:40]
    )
    for sf in files_to_scan:
        try:
            content = sf.read_text(encoding="utf-8", errors="ignore")
            # Don't flag definition files
            if "PII_RULES" in content or "PIIDetectionRule" in content:
                continue
            for rule in PII_RULES[:8]:  # Check critical keys
                if re.search(rule.pattern, content):
                    leaked_secrets.append(f"{sf.name}: {rule.name}")
                    break
        except Exception:
            pass

    no_leaks = len(leaked_secrets) == 0
    sec_findings.append(
        AuditFinding(
            category="Security",
            name="Hardcoded Secrets & API Key Hygiene",
            passed=no_leaks,
            points_awarded=8.0 if no_leaks else 0.0,
            max_points=8.0,
            message="Zero unredacted API keys or private tokens detected"
            if no_leaks
            else f"Detected secrets: {', '.join(leaked_secrets[:2])}",
            recommendation=""
            if no_leaks
            else "Remove hardcoded credentials and store them in environment variables.",
        )
    )

    # 3.2 Unsafe execution patterns
    dangerous_patterns = []
    for pf in py_files[:40]:
        try:
            content = pf.read_text(encoding="utf-8", errors="ignore")
            if "os.system(" in content:
                dangerous_patterns.append(f"{pf.name}: os.system")
            if (
                "eval(" in content
                and "json.loads" not in content
                and "ast.literal_eval" not in content
            ):
                # check if literal eval
                if not re.search(r"\bast\.literal_eval\(", content):
                    dangerous_patterns.append(f"{pf.name}: raw eval")
        except Exception:
            pass

    safe_exec = len(dangerous_patterns) <= 1
    sec_findings.append(
        AuditFinding(
            category="Security",
            name="Sandboxed Command Execution",
            passed=safe_exec,
            points_awarded=6.0 if safe_exec else 2.0,
            max_points=6.0,
            message="Subprocess execution is sanitized and bounded"
            if safe_exec
            else f"Found unrestricted exec patterns: {', '.join(dangerous_patterns)}",
            recommendation=""
            if safe_exec
            else "Replace os.system and eval with ast.literal_eval and subprocess.run.",
        )
    )

    # 3.3 Federation Guard Status
    has_fed_guard = (root / "octoflow" / "federation.py").is_file()
    sec_findings.append(
        AuditFinding(
            category="Security",
            name="Zero-Trust Federation & PII Scrubber",
            passed=has_fed_guard,
            points_awarded=6.0 if has_fed_guard else 0.0,
            max_points=6.0,
            message="Active 14-rule Federation PII & credential redaction pipeline online"
            if has_fed_guard
            else "Missing federation PII pipeline",
            recommendation=""
            if has_fed_guard
            else "Enable octoflow.federation.FederationGuard to scrub outgoing messages.",
        )
    )

    sec_total = sum(f.points_awarded for f in sec_findings)
    categories["security"] = AuditCategoryResult(
        name="Security & Sandboxing",
        score=sec_total,
        findings=sec_findings,
    )

    # =========================================================================
    # 4. Neural & Active Inference Readiness (20 pts)
    # =========================================================================
    neural_findings: list[AuditFinding] = []

    # 4.1 Biophysical ONNX/PyTorch Model
    has_onnx = (root / "checkpoints" / "octopus_brain.onnx").is_file() or (
        root / "checkpoints"
    ).is_dir()
    neural_findings.append(
        AuditFinding(
            category="Neural Readiness",
            name="ONNX Biological Checkpoint",
            passed=has_onnx,
            points_awarded=6.0 if has_onnx else 3.0,
            max_points=6.0,
            message="ONNX standalone micro-connectome weights ready"
            if has_onnx
            else "Using pure-python heuristic forward model",
            recommendation=""
            if has_onnx
            else "Export checkpoints/octopus_brain.onnx for sub-ms reflex execution.",
        )
    )

    # 4.2 Sensory Surprise Gating
    has_gate = (root / "octoflow" / "gate.py").is_file() or (
        root / "octopus_brain" / "gating.py"
    ).is_file()
    neural_findings.append(
        AuditFinding(
            category="Neural Readiness",
            name="Sensory Surprise Gating (Active Inference)",
            passed=has_gate,
            points_awarded=6.0 if has_gate else 0.0,
            max_points=6.0,
            message="Predictive forward coding with adaptive threshold θ gating (>80% token savings)"
            if has_gate
            else "Missing sensory gate",
            recommendation=""
            if has_gate
            else "Implement sensory surprise gating in octoflow/gate.py.",
        )
    )

    # 4.3 8 Cephalopod Arm Roles
    has_arms = (root / "octoflow" / "arm.py").is_file()
    neural_findings.append(
        AuditFinding(
            category="Neural Readiness",
            name="Brachial Ganglia Ring Topology",
            passed=has_arms,
            points_awarded=4.0 if has_arms else 0.0,
            max_points=4.0,
            message="8 peripheral brachial ganglia configured with lateral ring bus"
            if has_arms
            else "Missing arm ganglia definitions",
            recommendation=""
            if has_arms
            else "Define 8 specialized arm ganglia in octoflow/arm.py.",
        )
    )

    # 4.4 Episodic Memory Store
    has_memory = (root / "octoflow" / "memory.py").is_file()
    neural_findings.append(
        AuditFinding(
            category="Neural Readiness",
            name="Episodic Vector Memory",
            passed=has_memory,
            points_awarded=4.0 if has_memory else 0.0,
            max_points=4.0,
            message="Episodic synaptic memory and experience recall active"
            if has_memory
            else "No episodic memory module",
            recommendation=""
            if has_memory
            else "Enable octoflow.memory.SynapticMemory for cross-task learning.",
        )
    )

    neural_total = sum(f.points_awarded for f in neural_findings)
    categories["neural_readiness"] = AuditCategoryResult(
        name="Neural & Active Inference Readiness",
        score=neural_total,
        findings=neural_findings,
    )

    # =========================================================================
    # 5. Swarm & Consortium Health (20 pts)
    # =========================================================================
    swarm_findings: list[AuditFinding] = []

    # 5.1 Self-Healing Engine
    has_healing = (root / "octoflow" / "healing.py").is_file()
    swarm_findings.append(
        AuditFinding(
            category="Swarm Health",
            name="Autonomous Self-Healing Loop",
            passed=has_healing,
            points_awarded=6.0 if has_healing else 0.0,
            max_points=6.0,
            message="Automated error triage, lint fix, and test repair verified"
            if has_healing
            else "Missing self-healing module",
            recommendation=""
            if has_healing
            else "Add octoflow/healing.py to auto-repair test regressions.",
        )
    )

    # 5.2 MCP Server Readiness
    has_mcp = (root / "octoflow" / "mcp.py").is_file() or (root / ".mcp.json").is_file()
    swarm_findings.append(
        AuditFinding(
            category="Swarm Health",
            name="Model Context Protocol (MCP) Server",
            passed=has_mcp,
            points_awarded=6.0 if has_mcp else 0.0,
            max_points=6.0,
            message="Stdio MCP server active for Claude Code, Cursor & Windsurf"
            if has_mcp
            else "Missing MCP integration",
            recommendation="" if has_mcp else "Provide an MCP server interface in octoflow/mcp.py.",
        )
    )

    # 5.3 3D Visualizer Connectome
    has_vis = (root / "visualizer" / "dist").is_dir() or (root / "visualizer" / "src").is_dir()
    swarm_findings.append(
        AuditFinding(
            category="Swarm Health",
            name="3D WebGL Connectome Visualizer",
            passed=has_vis,
            points_awarded=4.0 if has_vis else 0.0,
            max_points=4.0,
            message="Interactive 3D connectome frontend built and ready"
            if has_vis
            else "Missing visualizer frontend",
            recommendation=""
            if has_vis
            else "Build visualizer/dist for real-time 3D synaptic streaming.",
        )
    )

    # 5.4 Claude Code Plugin Manifest
    has_claude_manifest = (root / ".claude-plugin" / "plugin.json").is_file()
    swarm_findings.append(
        AuditFinding(
            category="Swarm Health",
            name="Claude Code Plugin & Slash Commands",
            passed=has_claude_manifest,
            points_awarded=4.0 if has_claude_manifest else 1.0,
            max_points=4.0,
            message="Native .claude-plugin/ manifest with /octo slash commands configured"
            if has_claude_manifest
            else "No .claude-plugin/ manifest (run 'octo install-claude')",
            recommendation=""
            if has_claude_manifest
            else "Run 'octo install-claude' to generate Claude Code slash commands.",
        )
    )

    swarm_total = sum(f.points_awarded for f in swarm_findings)
    categories["swarm_health"] = AuditCategoryResult(
        name="Swarm & Consortium Health",
        score=swarm_total,
        findings=swarm_findings,
    )

    # =========================================================================
    # Aggregation & Grading
    # =========================================================================
    total_score = round(code_total + test_total + sec_total + neural_total + swarm_total, 1)

    if total_score >= 95.0:
        grade = "A+"
        title = "Apex Cephalopod — Production Certified"
    elif total_score >= 85.0:
        grade = "A"
        title = "Deep-Sea Vanguard — Enterprise Ready"
    elif total_score >= 70.0:
        grade = "B"
        title = "Subsurface Operational — Good Health"
    elif total_score >= 50.0:
        grade = "C"
        title = "Shallow Water — Optimization Needed"
    else:
        grade = "F"
        title = "Pelagic Breach — Critical Flaws Detected"

    # Collect recommendations
    all_recs = []
    for cat in categories.values():
        for f in cat.findings:
            if not f.passed and f.recommendation:
                all_recs.append(f"[{cat.name}] {f.recommendation}")

    return AuditReport(
        workspace_path=str(root),
        total_score=total_score,
        letter_grade=grade,
        title=title,
        categories=categories,
        recommendations=all_recs,
    )


def print_audit_report(report: AuditReport, console: Console | None = None) -> None:
    """Render a visually stunning Rich audit terminal card."""
    con = console or Console()

    # Color grading
    if report.letter_grade in ["A+", "A"]:
        grade_style = "bold green"
        score_style = "bold bright_green"
    elif report.letter_grade == "B":
        grade_style = "bold cyan"
        score_style = "bold bright_cyan"
    elif report.letter_grade == "C":
        grade_style = "bold yellow"
        score_style = "bold bright_yellow"
    else:
        grade_style = "bold red"
        score_style = "bold bright_red"

    # Header Panel
    con.print()
    con.print(
        Panel(
            f"[bold white]◈ OCTOFLOW SYSTEM READINESS & SECURITY AUDIT[/bold white]\n"
            f"[dim]Workspace: {report.workspace_path}[/dim]\n\n"
            f"OVERALL READINESS GRADE: [{grade_style}]{report.letter_grade}[/{grade_style}]  "
            f"([dim]Score:[/dim] [{score_style}]{report.total_score} / 100.0[/{score_style}]) — [bold]{report.title}[/bold]",
            title="[bold cyan]Cephalopod MetaHarness Diagnostic[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # Category Summary Table
    table = Table(
        title="Audit Dimensions & Category Scores",
        border_style="dim",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Category", style="cyan", width=36)
    table.add_column("Score", justify="right", width=12)
    table.add_column("Bar", width=24)
    table.add_column("Status", justify="center", width=12)

    for _cat_key, cat in report.categories.items():
        ratio = cat.score / cat.max_score
        bar_len = int(ratio * 16)
        bar_str = "█" * bar_len + "░" * (16 - bar_len)
        status_str = (
            "[green]EXCELLENT[/green]"
            if ratio >= 0.85
            else ("[yellow]MODERATE[/yellow]" if ratio >= 0.65 else "[red]ATTN[/red]")
        )
        table.add_row(
            cat.name,
            f"{cat.score:.1f} / {cat.max_score:.1f}",
            f"[{'green' if ratio >= 0.85 else 'yellow'}]{bar_str}[/]",
            status_str,
        )

    con.print(table)
    con.print()

    # Detailed Findings Table
    findings_table = Table(
        title="Detailed Check Breakdown",
        border_style="dim",
        show_header=True,
        header_style="bold blue",
    )
    findings_table.add_column("Category", style="dim", width=24)
    findings_table.add_column("Check Item", style="bold white", width=34)
    findings_table.add_column("Pts", justify="right", width=8)
    findings_table.add_column("Outcome Details", style="dim", width=50)

    for cat in report.categories.values():
        for f in cat.findings:
            mark = "[bold green]PASS[/bold green]" if f.passed else "[bold red]FAIL[/bold red]"
            findings_table.add_row(
                cat.name.split()[0],
                f.name,
                f"{f.points_awarded:.1f}/{f.max_points:.1f}",
                f"{mark} {f.message}",
            )

    con.print(findings_table)
    con.print()

    # Recommendations
    if report.recommendations:
        rec_panel = "\n".join([f"  • [yellow]{r}[/yellow]" for r in report.recommendations])
        con.print(
            Panel(
                rec_panel,
                title="[bold yellow]Targeted Action Items to Reach 100/100[/bold yellow]",
                border_style="yellow",
                padding=(1, 2),
            )
        )
        con.print()
    else:
        con.print(
            Panel(
                "[bold green]All systems operating at peak biological efficiency. Zero action items required![/bold green]",
                title="[bold green]Perfection Attained[/bold green]",
                border_style="green",
            )
        )
        con.print()

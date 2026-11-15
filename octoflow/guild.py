"""Declarative 8-arm specialist guild schema, validator, and loader for OctoFlow (P8.2).

Provides:
- Strict Pydantic models (ArmSpec, GuildSpec) validating 8-arm cephalopod rosters.
- RFC 6901 JSON pointer formatted validation error paths.
- Search path precedence: project .octoflow/guilds/*.json -> ~/.octoflow/guilds/*.json -> built-ins.
- Untrusted content safety and global ToolPolicy clamping with warning logs.
- Conversion to and from runtime ArmRoleConfig rosters.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_core import InitErrorDetails, ValidationError

from octoflow.config import ArmRoleConfig
from octoflow.logging_config import get_logger

logger = get_logger("guild")

HEX_COLOR_REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")
MAX_PROMPT_LENGTH = 2000

# Canonical recognized tool names
KNOWN_TOOLS: set[str] = {
    "read_file",
    "write_file",
    "run_command",
    "list_dir",
    "mark_quiescent",
}

# Accepted tool aliases mapping to canonical tool names
TOOL_ALIASES: dict[str, str] = {
    "cat": "read_file",
    "view_file": "read_file",
    "open_file": "read_file",
    "read": "read_file",
    "run": "run_command",
    "shell": "run_command",
    "bash": "run_command",
    "execute": "run_command",
    "exec": "run_command",
}


def normalize_tool_name(tool: str) -> str:
    """Normalize a tool name or alias to its canonical system tool name."""
    clean = tool.strip().lower()
    return TOOL_ALIASES.get(clean, clean)


class ToolPolicy(BaseModel):
    """Global execution policy defining allowed and denied tools for arm cycles."""

    allowed_tools: set[str] = Field(
        default_factory=lambda: {
            "read_file",
            "write_file",
            "run_command",
            "list_dir",
            "mark_quiescent",
        }
    )
    denied_tools: set[str] = Field(default_factory=set)

    def is_allowed(self, tool_name: str) -> bool:
        """Check whether a tool name or alias is permitted by the policy."""
        raw = tool_name.strip().lower()
        norm = normalize_tool_name(raw)
        if raw in self.denied_tools or norm in self.denied_tools:
            return False
        return raw in self.allowed_tools or norm in self.allowed_tools


# Module-level global tool policy singleton
_GLOBAL_TOOL_POLICY: ToolPolicy = ToolPolicy()


def get_global_tool_policy() -> ToolPolicy:
    """Return the active global ToolPolicy singleton."""
    return _GLOBAL_TOOL_POLICY


def set_global_tool_policy(policy: ToolPolicy) -> None:
    """Set the active global ToolPolicy singleton."""
    global _GLOBAL_TOOL_POLICY
    _GLOBAL_TOOL_POLICY = policy


def clamp_arm_tools(
    requested_tools: list[str], arm_id: int, policy: ToolPolicy | None = None
) -> list[str]:
    """Intersect requested tools with policy; drop denied tools with a logged warning."""
    active_policy = policy or get_global_tool_policy()
    clamped: list[str] = []
    for tool in requested_tools:
        if active_policy.is_allowed(tool):
            canonical = normalize_tool_name(tool)
            if canonical not in clamped:
                clamped.append(canonical)
        else:
            logger.warning("Tool '%s' denied by global policy for arm %d; clamped.", tool, arm_id)
    return clamped


class ArmSpec(BaseModel):
    """Declarative specification for an individual cephalopod brachial arm ganglion."""

    id: int = Field(..., description="Arm index strictly between 0 and 7")
    role: str = Field(..., min_length=1, description="Arm role name / identifier")
    focus: str = Field(..., min_length=1, description="Specialized focus area / domain description")
    color: str = Field(..., description="Hex color string matching '^#[0-9a-fA-F]{6}$'")
    system_prompt: str = Field(
        default="",
        max_length=MAX_PROMPT_LENGTH,
        description="Arm-specific system prompt guidelines (max 2000 characters)",
    )
    tools: list[str] = Field(
        default_factory=lambda: ["read_file", "write_file", "run_command", "list_dir"],
        description="Permitted tools subset for this arm",
    )
    file_scope: list[str] = Field(
        default_factory=list,
        description="Workspace domain paths or file globs steered to this arm",
    )

    @field_validator("color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not isinstance(v, str) or not HEX_COLOR_REGEX.match(v):
            raise ValueError(
                f"Color must be a 6-digit hex string matching '^#[0-9a-fA-F]{{6}}$', got '{v}'"
            )
        return v.upper()

    @field_validator("system_prompt")
    @classmethod
    def validate_system_prompt_safety(cls, v: str) -> str:
        if "\x00" in v:
            raise ValueError("Null bytes are not permitted in system prompt")
        if len(v) > MAX_PROMPT_LENGTH:
            raise ValueError(
                f"System prompt length ({len(v)}) exceeds maximum allowed limit ({MAX_PROMPT_LENGTH} characters)"
            )
        return v


class GuildSpec(BaseModel):
    """Validated declarative specification for an 8-arm specialist guild."""

    name: str = Field(..., min_length=1, description="Unique guild identifier")
    description: str = Field(..., min_length=1, description="Guild description and purpose")
    arms: list[ArmSpec] = Field(..., description="Exactly 8 specialist arm configurations")

    @field_validator("name")
    @classmethod
    def validate_guild_name(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[a-z0-9_-]+$", clean):
            raise ValueError(f"Guild name must be alphanumeric with underscores/hyphens, got '{v}'")
        return clean

    @field_validator("arms")
    @classmethod
    def validate_arms(cls, arms: list[ArmSpec]) -> list[ArmSpec]:
        errors: list[InitErrorDetails] = []

        if len(arms) != 8:
            errors.append(
                {
                    "type": "value_error",
                    "loc": ("arms",),
                    "input": len(arms),
                    "ctx": {
                        "error": ValueError(f"Guild must define exactly 8 arms, found {len(arms)}")
                    },
                }
            )

        seen_ids: dict[int, int] = {}
        for idx, arm in enumerate(arms):
            if arm.id < 0 or arm.id > 7:
                errors.append(
                    {
                        "type": "value_error",
                        "loc": ("arms", idx, "id"),
                        "input": arm.id,
                        "ctx": {
                            "error": ValueError(f"Arm ID must be between 0 and 7, got {arm.id}")
                        },
                    }
                )
            elif arm.id in seen_ids:
                errors.append(
                    {
                        "type": "value_error",
                        "loc": ("arms", idx, "id"),
                        "input": arm.id,
                        "ctx": {
                            "error": ValueError(
                                f"Duplicate arm ID {arm.id} (already defined at /arms/{seen_ids[arm.id]}/id)"
                            )
                        },
                    }
                )
            else:
                seen_ids[arm.id] = idx

            # Validate tools against known tools / aliases
            for tool_idx, t in enumerate(arm.tools):
                norm = normalize_tool_name(t)
                if norm not in KNOWN_TOOLS:
                    errors.append(
                        {
                            "type": "value_error",
                            "loc": ("arms", idx, "tools", tool_idx),
                            "input": t,
                            "ctx": {
                                "error": ValueError(
                                    f"Unknown tool '{t}'. Allowed tools: {sorted(KNOWN_TOOLS)}"
                                )
                            },
                        }
                    )

        if errors:
            raise ValidationError.from_exception_data("GuildSpec", errors)

        return sorted(arms, key=lambda a: a.id)

    def to_arm_roster(self, tool_policy: ToolPolicy | None = None) -> list[ArmRoleConfig]:
        """Convert GuildSpec arms into runtime ArmRoleConfig roster objects."""
        roster: list[ArmRoleConfig] = []
        for arm in sorted(self.arms, key=lambda a: a.id):
            clamped = clamp_arm_tools(arm.tools, arm.id, policy=tool_policy)
            roster.append(
                ArmRoleConfig(
                    arm_id=arm.id,
                    name=arm.role,
                    title=arm.focus if len(arm.focus) <= 30 else arm.role.replace("_", " ").title(),
                    description=arm.focus,
                    workspace_domain=list(arm.file_scope),
                    initial_threshold=0.50,
                    system_prompt=arm.system_prompt,
                    icon="◈",
                    model_tier="balanced",
                    color_hex=arm.color,
                    tools=clamped,
                )
            )
        return roster

    def get_palette(self) -> list[str]:
        """Return the 8 hex colors ordered by arm ID."""
        return [arm.color for arm in sorted(self.arms, key=lambda a: a.id)]

    def get_arm(self, arm_id: int) -> ArmSpec:
        """Retrieve ArmSpec by ID."""
        for arm in self.arms:
            if arm.id == arm_id:
                return arm
        raise KeyError(f"Arm {arm_id} not found in guild '{self.name}'")


def format_validation_errors(exc: ValidationError) -> list[str]:
    """Convert Pydantic validation errors into RFC 6901 JSON pointer error strings."""
    formatted: list[str] = []
    for err in exc.errors():
        loc = "/" + "/".join(str(p) for p in err["loc"])
        msg = err["msg"]
        # Strip internal Pydantic prefixes if present for cleaner output
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        formatted.append(f"{loc}: {msg}")
    return formatted


# ==============================================================================
# Built-In Guild Definitions (software_dev, aiml_research, fullstack_ai)
# ==============================================================================

BUILTIN_GUILD_SPECS: dict[str, GuildSpec] = {
    "software_dev": GuildSpec(
        name="software_dev",
        description="Full-Stack Software Engineering Guild (Arch, DB, API, UI, State, QA, Sec, DevOps)",
        arms=[
            ArmSpec(
                id=0,
                role="architect",
                focus="System specifications, directory topology, interface contracts, and module boundaries.",
                color="#00F0FF",
                file_scope=["specs/", "docs/", "architecture/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=1,
                role="database",
                focus="Data persistence models, migrations, ORM schemas, and database connectors.",
                color="#A855F7",
                file_scope=["models/", "db/", "migrations/", "schemas/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=2,
                role="backend",
                focus="REST/WebSocket endpoints, business logic services, routing, and controller handlers.",
                color="#3B82F6",
                file_scope=["backend/", "api/", "services/", "controllers/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=3,
                role="frontend",
                focus="User interface views, React/Vue components, package.json scaffolding, styling, layout, and visual presentation.",
                color="#EC4899",
                file_scope=[
                    "frontend/",
                    "frontend/package.json",
                    "frontend/index.html",
                    "frontend/vite.config.js",
                    "frontend/src/components/",
                    "frontend/src/views/",
                    "frontend/styles/",
                ],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=4,
                role="state_client",
                focus="Client reactive state, store management, custom hooks, and client-server synchronization.",
                color="#10B981",
                file_scope=["frontend/src/state/", "frontend/src/hooks/", "frontend/src/store/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=5,
                role="qa_tester",
                focus="Unit tests, integration suites, edge-case coverage, and load/stress test verification.",
                color="#EF4444",
                file_scope=["tests/", "cypress/", "e2e/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=6,
                role="security_audit",
                focus="Dependency vulnerability audits, input sanitization, authentication validation, and profiling.",
                color="#F59E0B",
                file_scope=["security/", "audit/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=7,
                role="devops_docs",
                focus="Containerization, Dockerfile, docker-compose, CI/CD pipelines, and project README.",
                color="#EAB308",
                file_scope=["deploy/", ".github/", "Dockerfile", "docker-compose.yml", "README.md"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
        ],
    ),
    "aiml_research": GuildSpec(
        name="aiml_research",
        description="AI/ML Research & Model Training Guild (ETL, Architect, Training, Eval, Tune, ONNX, FastServe, Docs)",
        arms=[
            ArmSpec(
                id=0,
                role="data_engineer",
                focus="Dataset ETL, feature scaling, PyTorch Dataset & DataLoader construction, synthetic data fallbacks, and data splits.",
                color="#00F0FF",
                file_scope=["data/", "datasets/", "etl/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=1,
                role="model_architect",
                focus="PyTorch neural architecture definition, custom layers, forward passes, and weight initialization.",
                color="#A855F7",
                file_scope=["models/", "architecture/", "layers/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=2,
                role="training_loop",
                focus="PyTorch training loop with CUDA/MPS/CPU autodetection, loss functions, optimizer setup, learning rate schedulers, and AMP.",
                color="#3B82F6",
                file_scope=["train/", "training/", "losses/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=3,
                role="eval_benchmark",
                focus="Validation metrics, test evaluation, ablation experiments, confusion matrices, and ROC curves.",
                color="#EC4899",
                file_scope=["eval/", "benchmarks/", "metrics/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=4,
                role="hpo_tuner",
                focus="Hyperparameter optimization, learning rate search, batch size tuning, and regularization.",
                color="#10B981",
                file_scope=["hpo/", "tuning/", "configs/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=5,
                role="quant_export",
                focus="INT8/FP16 post-training quantization, TorchScript tracing, and ONNX Runtime graph export.",
                color="#EF4444",
                file_scope=["export/", "onnx/", "quantized/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=6,
                role="inference_server",
                focus="FastAPI model inference endpoints, Triton serving wrappers, and latency benchmarking.",
                color="#F59E0B",
                file_scope=["serve/", "inference/", "api/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=7,
                role="mlops_governance",
                focus="Model cards, reproducibility tracking, environment lockfiles, and experiment reports.",
                color="#EAB308",
                file_scope=["mlops/", "reports/", "model_card.md", "README.md"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
        ],
    ),
    "fullstack_ai": GuildSpec(
        name="fullstack_ai",
        description="Fullstack AI Product Guild (Pipeline, PyTorch, FastAPI, UI Views, ONNX, E2E QA, Sec, Docker)",
        arms=[
            ArmSpec(
                id=0,
                role="data_pipeline",
                focus="Dataset pipeline, preprocessing, feature transformations, and input schema validation.",
                color="#00F0FF",
                file_scope=["data/", "datasets/", "preprocessing/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=1,
                role="model_training",
                focus="PyTorch neural model definition, training loop, loss computation, and checkpointing.",
                color="#A855F7",
                file_scope=["models/", "train/", "checkpoints/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=2,
                role="backend_serving",
                focus="FastAPI backend serving ONNX / PyTorch models, REST endpoints, and WebSocket streaming.",
                color="#3B82F6",
                file_scope=["backend/", "api/", "serve/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=3,
                role="frontend_ui",
                focus="Interactive web dashboard, package.json build manifests, canvas/drag-and-drop inference upload, and result visualization.",
                color="#EC4899",
                file_scope=[
                    "frontend/",
                    "frontend/package.json",
                    "frontend/index.html",
                    "frontend/vite.config.js",
                    "frontend/src/components/",
                    "frontend/src/views/",
                ],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=4,
                role="quant_opt",
                focus="ONNX export, FP16/INT8 inference optimization, latency profiling, and batching.",
                color="#10B981",
                file_scope=["export/", "opt/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=5,
                role="integration_qa",
                focus="End-to-end integration tests, tensor-to-API schema validation, and endpoint stress testing.",
                color="#EF4444",
                file_scope=["tests/", "e2e/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=6,
                role="security_perf",
                focus="Input sanitization against adversarial inputs, memory leak inspection, and security audit.",
                color="#F59E0B",
                file_scope=["security/"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
            ArmSpec(
                id=7,
                role="devops_deploy",
                focus="Docker container with CUDA/GPU support, docker-compose, and full documentation.",
                color="#EAB308",
                file_scope=["deploy/", "Dockerfile", "docker-compose.yml", "README.md"],
                tools=["read_file", "write_file", "run_command", "list_dir"],
            ),
        ],
    ),
}


# ==============================================================================
# Guild Discovery and Search Path Loader
# ==============================================================================


def get_project_guilds_dir(project_dir: Path | None = None) -> Path:
    """Return project .octoflow/guilds directory."""
    base = project_dir or Path.cwd()
    return base / ".octoflow" / "guilds"


def get_user_guilds_dir() -> Path:
    """Return user ~/.octoflow/guilds directory."""
    return Path.home() / ".octoflow" / "guilds"


def get_package_guilds_dir() -> Path:
    """Return packaged first-party octoflow/guilds directory."""
    return Path(__file__).resolve().parent / "guilds"


def _is_safe_guild_name(name: str) -> bool:
    """Verify that guild name contains no path traversal components."""
    if not name or ".." in name or "/" in name or "\\" in name:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name.strip()))


def validate_guild_file(path: Path | str) -> tuple[bool, list[str], GuildSpec | None]:
    """Validate a guild JSON file; returns (is_valid, error_list, guild_spec)."""
    p = Path(path).expanduser()
    if not p.exists():
        return False, [f"File not found: '{p}'"], None
    if not p.is_file():
        return False, [f"Path is not a regular file: '{p}'"], None

    try:
        raw_text = p.read_text(encoding="utf-8")
    except Exception as e:
        return False, [f"Failed to read file: {e}"], None

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        return False, [f"/ (root): Malformed JSON: {e}"], None

    if not isinstance(data, dict):
        return False, ["/ (root): Root of guild JSON must be an object/dict"], None

    # Handle legacy 'roster' field wrapping if present
    if "arms" not in data and "roster" in data and isinstance(data["roster"], list):
        data["arms"] = [
            {
                "id": r.get("arm_id", idx),
                "role": r.get("name", f"arm_{idx}"),
                "focus": r.get("description", r.get("title", "")),
                "color": r.get("color_hex", "#00F0FF"),
                "system_prompt": r.get("system_prompt", ""),
                "tools": r.get("tools", ["read_file", "write_file", "run_command", "list_dir"]),
                "file_scope": r.get("workspace_domain", []),
            }
            for idx, r in enumerate(data["roster"])
        ]

    try:
        spec = GuildSpec.model_validate(data)
        return True, [], spec
    except ValidationError as exc:
        return False, format_validation_errors(exc), None


def load_guild_file(path: Path | str) -> GuildSpec:
    """Load and validate a guild JSON file; raises ValueError on failure."""
    is_valid, errors, spec = validate_guild_file(path)
    if not is_valid or spec is None:
        raise ValueError(f"Invalid guild file '{path}':\n" + "\n".join(f"  {e}" for e in errors))
    return spec


def load_guild(name: str, project_dir: Path | None = None) -> GuildSpec:
    """Load a guild by name using search precedence: Project -> User -> Built-in.

    Enforces path traversal safety (rejects '..' or absolute paths).
    """
    clean = name.strip().lower()
    if not _is_safe_guild_name(clean):
        raise ValueError(
            f"Invalid guild name '{name}': guild names must be alphanumeric and cannot contain path traversal."
        )

    # 1. Project directory precedence: <project>/.octoflow/guilds/<name>.json
    proj_dir = get_project_guilds_dir(project_dir)
    proj_file = proj_dir / f"{clean}.json"
    if proj_file.is_file():
        return load_guild_file(proj_file)

    # 2. User directory precedence: ~/.octoflow/guilds/<name>.json
    user_dir = get_user_guilds_dir()
    user_file = user_dir / f"{clean}.json"
    if user_file.is_file():
        return load_guild_file(user_file)

    # 3. Built-in hardcoded guilds
    clean_aliases = {
        "software-dev": "software_dev",
        "aiml-research": "aiml_research",
        "fullstack-ai": "fullstack_ai",
        "ml": "aiml_research",
        "devops": "cloud_devops",
        "security": "cybersec_ops",
        "secops": "cybersec_ops",
        "embedded": "systems_embedded",
        "systems": "systems_embedded",
        "qa": "qa_resilience",
        "testing": "qa_resilience",
        "web": "web_fullstack",
        "fullstack": "web_fullstack",
        "mobile": "mobile_apps",
        "migration": "enterprise_migration",
        "ds": "data_science",
    }
    canonical = clean_aliases.get(clean, clean)
    if canonical in BUILTIN_GUILD_SPECS:
        return BUILTIN_GUILD_SPECS[canonical]

    # 4. Packaged first-party guilds in octoflow/guilds/<name>.json
    pkg_dir = get_package_guilds_dir()
    pkg_file = pkg_dir / f"{canonical}.json"
    if pkg_file.is_file():
        return load_guild_file(pkg_file)

    all_builtins = sorted(
        set(BUILTIN_GUILD_SPECS.keys())
        | {f.stem for f in pkg_dir.glob("*.json") if f.is_file()}
    )
    raise FileNotFoundError(
        f"Guild '{name}' not found. Searched:\n"
        f"  1. Project: {proj_file}\n"
        f"  2. User:    {user_file}\n"
        f"  3. Package: {pkg_file}\n"
        f"  4. Built-ins: {', '.join(all_builtins)}"
    )


def list_guilds(project_dir: Path | None = None) -> list[dict[str, Any]]:
    """List all available guilds across project, user, package, and built-ins with precedence."""
    results: dict[str, dict[str, Any]] = {}

    # 1. Built-in hardcoded guilds (lowest precedence)
    for name, spec in BUILTIN_GUILD_SPECS.items():
        results[name] = {
            "name": name,
            "description": spec.description,
            "source": "builtin",
            "path": None,
            "arms_count": 8,
        }

    # 2. Packaged first-party guilds in octoflow/guilds/*.json
    pkg_dir = get_package_guilds_dir()
    if pkg_dir.is_dir():
        for f in sorted(pkg_dir.glob("*.json")):
            is_valid, _, pkg_spec = validate_guild_file(f)
            if is_valid and pkg_spec:
                results[pkg_spec.name] = {
                    "name": pkg_spec.name,
                    "description": pkg_spec.description,
                    "source": "builtin",
                    "path": str(f),
                    "arms_count": len(pkg_spec.arms),
                }

    # 3. User ~/.octoflow/guilds/*.json
    user_dir = get_user_guilds_dir()
    if user_dir.is_dir():
        for f in sorted(user_dir.glob("*.json")):
            is_valid, _, user_spec = validate_guild_file(f)
            if is_valid and user_spec:
                results[user_spec.name] = {
                    "name": user_spec.name,
                    "description": user_spec.description,
                    "source": "user",
                    "path": str(f),
                    "arms_count": len(user_spec.arms),
                }

    # 4. Project .octoflow/guilds/*.json (highest precedence)
    proj_dir = get_project_guilds_dir(project_dir)
    if proj_dir.is_dir():
        for f in sorted(proj_dir.glob("*.json")):
            is_valid, _, proj_spec = validate_guild_file(f)
            if is_valid and proj_spec:
                results[proj_spec.name] = {
                    "name": proj_spec.name,
                    "description": proj_spec.description,
                    "source": "project",
                    "path": str(f),
                    "arms_count": len(proj_spec.arms),
                }

    return sorted(results.values(), key=lambda g: g["name"])


def save_guild(spec: GuildSpec, target_dir: Path | None = None) -> Path:
    """Save a GuildSpec to a JSON file (in target_dir or ~/.octoflow/guilds)."""
    dest_dir = target_dir or get_user_guilds_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_file = dest_dir / f"{spec.name}.json"
    payload = spec.model_dump()
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_file

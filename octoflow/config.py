"""OctoFlow Swarm Configuration & Morphology Presets.

Defines the 8-arm cephalopod agent roles across Software Development,
AI/ML Research, and Hybrid Full-Stack AI project domains.
"""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from octoflow.budget import RunBudget


class SwarmMorphology(str, Enum):
    """Cephalopod swarm operational morphology presets."""

    SOFTWARE_DEV = "software_dev"
    AIML_RESEARCH = "aiml_research"
    FULLSTACK_AI = "fullstack_ai"
    CUSTOM = "custom"


class ArmRoleConfig(BaseModel):
    """Configuration for an individual autonomous arm agent."""

    arm_id: int
    name: str
    title: str
    description: str
    workspace_domain: list[str] = Field(default_factory=list)
    initial_threshold: float = 0.50
    system_prompt: str = ""
    icon: str = "🐙"
    model_tier: str = "balanced"  # "frontier", "balanced", or "fast"


# Default 8-Arm Roster for Full-Stack Software Engineering
SOFTWARE_DEV_ROSTER: list[ArmRoleConfig] = [
    ArmRoleConfig(
        arm_id=0,
        name="architect",
        title="System Architect",
        description="System specifications, directory topology, interface contracts, and module boundaries.",
        workspace_domain=["specs/", "docs/", "architecture/"],
        initial_threshold=0.45,
        icon="📐",
        model_tier="frontier",
    ),
    ArmRoleConfig(
        arm_id=1,
        name="database",
        title="Database & Schemas",
        description="Data persistence models, migrations, ORM schemas, and database connectors.",
        workspace_domain=["models/", "db/", "migrations/", "schemas/"],
        initial_threshold=0.50,
        icon="🗄️",
    ),
    ArmRoleConfig(
        arm_id=2,
        name="backend",
        title="Backend API",
        description="REST/WebSocket endpoints, business logic services, routing, and controller handlers.",
        workspace_domain=["backend/", "api/", "services/", "controllers/"],
        initial_threshold=0.50,
        icon="⚡",
    ),
    ArmRoleConfig(
        arm_id=3,
        name="frontend",
        title="Frontend UI",
        description="User interface views, React/Vue components, package.json scaffolding, styling, layout, and visual presentation.",
        workspace_domain=[
            "frontend/",
            "frontend/package.json",
            "frontend/index.html",
            "frontend/vite.config.js",
            "frontend/src/components/",
            "frontend/src/views/",
            "frontend/styles/",
        ],
        initial_threshold=0.55,
        icon="🎨",
    ),
    ArmRoleConfig(
        arm_id=4,
        name="state_client",
        title="State & Hooks",
        description="Client reactive state, store management, custom hooks, and client-server synchronization.",
        workspace_domain=["frontend/src/state/", "frontend/src/hooks/", "frontend/src/store/"],
        initial_threshold=0.50,
        icon="🔄",
    ),
    ArmRoleConfig(
        arm_id=5,
        name="qa_tester",
        title="QA & Testing",
        description="Unit tests, integration suites, edge-case coverage, and load/stress test verification.",
        workspace_domain=["tests/", "cypress/", "e2e/"],
        initial_threshold=0.40,  # Lower threshold for high vigilance
        icon="🧪",
        model_tier="frontier",
    ),
    ArmRoleConfig(
        arm_id=6,
        name="security_audit",
        title="Security & Profiling",
        description="Dependency vulnerability audits, input sanitization, authentication validation, and profiling.",
        workspace_domain=["security/", "audit/"],
        initial_threshold=0.40,
        icon="🛡️",
        model_tier="frontier",
    ),
    ArmRoleConfig(
        arm_id=7,
        name="devops_docs",
        title="DevOps & Docs",
        description="Containerization, Dockerfile, docker-compose, CI/CD pipelines, and project README.",
        workspace_domain=["deploy/", ".github/", "Dockerfile", "docker-compose.yml", "README.md"],
        initial_threshold=0.50,
        icon="📦",
        model_tier="fast",
    ),
]

# Default 8-Arm Roster for AI/ML Research & Model Training
AIML_RESEARCH_ROSTER: list[ArmRoleConfig] = [
    ArmRoleConfig(
        arm_id=0,
        name="data_engineer",
        title="Data Engineer",
        description="Dataset ETL, feature scaling, PyTorch Dataset & DataLoader construction, synthetic data fallbacks, and data splits.",
        workspace_domain=["data/", "datasets/", "etl/"],
        initial_threshold=0.50,
        icon="📊",
    ),
    ArmRoleConfig(
        arm_id=1,
        name="model_architect",
        title="Model Architect",
        description="PyTorch neural architecture definition, custom layers, forward passes, and weight initialization.",
        workspace_domain=["models/", "architecture/", "layers/"],
        initial_threshold=0.45,
        icon="🧠",
    ),
    ArmRoleConfig(
        arm_id=2,
        name="training_loop",
        title="Training & Loss Engineer",
        description="PyTorch training loop with CUDA/MPS/CPU autodetection, loss functions, optimizer setup, learning rate schedulers, and AMP.",
        workspace_domain=["train/", "training/", "losses/"],
        initial_threshold=0.40,
        icon="🔥",
    ),
    ArmRoleConfig(
        arm_id=3,
        name="eval_benchmark",
        title="Eval & Benchmark",
        description="Validation metrics, test evaluation, ablation experiments, confusion matrices, and ROC curves.",
        workspace_domain=["eval/", "benchmarks/", "metrics/"],
        initial_threshold=0.45,
        icon="📈",
    ),
    ArmRoleConfig(
        arm_id=4,
        name="hpo_tuner",
        title="HPO / Tuner",
        description="Hyperparameter optimization, learning rate search, batch size tuning, and regularization.",
        workspace_domain=["hpo/", "tuning/", "configs/"],
        initial_threshold=0.50,
        icon="🎛️",
    ),
    ArmRoleConfig(
        arm_id=5,
        name="quant_export",
        title="Quantization & ONNX",
        description="INT8/FP16 post-training quantization, TorchScript tracing, and ONNX Runtime graph export.",
        workspace_domain=["export/", "onnx/", "quantized/"],
        initial_threshold=0.45,
        icon="⚡",
    ),
    ArmRoleConfig(
        arm_id=6,
        name="inference_server",
        title="Inference Serving",
        description="FastAPI model inference endpoints, Triton serving wrappers, and latency benchmarking.",
        workspace_domain=["serve/", "inference/", "api/"],
        initial_threshold=0.50,
        icon="🚀",
    ),
    ArmRoleConfig(
        arm_id=7,
        name="mlops_governance",
        title="MLOps & Governance",
        description="Model cards, reproducibility tracking, environment lockfiles, and experiment reports.",
        workspace_domain=["mlops/", "reports/", "model_card.md", "README.md"],
        initial_threshold=0.50,
        icon="📋",
    ),
]

# Default 8-Arm Roster for Hybrid Full-Stack AI Products
FULLSTACK_AI_ROSTER: list[ArmRoleConfig] = [
    ArmRoleConfig(
        arm_id=0,
        name="data_pipeline",
        title="Data & Prep",
        description="Dataset pipeline, preprocessing, feature transformations, and input schema validation.",
        workspace_domain=["data/", "datasets/", "preprocessing/"],
        initial_threshold=0.50,
        icon="📊",
    ),
    ArmRoleConfig(
        arm_id=1,
        name="model_training",
        title="Model & Train",
        description="PyTorch neural model definition, training loop, loss computation, and checkpointing.",
        workspace_domain=["models/", "train/", "checkpoints/"],
        initial_threshold=0.45,
        icon="🧠",
    ),
    ArmRoleConfig(
        arm_id=2,
        name="backend_serving",
        title="Backend & Serve",
        description="FastAPI backend serving ONNX / PyTorch models, REST endpoints, and WebSocket streaming.",
        workspace_domain=["backend/", "api/", "serve/"],
        initial_threshold=0.50,
        icon="⚡",
    ),
    ArmRoleConfig(
        arm_id=3,
        name="frontend_ui",
        title="Frontend UI",
        description="Interactive web dashboard, package.json build manifests, canvas/drag-and-drop inference upload, and result visualization.",
        workspace_domain=[
            "frontend/",
            "frontend/package.json",
            "frontend/index.html",
            "frontend/vite.config.js",
            "frontend/src/components/",
            "frontend/src/views/",
        ],
        initial_threshold=0.55,
        icon="🎨",
    ),
    ArmRoleConfig(
        arm_id=4,
        name="quant_opt",
        title="Quantization & HPO",
        description="ONNX export, FP16/INT8 inference optimization, latency profiling, and batching.",
        workspace_domain=["export/", "opt/"],
        initial_threshold=0.50,
        icon="⚙️",
    ),
    ArmRoleConfig(
        arm_id=5,
        name="integration_qa",
        title="Integration QA",
        description="End-to-end integration tests, tensor-to-API schema validation, and endpoint stress testing.",
        workspace_domain=["tests/", "e2e/"],
        initial_threshold=0.40,
        icon="🧪",
    ),
    ArmRoleConfig(
        arm_id=6,
        name="security_perf",
        title="Security & Profiling",
        description="Input sanitization against adversarial inputs, memory leak inspection, and security audit.",
        workspace_domain=["security/"],
        initial_threshold=0.40,
        icon="🛡️",
    ),
    ArmRoleConfig(
        arm_id=7,
        name="devops_deploy",
        title="DevOps & Deploy",
        description="Docker container with CUDA/GPU support, docker-compose, and full documentation.",
        workspace_domain=["deploy/", "Dockerfile", "docker-compose.yml", "README.md"],
        initial_threshold=0.50,
        icon="📦",
    ),
]


class LLMConfigEntry(BaseModel):
    """Configuration for an individual model in the failover cascade pool."""

    id: str
    provider: str  # "gemini", "grok", "deepseek", "openai", "anthropic", "ollama", "custom"
    name: str  # e.g. "Google Gemini 2.0 Flash"
    base_url: str | None = None
    api_key: str | None = None
    model: str = "default"
    enabled: bool = True
    priority: int = 1


def get_octoflow_dir() -> Path:
    """Return ~/.octoflow path, ensuring directory permissions are 0700."""
    cfg_dir = Path.home() / ".octoflow"
    if not cfg_dir.exists():
        cfg_dir.mkdir(parents=True, exist_ok=True)
        try:
            cfg_dir.chmod(0o700)
        except OSError:
            pass
    else:
        harden_permissions_if_looser(cfg_dir, 0o700, "directory")
    return cfg_dir


def harden_permissions_if_looser(path: Path, expected_mode: int, kind: str = "file") -> bool:
    """Fix permissions if looser than expected_mode, printing a one-line notice."""
    if not path.exists():
        return False
    try:
        current_mode = path.stat().st_mode & 0o777
        # Looser if any bits outside expected_mode are set (e.g. group/other read/write)
        if (current_mode & ~expected_mode) != 0:
            path.chmod(expected_mode)
            print(
                f"Notice: Hardened permissions on {path} to {oct(expected_mode)} (was {oct(current_mode)})."
            )
            return True
    except OSError:
        pass
    return False


def load_secure_config(cfg_path: Path | None = None) -> dict:
    """Load configuration from ~/.octoflow/config.json with permission hardening."""
    from octoflow.settings import get_default_config_path, load_settings

    p = cfg_path or get_default_config_path()
    if not p.exists():
        return {}
    try:
        settings = load_settings(cfg_path=p)
        data = settings.to_dict(mask_secrets=False)
        # Flatten for legacy callers expecting top-level fields
        legacy_compat = dict(data.get("extras", {}))
        legacy_compat.update(
            {
                "schema_version": settings.schema_version,
                "default_provider": settings.defaults.default_provider,
                "default_model": settings.defaults.default_model,
                "default_scale": settings.defaults.default_scale,
                "default_theme": settings.ui.theme,
                "theme": settings.ui.theme,
                "host": settings.server.host,
                "ws_port": settings.server.ws_port,
                "telemetry_port": settings.server.ws_port,
                "http_port": settings.server.http_port,
                "webhook_url": settings.webhook_url,
                "llm_pool": settings.llm_pool,
            }
        )
        for p_name, p_val in settings.providers.items():
            if p_val.api_key:
                raw_k = p_val.api_key
                legacy_compat[f"{p_name}_api_key"] = (
                    raw_k.get_secret_value() if hasattr(raw_k, "get_secret_value") else str(raw_k)
                )
            if p_name == "ollama" and p_val.base_url:
                legacy_compat["ollama_base_url"] = p_val.base_url
        legacy_compat.update(data)
        return legacy_compat
    except Exception:
        return {}


def save_secure_config(data: dict, cfg_path: Path | None = None) -> Path:
    """Write configuration to ~/.octoflow/config.json with mode 0600."""
    from octoflow.settings import (
        Settings,
        atomic_write_config,
        get_default_config_path,
        transform_legacy_config_data,
    )

    p = cfg_path or get_default_config_path()
    try:
        if data.get("schema_version") == 1 and "defaults" in data:
            settings = Settings.model_validate(data)
        else:
            transformed = transform_legacy_config_data(data)
            settings = Settings.model_validate(transformed)
        serialized = json.dumps(settings.to_dict(mask_secrets=False), indent=2)
    except Exception:
        serialized = json.dumps(data, indent=2)

    atomic_write_config(p, serialized)
    return p


def mask_credential(key: str | None) -> str:
    """Mask credentials for display, showing first 3 characters followed by ****."""
    if not key:
        return ""
    key_str = str(key).strip()
    if not key_str:
        return ""
    return key_str[:3] + "****"


class OctoFlowConfig(BaseModel):
    """Global configuration for an OctoFlow Swarm execution."""

    # Swarm Morphology & Custom Guilds
    morphology: SwarmMorphology = SwarmMorphology.SOFTWARE_DEV
    guild: str | None = None  # Custom community guild name in ~/.octoflow/guilds/
    custom_roster: list[ArmRoleConfig] | None = None

    # LLM Settings
    model_provider: str = (
        "mock"  # "mock", "anthropic", "openai", "gemini", "grok", "deepseek", "ollama"
    )
    model_name: str = "claude-3-5-sonnet-20241022"
    api_key: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    grok_api_key: str | None = None
    deepseek_api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.2

    # Dynamic Multi-LLM Cascade & Token Failover Pool
    llm_pool: list[LLMConfigEntry] = Field(default_factory=list)

    # Cross-Provider Heterogeneous Routing
    frontier_provider: str | None = None  # e.g. "anthropic"
    fast_provider: str | None = None  # e.g. "openai" or "ollama"
    frontier_model: str | None = None  # e.g. "claude-3-7-sonnet-20250219" or "o3-mini"
    fast_model: str | None = (
        None  # e.g. "gpt-4o-mini" or "claude-3-5-haiku-20241022" or "qwen2.5-coder:7b"
    )

    # Provider Failover & High Availability
    enable_failover: bool = False
    fallback_providers: list[str] = Field(default_factory=lambda: ["openai", "ollama", "mock"])

    # Webhook Alerts (Slack / Discord / CI)
    webhook_url: str | None = None

    # Workspace & Execution Settings
    workspace_dir: str = "."
    dry_run: bool = False
    max_budget_dollars: float = 5.00
    budget: RunBudget = Field(default_factory=RunBudget)
    max_steps_per_arm: int = 15
    surprise_threshold: float = 0.50
    gate_mode: str = "gated"  # "gated" or "always_escalate"
    allow_mock: bool = False
    is_bench: bool = False
    auto_git_checkpoint: bool = True
    sandbox_mode: str = "local"  # "local" or "docker"
    docker_image: str = "python:3.12-slim"

    # Telemetry & Visualizer Settings
    enable_3d_telemetry: bool = True
    telemetry_port: int = 8088

    # Privacy & Egress Hardening
    privacy_redact_outbound: bool = True

    # Biological Neural Core Settings
    neural_checkpoint_path: str | None = None
    obs_dim: int = 16
    action_dim: int = 8
    message_dim: int = 32

    def model_post_init(self, __context: Any) -> None:
        """Auto-populate API keys and defaults from ENV > KEYRING > CONFIG."""
        from octoflow.keyring_store import resolve_api_key

        user_cfg = load_secure_config() or {}
        try:
            env_redact = os.getenv("OCTOFLOW_REDACT_OUTBOUND")
            if env_redact is not None:
                self.privacy_redact_outbound = env_redact.lower() not in ("0", "false", "no", "off")
            elif user_cfg and "privacy" in user_cfg and isinstance(user_cfg["privacy"], dict):
                if "redact_outbound" in user_cfg["privacy"]:
                    self.privacy_redact_outbound = bool(user_cfg["privacy"]["redact_outbound"])
            elif user_cfg and "privacy_redact_outbound" in user_cfg:
                self.privacy_redact_outbound = bool(user_cfg["privacy_redact_outbound"])

            if not self.anthropic_api_key:
                self.anthropic_api_key = resolve_api_key("anthropic", user_cfg)[0]
            if not self.openai_api_key:
                self.openai_api_key = resolve_api_key("openai", user_cfg)[0]
            if not self.gemini_api_key:
                self.gemini_api_key = resolve_api_key("gemini", user_cfg)[0]
            if not self.grok_api_key:
                self.grok_api_key = resolve_api_key("grok", user_cfg)[0]
            if not self.deepseek_api_key:
                self.deepseek_api_key = resolve_api_key("deepseek", user_cfg)[0]

            if not self.frontier_provider:
                self.frontier_provider = user_cfg.get("frontier_provider")
            if not self.fast_provider:
                self.fast_provider = user_cfg.get("fast_provider")
            if not self.frontier_model:
                self.frontier_model = user_cfg.get("frontier_model")
            if not self.fast_model:
                self.fast_model = user_cfg.get("fast_model")

            if (
                not self.llm_pool
                and "llm_pool" in user_cfg
                and isinstance(user_cfg["llm_pool"], list)
            ):
                for entry_data in user_cfg["llm_pool"]:
                    try:
                        self.llm_pool.append(LLMConfigEntry(**entry_data))
                    except Exception:
                        pass

            if not self.api_key:
                if self.model_provider == "anthropic":
                    self.api_key = self.anthropic_api_key
                elif self.model_provider == "openai":
                    self.api_key = self.openai_api_key
                elif self.model_provider in ["gemini", "google"]:
                    self.api_key = self.gemini_api_key
                elif self.model_provider in ["grok", "xai"]:
                    self.api_key = self.grok_api_key
                elif self.model_provider == "deepseek":
                    self.api_key = self.deepseek_api_key

            if not self.base_url and self.model_provider == "ollama":
                self.base_url = user_cfg.get("ollama_base_url") or "http://localhost:11434"
            if not self.webhook_url:
                self.webhook_url = (
                    user_cfg.get("webhook_url")
                    or os.getenv("OCTOFLOW_WEBHOOK_URL")
                    or os.getenv("SLACK_WEBHOOK_URL")
                    or os.getenv("DISCORD_WEBHOOK_URL")
                )
        except Exception:
            pass

    def get_roster(self) -> list[ArmRoleConfig]:
        """Retrieve the 8-arm configuration for current morphology or custom community guild."""
        if self.guild:
            custom = load_custom_guild(self.guild)
            if custom:
                return custom
        if self.morphology == SwarmMorphology.SOFTWARE_DEV:
            return SOFTWARE_DEV_ROSTER
        elif self.morphology == SwarmMorphology.AIML_RESEARCH:
            return AIML_RESEARCH_ROSTER
        elif self.morphology == SwarmMorphology.FULLSTACK_AI:
            return FULLSTACK_AI_ROSTER
        elif self.morphology == SwarmMorphology.CUSTOM and self.custom_roster:
            return self.custom_roster
        return SOFTWARE_DEV_ROSTER


def get_guilds_dir() -> Path:
    """Return ~/.octoflow/guilds directory path."""
    guild_dir = Path.home() / ".octoflow" / "guilds"
    guild_dir.mkdir(parents=True, exist_ok=True)
    return guild_dir


def list_available_guilds() -> dict[str, str]:
    """List all built-in and community-installed 8-arm specialist guilds."""
    guilds = {
        "software_dev": "Full-Stack Software Engineering Guild (Arch, DB, API, UI, State, QA, Sec, DevOps)",
        "aiml_research": "AI/ML Research & Model Training Guild (ETL, Architect, Training, Eval, Tune, ONNX, FastServe, Docs)",
        "fullstack_ai": "Fullstack AI Product Guild (Pipeline, PyTorch, FastAPI, UI Views, ONNX, E2E QA, Sec, Docker)",
    }
    guild_dir = get_guilds_dir()
    for f in sorted(guild_dir.glob("*.json")):
        try:
            import json

            data = json.loads(f.read_text(encoding="utf-8"))
            desc = data.get("description", "Community 8-Arm Custom Guild")
            guilds[f.stem] = desc
        except Exception:
            guilds[f.stem] = "Custom Guild"
    return guilds


def load_custom_guild(guild_name: str) -> list[ArmRoleConfig] | None:
    """Load a custom 8-arm roster from ~/.octoflow/guilds/<guild_name>.json."""
    clean_name = guild_name.strip().lower()
    if clean_name in ["software_dev", "software-dev"]:
        return SOFTWARE_DEV_ROSTER
    elif clean_name in ["aiml_research", "aiml-research", "ml"]:
        return AIML_RESEARCH_ROSTER
    elif clean_name in ["fullstack_ai", "fullstack-ai"]:
        return FULLSTACK_AI_ROSTER

    guild_file = get_guilds_dir() / f"{clean_name}.json"
    if not guild_file.exists():
        # Check current workspace .octoflow/guilds/
        ws_file = Path.cwd() / ".octoflow" / "guilds" / f"{clean_name}.json"
        if ws_file.exists():
            guild_file = ws_file
        else:
            return None

    try:
        import json

        payload = json.loads(guild_file.read_text(encoding="utf-8"))
        roster_data = payload.get("roster", payload if isinstance(payload, list) else [])
        roles: list[ArmRoleConfig] = []
        for item in roster_data:
            roles.append(ArmRoleConfig(**item))
        if len(roles) == 8:
            return roles
        return None
    except Exception:
        return None


def save_custom_guild(name: str, roster: list[ArmRoleConfig], description: str = "") -> Path:
    """Export or save an 8-arm roster to ~/.octoflow/guilds/<name>.json."""
    import json

    guild_file = get_guilds_dir() / f"{name.strip().lower()}.json"
    payload = {
        "name": name,
        "description": description or f"Custom {name} specialist roster",
        "roster": [r.model_dump() for r in roster],
    }
    guild_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return guild_file

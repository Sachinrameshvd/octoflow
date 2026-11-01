"""OctosFlow Consortium: Multi-Cephalopod Swarm Orchestration.

Coordinates N autonomous octopus conductors (e.g. 3-Octopus Triad or 8-Octopus Octopolis)
via the Inter-Octopus Synaptic Bus, executing phased convergence gates from
scaffolding to fullstack construction and autonomous live-run verification.
"""

import asyncio
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from octoflow.conductor import SupraesophagealConductor, SwarmTelemetryEvent
from octoflow.config import OctoFlowConfig, SwarmMorphology
from octoflow.federation import GLOBAL_FEDERATION_GUARD, FederationGuard
from octoflow.ignition import ProjectIgniter


class SynapticContractEvent(BaseModel):
    """Event broadcasted across the consortium when an octopus establishes a contract or deliverable."""

    timestamp: float = Field(default_factory=time.time)
    sender_octopus_id: int
    sender_octopus_title: str
    event_type: (
        str  # "SCAFFOLD_READY", "API_CONTRACT", "SCHEMA_DEFINED", "UI_MOUNT_READY", "VERIFY_PASS"
    )
    topic: str
    summary: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


class InterOctopusSynapticBus:
    """High-level bus interconnecting multiple independent octopus conductors with zero-trust PII sanitization."""

    def __init__(self, guard: FederationGuard | None = None):
        self.guard = guard or GLOBAL_FEDERATION_GUARD
        self.events: list[SynapticContractEvent] = []
        self._subscribers: dict[str, list[Callable[[SynapticContractEvent], None]]] = {}

    def broadcast(
        self,
        sender_id: int,
        sender_title: str,
        event_type: str,
        topic: str,
        summary: str = "",
        payload: dict[str, Any] | None = None,
    ) -> SynapticContractEvent:
        clean_summary, _ = self.guard.scan_and_sanitize(summary) if self.guard else (summary, [])
        clean_payload, _ = (
            self.guard.sanitize_payload(payload or {}) if self.guard else (payload or {}, [])
        )

        event = SynapticContractEvent(
            sender_octopus_id=sender_id,
            sender_octopus_title=sender_title,
            event_type=event_type,
            topic=topic,
            summary=clean_summary,
            payload=clean_payload,
        )
        self.events.append(event)
        # Notify subscribers
        for callback in self._subscribers.get(topic, []):
            try:
                callback(event)
            except Exception:
                pass
        for callback in self._subscribers.get("*", []):
            try:
                callback(event)
            except Exception:
                pass
        return event

    def subscribe(self, topic: str, callback: Callable[[SynapticContractEvent], None]) -> None:
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)


class OctopusGuildConfig(BaseModel):
    """Configuration for an individual octopus in the consortium."""

    octopus_id: int
    name: str
    title: str
    description: str
    color_hex: str
    icon: str
    morphology: SwarmMorphology = SwarmMorphology.SOFTWARE_DEV
    focus_domain: str


# Standard 3-Octopus Consortium (The Triad: 24 Arms Total)
TRIAD_GUILDS: list[OctopusGuildConfig] = [
    OctopusGuildConfig(
        octopus_id=0,
        name="genesis",
        title="Genesis & Foundation",
        description="System topology, package.json, vite.config.js, requirements.txt, and schemas.",
        color_hex="#00F0FF",  # Bioluminescent Cyan
        icon="◈",
        focus_domain="scaffolding",
    ),
    OctopusGuildConfig(
        octopus_id=1,
        name="engine",
        title="Backend & Intelligence",
        description="FastAPI endpoints, hardware controllers, WebSockets, DB persistence, and AI bridges.",
        color_hex="#3B82F6",  # Electric Blue
        icon="↯",
        focus_domain="backend",
    ),
    OctopusGuildConfig(
        octopus_id=2,
        name="vision",
        title="Frontend & Experience",
        description="React components, holographic HUD visuals, state stores, and responsive animations.",
        color_hex="#EC4899",  # Neon Magenta
        icon="○",
        focus_domain="frontend",
    ),
]

# Full 8-Octopus Consortium (The Octopolis: 64 Arms Total)
OCTOPOLIS_GUILDS: list[OctopusGuildConfig] = [
    OctopusGuildConfig(
        octopus_id=0,
        name="architect",
        title="System Architect",
        description="Topology, specifications, package manifests, and modular contracts.",
        color_hex="#00F0FF",  # Cyan
        icon="◈",
        focus_domain="architecture",
    ),
    OctopusGuildConfig(
        octopus_id=1,
        name="database",
        title="Database & Storage",
        description="Data schemas, ORM models, migration bridges, and persistence connectors.",
        color_hex="#A855F7",  # Deep Purple
        icon="◇",
        focus_domain="database",
    ),
    OctopusGuildConfig(
        octopus_id=2,
        name="backend",
        title="Backend & Services",
        description="REST/WebSocket endpoints, controller logic, and OS/hardware controllers.",
        color_hex="#3B82F6",  # Electric Blue
        icon="↯",
        focus_domain="backend",
    ),
    OctopusGuildConfig(
        octopus_id=3,
        name="frontend",
        title="Frontend & UI",
        description="React views, CSS design system, responsive HUD, and audio visualizers.",
        color_hex="#EC4899",  # Neon Magenta
        icon="○",
        focus_domain="frontend",
    ),
    OctopusGuildConfig(
        octopus_id=4,
        name="cognitive",
        title="AI & Cognitive Logic",
        description="Local LLM/Ollama bridges, prompt templates, RAG indexing, and agent tools.",
        color_hex="#10B981",  # Emerald
        icon="•",
        focus_domain="ai",
    ),
    OctopusGuildConfig(
        octopus_id=5,
        name="sentinel",
        title="Security & Sentinel",
        description="Input sanitization, authentication guards, secret masking, and dependency audits.",
        color_hex="#EF4444",  # Rose Red
        icon="▲",
        focus_domain="security",
    ),
    OctopusGuildConfig(
        octopus_id=6,
        name="qa_tester",
        title="Chaos & QA Testing",
        description="Unit test suites, integration edge-cases, and behavioral assertions.",
        color_hex="#F59E0B",  # Amber
        icon="✓",
        focus_domain="testing",
    ),
    OctopusGuildConfig(
        octopus_id=7,
        name="runner",
        title="Runner & DevOps",
        description="Dockerfile, server execution verification, runtime health checks, and self-healing.",
        color_hex="#EAB308",  # Solar Gold
        icon="■",
        focus_domain="devops",
    ),
]

# AI/ML Research Consortium Roster (The AI Triad: 24 Arms Total)
AIML_TRIAD_GUILDS: list[OctopusGuildConfig] = [
    OctopusGuildConfig(
        octopus_id=0,
        name="data_etl",
        title="Dataset & ETL Guild",
        description="Dataset pipeline, feature scaling, DataLoader, synthetic data, and train/val/test splits.",
        color_hex="#00F0FF",
        icon="◈",
        focus_domain="datasets",
    ),
    OctopusGuildConfig(
        octopus_id=1,
        name="neural_engine",
        title="Model & Training Loop",
        description="PyTorch neural architecture, forward passes, custom loss, AdamW optimizer, and learning rate schedulers.",
        color_hex="#F59E0B",
        icon="↯",
        focus_domain="training",
    ),
    OctopusGuildConfig(
        octopus_id=2,
        name="eval_mlops",
        title="Eval, ONNX & MLOps",
        description="Evaluation metrics, confusion matrices, ONNX/TorchScript export, FastAPI serving, and model cards.",
        color_hex="#10B981",
        icon="•",
        focus_domain="mlops",
    ),
]

# AI/ML Research Full Consortium (The AI Octopolis: 64 Arms Total)
AIML_OCTOPOLIS_GUILDS: list[OctopusGuildConfig] = [
    OctopusGuildConfig(
        octopus_id=0,
        name="data_prep",
        title="Data & Dataset ETL",
        description="Data loading, transforms, and splits.",
        color_hex="#00F0FF",
        icon="◈",
        focus_domain="data",
    ),
    OctopusGuildConfig(
        octopus_id=1,
        name="model_arch",
        title="Model Architect",
        description="PyTorch layers, attention heads, and weights.",
        color_hex="#A855F7",
        icon="◇",
        focus_domain="architecture",
    ),
    OctopusGuildConfig(
        octopus_id=2,
        name="training_loop",
        title="Training & Loss Loop",
        description="Forward/backward passes and AMP.",
        color_hex="#EF4444",
        icon="↯",
        focus_domain="training",
    ),
    OctopusGuildConfig(
        octopus_id=3,
        name="hpo_tuner",
        title="HPO & Schedulers",
        description="Hyperparameter optimization and tuning.",
        color_hex="#3B82F6",
        icon="•",
        focus_domain="hpo",
    ),
    OctopusGuildConfig(
        octopus_id=4,
        name="eval_bench",
        title="Evaluation & Benchmark",
        description="Accuracy, ROC curves, and ablations.",
        color_hex="#F59E0B",
        icon="○",
        focus_domain="evaluation",
    ),
    OctopusGuildConfig(
        octopus_id=5,
        name="quant_export",
        title="Quantization & ONNX",
        description="INT8 quantization and ONNX graph export.",
        color_hex="#EC4899",
        icon="↯",
        focus_domain="export",
    ),
    OctopusGuildConfig(
        octopus_id=6,
        name="inference_api",
        title="Inference & Triton API",
        description="FastAPI model serving and batching.",
        color_hex="#10B981",
        icon="▲",
        focus_domain="serving",
    ),
    OctopusGuildConfig(
        octopus_id=7,
        name="mlops_docs",
        title="MLOps & Governance",
        description="Model cards, reproducibility, and logging.",
        color_hex="#EAB308",
        icon="■",
        focus_domain="mlops",
    ),
]

# Hybrid Full-Stack AI Consortium (The Fullstack AI Triad: 24 Arms Total)
FULLSTACK_AI_TRIAD_GUILDS: list[OctopusGuildConfig] = [
    OctopusGuildConfig(
        octopus_id=0,
        name="genesis_data",
        title="Genesis & Data Pipelines",
        description="Project scaffold, schemas, dataset transformers, and vector store indexing.",
        color_hex="#00F0FF",
        icon="◈",
        focus_domain="scaffolding",
    ),
    OctopusGuildConfig(
        octopus_id=1,
        name="ai_backend",
        title="LLM Engine & Backend API",
        description="FastAPI service, model inference wrappers, tokenizers, scoring algorithms, and DB state.",
        color_hex="#3B82F6",
        icon="↯",
        focus_domain="backend",
    ),
    OctopusGuildConfig(
        octopus_id=2,
        name="frontend_hud",
        title="Interactive UI & Experience",
        description="Responsive cyber-dark dashboard, animated radial score gauge, keyword tags, and sample data loader.",
        color_hex="#EC4899",
        icon="○",
        focus_domain="frontend",
    ),
]

# Hybrid Full-Stack AI Consortium (The Fullstack AI Octopolis: 64 Arms Total)
FULLSTACK_AI_OCTOPOLIS_GUILDS: list[OctopusGuildConfig] = [
    OctopusGuildConfig(
        octopus_id=0,
        name="foundation",
        title="Foundation & Topology",
        description="Monorepo structure, schemas, and contracts.",
        color_hex="#00F0FF",
        icon="◈",
        focus_domain="architecture",
    ),
    OctopusGuildConfig(
        octopus_id=1,
        name="data_prep",
        title="Data & Feature Pipeline",
        description="Dataset preprocessing and feature extraction.",
        color_hex="#A855F7",
        icon="◇",
        focus_domain="data",
    ),
    OctopusGuildConfig(
        octopus_id=2,
        name="cognitive_core",
        title="Model & Cognitive Engine",
        description="Inference pipeline, weights, and scoring.",
        color_hex="#3B82F6",
        icon="•",
        focus_domain="ai",
    ),
    OctopusGuildConfig(
        octopus_id=3,
        name="backend_api",
        title="FastAPI Backend Engine",
        description="High-throughput REST/WebSocket endpoints.",
        color_hex="#10B981",
        icon="↯",
        focus_domain="backend",
    ),
    OctopusGuildConfig(
        octopus_id=4,
        name="frontend_ui",
        title="Interactive Web UI & HUD",
        description="Dark-mode dashboard, gauges, and state stores.",
        color_hex="#EC4899",
        icon="○",
        focus_domain="frontend",
    ),
    OctopusGuildConfig(
        octopus_id=5,
        name="security_guard",
        title="Security & Zero-Trust Guard",
        description="PII redaction and input validation.",
        color_hex="#EF4444",
        icon="▲",
        focus_domain="security",
    ),
    OctopusGuildConfig(
        octopus_id=6,
        name="qa_benchmark",
        title="QA & Benchmark Suite",
        description="Integration tests and latency assertions.",
        color_hex="#F59E0B",
        icon="✓",
        focus_domain="testing",
    ),
    OctopusGuildConfig(
        octopus_id=7,
        name="devops_deploy",
        title="DevOps & Docker Deploy",
        description="Containerization, runner verification, and live ignition.",
        color_hex="#EAB308",
        icon="■",
        focus_domain="devops",
    ),
]


def detect_morphology_from_objective(objective: str) -> SwarmMorphology:
    """Automatically detect project morphology (Software Dev, AI/ML Research, or Fullstack AI) from goal signals."""
    text = objective.lower()
    aiml_signals = [
        "train",
        "training",
        "pytorch",
        "tensorflow",
        "dataset",
        "etl",
        "loss",
        "hpo",
        "hyperparameter",
        "onnx",
        "quantization",
        "model card",
        "epoch",
        "weights",
        "lora",
        "fine-tune",
        "embedding",
    ]
    ai_product_signals = [
        "ai",
        "llm",
        "gpt",
        "claude",
        "nlp",
        "resume",
        "ats",
        "analyzer",
        "chatbot",
        "assistant",
        "jarvis",
        "agent",
        "rag",
        "vector",
        "vision",
    ]
    web_signals = [
        "fastapi",
        "react",
        "frontend",
        "ui",
        "dashboard",
        "html",
        "web",
        "css",
        "score gauge",
        "gauge",
        "views",
        "fullstack",
        "full-stack",
    ]

    aiml_count = sum(1 for s in aiml_signals if s in text)
    ai_prod_count = sum(1 for s in ai_product_signals if s in text)
    web_count = sum(1 for s in web_signals if s in text)

    # Hybrid AI + Web -> Fullstack AI
    if (ai_prod_count >= 1 and web_count >= 1) or "fullstack" in text or "full-stack" in text:
        return SwarmMorphology.FULLSTACK_AI
    # Pure AI/ML Research
    if aiml_count >= 2 or ("train" in text and "model" in text):
        return SwarmMorphology.AIML_RESEARCH
    # Explicit AI product
    if ai_prod_count >= 2:
        return SwarmMorphology.FULLSTACK_AI
    return SwarmMorphology.SOFTWARE_DEV


def get_consortium_guilds(
    morphology: SwarmMorphology, octopus_count: int
) -> list[OctopusGuildConfig]:
    """Retrieve specialist department guilds dynamically adapted to project morphology."""
    if morphology == SwarmMorphology.AIML_RESEARCH:
        roster = AIML_OCTOPOLIS_GUILDS if octopus_count >= 8 else AIML_TRIAD_GUILDS
    elif morphology == SwarmMorphology.FULLSTACK_AI:
        roster = FULLSTACK_AI_OCTOPOLIS_GUILDS if octopus_count >= 8 else FULLSTACK_AI_TRIAD_GUILDS
    else:
        roster = OCTOPOLIS_GUILDS if octopus_count >= 8 else TRIAD_GUILDS

    if octopus_count == 1:
        prefix = (
            "AI/ML"
            if morphology == SwarmMorphology.AIML_RESEARCH
            else ("Fullstack AI" if morphology == SwarmMorphology.FULLSTACK_AI else "Software")
        )
        return [
            OctopusGuildConfig(
                octopus_id=0,
                name="solo",
                title=f"Solo {prefix} Core",
                description=f"Full 8-arm multi-agent {prefix.lower()} swarm.",
                color_hex="#00F0FF",
                icon="◈",
                focus_domain="autonomous",
            )
        ]
    return roster[:octopus_count]


class OctosConsortium:
    """The High Cephalopod Consortium orchestrating multiple 8-arm octopuses in phased convergence."""

    def __init__(
        self,
        config: OctoFlowConfig | None = None,
        octopus_count: int = 3,
        telemetry_callback: Callable[[SwarmTelemetryEvent], None] | None = None,
    ):
        self.config = config or OctoFlowConfig()
        self.octopus_count = max(1, min(octopus_count, 8))
        self.telemetry_callback = telemetry_callback
        self.synaptic_bus = InterOctopusSynapticBus()

        # Dynamically retrieve guilds matched to project morphology (AIML, Fullstack AI, or Software Dev)
        self.guilds = get_consortium_guilds(self.config.morphology, self.octopus_count)

        # Instantiate N identical, proven SupraesophagealConductor instances
        self.conductors: list[SupraesophagealConductor] = []
        for guild in self.guilds:
            # Clone config with guild-specific settings if necessary
            cond_cfg = self.config.model_copy()
            conductor = SupraesophagealConductor(
                config=cond_cfg,
                telemetry_callback=self._handle_conductor_telemetry,
                octopus_id=guild.octopus_id,
                octopus_name=guild.name,
                octopus_title=guild.title,
                color_hex=guild.color_hex,
                synaptic_bus=self.synaptic_bus,
            )
            self.conductors.append(conductor)

        # Global consortium metrics
        self.total_tokens_used: int = 0
        self.total_cost_dollars: float = 0.0
        self.igniter = ProjectIgniter(workspace_dir=self.config.workspace_dir)

    def _handle_conductor_telemetry(self, event: SwarmTelemetryEvent) -> None:
        """Route and forward telemetry events to global callbacks."""
        self.total_tokens_used += 100  # telemetry tracking
        if self.telemetry_callback:
            self.telemetry_callback(event)

    async def arun_consortium(
        self,
        objective: str,
        cycles_per_octopus: int = 5,
        open_browser: bool = False,
    ) -> dict[str, Any]:
        """Execute the multi-octopus consortium across synchronized phase gates."""
        t_start = time.time()
        results: dict[str, Any] = {}

        if self.octopus_count == 1:
            # Single octopus execution
            res = await self.conductors[0].arun_swarm(objective, max_cycles=cycles_per_octopus)
            return {
                "tier": "solo",
                "total_arms": 8,
                "results": [res],
                "execution_time": time.time() - t_start,
            }

        # ---------------------------------------------------------------------
        # PHASE GATE 1: Genesis & Scaffolding (Octopus 0)
        # ---------------------------------------------------------------------
        genesis_cond = self.conductors[0]
        genesis_goal = (
            f"Phase 1 Foundation: Scaffold project folder topology, package.json, "
            f"vite.config.js, index.html, requirements.txt, and schemas for: {objective}"
        )
        genesis_res = await genesis_cond.arun_swarm(
            genesis_goal, max_cycles=max(2, cycles_per_octopus // 2)
        )
        results["genesis"] = genesis_res

        self.synaptic_bus.broadcast(
            sender_id=genesis_cond.octopus_id,
            sender_title=genesis_cond.octopus_title,
            event_type="SCAFFOLD_READY",
            topic="foundation",
            summary="Base manifests and workspace topology established.",
        )

        # Check cumulative consortium budget before launching Phase 2 (Q17)
        total_cost = sum(c.total_cost for c in self.conductors)
        if total_cost < self.config.max_budget_dollars:
            construction_tasks = []
            for cond in self.conductors[1:]:
                domain_goal = (
                    f"Build complete, production-grade {cond.octopus_title} deliverables for: {objective}. "
                    f"Adhere strictly to established project architecture and connect with sibling modules."
                )
                construction_tasks.append(
                    cond.arun_swarm(domain_goal, max_cycles=cycles_per_octopus)
                )

            if construction_tasks:
                parallel_results = await asyncio.gather(*construction_tasks, return_exceptions=True)
                results["construction"] = parallel_results
        else:
            results["budget_halt"] = True

        # Checkpoint state to .octoflow/checkpoint.json (Q32)
        try:
            import json

            ckpt_dir = Path(self.config.workspace_dir) / ".octoflow"
            ckpt_dir.mkdir(parents=True, exist_ok=True)
            ckpt_file = ckpt_dir / "checkpoint.json"
            ckpt_data = {
                "timestamp": time.time(),
                "objective": objective,
                "tier": "octopolis" if self.octopus_count >= 8 else "triad",
                "octopus_count": self.octopus_count,
                "phases_completed": list(results.keys()),
                "total_cost": sum(c.total_cost for c in self.conductors),
            }
            ckpt_file.write_text(json.dumps(ckpt_data, indent=2))
        except Exception:
            pass

        # ---------------------------------------------------------------------
        # PHASE GATE 3: Integrity Shield & Convergence
        # ---------------------------------------------------------------------
        # Run our automated project integrity synthesizer on workspace
        try:
            self.conductors[0]._post_process_project_integrity()
        except Exception:
            pass

        # ---------------------------------------------------------------------
        # PHASE GATE 4: Live Ignition & Service Provisioning (Octo 7 Runner)
        # ---------------------------------------------------------------------
        ignition_manifest = None
        try:
            ignition_manifest = self.igniter.ignite(objective=objective, open_browser=open_browser)
            if ignition_manifest and ignition_manifest.status in ("RUNNING", "READY"):
                results["ignition"] = ignition_manifest.model_dump()
                self.synaptic_bus.broadcast(
                    sender_id=7 if self.octopus_count >= 8 else 0,
                    sender_title="OCTO_7 RUNNER" if self.octopus_count >= 8 else "Cephalopod Core",
                    event_type="LIVE_SERVICE_READY",
                    topic="deployment",
                    summary=f"Live service provisioned at {ignition_manifest.primary_url}",
                    payload=ignition_manifest.model_dump(),
                )
                if self.telemetry_callback:
                    telemetry_evt = SwarmTelemetryEvent(
                        event_type="LIVE_SERVICE_READY",
                        arm_id=7,
                        role="DevOps & Runner",
                        status="RUNNING",
                        surprise=0.0,
                        threshold=0.5,
                        summary=f"LIVE APP DEPLOYED: {ignition_manifest.primary_url}",
                        octopus_id=7 if self.octopus_count >= 8 else 0,
                        octopus_title="OCTO_7 RUNNER"
                        if self.octopus_count >= 8
                        else "Cephalopod Core",
                        color_hex="#EAB308",
                        service_url=ignition_manifest.primary_url,
                        api_docs_url=ignition_manifest.api_docs_url,
                        service_type=ignition_manifest.service_type,
                        payload=ignition_manifest.model_dump(),
                    )
                    self.telemetry_callback(telemetry_evt)
        except Exception:
            pass

        t_total = time.time() - t_start
        total_arms = self.octopus_count * 8

        # Calculate combined tokens and cost
        total_tokens = sum(c.total_tokens_used for c in self.conductors)
        total_cost = sum(c.total_cost for c in self.conductors)

        return {
            "tier": "octopolis" if self.octopus_count >= 8 else "triad",
            "octopus_count": self.octopus_count,
            "total_arms": total_arms,
            "execution_time_seconds": t_total,
            "total_tokens_consumed": total_tokens,
            "total_cost_dollars": total_cost,
            "phase_results": results,
            "ignition": ignition_manifest.model_dump() if ignition_manifest else None,
            "status": "COMPLETED",
        }

    def run_consortium(
        self,
        objective: str,
        cycles_per_octopus: int = 5,
        open_browser: bool = False,
    ) -> dict[str, Any]:
        """Synchronously execute consortium across all Python 3.10-3.14+ loop environments."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(
                    asyncio.run, self.arun_consortium(objective, cycles_per_octopus, open_browser)
                ).result()
        else:
            return asyncio.run(self.arun_consortium(objective, cycles_per_octopus, open_browser))


def get_system_ram_gb() -> float:
    """Detect available physical RAM in GB safely across OS platforms."""
    try:
        import os

        if (
            hasattr(os, "sysconf")
            and "SC_PAGE_SIZE" in os.sysconf_names
            and "SC_PHYS_PAGES" in os.sysconf_names
        ):
            return (os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")) / (1024**3)
    except Exception:
        pass
    try:
        import subprocess

        out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
        return int(out) / (1024**3)
    except Exception:
        pass
    return 16.0  # safe default fallback


def estimate_elastic_octopus_count(objective: str, model_provider: str = "mock") -> tuple[int, str]:
    """Dynamically determine the optimal octopus count (1 to 8) based on cognitive load and hardware.

    Returns:
        (optimal_count, rationale_description)
    """
    text = objective.lower()

    # 1. Complexity Signals
    enterprise_signals = [
        "enterprise",
        "multi-tenant",
        "microservices",
        "kubernetes",
        "k8s",
        "distributed",
        "analytics engine",
        "streaming platform",
        "oauth",
        "billing",
        "stripe",
        "chaos",
        "pipeline",
        "cluster",
        "production-grade",
    ]
    fullstack_signals = [
        "full-stack",
        "fullstack",
        "web app",
        "frontend",
        "react",
        "vue",
        "dashboard",
        "fastapi",
        "rest api",
        "websocket",
        "database",
        "sqlite",
        "postgres",
        "assistant",
        "jarvis",
        "ui",
        "hud",
        "holographic",
        "interface",
        "node",
    ]
    micro_signals = [
        "script",
        "utility",
        "cli tool",
        "convert",
        "parser",
        "regex",
        "one file",
        "mini",
        "simple",
        "clean up",
        "calculate",
    ]

    enterprise_score = sum(1 for s in enterprise_signals if s in text)
    fullstack_score = sum(1 for s in fullstack_signals if s in text)
    micro_score = sum(1 for s in micro_signals if s in text)

    # Base count determination
    if enterprise_score >= 2 or ("enterprise" in text or "multi-tenant" in text):
        raw_count = 8
        tier_reason = f"Enterprise scope detected ({enterprise_score} complexity signals)"
    elif micro_score >= 1 and fullstack_score == 0:
        raw_count = 1
        tier_reason = "Lightweight utility scope detected"
    elif fullstack_score >= 1 or len(text.split()) > 10:
        raw_count = 3
        tier_reason = f"Fullstack interactive scope detected ({fullstack_score} domain signals)"
    else:
        raw_count = 2
        tier_reason = "Standard software engineering task"

    # 2. Hardware Resource Boundary Guard
    ram_gb = get_system_ram_gb()
    if model_provider.lower() == "ollama" and ram_gb < 16.0 and raw_count > 3:
        raw_count = 3
        tier_reason += f" (capped at 3 octopuses to preserve {ram_gb:.0f}GB local RAM)"
    elif model_provider.lower() == "ollama" and ram_gb < 12.0 and raw_count > 2:
        raw_count = 2
        tier_reason += f" (capped at 2 octopuses for stability on {ram_gb:.0f}GB RAM)"

    return raw_count, tier_reason

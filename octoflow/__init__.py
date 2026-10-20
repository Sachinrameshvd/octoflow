"""OctoFlow: Decentralized Cephalopod Multi-Agent Swarm with Sensory Surprise Gating.

Inspired by the distributed neurobiology of Octopus vulgaris.
Features 8 autonomous arm ganglia, event-triggered silent execution,
dynamic multi-head coalition attention, and Vertical Lobe Hebbian memory.
"""

__version__ = "0.2.0"

from octoflow.config import (
    OctoFlowConfig,
    SwarmMorphology,
    ArmRoleConfig,
    SOFTWARE_DEV_ROSTER,
    AIML_RESEARCH_ROSTER,
    FULLSTACK_AI_ROSTER,
)
from octoflow.conductor import SupraesophagealConductor, SwarmTelemetryEvent
from octoflow.outcome import (
    RunMode,
    RunOutcome,
    RunResult,
    OctoFlowError,
    ProviderExhaustedError,
)
from octoflow.arm import ArmAgent, ArmStepResult
from octoflow.gate import SurpriseGate
from octoflow.bus import InterBrachialBus, BrachialMessage
from octoflow.memory import VerticalLobeMemory
from octoflow.encoder import CodeSensoryEncoder
from octoflow.tools import WorkspaceSandbox, ToolResult
from octoflow.provider import BaseLLMProvider, MockLLMProvider, get_llm_provider
from octoflow.mcp import OctoFlowMCPServer, MCPRegistry, MCPToolSchema, MCPToolCallResult
from octoflow.consortium import (
    OctosConsortium,
    InterOctopusSynapticBus,
    SynapticContractEvent,
    estimate_elastic_octopus_count,
)

from octoflow.report import generate_html_audit_report, collect_mission_audit_data
from octoflow.healing import self_heal_workspace
from octoflow.triage import triage_workspace_diffs
from octoflow.notify import send_mission_notification
from octoflow.provider import FailoverLLMProvider
from octoflow.bench import run_swarm_benchmark_suite
from octoflow.monorepo import scan_monorepo_topology
from octoflow.recorder import TerminalRecorder

__all__ = [
    "OctoFlowConfig",
    "SwarmMorphology",
    "ArmRoleConfig",
    "SOFTWARE_DEV_ROSTER",
    "AIML_RESEARCH_ROSTER",
    "FULLSTACK_AI_ROSTER",
    "SupraesophagealConductor",
    "SwarmTelemetryEvent",
    "ArmAgent",
    "ArmStepResult",
    "SurpriseGate",
    "InterBrachialBus",
    "BrachialMessage",
    "VerticalLobeMemory",
    "CodeSensoryEncoder",
    "WorkspaceSandbox",
    "ToolResult",
    "BaseLLMProvider",
    "MockLLMProvider",
    "get_llm_provider",
    "FailoverLLMProvider",
    "OctoFlowMCPServer",
    "MCPRegistry",
    "MCPToolSchema",
    "MCPToolCallResult",
    "OctosConsortium",
    "InterOctopusSynapticBus",
    "SynapticContractEvent",
    "estimate_elastic_octopus_count",
    "generate_html_audit_report",
    "collect_mission_audit_data",
    "self_heal_workspace",
    "triage_workspace_diffs",
    "send_mission_notification",
    "run_swarm_benchmark_suite",
    "scan_monorepo_topology",
    "TerminalRecorder",
]


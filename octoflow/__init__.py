"""OctoFlow: Decentralized Cephalopod Multi-Agent Swarm with Sensory Surprise Gating.

Inspired by the distributed neurobiology of Octopus vulgaris.
Features 8 autonomous arm ganglia, event-triggered silent execution,
dynamic multi-head coalition attention, and Vertical Lobe Hebbian memory.
"""

import importlib
from typing import Any

try:
    from importlib.metadata import version as _get_version, PackageNotFoundError as _PkgNotFound
    __version__ = _get_version("octoflow")
except (_PkgNotFound, Exception):
    __version__ = "0.3.0"

_LAZY_EXPORTS = {
    # config
    "OctoFlowConfig": "octoflow.config",
    "SwarmMorphology": "octoflow.config",
    "ArmRoleConfig": "octoflow.config",
    "SOFTWARE_DEV_ROSTER": "octoflow.config",
    "AIML_RESEARCH_ROSTER": "octoflow.config",
    "FULLSTACK_AI_ROSTER": "octoflow.config",
    # conductor
    "SupraesophagealConductor": "octoflow.conductor",
    "SwarmTelemetryEvent": "octoflow.conductor",
    # outcome
    "RunMode": "octoflow.outcome",
    "RunOutcome": "octoflow.outcome",
    "RunResult": "octoflow.outcome",
    "OctoFlowError": "octoflow.outcome",
    "ProviderExhaustedError": "octoflow.outcome",
    # arm
    "ArmAgent": "octoflow.arm",
    "ArmStepResult": "octoflow.arm",
    # gate
    "SurpriseGate": "octoflow.gate",
    # bus
    "InterBrachialBus": "octoflow.bus",
    "BrachialMessage": "octoflow.bus",
    # memory
    "VerticalLobeMemory": "octoflow.memory",
    # encoder
    "CodeSensoryEncoder": "octoflow.encoder",
    # tools
    "WorkspaceSandbox": "octoflow.tools",
    "ToolResult": "octoflow.tools",
    # provider
    "BaseLLMProvider": "octoflow.provider",
    "MockLLMProvider": "octoflow.provider",
    "FailoverLLMProvider": "octoflow.provider",
    "CascadePoolLLMProvider": "octoflow.provider",
    "get_llm_provider": "octoflow.provider",
    "register_provider": "octoflow.provider",
    "unregister_provider": "octoflow.provider",
    "get_registered_provider": "octoflow.provider",
    "list_registered_providers": "octoflow.provider",
    "ProviderError": "octoflow.provider",
    "ProviderAuthError": "octoflow.provider",
    "ProviderRateLimitError": "octoflow.provider",
    "ProviderTransientError": "octoflow.provider",
    "ProviderRequestError": "octoflow.provider",
    "ProviderUnavailableError": "octoflow.provider",
    "classify_http_error": "octoflow.provider",
    "redact_secrets": "octoflow.provider",
    "set_sleep_functions": "octoflow.provider",
    "reset_sleep_functions": "octoflow.provider",
    # router
    "Route": "octoflow.router",
    "RouteKind": "octoflow.router",
    "classify_input": "octoflow.router",
    # mcp
    "OctoFlowMCPServer": "octoflow.mcp",
    "MCPRegistry": "octoflow.mcp",
    "MCPToolSchema": "octoflow.mcp",
    "MCPToolCallResult": "octoflow.mcp",
    # consortium
    "OctosConsortium": "octoflow.consortium",
    # guild
    "ArmSpec": "octoflow.guild",
    "GuildSpec": "octoflow.guild",
    "ToolPolicy": "octoflow.guild",
    "load_guild": "octoflow.guild",
    "list_guilds": "octoflow.guild",
    "validate_guild_file": "octoflow.guild",
    "InterOctopusSynapticBus": "octoflow.consortium",
    "SynapticContractEvent": "octoflow.consortium",
    "estimate_elastic_octopus_count": "octoflow.consortium",
    # report
    "generate_html_audit_report": "octoflow.report",
    "collect_mission_audit_data": "octoflow.report",
    # healing
    "self_heal_workspace": "octoflow.healing",
    # triage
    "triage_workspace_diffs": "octoflow.triage",
    # notify
    "send_mission_notification": "octoflow.notify",
    # bench
    "run_swarm_benchmark_suite": "octoflow.bench",
    # monorepo
    "scan_monorepo_topology": "octoflow.monorepo",
    # recorder
    "TerminalRecorder": "octoflow.recorder",
    # settings
    "Settings": "octoflow.settings",
    "load_settings": "octoflow.settings",
    "save_settings": "octoflow.settings",
    "ProviderSettings": "octoflow.settings",
    "UISettings": "octoflow.settings",
    "ServerSettings": "octoflow.settings",
    "DefaultsSettings": "octoflow.settings",
    "ConfigurationError": "octoflow.settings",
}

__all__ = list(_LAZY_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    """Lazy module export resolution to avoid eagerly loading heavy dependencies."""
    if name in _LAZY_EXPORTS:
        mod_name = _LAZY_EXPORTS[name]
        mod = importlib.import_module(mod_name)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module 'octoflow' has no attribute '{name}'")

"""Tests for OctosFlow Multi-Cephalopod Swarm Consortium (Triad & Octopolis)."""

import pytest
import asyncio
from octoflow.config import OctoFlowConfig
from octoflow.consortium import (
    OctosConsortium,
    InterOctopusSynapticBus,
    SynapticContractEvent,
    TRIAD_GUILDS,
    OCTOPOLIS_GUILDS,
    estimate_elastic_octopus_count,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_elastic_autoscaler():
    """Verify dynamic cognitive load autoscaler assigns optimal octopus counts."""
    # 1. Micro utility script -> 1 Octopus
    count_micro, reason_micro = estimate_elastic_octopus_count("Write a python script to parse CSV files")
    assert count_micro == 1
    assert "utility" in reason_micro.lower()

    # 2. Fullstack interactive web application -> 3 Octopuses
    count_fs, reason_fs = estimate_elastic_octopus_count("Build a JARVIS assistant with FastAPI backend and React frontend")
    assert count_fs == 3
    assert "fullstack" in reason_fs.lower()

    # 3. Enterprise distributed platform -> 8 Octopuses
    count_ent, reason_ent = estimate_elastic_octopus_count("Build an enterprise multi-tenant microservices analytics platform with Docker and Kubernetes")
    assert count_ent == 8
    assert "enterprise" in reason_ent.lower()



def test_inter_octopus_synaptic_bus():
    """Verify event broadcasting and topic subscription across synaptic bus."""
    bus = InterOctopusSynapticBus()
    received = []

    bus.subscribe("api", lambda evt: received.append(evt))

    evt = bus.broadcast(
        sender_id=1,
        sender_title="Backend & Services",
        event_type="API_CONTRACT",
        topic="api",
        summary="POST /api/mac/volume",
        payload={"endpoint": "/api/mac/volume", "method": "POST"},
    )

    assert len(bus.events) == 1
    assert len(received) == 1
    assert received[0].topic == "api"
    assert received[0].summary == "POST /api/mac/volume"


def test_consortium_initialization_triad():
    """Verify 3-Octopus Triad creates 24 arms across 3 conductors."""
    cfg = OctoFlowConfig(model_provider="mock")
    consortium = OctosConsortium(config=cfg, octopus_count=3)

    assert len(consortium.conductors) == 3
    assert len(consortium.guilds) == 3
    assert consortium.guilds[0].title == "Genesis & Foundation"
    assert consortium.guilds[1].title == "Backend & Intelligence"
    assert consortium.guilds[2].title == "Frontend & Experience"

    # Each conductor must have 8 autonomous arms
    for conductor in consortium.conductors:
        assert len(conductor.arms) == 8


def test_consortium_initialization_octopolis():
    """Verify 8-Octopus Octopolis creates 64 arms across 8 conductors."""
    cfg = OctoFlowConfig(model_provider="mock")
    consortium = OctosConsortium(config=cfg, octopus_count=8)

    assert len(consortium.conductors) == 8
    assert len(consortium.guilds) == 8
    titles = [g.title for g in consortium.guilds]
    assert "System Architect" in titles
    assert "Database & Storage" in titles
    assert "Backend & Services" in titles
    assert "Frontend & UI" in titles
    assert "AI & Cognitive Logic" in titles
    assert "Security & Sentinel" in titles
    assert "Chaos & QA Testing" in titles
    assert "Runner & DevOps" in titles

    total_arms = sum(len(c.arms) for c in consortium.conductors)
    assert total_arms == 64


@pytest.mark.anyio
async def test_consortium_execution_flow(anyio_backend):
    """Verify asynchronous phase gate execution of multi-octopus swarm."""
    if anyio_backend != "asyncio":
        pytest.skip("Test specifically covers asyncio execution")

    cfg = OctoFlowConfig(model_provider="mock")
    consortium = OctosConsortium(config=cfg, octopus_count=3)

    result = await consortium.arun_consortium(
        objective="Build an autonomous IoT telemetry dashboard",
        cycles_per_octopus=1,
    )

    assert result["status"] == "COMPLETED"
    assert result["octopus_count"] == 3
    assert result["total_arms"] == 24
    assert result["tier"] == "triad"
    assert "genesis" in result["phase_results"]
    assert "construction" in result["phase_results"]


def test_render_consortium_dashboard_matrix():
    """Verify render_consortium_dashboard formats progress bars and 8-arm neural matrix."""
    from octoflow.cli import render_consortium_dashboard
    from rich.panel import Panel

    mock_states = {
        0: {
            "title": "Genesis & Foundation",
            "color_tag": "cyan",
            "progress_pct": 100.0,
            "arms": ["✔"] * 8,
            "action": "Completed workspace scaffold",
        },
        1: {
            "title": "Backend & Intelligence",
            "color_tag": "blue",
            "progress_pct": 65.0,
            "arms": ["✔", "⚡", "·", "·", "·", "·", "·", "·"],
            "action": "Writing FastAPI routes",
        },
    }

    panel = render_consortium_dashboard(
        objective="Build AI Resume & ATS Match Analyzer",
        octopus_states=mock_states,
        total_tokens_saved=87.5,
        total_cost=0.015,
        last_event_msg="[Backend / API]: Writing schemas/resume.py",
        elapsed_seconds=4.5,
        total_arms=16,
        tier_name="TEST_TIER",
    )

    assert isinstance(panel, Panel)


def test_domain_adaptive_morphology_and_guilds():
    """Verify consortium adapts guilds and arms to Software, AIML, and Fullstack AI domains."""
    from octoflow.config import SwarmMorphology
    from octoflow.consortium import detect_morphology_from_objective, get_consortium_guilds

    # 1. Pure AI/ML Research
    m_aiml = detect_morphology_from_objective("Train a PyTorch neural network on CIFAR-10 with custom loss and ONNX export")
    assert m_aiml == SwarmMorphology.AIML_RESEARCH
    guilds_aiml = get_consortium_guilds(m_aiml, 3)
    assert any("ETL" in g.title or "Dataset" in g.title for g in guilds_aiml)
    assert any("Training" in g.title for g in guilds_aiml)

    # 2. Hybrid Fullstack AI (e.g. AI Resume Analyzer)
    m_fullstack_ai = detect_morphology_from_objective("Build AI Resume & ATS Match Analyzer with FastAPI, 0-100 score gauge, and dark mode UI")
    assert m_fullstack_ai == SwarmMorphology.FULLSTACK_AI
    guilds_fs = get_consortium_guilds(m_fullstack_ai, 3)
    assert any("LLM" in g.title or "Backend" in g.title for g in guilds_fs)
    assert any("Interactive UI" in g.title or "Experience" in g.title for g in guilds_fs)

    # 3. Pure Software Engineering
    m_sw = detect_morphology_from_objective("Build a high performance microservice with Docker and PostgreSQL")
    assert m_sw == SwarmMorphology.SOFTWARE_DEV
    guilds_sw = get_consortium_guilds(m_sw, 3)
    assert any("Genesis" in g.title for g in guilds_sw)
    assert any("Frontend & Experience" in g.title for g in guilds_sw)

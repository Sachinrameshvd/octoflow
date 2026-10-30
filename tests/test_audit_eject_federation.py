"""Automated Test Suite for OctoFlow Audit, Eject, Federation, and Claude Plugin."""

import tempfile
from pathlib import Path

import pytest
from octoflow.audit import AuditReport, evaluate_workspace
from octoflow.bus import InterBrachialBus
from octoflow.consortium import InterOctopusSynapticBus
from octoflow.eject import eject_harness
from octoflow.federation import (
    FederationGuard,
    PeerTrustLevel,
    PIIAction,
)


def test_pii_rules_and_redaction():
    guard = FederationGuard(default_action=PIIAction.REDACT)

    # Test OpenAI Key
    text = "Here is my sk-1234567890abcdef1234567890abcdef1234567890 key"
    cleaned, evts = guard.scan_and_sanitize(text)
    assert "[REDACTED_OPENAI_KEY]" in cleaned
    assert "sk-123456" not in cleaned
    assert len(evts) >= 1

    # Test Anthropic Key
    text_ant = "Anthropic secret sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890"
    cleaned_ant, evts_ant = guard.scan_and_sanitize(text_ant)
    assert "[REDACTED_ANTHROPIC_KEY]" in cleaned_ant

    # Test Email
    text_email = "Contact developer at octopus@deepsea.io immediately"
    cleaned_email, _ = guard.scan_and_sanitize(text_email)
    assert "[REDACTED_EMAIL]" in cleaned_email

    # Test AWS Key
    text_aws = "Deploy using AKIAIOSFODNN7EXAMPLE"
    cleaned_aws, _ = guard.scan_and_sanitize(text_aws)
    assert "[REDACTED_AWS_ACCESS_KEY]" in cleaned_aws

    # Test Credit Card
    text_cc = "Payment card is 4111-2222-3333-4444"
    cleaned_cc, _ = guard.scan_and_sanitize(text_cc)
    assert "[REDACTED_CREDIT_CARD]" in cleaned_cc


def test_pii_blocking_action():
    guard = FederationGuard(default_action=PIIAction.BLOCK)
    with pytest.raises(PermissionError) as exc_info:
        guard.scan_and_sanitize("Leaking secret: sk-1234567890abcdef1234567890abcdef1234567890")
    assert "FederationGuard blocked transmission" in str(exc_info.value)


def test_pii_payload_recursion():
    guard = FederationGuard(default_action=PIIAction.REDACT)
    payload = {
        "user_email": "alice@domain.org",
        "nested": {
            "token": "ghp_123456789012345678901234567890123456",
            "items": ["safe_string", "contact@domain.org"],
        },
    }
    clean_payload, evts = guard.sanitize_payload(payload)
    assert clean_payload["user_email"] == "[REDACTED_EMAIL]"
    assert clean_payload["nested"]["token"] == "[REDACTED_GITHUB_TOKEN]"
    assert clean_payload["nested"]["items"][1] == "[REDACTED_EMAIL]"
    assert len(evts) >= 3


def test_federation_peer_trust_scoring():
    guard = FederationGuard()
    peer = guard.register_peer("peer_node_9", name="Cloud_Octopus_Sentinel")
    assert peer.trust_level == PeerTrustLevel.UNTRUSTED

    # Record 10 successes
    for _ in range(10):
        guard.record_peer_outcome("peer_node_9", success=True)
    assert peer.trust_score >= 0.70
    assert peer.trust_level in [PeerTrustLevel.VERIFIED, PeerTrustLevel.CORE]

    # Threat event causes immediate penalty and downgrade
    guard.record_peer_outcome("peer_node_9", success=False, threat=True)
    assert peer.threat_events == 1
    assert peer.trust_score < 0.70


def test_bus_pii_integration():
    bus = InterBrachialBus(n_arms=8)
    # Sending lateral message containing credential
    msg = bus.send_lateral(
        sender_id=1,
        target_id=2,
        intent="COOPERATIVE_PULL",
        summary="Use sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890 for API calls",
        payload={"secret": "AIzaSyD-1234567890abcdefghijklmnopqrstuv"},
    )
    assert "[REDACTED_ANTHROPIC_KEY]" in msg.summary
    assert "sk-ant-" not in msg.summary
    assert "[REDACTED_GOOGLE_KEY]" in msg.payload["secret"]


def test_consortium_bus_pii_integration():
    c_bus = InterOctopusSynapticBus()
    evt = c_bus.broadcast(
        sender_id=0,
        sender_title="Genesis",
        event_type="API_CONTRACT",
        topic="auth",
        summary="Database password is password='SuperSecretPassword123'",
        payload={"admin_email": "root@corp.com"},
    )
    assert "[REDACTED_SECRET]" in evt.summary or "[REDACTED" in evt.summary
    assert evt.payload["admin_email"] == "[REDACTED_EMAIL]"


def test_audit_workspace_evaluation():
    report = evaluate_workspace(".")
    assert isinstance(report, AuditReport)
    assert report.total_score >= 90.0
    assert report.letter_grade in ["A", "A+"]
    assert "code_hygiene" in report.categories
    assert "test_suite" in report.categories
    assert "security" in report.categories
    assert "neural_readiness" in report.categories
    assert "swarm_health" in report.categories


def test_eject_harness_generation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = eject_harness(output_dir=tmp_dir)
        assert out_path.is_dir()
        expected_files = [
            "pii_guard.py",
            "sensory_gate.py",
            "arm_dispatcher.py",
            "mcp_server.py",
            "run.py",
            "README.md",
            "requirements.txt",
        ]
        for f in expected_files:
            target = out_path / f
            assert target.is_file(), f"Missing ejected file: {f}"
            assert target.stat().st_size > 0


def test_claude_code_manifest_files():
    root = Path(".")
    plugin_json = root / ".claude-plugin" / "plugin.json"
    hooks_json = root / ".claude-plugin" / "hooks" / "hooks.json"
    mcp_json = root / ".mcp.json"

    assert plugin_json.is_file()
    assert hooks_json.is_file()
    assert mcp_json.is_file()

    import json

    data = json.loads(plugin_json.read_text())
    assert data["name"] == "octoflow"
    assert "/octo" in data["commands"]
    assert "/octo:audit" in data["commands"]
    assert "/octo:eject" in data["commands"]


def test_manual_and_field_guide():
    from octoflow.manual import MANUAL_SECTIONS

    assert len(MANUAL_SECTIONS) >= 6
    for k in ["1", "2", "3", "4", "5", "6"]:
        assert k in MANUAL_SECTIONS
        assert len(MANUAL_SECTIONS[k]["title"]) > 0
        assert len(MANUAL_SECTIONS[k]["content"]) > 0

    # Test markdown manual exists
    manual_md = Path("docs/MANUAL.md")
    assert manual_md.is_file()
    content = manual_md.read_text(encoding="utf-8")
    assert "OctoFlow: The Master Cephalopod Manual" in content
    assert "The 8 Specialized Neural Arm Ganglia" in content
    assert "Active Inference" in content

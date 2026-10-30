"""OctoFlow PII/Secret Redactor & Experimental Agent Federation Pipeline.

CORE UTILITY:
Provides automated 14-pattern PII, secret, and credential redaction (API keys,
tokens, credit cards, emails) and safe log filtering across arms and swarms.

EXPERIMENTAL / UNUSED:
Networking and peer node trust scoring (FederationPeer, PeerTrustLevel) are
currently experimental, unused prototypes. Networking for federation is not implemented.
"""

import hashlib
import re
import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PIIAction(str, Enum):
    """Action to take when PII or sensitive secrets are detected."""

    BLOCK = "BLOCK"
    REDACT = "REDACT"
    HASH = "HASH"
    PASS = "PASS"


class PeerTrustLevel(str, Enum):
    """Zero-trust security tiers for federated cephalopod agents. [experimental: unused prototype]"""

    UNTRUSTED = "UNTRUSTED"  # Level 0: Public/unknown peer, strict PII redaction & discovery only
    PROBATION = "PROBATION"  # Level 1: Initial verified handshake, task requests permitted
    VERIFIED = "VERIFIED"  # Level 2: Proven reliability, partial memory share
    CORE = "CORE"  # Level 3: Full consortium peer, direct synaptic bandwidth


class PIIDetectionRule(BaseModel):
    """Specification of a regex-based PII or credential pattern."""

    name: str
    pattern: str
    replacement: str
    severity: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW


# 14 Comprehensive PII and Secret Patterns
PII_RULES: list[PIIDetectionRule] = [
    PIIDetectionRule(
        name="OPENAI_API_KEY",
        pattern=r"\bsk-[a-zA-Z0-9]{20,60}\b",
        replacement="[REDACTED_OPENAI_KEY]",
        severity="CRITICAL",
    ),
    PIIDetectionRule(
        name="ANTHROPIC_API_KEY",
        pattern=r"\bsk-ant-[a-zA-Z0-9_-]{20,80}\b",
        replacement="[REDACTED_ANTHROPIC_KEY]",
        severity="CRITICAL",
    ),
    PIIDetectionRule(
        name="GITHUB_TOKEN",
        pattern=r"\b(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,255}\b",
        replacement="[REDACTED_GITHUB_TOKEN]",
        severity="CRITICAL",
    ),
    PIIDetectionRule(
        name="AWS_ACCESS_KEY",
        pattern=r"\b(AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}\b",
        replacement="[REDACTED_AWS_ACCESS_KEY]",
        severity="CRITICAL",
    ),
    PIIDetectionRule(
        name="AWS_SECRET_KEY",
        pattern=r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]",
        replacement="aws_secret_access_key='[REDACTED_AWS_SECRET]'",
        severity="CRITICAL",
    ),
    PIIDetectionRule(
        name="GOOGLE_AI_KEY",
        pattern=r"\bAIza[0-9A-Za-z-_]{30,42}\b",
        replacement="[REDACTED_GOOGLE_KEY]",
        severity="CRITICAL",
    ),
    PIIDetectionRule(
        name="STRIPE_KEY",
        pattern=r"\b(sk|rk)_(live|test)_[0-9a-zA-Z]{24,34}\b",
        replacement="[REDACTED_STRIPE_KEY]",
        severity="CRITICAL",
    ),
    PIIDetectionRule(
        name="SLACK_TOKEN",
        pattern=r"\bxox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}\b",
        replacement="[REDACTED_SLACK_TOKEN]",
        severity="CRITICAL",
    ),
    PIIDetectionRule(
        name="JWT_TOKEN",
        pattern=r"\beyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b",
        replacement="[REDACTED_JWT_TOKEN]",
        severity="HIGH",
    ),
    PIIDetectionRule(
        name="PRIVATE_KEY",
        pattern=r"-----BEGIN [A-Z ]*PRIVATE KEY-----[a-zA-Z0-9/+\s=]+-----END [A-Z ]*PRIVATE KEY-----",
        replacement="[REDACTED_PRIVATE_KEY_BLOCK]",
        severity="CRITICAL",
    ),
    PIIDetectionRule(
        name="GENERIC_PASSWORD",
        pattern=r"(?i)(password|passwd|secret|api_key|authToken)\s*[:=]\s*['\"][^'\"]{6,64}['\"]",
        replacement=r"\1='[REDACTED_SECRET]'",
        severity="HIGH",
    ),
    PIIDetectionRule(
        name="EMAIL_ADDRESS",
        pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
        replacement="[REDACTED_EMAIL]",
        severity="MEDIUM",
    ),
    PIIDetectionRule(
        name="IPV4_ADDRESS",
        pattern=r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
        replacement="[REDACTED_IP]",
        severity="LOW",
    ),
    PIIDetectionRule(
        name="CREDIT_CARD",
        pattern=r"\b(?:\d{4}[ -]?){3}\d{4}\b",
        replacement="[REDACTED_CREDIT_CARD]",
        severity="CRITICAL",
    ),
]


class SanitizationEvent(BaseModel):
    """Log entry when sensitive data is intercepted."""

    timestamp: float = Field(default_factory=time.time)
    rule_name: str
    severity: str
    action_taken: str


class FederationPeer(BaseModel):
    """Metadata and trust score for a federated agent or node."""

    peer_id: str
    name: str
    endpoint: str = ""
    trust_level: PeerTrustLevel = PeerTrustLevel.UNTRUSTED
    successful_tasks: int = 0
    failed_tasks: int = 0
    threat_events: int = 0
    created_at: float = Field(default_factory=time.time)
    last_seen: float = Field(default_factory=time.time)

    @property
    def trust_score(self) -> float:
        """Calculate dynamic trust score [0.0 - 1.0].

        Formula: 0.5 * (success_rate) + 0.3 * (liveness) - 0.5 * (threat_penalty)
        """
        total = self.successful_tasks + self.failed_tasks
        success_ratio = (self.successful_tasks / total) if total > 0 else 0.5
        recency = max(0.0, 1.0 - (time.time() - self.last_seen) / 86400.0)
        threat_penalty = min(1.0, self.threat_events * 0.25)

        score = (0.5 * success_ratio) + (0.3 * recency) - (0.5 * threat_penalty)
        return float(max(0.0, min(1.0, score)))


class FederationGuard:
    """Enterprise-grade PII & Secret filtering pipeline for agent messaging."""

    def __init__(self, default_action: PIIAction = PIIAction.REDACT):
        self.default_action = default_action
        self._compiled_rules = [(rule, re.compile(rule.pattern)) for rule in PII_RULES]
        self.audit_log: list[SanitizationEvent] = []
        self.peers: dict[str, FederationPeer] = {}

    def scan_and_sanitize(
        self,
        text: str,
        action: PIIAction | None = None,
    ) -> tuple[str, list[SanitizationEvent]]:
        """Scans text for all 14 PII/secret patterns and applies the chosen action."""
        if not text or not isinstance(text, str):
            return text, []

        act = action or self.default_action
        sanitized = text
        events: list[SanitizationEvent] = []

        for rule, compiled_regex in self._compiled_rules:
            matches = list(compiled_regex.finditer(sanitized))
            if matches:
                event = SanitizationEvent(
                    rule_name=rule.name,
                    severity=rule.severity,
                    action_taken=act.value,
                )
                events.append(event)
                self.audit_log.append(event)

                if act == PIIAction.BLOCK:
                    raise PermissionError(
                        f"FederationGuard blocked transmission: Detected {rule.name} ({rule.severity})"
                    )
                elif act == PIIAction.REDACT:
                    sanitized = compiled_regex.sub(rule.replacement, sanitized)
                elif act == PIIAction.HASH:

                    def _hasher(m: re.Match) -> str:
                        h = hashlib.sha256(m.group(0).encode()).hexdigest()[:12]
                        return f"[HASHED_{rule.name}_{h}]"

                    sanitized = compiled_regex.sub(_hasher, sanitized)
                elif act == PIIAction.PASS:
                    # Log event but leave text unmodified
                    pass

        return sanitized, events

    def sanitize_payload(
        self,
        payload: Any,
        action: PIIAction | None = None,
    ) -> tuple[Any, list[SanitizationEvent]]:
        """Recursively sanitizes dictionaries, lists, and strings in payloads."""
        all_events: list[SanitizationEvent] = []

        if isinstance(payload, str):
            clean_str, evts = self.scan_and_sanitize(payload, action)
            all_events.extend(evts)
            return clean_str, all_events
        elif isinstance(payload, dict):
            clean_dict = {}
            for k, v in payload.items():
                # Check key itself
                clean_k, k_evts = self.scan_and_sanitize(str(k), action)
                all_events.extend(k_evts)
                clean_v, v_evts = self.sanitize_payload(v, action)
                all_events.extend(v_evts)
                clean_dict[clean_k] = clean_v
            return clean_dict, all_events
        elif isinstance(payload, list):
            clean_list = []
            for item in payload:
                clean_item, item_evts = self.sanitize_payload(item, action)
                all_events.extend(item_evts)
                clean_list.append(clean_item)
            return clean_list, all_events
        else:
            return payload, all_events

    def register_peer(self, peer_id: str, name: str, endpoint: str = "") -> FederationPeer:
        """Register a new peer node in the federation."""
        peer = FederationPeer(peer_id=peer_id, name=name, endpoint=endpoint)
        self.peers[peer_id] = peer
        return peer

    def record_peer_outcome(self, peer_id: str, success: bool, threat: bool = False) -> None:
        """Record task outcome to update peer behavioral trust score."""
        if peer_id in self.peers:
            peer = self.peers[peer_id]
            peer.last_seen = time.time()
            if threat:
                peer.threat_events += 1
            elif success:
                peer.successful_tasks += 1
            else:
                peer.failed_tasks += 1

            # Recalculate tier
            score = peer.trust_score
            if score >= 0.85 and peer.threat_events == 0:
                peer.trust_level = PeerTrustLevel.CORE
            elif score >= 0.65:
                peer.trust_level = PeerTrustLevel.VERIFIED
            elif score >= 0.40:
                peer.trust_level = PeerTrustLevel.PROBATION
            else:
                peer.trust_level = PeerTrustLevel.UNTRUSTED


# Global Singleton for system-wide zero-trust federation
GLOBAL_FEDERATION_GUARD = FederationGuard()

import logging


class SecretSanitizingLogFilter(logging.Filter):
    """Logging filter that scrubs secrets and PII from all log records before emission."""

    def __init__(self, guard: FederationGuard | None = None):
        super().__init__()
        self.guard = guard or GLOBAL_FEDERATION_GUARD

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            clean_msg, _ = self.guard.scan_and_sanitize(record.msg, PIIAction.REDACT)
            record.msg = clean_msg
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    self.guard.scan_and_sanitize(str(a), PIIAction.REDACT)[0]
                    if isinstance(a, str)
                    else a
                    for a in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: (
                        self.guard.scan_and_sanitize(str(v), PIIAction.REDACT)[0]
                        if isinstance(v, str)
                        else v
                    )
                    for k, v in record.args.items()
                }
        return True


def get_safe_logger(name: str = "octoflow") -> logging.Logger:
    """Retrieve logger instance with automated PII and credential sanitization."""
    logger = logging.getLogger(name)
    has_filter = any(isinstance(f, SecretSanitizingLogFilter) for f in logger.filters)
    if not has_filter:
        logger.addFilter(SecretSanitizingLogFilter())
    return logger

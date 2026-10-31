"""Outbound Secret and PII Redactor for Cloud LLM Providers.

Scans outbound prompts sent to non-local providers, replacing secrets and credentials
with stable `[REDACTED:<type>]` placeholders to prevent accidental data exfiltration.

Local providers (Ollama, local mock) bypass outbound redaction to preserve raw local developer data.
"""

import re
from typing import NamedTuple


class OutboundRedactionRule(NamedTuple):
    name: str
    pattern: re.Pattern
    placeholder: str


# Specific secret patterns with word boundaries and negative lookbehaves
_COMPILED_RULES: list[OutboundRedactionRule] = [
    # 1. Anthropic API Keys (sk-ant-...) - checked before generic sk-...
    OutboundRedactionRule(
        name="ANTHROPIC_API_KEY",
        pattern=re.compile(r"\bsk-ant-[a-zA-Z0-9_\-]{20,80}\b"),
        placeholder="[REDACTED:ANTHROPIC_API_KEY]",
    ),
    # 2. OpenAI API Keys (sk-...)
    OutboundRedactionRule(
        name="OPENAI_API_KEY",
        pattern=re.compile(r"\bsk-(?:proj-)?[a-zA-Z0-9]{20,64}\b"),
        placeholder="[REDACTED:OPENAI_API_KEY]",
    ),
    # 3. GitHub Personal Access & OAuth Tokens (ghp_, gho_, ghu_, ghs_, ghr_)
    OutboundRedactionRule(
        name="GITHUB_TOKEN",
        pattern=re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,255}\b"),
        placeholder="[REDACTED:GITHUB_TOKEN]",
    ),
    # 4. AWS Access Key IDs (AKIA, ASIA, etc.)
    OutboundRedactionRule(
        name="AWS_ACCESS_KEY",
        pattern=re.compile(r"\b(?:AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}\b"),
        placeholder="[REDACTED:AWS_ACCESS_KEY]",
    ),
    # 5. AWS Secret Access Key expressions
    OutboundRedactionRule(
        name="AWS_SECRET_KEY",
        pattern=re.compile(
            r"(?i)(?:aws_secret_access_key|aws_secret_key)\s*[:=]\s*['\"][A-Za-z0-9/+=]{40}['\"]"
        ),
        placeholder="aws_secret_access_key='[REDACTED:AWS_SECRET_KEY]'",
    ),
    # 6. Google AI / Maps API Keys
    OutboundRedactionRule(
        name="GOOGLE_AI_KEY",
        pattern=re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
        placeholder="[REDACTED:GOOGLE_AI_KEY]",
    ),
    # 7. Stripe API Keys (sk_live_, rk_live_, etc.)
    OutboundRedactionRule(
        name="STRIPE_KEY",
        pattern=re.compile(r"\b(?:sk|rk)_(?:live|test)_[0-9a-zA-Z]{24,34}\b"),
        placeholder="[REDACTED:STRIPE_KEY]",
    ),
    # 8. Slack Tokens (xoxb-, xoxp-, etc.)
    OutboundRedactionRule(
        name="SLACK_TOKEN",
        pattern=re.compile(r"\bxox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}\b"),
        placeholder="[REDACTED:SLACK_TOKEN]",
    ),
    # 9. Private Key Blocks (RSA, EC, OPENSSH, etc.)
    OutboundRedactionRule(
        name="PRIVATE_KEY",
        pattern=re.compile(
            r"-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----[\s\S]+?-----END (?:[A-Z ]+)?PRIVATE KEY-----"
        ),
        placeholder="[REDACTED:PRIVATE_KEY]",
    ),
    # 10. Authorization / Bearer Tokens
    OutboundRedactionRule(
        name="BEARER_TOKEN",
        pattern=re.compile(r"(?i)\bBearer\s+[a-zA-Z0-9_\-\.]{20,}\b"),
        placeholder="Bearer [REDACTED:BEARER_TOKEN]",
    ),
    # 11. JSON Web Tokens (JWT)
    OutboundRedactionRule(
        name="JWT_TOKEN",
        pattern=re.compile(
            r"\beyJ[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{2,}\.[A-Za-z0-9\-_]{10,}\b"
        ),
        placeholder="[REDACTED:JWT_TOKEN]",
    ),
    # 12. Credit Card Numbers (13-16 digits with Luhn-like formatting)
    OutboundRedactionRule(
        name="CREDIT_CARD",
        pattern=re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),
        placeholder="[REDACTED:CREDIT_CARD]",
    ),
]


def redact_outbound_text(text: str) -> tuple[str, int]:
    """Scan and redact known secrets in text before outbound cloud transmission.

    Returns:
        tuple[redacted_text, count_of_redactions]
    """
    if not text or not isinstance(text, str):
        return text, 0

    redacted = text
    total_redactions = 0

    for rule in _COMPILED_RULES:
        # Don't re-match already redacted placeholders
        matches = list(rule.pattern.finditer(redacted))
        if matches:
            count = len(matches)
            total_redactions += count
            redacted = rule.pattern.sub(rule.placeholder, redacted)

    return redacted, total_redactions

# ADR 0001: Local-First Architecture and Privacy Boundary

## Status
Accepted

## Context
Developers using AI coding assistants frequently work on proprietary codebases, confidential customer data, and sensitive internal APIs. Traditional multi-agent harnesses operate as hosted cloud services that upload workspace code, environment variables, command outputs, and user prompts to centralized servers, introducing security, regulatory, and intellectual property risks.

## Decision
OctoFlow is designed with a strict **local-first, zero-telemetry** privacy architecture:
1. Default to local open-weights inference (Ollama running `qwen2.5-coder:7b`) requiring zero network egress.
2. Prohibit all external telemetry, analytics, and crash-reporting services; bind internal visualizer telemetry strictly to loopback (`127.0.0.1`).
3. Enforce loopback-only egress verification in CI via automated socket interception tests (`tests/test_egress_guard.py`).
4. When cloud providers (Anthropic, OpenAI) are explicitly chosen, scan and redact 12 categories of credentials and secrets before prompt transmission (`octoflow/federation.py`).

## Alternatives Considered
- **Cloud-Only Central Orchestrator:** Host the multi-agent graph on remote servers. Rejected due to security boundaries, data compliance (GDPR/HIPAA), and recurring hosting overhead.
- **Opt-Out Telemetry:** Collecting anonymous usage statistics by default with an opt-out flag. Rejected to establish unambiguous trust and guarantee zero phone-home behavior.

## Consequences
- **Positive:** Complete data sovereignty, offline functionality, airgapped environment support, zero SaaS subscription requirements, and elimination of credential leakage risks.
- **Negative:** Model quality depends on the user's local hardware (e.g., Apple Silicon or NVIDIA GPU). Local 7B models have lower reasoning capacity on complex architectural refactors than frontier cloud APIs.

## Evidence & References
- Policy: [`docs/PRIVACY.md`](../PRIVACY.md)
- CI Verification: [`tests/test_egress_guard.py`](../../tests/test_egress_guard.py)
- Commit: `12c300f` (P5.4 Outbound privacy guard & egress tests)

## What Would Change This Decision
If confidential computing enclaves with client-verifiable cryptographic hardware attestation become commoditized, enabling provably zero-knowledge cloud inference without client-side trust assumptions.

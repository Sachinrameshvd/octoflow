# ADR 0006: Local-Only Federation and Deferring Peer Networking

## Status
Accepted

## Context
Initial cephalopod design documents outlined a multi-machine federation architecture where independent developer laptops would discover each other over local networks and distribute arm tasks via peer-to-peer gossip protocols (`octoflow/federation.py`). However, opening network sockets and listening for incoming agent commands introduces severe attack surfaces, network discovery complexity, and potential data leakage across untrusted Wi-Fi environments.

## Decision
Retain the zero-trust PII and credential redactor as a core security utility while explicitly deferring cross-machine peer networking:
1. Promote the 14-rule regex redactor (`PII_RULES`, `FederationGuard`, `SecretSanitizingLogFilter`) to a **core security component** that scrubs all logs, bus events, and outbound cloud prompts.
2. Classify all peer networking prototypes (`PeerTrustLevel`, `FederationPeer`, `register_peer`) as **experimental, unused stubs** in [`docs/MODULE_TRIAGE.md`](../MODULE_TRIAGE.md).
3. Open zero incoming network listeners or gossip sockets.
4. Scale multi-octopus swarms (Consortium / Octopolis) purely in-process on the local host machine using loopback WebSockets and shared memory.

## Alternatives Considered
- **Implement mTLS Peer-to-Peer Networking Now:** Build authenticated TLS socket listeners for cross-machine swarms. Rejected as high risk and premature before single-machine stability and security audits were complete.
- **Delete `octoflow/federation.py` Entirely:** Remove the module. Rejected because the PII redactor embedded within it is a vital security requirement across the entire framework.

## Consequences
- **Positive:** Zero open network ports, zero remote attack vectors, and hardened credential scrubbing across all logs and cloud prompts.
- **Negative:** Multi-octopus scaling is bounded by single-machine CPU/RAM resources (up to 64 arms on a single 32 GB workstation).

## Evidence & References
- Triage Classification: [`docs/MODULE_TRIAGE.md`](../MODULE_TRIAGE.md) (Section 4)
- Implementation: [`octoflow/federation.py`](../../octoflow/federation.py) (`PII_RULES`, `GLOBAL_FEDERATION_GUARD`)
- Verification: [`tests/test_audit_eject_federation.py`](../../tests/test_audit_eject_federation.py)
- Commit: `524f0c9` (P2.6 Module triage and federation boundary)

## What Would Change This Decision
When an explicit enterprise requirement emerges for distributed cluster execution, backed by formal threat modeling, audited mutual TLS certificate exchange, and end-to-end payload encryption.

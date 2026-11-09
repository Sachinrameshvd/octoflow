# ADR 0007: Dynamic Swarm Scaling Default & Morphology Auto-Detection (D6)

## Status
Accepted

## Context
OctoFlow supports three operational swarm tiers: Solo (1 octopus, 8 arms), Triad (3 octopuses, 24 arms), and Octopolis (8 octopuses, 64 arms). Forcing developers to manually specify arm counts and morphology rosters on every command creates friction. Conversely, launching 64 arms for simple bug-fixing tasks exhausts system RAM and wastes LLM concurrency limits.

## Decision
Implement intelligent morphology auto-detection with a conservative Solo default (Decision D6):
1. Analyze user objective text via `detect_morphology_from_objective()`:
   - Goals containing algorithmic tasks, isolated scripts, or single-file fixes resolve to `SOFTWARE_DEV` (Solo, 8 arms).
   - Goals explicitly specifying multi-service architectures ("frontend and backend", "microservices", "fullstack") resolve to `FULLSTACK_AI` or `AIML_RESEARCH`.
2. Inspect available physical memory (`get_system_ram_gb()`) and scale cluster bounds elastically via `estimate_elastic_octopus_count()`, preventing out-of-memory crashes on resource-constrained laptops.
3. Default to Solo (8 arms) unless the user explicitly passes `--octos N` or `--morphology`.

## Alternatives Considered
- **Fixed Single Morphology:** Always run 8 arms regardless of goal scope. Rejected because complex full-stack projects require decoupled specialist groups (Database vs Backend vs Frontend).
- **Mandatory Interactive Prompting:** Ask the user how many agents to spawn before each run. Rejected because it breaks CI/CD scripting and slows down the developer inner loop.

## Consequences
- **Positive:** Zero-config first runs; lightweight resource footprint by default; seamless scaling on high-end hardware for massive projects.
- **Negative:** Keyword-based goal classification can occasionally misclassify nuanced multi-sentence prompts.

## Evidence & References
- Implementation: [`octoflow/consortium.py`](../../octoflow/consortium.py) (`detect_morphology_from_objective`, `estimate_elastic_octopus_count`)
- Verification: [`tests/test_consortium.py`](../../tests/test_consortium.py)
- Commit: `a64b971` (P2.3 Settings, configuration, and morphology detection)

## What Would Change This Decision
If heuristic prompt classification yields unacceptable false-positive scaling rates, prompting a switch to a small local embedding classifier.

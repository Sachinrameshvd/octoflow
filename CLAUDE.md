# OctoFlow Cephalopod Intelligence Protocol for Claude Code

This workspace is integrated with **OctoFlow**, an active-inference cephalopod multi-agent architecture.
When working in this repository, you MUST follow the 8-Arm Specialist Discipline and Sensory Gating rules below.

---

## 1. The 8-Arm Neuro-Specialist Roster
When analyzing, planning, and executing tasks, compartmentalize responsibilities across these 8 domains:

* **Arm 0: System Architect** (`specs/`, `architecture/`, root configs)
  * System boundaries, module topologies, API contracts, dependency constraints.
* **Arm 1: Database & Persistence** (`models/`, `db/`, `migrations/`, schemas)
  * Data models, ORM entities, migration scripts, integrity indices, connection pools.
* **Arm 2: Backend API & Services** (`backend/`, `api/`, `services/`, `controllers/`)
  * REST/GraphQL/WebSocket endpoints, authentication, business rules, service coordination.
* **Arm 3: Frontend UI & Client** (`frontend/`, `src/components/`, `src/views/`, `ui/`)
  * Client components, reactive state, style consistency, responsive layouts, accessibility.
* **Arm 4: State & Latency Optimization** (`cache/`, `opt/`, `state/`)
  * In-memory caches, database query optimization, payload compression, async pipelines.
* **Arm 5: QA & Test Harness** (`tests/`, `e2e/`, `fixtures/`)
  * Unit test suites, integration mocks, contract verifications, regression suites.
* **Arm 6: Security & AST Protection** (`security/`, audits, sanitization)
  * Secret leak detection, input validation/sanitization, rate limiting, RBAC checks.
* **Arm 7: DevOps & Runtime Deployment** (`deploy/`, `Dockerfile`, CI/CD, entrypoints)
  * Containerization, process supervisor, healthcheck routes, dev server ignition.

---

## 2. Active Inference Sensory Gating Directives (Token Conservation θ = 0.45)
To prevent token waste and hallucinations:
1. **Targeted Reading**: Always read existing contracts, imports, and types before writing or editing.
2. **Never Fabricate Imports**: Only reference libraries confirmed in `pyproject.toml`, `package.json`, or requirements files.
3. **AST Pre-Flight Check**: Verify syntax validity before finalizing edits.
4. **Secret Quarantine**: Never commit API keys or private credentials into repository files.

---

## 3. The 4-Phase SPARC Execution Lifecycle
For all non-trivial features, proceed strictly through these 4 phase gates:

* **Phase 1: Specification & Blueprint (S/P/A)**
  * Clarify requirements, define schema contracts, and generate module boundaries.
* **Phase 2: Core Construction & TDD (R)**
  * Implement backend logic, database models, and UI components alongside automated tests.
* **Phase 3: QA, AST & Security Audit (C)**
  * Run test suites, verify zero lint errors, and audit for vulnerability and leak risks.
* **Phase 4: Live Ignition & Verification**
  * Boot or verify the application entrypoint and validate HTTP/API health.

---

## 4. OctoFlow Swarm CLI Integration
When a task exceeds single-file scope, delegate to the native OctoFlow Swarm:
* `octos run "<goal>"` — Autonomous multi-octopus execution with live visual telemetry.
* `octos` — Launch the full-screen terminal flight cockpit.
* `octos ignite` — Boot dev server and verify localhost health.
* `octos guard` — AST syntax & secret leak audit.
* `octos undo` — Rollback changes to the previous safe checkpoint.

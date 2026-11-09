# Contributing to OctoFlow

Thank you for contributing to OctoFlow! We are building a local-first, truthful autonomous coding swarm designed to spend tokens only when necessary and keep proprietary code on your device.

Before contributing, please read our [Code of Conduct](CODE_OF_CONDUCT.md), [Governance Model](GOVERNANCE.md), [Support Guide](SUPPORT.md), and [Security Policy](SECURITY.md).

---

## 1. Development Setup

OctoFlow requires **Python >= 3.10**. Initialize your virtual environment and install locked development dependencies:

```bash
make setup
```

This installs base and development dependencies from `requirements.lock` and links OctoFlow in editable mode without overriding locked versions.

### Recommended Local Dependencies
- Local model inference: [Ollama](https://ollama.ai) with `qwen2.5-coder:7b` (`ollama pull qwen2.5-coder:7b`).
- Node.js >= 20 (for WebGL 3D visualizer development).

---

## 2. Running Tests & Markers

OctoFlow uses `pytest` with markers to categorize tests by speed and external network/daemon requirements:

```bash
# Fast in-memory unit tests (recommended during local feature development)
make test-fast

# Full test suite excluding live LLM daemon tests (runs in CI)
pytest tests/ -m "not live"

# Live provider integration tests (requires local Ollama daemon running)
pytest tests/ -m "live"

# Full test suite with coverage report
make test
```

### Key Test Suites
- Documentation & Reference Integrity: `pytest tests/test_docs_checker.py tests/test_gen_reference.py`
- Typography & Glyph Standards: `pytest tests/test_glyph_policy.py`
- Error Taxonomy & Exit Codes: `pytest tests/test_errors_logging.py`
- Configuration & Migrations: `pytest tests/test_settings.py`
- Workspace Sandbox Security: `pytest tests/test_tools_security.py`

---

## 3. Code Style, Formatting & Type Safety

Before pushing or opening a pull request, verify linting, typechecks, and generated references:

```bash
# Linting & style checks (Ruff)
ruff check .

# Code formatting verification (Ruff)
ruff format --check .

# Auto-format files
ruff format .

# Gradual typechecking (mypy)
mypy

# Synchronize and check generated reference docs
make docs-ref
make check-docs-ref

# Verify internal links, anchors, error codes, and zero-emoji compliance
make check-docs
```

---

## 4. Branch Naming & Commit Conventions

### Branch Naming
All pull requests must be submitted from branches following the prefix pattern:
```text
octos/<feature-or-fix-name>
```
*Examples:* `octos/add-vllm-provider`, `octos/fix-pty-resize`, `octos/data-science-guild`

### Commit Message Format
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
```text
<type>(<scope>): <concise description in imperative mood>

[optional body explaining motivation and context]
```
*Allowed Types:*
- `feat`: New feature, arm capability, or user-facing command.
- `fix`: Bug fix or error resolution.
- `docs`: Documentation, field guide, or tutorial additions.
- `perf`: Performance, latency, or token-efficiency improvements.
- `refactor`: Internal code reorganization with no functional changes.
- `test`: Unit, characterization, or contract test additions.
- `chore`: Maintenance, dependencies, or CI workflow updates.

---

## 5. The Hard Rules (Non-Negotiable)

OctoFlow enforces six non-negotiable architectural constraints across all contributions:

1. **Non-Blocking Cockpit Loop:**
   The interactive cockpit runs at 20 FPS in `octoflow.cockpit`. Never use blocking `input()`, `sys.stdin.read()`, or `time.sleep()` in cockpit code paths. All keyboard input must be non-blocking.
2. **Zero-Emoji & Single-Width Glyphs:**
   Ambiguous or double-width emoji characters are strictly prohibited in CLI ribbons, logs, and documentation. All UI glyphs must be imported from `octoflow/glyphs.py` (`wcwidth <= 1`). Support `--ascii` fallback for 7-bit environments.
3. **Truthful Run Outcomes:**
   Never silently fall back to `MockLLMProvider` in live mode when a model fails or credentials are missing. Live runs with unconfigured providers must raise `ProviderExhaustedError`, report `[FAILED]`, and exit with code 2. Only runs that write valid code and pass verification report `COMPLETE`.
4. **Test Isolation & Zero Real Secrets:**
   Never commit or use real API keys in tests or fixtures. Use synthetic strings (`sk-mock-...`) and mocked provider cassettes. All outputs must pass through `redact_secrets()`.
5. **Dependency Discipline:**
   Adhere to [`docs/DEPENDENCY_POLICY.md`](docs/DEPENDENCY_POLICY.md). Rely on the Python standard library first. If a new dependency is essential, it must use an OSI-approved permissive license (no copyleft/GPL), specify lower bounds only in `pyproject.toml`, and update `requirements.lock` via `make lock`.
6. **No Speculative Abstractions:**
   Implement concrete functionality tested against realistic tasks. Avoid unneeded wrapper layers.

---

## 6. How to Extend OctoFlow

### Adding a Custom LLM Provider
To add a new inference provider (e.g. vLLM, LM Studio, Mistral):
1. Subclass `BaseLLMProvider` in `octoflow/provider.py` (or a dedicated provider module).
2. Implement `name`, `generate(...)`, `count_tokens(...)`, and `is_available()`.
3. Register the provider in `CascadePoolLLMProvider`.
4. Validate compliance using `ProviderContractSuite` in `tests/contract/test_provider_contract.py`.
5. Consult the tutorial: [`docs/tutorials/05-adding-a-custom-provider.md`](docs/tutorials/05-adding-a-custom-provider.md) and [`docs/extending/providers.md`](docs/extending/providers.md).

### Adding a Custom Specialist Guild
To define a custom 8-arm specialist roster:
1. Create a JSON specification conforming to `GuildSpec` (8 arms, colors, tool permissions, and domain focus).
2. Validate with: `octoflow guild validate <path/to/guild.json>`.
3. Place in `~/.octoflow/guilds/<name>.json` or `.octoflow/guilds/<name>.json`.
4. Consult the tutorial: [`docs/tutorials/04-building-with-a-custom-guild.md`](docs/tutorials/04-building-with-a-custom-guild.md) and [`docs/extending/guilds.md`](docs/extending/guilds.md).

---

## 7. Proposing Larger Changes

Before embarking on significant structural changes (new morphologies, major tool refactorings, or configuration redesigns), please open a **GitHub Discussion** or **Issue** to discuss the concept.

Substantial architectural changes must include an **Architectural Decision Record (ADR)** in [`docs/adr/`](docs/adr/) explaining the context, alternatives considered, and consequences.

---

## 8. Review Turnaround Expectations (Solo Maintainer Reality)

OctoFlow is maintained by an open-source maintainer with community collaboration:
- Pull requests are reviewed thoroughly for test coverage, security boundaries, and adherence to the Hard Rules.
- Expected initial response and triage time is **3 business days**; comprehensive code review turnaround is **5 to 7 business days**.
- To expedite review, keep pull requests focused on a single change and verify that all automated checks in `.github/PULL_REQUEST_TEMPLATE.md` are checked.
- Maintainers follow our standard [Maintainer Operations Manual](docs/MAINTAINING.md) and use pre-drafted [Saved Replies](docs/saved_replies.md).

---

## 9. Contributor Ladder & Leadership

OctoFlow offers a structured path for sustained community involvement:
1. **Contributor**: Submits documentation fixes, bug reports, custom guilds, or seed issue PRs.
2. **Triager**: Helps reproduce issues, label PRs, and guide new contributors.
3. **Core Maintainer**: Reviews architecture changes, co-signs releases, and stewards core moats.

For full details on rights and requirements, see [`GOVERNANCE.md`](GOVERNANCE.md) and [`docs/MAINTAINING.md`](docs/MAINTAINING.md).

---

## 10. Cutting a Release

For repository owners and maintainers cutting a public release, follow the step-by-step procedure and PyPI Trusted Publishing setup in [`docs/RELEASING.md`](docs/RELEASING.md) and [`docs/MAINTAINING.md`](docs/MAINTAINING.md).

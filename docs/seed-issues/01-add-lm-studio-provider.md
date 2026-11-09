# Add LM Studio Local LLM Provider

**Difficulty:** Good First Issue  
**Labels:** `enhancement`, `provider`, `good first issue`  
**Mentoring Pointer:** Look at `OllamaLLMProvider` in [`octoflow/provider.py`](../../octoflow/provider.py) and the provider extension tutorial [`docs/tutorials/05-adding-a-custom-provider.md`](../tutorials/05-adding-a-custom-provider.md).

---

## Context
OctoFlow is local-first and supports Ollama out-of-the-box. Many developers also use [LM Studio](https://lmstudio.ai/) to run open-weight GGUF models locally on Apple Silicon and CUDA GPUs via its local HTTP server on `http://localhost:1234/v1`.

Currently, users must configure LM Studio as a generic OpenAI endpoint with a dummy API key. Adding a dedicated, first-class `LMStudioLLMProvider` will allow automatic endpoint discovery, health checks via `octoflow doctor`, and seamless model selection.

---

## Objectives & Requirements
1. Implement `LMStudioLLMProvider` in [`octoflow/provider.py`](../../octoflow/provider.py) subclassing `BaseLLMProvider`.
2. Default the base URL to `http://localhost:1234/v1` (configurable via `OCTOFLOW_LMSTUDIO_HOST` or settings).
3. Implement `generate(...)`, `count_tokens(...)`, and `is_available()`.
4. Register the provider in `CascadePoolLLMProvider` and add CLI flag `--model lmstudio` support in [`octoflow/commands/run.py`](../../octoflow/commands/run.py).
5. Add diagnostic check in [`octoflow/commands/doctor.py`](../../octoflow/commands/doctor.py) checking if port 1234 is reachable.

---

## Files to Touch
- [`octoflow/provider.py`](../../octoflow/provider.py): Add `LMStudioLLMProvider` implementation.
- [`octoflow/config.py`](../../octoflow/config.py): Add `ProviderType.LMSTUDIO` enum entry.
- [`octoflow/commands/doctor.py`](../../octoflow/commands/doctor.py): Add LM Studio diagnostic health ping.
- [`tests/contract/provider_contract.py`](../../tests/contract/provider_contract.py): Add `LMStudioLLMProvider` to the provider contract test matrix.

---

## Acceptance Criteria
- [ ] `LMStudioLLMProvider` passes all contract checks in `tests/contract/provider_contract.py`.
- [ ] Running `octoflow doctor` detects LM Studio status when running locally on port 1234.
- [ ] Running `octoflow run "x" --model lmstudio --dry-run` resolves without configuration errors.
- [ ] No external dependencies added (uses existing `httpx`).
- [ ] All unit tests pass with `pytest`.

# Frequently Asked Questions (FAQ)

Frequently asked questions about OctoFlow architecture, privacy boundaries, supported models, and operational workflows.

---

## Table of Contents

1. [Why an octopus?](#1-why-an-octopus)
2. [What is the gate in plain words?](#2-what-is-the-gate-in-plain-words)
3. [Is my code sent anywhere?](#3-is-my-code-sent-anywhere)
4. [Why did my run say DRY-RUN?](#4-why-did-my-run-say-dry-run)
5. [Which models work with OctoFlow?](#5-which-models-work-with-octoflow)
6. [How much does OctoFlow cost?](#6-how-much-does-octoflow-cost)
7. [Does OctoFlow work on Windows?](#7-does-octoflow-work-on-windows)
8. [How do I report a bug or issue?](#8-how-do-i-report-a-bug-or-issue)

---

## 1. Why an octopus?

Two-thirds of an octopus's ~500 million neurons reside in its eight arms rather than its central brain. This unique biological morphology enables each arm to explore, taste, touch, and manipulate objects semi-autonomously without burdening central cognition. The central brain (*Supraesophageal Ganglion*) steps in only to establish high-level goals or resolve unexpected novel situations.

OctoFlow adapts this biological division of labor to multi-agent software engineering: 8 specialized agents (System Architect, Database, Backend, Frontend, State, QA, Security, DevOps) handle routine execution locally, while the central planner coordinates overarching task graphs and arbitrates unexpected failures.

---

## 2. What is the gate in plain words?

The **Gate** is an automated change detector that runs on every arm.

Whenever an arm executes a tool (for example, writing a file or running a test), the gate compares the actual result with what was expected. If the result matches expectations (e.g., the file was written without error or the test passed cleanly), the calculated "surprise" is low ($\Delta S \le \theta$). The arm treats this as a **routine reflex** and proceeds to its next subtask locally in silence, without spending tokens to send a verbose status report to the central conductor.

Only when something unexpected occurs—such as a syntax error, test failure, or permission crash—does the surprise exceed the threshold ($\Delta S > \theta$). The arm then **escalates** to the central conductor with focused error context, triggering replanning. On code generation tasks, this change-driven reflex mechanism avoids 15% to 25% of redundant prompt tokens.

---

## 3. Is my code sent anywhere?

**No, by default nothing leaves your machine.**

* **Local-First Default:** When running with local models via Ollama (`--model ollama`), 100% of inference and tool execution occurs strictly on your host machine.
* **Zero Telemetry:** OctoFlow contains **zero telemetry services, zero analytics, and zero crash reporters**. It never phones home.
* **Enforced in CI:** Network isolation is verified in continuous integration via automated socket blocking tests ([`tests/test_egress_guard.py`](../tests/test_egress_guard.py)), ensuring zero non-loopback network calls during missions, diagnostics, and reporting.
* **Outbound Secret Scrubbing:** If you explicitly choose to connect to a cloud provider (such as Anthropic or OpenAI), OctoFlow scans all prompt payloads and redacts 12 categories of secrets (API keys, AWS credentials, private keys, bearer tokens) before transmission.

For complete data governance details, see [`docs/PRIVACY.md`](PRIVACY.md).

---

## 4. Why did my run say DRY-RUN?

A run displays `[DRY-RUN: no project files written]` when either:
1. You explicitly passed the `--dry-run` flag on the command line.
2. The model provider was set to `--model mock` or `OCTOFLOW_MODEL_PROVIDER=mock`.

In DRY-RUN mode, the swarm simulates the entire planning and active-inference loop using deterministic mock providers. To protect your working tree, all generated files are redirected to `.octoflow/dry-run/`, leaving your actual tracked repository files untouched.

Under Decision D1, OctoFlow **never** silently falls back to DRY-RUN mode in live environments. If real credentials are missing or an API call fails in LIVE mode, OctoFlow immediately reports `[FAILED]` with exit code `2`.

---

## 5. Which models work with OctoFlow?

OctoFlow supports both local open-weight models and cloud frontier APIs:

* **Recommended Local Model:** `qwen2.5-coder:7b` (or `qwen2.5-coder:14b` on machines with $\ge 32\text{ GB}$ RAM) via [Ollama](https://ollama.ai).
* **Cloud Frontier Models:**
  * Anthropic: Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
  * OpenAI: GPT-4o (`gpt-4o`)
  * Google: Gemini 1.5 Pro
* **Custom Backends:** Any OpenAI-compatible local server (LM Studio, vLLM, LocalAI) can be integrated in ~60 lines of Python. See [Tutorial 5: Adding a Custom Provider](tutorials/05-adding-a-custom-provider.md).

---

## 6. How much does OctoFlow cost?

* **Local Models (Ollama):** **$0.00 (Completely Free)**. All token processing runs on your local CPU or GPU.
* **Cloud Models (Anthropic, OpenAI):** Billed directly by your model provider according to their standard API token pricing. OctoFlow charges zero markup or subscription fees.
* **Cost Visibility:** Every mission produces a truthful token receipt (`octoflow receipt`) detailing exact input tokens, output tokens, and local tokens avoided by the gate. You can also configure strict spending ceilings via `--budget <dollars>` or `--max-tokens <n>`.

---

## 7. Does OctoFlow work on Windows?

**Yes.** OctoFlow is cross-platform:
* **WSL2 (Recommended):** Ubuntu on WSL2 provides a native Linux terminal environment identical to production deployment.
* **Native PowerShell / CMD:** OctoFlow runs directly on Python 3.10+ on Windows. Path validation automatically normalizes Windows backslashes (`\`) into POSIX slashes (`/`), and terminal glyphs fall back cleanly to 7-bit ASCII when ANSI Unicode support is disabled.

---

## 8. How do I report a bug or issue?

OctoFlow provides an automated diagnostics command that formats an issue summary with all credentials scrubbed:

```bash
octoflow bugreport
```

This command inspects your operating system, Python runtime, Git status, doctor findings, and recent log snippets. It automatically masks all API keys and secrets, printing clean Markdown ready to paste into a GitHub issue.


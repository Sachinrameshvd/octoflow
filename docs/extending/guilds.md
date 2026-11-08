# Extending OctoFlow: Custom 8-Arm Specialist Guilds

This guide walks through creating, validating, managing, and running custom 8-arm specialist guilds in OctoFlow (e.g. for **Data Science & ML**, **Embedded Systems & Firmware**, **Web3 & Smart Contracts**, **Game Development**, or **Enterprise DevOps**).

---

## 1. Overview & Architecture

OctoFlow models software engineering and AI research on the decentralized neurobiology of *Octopus vulgaris*: **exactly 8 peripheral brachial arm ganglia** operating in parallel under sensory surprise gating ($\Delta S > \theta$) coordinated by the supraesophageal center.

Rather than hardcoding arm roles in Python code, OctoFlow enables developers to author declarative, safe, JSON-based specialist rosters called **Guilds**.

### Key Architectural Principles
- **Strictly 8 Arms per Octopus**: Biological fidelity requires each octopus to operate with exactly 8 peripheral arms (indexed `0` through `7`). Guilds with fewer or more arms are rejected.
- **Zero Code Execution**: Guild files are pure JSON. No arbitrary Python execution, eval, or unvetted imports are permitted.
- **RFC 6901 JSON Pointer Validation**: Validation errors report exact JSON pointer paths (e.g. `/arms/3/color`, `/arms/0/system_prompt`, `/arms`).
- **Global ToolPolicy Clamping**: Arms specify tools, but the active system `ToolPolicy` strictly gates permissions. If a guild requests a tool denied by policy (e.g. `bash`), the tool is dropped and a warning is logged without crashing.
- **Dynamic 3D Visualizer Palettes**: The 3D connectome visualizer and HUD take their colors and arm identities dynamically from the guild's telemetry payload.

---

## 2. Guild Schema Specification

Guilds are defined as JSON documents conforming to `GuildSpec` and `ArmSpec` (`octoflow.guild`):

```json
{
  "name": "data_science",
  "description": "End-to-end Data Science & Machine Learning Guild",
  "arms": [
    {
      "id": 0,
      "role": "data_ingestion",
      "focus": "Data Ingestion & Cleaning: CSV/Parquet loading, schema verification, and null imputation.",
      "color": "#00F0FF",
      "system_prompt": "You are Arm 0 (Data Ingestion). Specialize in dataset ingestion and schema validation.",
      "tools": ["read_file", "write_file", "run_command", "list_dir"],
      "file_scope": ["data/", "datasets/", "ingestion/"]
    }
  ]
}
```

### Top-Level Fields (`GuildSpec`)

| Field | Type | Validation Rule | Description |
|:---|:---|:---|:---|
| `name` | `string` | Regex `^[a-zA-Z0-9_-]+$` | Unique identifier used with `octoflow run --guild <name>`. |
| `description` | `string` | Non-empty string | Human-readable description displayed in `guild list`. |
| `arms` | `list[ArmSpec]` | Exactly 8 items | Sequential arm configurations with unique IDs `0` through `7`. |

### Arm Fields (`ArmSpec`)

| Field | Type | Validation Rule | Description |
|:---|:---|:---|:---|
| `id` | `integer` | `0 <= id <= 7` | Unique numeric arm index (0 to 7). |
| `role` | `string` | Non-empty string | Machine-readable role identifier (e.g., `data_ingestion`). |
| `focus` | `string` | Non-empty string | Specialized focus domain and responsibilities. |
| `color` | `string` | Regex `^#[0-9a-fA-F]{6}$` | 6-digit hex color for 3D connectome visualizer & terminal UI. |
| `system_prompt` | `string` | Length $\le 2000$, no null bytes | Specialized instructions steered to this arm's LLM agent. |
| `tools` | `list[string]` | Subset of known tools | Permitted tools: `read_file`, `write_file`, `run_command`, `list_dir`, `mark_quiescent`. |
| `file_scope` | `list[string]` | List of paths/globs | Directory paths steered to this arm during decomposition. |

---

## 3. Search Precedence Order

When OctoFlow resolves a guild name (e.g. `octoflow run --guild data_science`), it searches locations in strict order:

```
1. Project Directory   --> .octoflow/guilds/<name>.json   (Highest Priority)
2. User Home Directory --> ~/.octoflow/guilds/<name>.json (Medium Priority)
3. Built-In Guilds     --> Built-in definitions           (Fallback)
```

- **Project Guilds**: Allow teams to check specialized rosters directly into repository version control (`.octoflow/guilds/`). Project guilds override user guilds and built-ins.
- **User Guilds**: Store personal specialist rosters in `~/.octoflow/guilds/` shared across local workspaces.
- **Built-In Guilds**: Default fallback rosters: `software_dev`, `aiml_research`, and `fullstack_ai`.

> **Security Note:** Path traversal sequences (such as `..` or absolute paths `/etc/...`) in guild names are rejected with a `ValueError`.

---

## 4. Safety Constraints & ToolPolicy Clamping

1. **System Prompt Bounding**: System prompts loaded from JSON are treated as untrusted user content. OctoFlow verifies prompts do not exceed 2000 characters and contain no null bytes (`\x00`).
2. **Global Tool Policy Intersection**: An arm cannot grant itself permissions beyond what the global `ToolPolicy` allows. When converting a guild to a runtime roster:
   ```python
   clamped_tools = clamp_arm_tools(arm.tools, arm.id, policy=active_policy)
   ```
   If an arm requests a tool denied by policy (e.g., `bash` or `run_command` in restricted sandboxes), the tool is dropped and a warning is logged:
   ```
   WARNING: Tool 'bash' denied by global policy for arm 0; clamped.
   ```
   Execution proceeds safely without crashing.

---

## 5. CLI Management Commands

OctoFlow provides first-class CLI commands for listing, validating, inspecting, and exporting guilds:

### List All Available Guilds
```bash
octoflow guild list
```
Displays all discovered guilds with their source (`Built-In`, `User`, `Project`), arm counts, and descriptions.

### Validate a Guild JSON File
```bash
octoflow guild validate examples/guilds/data_science.json
```
- Returns exit code `0` on success.
- Returns exit code `1` with RFC 6901 JSON pointer paths on failure:
  ```
  ✘ Validation failed for 'my_guild.json':
    • /arms: Guild must define exactly 8 arms, found 7
    • /arms/3/color: Color must be a 6-digit hex string matching '^#[0-9a-fA-F]{6}$'
  ```

### Inspect a Guild Roster
```bash
octoflow guild show data_science
# Or inspect a file directly:
octoflow guild show path/to/custom_guild.json
```
Renders a formatted Rich table showing all 8 arms, roles, colors, tools, and domain scopes.

### Export a Template
```bash
octoflow guild export my_guild
```
Exports a scaffolded 8-arm template to `~/.octoflow/guilds/my_guild.json` ready for customization.

### Run with a Custom Guild
```bash
octoflow run --guild data_science "Train a fraud detection classifier with ROC-AUC evaluation"
```

---

## 6. Complete Showcase Example: `data_science.json`

The flagship Data Science & ML guild is provided at `examples/guilds/data_science.json`:

```json
{
  "name": "data_science",
  "description": "End-to-end Data Science & Machine Learning Guild (Ingestion, EDA, Features, Modeling, HPO, Eval, XAI, Reporting)",
  "arms": [
    {
      "id": 0,
      "role": "data_ingestion",
      "focus": "Data Ingestion & Cleaning: CSV/Parquet loading, schema verification, and null imputation.",
      "color": "#00F0FF",
      "system_prompt": "You are Arm 0 (Data Ingestion). Specialize in dataset ingestion, validating input schemas, handling missing values, and formatting tabular and tensor pipelines.",
      "tools": ["read_file", "write_file", "run_command", "list_dir"],
      "file_scope": ["data/", "datasets/", "ingestion/"]
    },
    {
      "id": 1,
      "role": "eda_profiling",
      "focus": "Exploratory Data Analysis: Descriptive statistics, correlation matrices, and distribution profiling.",
      "color": "#A855F7",
      "system_prompt": "You are Arm 1 (EDA Profiling). Specialize in exploratory data analysis, summary statistics, correlation profiling, and anomaly discovery.",
      "tools": ["read_file", "write_file", "run_command", "list_dir"],
      "file_scope": ["eda/", "notebooks/", "profiles/"]
    },
    {
      "id": 2,
      "role": "feature_engineering",
      "focus": "Feature Engineering & Transforms: Categorical encoding, standard scaling, and feature interactions.",
      "color": "#3B82F6",
      "system_prompt": "You are Arm 2 (Feature Engineering). Specialize in feature extraction, column transformers, scaling, and dimensionality reduction pipelines.",
      "tools": ["read_file", "write_file", "run_command", "list_dir"],
      "file_scope": ["features/", "transforms/"]
    },
    {
      "id": 3,
      "role": "model_training",
      "focus": "Baseline & Advanced Modeling: Estimator selection, PyTorch/LightGBM training, and cross-validation.",
      "color": "#EC4899",
      "system_prompt": "You are Arm 3 (Model Training). Specialize in model selection, training loops, baseline benchmarking, and cross-validation folding.",
      "tools": ["read_file", "write_file", "run_command", "list_dir"],
      "file_scope": ["models/", "training/", "checkpoints/"]
    },
    {
      "id": 4,
      "role": "hyperparameter_tuning",
      "focus": "HPO & Model Calibration: Hyperparameter search, learning rate optimization, and probability calibration.",
      "color": "#10B981",
      "system_prompt": "You are Arm 4 (Hyperparameter Tuning). Specialize in search spaces, Bayesian optimization, learning rate schedules, and probability calibration.",
      "tools": ["read_file", "write_file", "run_command", "list_dir"],
      "file_scope": ["tuning/", "experiments/"]
    },
    {
      "id": 5,
      "role": "evaluation_metrics",
      "focus": "Model Diagnostics & Metrics: Precision, recall, ROC-AUC, regression losses, and confusion matrices.",
      "color": "#EF4444",
      "system_prompt": "You are Arm 5 (Evaluation & Metrics). Specialize in quantitative scoring, ROC-AUC, PR curves, regression metrics, and confusion matrix auditing.",
      "tools": ["read_file", "write_file", "run_command", "list_dir"],
      "file_scope": ["eval/", "metrics/", "benchmarks/"]
    },
    {
      "id": 6,
      "role": "explainability_governance",
      "focus": "Explainability & Safety: SHAP feature attributions, fairness audits, and model governance cards.",
      "color": "#F59E0B",
      "system_prompt": "You are Arm 6 (Explainability & Governance). Specialize in SHAP values, feature importance, bias auditing, and model card documentation.",
      "tools": ["read_file", "write_file", "run_command", "list_dir"],
      "file_scope": ["explainability/", "governance/", "model_card.md"]
    },
    {
      "id": 7,
      "role": "pipeline_deployment",
      "focus": "Serving & Pipeline Deployment: FastAPI inference endpoints, ONNX export, and pipeline lockfiles.",
      "color": "#EAB308",
      "system_prompt": "You are Arm 7 (Pipeline Deployment). Specialize in packaging trained artifacts, export to ONNX runtime, FastAPI inference endpoints, and Docker containerization.",
      "tools": ["read_file", "write_file", "run_command", "list_dir"],
      "file_scope": ["serve/", "api/", "Dockerfile", "README.md"]
    }
  ]
}
```

---

## 7. Visualizer Integration

When OctoFlow launches with a custom guild:
1. `SupraesophagealConductor` emits an initial `SWARM_INIT` telemetry packet containing the active guild name, arm names, and the 8 hex colors:
   ```json
   {
     "event_type": "SWARM_INIT",
     "payload": {
       "guild": "data_science",
       "arm_colors": ["#00F0FF", "#A855F7", "#3B82F6", "#EC4899", "#10B981", "#EF4444", "#F59E0B", "#EAB308"],
       "arms": [...]
     }
   }
   ```
2. The 3D connectome visualizer receives this packet over `ws://127.0.0.1:8088/ws/telemetry` and calls `updateArmProfilesFromGuild()`.
3. 3D nodes, particle action potentials, and HUD badges dynamically adapt to the custom guild's palette and names, with fallback to default theme tokens if no guild is loaded.

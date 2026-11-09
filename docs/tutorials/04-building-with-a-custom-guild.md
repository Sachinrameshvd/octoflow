# Tutorial 4: Building with a Custom 8-Arm Guild

**Estimated Duration:** 8 minutes  
**Verification:** Verified on 2026-11-09, OctoFlow v0.2.0  

This tutorial demonstrates how to define, validate, and execute an autonomous mission using a declarative, custom 8-arm specialist roster without writing any Python code.

---

## What is a Guild?

In OctoFlow, a **Guild** defines the specialized roles, system prompts, colors, and assigned tools for the 8 peripheral brachial arms. While OctoFlow provides built-in rosters (`software_dev`, `fullstack_ai`, `aiml_research`), you can define domain-tailored rosters (e.g. Data Science, Rust Systems, Game Dev) as safe JSON specifications.

---

## Step 1: Inspect Available Guilds

List discovered built-in, user, and project guilds:

```bash
octoflow guild list
```

### Expected Output

```text
╭──────────────────────── Discovered OctoFlow Guilds ────────────────────────╮
│ • software_dev (Built-in) - Standard 8-Arm Full-Stack Software Engineering │
│ • aiml_research (Built-in) - AI/ML Model Training & Curriculum Research    │
│ • fullstack_ai (Built-in) - Decoupled Frontend, Backend, and State Swarm   │
│ • data_science (Example) - Tabular ML, Feature Engineering & Analytics     │
╰────────────────────────────────────────────────────────────────────────────╯
```

---

## Step 2: Validate a Custom Guild File

Inspect and validate the schema of the example Data Science guild in `examples/guilds/data_science.json`:

```bash
octoflow guild validate examples/guilds/data_science.json
```

### Expected Output

```text
✔ Guild specification 'examples/guilds/data_science.json' is valid.
  • Name: data_science
  • Arms: 8 specialist roles defined
  • Tool Policy: 8/8 tools permitted under active workspace policy
```

*Note: If any required arm is missing or has an invalid hex color, `octoflow guild validate` outputs RFC 6901 JSON pointer diagnostics (e.g. `Field '/arms/3/color' must be a valid hex string`).*

---

## Step 3: Show Guild Roster Breakdown

View the 8 arm roles, colors, and capabilities defined in the guild:

```bash
octoflow guild show data_science
```

### Expected Output

```text
                      Guild Roster: data_science                      
┏━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Arm   ┃ Role                ┃ Color   ┃ Focus Domain               ┃
┡━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Arm 0 │ Lead Data Scientist │ #458588 │ Problem Framing & Metrics  │
│ Arm 1 │ Data Ingestion      │ #b16286 │ ETL & Pandas Pipelines     │
│ Arm 2 │ Feature Engineer    │ #689d6a │ Feature Transformations    │
│ Arm 3 │ Model Architect     │ #d79921 │ Scikit-Learn & LightGBM    │
│ Arm 4 │ Validation Engineer │ #cc241d │ Cross-Validation & Drift   │
│ Arm 5 │ Evaluation & QA     │ #98971a │ Metric Tests & Invariants  │
│ Arm 6 │ Optimization & Fast │ #d65d0e │ Quantization & Inference   │
│ Arm 7 │ Documentation       │ #a89984 │ Model Cards & README       │
└━━━━━━━┴━━━━━━━━━━━━━━━━━━━━━┴━━━━━━━━━┴━━━━━━━━━━━━━━━━━━━━━━━━━━━━┘
```

---

## Step 4: Execute a Swarm Mission Using the Custom Guild

Run a mission instructing the specialized Data Science guild to build a churn classification pipeline:

```bash
octoflow run "Build a customer churn predictor with ROC-AUC evaluation and tests" --guild data_science --dry-run
```

The 3D connectome visualizer and terminal HUD automatically adopt the custom arm names and hex colors defined in `data_science.json`.

---

## Next Steps

- Learn how to connect external LLM providers: [Tutorial 5: Adding a Custom Provider](05-adding-a-custom-provider.md)
- Complete guild authoring specification: [docs/extending/guilds.md](../extending/guilds.md)

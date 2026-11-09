# Add Built-in Data Science & Analytics Specialist Guild Preset

**Difficulty:** Good First Issue  
**Labels:** `enhancement`, `guild`, `good first issue`  
**Mentoring Pointer:** Check out [`octoflow/guild.py`](../../octoflow/guild.py) and the custom guild tutorial [`docs/tutorials/04-building-with-a-custom-guild.md`](../tutorials/04-building-with-a-custom-guild.md).

---

## Context
OctoFlow uses an 8-arm specialist guild model. By default, the `SOFTWARE_DEV` guild defines roles for Full-Stack Web and API engineering (Database, Backend API, Frontend UI, State, QA, Security, DevOps).

For data scientists, machine learning engineers, and analysts, these web development roles are not ideal. We want to provide a built-in `DATA_SCIENCE` guild specification that configures arms for exploratory data analysis, data cleaning, feature engineering, model training, and metrics reporting.

---

## Objectives & Requirements
1. Define a new built-in guild specification in [`octoflow/guild.py`](../../octoflow/guild.py) named `DATA_SCIENCE` (or as a JSON template in `octoflow/guilds/data_science.json`).
2. The guild must define exactly 8 specialist arms conforming to `GuildSpec`:
   - Arm 0: Conductor (Orchestration & Goal Decomposition)
   - Arm 1: Data Ingestion & Schema Extraction (Pandas, SQL, Parquet)
   - Arm 2: Data Cleaning & Preprocessing (Imputation, Outliers, Normalization)
   - Arm 3: Exploratory Data Analysis & Statistics (Correlation, Distributions)
   - Arm 4: Feature Engineering & Transformation (Encoding, Scaling, Embeddings)
   - Arm 5: Model Training & Tuning (Scikit-Learn, PyTorch, Baseline Comparison)
   - Arm 6: Evaluation & Metrics Validation (Cross-validation, ROC-AUC, Residuals)
   - Arm 7: Visualization & Reporting (Matplotlib, Markdown summaries)
3. Provide single-width glyph badges and distinct hex color accents for each arm.
4. Support loading via `--guild data_science`.

---

## Files to Touch
- [`octoflow/guild.py`](../../octoflow/guild.py): Add `DATA_SCIENCE` preset in `BUILTIN_GUILDS`.
- [`tests/test_guilds.py`](../../tests/test_guilds.py): Add unit tests validating that `octoflow guild show data_science` validates and displays all 8 arms.
- [`docs/extending/guilds.md`](../extending/guilds.md): Document the new guild and its arm roles.

---

## Acceptance Criteria
- [ ] `octoflow guild validate <spec>` succeeds for the new preset.
- [ ] `octoflow guild show data_science` prints the 8-arm roster with correct tool permissions.
- [ ] `octoflow run "Analyze dataset and build classifier" --guild data_science --dry-run` executes with the data science roles.
- [ ] Unit tests added to `tests/test_guilds.py` pass cleanly.


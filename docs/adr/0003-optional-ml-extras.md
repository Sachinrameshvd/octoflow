# ADR 0003: Optional ML Extras and Pure-NumPy Core

## Status
Accepted

## Context
The cephalopod biophysical model includes PyTorch neural network forward models (`octopus_brain/`) and 3D continuum physics environments (`envs/soft_body_tentacle.py`). However, heavy machine learning libraries (`torch`, `torchvision`, `onnxruntime`, `scipy`) exceed 800 MB to 1.5 GB in disk space and compile time, creating severe friction for developers who only need the software engineering swarm.

## Decision
Decouple the package into a lightweight, pure-NumPy base installation and an optional ML extra:
1. Base installation (`pip install octoflow`) requires only NumPy, Typer, Rich, and standard utilities (~25 MB total).
2. Sensory observation encoding (`CodeSensoryEncoder`) and surprise gating (`SurpriseGate`) default to vectorized NumPy implementations.
3. Neural policy training, LIF biophysics, and ONNX exports are isolated under the optional extra `[ml]` (`pip install "octoflow[ml]"`).
4. Subsystems requiring PyTorch perform lazy runtime feature checks and raise actionable `ImportError` messages directing users to install the `[ml]` extra.

## Alternatives Considered
- **Mandatory PyTorch Dependency:** Require PyTorch unconditionally in `requirements.txt`. Rejected because it increases CI container build times by 5x and discourages lightweight local usage.
- **Separate PyPI Packages (`octoflow` and `octoflow-brain`):** Split the repository into two separate packages. Rejected as premature monorepo fragmentation during Alpha development.

## Consequences
- **Positive:** Fast 30-second installation from source or wheel; minimal footprint for standard software engineering tasks; zero GPU requirements for default operation.
- **Negative:** Contributors working on biophysical reinforcement learning must remember to pass `pip install -e ".[ml]"`.

## Evidence & References
- Config: [`pyproject.toml`](../../pyproject.toml) (`[project.optional-dependencies] ml = [...]`)
- Implementation: [`octoflow/encoder.py`](../../octoflow/encoder.py) (`get_encoder(backend="numpy")`)
- Verification: [`tests/test_developer_pillars.py`](../../tests/test_developer_pillars.py)
- Commit: `a63f10d` (P2.5 Optional ML dependencies)

## What Would Change This Decision
If a micro-footprint (<5 MB) embedded tensor runtime becomes standardized across Python distributions without platform-specific wheel compilation overhead.


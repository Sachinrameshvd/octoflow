# ADR 0002: Visualizer Distribution Asset Bundling

## Status
Accepted & Automated in Release Pipeline (P10.2)

## Context
OctoFlow includes an interactive 3D WebGL Benthic Connectome Visualizer implemented in TypeScript with Three.js (`visualizer/`). To provide an out-of-the-box user experience via `octoflow ui` and standalone HTML report exports (`octoflow report`), the Python package requires pre-built frontend distribution assets (`octoflow/dist/`). We needed to decide whether `octoflow/dist/` should be pre-compiled and tracked in git, or generated dynamically in release CI.

## Decision
Pre-compile production web assets into `octoflow/dist/` and track them directly in the repository via `make visualizer-sync`. Bundle `octoflow/dist/` within package data in `pyproject.toml`. Provide `make dev` for active frontend contributors wanting Vite hot-module reload on `http://localhost:5173`.

## Alternatives Considered
- **Compile during `pip install`:** Require Node.js/npm on the user's host machine during Python wheel installation. Rejected due to severe developer friction and broken environments on systems lacking Node.js.
- **Dynamic CDN Runtime Fetching:** Fetch Three.js and visualizer bundles from public CDNs at runtime. Rejected because it violates the offline and local-first architectural boundary (ADR 0001).
- **Build Exclusively in GitHub Actions Release CI:** Omit `octoflow/dist/` from git and compile only during release tag jobs. Deferred until full release automation (P10.2) is verified, preventing broken local editable installs (`pip install -e .`).

## Consequences
- **Positive:** Users can clone the repo or install the package and immediately run `octoflow ui` without installing Node.js or running build tools.
- **Negative:** Commits modifying the visualizer produce binary bundle diffs in `octoflow/dist/` (~3 MB).

## Evidence & References
- Implementation: [`Makefile`](../../Makefile) (`visualizer-sync`, `visualizer-build`)
- Verification: [`octoflow/dist/index.html`](../../octoflow/dist/index.html), [`tests/test_server_security.py`](../../tests/test_server_security.py)
- Commit: `72ea4e6` (P4.4 Visualizer quality and dist sync)

## Resolution in P10.2 (Automated Release Packaging)
With the implementation of automated release packaging (P10.2):
- `make build` runs `visualizer-build` (`npm ci && npm run build`) and synchronizes bundles to `octoflow/dist/` before invoking `python -m build`.
- CI enforces deterministic dist verification via `scripts/verify_wheel.sh`, asserting that wheels contain `octoflow/dist/index.html` and assets, while excluding tests, `node_modules`, and `.env` files.
- Local editable checkouts (`pip install -e .`) continue to function offline with zero Node.js prerequisites, while release builds always produce fresh, verified distribution bundles.


"""OctoFlow Monorepo & Multi-Package Coordinator.

Detects monorepo workspaces (pnpm, npm/yarn workspaces, Lerna, Cargo workspaces, multi-service directories),
maps sub-packages to their optimal Ganglia arms, and aggregates cross-package topology.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def scan_monorepo_topology(root_dir: str = ".") -> Dict[str, Any]:
    """Scan workspace root for monorepo packages, workspaces, and multi-service subdirectories."""
    ws = Path(root_dir).resolve()
    packages: List[Dict[str, Any]] = []

    # 1. Check workspace manifests
    is_monorepo = False
    indicators = [
        ws / "pnpm-workspace.yaml",
        ws / "lerna.json",
        ws / "turbo.json",
        ws / "nx.json",
    ]
    if any(p.exists() for p in indicators):
        is_monorepo = True

    root_pkg_json = ws / "package.json"
    if root_pkg_json.exists():
        try:
            pj_data = json.loads(root_pkg_json.read_text(encoding="utf-8"))
            if "workspaces" in pj_data:
                is_monorepo = True
        except Exception:
            pass

    # 2. Discover sub-projects / packages
    candidate_dirs = [
        d for d in ws.iterdir()
        if d.is_dir() and not d.name.startswith(".") and d.name not in ["node_modules", "target", "dist", "build", "venv", ".venv"]
    ]

    # Also inspect packages/, apps/, services/ subdirectories if present
    for sub in ["packages", "apps", "services"]:
        sub_path = ws / sub
        if sub_path.exists() and sub_path.is_dir():
            candidate_dirs.extend([
                d for d in sub_path.iterdir()
                if d.is_dir() and not d.name.startswith(".") and d.name != "node_modules"
            ])

    for d in candidate_dirs:
        rel_path = str(d.relative_to(ws))
        manifest = None
        pkg_type = "library"
        primary_arm = 2  # Backend API

        # Check Node / Frontend / API
        if (d / "package.json").exists():
            manifest = "package.json"
            try:
                sub_pj = json.loads((d / "package.json").read_text(encoding="utf-8"))
                deps = str(sub_pj.get("dependencies", {})) + str(sub_pj.get("devDependencies", {}))
                if any(k in deps for k in ["react", "vue", "svelte", "next", "vite", "tailwind"]):
                    pkg_type = "frontend"
                    primary_arm = 3  # Frontend UI
                elif any(k in deps for k in ["express", "fastify", "nest", "koa"]):
                    pkg_type = "backend"
                    primary_arm = 2  # Backend API
            except Exception:
                pass

        # Check Python
        elif (d / "pyproject.toml").exists() or (d / "setup.py").exists() or (d / "requirements.txt").exists():
            manifest = "pyproject.toml" if (d / "pyproject.toml").exists() else "setup.py"
            pkg_type = "backend"
            primary_arm = 2

        # Check Rust
        elif (d / "Cargo.toml").exists():
            manifest = "Cargo.toml"
            pkg_type = "backend"
            primary_arm = 2

        # Check Docker / Infra
        elif (d / "Dockerfile").exists() or (d / "docker-compose.yml").exists():
            manifest = "Dockerfile"
            pkg_type = "infrastructure"
            primary_arm = 7  # DevOps

        if manifest:
            packages.append({
                "name": d.name,
                "rel_path": rel_path,
                "type": pkg_type,
                "manifest": manifest,
                "primary_arm": primary_arm,
            })

    if len(packages) >= 2:
        is_monorepo = True

    # Build arm routing map
    arm_routing: Dict[int, List[str]] = {i: [] for i in range(8)}
    for pkg in packages:
        arm_routing[pkg["primary_arm"]].append(pkg["rel_path"])

    return {
        "is_monorepo": is_monorepo,
        "package_count": len(packages),
        "packages": packages,
        "arm_routing": arm_routing,
    }

#!/usr/bin/env python3
"""CycloneDX v1.5 Software Bill of Materials (SBOM) Generator for OctoFlow.

Generates:
- dist-artifacts/bom-python.json: Full CycloneDX SBOM for Python dependencies.
- dist-artifacts/bom-npm.json: Full CycloneDX SBOM for WebGL Visualizer NPM packages.
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
import importlib.metadata as im


def generate_python_sbom(workspace_dir: Path, output_path: Path) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    serial_number = f"urn:uuid:{uuid.uuid4()}"

    # Load locked packages if present
    lock_file = workspace_dir / "requirements.lock"
    tracked_names: set[str] = set()
    if lock_file.exists():
        for line in lock_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "==" in line:
                tracked_names.add(line.split("==")[0].lower().replace("_", "-"))

    components = []
    for d in im.distributions():
        name = d.metadata.get("Name")
        if not name:
            continue
        norm_name = name.lower().replace("_", "-")
        if tracked_names and norm_name not in tracked_names and norm_name != "octoflow":
            continue

        ver = d.version
        lic = d.metadata.get("License-Expression") or d.metadata.get("License") or "MIT"
        if len(lic.splitlines()) > 1:
            lic = lic.splitlines()[0][:40]

        comp = {
            "type": "library",
            "name": name,
            "version": ver,
            "purl": f"pkg:pypi/{name.lower()}@{ver}",
            "scope": "required" if norm_name != "octoflow" else "root",
            "licenses": [{"license": {"name": lic}}],
        }
        components.append(comp)

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial_number,
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "tools": [
                {
                    "vendor": "OctoFlow",
                    "name": "cyclonedx-generator",
                    "version": "1.0.0",
                }
            ],
            "component": {
                "type": "application",
                "name": "octoflow",
                "version": "0.2.0",
                "licenses": [{"license": {"name": "MIT"}}],
            },
        },
        "components": sorted(components, key=lambda c: c["name"].lower()),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(sbom, indent=2), encoding="utf-8")
    print(f"✔ Generated Python CycloneDX SBOM at {output_path} ({len(components)} components)")
    return sbom


def generate_npm_sbom(visualizer_dir: Path, output_path: Path) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    serial_number = f"urn:uuid:{uuid.uuid4()}"

    nm_dir = visualizer_dir / "node_modules"
    components = []
    seen = set()

    if nm_dir.exists():
        for item in sorted(nm_dir.iterdir()):
            if item.name.startswith("."):
                continue
            if item.name.startswith("@"):
                for sub in sorted(item.iterdir()):
                    pkg_json = sub / "package.json"
                    if pkg_json.exists():
                        try:
                            data = json.loads(pkg_json.read_text(encoding="utf-8"))
                            name = data.get("name", sub.name)
                            if name not in seen:
                                seen.add(name)
                                ver = data.get("version", "0.0.0")
                                lic = data.get("license") or "MIT"
                                if isinstance(lic, dict):
                                    lic = lic.get("type", "MIT")
                                components.append({
                                    "type": "library",
                                    "name": name,
                                    "version": ver,
                                    "purl": f"pkg:npm/{name}@{ver}",
                                    "scope": "required",
                                    "licenses": [{"license": {"name": str(lic)}}],
                                })
                        except Exception:
                            pass
            else:
                pkg_json = item / "package.json"
                if pkg_json.exists():
                    try:
                        data = json.loads(pkg_json.read_text(encoding="utf-8"))
                        name = data.get("name", item.name)
                        if name not in seen:
                            seen.add(name)
                            ver = data.get("version", "0.0.0")
                            lic = data.get("license") or "MIT"
                            if isinstance(lic, dict):
                                lic = lic.get("type", "MIT")
                            components.append({
                                "type": "library",
                                "name": name,
                                "version": ver,
                                "purl": f"pkg:npm/{name}@{ver}",
                                "scope": "required",
                                "licenses": [{"license": {"name": str(lic)}}],
                            })
                    except Exception:
                        pass

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial_number,
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "tools": [
                {
                    "vendor": "OctoFlow",
                    "name": "cyclonedx-npm-generator",
                    "version": "1.0.0",
                }
            ],
            "component": {
                "type": "application",
                "name": "octoflow-visualizer",
                "version": "0.0.0",
                "licenses": [{"license": {"name": "MIT"}}],
            },
        },
        "components": sorted(components, key=lambda c: c["name"].lower()),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(sbom, indent=2), encoding="utf-8")
    print(f"✔ Generated NPM CycloneDX SBOM at {output_path} ({len(components)} components)")
    return sbom


def main():
    ws = Path(".").resolve()
    artifacts_dir = ws / "dist-artifacts"

    py_out = artifacts_dir / "bom-python.json"
    npm_out = artifacts_dir / "bom-npm.json"

    generate_python_sbom(ws, py_out)
    generate_npm_sbom(ws / "visualizer", npm_out)


if __name__ == "__main__":
    main()

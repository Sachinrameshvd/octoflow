#!/usr/bin/env python3
"""Coverage floor checker for OctoFlow core modules (P4.1).

Enforces an 80% line coverage floor for core modules:
- octoflow/gate.py
- octoflow/encoder.py
- octoflow/provider.py
- octoflow/tools.py
- octoflow/router.py
- octoflow/settings.py
- octoflow/outcome.py
- octoflow/budget.py
- octoflow/errors.py

Overall coverage is reported for visibility but not gated.
"""

import json
import sys
from pathlib import Path
from typing import Any

MODULE_FLOOR_PCT = 80.0

REQUIRED_MODULES = [
    "octoflow/gate.py",
    "octoflow/encoder.py",
    "octoflow/provider.py",
    "octoflow/tools.py",
    "octoflow/router.py",
    "octoflow/settings.py",
    "octoflow/outcome.py",
    "octoflow/budget.py",
    "octoflow/errors.py",
]


def load_coverage_data(json_path: Path) -> dict[str, Any]:
    if not json_path.exists():
        print(f"Error: Coverage JSON file not found at {json_path}")
        print("Run: pytest --cov=octoflow --cov-report=json:coverage.json")
        sys.exit(1)
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading coverage report {json_path}: {e}")
        sys.exit(1)


def find_file_entry(
    files_dict: dict[str, Any], target_rel: str
) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    norm_target = target_rel.replace("\\", "/").lstrip("./")
    for file_key, data in files_dict.items():
        norm_key = file_key.replace("\\", "/").lstrip("./")
        if norm_key.endswith(norm_target):
            return file_key, data
    return None, None


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    cov_path = repo_root / "coverage.json"
    cov_data = load_coverage_data(cov_path)

    totals = cov_data.get("totals", {})
    overall_pct = totals.get("percent_covered", 0.0)
    files_data = cov_data.get("files", {})

    print("=" * 72)
    print("OctoFlow Core Module Coverage Verification (Floor: 80.0%)")
    print("=" * 72)
    print(f"{'Module':<32} {'Coverage':<12} {'Floor':<10} {'Status':<10}")
    print("-" * 72)

    failed_modules: list[tuple[str, float]] = []

    for mod in REQUIRED_MODULES:
        key, entry = find_file_entry(files_data, mod)
        if entry is None:
            print(f"{mod:<32} {'MISSING':<12} {MODULE_FLOOR_PCT:>5.1f}%    FAIL (Not measured)")
            failed_modules.append((mod, 0.0))
            continue

        summary = entry.get("summary", {})
        cov_pct = float(summary.get("percent_covered", 0.0))
        passed = cov_pct >= MODULE_FLOOR_PCT
        status_str = "PASS" if passed else "FAIL"

        print(f"{mod:<32} {cov_pct:>6.1f}%      {MODULE_FLOOR_PCT:>5.1f}%    {status_str}")

        if not passed:
            failed_modules.append((mod, cov_pct))

    print("-" * 72)
    print(f"Overall Coverage: {overall_pct:.1f}% (informational, not gated)")
    print("=" * 72)

    if failed_modules:
        print(f"\n[FAILED] {len(failed_modules)} module(s) below the {MODULE_FLOOR_PCT}% floor:")
        for mod, pct in failed_modules:
            print(f"  • {mod}: {pct:.1f}% (required: {MODULE_FLOOR_PCT:.1f}%)")
        sys.exit(1)

    print(
        f"\n[PASSED] All {len(REQUIRED_MODULES)} core modules met or exceeded the {MODULE_FLOOR_PCT}% floor."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""OctoFlow Version Management and Release Helper.

Manages single-source version bumping across pyproject.toml and CHANGELOG.md.
Creates a release preparation commit without tagging or pushing.

Usage:
  python scripts/release.py version
  python scripts/release.py bump <major|minor|patch|X.Y.Z> [--dry-run]
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"


def get_current_version() -> str:
    """Extract current version from pyproject.toml."""
    text = PYPROJECT_PATH.read_text(encoding="utf-8")
    match = re.search(r'version\s*=\s*"([^"]+)"', text)
    if not match:
        raise ValueError(f"Could not find version string in {PYPROJECT_PATH}")
    return match.group(1)


def calculate_next_version(current: str, bump_type: str) -> str:
    """Calculate the next semantic version string."""
    semver_match = re.match(r"^(\d+)\.(\d+)\.(\d+)(.*)$", current)
    if not semver_match:
        raise ValueError(f"Current version '{current}' is not valid SemVer (X.Y.Z)")

    major = int(semver_match.group(1))
    minor = int(semver_match.group(2))
    patch = int(semver_match.group(3))

    b = bump_type.lower()
    if b == "major":
        return f"{major + 1}.0.0"
    if b == "minor":
        return f"{major}.{minor + 1}.0"
    if b == "patch":
        return f"{major}.{minor}.{patch + 1}"

    # Explicit version string provided
    if re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$", bump_type):
        return bump_type

    raise ValueError(f"Invalid bump type or version '{bump_type}'. Must be major, minor, patch, or X.Y.Z")


def apply_pyproject_version(text: str, new_version: str) -> str:
    """Update version in pyproject.toml text."""
    return re.sub(r'version\s*=\s*"[^"]+"', f'version = "{new_version}"', text, count=1)


def apply_changelog_version(text: str, new_version: str, release_date: str) -> str:
    """Update or insert release section in CHANGELOG.md."""
    # Check if this version header already exists
    existing_pattern = re.compile(rf"^## \[{re.escape(new_version)}\](?: - \d{{4}}-\d{{2}}-\d{{2}})?", re.MULTILINE)
    if existing_pattern.search(text):
        return existing_pattern.sub(f"## [{new_version}] - {release_date}", text, count=1)

    # Otherwise, move Unreleased content under the new version header
    unreleased_pattern = re.compile(r"## \[Unreleased\]\n\n(.*?)(?=\n## \[|\Z)", re.DOTALL)
    match = unreleased_pattern.search(text)
    if match and match.group(1).strip():
        unreleased_body = match.group(1).strip()
        new_section = (
            "## [Unreleased]\n\n"
            "### Added\n\n"
            "### Changed\n\n"
            "### Fixed\n\n"
            f"## [{new_version}] - {release_date}\n\n"
            f"{unreleased_body}\n"
        )
        return unreleased_pattern.sub(new_section, text, count=1)

    # Fallback: prepend new release header after [Unreleased]
    fallback_pattern = "## [Unreleased]\n"
    new_header = f"## [Unreleased]\n\n## [{new_version}] - {release_date}\n"
    if fallback_pattern in text:
        return text.replace(fallback_pattern, new_header, 1)

    return text


def is_working_tree_clean() -> bool:
    """Check if the git working tree has no uncommitted changes."""
    res = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True)
    return len(res.stdout.strip()) == 0


def bump_version(bump_type: str, dry_run: bool = False, allow_dirty: bool = False) -> str:
    """Perform version bump, show diff, and optionally commit."""
    if not dry_run and not allow_dirty and not is_working_tree_clean():
        raise RuntimeError(
            "Working directory has uncommitted modifications. "
            "Please commit or stash your changes before bumping version, or pass --allow-dirty."
        )

    current = get_current_version()
    new_version = calculate_next_version(current, bump_type)
    today = datetime.date.today().strftime("%Y-%m-%d")

    orig_pyproject = PYPROJECT_PATH.read_text(encoding="utf-8")
    new_pyproject = apply_pyproject_version(orig_pyproject, new_version)

    orig_changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
    new_changelog = apply_changelog_version(orig_changelog, new_version, today)

    # Compute diffs
    pyproject_diff = "".join(
        difflib.unified_diff(
            orig_pyproject.splitlines(keepends=True),
            new_pyproject.splitlines(keepends=True),
            fromfile="a/pyproject.toml",
            tofile="b/pyproject.toml",
        )
    )
    changelog_diff = "".join(
        difflib.unified_diff(
            orig_changelog.splitlines(keepends=True),
            new_changelog.splitlines(keepends=True),
            fromfile="a/CHANGELOG.md",
            tofile="b/CHANGELOG.md",
        )
    )

    if dry_run:
        print(f"◈ [DRY-RUN] Version bump: {current} -> {new_version} (Release date: {today})\n")
        if pyproject_diff:
            print("--- pyproject.toml diff ---")
            print(pyproject_diff)
        if changelog_diff:
            print("--- CHANGELOG.md diff ---")
            print(changelog_diff)
        print("✔ Dry-run complete. No files written, no commits created.")
        return new_version

    # Write changes
    PYPROJECT_PATH.write_text(new_pyproject, encoding="utf-8")
    CHANGELOG_PATH.write_text(new_changelog, encoding="utf-8")

    # Create release preparation commit (NO tag, NO push)
    commit_msg = f"chore(release): bump version to {new_version}"
    subprocess.run(["git", "add", "pyproject.toml", "CHANGELOG.md"], cwd=REPO_ROOT, check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_ROOT, check=True)

    print(f"✔ Version bumped successfully: {current} -> {new_version}")
    print(f"✔ Created commit: '{commit_msg}'")
    print("NOTE: Release script does NOT tag or push. Inspect commit with 'git show HEAD'.")
    return new_version


def main() -> int:
    parser = argparse.ArgumentParser(description="OctoFlow version and release manager.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # version subcommand
    subparsers.add_parser("version", help="Print current repository version.")

    # bump subcommand
    bump_parser = subparsers.add_parser("bump", help="Bump version and update release notes.")
    bump_parser.add_argument("target", help="major, minor, patch, or explicit X.Y.Z")
    bump_parser.add_argument("--dry-run", action="store_true", help="Show diff without modifying files or committing.")
    bump_parser.add_argument("--allow-dirty", action="store_true", help="Allow bumping version even if working directory has uncommitted changes.")

    args = parser.parse_args()

    if args.command == "version":
        print(get_current_version())
        return 0

    if args.command == "bump":
        try:
            bump_version(args.target, dry_run=args.dry_run, allow_dirty=args.allow_dirty)
            return 0
        except Exception as err:
            sys.stderr.write(f"Error bumping version: {err}\n")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

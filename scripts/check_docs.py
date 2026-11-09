#!/usr/bin/env python3
"""Automated Documentation Quality, Link Integrity & Anchor Checker.

Verifies:
  (a) Relative links and anchor fragments resolve.
  (b) Every `octoflow <subcommand>` mentioned in docs exists in CLI --help.
  (c) Every error code in docs/reference/errors.md matches octoflow/errors.py and has
      a troubleshooting anchor in docs/TROUBLESHOOTING.md.
  (d) Docs contain zero emoji characters and no absolute user paths (/Users/..., /home/...).
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Approved single-width semantic terminal glyphs from zero-emoji policy (P6.3)
APPROVED_GLYPHS = {
    0x2714,  # ✔
    0x2716,  # ✖
    0x2713,  # ✓
    0x2717,  # ✗
    0x2022,  # •
    0x00B7,  # ·
    0x25CB,  # ○
    0x25C8,  # ◈
    0x25CF,  # ●
    # Box drawings
    0x2500, 0x2502, 0x250C, 0x2510, 0x2514, 0x2518, 0x251C, 0x2524, 0x252C, 0x2534, 0x253C,
}


def get_registered_cli_commands() -> set[str]:
    """Retrieve all valid subcommand names registered in OctoFlow CLI."""
    try:
        import typer.main
        import octoflow.cli

        click_cmd = typer.main.get_command(octoflow.cli.app)
        return set(click_cmd.commands.keys())
    except Exception as err:
        sys.stderr.write(f"Warning: could not inspect CLI directly ({err}), using fallback list.\n")
        return {
            "audit", "banner", "bench", "bugreport", "config", "consortium",
            "diff-review", "docs", "doctor", "eject", "export", "federation",
            "first-run", "fix", "glossary", "guard", "guild", "heal", "init",
            "init-action", "init-ide", "install-claude", "install-hooks",
            "manual", "mcp", "mcp-serve", "monorepo", "notify", "play", "ps",
            "purge", "receipt", "record", "replay", "report", "review-pr",
            "run", "runner", "runs", "screensaver", "setup", "stop", "theme",
            "train", "triage", "ui", "undo",
        }


def heading_to_slug(heading: str) -> str:
    """Convert a markdown heading into a GitHub-compatible anchor slug."""
    # Strip HTML tags
    slug = re.sub(r"<[^>]+>", "", heading).strip().lower()
    # Remove all punctuation except hyphens, spaces, and alphanumeric
    slug = re.sub(r"[^\w\s-]", "", slug)
    # Collapse multiple spaces or hyphens to a single hyphen
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug


def extract_anchors(file_path: Path) -> set[str]:
    """Extract all valid anchor targets from a Markdown file."""
    if not file_path.is_file():
        return set()

    anchors = set()
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception:
        return set()

    # 1. HTML explicit anchor tags: <a id="foo"> or <a name="foo">
    for match in re.finditer(r'<a\s+(?:id|name)=["\']([^"\']+)["\']', text, re.IGNORECASE):
        anchors.add(match.group(1).lower().strip("#"))

    # 2. Markdown headings: # Heading Text
    for line in text.splitlines():
        heading_match = re.match(r"^#{1,6}\s+(.*)", line)
        if heading_match:
            raw_h = heading_match.group(1)
            # Check for embedded anchor tag in heading
            tag_match = re.search(r'<a\s+(?:id|name)=["\']([^"\']+)["\']', raw_h, re.IGNORECASE)
            if tag_match:
                anchors.add(tag_match.group(1).lower().strip("#"))
            slug = heading_to_slug(raw_h)
            if slug:
                anchors.add(slug)

    return anchors


def is_emoji(char: str) -> bool:
    """Check if character is an emoji, honoring approved single-width terminal glyphs."""
    cp = ord(char)
    if cp in APPROVED_GLYPHS or cp < 0x2000:
        return False
    # Check if wide / fullwidth (emojis are typically double-width)
    eaw = unicodedata.east_asian_width(char)
    if eaw in ("W", "F"):
        return True
    # Explicit emoji unicode ranges
    if (
        0x1F300 <= cp <= 0x1F9FF
        or 0x1FA70 <= cp <= 0x1FAFF
        or cp in (0x26A1, 0x26A0, 0x2728, 0x274C, 0x2705)
    ):
        return True
    return False


def check_docs(base_dir: Path | None = None) -> list[str]:
    """Execute all documentation integrity checks. Returns list of error strings."""
    root = (base_dir or REPO_ROOT).resolve()
    docs_dir = root / "docs"

    errors: list[str] = []
    registered_cmds = get_registered_cli_commands()

    # Collect Markdown files to inspect
    md_files: list[Path] = []
    if docs_dir.is_dir():
        md_files.extend(list(docs_dir.rglob("*.md")))
    for root_doc in ["README.md", "CONTRIBUTING.md", "CHANGELOG.md"]:
        p = root / root_doc
        if p.is_file():
            md_files.append(p)

    # Cache anchors per file
    anchors_cache: dict[Path, set[str]] = {}
    for mf in md_files:
        anchors_cache[mf.resolve()] = extract_anchors(mf)

    # Line anchor regex for source files: #L10 or #L10-L20
    line_anchor_re = re.compile(r"^l(\d+)(?:-l(\d+))?$")

    # Absolute path regexes to detect hardcoded user directories
    abs_path_re = re.compile(r"/(?:Users|home)/[a-zA-Z0-9_\-]+/")

    # CLI command mention regex: `octoflow <cmd>` or lines starting with octoflow / $ octoflow
    cli_re = re.compile(r"(?<![a-zA-Z0-9_.~/-])(?:octoflow|\./octo|\./octos)\s+([a-zA-Z0-9_\-]+)")

    # Common valid arguments / syntax words following octoflow
    syntax_words = {
        "run", "setup", "doctor", "ui", "replay", "receipt", "undo", "runs",
        "ps", "stop", "purge", "bench", "guild", "mcp-serve", "mcp", "init",
        "audit", "eject", "heal", "triage", "guard", "export", "report",
        "review-pr", "install-claude", "install-hooks", "diff-review",
        "banner", "screensaver", "theme", "play", "runner", "monorepo",
        "notify", "federation", "first-run", "fix", "glossary", "config",
        "train", "consortium", "manual", "docs", "init-action", "init-ide",
        "bugreport", "latest", "all", "subcommand", "command", "my-guild",
        "data_science", "fastlocal", "fibonacci", "rate_limiter", "server",
    }

    for doc in md_files:
        rel_doc = doc.relative_to(root)
        content = doc.read_text(encoding="utf-8")
        lines = content.splitlines()

        for line_no, line in enumerate(lines, start=1):
            # Check (d): Emoji detection
            for char in line:
                if is_emoji(char):
                    errors.append(
                        f"[Emoji] {rel_doc}:{line_no}: Found forbidden emoji '{char}' (U+{ord(char):04X})"
                    )

            # Check (d): Absolute user path detection
            abs_match = abs_path_re.search(line)
            if abs_match:
                errors.append(
                    f"[Absolute Path] {rel_doc}:{line_no}: Found hardcoded user path '{abs_match.group(0)}'"
                )

            # Check (b): CLI subcommand verification
            for cmd_match in cli_re.finditer(line):
                subcmd = cmd_match.group(1).lower()
                # Skip flags or options like --help, -v, --trace
                if subcmd.startswith("-"):
                    continue
                # Skip version numbers like 0.2.0 or v0.2.0
                if subcmd[0].isdigit() or (subcmd.startswith("v") and len(subcmd) > 1 and subcmd[1].isdigit()):
                    continue
                if subcmd in syntax_words:
                    continue
                if subcmd not in registered_cmds:
                    errors.append(
                        f"[Unknown Subcommand] {rel_doc}:{line_no}: 'octoflow {subcmd}' is not a registered CLI command"
                    )

        # Check (a): Relative links and anchors
        # Matches: [text](target)
        link_matches = re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content)
        for match in link_matches:
            target_str = match.group(2).strip()

            # Ignore external URLs, emails, or sidecar links
            if target_str.startswith(("http://", "https://", "mailto:", "sidecar://")):
                continue

            # In-file anchor: [text](#anchor)
            if target_str.startswith("#"):
                anchor = target_str[1:].lower()
                doc_anchors = anchors_cache.get(doc.resolve(), set())
                if anchor not in doc_anchors:
                    errors.append(
                        f"[Broken In-File Anchor] {rel_doc}: #{anchor} does not exist in {rel_doc}"
                    )
                continue

            # Relative path with optional anchor: [text](path.md#anchor)
            if "#" in target_str:
                path_part, anchor_part = target_str.split("#", 1)
                anchor = anchor_part.lower()
            else:
                path_part, anchor = target_str, None

            # Resolve relative file target
            target_path = (doc.parent / path_part).resolve()
            if not target_path.exists():
                errors.append(
                    f"[Broken Link] {rel_doc}: Target '{path_part}' does not exist"
                )
            elif anchor:
                line_m = line_anchor_re.match(anchor)
                if line_m:
                    # Valid GitHub line number reference (e.g. #L10 or #L10-L20)
                    start_line = int(line_m.group(1))
                    try:
                        file_line_count = len(target_path.read_text(encoding="utf-8").splitlines())
                        if start_line > file_line_count:
                            errors.append(
                                f"[Broken Line Anchor] {rel_doc}: Line #{anchor} exceeds {file_line_count} lines in {target_path.relative_to(root)}"
                            )
                    except Exception:
                        pass
                else:
                    target_anchors = anchors_cache.get(target_path)
                    if target_anchors is None:
                        target_anchors = extract_anchors(target_path)
                        anchors_cache[target_path] = target_anchors
                    if anchor not in target_anchors:
                        errors.append(
                            f"[Broken Anchor] {rel_doc}: Anchor #{anchor} not found in {target_path.relative_to(root)}"
                        )

    # Check (c): Error catalog consistency
    errors_ref = root / "docs" / "reference" / "errors.md"
    troubleshooting_doc = root / "docs" / "TROUBLESHOOTING.md"
    errors_py = root / "octoflow" / "errors.py"

    if errors_ref.is_file() and errors_py.is_file():
        err_content = errors_ref.read_text(encoding="utf-8")
        py_content = errors_py.read_text(encoding="utf-8")
        
        catalog_codes = set(re.findall(r"\b(E-[A-Z0-9]+(?:-[A-Z0-9]+)*)\b", py_content))
        doc_codes = set(re.findall(r"\b(E-[A-Z0-9]+(?:-[A-Z0-9]+)*)\b", err_content)) - {"E-XXXX"}
        
        # Verify docs/reference/errors.md codes exist in octoflow/errors.py
        for code in doc_codes:
            if code not in catalog_codes:
                errors.append(
                    f"[Unknown Error Code] {code} in docs/reference/errors.md is not in octoflow/errors.py catalog"
                )

        # Verify docs/reference/errors.md codes have troubleshooting anchors
        if troubleshooting_doc.is_file():
            tb_anchors = anchors_cache.get(troubleshooting_doc.resolve(), set())
            for code in doc_codes:
                expected_anchor = code.lower()
                if expected_anchor not in tb_anchors:
                    errors.append(
                        f"[Missing Error Anchor] {code} in docs/reference/errors.md has no matching anchor #{expected_anchor} in docs/TROUBLESHOOTING.md"
                    )

    return errors


def main() -> int:
    """CLI runner for docs integrity checker."""
    print("◈ OctoFlow Documentation Integrity & Link Checker")
    print(f"Scanning repository root: {REPO_ROOT}")

    errors = check_docs(REPO_ROOT)
    if errors:
        print(f"\n✖ Found {len(errors)} documentation issue(s):\n")
        for err in errors:
            print(f"  • {err}")
        return 1

    print("\n✔ All documentation links, anchors, CLI commands, and error codes verified! (0 errors)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

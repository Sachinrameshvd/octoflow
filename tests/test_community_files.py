"""Tests for open-source community, governance, and issue form configurations."""

from __future__ import annotations

import os
from pathlib import Path
import pytest
import yaml

from scripts.check_docs import is_emoji

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_required_community_files_exist() -> None:
    """Verifies that all required governance and community files exist."""
    required_files = [
        REPO_ROOT / "CONTRIBUTING.md",
        REPO_ROOT / "CODE_OF_CONDUCT.md",
        REPO_ROOT / "SECURITY.md",
        REPO_ROOT / "SUPPORT.md",
        REPO_ROOT / "GOVERNANCE.md",
        REPO_ROOT / "docs" / "OWNER_CHECKLIST.md",
        REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md",
        REPO_ROOT / ".github" / "CODEOWNERS",
        REPO_ROOT / ".github" / "labels.yml",
        REPO_ROOT / ".github" / "labeler.yml",
        REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml",
        REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml",
        REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml",
        REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "provider_request.yml",
    ]
    for p in required_files:
        assert p.is_file(), f"Required community file missing: {p.relative_to(REPO_ROOT)}"
        assert p.stat().st_size > 50, f"File {p.name} is unexpectedly empty"


def test_issue_form_schemas_validate() -> None:
    """Validates GitHub issue form YAML schemas using PyYAML."""
    template_dir = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"

    # 1. config.yml
    config_file = template_dir / "config.yml"
    with open(config_file, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert cfg.get("blank_issues_enabled") is False
    assert isinstance(cfg.get("contact_links"), list)
    for link in cfg["contact_links"]:
        assert "name" in link and "url" in link and "about" in link

    # 2. Form files
    form_files = ["bug_report.yml", "feature_request.yml", "provider_request.yml"]
    valid_element_types = {"markdown", "input", "textarea", "dropdown", "checkboxes"}

    for ff in form_files:
        form_path = template_dir / ff
        with open(form_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert "name" in data, f"{ff} missing 'name'"
        assert "description" in data, f"{ff} missing 'description'"
        assert "body" in data, f"{ff} missing 'body'"
        assert isinstance(data["body"], list), f"{ff} 'body' must be a list"

        for element in data["body"]:
            assert "type" in element, f"Element in {ff} missing 'type'"
            elem_type = element["type"]
            assert elem_type in valid_element_types, f"Invalid type '{elem_type}' in {ff}"
            assert "attributes" in element, f"Element {elem_type} in {ff} missing 'attributes'"


def test_labels_yaml_structure() -> None:
    """Verifies .github/labels.yml defines all required project labels."""
    labels_file = REPO_ROOT / ".github" / "labels.yml"
    with open(labels_file, "r", encoding="utf-8") as f:
        labels = yaml.safe_load(f)

    assert isinstance(labels, list)
    label_names = {l["name"] for l in labels}

    required_labels = {
        "bug",
        "enhancement",
        "good first issue",
        "help wanted",
        "provider",
        "guild",
        "visualizer",
        "docs",
        "security",
        "needs-repro",
        "wontfix",
        "experimental",
    }
    missing = required_labels - label_names
    assert not missing, f"Missing required labels in labels.yml: {missing}"

    for l in labels:
        assert "name" in l and "color" in l and "description" in l
        assert len(str(l["color"])) == 6, f"Invalid color '{l['color']}' for label '{l['name']}'"


def test_labeler_yaml_structure() -> None:
    """Verifies .github/labeler.yml has valid path rules."""
    labeler_file = REPO_ROOT / ".github" / "labeler.yml"
    with open(labeler_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert isinstance(config, dict)
    assert "docs" in config
    assert "provider" in config
    assert "guild" in config
    assert "visualizer" in config
    assert "security" in config


def test_code_of_conduct_official_text() -> None:
    """Verifies CODE_OF_CONDUCT.md matches Contributor Covenant 2.1."""
    coc_path = REPO_ROOT / "CODE_OF_CONDUCT.md"
    content = coc_path.read_text(encoding="utf-8")
    assert "Contributor Covenant Code of Conduct" in content
    assert "version 2.1" in content
    assert "Enforcement Guidelines" in content
    assert "TODO: INSERT OWNER/MAINTAINER EMAIL HERE" in content


def test_security_and_support_realistic_sla() -> None:
    """Verifies that SECURITY and SUPPORT state realistic response targets for solo maintainers."""
    sec = (REPO_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "7 business days" in sec
    assert "Solo Maintainer Reality" in sec
    assert "Supported Versions" in sec

    sup = (REPO_ROOT / "SUPPORT.md").read_text(encoding="utf-8")
    assert "GitHub Discussions" in sup
    assert "5 to 7 business days" in sup


def test_community_files_zero_emojis() -> None:
    """Verifies zero-emoji policy compliance across all community files."""
    community_files = [
        REPO_ROOT / "CONTRIBUTING.md",
        REPO_ROOT / "CODE_OF_CONDUCT.md",
        REPO_ROOT / "SECURITY.md",
        REPO_ROOT / "SUPPORT.md",
        REPO_ROOT / "GOVERNANCE.md",
        REPO_ROOT / "ROADMAP.md",
        REPO_ROOT / "docs" / "OWNER_CHECKLIST.md",
        REPO_ROOT / "docs" / "RELEASING.md",
        REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md",
    ]
    for p in community_files:
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            for char in line:
                assert not is_emoji(char), (
                    f"Forbidden emoji '{char}' (U+{ord(char):04X}) in {p.name}:{line_no}"
                )


def test_roadmap_structure() -> None:
    """Verifies ROADMAP.md contains required horizons and un-planned areas."""
    roadmap = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    assert "Now (Next 2 Releases" in roadmap
    assert "Next (" in roadmap
    assert "Later (" in roadmap
    assert "Not Planned" in roadmap
    assert "Remote WAN / Internet Swarm Networking" in roadmap
    assert "Native Windows Console" in roadmap
    assert "Internationalization (i18n)" in roadmap
    assert "Dynamic Remote Plugin Marketplace" in roadmap
    assert "64-Arm Default Scaling" in roadmap


def test_seed_issues_complete_and_verified() -> None:
    """Verifies that all 10 seed issues exist, have required metadata, and reference real files."""
    seed_dir = REPO_ROOT / "docs" / "seed-issues"
    assert seed_dir.is_dir()
    issue_files = sorted(seed_dir.glob("*.md"))
    assert len(issue_files) == 10, f"Expected 10 seed issues, found {len(issue_files)}"

    for issue_path in issue_files:
        content = issue_path.read_text(encoding="utf-8")
        assert content.startswith("# "), f"{issue_path.name} must start with '# <Title>'"
        assert "**Difficulty:**" in content, f"{issue_path.name} missing Difficulty"
        assert "**Labels:**" in content, f"{issue_path.name} missing Labels"
        assert "**Mentoring Pointer:**" in content, f"{issue_path.name} missing Mentoring Pointer"
        assert "## Context" in content, f"{issue_path.name} missing Context"
        assert "## Objectives & Requirements" in content, f"{issue_path.name} missing Objectives"
        assert "## Files to Touch" in content, f"{issue_path.name} missing Files to Touch"
        assert "## Acceptance Criteria" in content, f"{issue_path.name} missing Acceptance Criteria"

        for line_no, line in enumerate(content.splitlines(), start=1):
            for char in line:
                assert not is_emoji(char), (
                    f"Forbidden emoji '{char}' in {issue_path.name}:{line_no}"
                )


def test_seed_issue_and_label_scripts_dry_run() -> None:
    """Verifies sync_labels.sh and create_seed_issues.sh run cleanly in dry run mode."""
    import subprocess

    sync_script = REPO_ROOT / "scripts" / "sync_labels.sh"
    create_script = REPO_ROOT / "scripts" / "create_seed_issues.sh"
    assert sync_script.is_file() and os.access(sync_script, os.X_OK)
    assert create_script.is_file() and os.access(create_script, os.X_OK)

    res_sync = subprocess.run(["bash", str(sync_script), "--dry-run"], capture_output=True, text=True)
    assert res_sync.returncode == 0
    assert "OctoFlow Label Synchronization Utility" in res_sync.stdout

    res_create = subprocess.run(["bash", str(create_script), "--dry-run"], capture_output=True, text=True)
    assert res_create.returncode == 0
    assert "Found 10 seed issue template(s)" in res_create.stdout
    assert "gh issue create --title" in res_create.stdout

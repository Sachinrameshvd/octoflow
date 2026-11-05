"""Skills taxonomy mapping, normalization, and gap analysis module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

TAXONOMY_FILE = Path(__file__).resolve().parent / "skills_taxonomy.json"

DEFAULT_TAXONOMY: dict[str, Any] = {
    "domains": {
        "languages": ["python", "javascript", "typescript", "go", "rust", "java", "c++", "sql"],
        "backend": ["fastapi", "django", "flask", "express", "node.js", "graphql", "rest"],
        "frontend": ["react", "vue", "angular", "svelte", "next.js", "tailwind", "html", "css"],
        "cloud": ["aws", "gcp", "azure", "terraform", "docker"],
        "data": ["postgresql", "mysql", "mongodb", "redis", "pandas", "numpy"],
        "devops": ["docker", "kubernetes", "ci/cd", "github actions"],
        "ai_ml": ["pytorch", "tensorflow", "scikit-learn", "llm", "onnx"],
    },
    "synonyms": {
        "golang": "go",
        "k8s": "kubernetes",
        "postgres": "postgresql",
        "nodejs": "node.js",
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
    },
}


class SkillsTaxonomy:
    """Manages skill taxonomy lookup, aliases, and category mapping."""

    def __init__(self, config_path: Path | None = None):
        self.domains: dict[str, list[str]] = {}
        self.synonyms: dict[str, str] = {}
        self._load(config_path or TAXONOMY_FILE)

    def _load(self, path: Path) -> None:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self.domains = data.get("domains", DEFAULT_TAXONOMY["domains"])
                self.synonyms = data.get("synonyms", DEFAULT_TAXONOMY["synonyms"])
                return
            except Exception:
                pass
        self.domains = DEFAULT_TAXONOMY["domains"]
        self.synonyms = DEFAULT_TAXONOMY["synonyms"]

    def normalize(self, skill: str) -> str:
        """Resolve skill aliases and normalize case."""
        cleaned = skill.strip().lower()
        return self.synonyms.get(cleaned, cleaned)

    def get_domain(self, skill: str) -> str:
        """Find the biological domain for a normalized skill."""
        norm = self.normalize(skill)
        for domain, skills in self.domains.items():
            if norm in [self.normalize(s) for s in skills]:
                return domain
        return "other"


# Shared global taxonomy instance
_TAXONOMY = SkillsTaxonomy()


def normalize_skill(skill: str) -> str:
    """Resolve skill synonyms to standard forms."""
    return _TAXONOMY.normalize(skill)


def categorize_skills(skills: Sequence[str]) -> dict[str, list[str]]:
    """Group skills into domains (languages, backend, frontend, cloud, data, devops, ai_ml)."""
    categorized: dict[str, list[str]] = {d: [] for d in _TAXONOMY.domains}
    categorized["other"] = []

    seen = set()
    for s in skills:
        norm = _TAXONOMY.normalize(s)
        if norm in seen or not norm:
            continue
        seen.add(norm)
        domain = _TAXONOMY.get_domain(norm)
        if domain in categorized:
            categorized[domain].append(norm)
        else:
            categorized["other"].append(norm)

    return {k: sorted(v) for k, v in categorized.items() if v}


def identify_competencies(
    resume_skills: Sequence[str], required_skills: Sequence[str]
) -> dict[str, Any]:
    """Compare candidate competencies against job requirements with synonym resolution."""
    norm_resume = {_TAXONOMY.normalize(s) for s in resume_skills if s.strip()}
    norm_required = [_TAXONOMY.normalize(s) for s in required_skills if s.strip()]

    matched: list[str] = []
    missing: list[str] = []

    for req in norm_required:
        if req in norm_resume:
            matched.append(req)
        else:
            missing.append(req)

    total_req = max(1, len(norm_required))
    coverage_pct = round((len(matched) / total_req) * 100.0, 1)

    return {
        "matched": sorted(matched),
        "missing": sorted(missing),
        "coverage_pct": coverage_pct,
        "by_domain": {
            "resume": categorize_skills(resume_skills),
            "required": categorize_skills(required_skills),
        },
    }

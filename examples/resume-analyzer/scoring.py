"""ATS match scoring heuristics and gap calculation module."""

from __future__ import annotations

import re
from typing import Sequence
try:
    from .models import ATSScoreResult, JobDescription, ResumeData
except ImportError:
    from models import ATSScoreResult, JobDescription, ResumeData


def _extract_words(text: str) -> set[str]:
    """Tokenize text into lowercase alphanumeric words."""
    tokens = re.findall(r"\b[a-zA-Z0-9_\-\+\#\.\/]+\b", text.lower())
    return set(tokens)


def compute_score(resume: ResumeData, job_description: JobDescription) -> ATSScoreResult:
    """Calculate transparent ATS match score based on keyword, experience, and format weights.

    Weights:
      - 55% Keyword match (required skills + text overlap)
      - 25% Experience alignment
      - 20% Section completeness and formatting
    """
    resume_text_lower = resume.raw_text.lower()
    resume_tokens = _extract_words(resume.raw_text)

    # 1. Keyword Matching
    required = [s.strip().lower() for s in job_description.required_skills if s.strip()]
    if not required:
        # Fallback: extract potential technical words from raw JD
        jd_tokens = _extract_words(job_description.raw_text)
        required = list(jd_tokens)[:15]

    matched: list[str] = []
    missing: list[str] = []

    for req in required:
        # Check either exact substring in text or token match
        if req in resume_text_lower or req in resume_tokens:
            matched.append(req)
        else:
            missing.append(req)

    total_req = max(1, len(required))
    keyword_score = round((len(matched) / total_req) * 100.0, 1)

    # 2. Experience Alignment
    min_exp = job_description.min_years_experience
    cand_exp = resume.experience_years
    if min_exp <= 0.0:
        experience_score = 100.0
    else:
        experience_score = min(100.0, round((cand_exp / min_exp) * 100.0, 1))

    # 3. Document Format & Sections
    standard_sections = ["experience", "education", "skills", "projects"]
    detected_sections = sum(
        1
        for s in standard_sections
        if (s in resume.sections) or (re.search(rf"\b{s}\b", resume_text_lower))
    )
    format_score = round((detected_sections / len(standard_sections)) * 100.0, 1)

    # 4. Composite Score
    overall = round(
        (0.55 * keyword_score) + (0.25 * experience_score) + (0.20 * format_score), 1
    )
    overall = max(0.0, min(100.0, overall))

    # 5. Actionable Suggestions
    suggestions: list[str] = []
    if missing:
        missing_preview = ", ".join(missing[:5])
        suggestions.append(f"Add critical missing keywords to your experience or skills: {missing_preview}")
    if cand_exp < min_exp:
        suggestions.append(
            f"Highlight project leadership or relevant coursework to bridge the {round(min_exp - cand_exp, 1)} yr experience gap"
        )
    if detected_sections < 3:
        missing_secs = [
            s.capitalize()
            for s in standard_sections
            if not ((s in resume.sections) or re.search(rf"\b{s}\b", resume_text_lower))
        ]
        if missing_secs:
            suggestions.append(f"Ensure standard ATS headers are clearly labeled: {', '.join(missing_secs)}")

    if not suggestions:
        suggestions.append("Strong alignment! Ensure achievements include quantifiable metrics and business impact.")

    summary = (
        f"Overall match is {overall}%. Matched {len(matched)}/{total_req} key competencies. "
        f"Experience alignment is {experience_score}%, and format completeness is {format_score}%."
    )

    return ATSScoreResult(
        overall_score=overall,
        keyword_match_score=keyword_score,
        experience_score=experience_score,
        format_score=format_score,
        matching_keywords=matched,
        missing_critical_keywords=missing,
        suggestions=suggestions,
        summary=summary,
    )

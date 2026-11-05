"""Data models for AI Resume & ATS Match Analyzer."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ResumeData(BaseModel):
    """Parsed structured resume data extracted from document text or PDF."""

    raw_text: str = Field(..., description="Full extracted raw text of the resume")
    name: str | None = Field(default=None, description="Candidate name if detected")
    email: str | None = Field(default=None, description="Candidate contact email")
    phone: str | None = Field(default=None, description="Candidate phone number")
    skills: list[str] = Field(default_factory=list, description="Extracted candidate skills")
    experience_years: float = Field(default=0.0, description="Estimated years of experience")
    sections: dict[str, str] = Field(
        default_factory=dict, description="Identified sections (e.g. education, experience)"
    )


class JobDescription(BaseModel):
    """Parsed structured job description input."""

    raw_text: str = Field(..., description="Raw text of the target job posting")
    title: str = Field(default="", description="Job title if provided")
    required_skills: list[str] = Field(
        default_factory=list, description="Mandatory technical competencies"
    )
    nice_to_have_skills: list[str] = Field(
        default_factory=list, description="Preferred or bonus skills"
    )
    min_years_experience: float = Field(
        default=0.0, description="Minimum recommended years of experience"
    )


class ATSScoreResult(BaseModel):
    """Computed ATS gauntlet score, keyword analysis, and actionable suggestions."""

    overall_score: float = Field(
        ..., ge=0.0, le=100.0, description="Composite ATS match score (0-100)"
    )
    keyword_match_score: float = Field(
        ..., ge=0.0, le=100.0, description="Keyword coverage sub-score"
    )
    experience_score: float = Field(
        ..., ge=0.0, le=100.0, description="Experience alignment sub-score"
    )
    format_score: float = Field(
        ..., ge=0.0, le=100.0, description="Document structure and section sub-score"
    )
    matching_keywords: list[str] = Field(
        default_factory=list, description="Keywords present in both resume and JD"
    )
    missing_critical_keywords: list[str] = Field(
        default_factory=list, description="Important JD requirements absent in resume"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="Actionable recommendations to improve ATS match"
    )
    summary: str = Field(default="", description="Executive summary of candidate fit")

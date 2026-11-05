"""In-memory PDF and text parsing module for resumes."""

from __future__ import annotations

import re
from io import BytesIO
from typing import BinaryIO
import pypdf

try:
    from .models import ResumeData
except ImportError:
    from models import ResumeData


def extract_text_from_pdf(source: bytes | BinaryIO) -> str:
    """Extract full raw text from PDF bytes or a file-like stream in-memory.

    Guarantees zero file system writes: operates purely on bytes/memory streams.
    """
    if isinstance(source, bytes):
        stream = BytesIO(source)
    else:
        stream = source

    reader = pypdf.PdfReader(stream)
    pages_text = []
    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            pages_text.append(txt)

    return "\n".join(pages_text)


def extract_contact_info(text: str) -> tuple[str | None, str | None, str | None]:
    """Extract candidate name, email, and phone number heuristics from resume text."""
    # Email detection
    email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    email = email_match.group(0) if email_match else None

    # Phone detection (supports US and international formats)
    phone_match = re.search(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text
    )
    phone = phone_match.group(0).strip() if phone_match else None

    # Name detection (first non-empty line with 2-4 capitalized words before contact info)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = None
    for line in lines[:5]:
        if email and email in line:
            continue
        if phone and phone in line:
            continue
        if re.match(r"^[A-Z][a-zA-Z'.\-]+(?:\s+[A-Z][a-zA-Z'.\-]+){1,3}$", line):
            name = line
            break

    return name, email, phone


def extract_sections(text: str) -> dict[str, str]:
    """Segment resume text into standard ATS recognized sections."""
    known_headers = [
        "experience",
        "employment history",
        "work experience",
        "education",
        "skills",
        "technical skills",
        "projects",
        "certifications",
        "summary",
        "profile",
        "objective",
    ]

    pattern = r"(?i)^[ \t]*(?:[#*•\-–—]\s*)?(" + "|".join(re.escape(h) for h in known_headers) + r")(?:\s*[:\-–—])?[ \t]*$"
    matches = list(re.finditer(pattern, text, re.MULTILINE))

    sections: dict[str, str] = {}
    if not matches:
        return sections

    for i, match in enumerate(matches):
        raw_header = match.group(1).lower()
        # Canonicalize header names
        if "experience" in raw_header or "employment" in raw_header:
            header_key = "experience"
        elif "skill" in raw_header:
            header_key = "skills"
        elif "education" in raw_header:
            header_key = "education"
        elif "project" in raw_header:
            header_key = "projects"
        elif "cert" in raw_header:
            header_key = "certifications"
        elif "summary" in raw_header or "profile" in raw_header or "objective" in raw_header:
            header_key = "summary"
        else:
            header_key = raw_header

        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start_pos:end_pos].strip()
        sections[header_key] = content

    return sections


def estimate_experience_years(text: str) -> float:
    """Estimate total professional experience years from explicit mentions or date spans."""
    # Pattern 1: explicit mention "X+ years of experience"
    exp_explicit = re.findall(
        r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\b", text, re.IGNORECASE
    )
    if exp_explicit:
        try:
            return max(float(x) for x in exp_explicit)
        except ValueError:
            pass

    # Pattern 2: date ranges like 2018 - 2023 or 2018 – Present
    year_ranges = re.findall(
        r"\b(20[0-2]\d|199\d)\s*(?:-|–|—|to)\s*(20[0-2]\d|present|current)\b",
        text,
        re.IGNORECASE,
    )
    if year_ranges:
        import datetime

        current_year = datetime.date.today().year
        total_span = 0.0
        for start_str, end_str in year_ranges:
            start_yr = int(start_str)
            end_yr = current_year if end_str.lower() in ("present", "current") else int(end_str)
            if end_yr >= start_yr:
                total_span = max(total_span, float(end_yr - start_yr))
        if total_span > 0:
            return total_span

    return 0.0


def parse_resume(source: bytes | BinaryIO | str, filename: str | None = None) -> ResumeData:
    """Parse resume source (bytes, file-like stream, or raw text) into ResumeData."""
    if isinstance(source, (bytes, BinaryIO)) or hasattr(source, "read"):
        raw_text = extract_text_from_pdf(source)
    else:
        raw_text = str(source)

    name, email, phone = extract_contact_info(raw_text)
    sections = extract_sections(raw_text)
    exp_years = estimate_experience_years(raw_text)

    # Extract detected skills from skills section or whole text
    skills_text = sections.get("skills", raw_text)
    extracted_skills = [
        s.strip().lower()
        for s in re.split(r"[,•|\n;]", skills_text)
        if len(s.strip()) > 1 and not s.strip().startswith("http")
    ]

    return ResumeData(
        raw_text=raw_text,
        name=name,
        email=email,
        phone=phone,
        skills=extracted_skills[:30],
        experience_years=exp_years,
        sections=sections,
    )

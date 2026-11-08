"""FastAPI backend application for AI Resume & ATS Match Analyzer."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from .models import ATSScoreResult, JobDescription, ResumeData
    from .parser import extract_text_from_pdf, parse_resume
    from .scoring import compute_score
    from .skills import categorize_skills, identify_competencies, normalize_skill
except ImportError:
    from models import ATSScoreResult, JobDescription, ResumeData
    from parser import extract_text_from_pdf, parse_resume
    from scoring import compute_score
    from skills import categorize_skills, identify_competencies, normalize_skill

app = FastAPI(
    title="AI Resume & ATS Match Analyzer",
    description="Turnkey, privacy-first resume analysis and ATS scoring gauntlet",
    version="1.0.0",
)

# Enable CORS for local dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class AnalyzeJsonRequest(BaseModel):
    """JSON payload schema for text-based analysis without file uploads."""

    resume_text: str = Field(..., description="Full text of candidate resume")
    job_description: str = Field(..., description="Target job description text")
    title: str = Field(default="", description="Target job title")
    required_skills: list[str] = Field(default_factory=list, description="Mandatory skills")
    min_years_experience: float = Field(default=0.0, description="Minimum experience required")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint confirming service operational status."""
    return {"status": "healthy", "service": "resume-analyzer", "version": "1.0.0"}


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard() -> HTMLResponse:
    """Serve the single-page dark-mode dashboard."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="""<!DOCTYPE html>
        <html>
        <head><title>AI Resume Analyzer</title><style>body{background:#0b0b12;color:#cdd6f4;font-family:sans-serif;padding:2rem;}</style></head>
        <body>
            <h1>AI Resume & ATS Match Analyzer</h1>
            <p>API is active. Endpoints: <code>/health</code>, <code>/api/analyze</code></p>
        </body>
        </html>"""
    )


@app.post("/api/analyze")
async def analyze_resume(
    request: Request,
    file: UploadFile | None = File(None),
    resume_text: str | None = Form(None),
    job_description: str = Form(""),
    title: str = Form(""),
    required_skills_csv: str = Form(""),
    min_years_experience: float = Form(0.0),
) -> dict[str, Any]:
    """Analyze resume against a job description.

    Processes uploads 100% in-memory; never writes files to disk.
    Accepts both multipart/form-data (file upload or form text) and JSON payloads.
    """
    content_type = request.headers.get("content-type", "")

    # 1. Handle JSON body payload
    if "application/json" in content_type:
        try:
            body = await request.json()
            payload = AnalyzeJsonRequest(**body)
            raw_resume = payload.resume_text
            jd_text = payload.job_description
            jd_title = payload.title
            req_skills = payload.required_skills
            min_exp = payload.min_years_experience
            resume_data = parse_resume(raw_resume)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON request payload: {e}")
    # 2. Handle multipart form or file upload
    else:
        if file is not None:
            file_bytes = await file.read()
            if not file_bytes:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            try:
                resume_data = parse_resume(file_bytes, filename=file.filename)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse resume: {e}")
        elif resume_text:
            try:
                resume_data = parse_resume(resume_text)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse resume text: {e}")
        else:
            raise HTTPException(
                status_code=400, detail="Must provide either a PDF file upload or resume_text"
            )

        jd_text = job_description
        jd_title = title
        req_skills = (
            [s.strip() for s in required_skills_csv.split(",") if s.strip()]
            if required_skills_csv
            else []
        )
        min_exp = min_years_experience

    # Construct JobDescription model
    jd = JobDescription(
        raw_text=jd_text or "General Software Engineering Position",
        title=jd_title or "Software Engineer",
        required_skills=req_skills,
        min_years_experience=min_exp,
    )

    # Compute ATS Gauntlet score
    score_result = compute_score(resume_data, jd)

    # Compute skills gap analysis
    skills_gap = identify_competencies(
        resume_skills=resume_data.skills,
        required_skills=score_result.matching_keywords + score_result.missing_critical_keywords,
    )

    return {
        "candidate": {
            "name": resume_data.name or "Candidate",
            "email": resume_data.email,
            "phone": resume_data.phone,
            "experience_years": resume_data.experience_years,
            "detected_skills": resume_data.skills,
            "sections": list(resume_data.sections.keys()),
        },
        "job": {
            "title": jd.title,
            "required_skills": jd.required_skills,
            "min_years_experience": jd.min_years_experience,
        },
        "score": score_result.model_dump(),
        "skills_analysis": skills_gap,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

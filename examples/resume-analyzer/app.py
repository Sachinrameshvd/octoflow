from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from models import ResumeData, JobDescription
from parser import parse_resume
from scoring import compute_score
from skills import normalize_skill, categorize_skills
from typing import Union

app = FastAPI()

@app.get("/health")
def health_check():
    return JSONResponse(content={"status": "healthy"})

@app.post("/api/analyze")
def analyze_resume(file: Union[UploadFile, None] = File(None), json_payload: Union[dict, None] = None):
    if not file and not json_payload:
        raise HTTPException(status_code=400, detail="Either file or json_payload must be provided")

    if file:
        file_content = await file.read()
        resume_data = parse_resume(file_content)
    elif json_payload:
        resume_data = ResumeData(**json_payload)

    job_description = JobDescription()  # Placeholder for job description
    score = compute_score(resume_data, job_description)
    normalized_skills = [normalize_skill(skill) for skill in resume_data.skills]
    categorized_skills = categorize_skills(normalized_skills)

    return JSONResponse(content={
        "score": score,
        "skills": categorized_skills
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI, File, UploadFile, WebSocket
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import skills
import scoring
import models

app = FastAPI()

class ResumeData(BaseModel):
    resume: UploadFile
    job_description: str

class SkillMatch(BaseModel):
    skill: str
    matched: bool
    suggestion: str

@app.post("/analyze")
def analyze(resume_data: ResumeData):
    resume_content = await resume_data.resume.read()
    job_description = resume_data.job_description
    score = scoring.compute_score(resume_content, job_description)
    skills_data = skills.normalize_skill(resume_content)
    categorized_skills = skills.categorize_skills(skills_data)
    matches = [SkillMatch(skill=skill, matched=skill in categorized_skills, suggestion='') for skill in skills_data]
    return {"score": score, "matches": matches}

@app.get("/index.html")
def get_index_html():
    return HTMLResponse(content=open("frontend/static/index.html", "r").read())

@app.get("/app.js")
def get_app_js():
    return HTMLResponse(content=open("frontend/static/app.js", "r").read())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
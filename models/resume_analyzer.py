from fastapi import FastAPI
from pdfminer.high_level import extract_text
from pydantic import BaseModel

app = FastAPI()


class Resume(BaseModel):
    text: str


@app.post("/analyze")
async def analyze_resume(resume: Resume):
    text = extract_text(resume.text)
    # Placeholder for ATS scoring algorithm
    score = 0
    return {"score": score}

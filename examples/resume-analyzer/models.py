from typing import List, Dict


class ResumeData:
    def __init__(self, text: str):
        self.text = text

class JobDescription:
    def __init__(self, text: str):
        self.text = text

class ATSScoreResult:
    def __init__(self, score: float):
        self.score = score

# Placeholder for scoring logic
def compute_atsscore(resume: ResumeData, job_description: JobDescription) -> ATSScoreResult:
    return ATSScoreResult(0.0)
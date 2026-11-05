from dataclasses import dataclass

@dataclass
class ResumeData:
    text: str

@dataclass
class JobDescription:
    text: str

@dataclass
class ATSScoreResult:
    score: float

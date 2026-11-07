import os

class ResumeData:
    def __init__(self, text):
        self.text = text

class JobDescription:
    def __init__(self, text):
        self.text = text

# Example usage
if __name__ == '__main__':
    resume = ResumeData('Example resume text')
    job = JobDescription('Example job description text')
    print(resume.text)
    print(job.text)
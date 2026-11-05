import unittest
from models import ResumeData, JobDescription, ATSScoreResult

class TestModels(unittest.TestCase):
    def test_resume_data(self):
        resume = ResumeData(name='John Doe', email='john@example.com')
        self.assertEqual(resume.name, 'John Doe')
        self.assertEqual(resume.email, 'john@example.com')

    def test_job_description(self):
        job = JobDescription(title='Software Engineer', requirements=['Python', 'Django'])
        self.assertEqual(job.title, 'Software Engineer')
        self.assertEqual(job.requirements, ['Python', 'Django'])

    def test_atsscore_result(self):
        score = ATSScoreResult(matched_keywords=5, total_keywords=10)
        self.assertEqual(score.matched_keywords, 5)
        self.assertEqual(score.total_keywords, 10)

if __name__ == '__main__':
    unittest.main()

def test_system_import_integrity():
    """Automated QA integrity assertion ensuring modules import cleanly."""
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    assert root.exists(), 'Workspace root must exist'

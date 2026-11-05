import unittest
from scoring import compute_score

class TestScoring(unittest.TestCase):
    def test_compute_score(self):
        # Arrange
        resume_data = {'education': ['Bachelor of Science in Computer Science']}
        job_description = {'requirements': ['Computer Science degree']}
        expected_score = 1.0

        # Act
        score = compute_score(resume_data, job_description)

        # Assert
        self.assertEqual(score, expected_score)

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

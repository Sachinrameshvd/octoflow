import pytest
from skills import categorize_skills, identify_competencies

@pytest.fixture
def sample_resume_data():
    return {'skills': ['Python', 'JavaScript', 'AWS']}

@pytest.fixture
def sample_job_description():
    return {'required_skills': ['Python', 'Docker', 'Kubernetes']}

def test_categorize_skills(sample_resume_data):
    result = categorize_skills(sample_resume_data['skills'])
    assert 'languages' in result
    assert 'backend' in result
    assert 'frontend' in result
    assert 'cloud' in result
    assert 'data' not in result
    assert 'devops' not in result

def test_identify_competencies(sample_resume_data, sample_job_description):
    result = identify_competencies(sample_resume_data['skills'], sample_job_description['required_skills'])
    assert 'matched' in result
    assert 'missing' in result
    assert 'synonyms' in result
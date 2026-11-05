import json
import os
from typing import List, Dict, Any

class Skill:
    def __init__(self, name: str, domain: str, synonyms: List[str]):
        self.name = name
        self.domain = domain
        self.synonyms = synonyms

    def match(self, text: str) -> bool:
        return self.name.lower() in text.lower() or any(syn.lower() in text.lower() for syn in self.synonyms)

class SkillsTaxonomy:
    def __init__(self, taxonomy_path: str):
        with open(taxonomy_path, 'r') as f:
            self.taxonomy = json.load(f)

    def categorize_skills(self, text: str) -> Dict[str, List[str]]:
        categorized_skills = {domain: [] for domain in self.taxonomy}
        for skill in self.taxonomy['skills']:
            if skill.match(text):
                categorized_skills[skill.domain].append(skill.name)
        return categorized_skills

    def identify_competencies(self, resume_data: Dict[str, Any], job_description: Dict[str, Any]) -> Dict[str, List[str]]:
        resume_skills = self.categorize_skills(resume_data['text'])
        job_skills = self.categorize_skills(job_description['text'])
        matched_skills = {domain: list(set(resume_skills[domain]) & set(job_skills[domain])) for domain in self.taxonomy}
        missing_skills = {domain: list(set(job_skills[domain]) - set(resume_skills[domain])) for domain in self.taxonomy}
        return {'matched': matched_skills, 'missing': missing_skills}

# Example usage
if __name__ == '__main__':
    taxonomy = SkillsTaxonomy('skills_taxonomy.json')
    resume_data = {'text': 'Python, Django, React, AWS, SQL'}
    job_description = {'text': 'Python, Django, React, AWS, SQL, Kubernetes'}
    competencies = taxonomy.identify_competencies(resume_data, job_description)
    print(competencies)
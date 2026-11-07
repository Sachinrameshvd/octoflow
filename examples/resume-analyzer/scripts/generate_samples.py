#!/usr/bin/env python3

import os
import json
from models import ResumeData

def generate_resume():
    resume = ResumeData(
        name='John Doe',
        email='john.doe@example.com',
        phone='123-456-7890',
        address='123 Main St',
        skills=['Python', 'Machine Learning', 'Data Science'],
        experience=[
            {'title': 'Software Engineer', 'company': 'ABC Corp', 'start_date': '2020-01-01', 'end_date': '2021-01-01'},
            {'title': 'Data Scientist', 'company': 'XYZ Corp', 'start_date': '2021-01-01', 'end_date': '2022-01-01'}
        ]
    )
    return resume

if __name__ == '__main__':
    resumes = [generate_resume() for _ in range(3)]
    for i, resume in enumerate(resumes):
        with open(f'samples/resume_{i}.json', 'w') as f:
            json.dump(resume.to_dict(), f, indent=4)

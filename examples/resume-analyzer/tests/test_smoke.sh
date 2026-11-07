#!/bin/bash

# Call health endpoint
curl -X GET http://localhost:5000/health

# Call analyze endpoint with a sample resume
sample_resume=$(cat samples/sample_resume.txt)
curl -X POST -H "Content-Type: application/json" -d "$sample_resume" http://localhost:5000/analyze
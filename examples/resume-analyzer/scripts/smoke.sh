#!/usr/bin/env bash
# Smoke test script for AI Resume & ATS Match Analyzer
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"
BASE_URL="http://${HOST}:${PORT}"

# Detect Python interpreter with uvicorn available
PYTHON="${PYTHON:-}"
if [[ -z "${PYTHON}" ]]; then
  if python3 -m uvicorn --version >/dev/null 2>&1; then
    PYTHON="python3"
  elif command -v python3.12 >/dev/null 2>&1; then
    PYTHON="python3.12"
  else
    PYTHON="python3"
  fi
fi

echo "========================================================================"
echo "◈ Resume Analyzer: Smoke Verification"
echo "◈ Target: ${BASE_URL}"
echo "========================================================================"

SERVER_PID=""

cleanup() {
  if [[ -n "${SERVER_PID}" ]]; then
    echo "Stopping test background server (PID: ${SERVER_PID})..."
    kill "${SERVER_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# 1. Start server if not running
if ! curl -s -f "${BASE_URL}/health" >/dev/null 2>&1; then
  echo "• Starting uvicorn background test instance on ${BASE_URL} using ${PYTHON}..."
  PYTHONPATH="${APP_DIR}" "${PYTHON}" -m uvicorn app:app --app-dir "${APP_DIR}" --host "${HOST}" --port "${PORT}" &
  SERVER_PID=$!
  
  # Wait for readiness
  for i in {1..20}; do
    if curl -s -f "${BASE_URL}/health" >/dev/null 2>&1; then
      break
    fi
    sleep 0.5
  done
fi

# 2. Test /health endpoint
echo "• Testing GET /health..."
HEALTH_RESP=$(curl -s -f "${BASE_URL}/health")
echo "  Response: ${HEALTH_RESP}"
if [[ "${HEALTH_RESP}" != *"healthy"* ]]; then
  echo "✖ Health check failed!"
  exit 1
fi
echo "  ✓ Health check passed."

# 3. Ensure synthetic sample exists
SAMPLE_PDF="${APP_DIR}/samples/sample_backend_senior.pdf"
if [[ ! -f "${SAMPLE_PDF}" ]]; then
  echo "• Generating synthetic sample PDF..."
  "${PYTHON}" "${APP_DIR}/scripts/generate_samples.py"
fi

# 4. Test /api/analyze with PDF upload
echo "• Testing POST /api/analyze with synthetic PDF (${SAMPLE_PDF})..."
ANALYZE_RESP=$(curl -s -f -X POST "${BASE_URL}/api/analyze" \
  -F "file=@${SAMPLE_PDF}" \
  -F "title=Senior Backend Engineer" \
  -F "min_years_experience=4.0" \
  -F "required_skills_csv=python,fastapi,docker,kubernetes,postgresql" \
  -F "job_description=Seeking a Senior Backend Engineer proficient in Python, FastAPI, Docker, and Kubernetes.")

echo "  Parsing response summary..."
OVERALL_SCORE=$(echo "${ANALYZE_RESP}" | "${PYTHON}" -c 'import sys, json; data=json.load(sys.stdin); print(data["score"]["overall_score"])')
CANDIDATE_NAME=$(echo "${ANALYZE_RESP}" | "${PYTHON}" -c 'import sys, json; data=json.load(sys.stdin); print(data["candidate"]["name"])')
MATCHED_SKILLS=$(echo "${ANALYZE_RESP}" | "${PYTHON}" -c 'import sys, json; data=json.load(sys.stdin); print(", ".join(data["score"]["matching_keywords"]))')

echo "  ✓ Candidate: ${CANDIDATE_NAME}"
echo "  ✓ Overall ATS Score: ${OVERALL_SCORE}%"
echo "  ✓ Matched Skills: ${MATCHED_SKILLS}"

if (( $(echo "${OVERALL_SCORE} < 60.0" | bc -l) )); then
  echo "✖ ATS score too low for high-match candidate!"
  exit 1
fi

echo "========================================================================"
echo "✔ SMOKE TEST PASSED: All endpoints operational."
echo "========================================================================"

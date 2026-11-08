# AI Resume & ATS Match Analyzer

> **Built with OctoFlow Swarm Orchestration**  
> A transparent showcase of autonomous software development using local open-weight models (`qwen2.5-coder:7b` via Ollama), featuring full provenance tracking, honest accounting of automated versus manual code, and zero-persistence privacy.

---

## Overview

The **AI Resume & ATS Match Analyzer** is a lightweight, turnkey, privacy-first web application that evaluates candidate resumes against target job descriptions. It provides:

1. **In-Memory PDF Extraction**: Extracts text, contact info, and structural sections directly from in-memory byte streams using `pypdf`, guaranteeing **zero disk writes** for candidate confidentiality.
2. **Skills-Gap Analysis & Normalization**: Maps candidate skills against a categorized taxonomy (`skills_taxonomy.json`) with automated alias resolution (e.g., `k8s` → `kubernetes`, `golang` → `go`, `postgres` → `postgresql`).
3. **ATS Gauntlet Scoring**: Computes a transparent, multi-factor match score combining keyword coverage, experience alignment, and formatting completeness.
4. **FastAPI Web Service**: High-performance asynchronous API providing `GET /health` and `POST /api/analyze` supporting both multipart PDF uploads and structured JSON requests.
5. **Dark-Mode Single-Page Dashboard**: Accessible, responsive cyber-styled interface (`static/index.html` & `static/app.js`) with drag-and-drop resume upload, interactive ATS gauge, matched/missing skill badges, and actionable recommendations.

---

## Architecture

```
examples/resume-analyzer/
├── app.py                      # FastAPI application, route handlers, and static mount
├── models.py                   # Pydantic v2 domain schemas (ResumeData, JobDescription, ATSScoreResult)
├── parser.py                   # In-memory PDF text extraction and regex section parser
├── scoring.py                  # ATS heuristic scoring gauntlet (keywords, experience, formatting)
├── skills.py                   # Skills taxonomy loader, alias normalization, and gap analyzer
├── skills_taxonomy.json        # Domain taxonomy mapping 100+ skills and canonical aliases
├── static/
│   ├── index.html              # Accessible dark-mode single-page dashboard
│   └── app.js                  # Vanilla JS frontend with drag-and-drop and real-time ATS gauge
├── samples/                    # Synthetic non-PII PDF resumes for testing
│   ├── sample_backend_senior.pdf
│   ├── sample_frontend_mid.pdf
│   └── sample_data_engineer.pdf
├── scripts/
│   ├── generate_samples.py     # Script to generate synthetic test resumes via ReportLab
│   └── smoke.sh                # End-to-end smoke test script with live API verification
├── tests/                      # 26 automated unit and integration tests (100% in-memory)
│   ├── test_app.py
│   ├── test_dashboard.py
│   ├── test_models.py
│   ├── test_parser.py
│   ├── test_privacy.py         # Zero-disk-persistence & synthetic data verification
│   ├── test_scoring.py
│   └── test_skills.py
├── provenance/                 # Transparent records of OctoFlow swarm runs and receipts
│   ├── FAILURES.md             # Detailed log of swarm defects, hallucinations, and human fixes
│   ├── mission-1-meta.json & mission-1-receipt.json
│   ├── mission-2-meta.json & mission-2-receipt.json
│   ├── mission-3-meta.json & mission-3-receipt.json
│   ├── mission-4-meta.json & mission-4-receipt.json
│   ├── mission-5-meta.json & mission-5-receipt.json
│   └── mission-6-meta.json & mission-6-receipt.json
└── requirements.txt            # Minimal runtime dependencies
```

---

## Provenance & Honest Accounting

This showcase was built incrementally across **6 autonomous missions** using OctoFlow's 8-arm cephalopod swarm powered by a local Ollama instance (`qwen2.5-coder:7b`). To maintain strict technical credibility, we record the exact provenance of what the autonomous swarm produced versus what required human engineering intervention:

| Mission | Objective / Component | Run ID | LLM Calls | Tokens Spent | Tokens Avoided | Swarm Lines (+/-) | Manual Edits (+/-) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | Data Models & ATS Scoring | `1793846906-660ca2` | 34 | 21,530 | 5,372 | +161 / -0 | +499 / -152 |
| **2** | In-Memory PDF Extraction | `1793885711-897ab6` | 21 | 20,400 | 6,800 | +132 / -63 | +421 / -126 |
| **3** | Skills Taxonomy & Gap Analysis | `1793888056-f4c83b` | 44 | 35,795 | 10,038 | +161 / -0 | +387 / -156 |
| **4** | FastAPI Endpoints (`/health`, `/analyze`) | `1793891796-d7c96d` | 23 | 18,561 | 4,303 | +113 / -0 | +447 / -95 |
| **5** | Dark-Mode SPA Dashboard | `1794048922-910979` | 31 | 24,193 | 7,048 | +186 / -330 | +1152 / -186 |
| **6** | Wiring, Samples, Smoke Script & Docs | `1794049840-56720e` | 29 | 22,637 | 7,704 | +249 / -63 | +368 / -239 |
| **Total** | **Full Application Build** | — | **182** | **143,116** | **41,265** | **+1,002 / -456** | **+3,274 / -954** |

### Swarm Performance Insights
- **Token Efficiency**: OctoFlow's local sensory gating avoided **41,265 tokens (22.4% reduction)** by resolving repetitive arm decisions via local reflex routing rather than central LLM escalation.
- **Observed Swarm Failure Modes**:
  1. *Regressive Overwriting*: Local 7B models frequently overwrite existing files with toy code or PyTorch templates when prompted incrementally.
  2. *Framework Semantic Bleed*: Tendency to bleed Flask patterns (`app.test_client()`, port 5000) into FastAPI applications (`TestClient(app)`, port 8000).
  3. *Syntax Confusion*: Async/await mismatches in endpoint definitions (`def` vs `async def`).
  4. *Directory Sprawl*: Unsolicited generation of React/Vite scaffolding (`frontend/`) and deep subfolders (`deploy/`, `train/`) instead of clean flat packages.

Full failure post-mortems and remediation details are recorded in [`provenance/FAILURES.md`](provenance/FAILURES.md) and [`docs/audit/P7.2-feedback.md`](../../docs/audit/P7.2-feedback.md).

---

## Quickstart

### 1. Installation

Create and activate a virtual environment, then install dependencies:

```bash
cd examples/resume-analyzer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Generate Synthetic Test Resumes

Generate the synthetic sample resumes used for testing and demonstrations:

```bash
python scripts/generate_samples.py
```

This creates 3 realistic, non-PII resumes in `samples/`:
- `sample_backend_senior.pdf` (Alex Mercer: Python, FastAPI, Docker, Kubernetes, PostgreSQL)
- `sample_frontend_mid.pdf` (Jordan Lee: TypeScript, React, Next.js, Tailwind CSS)
- `sample_data_engineer.pdf` (Samira Khan: Python, Apache Spark, Kafka, AWS, Snowflake)

### 3. Run the Web Application

Start the FastAPI server via Uvicorn:

```bash
uvicorn app:app --reload --port 8000
```

Open your browser to **`http://localhost:8000/`** to interact with the dark-mode dashboard.

### 4. Run the Test Suite

Execute the 26 unit, integration, and privacy tests:

```bash
pytest tests -v
```

### 5. Run the Automated Smoke Verification

Run the end-to-end smoke verification script:

```bash
bash scripts/smoke.sh
```

---

## Privacy & Security Guarantees

- **Zero Disk Persistence**: Uploaded PDF resumes and parsed strings are processed entirely in-memory using `BytesIO` streams. No candidate resume files or temporary files are ever written to the server's local file system or database.
- **Zero Cloud Leakage**: In standard configuration, all text extraction, taxonomy normalization, and scoring calculations run locally on your host CPU.
- **Strictly Synthetic Fixtures**: All sample documents and test fixtures utilize RFC 2606 reserved domains (`@example.com`) and synthetic numbers. Verified automatically by `tests/test_privacy.py`.

---

## Limitations & Disclaimer

- **Heuristic Scoring Model**: The ATS match score produced by this application is based on transparent heuristic algorithms (weighted keyword coverage, regex-estimated years of experience, and structural section detection). It is **not** an enterprise proprietary ATS score (such as Workday, Taleo, Greenhouse, or Lever) and should not be used as an authoritative predictor of candidate hiring outcomes.
- **PDF Layout Complexity**: In-memory text extraction via `pypdf` operates best on standard single-column or cleanly tagged two-column resumes. Heavily stylized graphics, rasterized scanned images, or table-based column layouts without explicit reading orders may experience reduced extraction fidelity.

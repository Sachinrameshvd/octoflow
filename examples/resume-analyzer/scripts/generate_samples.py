#!/usr/bin/env python3
"""Generate 3 synthetic, non-PII PDF resumes for demonstration and testing."""

from __future__ import annotations

import io
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"


def generate_pdf(
    filename: str,
    name: str,
    title: str,
    contact_line: str,
    years_text: str,
    experience_bullets: list[str],
    education_line: str,
    skills_csv: str,
    projects: list[str],
) -> Path:
    """Generate a clean, single-page synthetic PDF resume without real personal data."""
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SAMPLES_DIR / filename

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, height - 72, name)

    c.setFont("Helvetica", 12)
    c.drawString(72, height - 90, title)

    c.setFont("Helvetica", 9)
    c.drawString(72, height - 106, contact_line)

    # Line separator
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.line(72, height - 116, width - 72, height - 116)

    y = height - 136

    # Summary
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Professional Summary")
    y -= 16
    c.setFont("Helvetica", 10)
    c.drawString(72, y, f"Experienced {title.lower()} with {years_text}.")
    y -= 26

    # Experience
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Work Experience")
    y -= 16
    for bullet in experience_bullets:
        c.setFont("Helvetica", 9.5)
        c.drawString(84, y, f"• {bullet}")
        y -= 16
    y -= 10

    # Education
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Education")
    y -= 16
    c.setFont("Helvetica", 9.5)
    c.drawString(84, y, education_line)
    y -= 26

    # Skills
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Technical Skills")
    y -= 16
    c.setFont("Helvetica", 9.5)
    c.drawString(84, y, skills_csv)
    y -= 26

    # Projects
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Key Projects")
    y -= 16
    for proj in projects:
        c.setFont("Helvetica", 9.5)
        c.drawString(84, y, f"• {proj}")
        y -= 16

    c.save()
    buffer.seek(0)
    out_path.write_bytes(buffer.getvalue())
    return out_path


def main():
    print("Generating synthetic non-PII demo resumes in samples/...")

    # Sample 1: Senior Backend Engineer (High match candidate)
    p1 = generate_pdf(
        filename="sample_backend_senior.pdf",
        name="Alex Mercer",
        title="Staff Backend Engineer",
        contact_line="Email: alex.mercer.synthetic@example.com | Phone: (555) 012-3456 | Seattle, WA",
        years_text="6+ years of distributed backend and cloud architecture experience",
        experience_bullets=[
            "Senior Software Engineer, TechNova (2020 - Present): Architected microservices with Python, FastAPI, and Kubernetes.",
            "Backend Engineer, CloudScale (2018 - 2020): Scaled PostgreSQL databases and Redis caching layers.",
            "Software Developer, DataFlow (2017 - 2018): Designed event pipelines processing 20k events/sec.",
        ],
        education_line="B.S. in Computer Science, University of Washington (2017)",
        skills_csv="Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, AWS, CI/CD, Go, Linux",
        projects=[
            "Distributed Task Queue: Built high-throughput Celery/Redis cluster handling 100k daily jobs.",
            "FastAPI Gateway: Unified OAuth2 auth and request routing across 12 upstream services.",
        ],
    )
    print(f"  ✓ Created {p1.name}")

    # Sample 2: Mid-Level Frontend Engineer (Skills gap candidate for backend JD)
    p2 = generate_pdf(
        filename="sample_frontend_mid.pdf",
        name="Jordan Taylor",
        title="Frontend Engineer",
        contact_line="Email: jordan.taylor.synthetic@example.com | Phone: (555) 019-8765 | San Francisco, CA",
        years_text="3.5 years of experience building responsive, accessible web dashboards",
        experience_bullets=[
            "Frontend Engineer, WebCraft Labs (2021 - Present): Built React/TypeScript design systems and state stores.",
            "UI Developer, PixelPeak (2020 - 2021): Optimized Core Web Vitals and SPA load performance.",
        ],
        education_line="B.A. in Digital Design & Informatics, San Francisco State (2020)",
        skills_csv="React, TypeScript, JavaScript, Next.js, Tailwind CSS, HTML5, Redux, Jest, Git",
        projects=[
            "Design System: Created 40+ accessible WCAG 2.2 AA compliant React UI components.",
            "E-Commerce Checkout: Built zero-layout-shift checkout flow with 98 Lighthouse score.",
        ],
    )
    print(f"  ✓ Created {p2.name}")

    # Sample 3: Data Engineer (Cross-disciplinary candidate)
    p3 = generate_pdf(
        filename="sample_data_engineer.pdf",
        name="Samira Khan",
        title="Data Engineer",
        contact_line="Email: samira.khan.synthetic@example.com | Phone: (555) 018-9922 | Austin, TX",
        years_text="5+ years of data warehousing, ETL engineering, and streaming data experience",
        experience_bullets=[
            "Lead Data Engineer, DataSphere (2020 - Present): Maintained Snowflake and Kafka data lake architectures.",
            "BI Engineer, MetroMetrics (2019 - 2020): Created automated Airflow DAG pipelines and Postgres warehouses.",
        ],
        education_line="B.S. in Statistics & Computer Science, UT Austin (2019)",
        skills_csv="Python, SQL, PostgreSQL, Kafka, Spark, Pandas, Snowflake, Airflow, Docker, AWS",
        projects=[
            "Real-Time Stream Processor: Deployed Kafka-to-Snowflake pipelines handling 10M records/day.",
            "Automated ETL Audit: Python verification tool reducing data drift alerts by 85%.",
        ],
    )
    print(f"  ✓ Created {p3.name}")

    print("\n✓ All 3 synthetic non-PII resumes generated successfully.")


if __name__ == "__main__":
    main()

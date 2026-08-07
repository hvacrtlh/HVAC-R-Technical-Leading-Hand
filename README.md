# TechCheck HVAC&R — Proof of Concept

A simple Streamlit proof-of-concept for HVAC&R technical and commercial QA.

## Included

- Dashboard
- Service Report Review
- Challenge the Technician
- Quote Review with genuine AI reasoning
- Sounding Board
- PDF, DOCX and text report extraction
- Flat project structure to make GitHub web uploads simple

## Upload to GitHub

Upload every file in this folder directly to the root of your GitHub repository.

Your repo should look like:

- app.py
- ai_backend.py
- prompts.py
- report_parser.py
- requirements.txt
- runtime.txt
- README.md
- sample_report.txt

There are no required subfolders.

## Streamlit Secrets

In Streamlit Community Cloud:

App settings -> Secrets

Add:

```toml
OPENAI_API_KEY = "sk-proj-your-key-here"
OPENAI_MODEL = "gpt-5.5"
```

Do not put your real API key in GitHub.

## Good proof-of-concept tests

### Quote test
Scope: Supply and install new condensate drain to a standard high wall split system.
Labour: 20 hours
Materials/equipment: $10,000

The AI should challenge the allowance unless the scope explains major access, builder's works, EWP/scaffold or other complexity.

### Service report test
Use `sample_report.txt` and enter 14.89 labour hours.

## Important

This is a testing/proof-of-concept application, not a production system for confidential customer data.

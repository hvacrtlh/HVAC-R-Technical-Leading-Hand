# TechCheck HVAC&R — Proof of Concept v1

This is the flat-file Streamlit proof of concept.

## Upload

Upload every file in this ZIP directly into the ROOT of the GitHub repository.

Required files:
- app.py
- ai_backend.py
- prompts.py
- report_parser.py
- requirements.txt
- runtime.txt
- sample_report.txt

There are no required folders.

## Streamlit secrets

Under Streamlit -> App settings -> Secrets:

```toml
OPENAI_API_KEY = "sk-proj-your-key-here"
OPENAI_MODEL = "gpt-5.5"
```

Do not put the real API key in GitHub.

## Test 1 — Quote Review

Scope:
Supply and install new condensate drain to standard high wall split system.

Labour:
20 hours

Materials/equipment allowance:
10000

The system should challenge those allowances unless the scope explains significant complexity.

## Test 2 — Service Review

Upload sample_report.txt and enter 14.89 hours.

## Included features

- Service report review
- Challenge the technician
- Quote review
- Sounding Board
- PDF/DOCX/TXT extraction
- Flat project structure

# TechCheck HVAC&R — Clean Proof of Concept

This is the flat-file Streamlit testing build.

## Upload to GitHub

Delete old Python files from the repository first.

Then upload EVERY file from this ZIP directly into the ROOT of the repository.

The repository should show:

- app.py
- ai_backend.py
- prompts.py
- report_parser.py
- self_check.py
- requirements.txt
- README.md
- sample_report.txt

There are no required subfolders.

## Streamlit Secret

Go to:

Streamlit -> App settings -> Secrets

Add only:

```toml
OPENAI_API_KEY = "sk-proj-your-real-key"
```

Do not put the real API key in GitHub.

## Proof-of-concept test

### Quote Review

Scope:
Supply and install new condensate drain to standard high wall split system.

Labour:
20 hours

Materials/equipment:
10000

The AI should challenge the quotation unless the scope identifies significant complexity that could justify it.

### Service Report Review

Upload sample_report.txt and enter:

14.89 hours

### Sounding Board

Try:
Cool room is icing up at the TXV outlet and box temperature is not pulling down properly.

## Self-check

If you have Python installed locally, run:

python self_check.py

It should display:

PASS - project structure and Python syntax are valid.

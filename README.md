# TechCheck HVAC&R — testing project

A Streamlit pilot for independent HVAC&R technical and commercial QA.

## What changed

The app is now split into a thin UI (`app.py`) and backend modules under `techcheck/`.

All OpenAI calls go through `techcheck/ai.py`. The selected model is stored on `AIClient`, so page code never relies on an undefined `model` variable.

## Features

- Service docket / technician report review
- Quote review with live AI commercial reasoning
- Sounding Board fault-finding chat
- PDF / DOCX / text extraction
- Live AI and clearly-labelled demonstration modes
- Automated tests
- GitHub Actions test workflow
- Python 3.12 deployment target

## Streamlit Community Cloud

Entrypoint:

`app.py`

Secrets:

```toml
OPENAI_API_KEY = "sk-proj-..."
OPENAI_MODEL = "gpt-5.5"
```

Do not put the API key in GitHub.

## GitHub upload

Upload the **contents of this folder** to the root of your repository. Keep the `.github`, `.streamlit`, `techcheck`, and `tests` folders.

GitHub Actions runs `pytest` after each push. A green tick on the commit means the automated tests passed.

## Pilot limitation

This is still a testing build. It does not yet provide production authentication, permanent multi-tenant storage, billing, or enterprise security controls.

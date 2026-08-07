# TechCheck HVAC&R — Commercial Pilot

A polished Streamlit pilot for HVAC&R technical quality assurance.

## Included

- Dashboard
- Technician report review
- Sounding Board diagnostic chat
- Preliminary quotation review
- Technician scorecards
- Analytics
- Review history
- Company standards
- Streamlit Secrets configuration

## Deploy

Upload all files to the root of the existing GitHub repository. Streamlit should automatically redeploy.

## Streamlit Secrets

```toml
OPENAI_API_KEY = "sk-proj-..."
OPENAI_MODEL = "gpt-4.1-mini"
APP_PASSWORD = "optional-password"
```

Do not commit secrets to GitHub.

## Important

This is a pilot, not a production SaaS platform. Use de-identified reports until privacy, security, storage and organisational approvals are completed.

## Streamlit Community Cloud test deployment
Upload the files in this folder to the root of the GitHub repository. Do not upload Python cache files.

The repository should contain at least:
- app.py
- requirements.txt
- runtime.txt
- .gitignore
- README.md

Set the OpenAI credentials in Streamlit **App settings > Secrets**, not in GitHub:

```toml
OPENAI_API_KEY = "your-key"
OPENAI_MODEL = "your-available-model-name"
```

If Streamlit still reports an installation error, open **Manage app > Logs** and use the final package error to identify the failing dependency.

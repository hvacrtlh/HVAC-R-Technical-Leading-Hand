# TechCheck HVAC&R — Commercial MVP

A Streamlit-based technical QA application for reviewing HVAC&R technician reports before they are issued to customers.

## What is included

- Live OpenAI review and clearly labelled demonstration mode.
- Adaptive HVAC&R technical review prompt.
- Work-order, customer, site and technician fields.
- PDF, DOCX, TXT, CSV and Markdown extraction.
- Labour-hours and parts justification review.
- Dashboard and saved review history using SQLite.
- Review register CSV and individual JSON exports.
- Company-specific technical standards.
- Optional private-beta password.
- Indicative plans and production-readiness checklist.

## Deploy update to Streamlit

Upload/replace these files in the existing GitHub repository:

- `app.py`
- `requirements.txt`
- `README.md`

Streamlit normally redeploys automatically after the GitHub commit.

## Streamlit Secrets

Open the app in Streamlit Community Cloud, then **App settings → Secrets**:

```toml
OPENAI_API_KEY = "sk-proj-your-key"
OPENAI_MODEL = "gpt-4.1-mini"
APP_PASSWORD = "optional-private-beta-password"
```

Do not put API keys in GitHub.

## Important limitations

This is a commercial MVP, not a production SaaS platform. SQLite data stored on free Streamlit hosting may be lost when the instance is rebuilt or sleeps. Before charging customers, replace it with a hosted database and add proper authentication, subscriptions, usage metering, encrypted storage, audit logs, privacy terms and security review.

## Suggested production architecture

- Frontend: Next.js or React.
- Backend: FastAPI.
- Database/auth: PostgreSQL + Supabase or Azure SQL + Entra ID.
- Billing: Stripe.
- File storage: Azure Blob or S3-compatible storage.
- AI: server-side OpenAI Responses API.

## Technical Leading Hand chat

The app includes an **Ask Technical Leading Hand** page. It can use the most recent structured review as context, analyse a separately uploaded report, or answer a general HVAC&R question. Live chat requires `OPENAI_API_KEY` and `OPENAI_MODEL` in Streamlit Secrets.

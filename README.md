# HVAC&R Technical Review System — MVP

A Streamlit web application for pre-issue QA of HVAC&R technician reports.

## Included

- Paste notes or upload PDF, DOCX, TXT, CSV or Markdown.
- Claimed labour-hours review.
- Adaptive modules for refrigeration, controls, VRF/VRV, chillers, PM audits and general HVAC&R.
- Diagnosis/evidence challenge, parts justification, risk review, coaching and customer-ready summary.
- Demonstration mode works without an API key.
- Live mode connects server-side to the OpenAI Responses API.
- JSON export for future database, Power Automate or job-management integration.

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
set OPENAI_API_KEY=your_key_here      # Windows Command Prompt
# or: $env:OPENAI_API_KEY="your_key_here"  # PowerShell
# or: export OPENAI_API_KEY=your_key_here   # macOS/Linux

streamlit run app.py
```

Then open the local address shown by Streamlit, usually `http://localhost:8501`.

## Recommended production architecture

1. Microsoft shared mailbox receives contractor emails.
2. Power Automate copies approved attachments and metadata to a secure intake endpoint or SharePoint library.
3. Backend extracts text/files and calls the AI review service.
4. Structured review is stored against work order, asset, technician and customer.
5. Supervisor sees a review queue and makes the final decision.
6. Only approved reports are released to the customer.

## Important production controls

- Keep API keys server-side; never embed them in browser JavaScript.
- Confirm organisational approval before sending customer, asset or employee data to any AI provider.
- Add authentication, role-based access, audit logs, retention rules and encryption.
- Do not auto-approve technical, safety, warranty or compliance decisions.
- Add a technician feedback workflow so supervisor corrections can improve company rules without silently retraining on unverified feedback.
- Use manufacturer manuals and company standards as controlled reference documents, with version and source tracking.

## Next build stage

- Outlook/Power Automate email ingestion.
- Scanned PDF and image handling.
- SQL database and review history.
- Company rule editor and labour benchmark table.
- Technician/branch dashboards and recurring issue analytics.
- Quote line-item review and approval workflow.

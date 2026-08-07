import io
import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from docx import Document
from openai import OpenAI
from pypdf import PdfReader

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "hvacr_reviews.db"

st.set_page_config(page_title="TechCheck HVAC&R", page_icon="🛠️", layout="wide")

SYSTEM_PROMPT = r"""
You are an independent Senior HVAC&R Technical Manager reviewing technician reports before they are issued to a customer.
Protect both contractor and customer. Do not merely agree with the technician. Require evidence, identify assumptions,
challenge expensive repairs, check labour reasonableness, and distinguish symptoms from root cause.

ADAPTIVE REVIEW
First classify the job and activate only relevant modules: refrigeration/cold room, DX air conditioning, VRF/VRV,
controls/BMS, electrical, hydronics, chiller, cooling tower, heat pump/pool heating, ventilation/exhaust, PM audit,
quotation/additional works, compliance, or general mechanical.

MANDATORY REVIEW
1. Job summary: complaint, findings, root cause, work completed, outstanding work, criticality.
2. Diagnosis: Supported / Possibly Supported / Not Supported, with evidence for and against.
3. Activated modules and why.
4. Technical analysis of all readings and observations. Never invent missing readings.
5. Missing tests/evidence, prioritised by what most increases diagnostic confidence.
6. Parts review: each recommended/replaced part, justification YES/NO/UNSURE, confidence 0-100%, alternatives.
7. Labour analysis: estimate reasonable onsite labour range, compare with claimed hours, and account for access,
   defrosting, waiting/stabilisation, multiple technicians, commissioning, documentation and return visits.
8. Report quality: clarity, sequence, professionalism, customer defensibility, photos/evidence.
9. Risks: callback, safety, financial, warranty, compliance, reputation.
10. Senior Technician Challenge: alternatives, cheapest sensible next step, strongest missing test, symptom vs root cause,
    and whether the recommendation is sufficiently evidenced to spend the customer's money.
11. Coaching feedback: what was done well and what should improve.
12. Final decision: Approve / Approve with Comments / Request Further Information / Reject Recommendation.

COMPANY RULES
- Expensive component replacements require direct evidence, not inference alone.
- Compressor recommendations should normally include electrical checks, operating readings, system condition and cause of failure.
- TXV/EEV recommendations should normally address load, airflow, charge, restriction, bulb mounting/insulation, equaliser and controls.
- Controller/sensor faults require calibration, offsets, placement, setpoint/deadband and actual-temperature comparison.
- Refrigeration conclusions should use refrigerant type and saturated temperatures where possible.
- A successful outcome does not retroactively prove every earlier diagnosis.
- Avoid false precision. State uncertainty clearly.

Return valid JSON only using this exact structure:
{
  "job_classification": {"type": "", "activated_modules": [""], "criticality": "Low|Medium|High|Critical"},
  "executive_summary": "",
  "diagnosis": {"rating": "Supported|Possibly Supported|Not Supported", "confidence": 0, "analysis": "", "root_cause": ""},
  "technical_findings": [{"finding": "", "assessment": "Good|Concern|Missing|Neutral", "explanation": ""}],
  "missing_evidence": [{"priority": "High|Medium|Low", "item": "", "why": ""}],
  "parts_review": [{"part": "", "justified": "YES|NO|UNSURE", "confidence": 0, "reason": "", "alternatives": [""]}],
  "labour_review": {"claimed_hours": 0, "reasonable_low": 0, "reasonable_high": 0, "rating": "Unusually Low|Reasonable|High|Excessive|Cannot Assess", "analysis": ""},
  "risk_review": [{"risk": "Callback|Safety|Financial|Warranty|Compliance|Reputation", "level": "Low|Medium|High", "explanation": ""}],
  "senior_technician_challenge": [{"question": "", "answer": ""}],
  "questions_for_technician": [""],
  "coaching": {"done_well": [""], "improvements": [""], "better_approach": [""]},
  "scores": {"fault_finding": 0, "evidence": 0, "technical_quality": 0, "efficiency": 0, "labour_accuracy": 0, "report_quality": 0, "customer_confidence": 0, "overall_100": 0},
  "final_decision": {"decision": "Approve|Approve with Comments|Request Further Information|Reject Recommendation", "confidence": 0, "justification": ""},
  "customer_ready_summary": ""
}
"""


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            work_order TEXT,
            customer TEXT,
            site TEXT,
            technician TEXT,
            report_name TEXT,
            claimed_hours REAL,
            mode TEXT,
            decision TEXT,
            overall_score INTEGER,
            report_text TEXT,
            review_json TEXT
        )
        """)
        conn.commit()


def save_review(meta: dict[str, Any], report_text: str, result: dict[str, Any], mode: str) -> int:
    decision = result.get("final_decision", {}).get("decision", "")
    score = int(result.get("scores", {}).get("overall_100", 0) or 0)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """INSERT INTO reviews
            (created_at, work_order, customer, site, technician, report_name, claimed_hours, mode,
             decision, overall_score, report_text, review_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().isoformat(timespec="seconds"), meta.get("work_order", ""), meta.get("customer", ""),
                meta.get("site", ""), meta.get("technician", ""), meta.get("report_name", ""),
                float(meta.get("hours", 0)), mode, decision, score, report_text, json.dumps(result),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def load_reviews() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT id, created_at, work_order, customer, site, technician, report_name, claimed_hours, mode, decision, overall_score FROM reviews ORDER BY id DESC",
            conn,
        )


def get_review(review_id: int) -> tuple[str, dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT report_text, review_json FROM reviews WHERE id = ?", (review_id,)).fetchone()
    if not row:
        raise ValueError("Review not found")
    return row[0], json.loads(row[1])


def extract_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    if name.endswith(".docx"):
        doc = Document(io.BytesIO(data))
        lines = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                lines.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(lines)
    if name.endswith((".txt", ".csv", ".md")):
        return data.decode("utf-8", errors="replace")
    raise ValueError("Supported files: PDF, DOCX, TXT, CSV and MD.")


def parse_json_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The AI response did not contain JSON.")
    return json.loads(text[start:end + 1])


def live_review(report: str, hours: float, context: str, standards: str, model: str) -> dict[str, Any]:
    client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY")))
    user_input = f"""Review this HVAC&R technician report.
Claimed total labour hours: {hours:.2f}
Additional company/job context: {context or 'None provided'}
Company-specific standards: {standards or 'Use the default standards in the system instructions.'}

TECHNICIAN REPORT:
{report}
"""
    response = client.responses.create(model=model, instructions=SYSTEM_PROMPT, input=user_input)
    return parse_json_response(response.output_text)


def demo_review(report: str, hours: float) -> dict[str, Any]:
    lower = report.lower()
    modules = []
    for keywords, module in [
        (("cool room", "freezer", "txv", "r404", "evaporator"), "Refrigeration / Cold Room"),
        (("controller", "sensor", "offset", "thermostat"), "Controls"),
        (("chiller",), "Chiller / Hydronics"),
        (("vrf", "vrv", "refnet"), "VRF / VRV"),
        (("pm", "preventative maintenance"), "PM Audit"),
        (("quote", "quotation", "additional works"), "Quotation / Additional Works"),
    ]:
        if any(k in lower for k in keywords):
            modules.append(module)
    modules = modules or ["General HVAC&R"]
    offset, txv, compressor = "offset" in lower, "txv" in lower, "compressor" in lower
    heavy_defrost = "ice" in lower and any(k in lower for k in ("melt", "defrost", "block"))
    reasonable_low, reasonable_high = (8.0, 14.0) if heavy_defrost else (2.0, 7.0)
    labour_rating = "Reasonable" if reasonable_low <= hours <= reasonable_high + 1 else ("High" if hours > reasonable_high else "Unusually Low")
    key_part = "Compressor" if compressor else ("TXV" if txv else "No major part identified")
    return {
        "job_classification": {"type": modules[0], "activated_modules": modules, "criticality": "Medium"},
        "executive_summary": "Demonstration review only. It uses basic rules to prove the workflow; select Live AI for a report-specific technical assessment.",
        "diagnosis": {"rating": "Possibly Supported", "confidence": 65, "analysis": "The repair path may be plausible, but demonstration mode cannot perform full technical reasoning.", "root_cause": "Controller configuration/calibration appears relevant." if offset else "Insufficient information to confirm a single root cause."},
        "technical_findings": [
            {"finding": "Adaptive modules", "assessment": "Good", "explanation": ", ".join(modules)},
            {"finding": "Controller calibration", "assessment": "Good" if offset else "Missing", "explanation": "Offsets and actual-temperature comparison are key control checks."},
            {"finding": f"{key_part} justification", "assessment": "Concern" if (txv or compressor) else "Neutral", "explanation": "Major components require an evidence chain, not symptoms alone."},
        ],
        "missing_evidence": [
            {"priority": "High", "item": "Evidence chain", "why": "Link each conclusion and part recommendation to the tests that support it."},
            {"priority": "Medium", "item": "Time breakdown", "why": "Break labour down by visit and task so the charge is defensible."},
        ],
        "parts_review": [{"part": key_part, "justified": "UNSURE", "confidence": 50, "reason": "Demonstration mode cannot validate component failure.", "alternatives": ["Controls", "Sensor calibration", "Airflow/load", "Charge or restriction"]}],
        "labour_review": {"claimed_hours": hours, "reasonable_low": reasonable_low, "reasonable_high": reasonable_high, "rating": labour_rating, "analysis": "Assess defrost time, access, stabilisation, return visits and documentation."},
        "risk_review": [
            {"risk": "Callback", "level": "Medium", "explanation": "Root cause and contributing faults must be separated."},
            {"risk": "Financial", "level": "Medium", "explanation": "Weak part justification can lead to customer challenge."},
        ],
        "senior_technician_challenge": [
            {"question": "What else could cause the symptoms?", "answer": "Controls, sensor placement, airflow/load, charge or restriction."},
            {"question": "What test most increases confidence?", "answer": "Repeatable measurements before and after each isolated correction."},
            {"question": "Would you spend your own money?", "answer": "Only after the evidence supports the recommendation."},
        ],
        "questions_for_technician": ["Provide labour by visit/task.", "Confirm the primary root cause.", "List tests that ruled out alternatives."],
        "coaching": {"done_well": ["Recorded observations."], "improvements": ["Separate hypothesis from confirmed diagnosis.", "Link labour to activities."], "better_approach": ["Correct control and installation defects first, stabilise, then reassess."]},
        "scores": {"fault_finding": 6, "evidence": 5, "technical_quality": 6, "efficiency": 6, "labour_accuracy": 6, "report_quality": 6, "customer_confidence": 6, "overall_100": 58},
        "final_decision": {"decision": "Request Further Information", "confidence": 65, "justification": "Use Live AI before relying on this result for a real commercial decision."},
        "customer_ready_summary": "Demonstration result only. A report-specific live AI review is required before issue.",
    }


def render_review(r: dict[str, Any], key_prefix: str = "current") -> None:
    decision = r.get("final_decision", {})
    st.subheader(f"Decision: {decision.get('decision', '—')}")
    st.write(decision.get("justification", ""))
    scores = r.get("scores", {})
    cols = st.columns(4)
    cols[0].metric("Overall", f"{scores.get('overall_100', 0)}/100")
    cols[1].metric("Diagnosis confidence", f"{r.get('diagnosis', {}).get('confidence', 0)}%")
    cols[2].metric("Labour", r.get("labour_review", {}).get("rating", "—"))
    cols[3].metric("Criticality", r.get("job_classification", {}).get("criticality", "—"))

    tabs = st.tabs(["Summary", "Technical", "Labour & Parts", "Risk & Challenge", "Coaching", "Customer Copy", "Raw JSON"])
    with tabs[0]:
        st.markdown("### Classification")
        st.write(r.get("job_classification", {}))
        st.markdown("### Executive summary")
        st.write(r.get("executive_summary", ""))
        st.markdown("### Diagnosis")
        st.write(r.get("diagnosis", {}))
    with tabs[1]:
        for item in r.get("technical_findings", []):
            st.markdown(f"**{item.get('assessment', '')}: {item.get('finding', '')}**")
            st.write(item.get("explanation", ""))
        st.markdown("### Missing evidence")
        st.dataframe(r.get("missing_evidence", []), use_container_width=True)
        st.markdown("### Questions for technician")
        for q in r.get("questions_for_technician", []):
            st.write(f"• {q}")
    with tabs[2]:
        st.markdown("### Labour")
        st.write(r.get("labour_review", {}))
        st.markdown("### Parts")
        st.dataframe(r.get("parts_review", []), use_container_width=True)
    with tabs[3]:
        st.markdown("### Risks")
        st.dataframe(r.get("risk_review", []), use_container_width=True)
        st.markdown("### Senior Technician Challenge")
        for item in r.get("senior_technician_challenge", []):
            st.markdown(f"**{item.get('question', '')}**")
            st.write(item.get("answer", ""))
    with tabs[4]:
        coaching = r.get("coaching", {})
        for heading, key in [("Done well", "done_well"), ("Improvements", "improvements"), ("Better approach", "better_approach")]:
            st.markdown(f"### {heading}")
            for x in coaching.get(key, []):
                st.write(f"• {x}")
    with tabs[5]:
        st.text_area("Customer-ready summary", r.get("customer_ready_summary", ""), height=240, key=f"{key_prefix}_customer")
    with tabs[6]:
        st.json(r)
    st.download_button("Download review JSON", json.dumps(r, indent=2), file_name=f"hvacr_review_{datetime.now():%Y%m%d_%H%M}.json", mime="application/json", key=f"{key_prefix}_download")


def require_access() -> None:
    expected = st.secrets.get("APP_PASSWORD", os.getenv("APP_PASSWORD", ""))
    if not expected:
        return
    if st.session_state.get("authenticated"):
        return
    st.title("TechCheck HVAC&R")
    st.caption("Private beta access")
    password = st.text_input("Access password", type="password")
    if st.button("Sign in", type="primary"):
        if password == expected:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()


init_db()
require_access()

st.sidebar.title("TechCheck HVAC&R")
page = st.sidebar.radio("Navigation", ["Dashboard", "Review report", "History", "Company standards", "Plans & setup"])
st.sidebar.caption("AI supports supervisor judgement; it does not certify safety, compliance or workmanship.")

if page == "Dashboard":
    st.title("Technical QA Dashboard")
    reviews = load_reviews()
    if reviews.empty:
        st.info("No saved reviews yet. Open ‘Review report’ to create the first one.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Reviews", len(reviews))
        c2.metric("Average score", f"{reviews['overall_score'].mean():.0f}/100")
        c3.metric("Hours reviewed", f"{reviews['claimed_hours'].sum():.1f}")
        flagged = reviews[reviews["decision"].isin(["Request Further Information", "Reject Recommendation"])]
        c4.metric("Flagged", len(flagged))
        st.markdown("### Recent reviews")
        st.dataframe(reviews.head(10), use_container_width=True, hide_index=True)
        st.markdown("### Decisions")
        st.bar_chart(reviews["decision"].value_counts())

elif page == "Review report":
    st.title("Review technician report")
    live_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    if not live_key:
        st.warning("Live AI is not configured. Demonstration mode uses generic rules and can produce similar results for similar reports.")
    with st.sidebar:
        st.header("Review settings")
        mode = st.radio("Review mode", ["Live AI", "Demonstration"], index=0 if live_key else 1)
        model = st.text_input("Model", value=st.secrets.get("OPENAI_MODEL", os.getenv("OPENAI_MODEL", "gpt-4.1-mini")))
        hours = st.number_input("Claimed total hours", min_value=0.0, value=0.0, step=0.25)
        context = st.text_area("Job context", placeholder="Access, number of technicians, SLA, travel policy, operating conditions...")
    cols = st.columns(2)
    with cols[0]:
        work_order = st.text_input("Work order / job number")
        customer = st.text_input("Customer")
        site = st.text_input("Site")
    with cols[1]:
        technician = st.text_input("Technician")
        uploaded = st.file_uploader("Upload report", type=["pdf", "docx", "txt", "csv", "md"])
    report_text = st.text_area("Technician notes", height=340, placeholder="Paste the complete job notes here...")
    report_name = "Pasted notes"
    if uploaded:
        report_name = uploaded.name
        try:
            extracted = extract_text(uploaded)
            if extracted.strip():
                report_text = extracted
                st.success(f"Extracted {len(extracted):,} characters from {uploaded.name}.")
            else:
                st.warning("No selectable text was found. A scanned PDF requires OCR or image-capable processing.")
        except Exception as exc:
            st.error(str(exc))
    standards = st.session_state.get("company_standards", st.secrets.get("COMPANY_STANDARDS", ""))
    if st.button("Run technical review", type="primary", use_container_width=True):
        if not report_text.strip():
            st.error("Paste notes or upload a report first.")
        elif mode == "Live AI" and not live_key:
            st.error("Add OPENAI_API_KEY in Streamlit Secrets first.")
        else:
            with st.spinner("Reviewing report..."):
                try:
                    result = live_review(report_text, hours, context, standards, model) if mode == "Live AI" else demo_review(report_text, hours)
                    meta = {"work_order": work_order, "customer": customer, "site": site, "technician": technician, "report_name": report_name, "hours": hours}
                    review_id = save_review(meta, report_text, result, mode)
                    st.session_state["review"] = result
                    st.session_state["review_id"] = review_id
                    st.success(f"Review saved as #{review_id}.")
                except Exception as exc:
                    st.exception(exc)
    if "review" in st.session_state:
        render_review(st.session_state["review"])

elif page == "History":
    st.title("Review history")
    reviews = load_reviews()
    if reviews.empty:
        st.info("No reviews saved yet.")
    else:
        st.dataframe(reviews, use_container_width=True, hide_index=True)
        selected = st.selectbox("Open review", reviews["id"].tolist(), format_func=lambda x: f"#{x} — {reviews.loc[reviews['id'] == x, 'work_order'].iloc[0] or 'No work order'}")
        if selected:
            report, result = get_review(int(selected))
            with st.expander("Original technician report"):
                st.text(report)
            render_review(result, key_prefix=f"history_{selected}")
        st.download_button("Export review register CSV", reviews.to_csv(index=False), file_name="hvacr_review_register.csv", mime="text/csv")

elif page == "Company standards":
    st.title("Company standards")
    st.write("Add rules that should be applied to every review, such as evidence required before compressor replacement or labour policies.")
    default_standards = st.session_state.get("company_standards", """Compressor replacement requires voltage, current, winding resistance, insulation resistance, operating pressures and likely cause of failure.
TXV replacement requires confirmation of charge, airflow/load, bulb mounting and insulation, equaliser condition, restriction checks and response to adjustment.
All labour above 8 hours must include a visit-by-visit task breakdown.
Photos should support major defects and completed repairs.""")
    standards = st.text_area("Standards and approval rules", value=default_standards, height=360)
    if st.button("Save standards", type="primary"):
        st.session_state["company_standards"] = standards
        st.success("Standards saved for this app session. For permanent cloud storage, add a hosted database in the production build.")

elif page == "Plans & setup":
    st.title("Plans and commercial setup")
    st.info("This MVP does not take payments yet. Stripe billing and genuine user accounts require a secure production backend.")
    plans = pd.DataFrame([
        {"Plan": "Trial", "Reports/month": 5, "Indicative price": "$0", "Best for": "Testing"},
        {"Plan": "Solo", "Reports/month": 50, "Indicative price": "$39", "Best for": "Technician / sole trader"},
        {"Plan": "Team", "Reports/month": 300, "Indicative price": "$149", "Best for": "Small contractor"},
        {"Plan": "Business", "Reports/month": 1500, "Indicative price": "$499", "Best for": "Multi-branch contractor"},
    ])
    st.dataframe(plans, use_container_width=True, hide_index=True)
    st.markdown("### Live AI setup")
    st.code('OPENAI_API_KEY = "sk-proj-..."\nOPENAI_MODEL = "gpt-4.1-mini"\nAPP_PASSWORD = "choose-a-private-beta-password"', language="toml")
    st.markdown("### Production work still required before charging customers")
    st.write("• Proper user accounts and password reset\n• Stripe subscriptions and usage metering\n• Hosted database and encrypted file storage\n• Privacy policy, terms and data-retention controls\n• Audit logs, backups and role-based permissions\n• Security and legal review")

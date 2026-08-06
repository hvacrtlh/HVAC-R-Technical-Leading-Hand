import io
import json
import os
import re
from datetime import datetime
from typing import Any

import streamlit as st
from docx import Document
from openai import OpenAI
from pypdf import PdfReader

st.set_page_config(page_title="HVAC&R Technical Review", page_icon="🛠️", layout="wide")

SYSTEM_PROMPT = r"""
You are an independent Senior HVAC&R Technical Manager reviewing technician reports before they are issued to a customer.
Protect both contractor and customer. Do not merely agree with the technician. Require evidence, identify assumptions,
challenge expensive repairs, check labour reasonableness, and distinguish symptoms from root cause.

ADAPTIVE MODULES
First classify the job and activate only relevant modules: refrigeration/cold room, DX air conditioning, VRF/VRV,
controls/BMS, electrical, hydronics, chiller, cooling tower, heat pump/pool heating, ventilation/exhaust, PM audit,
quotation/additional works, compliance, or general mechanical.

MANDATORY REVIEW
1. Job summary: complaint, findings, root cause, work completed, outstanding work, criticality.
2. Diagnosis: Supported / Possibly Supported / Not Supported, with evidence for and against.
3. Activated modules and why.
4. Technical analysis of all readings and observations. Do not invent missing readings.
5. Missing tests/evidence, prioritised by what most increases diagnostic confidence.
6. Parts review: each recommended/replaced part, justification YES/NO/UNSURE, confidence 0-100%, alternatives.
7. Labour analysis: estimate reasonable onsite labour range, compare with claimed hours, account for access,
   defrosting, waiting/stabilisation, multiple technicians, commissioning, documentation and return visits.
8. Report quality: clarity, sequence, professionalism, customer defensibility, photos/evidence.
9. Risks: callback, safety, financial, warranty, compliance, reputation.
10. Senior Technician Challenge:
   - What else could cause the symptoms?
   - What evidence rules alternatives out?
   - Cheapest reasonable diagnostic/repair step first?
   - What test most increases confidence?
   - Has the technician confused symptom and root cause?
   - Would you spend your own money on the recommendation?
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

Return valid JSON only with this structure:
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


def extract_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    if name.endswith(".docx"):
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
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
    return json.loads(text[start : end + 1])


def live_review(report: str, hours: float, context: str, model: str) -> dict[str, Any]:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    user_input = f"""Review this HVAC&R technician report.
Claimed total labour hours: {hours:.2f}
Additional company/job context: {context or 'None provided'}

TECHNICIAN REPORT:
{report}
"""
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=user_input,
    )
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
    ]:
        if any(k in lower for k in keywords):
            modules.append(module)
    modules = modules or ["General HVAC&R"]
    offset = "offset" in lower
    txv = "txv" in lower
    reasonable_low, reasonable_high = (10.0, 14.0) if "ice" in lower and "return" in lower else (3.0, 8.0)
    labour_rating = "Reasonable" if hours <= reasonable_high + 1 else "High"
    return {
        "job_classification": {"type": modules[0], "activated_modules": modules, "criticality": "Medium"},
        "executive_summary": "Demonstration review generated using built-in rules. Connect the live AI service for a full technical assessment.",
        "diagnosis": {
            "rating": "Possibly Supported",
            "confidence": 72,
            "analysis": "The report contains a plausible repair path, but conclusions should be tied more clearly to measured evidence and the sequence of corrections.",
            "root_cause": "Controller configuration/calibration appears primary." if offset else "Insufficient information to confirm a single root cause.",
        },
        "technical_findings": [
            {"finding": "Adaptive review modules", "assessment": "Good", "explanation": ", ".join(modules)},
            {"finding": "Controller calibration", "assessment": "Good" if offset else "Missing", "explanation": "Offsets and actual temperature comparison are important control checks."},
            {"finding": "TXV conclusion", "assessment": "Concern" if txv else "Neutral", "explanation": "A TXV diagnosis should rule out load, airflow, charge, restrictions, bulb mounting/insulation and controls."},
        ],
        "missing_evidence": [
            {"priority": "High", "item": "Clear evidence chain", "why": "Each diagnosis and part recommendation should be linked to the tests that support it."},
            {"priority": "Medium", "item": "Time breakdown by visit/activity", "why": "This makes the labour charge defensible."},
        ],
        "parts_review": [{"part": "TXV" if txv else "No major part identified", "justified": "UNSURE", "confidence": 55, "reason": "Replacement is not justified without complete elimination testing.", "alternatives": ["Controls", "Sensor calibration", "Load/airflow", "Charge or restriction"]}],
        "labour_review": {"claimed_hours": hours, "reasonable_low": reasonable_low, "reasonable_high": reasonable_high, "rating": labour_rating, "analysis": "Hours should be checked against defrost time, access, stabilisation waits, return visits and documentation."},
        "risk_review": [
            {"risk": "Callback", "level": "Medium", "explanation": "Root cause and contributing faults must be separated."},
            {"risk": "Financial", "level": "Medium", "explanation": "Weak part justification can lead to customer challenge."},
        ],
        "senior_technician_challenge": [
            {"question": "What else could cause the symptoms?", "answer": "Control calibration, sensor placement, airflow/load, charge or restriction."},
            {"question": "What test most increases confidence?", "answer": "Repeatable measurements before and after each isolated correction."},
            {"question": "Would you spend your own money?", "answer": "Only after the evidence chain supports the recommended repair."},
        ],
        "questions_for_technician": ["Provide the labour breakdown by visit.", "Confirm which fault was considered the primary root cause.", "List the tests that ruled out alternative causes."],
        "coaching": {"done_well": ["Recorded observations and returned to verify operation."], "improvements": ["Separate hypothesis from confirmed diagnosis.", "Link labour to activities."], "better_approach": ["Correct controls and installation defects first, stabilise, then reassess the refrigeration circuit."]},
        "scores": {"fault_finding": 7, "evidence": 6, "technical_quality": 7, "efficiency": 6, "labour_accuracy": 6, "report_quality": 7, "customer_confidence": 7, "overall_100": 66},
        "final_decision": {"decision": "Approve with Comments", "confidence": 70, "justification": "Outcome appears acceptable, but the report should better document root cause and labour allocation."},
        "customer_ready_summary": "The system was tested and returned to operation. Before issue, clarify the confirmed root cause and provide a concise labour breakdown.",
    }


def render_review(r: dict[str, Any]):
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
        st.text_area("Customer-ready summary", r.get("customer_ready_summary", ""), height=240)
    with tabs[6]:
        st.json(r)

    export = json.dumps(r, indent=2)
    st.download_button("Download review JSON", export, file_name=f"hvacr_review_{datetime.now():%Y%m%d_%H%M}.json", mime="application/json")


st.title("HVAC&R Technical Review System")
st.caption("Pre-issue QA for technician reports, labour, parts justification and customer defensibility.")

with st.sidebar:
    st.header("Review settings")
    mode = st.radio("Review mode", ["Demonstration", "Live AI"], help="Live AI requires OPENAI_API_KEY on the server.")
    model = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-5.6"))
    hours = st.number_input("Claimed total hours", min_value=0.0, value=0.0, step=0.25)
    context = st.text_area("Company/job context", placeholder="SLA, site access, technicians attending, travel policy, customer standards...")
    st.info("Keep the final approval with a competent supervisor. AI flags issues; it does not certify compliance or workmanship.")

uploaded = st.file_uploader("Upload technician report", type=["pdf", "docx", "txt", "csv", "md"])
report_text = st.text_area("Or paste technician notes", height=330, placeholder="Paste the complete job notes here...")

if uploaded:
    try:
        extracted = extract_text(uploaded)
        if extracted.strip():
            report_text = extracted
            st.success(f"Extracted {len(extracted):,} characters from {uploaded.name}.")
        else:
            st.warning("No selectable text was found. A scanned PDF will need OCR or direct image/PDF model input in the production version.")
    except Exception as exc:
        st.error(str(exc))

if st.button("Review report", type="primary", use_container_width=True):
    if not report_text.strip():
        st.error("Paste notes or upload a report first.")
    elif mode == "Live AI" and not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is not configured on the server.")
    else:
        with st.spinner("Reviewing report..."):
            try:
                result = live_review(report_text, hours, context, model) if mode == "Live AI" else demo_review(report_text, hours)
                st.session_state["review"] = result
            except Exception as exc:
                st.exception(exc)

if "review" in st.session_state:
    render_review(st.session_state["review"])

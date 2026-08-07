from __future__ import annotations
import os
import streamlit as st

from ai_backend import TechCheckAI, TechCheckAIError
from report_parser import extract_text
from prompts import (
    SERVICE_REVIEW_PROMPT,
    QUOTE_REVIEW_PROMPT,
    CHALLENGE_PROMPT,
    SOUNDING_BOARD_PROMPT,
)

st.set_page_config(
    page_title="TechCheck HVAC&R",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
:root{
  --navy:#0C2242;
  --navy2:#122F57;
  --orange:#F28A21;
  --bg:#F5F7FB;
  --card:#FFFFFF;
  --border:#DDE5EF;
  --muted:#61718A;
}
.stApp{background:var(--bg);}
.block-container{max-width:1400px;padding-top:2rem;padding-bottom:5rem;}
h1,h2,h3{color:var(--navy);letter-spacing:-.02em;}
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,var(--navy),var(--navy2));
}
[data-testid="stSidebar"] *{color:white;}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.15);}
div.stButton > button{
  background:var(--orange);
  border:0;
  color:white;
  border-radius:10px;
  font-weight:750;
  min-height:44px;
}
div.stButton > button:hover{
  background:#DD7613;
  color:white;
  border:0;
}
.tc-brand{font-size:1.45rem;font-weight:850;color:white;margin-bottom:0;}
.tc-brand-sub{font-size:.82rem;color:#C6D3E6;margin-bottom:1rem;}
.tc-kicker{
  color:var(--orange);
  text-transform:uppercase;
  letter-spacing:.14em;
  font-size:.76rem;
  font-weight:850;
}
.tc-card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:15px;
  padding:20px;
  box-shadow:0 5px 20px rgba(12,34,66,.045);
  min-height:120px;
}
.tc-label{font-size:.83rem;color:var(--muted);font-weight:650;}
.tc-value{font-size:1.55rem;color:var(--navy);font-weight:850;margin:.2rem 0;}
.tc-note{font-size:.88rem;color:var(--muted);}
.tc-status{
  background:#EDF4FF;border:1px solid #D8E5F7;border-radius:12px;padding:14px 16px;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def secret(name: str, default=None):
    try:
        value = st.secrets.get(name)
        if value is not None:
            return value
    except Exception:
        pass
    return os.getenv(name, default)

API_KEY = secret("OPENAI_API_KEY")
MODEL = secret("OPENAI_MODEL", "gpt-5.5")

def ai():
    return TechCheckAI(API_KEY, MODEL)

def card(label, value, note=""):
    st.markdown(
        f'<div class="tc-card"><div class="tc-label">{label}</div>'
        f'<div class="tc-value">{value}</div><div class="tc-note">{note}</div></div>',
        unsafe_allow_html=True,
    )

def bullets(items):
    if not items:
        st.write("None identified.")
        return
    for item in items:
        if isinstance(item, dict):
            st.write("• " + " — ".join(str(v) for v in item.values() if v))
        else:
            st.write(f"• {item}")

with st.sidebar:
    st.markdown('<div class="tc-brand">TechCheck HVAC&R</div>', unsafe_allow_html=True)
    st.markdown('<div class="tc-brand-sub">Technical QA Platform</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        ["Dashboard", "Review Report", "Quote Review", "Sounding Board", "Settings"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    if API_KEY:
        st.caption("● Live AI connected")
    else:
        st.caption("○ Live AI not configured")

if page == "Dashboard":
    st.markdown('<div class="tc-kicker">HVAC&R Technical QA</div>', unsafe_allow_html=True)
    st.title("Technical decisions with a second set of eyes")
    st.write(
        "Review service reports, challenge repair recommendations, check quotation allowances "
        "and work through faults with Sounding Board."
    )
    c1,c2,c3 = st.columns(3)
    with c1:
        card("SERVICE REPORTS", "Technical Review", "Diagnosis, evidence, labour and callback risk.")
    with c2:
        card("QUOTATIONS", "Commercial Review", "Scope, labour, materials and approval risk.")
    with c3:
        card("SOUNDING BOARD", "Fault Finding", "Talk through symptoms with a senior technical mentor.")

    st.write("")
    st.subheader("Proof-of-concept workflow")
    st.write(
        "Upload or paste the information you already receive. TechCheck challenges what is written, "
        "highlights what is missing and gives you a recommendation. You remain the final decision-maker."
    )

elif page == "Review Report":
    st.markdown('<div class="tc-kicker">Service Report Review</div>', unsafe_allow_html=True)
    st.title("Review technician report")
    st.write("Upload the service docket or paste the technician notes below.")

    left, right = st.columns([1.45, .55])
    with left:
        uploaded = st.file_uploader("Upload report", type=["pdf", "docx", "txt", "md", "csv"])
        pasted = st.text_area("Technician notes", height=300, placeholder="Paste technician notes here…")
    with right:
        work_order = st.text_input("Work order / reference")
        claimed_hours = st.number_input("Total labour hours", min_value=0.0, step=0.25)
        st.markdown('<div class="tc-status">The labour figure is sent to the same AI review as the technician notes, so it is assessed in context.</div>', unsafe_allow_html=True)

    b1,b2 = st.columns(2)
    run_review = b1.button("Review report", width="stretch")
    run_challenge = b2.button("Challenge the technician", width="stretch")

    if run_review or run_challenge:
        try:
            text = pasted.strip() or extract_text(uploaded)
            if not text:
                st.warning("Upload a report or paste technician notes first.")
            elif not API_KEY:
                st.error("Live AI is not configured. Add OPENAI_API_KEY in Streamlit Secrets.")
            else:
                payload = {
                    "work_order": work_order,
                    "claimed_labour_hours": claimed_hours,
                    "technician_report": text,
                }
                prompt = CHALLENGE_PROMPT if run_challenge else SERVICE_REVIEW_PROMPT
                with st.spinner("Analysing the report…"):
                    result = ai().structured_review(prompt, payload)

                if run_challenge:
                    st.subheader("Technician challenge")
                    a,b,c = st.columns(3)
                    with a: card("RESULT", result.get("challenge_result",""), result.get("main_issue",""))
                    with b: card("CONFIDENCE", f"{result.get('confidence',0)}%", "")
                    with c: card("WOULD APPROVE", result.get("would_you_approve",""), result.get("reason",""))

                    st.subheader("Alternative causes")
                    bullets(result.get("alternative_causes", []))
                    st.subheader("Missing evidence")
                    bullets(result.get("missing_evidence", []))
                    st.subheader("Best next test")
                    st.write(result.get("best_next_test",""))
                    st.subheader("Labour comment")
                    st.write(result.get("labour_comment",""))
                    with st.expander("Full structured result"):
                        st.json(result)
                else:
                    st.subheader("Review outcome")
                    d = result.get("diagnosis", {})
                    l = result.get("labour", {})
                    a,b,c,dcol = st.columns(4)
                    with a: card("DECISION", result.get("decision",""), result.get("summary",""))
                    with b: card("OVERALL SCORE", f"{result.get('overall_score',0)}/100", f"{result.get('confidence',0)}% confidence")
                    with c: card("DIAGNOSIS", d.get("rating",""), d.get("reason",""))
                    with dcol: card("LABOUR", l.get("rating",""), l.get("reasonable_range",""))

                    st.subheader("Labour assessment")
                    st.write(l.get("reason",""))

                    for title, key in [
                        ("Technical concerns", "technical_concerns"),
                        ("Missing tests", "missing_tests"),
                        ("Parts review", "parts_review"),
                        ("Risks", "risks"),
                        ("Questions for technician", "questions_for_technician"),
                        ("Coaching", "coaching"),
                    ]:
                        vals = result.get(key, [])
                        if vals:
                            st.subheader(title)
                            bullets(vals)

                    challenge = result.get("challenge", {})
                    with st.expander("Senior technician challenge"):
                        st.write("**Alternative causes**")
                        bullets(challenge.get("alternative_causes", []))
                        st.write("**What has not been ruled out**")
                        bullets(challenge.get("what_has_not_been_ruled_out", []))
                        st.write("**Best next test:**", challenge.get("best_next_test",""))
                        st.write("**Cheaper first step:**", challenge.get("cheaper_first_step",""))
                        st.write("**Root cause:**", challenge.get("root_cause_comment",""))

                    with st.expander("Full structured review"):
                        st.json(result)
        except Exception as exc:
            st.error(str(exc))

elif page == "Quote Review":
    st.markdown('<div class="tc-kicker">Commercial Review</div>', unsafe_allow_html=True)
    st.title("Review quotation")
    st.write("Check whether the scope, hours and allowances make commercial sense before approval.")

    c1,c2,c3 = st.columns([1.1,.8,1.1])
    with c1:
        quote_ref = st.text_input("Quote reference")
    with c2:
        labour = st.number_input("Labour hours", min_value=0.0, step=0.25)
    with c3:
        materials = st.number_input("Materials / equipment allowance ($)", min_value=0.0, step=50.0)

    scope = st.text_area(
        "Scope and quotation details",
        height=300,
        placeholder="Example: Supply and install new condensate drain to high wall split system…",
    )

    if st.button("Review quotation", width="stretch"):
        if not scope.strip():
            st.warning("Enter the quotation scope first.")
        elif not API_KEY:
            st.error("Live AI is not configured. Add OPENAI_API_KEY in Streamlit Secrets.")
        else:
            try:
                payload = {
                    "quote_reference": quote_ref,
                    "claimed_labour_hours": labour,
                    "materials_and_equipment_allowance_aud": materials,
                    "scope_and_quotation_details": scope,
                }
                with st.spinner("Reviewing scope, labour and commercial risk…"):
                    result = ai().structured_review(QUOTE_REVIEW_PROMPT, payload)

                l = result.get("labour", {})
                m = result.get("materials", {})
                a,b,c = st.columns(3)
                with a: card("COMMERCIAL RISK", result.get("commercial_risk",""), result.get("headline",""))
                with b: card("LABOUR", l.get("rating",""), l.get("reasonable_range",""))
                with c: card("MATERIALS", m.get("rating",""), f"${materials:,.0f} entered")

                st.subheader("Recommendation")
                st.write(f"**{result.get('decision','')}** — confidence {result.get('confidence',0)}%")

                st.subheader("Labour assessment")
                st.write(l.get("reason",""))
                st.subheader("Materials / equipment assessment")
                st.write(m.get("reason",""))

                for title,key in [
                    ("Items to check","items_to_check"),
                    ("Missing scope items","missing_scope_items"),
                    ("Questions before approval","questions_before_approval"),
                    ("Commercial notes","commercial_notes"),
                ]:
                    vals = result.get(key, [])
                    if vals:
                        st.subheader(title)
                        bullets(vals)

                with st.expander("Why did TechCheck reach this result?"):
                    st.write(
                        "The assessment is based on the described scope, entered labour and allowance, "
                        "plus any complexity actually stated in the quote. Missing access or complexity "
                        "information is treated as uncertainty rather than assumed."
                    )
                    st.json(result)
            except Exception as exc:
                st.error(str(exc))

elif page == "Sounding Board":
    st.title("Sounding Board")
    if "sounding_board" not in st.session_state:
        st.session_state.sounding_board = [
            {
                "role":"assistant",
                "content":"Describe the fault or symptoms and I’ll help you work through it."
            }
        ]

    for msg in st.session_state.sounding_board:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_message = st.chat_input("Describe the symptoms…")
    if user_message:
        st.session_state.sounding_board.append({"role":"user","content":user_message})
        with st.chat_message("user"):
            st.write(user_message)

        if not API_KEY:
            answer = "Live AI is not configured yet. Add your OpenAI API key in Streamlit Secrets."
        else:
            try:
                with st.spinner("Thinking through the fault…"):
                    answer = ai().chat(SOUNDING_BOARD_PROMPT, st.session_state.sounding_board)
            except Exception as exc:
                answer = str(exc)

        st.session_state.sounding_board.append({"role":"assistant","content":answer})
        with st.chat_message("assistant"):
            st.write(answer)

    if st.button("Clear conversation"):
        st.session_state.sounding_board = [
            {
                "role":"assistant",
                "content":"Describe the fault or symptoms and I’ll help you work through it."
            }
        ]
        st.rerun()

elif page == "Settings":
    st.markdown('<div class="tc-kicker">Configuration</div>', unsafe_allow_html=True)
    st.title("Settings")
    if API_KEY:
        st.success("OpenAI API key is configured.")
    else:
        st.error("OpenAI API key is not configured.")

    st.write("Add these under **Streamlit → App settings → Secrets**:")
    st.code(
        'OPENAI_API_KEY = "sk-proj-your-key-here"\n'
        'OPENAI_MODEL = "gpt-5.5"',
        language="toml",
    )
    st.caption("The model setting stays server-side and is not shown to normal users.")

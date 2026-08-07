from __future__ import annotations

import os
import streamlit as st

from ai_backend import TechCheckAI, TechCheckError
from prompts import (
    SERVICE_REVIEW_PROMPT,
    QUOTE_REVIEW_PROMPT,
    CHALLENGE_PROMPT,
    SOUNDING_BOARD_PROMPT,
)
from report_parser import extract_text


st.set_page_config(
    page_title="TechCheck HVAC&R",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root{
  --navy:#0D2344;
  --navy2:#15365F;
  --orange:#F58A1F;
  --bg:#F5F7FB;
  --card:#FFFFFF;
  --line:#DEE6F0;
  --muted:#63728A;
}
.stApp {background:var(--bg);}
.block-container {max-width:1400px;padding-top:2rem;padding-bottom:5rem;}
h1,h2,h3 {color:var(--navy);letter-spacing:-0.02em;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,var(--navy),var(--navy2));}
[data-testid="stSidebar"] * {color:white;}
[data-testid="stSidebar"] hr {border-color:rgba(255,255,255,.15);}
div.stButton > button {
  background:var(--orange);color:white;border:0;border-radius:10px;
  min-height:44px;font-weight:800;
}
div.stButton > button:hover {background:#DF7610;color:white;border:0;}
.tc-brand {font-size:1.5rem;font-weight:900;color:white;}
.tc-sub {font-size:.82rem;color:#CBD7E7;margin-bottom:1rem;}
.tc-kicker {color:var(--orange);font-weight:900;letter-spacing:.14em;font-size:.75rem;text-transform:uppercase;}
.tc-card {
  background:var(--card);border:1px solid var(--line);border-radius:15px;
  padding:20px;box-shadow:0 6px 20px rgba(13,35,68,.05);min-height:120px;
}
.tc-label {color:var(--muted);font-size:.8rem;font-weight:750;text-transform:uppercase;letter-spacing:.05em;}
.tc-value {color:var(--navy);font-size:1.55rem;font-weight:900;margin:.25rem 0;}
.tc-note {color:var(--muted);font-size:.88rem;}
</style>
""", unsafe_allow_html=True)


def get_secret(name: str, default=None):
    try:
        value = st.secrets.get(name)
        if value is not None:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


API_KEY = get_secret("OPENAI_API_KEY")
MODEL = get_secret("OPENAI_MODEL", "gpt-5.5")


def get_ai() -> TechCheckAI:
    return TechCheckAI(API_KEY, MODEL)


def card(label: str, value: str, note: str = ""):
    st.markdown(
        f'<div class="tc-card"><div class="tc-label">{label}</div>'
        f'<div class="tc-value">{value}</div><div class="tc-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def bullet_list(items):
    if not items:
        st.write("None identified.")
        return
    for item in items:
        if isinstance(item, dict):
            text = " — ".join(str(v) for v in item.values() if v not in (None, "", []))
            st.write(f"• {text}")
        else:
            st.write(f"• {item}")


with st.sidebar:
    st.markdown('<div class="tc-brand">TechCheck HVAC&R</div>', unsafe_allow_html=True)
    st.markdown('<div class="tc-sub">Technical QA Platform</div>', unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["Dashboard", "Review Report", "Quote Review", "Sounding Board", "Settings"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("● Live AI connected" if API_KEY else "○ Live AI not configured")


if page == "Dashboard":
    st.markdown('<div class="tc-kicker">HVAC&R Technical QA</div>', unsafe_allow_html=True)
    st.title("A second set of eyes on technical decisions")
    st.write(
        "Review technician reports, challenge repair recommendations, check quotation allowances "
        "and work through faults with Sounding Board."
    )

    a, b, c = st.columns(3)
    with a:
        card("Service reports", "Technical Review", "Diagnosis, evidence, labour and callback risk.")
    with b:
        card("Quotations", "Commercial Review", "Scope, labour, materials and approval risk.")
    with c:
        card("Sounding Board", "Fault Finding", "Talk through symptoms with a senior technical mentor.")

    st.subheader("How the proof of concept works")
    st.write(
        "Provide the same information a supervisor normally receives. TechCheck challenges what is "
        "written, identifies missing evidence and provides a recommendation. The supervisor remains "
        "the final decision-maker."
    )


elif page == "Review Report":
    st.markdown('<div class="tc-kicker">Service Report Review</div>', unsafe_allow_html=True)
    st.title("Review technician report")
    st.write("Upload the service docket or paste the technician notes.")

    left, right = st.columns([1.5, .5])
    with left:
        upload = st.file_uploader("Upload report", type=["pdf", "docx", "txt", "md", "csv"])
        notes = st.text_area(
            "Technician notes",
            height=300,
            placeholder="Paste technician notes here…",
        )
    with right:
        reference = st.text_input("Work order / reference")
        hours = st.number_input("Total labour hours", min_value=0.0, step=0.25)
        st.info("Labour is assessed in context with the technician notes.")

    b1, b2 = st.columns(2)
    review_clicked = b1.button("Review report", width="stretch")
    challenge_clicked = b2.button("Challenge the technician", width="stretch")

    if review_clicked or challenge_clicked:
        try:
            text = notes.strip() or extract_text(upload)

            if not text:
                st.warning("Upload a report or paste technician notes first.")
            elif not API_KEY:
                st.error("Add OPENAI_API_KEY in Streamlit App settings → Secrets.")
            else:
                payload = {
                    "work_order": reference,
                    "claimed_labour_hours": hours,
                    "technician_report": text,
                }
                instructions = CHALLENGE_PROMPT if challenge_clicked else SERVICE_REVIEW_PROMPT

                with st.spinner("Analysing the report…"):
                    result = get_ai().structured(instructions, payload)

                if challenge_clicked:
                    st.subheader("Technician challenge")
                    x, y, z = st.columns(3)
                    with x:
                        card("Result", result.get("challenge_result", ""), result.get("main_issue", ""))
                    with y:
                        card("Confidence", f"{result.get('confidence', 0)}%", "")
                    with z:
                        card("Would approve", result.get("would_you_approve", ""), result.get("reason", ""))

                    st.subheader("Alternative causes")
                    bullet_list(result.get("alternative_causes", []))
                    st.subheader("Missing evidence")
                    bullet_list(result.get("missing_evidence", []))
                    st.subheader("Best next test")
                    st.write(result.get("best_next_test", ""))
                    st.subheader("Labour")
                    st.write(result.get("labour_comment", ""))

                else:
                    diagnosis = result.get("diagnosis", {})
                    labour = result.get("labour", {})

                    st.subheader("Review outcome")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        card("Decision", result.get("decision", ""), result.get("summary", ""))
                    with c2:
                        card("Overall score", f"{result.get('overall_score', 0)}/100",
                             f"{result.get('confidence', 0)}% confidence")
                    with c3:
                        card("Diagnosis", diagnosis.get("rating", ""), diagnosis.get("reason", ""))
                    with c4:
                        card("Labour", labour.get("rating", ""), labour.get("reasonable_range", ""))

                    st.subheader("Labour assessment")
                    st.write(labour.get("reason", ""))

                    sections = [
                        ("Technical concerns", "technical_concerns"),
                        ("Missing tests", "missing_tests"),
                        ("Parts review", "parts_review"),
                        ("Risks", "risks"),
                        ("Questions for technician", "questions_for_technician"),
                        ("Technician coaching", "coaching"),
                    ]
                    for title, key in sections:
                        values = result.get(key, [])
                        if values:
                            st.subheader(title)
                            bullet_list(values)

                    sc = result.get("senior_challenge", {})
                    with st.expander("Senior technician challenge"):
                        st.write("**Alternative causes**")
                        bullet_list(sc.get("alternative_causes", []))
                        st.write("**Not ruled out**")
                        bullet_list(sc.get("not_ruled_out", []))
                        st.write("**Best next test:**", sc.get("best_next_test", ""))
                        st.write("**Cheaper first step:**", sc.get("cheaper_first_step", ""))
                        st.write("**Root cause:**", sc.get("root_cause_comment", ""))

                with st.expander("Full structured result"):
                    st.json(result)

        except Exception as exc:
            st.error(str(exc))


elif page == "Quote Review":
    st.markdown('<div class="tc-kicker">Commercial QA</div>', unsafe_allow_html=True)
    st.title("Review quotation")
    st.write("Check scope clarity, labour allowances and commercial risk before approval.")

    a, b, c = st.columns([1.1, .8, 1.1])
    with a:
        quote_ref = st.text_input("Quote reference")
    with b:
        labour_hours = st.number_input("Labour hours", min_value=0.0, step=0.25)
    with c:
        allowance = st.number_input("Materials and equipment allowance ($)", min_value=0.0, step=50.0)

    scope = st.text_area(
        "Scope and quotation details",
        height=300,
        placeholder="Example: Supply and install new condensate drain to high wall split system…",
    )

    if st.button("Review quotation", width="stretch"):
        if not scope.strip():
            st.warning("Enter the quotation scope first.")
        elif not API_KEY:
            st.error("Add OPENAI_API_KEY in Streamlit App settings → Secrets.")
        else:
            try:
                payload = {
                    "quote_reference": quote_ref,
                    "claimed_labour_hours": labour_hours,
                    "materials_and_equipment_allowance_aud": allowance,
                    "scope_and_quotation_details": scope,
                }

                with st.spinner("Reviewing quotation…"):
                    result = get_ai().structured(QUOTE_REVIEW_PROMPT, payload)

                labour = result.get("labour", {})
                materials = result.get("materials", {})

                c1, c2, c3 = st.columns(3)
                with c1:
                    card("Commercial risk", result.get("commercial_risk", ""), result.get("headline", ""))
                with c2:
                    card("Labour", labour.get("rating", ""), labour.get("reasonable_range", ""))
                with c3:
                    card("Materials / equipment", materials.get("rating", ""), f"${allowance:,.0f} entered")

                st.subheader("Recommendation")
                st.write(
                    f"**{result.get('decision', '')}** — "
                    f"{result.get('confidence', 0)}% confidence"
                )

                st.subheader("Labour assessment")
                st.write(labour.get("reason", ""))

                st.subheader("Materials / equipment assessment")
                st.write(materials.get("reason", ""))

                for title, key in [
                    ("Items to check", "items_to_check"),
                    ("Missing scope items", "missing_scope_items"),
                    ("Questions before approval", "questions_before_approval"),
                    ("Commercial notes", "commercial_notes"),
                ]:
                    values = result.get(key, [])
                    if values:
                        st.subheader(title)
                        bullet_list(values)

                with st.expander("Why?"):
                    st.write(
                        "TechCheck compares the stated work with the labour and allowance supplied. "
                        "It only treats access, builder's works, EWP/scaffold or other complexity as "
                        "justification when that complexity is actually stated or supported."
                    )
                    st.json(result)

            except Exception as exc:
                st.error(str(exc))


elif page == "Sounding Board":
    st.title("Sounding Board")

    if "sb_chat" not in st.session_state:
        st.session_state.sb_chat = [
            {
                "role": "assistant",
                "content": "Describe the fault or symptoms and I’ll help you work through it.",
            }
        ]

    for message in st.session_state.sb_chat:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    new_message = st.chat_input("Describe the symptoms…")

    if new_message:
        st.session_state.sb_chat.append({"role": "user", "content": new_message})

        with st.chat_message("user"):
            st.write(new_message)

        if not API_KEY:
            answer = "Add OPENAI_API_KEY in Streamlit App settings → Secrets to use Sounding Board."
        else:
            try:
                with st.spinner("Thinking through the fault…"):
                    answer = get_ai().chat(SOUNDING_BOARD_PROMPT, st.session_state.sb_chat)
            except Exception as exc:
                answer = str(exc)

        st.session_state.sb_chat.append({"role": "assistant", "content": answer})

        with st.chat_message("assistant"):
            st.write(answer)

    if st.button("Clear conversation"):
        st.session_state.sb_chat = [
            {
                "role": "assistant",
                "content": "Describe the fault or symptoms and I’ll help you work through it.",
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

    st.write("In Streamlit go to **App settings → Secrets** and enter:")
    st.code(
        'OPENAI_API_KEY = "sk-proj-your-key-here"\n'
        'OPENAI_MODEL = "gpt-5.5"',
        language="toml",
    )
    st.caption("Do not put your real API key in GitHub.")

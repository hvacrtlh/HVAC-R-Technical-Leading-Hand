from __future__ import annotations

import os
import streamlit as st

from ai_backend import TechCheckAI
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

st.markdown(
    """
<style>
:root {
  --navy:#0D2344;
  --navy2:#15365F;
  --orange:#F58A1F;
  --bg:#F5F7FB;
  --card:#FFFFFF;
  --line:#DEE6F0;
  --muted:#63728A;
}
.stApp { background:var(--bg); }
.block-container { max-width:1400px; padding-top:2rem; padding-bottom:5rem; }
h1,h2,h3 { color:var(--navy); letter-spacing:-0.02em; }
[data-testid="stSidebar"] {
  background:linear-gradient(180deg,var(--navy),var(--navy2));
}
[data-testid="stSidebar"] * { color:white; }
[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.15); }
div.stButton > button {
  background:var(--orange);
  color:white;
  border:0;
  border-radius:10px;
  min-height:44px;
  font-weight:800;
}
div.stButton > button:hover {
  background:#DF7610;
  color:white;
  border:0;
}
.tc-brand { font-size:1.5rem; font-weight:900; color:white; }
.tc-sub { font-size:.82rem; color:#CBD7E7; margin-bottom:1rem; }
.tc-kicker {
  color:var(--orange);
  font-weight:900;
  letter-spacing:.14em;
  font-size:.75rem;
  text-transform:uppercase;
}
.tc-card {
  background:var(--card);
  border:1px solid var(--line);
  border-radius:15px;
  padding:20px;
  box-shadow:0 6px 20px rgba(13,35,68,.05);
  min-height:120px;
}
.tc-label {
  color:var(--muted);
  font-size:.8rem;
  font-weight:750;
  text-transform:uppercase;
  letter-spacing:.05em;
}
.tc-value {
  color:var(--navy);
  font-size:1.55rem;
  font-weight:900;
  margin:.25rem 0;
}
.tc-note { color:var(--muted); font-size:.88rem; }
</style>
""",
    unsafe_allow_html=True,
)


def read_secret(name: str, default=None):
    try:
        value = st.secrets.get(name)
        if value is not None:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


API_KEY = read_secret("OPENAI_API_KEY")


def get_ai():
    return TechCheckAI(API_KEY)


def card(label: str, value: str, note: str = ""):
    st.markdown(
        f'<div class="tc-card">'
        f'<div class="tc-label">{label}</div>'
        f'<div class="tc-value">{value}</div>'
        f'<div class="tc-note">{note}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def bullets(items):
    if not items:
        st.write("None identified.")
        return

    for item in items:
        if isinstance(item, dict):
            text = " — ".join(
                str(value)
                for value in item.values()
                if value not in (None, "", [])
            )
            st.write(f"• {text}")
        else:
            st.write(f"• {item}")


with st.sidebar:
    st.markdown(
        '<div class="tc-brand">TechCheck HVAC&R</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="tc-sub">Technical QA Platform</div>',
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Review Report",
            "Quote Review",
            "Sounding Board",
            "Settings",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("● Live AI connected" if API_KEY else "○ Live AI not configured")


if page == "Dashboard":
    st.markdown(
        '<div class="tc-kicker">HVAC&R Technical QA</div>',
        unsafe_allow_html=True,
    )
    st.title("A second set of eyes on technical decisions")
    st.write(
        "Review technician reports, challenge repair recommendations, "
        "check quotation allowances and work through faults with Sounding Board."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        card(
            "Service reports",
            "Technical Review",
            "Diagnosis, evidence, labour and callback risk.",
        )

    with c2:
        card(
            "Quotations",
            "Commercial Review",
            "Scope, labour, materials and approval risk.",
        )

    with c3:
        card(
            "Sounding Board",
            "Fault Finding",
            "Work through symptoms with a senior technical mentor.",
        )

    st.subheader("Proof-of-concept workflow")
    st.write(
        "Provide the information a supervisor normally receives. TechCheck "
        "challenges the evidence, identifies what is missing and provides a "
        "recommendation. The supervisor remains the final decision-maker."
    )


elif page == "Review Report":
    st.markdown(
        '<div class="tc-kicker">Service Report Review</div>',
        unsafe_allow_html=True,
    )
    st.title("Review technician report")
    st.write("Upload the service docket or paste the technician notes.")

    left, right = st.columns([1.5, 0.5])

    with left:
        upload = st.file_uploader(
            "Upload report",
            type=["pdf", "docx", "txt", "md", "csv"],
        )
        notes = st.text_area(
            "Technician notes",
            height=300,
            placeholder="Paste technician notes here…",
        )

    with right:
        reference = st.text_input("Work order / reference")
        hours = st.number_input(
            "Total labour hours",
            min_value=0.0,
            step=0.25,
        )
        st.info(
            "Labour is assessed in context with the technician notes."
        )

    button1, button2 = st.columns(2)
    review_clicked = button1.button("Review report", width="stretch")
    challenge_clicked = button2.button(
        "Challenge the technician",
        width="stretch",
    )

    if review_clicked or challenge_clicked:
        try:
            text = notes.strip() or extract_text(upload)

            if not text:
                st.warning(
                    "Upload a report or paste technician notes first."
                )

            elif not API_KEY:
                st.error(
                    "Live AI is not configured. Add OPENAI_API_KEY "
                    "under Streamlit → App settings → Secrets."
                )

            else:
                payload = {
                    "work_order": reference,
                    "claimed_labour_hours": hours,
                    "technician_report": text,
                }

                prompt = (
                    CHALLENGE_PROMPT
                    if challenge_clicked
                    else SERVICE_REVIEW_PROMPT
                )

                with st.spinner("Analysing the report…"):
                    result = get_ai().structured(prompt, payload)

                if challenge_clicked:
                    st.subheader("Technician challenge")

                    a, b, c = st.columns(3)

                    with a:
                        card(
                            "Result",
                            result.get("challenge_result", ""),
                            result.get("main_issue", ""),
                        )

                    with b:
                        card(
                            "Confidence",
                            f"{result.get('confidence', 0)}%",
                        )

                    with c:
                        card(
                            "Would approve",
                            result.get("would_you_approve", ""),
                            result.get("reason", ""),
                        )

                    st.subheader("Alternative causes")
                    bullets(result.get("alternative_causes", []))

                    st.subheader("Missing evidence")
                    bullets(result.get("missing_evidence", []))

                    st.subheader("Best next test")
                    st.write(result.get("best_next_test", ""))

                    st.subheader("Labour comment")
                    st.write(result.get("labour_comment", ""))

                else:
                    diagnosis = result.get("diagnosis", {})
                    labour = result.get("labour", {})

                    st.subheader("Review outcome")

                    a, b, c, d = st.columns(4)

                    with a:
                        card(
                            "Decision",
                            result.get("decision", ""),
                            result.get("summary", ""),
                        )

                    with b:
                        card(
                            "Overall score",
                            f"{result.get('overall_score', 0)}/100",
                            f"{result.get('confidence', 0)}% confidence",
                        )

                    with c:
                        card(
                            "Diagnosis",
                            diagnosis.get("rating", ""),
                            diagnosis.get("reason", ""),
                        )

                    with d:
                        card(
                            "Labour",
                            labour.get("rating", ""),
                            labour.get("reasonable_range", ""),
                        )

                    st.subheader("Labour assessment")
                    st.write(labour.get("reason", ""))

                    sections = [
                        ("Technical concerns", "technical_concerns"),
                        ("Missing tests", "missing_tests"),
                        ("Parts review", "parts_review"),
                        ("Risks", "risks"),
                        (
                            "Questions for technician",
                            "questions_for_technician",
                        ),
                        ("Technician coaching", "coaching"),
                    ]

                    for title, key in sections:
                        values = result.get(key, [])
                        if values:
                            st.subheader(title)
                            bullets(values)

                    senior = result.get("senior_challenge", {})

                    with st.expander("Senior technician challenge"):
                        st.write("**Alternative causes**")
                        bullets(senior.get("alternative_causes", []))

                        st.write("**Not ruled out**")
                        bullets(senior.get("not_ruled_out", []))

                        st.write(
                            "**Best next test:**",
                            senior.get("best_next_test", ""),
                        )
                        st.write(
                            "**Cheaper first step:**",
                            senior.get("cheaper_first_step", ""),
                        )
                        st.write(
                            "**Root cause:**",
                            senior.get("root_cause_comment", ""),
                        )

                with st.expander("Full structured result"):
                    st.json(result)

        except Exception as exc:
            st.error(str(exc))


elif page == "Quote Review":
    st.markdown(
        '<div class="tc-kicker">Commercial QA</div>',
        unsafe_allow_html=True,
    )
    st.title("Review quotation")
    st.write(
        "Check scope clarity, labour allowances and commercial risk "
        "before approval."
    )

    col1, col2, col3 = st.columns([1.1, 0.8, 1.1])

    with col1:
        quote_reference = st.text_input("Quote reference")

    with col2:
        labour_hours = st.number_input(
            "Labour hours",
            min_value=0.0,
            step=0.25,
        )

    with col3:
        allowance = st.number_input(
            "Materials and equipment allowance ($)",
            min_value=0.0,
            step=50.0,
        )

    scope = st.text_area(
        "Scope and quotation details",
        height=300,
        placeholder=(
            "Example: Supply and install new condensate drain "
            "to high wall split system…"
        ),
    )

    if st.button("Review quotation", width="stretch"):
        if not scope.strip():
            st.warning("Enter the quotation scope first.")

        elif not API_KEY:
            st.error(
                "Live AI is not configured. Add OPENAI_API_KEY "
                "under Streamlit → App settings → Secrets."
            )

        else:
            try:
                payload = {
                    "quote_reference": quote_reference,
                    "claimed_labour_hours": labour_hours,
                    "materials_and_equipment_allowance_aud": allowance,
                    "scope_and_quotation_details": scope,
                }

                with st.spinner("Reviewing quotation…"):
                    result = get_ai().structured(
                        QUOTE_REVIEW_PROMPT,
                        payload,
                    )

                labour = result.get("labour", {})
                materials = result.get("materials", {})

                a, b, c = st.columns(3)

                with a:
                    card(
                        "Commercial risk",
                        result.get("commercial_risk", ""),
                        result.get("headline", ""),
                    )

                with b:
                    card(
                        "Labour",
                        labour.get("rating", ""),
                        labour.get("reasonable_range", ""),
                    )

                with c:
                    card(
                        "Materials / equipment",
                        materials.get("rating", ""),
                        f"${allowance:,.0f} entered",
                    )

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
                    (
                        "Questions before approval",
                        "questions_before_approval",
                    ),
                    ("Commercial notes", "commercial_notes"),
                ]:
                    values = result.get(key, [])

                    if values:
                        st.subheader(title)
                        bullets(values)

                with st.expander("Why?"):
                    st.write(
                        "TechCheck assesses the stated work against the "
                        "labour and allowance supplied. Access, EWP, builder's "
                        "works and other complexity are only treated as "
                        "justification when they are actually stated."
                    )
                    st.json(result)

            except Exception as exc:
                st.error(str(exc))


elif page == "Sounding Board":
    st.title("Sounding Board")

    if "sounding_board_messages" not in st.session_state:
        st.session_state.sounding_board_messages = [
            {
                "role": "assistant",
                "content": (
                    "Describe the fault or symptoms and I’ll help you "
                    "work through it."
                ),
            }
        ]

    for message in st.session_state.sounding_board_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_message = st.chat_input("Describe the symptoms…")

    if user_message:
        st.session_state.sounding_board_messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        with st.chat_message("user"):
            st.write(user_message)

        if not API_KEY:
            answer = (
                "Live AI is not configured yet. Add OPENAI_API_KEY "
                "in Streamlit Secrets."
            )

        else:
            try:
                with st.spinner("Thinking through the fault…"):
                    answer = get_ai().chat(
                        SOUNDING_BOARD_PROMPT,
                        st.session_state.sounding_board_messages,
                    )
            except Exception as exc:
                answer = str(exc)

        st.session_state.sounding_board_messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        with st.chat_message("assistant"):
            st.write(answer)

    if st.button("Clear conversation"):
        st.session_state.sounding_board_messages = [
            {
                "role": "assistant",
                "content": (
                    "Describe the fault or symptoms and I’ll help you "
                    "work through it."
                ),
            }
        ]
        st.rerun()


elif page == "Settings":
    st.markdown(
        '<div class="tc-kicker">Configuration</div>',
        unsafe_allow_html=True,
    )
    st.title("Settings")

    if API_KEY:
        st.success("Live AI connection is configured.")
    else:
        st.error("Live AI connection is not configured.")

    st.write(
        "In Streamlit, go to **App settings → Secrets** and add:"
    )

    st.code(
        'OPENAI_API_KEY = "sk-proj-your-real-key"',
        language="toml",
    )

    st.caption(
        "The AI model is configured inside the backend and is not "
        "shown to users."
    )

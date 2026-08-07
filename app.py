from __future__ import annotations
import streamlit as st

from techcheck.config import load_config
from techcheck.ai import AIClient, AIError
from techcheck.file_extract import extract_text
from techcheck.reviews import review_service, review_quote, demo_service, demo_quote
from techcheck.prompts import SOUNDING_BOARD_PROMPT
from techcheck.styles import CSS, card

st.set_page_config(page_title="TechCheck HVAC&R", page_icon="🛠️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
cfg = load_config(st)

def get_ai():
    if not cfg.api_key:
        raise AIError("Live AI is not configured. Add OPENAI_API_KEY in Streamlit Secrets.")
    return AIClient(cfg.api_key, cfg.model)

with st.sidebar:
    st.markdown("## TechCheck HVAC&R")
    st.caption("Technical QA platform")
    page = st.radio(
        "Navigation",
        ["Dashboard", "Review Report", "Quote Review", "Sounding Board", "Settings"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    mode = st.radio("Review mode", ["Live AI", "Demonstration"])
    if mode == "Live AI":
        st.caption("Live AI ready" if cfg.api_key else "API key not configured")

if page == "Dashboard":
    st.markdown('<div class="tc-kicker">Technical QA</div>', unsafe_allow_html=True)
    st.title("Dashboard")
    st.write("Independent HVAC&R technical and commercial review.")
    a,b,c = st.columns(3)
    with a:
        st.markdown(card("Report review", "Technical QA", "Challenge diagnosis, evidence and labour"), unsafe_allow_html=True)
    with b:
        st.markdown(card("Quote review", "Commercial QA", "Check scope, hours and allowances"), unsafe_allow_html=True)
    with c:
        st.markdown(card("Sounding Board", "Fault finding", "Work through symptoms with a senior technical mentor"), unsafe_allow_html=True)

elif page == "Review Report":
    st.markdown('<div class="tc-kicker">Technical QA</div>', unsafe_allow_html=True)
    st.title("Review service report")
    st.write("Upload a service docket or paste the technician notes.")
    upload = st.file_uploader("Report", type=["pdf","docx","txt","md","csv"])
    pasted = st.text_area("Technician report / notes", height=260)
    hours = st.number_input("Claimed labour hours", min_value=0.0, step=0.25)
    if st.button("Review report", use_container_width=True):
        try:
            text = pasted.strip() or extract_text(upload)
            if not text:
                st.warning("Add a report or paste technician notes first.")
            else:
                with st.spinner("Reviewing technical evidence..."):
                    result = review_service(get_ai(), text, hours) if mode == "Live AI" else demo_service(text, hours)
                st.success(f"{result.get('decision','Review complete')} — confidence {result.get('confidence','?')}%")
                st.subheader("Summary")
                st.write(result.get("summary",""))
                x,y,z = st.columns(3)
                with x: st.metric("Overall score", f"{result.get('overall_score',0)}/100")
                with y: st.metric("Labour", result.get("labour",{}).get("rating",""))
                with z: st.metric("Reasonable range", result.get("labour",{}).get("reasonable_range",""))
                for heading, key in [
                    ("Technical concerns","technical_concerns"),
                    ("Missing tests","missing_tests"),
                    ("Questions for technician","questions_for_technician"),
                    ("Coaching","coaching")
                ]:
                    vals = result.get(key, [])
                    if vals:
                        st.subheader(heading)
                        for v in vals:
                            st.write(f"• {v}")
                with st.expander("Full structured review"):
                    st.json(result)
        except Exception as exc:
            st.error(str(exc))

elif page == "Quote Review":
    st.markdown('<div class="tc-kicker">Commercial QA</div>', unsafe_allow_html=True)
    st.title("Review quotation")
    st.write("Check scope clarity, labour allowances, exclusions and commercial risk before issue or approval.")
    c1,c2,c3 = st.columns([1.05,.9,1.05])
    with c1:
        ref = st.text_input("Quote reference")
    with c2:
        q_hours = st.number_input("Labour hours", min_value=0.0, step=0.25)
    with c3:
        materials = st.number_input("Materials and equipment allowance ($)", min_value=0.0, step=50.0)
    scope = st.text_area("Scope and quotation details", height=300)
    if st.button("Review quotation", use_container_width=True):
        if not scope.strip():
            st.warning("Enter the quotation scope first.")
        else:
            try:
                with st.spinner("Reviewing scope, labour and commercial risk..."):
                    result = review_quote(get_ai(), ref, q_hours, materials, scope) if mode == "Live AI" else demo_quote(ref, q_hours, materials, scope)
                risk = result.get("commercial_risk","")
                decision = result.get("decision","")
                st.success(f"{decision} — {risk} commercial risk — confidence {result.get('confidence','?')}%")
                a,b,c = st.columns(3)
                with a:
                    st.markdown(card("Commercial risk", risk, result.get("headline","")), unsafe_allow_html=True)
                with b:
                    st.markdown(card("Labour assessment", result.get("labour",{}).get("rating",""), result.get("labour",{}).get("reasonable_range","")), unsafe_allow_html=True)
                with c:
                    st.markdown(card("Materials assessment", result.get("materials",{}).get("rating",""), f"${materials:,.0f} entered"), unsafe_allow_html=True)
                st.subheader("Labour")
                st.write(result.get("labour",{}).get("reason",""))
                st.subheader("Materials / equipment")
                st.write(result.get("materials",{}).get("reason",""))
                for heading,key in [
                    ("Items to check","items_to_check"),
                    ("Missing scope items","missing_scope_items"),
                    ("Questions before approval","questions_before_approval"),
                    ("Commercial notes","commercial_notes")
                ]:
                    vals=result.get(key,[])
                    if vals:
                        st.subheader(heading)
                        for v in vals:
                            st.write(f"• {v}")
                with st.expander("Full structured review"):
                    st.json(result)
            except Exception as exc:
                st.error(str(exc))

elif page == "Sounding Board":
    st.title("Sounding Board")
    if "chat" not in st.session_state:
        st.session_state.chat = [{
            "role":"assistant",
            "content":"Describe the fault or symptoms and I’ll help you work through it."
        }]
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    prompt = st.chat_input("Describe the symptoms…")
    if prompt:
        st.session_state.chat.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.write(prompt)
        try:
            if mode != "Live AI":
                answer = "Sounding Board requires Live AI. Add your API key and select Live AI in the sidebar."
            else:
                answer = get_ai().chat(SOUNDING_BOARD_PROMPT, st.session_state.chat)
            st.session_state.chat.append({"role":"assistant","content":answer})
            with st.chat_message("assistant"):
                st.write(answer)
        except Exception as exc:
            st.error(str(exc))
    if st.button("Clear chat"):
        st.session_state.chat = [{
            "role":"assistant",
            "content":"Describe the fault or symptoms and I’ll help you work through it."
        }]
        st.rerun()

elif page == "Settings":
    st.markdown('<div class="tc-kicker">Configuration</div>', unsafe_allow_html=True)
    st.title("Settings")
    st.write("The AI model is configured server-side and is not exposed to end users.")
    st.info("OpenAI API key: configured" if cfg.api_key else "OpenAI API key: not configured")
    st.write("For Streamlit Community Cloud, add these in **App settings → Secrets**:")
    st.code('OPENAI_API_KEY = "sk-proj-..."\nOPENAI_MODEL = "gpt-5.5"', language="toml")

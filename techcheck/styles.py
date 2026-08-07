CSS = """
<style>
:root {
  --navy:#0D2344;
  --orange:#F58A1F;
  --muted:#60708A;
}
.block-container {max-width: 1400px; padding-top: 2rem; padding-bottom: 4rem;}
h1,h2,h3 {color:var(--navy);}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#0B1D38,#102A4F);}
[data-testid="stSidebar"] * {color:white;}
div.stButton > button {
  background:var(--orange); color:white; border:none; border-radius:10px;
  min-height:42px; font-weight:700;
}
div.stButton > button:hover {background:#E57A10;color:white;border:none;}
.tc-card {
  background:#fff;border:1px solid #E1E7F0;border-radius:15px;padding:18px 20px;
  box-shadow:0 5px 18px rgba(13,35,68,.05); height:100%;
}
.tc-kicker {color:var(--orange);font-size:.78rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;}
.tc-muted {color:var(--muted);}
.tc-value {font-size:2rem;font-weight:800;color:var(--navy);}
</style>
"""

def card(title: str, value: str, note: str = "") -> str:
    return f'<div class="tc-card"><div class="tc-muted">{title}</div><div class="tc-value">{value}</div><div class="tc-muted">{note}</div></div>'

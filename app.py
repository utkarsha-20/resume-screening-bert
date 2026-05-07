import io
import os
import tempfile
from datetime import datetime

import pandas as pd
import streamlit as st

from src.parser import extract_text
from src.skills import extract_skills
from src.experience import extract_experience
from src.email_extractor import extract_email
from src.scorer import calculate_similarity, calculate_skill_match

st.set_page_config(
    page_title="HireMatch — Resume Screener",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Users ─────────────────────────────────────────────────────────────────────

USERS = {
    "admin":   {"password": "admin123",   "role": "Administrator", "name": "Admin"},
    "hr":      {"password": "hr2024",     "role": "HR Specialist",  "name": "HR Team"},
    "manager": {"password": "manager123", "role": "Hiring Manager", "name": "Manager"},
}

# ── Global CSS ────────────────────────────────────────────────────────────────

BASE_CSS = """
<style>
  html, body,
  [data-testid="stAppViewContainer"],
  [data-testid="stMain"],
  [data-testid="stApp"],
  .stApp, .main {
    background: #F6F4E8 !important;
    color: #2e2e2e !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
    font-size: 14px;
  }

  [data-testid="stSidebar"],
  [data-testid="collapsedControl"] { display: none; }
  #MainMenu, footer, header { visibility: hidden; }

  .block-container {
    max-width: 1240px;
    padding: 0 32px 64px;
    margin: 0 auto;
  }

  /* inputs */
  [data-testid="stTextArea"] textarea,
  [data-testid="stTextInput"] input {
    background: #fff !important;
    border: 1px solid #d8d4c8 !important;
    border-radius: 6px !important;
    color: #2e2e2e !important;
    font-size: 14px !important;
  }
  [data-testid="stTextArea"] textarea:focus,
  [data-testid="stTextInput"] input:focus {
    border-color: #DC9B9B !important;
    box-shadow: 0 0 0 2px #DC9B9B22 !important;
  }
  [data-testid="stFileUploader"] {
    background: #fff;
    border: 1px dashed #d0ccbf;
    border-radius: 6px;
  }
  [data-testid="stRadio"] label { font-size: 13px; color: #2e2e2e; }

  .stButton > button {
    background: #DC9B9B;
    color: #fff;
    border: 1px solid #c98888;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    padding: 8px 20px;
    transition: background 120ms ease;
  }
  .stButton > button:hover { background: #c98888; border-color: #b87777; }

  .stDownloadButton > button {
    background: #fff;
    color: #2e2e2e;
    border: 1px solid #d8d4c8;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    padding: 7px 16px;
  }
  .stDownloadButton > button:hover { background: #E5EEE4; border-color: #cdd8cc; }

  [data-testid="stTabs"] [role="tablist"] { border-bottom: 1px solid #d8d4c8; gap: 4px; }
  [data-testid="stTabs"] button {
    font-size: 14px; color: #7a7a72; background: transparent;
    border: none; border-bottom: 2px solid transparent;
    padding: 8px 14px; margin-bottom: -1px;
  }
  [data-testid="stTabs"] button[aria-selected="true"] {
    color: #2e2e2e; border-bottom-color: #DC9B9B; font-weight: 600;
  }

  [data-testid="stDataFrame"] { border: 1px solid #d8d4c8; border-radius: 6px; overflow: hidden; }
  [data-testid="stSlider"] { padding: 0; }
</style>
"""

# ── Login ─────────────────────────────────────────────────────────────────────

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    st.markdown("""
    <style>
      .login-shell {
        display: flex;
        min-height: calc(100vh - 80px);
        margin: 0 -32px;
      }
      .login-left {
        flex: 1;
        background: #DC9B9B;
        color: #fff;
        padding: 60px 56px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
      }
      .brand-row { font-size: 16px; font-weight: 700; letter-spacing: -0.2px; }
      .brand-row span { opacity: 0.8; font-weight: 500; margin-left: 8px; font-size: 13px; }
      .left-headline { font-size: 28px; font-weight: 600; line-height: 1.3; max-width: 380px; }
      .left-foot { font-size: 12px; opacity: 0.85; }

      .login-right {
        flex: 1;
        background: #F6F4E8;
        padding: 60px 64px;
        display: flex;
        align-items: center;
      }
      .login-card { max-width: 360px; width: 100%; }
      .login-h1 { font-size: 22px; font-weight: 600; color: #2e2e2e; margin-bottom: 6px; }
      .login-p  { font-size: 13px; color: #7a7a72; margin-bottom: 28px; }
      .login-creds {
        margin-top: 20px;
        font-size: 12px;
        color: #7a7a72;
        background: #E5EEE4;
        border: 1px solid #cdd8cc;
        border-radius: 6px;
        padding: 10px 12px;
        line-height: 1.6;
      }
      .login-creds b { color: #2e2e2e; }
      .login-err {
        font-size: 13px; color: #8a3a3a;
        background: #DC9B9B22; border: 1px solid #DC9B9B66;
        border-radius: 5px; padding: 8px 12px; margin-top: 10px;
      }
    </style>
    """, unsafe_allow_html=True)

    left, right = st.columns([1, 1], gap="small")
    with left:
        st.markdown("""
        <div style="background:#DC9B9B;color:#fff;padding:60px 48px;min-height:540px;
                    display:flex;flex-direction:column;justify-content:space-between;
                    border-radius:8px 0 0 8px;">
          <div style="font-size:16px;font-weight:700">HireMatch <span style="opacity:0.8;font-weight:500;font-size:13px;margin-left:6px">Recruiting workspace</span></div>
          <div style="font-size:26px;font-weight:600;line-height:1.35;max-width:360px">
            Screen and rank candidates against any job description in seconds.
          </div>
          <div style="font-size:12px;opacity:0.85">© HireMatch · Internal use only</div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div style="background:#fff;padding:48px 44px;min-height:540px;
                    border:1px solid #d8d4c8;border-left:none;border-radius:0 8px 8px 0;">
        """, unsafe_allow_html=True)
        st.markdown('<div style="font-size:22px;font-weight:600;color:#2e2e2e;margin-bottom:6px">Sign in</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;color:#7a7a72;margin-bottom:24px">Use your team credentials to continue.</div>', unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="username", label_visibility="visible")
        password = st.text_input("Password", placeholder="••••••••", type="password", label_visibility="visible")

        if st.button("Sign in", use_container_width=True):
            user = USERS.get(username)
            if user and user["password"] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = user["role"]
                st.session_state["display_name"] = user["name"]
                st.rerun()
            else:
                st.markdown('<div style="font-size:13px;color:#8a3a3a;background:#DC9B9B22;border:1px solid #DC9B9B66;border-radius:5px;padding:8px 12px;margin-top:10px">Incorrect username or password.</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:24px;font-size:12px;color:#7a7a72;background:#E5EEE4;border:1px solid #cdd8cc;border-radius:6px;padding:10px 12px;line-height:1.7">
          <b style="color:#2e2e2e">Demo accounts</b><br>
          admin / admin123 &nbsp; · &nbsp; hr / hr2024 &nbsp; · &nbsp; manager / manager123
        </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ── Authed app ────────────────────────────────────────────────────────────────

st.markdown(BASE_CSS, unsafe_allow_html=True)

st.markdown("""
<style>
  .topbar {
    background: #fff;
    border-bottom: 1px solid #d8d4c8;
    padding: 14px 32px;
    margin: 0 -32px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .brand { font-size: 16px; font-weight: 700; color: #2e2e2e; letter-spacing: -0.2px; }
  .brand span { color: #DC9B9B; }
  .nav-links { display: flex; gap: 22px; font-size: 13px; }
  .nav-links a {
    color: #7a7a72; text-decoration: none; padding: 6px 0;
    border-bottom: 2px solid transparent;
  }
  .nav-links a.active { color: #2e2e2e; border-bottom-color: #DC9B9B; font-weight: 500; }
  .user-pill {
    display: flex; align-items: center; gap: 10px;
    font-size: 13px; color: #2e2e2e;
  }
  .user-avatar {
    width: 28px; height: 28px; border-radius: 50%;
    background: #DC9B9B; color: #fff;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 600;
  }
  .user-meta { line-height: 1.2; }
  .user-name { font-weight: 600; color: #2e2e2e; }
  .user-role { font-size: 11px; color: #7a7a72; }

  .page-head {
    display: flex; justify-content: space-between; align-items: flex-end;
    margin-bottom: 20px;
  }
  .page-title { font-size: 22px; font-weight: 600; color: #2e2e2e; }
  .page-sub { font-size: 13px; color: #7a7a72; margin-top: 2px; }
  .page-meta { font-size: 12px; color: #7a7a72; }

  .panel {
    background: #fff;
    border: 1px solid #d8d4c8;
    border-radius: 8px;
    padding: 20px 22px;
  }
  .panel-h {
    font-size: 13px; font-weight: 600; color: #2e2e2e;
    margin-bottom: 4px;
  }
  .panel-sub { font-size: 12px; color: #7a7a72; margin-bottom: 14px; }

  .kpi-row { display: flex; gap: 12px; margin-bottom: 20px; }
  .kpi {
    flex: 1; background: #fff;
    border: 1px solid #d8d4c8; border-radius: 8px;
    padding: 16px 18px;
  }
  .kpi-l { font-size: 12px; color: #7a7a72; margin-bottom: 6px; }
  .kpi-v { font-size: 22px; font-weight: 600; color: #2e2e2e; line-height: 1; }

  .jd-block-h {
    font-size: 14px; font-weight: 600; color: #2e2e2e;
    padding: 14px 0 10px;
    border-bottom: 1px solid #d8d4c8;
    margin-bottom: 14px;
    display: flex; align-items: center; justify-content: space-between;
  }
  .jd-block-h .badge {
    font-size: 11px; font-weight: 500;
    background: #E5EEE4; color: #3a6b5a;
    border: 1px solid #cdd8cc;
    border-radius: 10px; padding: 2px 9px;
  }

  .row-card {
    background: #fff;
    border: 1px solid #d8d4c8;
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 8px;
  }
  .row-card.top { border-left: 3px solid #DC9B9B; }
  .name { font-size: 14px; font-weight: 600; color: #2e2e2e; }
  .rank { font-size: 12px; color: #7a7a72; margin-right: 8px; font-weight: 500; }
  .email-l { font-size: 12px; color: #7a7a72; }
  .meta-l  { font-size: 12px; color: #7a7a72; }
  .meta-l b { color: #2e2e2e; font-weight: 600; }

  .sbar { background: #ede9df; border-radius: 2px; height: 4px; width: 100%; margin: 8px 0 10px; }

  .tag {
    font-size: 11px; color: #3a6b5a;
    background: #E5EEE4; border: 1px solid #cdd8cc;
    border-radius: 3px; padding: 2px 8px;
    display: inline-block; margin: 2px 3px 2px 0;
  }
  .tag.gap { color: #7a7a72; background: transparent; border-color: #d8d4c8; border-style: dashed; }

  .empty {
    background: #fff;
    border: 1px dashed #d0ccbf;
    border-radius: 8px;
    padding: 40px 24px;
    text-align: center;
    color: #7a7a72;
    font-size: 14px;
  }
  .empty b { color: #2e2e2e; }

  .footer-bar {
    margin-top: 56px; padding-top: 18px;
    border-top: 1px solid #d8d4c8;
    font-size: 12px; color: #7a7a72;
    display: flex; justify-content: space-between;
  }
</style>
""", unsafe_allow_html=True)

uname    = st.session_state.get("username", "")
display  = st.session_state.get("display_name", uname.title())
role     = st.session_state.get("role", "User")
initials = (display[:2] if display else uname[:2]).upper()

# ── Top bar ───────────────────────────────────────────────────────────────────

bar_l, bar_c, bar_r = st.columns([2, 4, 2])
with bar_l:
    st.markdown(
        '<div style="font-size:18px;font-weight:700;color:#2e2e2e;padding-top:8px">'
        'Hire<span style="color:#DC9B9B">Match</span>'
        '</div>',
        unsafe_allow_html=True
    )
with bar_c:
    st.markdown(
        '<div style="display:flex;gap:24px;font-size:13px;padding-top:10px;justify-content:center">'
        '<span style="color:#2e2e2e;font-weight:500;border-bottom:2px solid #DC9B9B;padding-bottom:6px">Screening</span>'
        '<span style="color:#7a7a72">Candidates</span>'
        '<span style="color:#7a7a72">Roles</span>'
        '<span style="color:#7a7a72">Reports</span>'
        '</div>',
        unsafe_allow_html=True
    )
with bar_r:
    user_col, btn_col = st.columns([3, 2])
    with user_col:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;justify-content:flex-end;padding-top:4px">'
            f'<div style="text-align:right;line-height:1.2">'
            f'<div style="font-size:13px;font-weight:600;color:#2e2e2e">{display}</div>'
            f'<div style="font-size:11px;color:#7a7a72">{role}</div>'
            f'</div>'
            f'<div style="width:32px;height:32px;border-radius:50%;background:#DC9B9B;color:#fff;'
            f'display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:600">'
            f'{initials}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with btn_col:
        if st.button("Sign out", key="logout"):
            st.session_state.clear()
            st.rerun()

st.markdown('<div style="height:1px;background:#d8d4c8;margin:8px -32px 24px"></div>', unsafe_allow_html=True)

# ── Page header ───────────────────────────────────────────────────────────────

today = datetime.now().strftime("%a, %b %d %Y")
head_l, head_r = st.columns([3, 1])
with head_l:
    st.markdown(
        f'<div style="font-size:22px;font-weight:600;color:#2e2e2e">Resume screening</div>'
        f'<div style="font-size:13px;color:#7a7a72;margin-top:2px">'
        f'Match candidates against one or more job descriptions.</div>',
        unsafe_allow_html=True
    )
with head_r:
    st.markdown(
        f'<div style="text-align:right;font-size:12px;color:#7a7a72;padding-top:6px">{today}</div>',
        unsafe_allow_html=True
    )

st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def score_class(score):
    if score >= 55: return ""
    if score >= 35: return "mid"
    return "low"


def run_screening(resumes: dict, jd_text: str):
    jd_skills = extract_skills(jd_text)
    results = []
    progress = st.progress(0, text="Analysing resumes…")
    total = len(resumes)

    for i, (name, text) in enumerate(resumes.items()):
        resume_skills = extract_skills(text)
        years_exp = extract_experience(text)
        email = extract_email(text)
        semantic_score = round(calculate_similarity(jd_text, text), 2)
        skill_score, matched = calculate_skill_match(jd_skills, resume_skills)
        skill_score = round(skill_score, 2)
        final = round(semantic_score * 0.75 + skill_score * 0.25, 2)
        missing = [s for s in jd_skills if s not in matched]

        results.append({
            "Resume": name,
            "Email": email,
            "Final Score (%)": final,
            "Semantic Score (%)": semantic_score,
            "Skill Match Score (%)": skill_score,
            "Years of Experience": years_exp,
            "Matched Skills": matched,
            "Missing Skills": missing,
        })
        progress.progress((i + 1) / total, text=f"Analysed {i + 1} of {total} resumes")

    progress.empty()
    results.sort(key=lambda x: x["Final Score (%)"], reverse=True)
    return results


def to_excel(all_results: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for jd_name, results in all_results.items():
            sheet_name = jd_name[:31]
            df = pd.DataFrame([{
                "Rank": f"#{i + 1}",
                "Resume": r["Resume"],
                "Email": r["Email"],
                "Final (%)": r["Final Score (%)"],
                "Semantic (%)": r["Semantic Score (%)"],
                "Skill Match (%)": r["Skill Match Score (%)"],
                "Experience (yrs)": r["Years of Experience"],
                "Matched Skills": ", ".join(r["Matched Skills"]),
                "Skill Gaps": ", ".join(r["Missing Skills"]),
            } for i, r in enumerate(results)])
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return buf.getvalue()


# ── Inputs ────────────────────────────────────────────────────────────────────

col_jd, col_resumes = st.columns([1, 1], gap="large")

with col_jd:
    st.markdown('<div style="font-size:13px;font-weight:600;color:#2e2e2e;margin-bottom:4px">Job description</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px;color:#7a7a72;margin-bottom:10px">The role you are hiring for.</div>', unsafe_allow_html=True)

    jd_input_mode = st.radio(
        "JD mode", ["Paste text", "Upload .txt file"],
        horizontal=True, label_visibility="collapsed"
    )

    jd_texts = {}

    if jd_input_mode == "Paste text":
        jd_role = st.text_input("Role name", placeholder="Role name, e.g. Data Scientist", label_visibility="collapsed")
        jd_text_input = st.text_area("Paste JD", height=160,
            placeholder="Paste the job description here — responsibilities, required skills, qualifications…",
            label_visibility="collapsed")
        if jd_role.strip() and jd_text_input.strip():
            jd_texts[jd_role.strip()] = jd_text_input.strip()
        elif jd_text_input.strip():
            jd_texts["Job Description"] = jd_text_input.strip()
    else:
        jd_files = st.file_uploader("Upload JDs", type=["txt"],
            accept_multiple_files=True, label_visibility="collapsed",
            help="Upload one .txt file per role.")
        for jf in (jd_files or []):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
                f.write(jf.read())
                tmp_path = f.name
            text = extract_text(tmp_path)
            if text.strip():
                jd_texts[jf.name] = text
        if jd_files:
            st.markdown(f'<div style="font-size:12px;color:#7a7a72;margin-top:6px">{len(jd_texts)} JD{"s" if len(jd_texts) != 1 else ""} loaded</div>', unsafe_allow_html=True)

with col_resumes:
    st.markdown('<div style="font-size:13px;font-weight:600;color:#2e2e2e;margin-bottom:4px">Candidate resumes</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px;color:#7a7a72;margin-bottom:10px">Upload PDF, DOCX or TXT files. Bulk supported.</div>', unsafe_allow_html=True)

    resume_files = st.file_uploader("Upload resumes", type=["pdf", "docx", "txt"],
        accept_multiple_files=True, label_visibility="collapsed")
    if resume_files:
        st.markdown(f'<div style="font-size:12px;color:#7a7a72;margin-top:6px">{len(resume_files)} resume{"s" if len(resume_files) > 1 else ""} selected</div>', unsafe_allow_html=True)

st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
btn_l, btn_r = st.columns([1, 6])
with btn_l:
    run_clicked = st.button("Run screening", key="run")

st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

# ── Run ──────────────────────────────────────────────────────────────────────

if run_clicked:
    if not jd_texts:
        st.error("Please provide at least one job description.")
        st.stop()
    if not resume_files:
        st.error("Please upload at least one resume.")
        st.stop()

    resumes = {}
    for f in resume_files:
        suffix = os.path.splitext(f.name)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(f.read())
            tmp_path = tmp.name
        text = extract_text(tmp_path)
        if text.strip():
            resumes[f.name] = text

    if not resumes:
        st.error("Could not extract text from the uploaded resumes.")
        st.stop()

    all_results = {}
    for jd_name, jd_text in jd_texts.items():
        all_results[jd_name] = run_screening(resumes, jd_text)

    st.session_state["all_results"] = all_results

if "all_results" not in st.session_state:
    st.markdown(
        '<div style="background:#fff;border:1px dashed #d0ccbf;border-radius:8px;'
        'padding:48px 24px;text-align:center;color:#7a7a72;font-size:14px">'
        'Add a job description and upload resumes above, then run the screening.'
        '</div>',
        unsafe_allow_html=True
    )
    st.stop()

all_results = st.session_state["all_results"]

# ── Toolbar above results ────────────────────────────────────────────────────

t_l, t_r = st.columns([3, 1], gap="large")
with t_l:
    st.markdown('<div style="font-size:13px;font-weight:600;color:#2e2e2e;margin-bottom:4px">Minimum score</div>', unsafe_allow_html=True)
    min_score = st.slider("Minimum score", 0, 100, 0, 5, format="%d%%", label_visibility="collapsed")
with t_r:
    st.markdown('<div style="font-size:13px;font-weight:600;color:#2e2e2e;margin-bottom:4px">Export</div>', unsafe_allow_html=True)
    excel_bytes = to_excel(all_results)
    st.download_button(
        "Download Excel report",
        excel_bytes,
        "hirematch_results.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown('<div style="height:1px;background:#d8d4c8;margin:24px 0"></div>', unsafe_allow_html=True)

# ── Results per JD ────────────────────────────────────────────────────────────

for jd_name, results in all_results.items():
    filtered = [r for r in results if r["Final Score (%)"] >= min_score]

    top_score = round(float(results[0]["Final Score (%)"]), 2) if results else 0
    avg_score = round(sum(r["Final Score (%)"] for r in results) / len(results), 2) if results else 0
    strong = sum(1 for r in results if r["Final Score (%)"] >= 55)

    st.markdown(
        f'<div style="font-size:14px;font-weight:600;color:#2e2e2e;'
        f'padding:14px 0 10px;border-bottom:1px solid #d8d4c8;margin-bottom:14px;'
        f'display:flex;align-items:center;justify-content:space-between">'
        f'<span>{jd_name}</span>'
        f'<span style="font-size:11px;font-weight:500;background:#E5EEE4;color:#3a6b5a;'
        f'border:1px solid #cdd8cc;border-radius:10px;padding:2px 9px">'
        f'{len(filtered)} of {len(results)} shown</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    k1, k2, k3, k4 = st.columns(4)
    for col, label, val in [
        (k1, "Screened", f"{len(results)}"),
        (k2, "Top score", f"{top_score}%"),
        (k3, "Average", f"{avg_score}%"),
        (k4, "Strong matches", f"{strong}"),
    ]:
        col.markdown(
            f'<div style="background:#fff;border:1px solid #d8d4c8;border-radius:8px;padding:14px 16px">'
            f'<div style="font-size:12px;color:#7a7a72;margin-bottom:6px">{label}</div>'
            f'<div style="font-size:22px;font-weight:600;color:#2e2e2e;line-height:1">{val}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)

    tab_cards, tab_table = st.tabs(["Ranked candidates", "Table view"])

    with tab_cards:
        if not filtered:
            st.markdown(
                f'<p style="color:#7a7a72;font-size:13px">No candidates above {min_score}%. Lower the threshold.</p>',
                unsafe_allow_html=True
            )
        for idx, r in enumerate(filtered):
            score = round(float(r["Final Score (%)"]), 2)
            sem   = round(float(r["Semantic Score (%)"]), 2)
            skl   = round(float(r["Skill Match Score (%)"]), 2)
            exp   = r["Years of Experience"]
            cls   = score_class(score)

            badge = {
                "":    ("#5a3a3a", "#DC9B9B22", "#DC9B9B66"),
                "mid": ("#3a5a4a", "#E5EEE4",  "#cdd8cc"),
                "low": ("#7a7a72", "#F6F4E8",  "#d8d4c8"),
            }[cls]
            bar_color = {"": "#DC9B9B", "mid": "#C0E1D2", "low": "#d8d4c8"}[cls]
            border = "border-left: 3px solid #DC9B9B;" if idx == 0 else ""

            st.markdown(
                f'<div style="background:#fff;border:1px solid #d8d4c8;{border}'
                f'border-radius:6px;padding:14px 18px;margin-bottom:8px">',
                unsafe_allow_html=True
            )

            c_name, c_score = st.columns([5, 1])
            with c_name:
                st.markdown(
                    f'<div style="font-size:14px;font-weight:600;color:#2e2e2e">'
                    f'<span style="color:#7a7a72;font-weight:500;margin-right:8px">#{idx + 1}</span>'
                    f'{r["Resume"]}'
                    f'{"  ·  " + r["Email"] if r["Email"] else ""}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with c_score:
                st.markdown(
                    f'<div style="text-align:right;font-size:14px;font-weight:600;'
                    f'color:{badge[0]};background:{badge[1]};'
                    f'border:1px solid {badge[2]};border-radius:4px;padding:3px 12px">'
                    f'{score}%</div>',
                    unsafe_allow_html=True
                )

            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div style="font-size:12px;color:#7a7a72;margin-top:8px">Semantic fit&nbsp; <b style="color:#2e2e2e">{sem}%</b></div>', unsafe_allow_html=True)
            c2.markdown(f'<div style="font-size:12px;color:#7a7a72;margin-top:8px">Skill match&nbsp; <b style="color:#2e2e2e">{skl}%</b></div>', unsafe_allow_html=True)
            c3.markdown(f'<div style="font-size:12px;color:#7a7a72;margin-top:8px">Experience&nbsp; <b style="color:#2e2e2e">{exp} yrs</b></div>', unsafe_allow_html=True)

            st.markdown(
                f'<div style="background:#ede9df;border-radius:2px;height:4px;width:100%;margin:10px 0">'
                f'<div style="height:4px;border-radius:2px;background:{bar_color};width:{min(score,100)}%"></div>'
                f'</div>',
                unsafe_allow_html=True
            )

            matched = r["Matched Skills"]
            if matched:
                st.markdown(
                    f'<div style="font-size:12px;color:#7a7a72;margin:6px 0 4px">Matched skills ({len(matched)})</div>'
                    + '<div>'
                    + "".join(f'<span style="font-size:11px;color:#3a6b5a;background:#E5EEE4;border:1px solid #cdd8cc;border-radius:3px;padding:2px 8px;display:inline-block;margin:2px 3px 2px 0">{s}</span>' for s in matched)
                    + '</div>',
                    unsafe_allow_html=True
                )

            missing = r["Missing Skills"]
            if missing:
                st.markdown(
                    f'<div style="font-size:12px;color:#7a7a72;margin:8px 0 4px">Skill gaps ({len(missing)})</div>'
                    + '<div>'
                    + "".join(f'<span style="font-size:11px;color:#7a7a72;background:transparent;border:1px dashed #d8d4c8;border-radius:3px;padding:2px 8px;display:inline-block;margin:2px 3px 2px 0">{s}</span>' for s in missing)
                    + '</div>',
                    unsafe_allow_html=True
                )

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    with tab_table:
        df = pd.DataFrame([{
            "Rank": f"#{i + 1}",
            "Resume": r["Resume"],
            "Email": r["Email"],
            "Final (%)": r["Final Score (%)"],
            "Semantic (%)": r["Semantic Score (%)"],
            "Skill Match (%)": r["Skill Match Score (%)"],
            "Experience (yrs)": r["Years of Experience"],
            "Matched Skills": ", ".join(r["Matched Skills"]),
            "Skill Gaps": ", ".join(r["Missing Skills"]),
        } for i, r in enumerate(filtered)])

        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown('<div style="height:1px;background:#d8d4c8;margin:24px 0"></div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown(
    '<div style="margin-top:48px;padding-top:18px;border-top:1px solid #d8d4c8;'
    'font-size:12px;color:#7a7a72;display:flex;justify-content:space-between">'
    '<span>HireMatch · Internal recruiting workspace</span>'
    f'<span>Signed in as {display} ({role})</span>'
    '</div>',
    unsafe_allow_html=True
)

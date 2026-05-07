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
      .block-container { padding: 0 !important; max-width: 100% !important; }
      [data-testid="stAppViewContainer"] { background: #F6F4E8 !important; }

      .login-form-wrap {
        max-width: 360px;
        margin: 0 auto;
        padding: 0 8px;
      }
      .login-form-wrap [data-testid="stTextInput"] input {
        background: #fff !important;
        border: 1px solid #d8d4c8 !important;
        border-radius: 6px !important;
        padding: 10px 12px !important;
        font-size: 14px !important;
      }
      .login-form-wrap [data-testid="stTextInput"] label {
        font-size: 12px !important;
        font-weight: 500 !important;
        color: #2e2e2e !important;
      }
      .login-form-wrap div[data-testid="stButton"] > button {
        background: #2e2e2e !important;
        color: #fff !important;
        border: 1px solid #2e2e2e !important;
        border-radius: 6px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 10px 18px !important;
        width: 100%;
      }
      .login-form-wrap div[data-testid="stButton"] > button:hover {
        background: #1f1f1f !important;
        border-color: #1f1f1f !important;
      }
      .login-form-wrap [data-testid="stCheckbox"] label {
        font-size: 12px !important;
        color: #7a7a72 !important;
      }
    </style>
    """, unsafe_allow_html=True)

    left, right = st.columns([5, 6], gap="small")

    with left:
        st.markdown("""
        <div style="background:#DC9B9B;min-height:100vh;padding:48px 44px;
                    display:flex;flex-direction:column;justify-content:space-between;color:#fff">

          <div style="display:flex;align-items:center;gap:10px;font-size:15px;font-weight:600">
            <div style="width:28px;height:28px;background:#fff;color:#DC9B9B;
                        border-radius:6px;display:inline-flex;align-items:center;justify-content:center;
                        font-weight:700;font-size:13px">H</div>
            HireMatch
          </div>

          <div style="max-width:380px">
            <div style="font-size:13px;font-weight:500;opacity:0.85;margin-bottom:14px;
                        text-transform:uppercase;letter-spacing:0.4px">Recruiting workspace</div>
            <div style="font-size:26px;font-weight:600;line-height:1.35;margin-bottom:18px">
              Screen and rank candidates the way your team already works.
            </div>
            <div style="font-size:14px;line-height:1.6;opacity:0.92;margin-bottom:28px">
              Upload resumes, paste a job description, and get a ranked shortlist in seconds —
              with skill-match analysis and an Excel export when you need to share it.
            </div>

            <div style="background:#ffffff14;border:1px solid #ffffff33;border-radius:8px;padding:14px 16px">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <div style="font-size:12px;opacity:0.85">Senior Data Scientist · 47 candidates</div>
                <div style="font-size:11px;background:#ffffff22;border:1px solid #ffffff33;
                            border-radius:3px;padding:2px 8px">Live</div>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:13px;font-weight:500">
                <span>Priya Nair</span><span>91%</span>
              </div>
              <div style="background:#ffffff22;height:3px;border-radius:2px;margin:6px 0">
                <div style="background:#fff;width:91%;height:3px;border-radius:2px"></div>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:13px;opacity:0.85">
                <span>Arjun Sharma</span><span>78%</span>
              </div>
              <div style="background:#ffffff22;height:3px;border-radius:2px;margin:6px 0">
                <div style="background:#ffffffcc;width:78%;height:3px;border-radius:2px"></div>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:13px;opacity:0.65">
                <span>Lina Park</span><span>62%</span>
              </div>
              <div style="background:#ffffff22;height:3px;border-radius:2px;margin:6px 0 0">
                <div style="background:#ffffff99;width:62%;height:3px;border-radius:2px"></div>
              </div>
            </div>
          </div>

          <div style="display:flex;justify-content:space-between;font-size:12px;opacity:0.8">
            <span>© HireMatch</span>
            <span>v1.0 · Internal</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown(
            '<div style="min-height:100vh;display:flex;flex-direction:column;justify-content:center;'
            'padding:48px 32px">',
            unsafe_allow_html=True
        )
        st.markdown('<div class="login-form-wrap">', unsafe_allow_html=True)

        st.markdown(
            '<div style="font-size:24px;font-weight:600;color:#2e2e2e;margin-bottom:6px;'
            'letter-spacing:-0.3px">Welcome back</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="font-size:13px;color:#7a7a72;margin-bottom:28px">'
            'Sign in to continue to your recruiting workspace.</div>',
            unsafe_allow_html=True
        )

        username = st.text_input("Username", placeholder="e.g. hr")
        password = st.text_input("Password", placeholder="Enter password", type="password")

        opt_l, opt_r = st.columns([1, 1])
        with opt_l:
            st.checkbox("Remember username", value=False)
        with opt_r:
            st.markdown(
                '<div style="text-align:right;font-size:12px;color:#7a7a72;padding-top:6px">'
                '<a href="#" style="color:#7a7a72;text-decoration:none">Need help?</a></div>',
                unsafe_allow_html=True
            )

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        if st.button("Sign in", use_container_width=True, key="login_btn"):
            user = USERS.get(username)
            if user and user["password"] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = user["role"]
                st.session_state["display_name"] = user["name"]
                st.rerun()
            else:
                st.markdown(
                    '<div style="font-size:13px;color:#8a3a3a;background:#DC9B9B1f;'
                    'border:1px solid #DC9B9B55;border-radius:6px;padding:9px 12px;margin-top:12px">'
                    'Incorrect username or password.</div>',
                    unsafe_allow_html=True
                )

        st.markdown(
            '<div style="margin-top:32px;padding-top:18px;border-top:1px solid #d8d4c8">'
            '<div style="font-size:11px;color:#7a7a72;text-transform:uppercase;'
            'letter-spacing:0.4px;margin-bottom:10px">Demo accounts</div>'
            '<div style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;'
            'color:#2e2e2e;line-height:1.9">'
            '<div>admin <span style="color:#7a7a72">·</span> admin123</div>'
            '<div>hr <span style="color:#7a7a72">·</span> hr2024</div>'
            '<div>manager <span style="color:#7a7a72">·</span> manager123</div>'
            '</div></div>',
            unsafe_allow_html=True
        )

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

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

if "page" not in st.session_state:
    st.session_state["page"] = "Screening"

# ── Top bar ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  .nav-btns div[data-testid="stButton"] > button {
    background: transparent !important;
    color: #7a7a72 !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 4px !important;
    margin: 0 8px !important;
    box-shadow: none !important;
  }
  .nav-btns div[data-testid="stButton"] > button:hover {
    color: #2e2e2e !important;
    background: transparent !important;
  }
  .nav-btns .nav-active div[data-testid="stButton"] > button {
    color: #2e2e2e !important;
    border-bottom: 2px solid #DC9B9B !important;
    font-weight: 600 !important;
  }
  .signout-btn div[data-testid="stButton"] > button {
    background: #fff !important;
    color: #2e2e2e !important;
    border: 1px solid #d8d4c8 !important;
    border-radius: 6px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
  }
</style>
""", unsafe_allow_html=True)

bar_l, bar_c, bar_r = st.columns([2, 5, 2])

with bar_l:
    st.markdown(
        '<div style="font-size:18px;font-weight:700;color:#2e2e2e;padding-top:8px">'
        'Hire<span style="color:#DC9B9B">Match</span>'
        '</div>',
        unsafe_allow_html=True
    )

with bar_c:
    st.markdown('<div class="nav-btns" style="display:flex;justify-content:center;padding-top:4px">', unsafe_allow_html=True)
    n1, n2, n3, n4 = st.columns(4)
    pages = [("Screening", n1), ("Candidates", n2), ("Roles", n3), ("Reports", n4)]
    for label, col in pages:
        active_cls = "nav-active" if st.session_state["page"] == label else ""
        with col:
            st.markdown(f'<div class="{active_cls}">', unsafe_allow_html=True)
            if st.button(label, key=f"nav_{label}", use_container_width=True):
                st.session_state["page"] = label
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

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
        st.markdown('<div class="signout-btn">', unsafe_allow_html=True)
        if st.button("Sign out", key="logout"):
            st.session_state.clear()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="height:1px;background:#d8d4c8;margin:8px -32px 24px"></div>', unsafe_allow_html=True)

current_page = st.session_state["page"]

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


# ── Page router ──────────────────────────────────────────────────────────────

today = datetime.now().strftime("%a, %b %d %Y")

PAGE_INFO = {
    "Screening":  ("Resume screening",  "Match candidates against one or more job descriptions."),
    "Candidates": ("Candidates",        "Browse and search candidates from past screenings."),
    "Roles":      ("Roles",             "Manage saved job descriptions and role templates."),
    "Reports":    ("Reports",           "Aggregate metrics across recent screening sessions."),
}
title, sub = PAGE_INFO[current_page]

head_l, head_r = st.columns([3, 1])
with head_l:
    st.markdown(
        f'<div style="font-size:22px;font-weight:600;color:#2e2e2e">{title}</div>'
        f'<div style="font-size:13px;color:#7a7a72;margin-top:2px">{sub}</div>',
        unsafe_allow_html=True
    )
with head_r:
    st.markdown(
        f'<div style="text-align:right;font-size:12px;color:#7a7a72;padding-top:6px">{today}</div>',
        unsafe_allow_html=True
    )
st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)


def render_coming_soon(name, lines):
    st.markdown(
        f'<div style="background:#fff;border:1px solid #d8d4c8;border-radius:8px;'
        f'padding:32px 28px;margin-bottom:16px">'
        f'<div style="font-size:13px;font-weight:600;color:#2e2e2e;margin-bottom:8px">{name}</div>'
        f'<div style="font-size:13px;color:#7a7a72;line-height:1.6">{lines}</div>'
        f'<div style="margin-top:14px;font-size:11px;color:#3a6b5a;background:#E5EEE4;'
        f'border:1px solid #cdd8cc;border-radius:10px;padding:3px 10px;display:inline-block">'
        f'In development</div>'
        f'</div>',
        unsafe_allow_html=True
    )


if current_page == "Candidates":
    render_coming_soon(
        "Candidate database",
        "A unified view of every resume processed across all screening runs. "
        "Search by name, email, skill or score, and revisit past results without re-uploading."
    )
    saved = st.session_state.get("all_results", {})
    if saved:
        all_rows = []
        seen = set()
        for jd_name, results in saved.items():
            for r in results:
                key = (r["Resume"], r["Email"])
                if key in seen: continue
                seen.add(key)
                all_rows.append({
                    "Resume":      r["Resume"],
                    "Email":       r["Email"],
                    "Last role":   jd_name,
                    "Last score":  r["Final Score (%)"],
                    "Experience":  r["Years of Experience"],
                })
        st.markdown('<div style="font-size:13px;color:#7a7a72;margin-bottom:8px">'
                    f'Showing {len(all_rows)} unique candidate{"s" if len(all_rows) != 1 else ""} from your most recent session.</div>',
                    unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(all_rows), use_container_width=True, hide_index=True)
    st.stop()

if current_page == "Roles":
    render_coming_soon(
        "Role library",
        "Save commonly used job descriptions as reusable templates. "
        "Tag by department, seniority, or location and load them into a screening with one click."
    )
    saved = st.session_state.get("all_results", {})
    if saved:
        st.markdown('<div style="font-size:13px;font-weight:600;color:#2e2e2e;margin:16px 0 8px">Recent roles</div>', unsafe_allow_html=True)
        for jd_name, results in saved.items():
            st.markdown(
                f'<div style="background:#fff;border:1px solid #d8d4c8;border-radius:6px;padding:12px 16px;margin-bottom:6px">'
                f'<div style="font-size:13px;font-weight:600;color:#2e2e2e">{jd_name}</div>'
                f'<div style="font-size:12px;color:#7a7a72;margin-top:2px">{len(results)} candidates screened</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    st.stop()

if current_page == "Reports":
    render_coming_soon(
        "Aggregate reports",
        "Track screening volume, average match quality, and skill-gap trends over time. "
        "Export hiring funnel data for stakeholder reviews."
    )
    saved = st.session_state.get("all_results", {})
    if saved:
        total_jds       = len(saved)
        total_resumes   = sum(len(r) for r in saved.values())
        total_strong    = sum(1 for results in saved.values() for r in results if r["Final Score (%)"] >= 55)
        avg_top_score   = round(sum(results[0]["Final Score (%)"] for results in saved.values() if results) / max(total_jds, 1), 2)

        k1, k2, k3, k4 = st.columns(4)
        for col, label, val in [
            (k1, "Roles screened",  f"{total_jds}"),
            (k2, "Resumes processed", f"{total_resumes}"),
            (k3, "Strong matches", f"{total_strong}"),
            (k4, "Avg. top score", f"{avg_top_score}%"),
        ]:
            col.markdown(
                f'<div style="background:#fff;border:1px solid #d8d4c8;border-radius:8px;padding:14px 16px">'
                f'<div style="font-size:12px;color:#7a7a72;margin-bottom:6px">{label}</div>'
                f'<div style="font-size:22px;font-weight:600;color:#2e2e2e;line-height:1">{val}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    st.stop()

# ── Screening page ───────────────────────────────────────────────────────────

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

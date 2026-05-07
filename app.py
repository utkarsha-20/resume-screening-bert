import io
import os
import tempfile

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
    "admin":   "admin123",
    "hr":      "hr2024",
    "manager": "manager123",
}

# ── Login ─────────────────────────────────────────────────────────────────────

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("""
    <style>
      .login-wrap {
        max-width: 380px;
        margin: 80px auto 0;
        background: #fff;
        border: 1px solid #d8d4c8;
        border-radius: 8px;
        padding: 36px 32px 32px;
      }
      .login-title {
        font-size: 22px;
        font-weight: 700;
        color: #2e2e2e;
        margin-bottom: 4px;
      }
      .login-sub {
        font-size: 13px;
        color: #7a7a72;
        margin-bottom: 24px;
      }
      .login-err {
        font-size: 13px;
        color: #c0392b;
        background: #fdf0ee;
        border: 1px solid #e8b4ae;
        border-radius: 5px;
        padding: 8px 12px;
        margin-top: 12px;
      }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="
        background:#DC9B9B;
        padding: 40px 0 32px;
        text-align:center;
        margin: 0 -48px 32px;
    ">
        <div style="font-size:28px;font-weight:700;color:#fff;margin-bottom:6px">HireMatch 🎯</div>
        <div style="font-size:14px;color:#fff;opacity:0.88">Sign in to access the resume screener</div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", placeholder="Enter password", type="password")

        if st.button("Sign in", use_container_width=True):
            if username in USERS and USERS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.markdown('<div class="login-err">Incorrect username or password.</div>', unsafe_allow_html=True)

    st.stop()

st.markdown("""
<style>
  html, body,
  [data-testid="stAppViewContainer"],
  [data-testid="stMain"],
  [data-testid="stApp"],
  .stApp, .main {
    background: #F6F4E8 !important;
    color: #2e2e2e !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    font-size: 15px;
  }

  [data-testid="stSidebar"],
  [data-testid="collapsedControl"] { display: none; }
  #MainMenu, footer, header { visibility: hidden; }

  .block-container {
    max-width: 1200px;
    padding: 0 48px 56px;
    margin: 0 auto;
  }

  .hero {
    background: #DC9B9B;
    color: #fff;
    padding: 40px 48px 36px;
    margin: 0 -48px 36px;
  }
  .hero-title {
    font-size: 32px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }
  .hero-sub {
    font-size: 16px;
    color: #fff;
    opacity: 0.88;
    margin-bottom: 20px;
    max-width: 680px;
    line-height: 1.5;
  }
  .hero-pills { display: flex; gap: 10px; flex-wrap: wrap; }
  .hero-pill {
    font-size: 12px;
    color: #fff;
    border: 1px solid #ffffff55;
    border-radius: 4px;
    padding: 3px 10px;
  }

  .how-row {
    display: flex;
    gap: 0;
    margin-bottom: 32px;
    border: 1px solid #d8d4c8;
    border-radius: 8px;
    overflow: hidden;
  }
  .how-step {
    flex: 1;
    padding: 16px 18px;
    background: #fff;
    border-right: 1px solid #d8d4c8;
  }
  .how-step:last-child { border-right: none; }
  .how-num { font-size: 11px; font-weight: 700; color: #DC9B9B; margin-bottom: 4px; }
  .how-text { font-size: 13px; color: #2e2e2e; font-weight: 500; }
  .how-desc { font-size: 12px; color: #7a7a72; margin-top: 2px; }

  .section-label { font-size: 13px; font-weight: 600; color: #3a3a32; margin-bottom: 10px; }

  [data-testid="stTextArea"] textarea,
  [data-testid="stTextInput"] input {
    background: #F6F4E8 !important;
    border: 1px solid #ccc9bc !important;
    border-radius: 6px !important;
    color: #2e2e2e !important;
    font-size: 14px !important;
  }
  [data-testid="stTextArea"] textarea:focus,
  [data-testid="stTextInput"] input:focus {
    border-color: #DC9B9B !important;
    box-shadow: 0 0 0 3px #DC9B9B1a !important;
  }
  [data-testid="stFileUploader"] {
    background: #F6F4E8;
    border: 1px dashed #ccc9bc;
    border-radius: 6px;
  }
  [data-testid="stRadio"] label { font-size: 14px; color: #2e2e2e; }

  .stButton > button {
    background: #DC9B9B;
    color: #fff;
    border: 1px solid #c98888;
    border-radius: 6px;
    font-size: 15px;
    font-weight: 600;
    padding: 10px 32px;
    transition: background 150ms ease;
  }
  .stButton > button:hover { background: #c98888; border-color: #b87777; }

  .stDownloadButton > button {
    background: #E5EEE4;
    color: #2e2e2e;
    border: 1px solid #cdd8cc;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    padding: 7px 18px;
  }

  .divider { height: 1px; background: #d8d4c8; margin: 28px 0; }

  /* ── JD section header ── */
  .jd-header {
    font-size: 15px;
    font-weight: 700;
    color: #2e2e2e;
    padding: 14px 0 10px;
    border-bottom: 1px solid #d8d4c8;
    margin-bottom: 16px;
  }

  .stat-row { display: flex; gap: 10px; margin-bottom: 24px; }
  .stat-box {
    flex: 1;
    background: #fff;
    border: 1px solid #d8d4c8;
    border-radius: 6px;
    padding: 16px 18px;
  }
  .stat-box.rose { border-left: 3px solid #DC9B9B; }
  .stat-box.mint { border-left: 3px solid #C0E1D2; }
  .stat-box .icon { font-size: 18px; margin-bottom: 6px; }
  .stat-box .val { font-size: 28px; font-weight: 700; color: #2e2e2e; line-height: 1; }
  .stat-box .lbl { font-size: 13px; color: #7a7a72; margin-top: 4px; }

  .result-card {
    background: #fff;
    border: 1px solid #d8d4c8;
    border-radius: 6px;
    padding: 18px 20px;
    margin-bottom: 10px;
  }
  .result-card.top-card { border-left: 3px solid #DC9B9B; }

  .card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  .resume-name { font-size: 16px; font-weight: 600; color: #2e2e2e; }
  .top-label { font-size: 11px; font-weight: 600; color: #DC9B9B; margin-left: 8px; }
  .email-link { font-size: 12px; color: #7a7a72; margin-left: 10px; }

  .score-badge {
    font-size: 14px; font-weight: 700;
    color: #5a3a3a; background: #DC9B9B1a;
    border: 1px solid #DC9B9B88;
    border-radius: 4px; padding: 3px 12px;
  }
  .score-badge.mid { color: #3a5a4a; background: #C0E1D21a; border-color: #C0E1D2; }
  .score-badge.low { color: #7a7a72; background: #E5EEE4; border-color: #cdd8cc; }

  .meta-row { display: flex; gap: 24px; margin-bottom: 10px; font-size: 13px; color: #7a7a72; }
  .meta-row span b { color: #2e2e2e; font-weight: 600; }
  .meta-item { font-size: 13px; color: #7a7a72; margin-bottom: 8px; }
  .meta-item b { color: #2e2e2e; font-weight: 600; }

  .bar-track { background: #ede9df; border-radius: 3px; height: 5px; width: 100%; margin-bottom: 14px; }
  .bar-fill     { height: 5px; border-radius: 3px; background: #DC9B9B; }
  .bar-fill.mid { background: #C0E1D2; }
  .bar-fill.low { background: #d8d4c8; }

  .skills-row { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; }
  .skill-tag {
    font-size: 12px; color: #3a6b5a;
    background: #C0E1D230; border: 1px solid #C0E1D2;
    border-radius: 4px; padding: 2px 9px;
  }
  .skill-tag.miss { color: #7a7a72; background: transparent; border-color: #d0d0c8; }
  .skills-section-label { font-size: 12px; color: #7a7a72; margin: 10px 0 4px; }

  .empty-state { text-align: center; padding: 48px 24px; color: #7a7a72; font-size: 15px; }
  .empty-state .big { font-size: 36px; margin-bottom: 12px; }
  .empty-state b { color: #2e2e2e; }

  [data-testid="stTabs"] [role="tablist"] { border-bottom: 1px solid #d8d4c8; }
  [data-testid="stTabs"] button {
    font-size: 15px; color: #7a7a72; background: transparent;
    border: none; border-bottom: 2px solid transparent;
    padding: 8px 16px; margin-bottom: -1px;
  }
  [data-testid="stTabs"] button[aria-selected="true"] {
    color: #2e2e2e; border-bottom-color: #DC9B9B; font-weight: 600;
  }

  [data-testid="stDataFrame"] { border: 1px solid #d8d4c8; border-radius: 6px; overflow: hidden; }

  .app-footer {
    margin-top: 48px; padding-top: 20px;
    border-top: 1px solid #d8d4c8;
    font-size: 12px; color: #7a7a72;
    display: flex; justify-content: space-between;
  }

  /* slider */
  [data-testid="stSlider"] { padding: 0; }
</style>
""", unsafe_allow_html=True)


def score_class(score):
    if score >= 55:
        return ""
    if score >= 35:
        return "mid"
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
        semantic_score = round(calculate_similarity(jd_text, text), 1)
        skill_score, matched = calculate_skill_match(jd_skills, resume_skills)
        skill_score = round(skill_score, 1)
        final = round(semantic_score * 0.75 + skill_score * 0.25, 1)
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
            sheet_name = jd_name[:31]  # Excel sheet name limit
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


# ── Hero ─────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="hero">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div class="hero-title">HireMatch 🎯</div>
      <div class="hero-sub">
        Screen resumes in seconds. Rank candidates by semantic fit and skill coverage — not just keyword count.
      </div>
      <div class="hero-pills">
        <span class="hero-pill">🧠 BERT-powered matching</span>
        <span class="hero-pill">📄 PDF · DOCX · TXT</span>
        <span class="hero-pill">🛠 Skill gap analysis</span>
        <span class="hero-pill">📧 Email extraction</span>
        <span class="hero-pill">📊 Export to Excel</span>
      </div>
    </div>
    <div style="font-size:13px;color:#fff;opacity:0.85;white-space:nowrap;padding-top:4px">
      👤 {st.session_state.get("username","")}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

if st.button("Sign out", key="logout"):
    st.session_state.clear()
    st.rerun()

# ── How it works ─────────────────────────────────────────────────────────────

st.markdown("""
<div class="how-row">
  <div class="how-step">
    <div class="how-num">STEP 1</div>
    <div class="how-text">📋 Upload job descriptions</div>
    <div class="how-desc">One or multiple JDs at once</div>
  </div>
  <div class="how-step">
    <div class="how-num">STEP 2</div>
    <div class="how-text">📂 Upload resumes</div>
    <div class="how-desc">Bulk upload PDF, DOCX, or TXT</div>
  </div>
  <div class="how-step">
    <div class="how-num">STEP 3</div>
    <div class="how-text">⚡ Run screening</div>
    <div class="how-desc">BERT scores every resume instantly</div>
  </div>
  <div class="how-step">
    <div class="how-num">STEP 4</div>
    <div class="how-text">✅ Filter & export</div>
    <div class="how-desc">Set score threshold, download Excel</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Inputs ────────────────────────────────────────────────────────────────────

col_jd, col_resumes = st.columns([1, 1], gap="large")

with col_jd:
    st.markdown(
        '<div class="section-label">📋 Job Description <span style="font-weight:400;color:#7a7a72;font-size:12px">— the role you are hiring for</span></div>',
        unsafe_allow_html=True
    )
    jd_input_mode = st.radio(
        "JD mode", ["Paste text", "Upload .txt file"],
        horizontal=True, label_visibility="collapsed"
    )

    jd_texts = {}

    if jd_input_mode == "Paste text":
        jd_role = st.text_input(
            "Role name", placeholder="Role name, e.g. Data Scientist",
            label_visibility="collapsed"
        )
        jd_text_input = st.text_area(
            "Paste JD",
            height=148,
            placeholder="Paste the job description text here — skills, requirements, responsibilities…",
            label_visibility="collapsed"
        )
        if jd_role.strip() and jd_text_input.strip():
            jd_texts[jd_role.strip()] = jd_text_input.strip()
        elif jd_text_input.strip():
            jd_texts["Job Description"] = jd_text_input.strip()
    else:
        st.markdown(
            '<div style="font-size:12px;color:#7a7a72;margin-bottom:6px">Upload .txt job description files — one file per role</div>',
            unsafe_allow_html=True
        )
        jd_files = st.file_uploader(
            "Upload JDs", type=["txt"],
            accept_multiple_files=True, label_visibility="collapsed"
        )
        for jf in (jd_files or []):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
                f.write(jf.read())
                tmp_path = f.name
            text = extract_text(tmp_path)
            if text.strip():
                jd_texts[jf.name] = text
        if jd_files:
            st.markdown(
                f'<div style="font-size:13px;color:#7a7a72;margin-top:6px">✓ {len(jd_texts)} JD{"s" if len(jd_texts) != 1 else ""} loaded</div>',
                unsafe_allow_html=True
            )

with col_resumes:
    st.markdown(
        '<div class="section-label">📂 Candidate Resumes <span style="font-weight:400;color:#7a7a72;font-size:12px">— PDF, DOCX, or TXT</span></div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div style="font-size:12px;color:#7a7a72;margin-bottom:6px">Upload one or more candidate resume files</div>',
        unsafe_allow_html=True
    )
    resume_files = st.file_uploader(
        "Upload resumes",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if resume_files:
        st.markdown(
            f'<div style="font-size:13px;color:#7a7a72;margin-top:6px">✓ {len(resume_files)} resume{"s" if len(resume_files) > 1 else ""} selected</div>',
            unsafe_allow_html=True
        )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
run_clicked = st.button("⚡ Run Screening", key="run")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Guard ────────────────────────────────────────────────────────────────────

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
    st.markdown("""
    <div class="empty-state">
      <div class="big">📄</div>
      Add job descriptions and upload candidate resumes above, then hit <b>Run Screening</b>.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

all_results = st.session_state["all_results"]

# ── Score filter ──────────────────────────────────────────────────────────────

col_filter, col_export = st.columns([3, 1], gap="large")

with col_filter:
    st.markdown('<div class="section-label">Filter by minimum score</div>', unsafe_allow_html=True)
    min_score = st.slider(
        "Minimum score", 0, 100, 0, 5,
        format="%d%%", label_visibility="collapsed"
    )

with col_export:
    st.markdown('<div class="section-label">Export all results</div>', unsafe_allow_html=True)
    excel_bytes = to_excel(all_results)
    st.download_button(
        "⬇ Download Excel",
        excel_bytes,
        "hirematch_results.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Results per JD ────────────────────────────────────────────────────────────

for jd_name, results in all_results.items():
    filtered = [r for r in results if r["Final Score (%)"] >= min_score]

    top_score = round(float(results[0]["Final Score (%)"]), 2) if results else 0
    avg_score = round(sum(r["Final Score (%)"] for r in results) / len(results), 2) if results else 0
    strong = sum(1 for r in results if r["Final Score (%)"] >= 55)

    st.markdown(f'<div class="jd-header">📋 {jd_name}</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-box">
        <div class="icon">📄</div>
        <div class="val">{len(results)}</div>
        <div class="lbl">Screened</div>
      </div>
      <div class="stat-box rose">
        <div class="icon">🏆</div>
        <div class="val">{top_score}%</div>
        <div class="lbl">Top score</div>
      </div>
      <div class="stat-box">
        <div class="icon">📊</div>
        <div class="val">{avg_score}%</div>
        <div class="lbl">Average</div>
      </div>
      <div class="stat-box mint">
        <div class="icon">✅</div>
        <div class="val">{strong}</div>
        <div class="lbl">Strong matches ≥55%</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    tab_cards, tab_table = st.tabs(["📋 Ranked Results", "📊 Table View"])

    with tab_cards:
        if not filtered:
            st.markdown(
                f'<p style="color:#7a7a72;font-size:13px">No candidates scored above {min_score}%. Lower the filter threshold.</p>',
                unsafe_allow_html=True
            )
        for idx, r in enumerate(filtered):
            score = round(float(r["Final Score (%)"]), 2)
            sem   = round(float(r["Semantic Score (%)"]), 2)
            skl   = round(float(r["Skill Match Score (%)"]), 2)
            exp   = r["Years of Experience"]
            cls   = score_class(score)
            border = "border-left: 3px solid #DC9B9B;" if idx == 0 else ""

            badge_color = {
                "":    ("#5a3a3a", "#DC9B9B1a", "#DC9B9B88"),
                "mid": ("#3a5a4a", "#C0E1D21a", "#C0E1D2"),
                "low": ("#7a7a72", "#E5EEE4",   "#cdd8cc"),
            }[cls]
            bar_color = {"": "#DC9B9B", "mid": "#C0E1D2", "low": "#d8d4c8"}[cls]

            # ── card open
            st.markdown(
                f'<div class="result-card" style="{border}">',
                unsafe_allow_html=True
            )

            # ── header row: name + score
            c_name, c_score = st.columns([5, 1])
            with c_name:
                rank_str = f"#{idx + 1} — {r['Resume']}"
                best     = "  ⭐ Best match" if idx == 0 else ""
                email    = f"  ·  📧 {r['Email']}" if r["Email"] else ""
                st.markdown(
                    f'<div class="resume-name">{rank_str}'
                    f'<span class="top-label">{best}</span>'
                    f'<span class="email-link">{email}</span></div>',
                    unsafe_allow_html=True
                )
            with c_score:
                st.markdown(
                    f'<div style="text-align:right;font-size:15px;font-weight:700;'
                    f'color:{badge_color[0]};background:{badge_color[1]};'
                    f'border:1px solid {badge_color[2]};border-radius:4px;padding:4px 12px;">'
                    f'{score}%</div>',
                    unsafe_allow_html=True
                )

            # ── meta row
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="meta-item">🧠 Semantic fit&nbsp; <b>{sem}%</b></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="meta-item">🛠 Skill match&nbsp; <b>{skl}%</b></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="meta-item">📅 Experience&nbsp; <b>{exp} yrs</b></div>', unsafe_allow_html=True)

            # ── score bar
            st.markdown(
                f'<div class="bar-track"><div style="height:5px;border-radius:3px;'
                f'background:{bar_color};width:{min(score,100)}%"></div></div>',
                unsafe_allow_html=True
            )

            # ── matched skills
            matched = r["Matched Skills"]
            st.markdown(f'<div class="skills-section-label">Matched skills ({len(matched)})</div>', unsafe_allow_html=True)
            if matched:
                st.markdown(
                    '<div class="skills-row">'
                    + "".join(f'<span class="skill-tag">{s}</span>' for s in matched)
                    + "</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown('<div style="color:#7a7a72;font-size:12px">None found</div>', unsafe_allow_html=True)

            # ── skill gaps
            missing = r["Missing Skills"]
            if missing:
                st.markdown(f'<div class="skills-section-label">Skill gaps ({len(missing)})</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="skills-row">'
                    + "".join(f'<span class="skill-tag miss">{s}</span>' for s in missing)
                    + "</div>",
                    unsafe_allow_html=True
                )

            # ── card close
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

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="app-footer">
  <span>HireMatch — powered by BERT · sentence-transformers</span>
  <span>Results are ranked by semantic fit + skill coverage</span>
</div>
""", unsafe_allow_html=True)

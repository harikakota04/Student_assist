import streamlit as st
import requests
import math
import re as _re
from datetime import date, timedelta, datetime

st.set_page_config(
    page_title="StudentAssist",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

API = "http://localhost:8000/api/v1"

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

*, body { font-family: 'DM Sans', sans-serif; }
h1,h2,h3,.sec-title,.score-num,.word-title { font-family: 'Sora', sans-serif; }
.stApp { background: #0B0D14; color: #E2E4EE; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0F1117 !important;
    border-right: 1px solid #1E2130 !important;
    width: 230px !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    border-radius: 10px !important;
    color: #8B8FA8 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    text-align: left !important;
    padding: 10px 16px !important;
    width: 100% !important;
    transition: all 0.15s !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1A1D2E !important;
    color: #A5B4FC !important;
    transform: none !important;
}
.nav-active > button {
    background: linear-gradient(135deg,#312E81,#1E1B4B) !important;
    color: #C4B5FD !important;
    border: 1px solid #4338CA44 !important;
}

/* ── Cards ── */
.card { background: #13161F; border-radius: 14px; padding: 20px; border: 1px solid #1E2130; margin-bottom: 12px; }
.hero-bar { background: linear-gradient(135deg,#312E81,#4C1D95); border-radius: 16px; padding: 24px 28px; margin-bottom: 18px; }
.accent-bar { background: #0F1117; border: 1px solid #312E8155; border-radius: 14px; padding: 16px 20px; margin-bottom: 14px; }

/* ── Badges ── */
.badge { display:inline-block; padding:3px 11px; border-radius:20px; font-size:11px; font-weight:600; margin:2px; }
.b-blue   { background:#172554; color:#93C5FD; border:1px solid #1D4ED844; }
.b-purple { background:#1E1B4B; color:#C4B5FD; border:1px solid #6D28D944; }
.b-green  { background:#052E16; color:#6EE7B7; border:1px solid #16A34A44; }
.b-yellow { background:#1C1100; color:#FCD34D; border:1px solid #D9770644; }
.b-red    { background:#1F0808; color:#FCA5A5; border:1px solid #DC262644; }
.b-gray   { background:#111827; color:#9CA3AF; border:1px solid #374151; }
.b-teal   { background:#042F2E; color:#5EEAD4; border:1px solid #0D948044; }
.b-orange { background:#1C0A00; color:#FDBA74; border:1px solid #C2410C44; }

/* ── Text boxes ── */
.expbox     { background:#12103A; border-left:4px solid #818CF8; border-radius:0 10px 10px 0; padding:14px 18px; font-size:14px; color:#C4B5FD; line-height:1.7; margin:10px 0; }
.tipbox     { background:#110D00; border:1px solid #D9770644; border-radius:10px; padding:12px 16px; font-size:13px; color:#FCD34D; margin:8px 0; }
.successbox { background:#021208; border:1px solid #16A34A44; border-radius:10px; padding:12px 16px; font-size:13px; color:#86EFAC; margin:8px 0; }
.errorbox   { background:#1F0808; border:1px solid #DC262644; border-radius:10px; padding:12px 16px; font-size:13px; color:#FCA5A5; margin:8px 0; }
.infobox    { background:#0C1628; border:1px solid #3B82F644; border-radius:10px; padding:12px 16px; font-size:13px; color:#93C5FD; margin:8px 0; }

/* ── Steps ── */
.step  { display:flex; gap:10px; align-items:flex-start; padding:11px 14px; background:#13161F; border-radius:10px; border:1px solid #1E2130; margin-bottom:8px; }
.stepn { background:linear-gradient(135deg,#4338CA,#6D28D9); color:white; border-radius:50%; min-width:26px; height:26px; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; flex-shrink:0; }

/* ── Progress bars ── */
.progress-wrap { background:#1A1D27; border-radius:8px; height:10px; overflow:hidden; }
.skill-bar-bg  { background:#1A1D27; border-radius:6px; height:8px; overflow:hidden; margin-top:4px; }

/* ── Questions ── */
.question-card  { background:#13161F; border:1px solid #1E2130; border-radius:14px; padding:18px; margin-bottom:12px; }
.q-header       { display:flex; align-items:center; gap:8px; margin-bottom:10px; flex-wrap:wrap; }
.q-num          { background:linear-gradient(135deg,#4338CA,#6D28D9); color:white; border-radius:6px; padding:2px 10px; font-size:12px; font-weight:700; }
.diff-easy      { background:#052E16; color:#6EE7B7; border-radius:6px; padding:2px 9px; font-size:11px; font-weight:700; }
.diff-medium    { background:#1C1100; color:#FCD34D; border-radius:6px; padding:2px 9px; font-size:11px; font-weight:700; }
.diff-hard      { background:#1F0808; color:#FCA5A5; border-radius:6px; padding:2px 9px; font-size:11px; font-weight:700; }
.correct-opt    { background:#021208; border:2px solid #16A34A; border-radius:8px; padding:8px 14px; margin:4px 0; font-size:14px; color:#86EFAC; }
.wrong-opt      { background:#1F0808; border:2px solid #DC2626; border-radius:8px; padding:8px 14px; margin:4px 0; font-size:14px; color:#FCA5A5; }
.neutral-opt    { background:#0B0D14; border:1px solid #1E2130; border-radius:8px; padding:8px 14px; margin:4px 0; font-size:14px; color:#9CA3AF; }

/* ── Score hero ── */
.score-hero { background:linear-gradient(135deg,#1E1B4B,#2E1065); border-radius:16px; padding:28px; color:white; text-align:center; margin-bottom:18px; border:1px solid #4338CA33; }
.score-num  { font-size:56px; font-weight:800; line-height:1; font-family:'Sora',sans-serif; }

/* ── Stat cards ── */
.stat-card  { background:#13161F; border:1px solid #1E2130; border-radius:14px; padding:18px; text-align:center; }
.stat-num   { font-size:32px; font-weight:800; font-family:'Sora',sans-serif; }
.stat-label { font-size:11px; color:#4B5563; margin-top:4px; text-transform:uppercase; letter-spacing:.05em; }

/* ── Tracker ── */
.week-card      { background:#13161F; border:1px solid #1E2130; border-radius:12px; padding:16px; margin-bottom:10px; }
.topic-entry    { background:#0B0D14; border:1px solid #1E2130; border-radius:8px; padding:10px 14px; margin-bottom:8px; }
.conf-dot       { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:4px; }
.sched-week     { background:#13161F; border:1px solid #1E2130; border-radius:10px; padding:14px 16px; margin-bottom:8px; }
.sched-done     { border-color:#16A34A44; background:#021208; }
.sched-current  { border-color:#6D28D944; background:#0F0D20; }

/* ── Flashcards ── */
.fc-front { background:linear-gradient(135deg,#1E1B4B,#2E1065); border-radius:16px; padding:28px; color:white; min-height:180px; }
.fc-back  { background:#13161F; border:2px solid #4338CA; border-radius:16px; padding:24px; min-height:180px; }
.fc-q     { font-size:17px; font-weight:700; line-height:1.5; font-family:'Sora',sans-serif; }
.fc-answer{ font-size:15px; font-weight:700; color:#E2E4EE; margin-bottom:12px; line-height:1.6; font-family:'Sora',sans-serif; }
.fc-example{ background:#021208; border-left:3px solid #16A34A; border-radius:0 8px 8px 0; padding:9px 13px; font-size:13px; color:#86EFAC; margin-bottom:10px; }
.fc-tip    { background:#110D00; border:1px solid #D9770644; border-radius:8px; padding:9px 13px; font-size:12px; color:#FCD34D; }

/* ── Word ── */
.word-hero { background:linear-gradient(135deg,#1E1B4B,#2E1065); border-radius:14px; padding:20px; color:white; margin-bottom:14px; text-align:center; }
.word-title{ font-size:26px; font-weight:800; }
.word-type { background:rgba(255,255,255,.12); border-radius:20px; padding:3px 13px; font-size:12px; display:inline-block; }
.meaning-box{ background:#0B0D14; border:1px solid #1E2130; border-radius:10px; padding:14px; margin:8px 0; color:#D1D5DB; }
.syn-tag { display:inline-block; background:#1E1B4B; color:#A5B4FC; border-radius:6px; padding:3px 10px; font-size:12px; margin:3px; border:1px solid #4338CA44; }
.ant-tag { display:inline-block; background:#1F0808; color:#FCA5A5; border-radius:6px; padding:3px 10px; font-size:12px; margin:3px; border:1px solid #DC262644; }

/* ── News ── */
.news-card    { background:#13161F; border:1px solid #1E2130; border-radius:12px; padding:14px; margin-bottom:10px; }
.news-title   { font-size:14px; font-weight:700; color:#E2E4EE; margin-bottom:4px; line-height:1.4; font-family:'Sora',sans-serif; }
.news-meta    { font-size:11px; color:#374151; margin-bottom:6px; }
.news-summary { font-size:13px; color:#9CA3AF; line-height:1.6; }
.article-full { background:#13161F; border-radius:14px; padding:24px 28px; border:1px solid #1E2130; font-size:15px; color:#D1D5DB; line-height:1.9; }

/* ── Monthly assessment ── */
.monthly-locked { background:linear-gradient(135deg,#1C1100,#130C00); border:1px solid #D9770644; border-radius:16px; padding:28px; text-align:center; margin-bottom:18px; }
.monthly-open   { background:linear-gradient(135deg,#021208,#031A0F); border:1px solid #16A34A44; border-radius:16px; padding:28px; text-align:center; margin-bottom:18px; }
.attempt-row    { background:#0B0D14; border:1px solid #1E2130; border-radius:10px; padding:12px 16px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; }

/* ── Schedule ── */
.weak-pill   { background:#1F0808; color:#FCA5A5; border:1px solid #DC262644; border-radius:20px; padding:4px 11px; font-size:12px; margin:3px; display:inline-block; }
.strong-pill { background:#021208; color:#86EFAC; border:1px solid #16A34A44; border-radius:20px; padding:4px 11px; font-size:12px; margin:3px; display:inline-block; }

/* ── Streamlit overrides ── */
.stButton > button {
    background:linear-gradient(135deg,#4338CA,#6D28D9) !important;
    color:white !important; border:none !important;
    border-radius:9px !important; font-weight:600 !important;
    font-family:'DM Sans',sans-serif !important; transition:all .15s !important;
}
.stButton > button:hover { transform:translateY(-1px) !important; box-shadow:0 4px 16px rgba(99,102,241,.35) !important; }
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea,
.stNumberInput > div > div > input {
    background:#0B0D14 !important; border:1px solid #1E2130 !important;
    border-radius:9px !important; color:#E2E4EE !important;
}
.stSelectbox > div > div { background:#0B0D14 !important; border:1px solid #1E2130 !important; border-radius:9px !important; color:#E2E4EE !important; }
.stSlider > div { color:#D1D5DB !important; }
.stRadio > div > div > label { color:#D1D5DB !important; }
.stCheckbox > div > div > label { color:#D1D5DB !important; }
hr { border-color:#1E2130 !important; }
.stSpinner > div { border-top-color:#6D28D9 !important; }
div[data-testid="stAlert"] { border-radius:9px !important; }
.stMetric > div { background:#13161F !important; border-radius:12px !important; padding:12px !important; border:1px solid #1E2130 !important; }
.stMetric label { color:#4B5563 !important; }
.stDateInput > div > div > input { background:#0B0D14 !important; border:1px solid #1E2130 !important; border-radius:9px !important; color:#E2E4EE !important; }
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def check_backend_health():
    """Quick check if backend is running. Called once at app startup."""
    try:
        r = requests.get(f"{API}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

def api_post(ep, payload, timeout=60):
    try:
        r = requests.post(f"{API}{ep}", json=payload, timeout=timeout)
        r.raise_for_status(); return r.json(), None
    except requests.exceptions.ConnectionError as e:
        err = (
            f"🚨 **Backend is not running!**\n\n"
            f"Connection failed to: {API}\n\n"
            f"**Fix:**\n"
            f"1. Open a terminal in `backend/` folder\n"
            f"2. Run: `python startup_check.py`\n"
            f"3. Wait for 'Listening on: http://0.0.0.0:8000'\n"
            f"4. Refresh this page\n\n"
            f"See `BACKEND_STARTUP_GUIDE.md` for more help."
        )
        return None, err
    except requests.exceptions.HTTPError as e:
        try: detail = e.response.json().get("detail", str(e))
        except: detail = str(e)
        return None, detail
    except Exception as e:
        return None, str(e)

def api_get(ep, params=None, timeout=30):
    try:
        r = requests.get(f"{API}{ep}", params=params or {}, timeout=timeout)
        r.raise_for_status(); return r.json(), None
    except requests.exceptions.ConnectionError as e:
        err = (
            f"🚨 **Backend is not running!**\n\n"
            f"Connection failed to: {API}\n\n"
            f"**Fix:**\n"
            f"1. Open a terminal in `backend/` folder\n"
            f"2. Run: `python startup_check.py`\n"
            f"3. Wait for 'Listening on: http://0.0.0.0:8000'\n"
            f"4. Refresh this page\n\n"
            f"See `BACKEND_STARTUP_GUIDE.md` for more help."
        )
        return None, err
    except Exception as e:
        return None, str(e)

def api_put(ep, payload, timeout=30):
    try:
        r = requests.put(f"{API}{ep}", json=payload, timeout=timeout)
        r.raise_for_status(); return r.json(), None
    except requests.exceptions.ConnectionError as e:
        err = (
            f"🚨 **Backend is not running!**\n\n"
            f"Connection failed to: {API}\n\n"
            f"**Fix:**\n"
            f"1. Open a terminal in `backend/` folder\n"
            f"2. Run: `python startup_check.py`\n"
            f"3. Wait for 'Listening on: http://0.0.0.0:8000'\n"
            f"4. Refresh this page\n\n"
            f"See `BACKEND_STARTUP_GUIDE.md` for more help."
        )
        return None, err
    except Exception as e:
        return None, str(e)

def grade_color(g):
    return {"A+":"#059669","A":"#10B981","B":"#3B82F6","C":"#F59E0B","D":"#F97316","F":"#EF4444"}.get(g,"#6B7280")

def score_color(s):
    return "#10B981" if s >= 70 else "#F59E0B" if s >= 45 else "#EF4444"

def compute_num_questions(content):
    w = len(content.split())
    return 5 if w<300 else 7 if w<600 else 10 if w<1000 else 12

def difficulty_split(n):
    easy=max(1,math.ceil(n*.3)); hard=max(1,math.floor(n*.25)); medium=n-easy-hard
    return easy, medium, hard

def monday_of(d=None):
    d = d or date.today()
    return d - timedelta(days=d.weekday())

def conf_color(c):
    return {1:"#EF4444",2:"#F97316",3:"#F59E0B",4:"#10B981",5:"#059669"}.get(int(c),"#6B7280")

def render_question_text(qt):
    pm = _re.search(r'\[PASSAGE\](.*?)\[/PASSAGE\](.*)', qt, _re.DOTALL|_re.IGNORECASE)
    if pm:
        passage = pm.group(1).strip()
        question = pm.group(2).strip().lstrip('\n').strip()
        st.markdown(f"""
        <div style="background:#0B0D14;border:1px solid #4338CA44;border-left:4px solid #818CF8;
                    border-radius:0 12px 12px 0;padding:14px 18px;margin-bottom:12px;">
            <div style="font-size:10px;font-weight:700;color:#818CF8;text-transform:uppercase;
                        letter-spacing:.08em;margin-bottom:8px;">📖 Read the Passage</div>
            <div style="font-size:14px;color:#CBD5E1;line-height:1.9;font-style:italic;">{passage}</div>
        </div>
        <div style="font-size:15px;font-weight:600;color:#E2E4EE;line-height:1.5;margin-bottom:10px;">{question}</div>
        """, unsafe_allow_html=True)
        return
    if '\n' in qt:
        lines = [l for l in qt.split('\n') if l.strip()]
        st.markdown(f'<div style="font-size:15px;font-weight:600;color:#E2E4EE;line-height:1.5;margin-bottom:8px;">{lines[0]}</div>', unsafe_allow_html=True)
        if len(lines)>1:
            st.markdown("".join(f'<div style="background:#0B0D14;border:1px solid #1E2130;border-radius:7px;padding:8px 13px;margin-bottom:5px;font-size:14px;color:#D1D5DB;">{l}</div>' for l in lines[1:]), unsafe_allow_html=True)
        return
    st.markdown(f'<div style="font-size:15px;font-weight:600;color:#E2E4EE;line-height:1.5;margin-bottom:10px;">{qt}</div>', unsafe_allow_html=True)

SUBJECT_COLORS = {
    "Quantitative Ability":      ("🔢","#818CF8","#1A1730"),
    "Logical Reasoning":         ("🧩","#A78BFA","#1A1030"),
    "Verbal Ability":            ("📝","#38BDF8","#0A1C2A"),
    "Data Interpretation":       ("📊","#34D399","#041A0F"),
    "General Knowledge (IPMAT)": ("🌍","#FBBF24","#1C1000"),
    "English Language (CLAT)":   ("🔤","#06B6D4","#051B1F"),
    "Current Affairs & GK (CLAT)": ("🗺️","#F59E0B","#1A0F00"),
    "Logical Reasoning (CLAT)":  ("🧠","#A78BFA","#1A1030"),
    "Legal Reasoning (CLAT)":    ("⚖️","#EF4444","#1E0A0A"),
    "Quantitative Techniques (CLAT)": ("🔢","#8B5CF6","#1A0F2E"),
}
DIFF_CLASS = {"Easy":"diff-easy","Medium":"diff-medium","Hard":"diff-hard"}
SKILL_BADGE = {"comprehension":"b-blue","vocabulary":"b-purple","inference":"b-yellow","main idea":"b-green","critical thinking":"b-red"}
INTENT_EMOJI = {"Explanation":"💡","Example":"🔍","Doubt Clarification":"❓","Revision":"📖"}

# ══════════════════════════════════════════════════════════════════════════════
# SESSION DEFAULTS
# ══════════════════════════════════════════════════════════════════════════════
DEFAULTS = {
    "student": None, "page": "dashboard",
    "ask_result": None, "ask_error": None, "ask_query": "", "ask_cache_hit": None, "ask_entry_id": None,
    "kb_list": None, "kb_search": "", "kb_page": 0,
    "news_data": None, "news_error": None,
    "reading_article": None, "reader_word_result": None,
    "word_result": None, "word_error": None, "word_input": "",
    "test_data": None, "test_answers": {}, "test_result": None, "test_article": None,
    "fc_topics": None, "fc_subject": None, "fc_category": None,
    "fc_topic": None, "fc_cards": None, "fc_card_idx": 0, "fc_flipped": False,
    "dashboard_data": None,
    "assessment_status": None, "assessment_data": None,
    "assessment_result": None, "assessment_answers": {},
    "exam_test_data": None, "exam_test_result": None, "exam_test_answers": {},
    "exam_subject": None, "exam_topic": None, "exam_diff": "Intermediate",
    "chosen_exam_for_test": None, "syllabus_data": None,
    # tracker
    "tracker_summary": None,
    "tracker_week": monday_of().strftime("%Y-%m-%d"),
    "tracker_log": None,
    "tracker_topics": [],
    # schedule
    "schedule_data": None,
    "sched_edit_week": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# AUTH SCREEN
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state["student"]:
    _c = st.columns([1,1.6,1])[1]
    with _c:
        st.markdown("""
        <div style="text-align:center;padding:48px 0 28px;">
            <div style="font-size:48px;">🎓</div>
            <div style="font-size:30px;font-weight:800;font-family:'Sora',sans-serif;
                        background:linear-gradient(135deg,#818CF8,#C084FC);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        margin:8px 0 4px;">StudentAssist</div>
            <div style="font-size:13px;color:#4B5563;">Adaptive CAT, IPMAT & CLAT preparation</div>
        </div>""", unsafe_allow_html=True)

        mode = st.session_state.get("auth_mode","login")
        ac1,ac2 = st.columns(2)
        with ac1:
            if st.button("🔑 Login", use_container_width=True, key="m_login"):
                st.session_state["auth_mode"]="login"; st.rerun()
        with ac2:
            if st.button("✨ Register", use_container_width=True, key="m_reg"):
                st.session_state["auth_mode"]="register"; st.rerun()

        st.markdown('<div class="card" style="margin-top:16px;">', unsafe_allow_html=True)
        if mode=="login":
            st.markdown('<div style="font-size:17px;font-weight:700;font-family:\'Sora\',sans-serif;margin-bottom:14px;">Welcome back 👋</div>', unsafe_allow_html=True)
            email = st.text_input("Email", key="li_email", placeholder="you@example.com")
            pwd   = st.text_input("Password", type="password", key="li_pwd")
            if st.button("🚀 Login", type="primary", use_container_width=True):
                if email.strip() and pwd.strip():
                    with st.spinner("Logging in..."):
                        data,err = api_post("/login",{"email":email.strip(),"password":pwd.strip()})
                    if err: st.markdown(f'<div class="errorbox">❌ {err}</div>', unsafe_allow_html=True)
                    else:
                        st.session_state["student"]=data["student"]
                        st.session_state["page"]="dashboard"
                        st.rerun()
                else: st.warning("Fill in all fields.")
        else:
            st.markdown('<div style="font-size:17px;font-weight:700;font-family:\'Sora\',sans-serif;margin-bottom:14px;">Create account ✨</div>', unsafe_allow_html=True)
            rname  = st.text_input("Full Name", key="rg_name")
            remail = st.text_input("Email", key="rg_email")
            rpwd   = st.text_input("Password", type="password", key="rg_pwd")
            st.markdown('<div style="font-size:12px;color:#6B7280;margin:10px 0 6px;">Preparing for:</div>', unsafe_allow_html=True)
            rc1,rc2,rc3 = st.columns(3)
            with rc1:
                if st.button("📘 CAT",  use_container_width=True, key="pk_cat"):
                    st.session_state["reg_exam"]="CAT"; st.rerun()
            with rc2:
                if st.button("📗 IPMAT",use_container_width=True, key="pk_ipm"):
                    st.session_state["reg_exam"]="IPMAT"; st.rerun()
            with rc3:
                if st.button("📕 CLAT", use_container_width=True, key="pk_clat"):
                    st.session_state["reg_exam"]="CLAT"; st.rerun()
            exam_c = st.session_state.get("reg_exam","CAT")
            st.markdown(f'<div class="successbox" style="margin:6px 0;">✅ Selected: <b>{exam_c}</b></div>', unsafe_allow_html=True)
            if st.button("✨ Create Account", type="primary", use_container_width=True):
                if rname.strip() and remail.strip() and rpwd.strip():
                    with st.spinner("Creating account..."):
                        data,err=api_post("/register",{"name":rname.strip(),"email":remail.strip(),"password":rpwd.strip(),"exam_target":exam_c})
                    if err: st.markdown(f'<div class="errorbox">❌ {err}</div>', unsafe_allow_html=True)
                    else:
                        st.session_state["student"]=data["student"]
                        st.session_state["page"]="dashboard"
                        st.rerun()
                else: st.warning("Fill in all fields.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════
student    = st.session_state["student"]
exam_target= student.get("exam_target","CAT")
if not st.session_state.get("chosen_exam_for_test"):
    st.session_state["chosen_exam_for_test"] = exam_target

with st.sidebar:
    st.markdown(f"""
    <div style="padding:20px 16px 14px;border-bottom:1px solid #1E2130;margin-bottom:10px;">
        <div style="font-size:20px;font-weight:800;font-family:'Sora',sans-serif;
                    background:linear-gradient(135deg,#818CF8,#C084FC);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">🎓 StudentAssist</div>
        <div style="font-size:12px;color:#4B5563;margin-top:4px;">
            {student['name'].split()[0]} &nbsp;·&nbsp;
            <span style="color:#A5B4FC;font-weight:600;">{exam_target}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    NAV = [
        ("dashboard",  "📊", "Dashboard"),
        ("assessment", "📋", "Monthly Assessment"),
        ("tracker",    "📅", "Weekly Tracker"),
        ("schedule",   "🗓️", "Prep Schedule"),
        ("exam_tests", "🏆", "Mock Tests"),
        ("flashcards", "🃏", "Flashcards"),
        ("ask",        "🤖", "Ask AI"),
        ("news",       "📰", "News & Articles"),
        ("word",       "💬", "Word Assistant"),
        ("mock",       "📝", "Article Mock Test"),
    ]

    for page_id, icon, label in NAV:
        is_active = st.session_state["page"] == page_id
        div_cls = "nav-active" if is_active else ""
        st.markdown(f'<div class="{div_cls}">', unsafe_allow_html=True)
        if st.button(f"{icon}  {label}", key=f"nav_{page_id}", use_container_width=True):
            st.session_state["page"] = page_id
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="border-top:1px solid #1E2130;margin:12px 0 8px;"></div>', unsafe_allow_html=True)
    if st.button("🚪  Logout", use_container_width=True, key="nav_logout"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

page = st.session_state["page"]

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":
    st.markdown('<div class="hero-bar"><div style="font-size:22px;font-weight:800;font-family:\'Sora\',sans-serif;">📊 Your Dashboard</div><div style="font-size:13px;opacity:.8;margin-top:4px;">Overview of your preparation progress</div></div>', unsafe_allow_html=True)

    col_r,_ = st.columns([1,5])
    with col_r:
        if st.button("🔄 Refresh"):
            st.session_state["dashboard_data"]=None

    needs_assessment = not student.get("has_taken_assessment",False)
    if needs_assessment:
        st.markdown("""
        <div class="card" style="text-align:center;padding:40px;">
            <div style="font-size:40px;margin-bottom:12px;">📋</div>
            <div style="font-size:17px;font-weight:700;font-family:'Sora',sans-serif;margin-bottom:8px;">Complete Your Monthly Assessment First</div>
            <div style="font-size:13px;color:#4B5563;">Go to <b>📋 Monthly Assessment</b> in the sidebar to get started.</div>
        </div>""", unsafe_allow_html=True)
    else:
        if not st.session_state.get("dashboard_data"):
            with st.spinner("Loading dashboard..."):
                data,err = api_get(f"/dashboard/{student['id']}")
            if err: st.error(f"❌ {err}")
            else: st.session_state["dashboard_data"]=data

        dash = st.session_state.get("dashboard_data") or {}
        overall  = dash.get("overall_score") or 0
        diff_lvl = dash.get("difficulty_level") or "—"
        total_t  = dash.get("total_tests_taken",0)
        avg_sc   = dash.get("overall_avg_score",0)

        c1,c2,c3,c4 = st.columns(4)
        for col,num,label,color in [
            (c1,f"{overall:.0f}%","Assessment Score",score_color(overall)),
            (c2,diff_lvl,"Current Level","#818CF8"),
            (c3,str(total_t),"Tests Taken","#38BDF8"),
            (c4,f"{avg_sc:.0f}%","Avg Mock Score",score_color(avg_sc)),
        ]:
            with col:
                st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:{color};">{num}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        d1,d2 = st.columns(2, gap="medium")

        with d1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="sec-title" style="font-size:15px;font-weight:700;margin-bottom:10px;color:#FCA5A5;">⚠️ Weak Topics</div>', unsafe_allow_html=True)
            for w in (dash.get("weak_topics") or []): st.markdown(f'<span class="weak-pill">📍 {w}</span>', unsafe_allow_html=True)
            if not dash.get("weak_topics"): st.markdown('<span style="color:#4B5563;font-size:13px;">None identified yet</span>', unsafe_allow_html=True)
            st.markdown('<div style="height:12px;"></div><div class="sec-title" style="font-size:15px;font-weight:700;margin-bottom:10px;color:#86EFAC;">💪 Strengths</div>', unsafe_allow_html=True)
            for s in (dash.get("strong_topics") or []): st.markdown(f'<span class="strong-pill">✅ {s}</span>', unsafe_allow_html=True)
            if not dash.get("strong_topics"): st.markdown('<span style="color:#4B5563;font-size:13px;">Keep practicing!</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="font-size:15px;font-weight:700;margin-bottom:12px;">📊 Section Performance</div>', unsafe_allow_html=True)
            for sec,score in (dash.get("section_scores") or {}).items():
                sc=score_color(score); short=sec.split("(")[0].strip()
                st.markdown(f'<div style="margin-bottom:10px;"><div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;"><span style="color:#D1D5DB;">{short}</span><span style="color:{sc};font-weight:700;">{score}%</span></div><div class="skill-bar-bg"><div style="background:{sc};height:8px;width:{score}%;border-radius:6px;"></div></div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with d2:
            alp = dash.get("adaptive_learning_path") or {}
            if alp:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:15px;font-weight:700;margin-bottom:10px;">🗺️ Adaptive Learning Path <span class="badge b-purple">{alp.get("difficulty_level","")}</span></div>', unsafe_allow_html=True)
                if alp.get("motivational_tip"): st.markdown(f'<div class="tipbox">✨ {alp["motivational_tip"]}</div>', unsafe_allow_html=True)
                for i,step in enumerate(alp.get("suggested_steps",[]),1):
                    st.markdown(f'<div class="step"><div class="stepn">{i}</div><div style="font-size:13px;color:#D1D5DB;padding-top:2px;line-height:1.6;">{step}</div></div>', unsafe_allow_html=True)
                if alp.get("daily_goal"): st.markdown(f'<div class="successbox" style="margin-top:8px;">🎯 <b>Daily Goal:</b> {alp["daily_goal"]}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="font-size:15px;font-weight:700;margin-bottom:10px;">🕐 Recent Mock Tests</div>', unsafe_allow_html=True)
            recent = dash.get("recent_mock_tests") or []
            if recent:
                for t in recent[:5]:
                    sc=score_color(t.get("score",0)); gc=grade_color(t.get("grade",""))
                    st.markdown(f'<div class="attempt-row"><div><div style="font-size:13px;font-weight:600;color:#D1D5DB;">{t.get("topic","")}</div><div style="font-size:11px;color:#4B5563;">{t.get("subject","").split("(")[0].strip()}</div></div><div style="text-align:right;"><div style="font-size:16px;font-weight:800;font-family:\'Sora\',sans-serif;color:{sc};">{t.get("score",0):.0f}%</div><div style="background:{gc};color:white;border-radius:5px;padding:1px 7px;font-size:11px;font-weight:700;display:inline-block;">{t.get("grade","")}</div></div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="font-size:13px;color:#4B5563;text-align:center;padding:10px;">No tests yet. Try <b>🏆 Mock Tests</b>!</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MONTHLY ASSESSMENT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "assessment":
    st.markdown('<div class="hero-bar"><div style="font-size:22px;font-weight:800;font-family:\'Sora\',sans-serif;">📋 Monthly Assessment</div><div style="font-size:13px;opacity:.8;margin-top:4px;">Track your progress every month • Results shape your learning path</div></div>', unsafe_allow_html=True)

    # Always fetch fresh status
    if not st.session_state.get("assessment_status"):
        status,err = api_get(f"/assessment-status/{student['id']}")
        if not err: st.session_state["assessment_status"]=status

    status = st.session_state.get("assessment_status") or {}
    can_take       = status.get("can_take", not student.get("has_taken_assessment",False))
    days_rem       = status.get("days_remaining",0)
    last_attempt   = status.get("last_attempt")
    attempt_number = status.get("attempt_number",1)
    history        = status.get("history",[])

    aresult = st.session_state.get("assessment_result")
    adata   = st.session_state.get("assessment_data")

    if aresult:
        # ── Show results ──────────────────────────────────────────────────
        pct=aresult.get("percentage",0); grade=aresult.get("grade",""); gc=grade_color(grade); sc=score_color(pct)
        st.markdown(f"""
        <div class="score-hero">
            <div style="font-size:11px;opacity:.7;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">
                Attempt #{attempt_number-1} Complete ✅ · {exam_target}
            </div>
            <div class="score-num" style="color:{sc};">{pct}<span style="font-size:26px;opacity:.5;">%</span></div>
            <div style="font-size:14px;margin:8px 0;opacity:.8;">{aresult.get('total_score',0):.0f} correct answers</div>
            <div style="display:inline-flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:8px;">
                <div style="background:{gc};padding:4px 20px;border-radius:20px;font-weight:800;font-size:16px;font-family:'Sora',sans-serif;">Grade: {grade}</div>
                <div style="background:rgba(255,255,255,.1);padding:4px 18px;border-radius:20px;font-size:13px;">{aresult.get("difficulty_level","")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f'<div class="successbox">✨ {aresult.get("message","")}</div>', unsafe_allow_html=True)
        r1,r2=st.columns(2)
        with r1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="font-size:14px;font-weight:700;color:#FCA5A5;margin-bottom:8px;">⚠️ Focus Areas</div>', unsafe_allow_html=True)
            for w in (aresult.get("weak_topics") or []): st.markdown(f'<span class="weak-pill">📍 {w}</span>', unsafe_allow_html=True)
            if not aresult.get("weak_topics"): st.markdown('<span style="color:#4B5563;font-size:13px;">No weak areas — great start!</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with r2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="font-size:14px;font-weight:700;color:#86EFAC;margin-bottom:8px;">💪 Strengths</div>', unsafe_allow_html=True)
            for s in (aresult.get("strong_topics") or []): st.markdown(f'<span class="strong-pill">✅ {s}</span>', unsafe_allow_html=True)
            if not aresult.get("strong_topics"): st.markdown('<span style="color:#4B5563;font-size:13px;">Keep practicing!</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:14px;font-weight:700;margin-bottom:10px;">📊 Section-wise</div>', unsafe_allow_html=True)
        for sec,score in (aresult.get("section_scores") or {}).items():
            sc2=score_color(score); short=sec.split("(")[0].strip()
            st.markdown(f'<div style="margin-bottom:10px;"><div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;"><span style="color:#D1D5DB;">{short}</span><span style="color:{sc2};font-weight:700;">{score}%</span></div><div class="skill-bar-bg"><div style="background:{sc2};height:8px;width:{score}%;border-radius:6px;"></div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="tipbox">🔄 Next assessment unlocks in <b>30 days</b>. Use this time to focus on your weak topics!</div>', unsafe_allow_html=True)

    elif adata:
        # ── Test in progress ───────────────────────────────────────────────
        questions = adata.get("questions",[])
        answers   = st.session_state.get("assessment_answers",{})
        total_q   = len(questions)
        answered  = sum(1 for a in answers.values() if a)
        pct_done  = int(answered/total_q*100) if total_q else 0

        st.markdown(f"""
        <div class="accent-bar">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-size:14px;font-weight:700;color:#E2E4EE;">{adata.get('description','')}</div>
                    <div style="font-size:12px;color:#4B5563;margin-top:3px;">⏱️ {adata.get('time_limit_minutes',30)} min · Attempt #{attempt_number}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:22px;font-weight:800;font-family:'Sora',sans-serif;color:#A5B4FC;">{answered}/{total_q}</div>
                    <div style="font-size:11px;color:#4B5563;">answered</div>
                </div>
            </div>
            <div style="margin-top:10px;"><div class="progress-wrap"><div style="background:linear-gradient(135deg,#4338CA,#6D28D9);height:10px;width:{pct_done}%;border-radius:8px;"></div></div></div>
        </div>
        """, unsafe_allow_html=True)

        sections={}
        for q in questions:
            sections.setdefault(q.get("section","General"),[]).append(q)

        for sec_name,sec_qs in sections.items():
            short=sec_name.split("(")[0].strip()
            st.markdown(f'<div style="font-size:12px;font-weight:700;color:#A5B4FC;text-transform:uppercase;letter-spacing:.06em;margin:16px 0 8px;">📌 {short}</div>', unsafe_allow_html=True)
            for q in sec_qs:
                qid=str(q["id"])
                st.markdown(f'<div class="question-card"><div class="q-header"><span class="q-num">{qid.upper()}</span><span class="badge b-gray">{q.get("topic","")}</span></div>', unsafe_allow_html=True)
                render_question_text(q.get("question",""))
                st.markdown('</div>', unsafe_allow_html=True)
                sel=st.radio(f"ans_{qid}", options=[f"{k}. {v}" for k,v in q.get("options",{}).items()], key=f"assess_{qid}", label_visibility="collapsed")
                if sel: answers[qid]=sel[0]
                st.markdown("<br>", unsafe_allow_html=True)

        st.session_state["assessment_answers"]=answers
        rem=total_q-len(answers)
        if rem>0: st.info(f"📋 {rem} question(s) remaining.")
        if st.button("✅ Submit Assessment", type="primary", use_container_width=True, disabled=(len(answers)<total_q)):
            with st.spinner("Evaluating..."):
                result,err=api_post("/assessment/submit",{"student_id":student["id"],"exam_target":exam_target,"answers":answers,"questions":questions},timeout=60)
            if err: st.error(f"❌ {err}")
            else:
                st.session_state["assessment_result"]=result
                st.session_state["student"]["has_taken_assessment"]=True
                st.session_state["assessment_status"]=None
                st.session_state["dashboard_data"]=None
                st.rerun()

    else:
        # ── Gating screen ──────────────────────────────────────────────────
        if can_take:
            st.markdown(f"""
            <div class="monthly-open">
                <div style="font-size:36px;margin-bottom:12px;">✅</div>
                <div style="font-size:18px;font-weight:800;font-family:'Sora',sans-serif;color:#86EFAC;margin-bottom:6px;">
                    Assessment Available!
                </div>
                <div style="font-size:13px;color:#4ADE80;margin-bottom:4px;">
                    {"First assessment — establish your baseline!" if attempt_number==1 else f"Attempt #{attempt_number} — see how much you've grown!"}
                </div>
                {"" if not last_attempt else f'<div style="font-size:12px;color:#6B7280;margin-top:6px;">Last taken: {last_attempt}</div>'}
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🚀 Start {'Placement' if attempt_number==1 else 'Monthly'} Assessment", type="primary", use_container_width=True):
                with st.spinner(f"Generating {exam_target} assessment..."):
                    data,err=api_get(f"/assessment/{exam_target}",timeout=120)
                if err: st.error(f"❌ {err}")
                else:
                    st.session_state["assessment_data"]=data
                    st.session_state["assessment_answers"]={}
                    st.session_state["assessment_result"]=None
                    st.rerun()
        else:
            st.markdown(f"""
            <div class="monthly-locked">
                <div style="font-size:36px;margin-bottom:12px;">🔒</div>
                <div style="font-size:18px;font-weight:800;font-family:'Sora',sans-serif;color:#FCD34D;margin-bottom:8px;">
                    Assessment Locked
                </div>
                <div style="font-size:14px;color:#F59E0B;margin-bottom:6px;">
                    Next assessment unlocks in <b>{days_rem} day{"s" if days_rem!=1 else ""}</b>
                </div>
                <div style="font-size:12px;color:#6B7280;">Last taken: {last_attempt}</div>
            </div>
            """, unsafe_allow_html=True)
            # Cooldown progress bar
            pct_wait=int(((30-days_rem)/30)*100)
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:12px;color:#4B5563;margin-bottom:8px;text-transform:uppercase;letter-spacing:.05em;">Cooldown Progress</div>
                <div class="progress-wrap" style="height:14px;margin-bottom:8px;">
                    <div style="background:linear-gradient(135deg,#D97706,#F59E0B);height:14px;width:{pct_wait}%;border-radius:8px;"></div>
                </div>
                <div style="font-size:13px;color:#FCD34D;font-weight:600;">{pct_wait}% of 30 days elapsed</div>
            </div>
            """, unsafe_allow_html=True)

        # Assessment history
        if history:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="font-size:15px;font-weight:700;margin-bottom:12px;">📈 Assessment History</div>', unsafe_allow_html=True)
            for h in history:
                sc=score_color(h.get("percentage",0)); gc=grade_color(h.get("grade",""))
                st.markdown(f"""
                <div class="attempt-row">
                    <div>
                        <div style="font-size:13px;font-weight:700;color:#E2E4EE;">Attempt #{h.get('attempt_number',1)}</div>
                        <div style="font-size:11px;color:#4B5563;">{h.get('taken_at','')} · {h.get('difficulty_level','')}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:18px;font-weight:800;font-family:'Sora',sans-serif;color:{sc};">{h.get('percentage',0):.0f}%</div>
                        <div style="background:{gc};color:white;border-radius:5px;padding:1px 8px;font-size:11px;font-weight:700;display:inline-block;">{h.get('grade','')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: WEEKLY TRACKER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "tracker":
    st.markdown('<div class="hero-bar"><div style="font-size:22px;font-weight:800;font-family:\'Sora\',sans-serif;">📅 Weekly Study Tracker</div><div style="font-size:13px;opacity:.8;margin-top:4px;">Log topics, hours and confidence every week</div></div>', unsafe_allow_html=True)

    tr1,tr2 = st.columns([1.4,1], gap="large")

    with tr1:
        st.subheader("📝 Log This Week")

        # Week selector
        chosen_date = st.date_input("Select any day in the week:", value=date.today(), key="tracker_date_pick")
        week_start_dt = monday_of(chosen_date)
        week_start    = week_start_dt.strftime("%Y-%m-%d")
        week_end_dt   = week_start_dt + timedelta(days=6)
        st.info(f"📅 Week: **{week_start_dt.strftime('%d %b')} – {week_end_dt.strftime('%d %b %Y')}**")

        # Load existing log for this week
        if st.session_state.get("tracker_week") != week_start:
            st.session_state["tracker_week"]  = week_start
            st.session_state["tracker_log"]   = None
            st.session_state["tracker_topics"]= []

        if st.session_state.get("tracker_log") is None:
            log_data,_ = api_get(f"/weekly-log/{student['id']}/{week_start}")
            if log_data and log_data.get("exists"):
                st.session_state["tracker_log"]    = log_data
                st.session_state["tracker_topics"] = log_data.get("topics_covered",[])
            else:
                st.session_state["tracker_log"]    = {}
                st.session_state["tracker_topics"] = []

        topics_list = st.session_state.get("tracker_topics",[])

        st.markdown("---")
        st.markdown("**➕ Add Topic Studied**")
        fa,fb = st.columns([2,1])
        with fa: new_topic   = st.text_input("Topic name",  key="new_topic_name",  placeholder="e.g. Permutation & Combination")
        with fb: new_subject = st.text_input("Subject",     key="new_topic_subj",  placeholder="e.g. QA")
        fc,fd,fe = st.columns(3)
        with fc: new_hours = st.number_input("Hours", 0.5, 12.0, 1.0, 0.5, key="new_topic_hrs")
        with fd: new_conf  = st.selectbox("Confidence (1–5)", [1,2,3,4,5], index=2, key="new_topic_conf")
        with fe: new_notes = st.text_input("Notes", key="new_topic_notes", placeholder="optional")

        if st.button("➕ Add Topic", use_container_width=True, key="add_topic_btn"):
            if new_topic.strip():
                topics_list.append({
                    "topic":      new_topic.strip(),
                    "subject":    new_subject.strip() or "General",
                    "hours":      new_hours,
                    "confidence": new_conf,
                    "notes":      new_notes.strip(),
                })
                st.session_state["tracker_topics"] = topics_list
                st.rerun()

        # Show topics added
        if topics_list:
            st.markdown("---")
            st.caption("TOPICS LOGGED THIS WEEK")
            for i,t in enumerate(topics_list):
                cc=conf_color(t.get("confidence",3))
                col_t,col_del=st.columns([10,1])
                with col_t:
                    st.markdown(f"""
                    <div class="topic-entry">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <span style="font-size:13px;font-weight:600;color:#E2E4EE;">{t['topic']}</span>
                                <span class="badge b-gray" style="margin-left:6px;">{t['subject']}</span>
                            </div>
                            <div>
                                <span style="font-size:12px;color:#A5B4FC;font-weight:600;">{t['hours']}h</span>
                                <span style="background:{cc};color:white;border-radius:20px;padding:2px 8px;font-size:11px;font-weight:700;margin-left:6px;">⭐ {t['confidence']}/5</span>
                            </div>
                        </div>
                        {"" if not t.get("notes") else f'<div style="font-size:12px;color:#4B5563;margin-top:4px;">📝 {t["notes"]}</div>'}
                    </div>
                    """, unsafe_allow_html=True)
                with col_del:
                    if st.button("🗑️", key=f"del_t_{i}", help="Remove"):
                        topics_list.pop(i)
                        st.session_state["tracker_topics"]=topics_list
                        st.rerun()

        st.markdown("---")
        summary_notes = st.text_area("Week summary / notes:", value=(st.session_state.get("tracker_log") or {}).get("summary_notes",""), key="week_summary", placeholder="How did this week go? Any blockers?", height=80)

        total_h = sum(float(t.get("hours",0)) for t in topics_list)
        st.info(f"⏱️ Total study time this week: **{total_h:.1f} hours**")

        if st.button("💾 Save This Week's Log", type="primary", use_container_width=True, key="save_log_btn"):
            with st.spinner("Saving..."):
                res,err=api_post("/weekly-log",{
                    "student_id":     student["id"],
                    "exam_target":    exam_target,
                    "week_start":     week_start,
                    "topics_covered": topics_list,
                    "summary_notes":  summary_notes,
                })
            if err: st.error(f"❌ {err}")
            else:
                st.success("✅ Week logged successfully!")
                st.session_state["tracker_log"]=None
                st.session_state["tracker_summary"]=None

    with tr2:
        if not st.session_state.get("tracker_summary"):
            summ,_ = api_get(f"/weekly-logs/{student['id']}")
            if summ: st.session_state["tracker_summary"]=summ

        summ = st.session_state.get("tracker_summary") or {}

        st.subheader("📊 Your Stats")
        s1,s2=st.columns(2)
        with s1:
            st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#818CF8;">{summ.get("total_weeks_logged",0)}</div><div class="stat-label">Weeks Logged</div></div>', unsafe_allow_html=True)
        with s2:
            st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#38BDF8;">{summ.get("total_hours",0):.0f}h</div><div class="stat-label">Total Hours</div></div>', unsafe_allow_html=True)

        st.caption(f"Avg {summ.get('avg_hours_per_week',0):.1f}h/week · {summ.get('total_topics_covered',0)} topics covered")

        if summ.get("topic_frequency"):
            st.markdown("---")
            st.caption("🔥 MOST STUDIED TOPICS")
            for t,freq in list(summ["topic_frequency"].items())[:6]:
                conf=summ.get("confidence_by_topic",{}).get(t,3)
                cc=conf_color(conf)
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:7px 10px;background:#0B0D14;border-radius:7px;
                            border:1px solid #1E2130;margin-bottom:5px;">
                    <span style="font-size:12px;color:#D1D5DB;">{t}</span>
                    <div>
                        <span style="font-size:11px;color:#6B7280;">{freq}×</span>
                        <span style="background:{cc};color:white;border-radius:20px;padding:1px 7px;font-size:11px;font-weight:700;margin-left:5px;">⭐{conf:.1f}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

        if summ.get("logs"):
            st.markdown("---")
            st.caption("📚 PAST WEEKS")
            for log in summ["logs"][:8]:
                st.markdown(f"""
                <div class="week-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                        <div style="font-size:13px;font-weight:600;color:#E2E4EE;">{log.get('week_label','')}</div>
                        <div>
                            <span style="font-size:12px;color:#A5B4FC;font-weight:600;">{log.get('total_hours',0):.1f}h</span>
                            <span class="badge b-gray" style="margin-left:4px;">{log.get('topics_count',0)} topics</span>
                        </div>
                    </div>
                    {"" if not log.get('summary_notes') else f'<div style="font-size:12px;color:#4B5563;line-height:1.5;">{log["summary_notes"]}</div>'}
                </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PREP SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "schedule":
    st.markdown('<div class="hero-bar"><div style="font-size:22px;font-weight:800;font-family:\'Sora\',sans-serif;">🗓️ Prep Schedule</div><div style="font-size:13px;opacity:.8;margin-top:4px;">Your personalised week-by-week plan · edit anytime</div></div>', unsafe_allow_html=True)

    if not st.session_state.get("schedule_data"):
        sched,_ = api_get(f"/schedule/{student['id']}")
        if sched: st.session_state["schedule_data"]=sched

    sched = st.session_state.get("schedule_data") or {}

    if not sched.get("exists"):
        # ── Create schedule ────────────────────────────────────────────────
        with st.container():
            st.markdown("""
            <div style="background:#13161F;border:1px solid #1E2130;border-radius:14px;
                        padding:20px;margin-bottom:16px;">
                <div style="font-size:16px;font-weight:700;margin-bottom:4px;">📅 Create Your Prep Plan</div>
                <div style="font-size:12px;color:#4B5563;">Choose your duration and we'll generate a week-by-week template you can edit anytime.</div>
            </div>
            """, unsafe_allow_html=True)

            sc1,sc2=st.columns(2)
            with sc1:
                plan_months=st.selectbox("Duration",["3 months","6 months","9 months"],index=1,key="sched_dur")
                months_int=int(plan_months.split()[0])
            with sc2:
                exam_options = ["CAT", "IPMAT", "CLAT"]
                default_idx = exam_options.index(exam_target) if exam_target in exam_options else 0
                sched_exam=st.selectbox("Exam", exam_options, index=default_idx, key="sched_exam")

            sc3,sc4=st.columns(2)
            with sc3:
                start_dt=st.date_input("Start date", value=date.today(), key="sched_start")
            with sc4:
                exam_dt=st.date_input("Target exam date (optional)", value=date.today()+timedelta(weeks=months_int*4), key="sched_exam_dt")

            st.info("💡 A template schedule will be generated based on the standard CAT/IPMAT/CLAT syllabus. You can edit any week after creation.")

            if st.button("🗓️ Generate Schedule", type="primary", use_container_width=True, key="gen_sched"):
                with st.spinner("Building your plan..."):
                    res,err=api_post("/schedule",{
                        "student_id":  student["id"],
                        "exam_target": sched_exam,
                        "plan_months": months_int,
                        "start_date":  start_dt.strftime("%Y-%m-%d"),
                        "exam_date":   exam_dt.strftime("%Y-%m-%d"),
                    })
                if err: st.error(f"❌ {err}")
                else:
                    st.session_state["schedule_data"]={"exists":True,"weeks":res["weeks"],"plan_months":res["plan_months"],"exam_target":sched_exam,"start_date":start_dt.strftime("%Y-%m-%d")}
                    st.success("✅ Schedule created!")
                    st.rerun()

    else:
        # ── Show schedule ──────────────────────────────────────────────────
        weeks      = sched.get("weeks", [])
        total_weeks= len(weeks)
        done_weeks = sum(1 for w in weeks if w.get("completed"))
        today_str  = date.today().strftime("%Y-%m-%d")
        pct_done   = int(done_weeks / total_weeks * 100) if total_weeks else 0

        # ── Stats row ──────────────────────────────────────────────────────
        hs1,hs2,hs3,hs4 = st.columns(4)
        with hs1: st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#818CF8;">{total_weeks}</div><div class="stat-label">Total Weeks</div></div>', unsafe_allow_html=True)
        with hs2: st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#10B981;">{done_weeks}</div><div class="stat-label">Completed</div></div>', unsafe_allow_html=True)
        with hs3: st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#F59E0B;">{total_weeks-done_weeks}</div><div class="stat-label">Remaining</div></div>', unsafe_allow_html=True)
        with hs4: st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#38BDF8;">{pct_done}%</div><div class="stat-label">Progress</div></div>', unsafe_allow_html=True)

        st.markdown(f'<div style="margin:12px 0 4px;"><div style="background:#1A1D27;border-radius:8px;height:12px;overflow:hidden;"><div style="background:linear-gradient(135deg,#059669,#10B981);height:12px;width:{pct_done}%;border-radius:8px;"></div></div></div>', unsafe_allow_html=True)

        rc1, _ = st.columns([1, 4])
        with rc1:
            if st.button("🔄 New Plan", key="regen_sched"):
                st.session_state["schedule_data"] = {"exists": False}
                st.rerun()

        st.markdown("---")

        # ── Week selector + editor side by side ────────────────────────────
        left_col, right_col = st.columns([1, 1.6], gap="large")

        with left_col:
            st.markdown("**📅 All Weeks**")

            # Group by month
            month_groups = {}
            for w in weeks:
                m = (w["week_number"] - 1) // 4 + 1
                month_groups.setdefault(m, []).append(w)

            sel_wn = st.session_state.get("sched_edit_week")

            for month, mweeks in month_groups.items():
                st.caption(f"MONTH {month}")
                for w in mweeks:
                    wn   = w["week_number"]
                    done = w.get("completed", False)
                    focus= w.get("focus", "")
                    wlabel = w.get("week_label", f"Week {wn}")
                    topics = w.get("topics", [])

                    # Determine if current week
                    ws = w.get("week_start", "")
                    try:
                        we = (datetime.strptime(ws, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")
                        is_cur = ws <= today_str <= we
                    except Exception:
                        is_cur = False

                    # Status icon
                    if done:    status = "✅"
                    elif is_cur: status = "▶"
                    else:        status = "○"

                    # Topic preview (safe - no f-string inside f-string)
                    topic_names = [t.get("topic", "") for t in topics]
                    preview = ", ".join(topic_names[:2])
                    if len(topic_names) > 2:
                        preview += f" +{len(topic_names)-2}"

                    btn_label = f"{status} W{wn}  {focus[:22]}"
                    is_selected = sel_wn == wn

                    if is_selected:
                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg,#312E81,#1E1B4B);border:1px solid #6D28D9;
                                    border-radius:9px;padding:9px 13px;margin-bottom:5px;cursor:pointer;">
                            <div style="font-size:12px;font-weight:700;color:#C4B5FD;">{status} Week {wn} · {focus}</div>
                            <div style="font-size:11px;color:#818CF8;margin-top:2px;">{wlabel}</div>
                            <div style="font-size:11px;color:#4B5563;margin-top:2px;">{preview}</div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        border = "#16A34A44" if done else ("#6D28D944" if is_cur else "#1E2130")
                        bg     = "#021208"   if done else ("#0F0D20"   if is_cur else "#0B0D14")
                        tc     = "#86EFAC"   if done else ("#C4B5FD"   if is_cur else "#9CA3AF")
                        st.markdown(f"""
                        <div style="background:{bg};border:1px solid {border};
                                    border-radius:9px;padding:8px 12px;margin-bottom:5px;">
                            <div style="font-size:12px;font-weight:600;color:{tc};">{status} Week {wn} · {focus}</div>
                            <div style="font-size:11px;color:#4B5563;margin-top:1px;">{wlabel}</div>
                        </div>""", unsafe_allow_html=True)
                        if st.button(f"Edit W{wn}", key=f"sel_w_{wn}", use_container_width=True):
                            st.session_state["sched_edit_week"] = wn
                            st.rerun()

        with right_col:
            if not sel_wn:
                st.markdown("""
                <div style="background:#0B0D14;border:1px solid #1E2130;border-radius:14px;
                            padding:60px 20px;text-align:center;">
                    <div style="font-size:36px;margin-bottom:12px;">👈</div>
                    <div style="font-size:14px;color:#4B5563;">Click <b>Edit W#</b> on any week to view and edit it</div>
                </div>""", unsafe_allow_html=True)
            else:
                # Find the selected week object
                sel_week = next((w for w in weeks if w["week_number"] == sel_wn), None)
                if sel_week:
                    wn   = sel_week["week_number"]
                    done = sel_week.get("completed", False)

                    st.markdown(f"**✏️ Editing Week {wn}** — {sel_week.get('week_label','')}")
                    st.markdown("---")

                    # Focus + notes
                    ed1, ed2 = st.columns(2)
                    with ed1:
                        new_focus = st.text_input("Focus theme", value=sel_week.get("focus",""), key=f"ef_{wn}")
                    with ed2:
                        new_notes = st.text_input("Notes / reminder", value=sel_week.get("notes",""), key=f"en_{wn}")

                    new_done = st.checkbox("✅ Mark as completed", value=done, key=f"ed_{wn}")

                    # Topics editor — stored in session state so Add/Delete work live
                    tkey = f"edit_topics_{wn}"
                    if tkey not in st.session_state:
                        st.session_state[tkey] = [dict(t) for t in sel_week.get("topics", [])]

                    cur_topics = st.session_state[tkey]

                    st.caption(f"TOPICS ({len(cur_topics)})")
                    for ti, tt in enumerate(cur_topics):
                        tc1, tc2, tc3 = st.columns([3, 2, 1])
                        with tc1:
                            cur_topics[ti]["topic"] = st.text_input(
                                "Topic", value=tt.get("topic",""),
                                key=f"tt_{wn}_{ti}", label_visibility="collapsed",
                                placeholder="Topic name"
                            )
                        with tc2:
                            cur_topics[ti]["subject"] = st.text_input(
                                "Subject", value=tt.get("subject",""),
                                key=f"ts_{wn}_{ti}", label_visibility="collapsed",
                                placeholder="QA / VA / LR"
                            )
                        with tc3:
                            if st.button("🗑️", key=f"td_{wn}_{ti}"):
                                st.session_state[tkey].pop(ti)
                                st.rerun()

                    add_c, save_c = st.columns([1, 2])
                    with add_c:
                        if st.button("➕ Add topic", key=f"tadd_{wn}", use_container_width=True):
                            st.session_state[tkey].append({"subject": "", "topic": ""})
                            st.rerun()
                    with save_c:
                        if st.button(f"💾 Save Week {wn}", type="primary", use_container_width=True, key=f"save_w_{wn}"):
                            final_topics = [t for t in st.session_state[tkey] if t.get("topic","").strip()]
                            with st.spinner("Saving..."):
                                res, err = api_put("/schedule/week", {
                                    "student_id":  student["id"],
                                    "week_number": wn,
                                    "focus":       new_focus,
                                    "topics":      final_topics,
                                    "notes":       new_notes,
                                    "completed":   new_done,
                                })
                            if err:
                                st.error(f"❌ {err}")
                            else:
                                st.success(f"✅ Week {wn} saved!")
                                # Clear topic editor cache and reload schedule
                                if tkey in st.session_state:
                                    del st.session_state[tkey]
                                st.session_state["schedule_data"] = None
                                st.rerun()

                    if st.button("← Back to list", key=f"back_w_{wn}"):
                        st.session_state["sched_edit_week"] = None
                        if tkey in st.session_state:
                            del st.session_state[tkey]
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MOCK TESTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "exam_tests":
    # show a little schedule help if user has a plan
    covered = []
    if not st.session_state.get("schedule_data"):
        sched, _ = api_get(f"/schedule/{student['id']}")
        if sched:
            st.session_state["schedule_data"] = sched
    cur_week_topics = []
    cur_week_start = None
    sched = st.session_state.get("schedule_data", {})
    if sched.get("exists"):
        today_str = date.today().strftime("%Y-%m-%d")
        for w in sched.get("weeks", []):
            ws = w.get("week_start", "")
            if ws:
                try:
                    we = (datetime.strptime(ws, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")
                    if ws <= today_str <= we:
                        cur_week_topics = [t.get("topic", "") for t in w.get("topics", [])]
                        cur_week_start = ws
                        break
                except Exception:
                    pass
    if cur_week_topics:
        st.markdown(f'<div class="tipbox">📝 This week’s scheduled topics: {", ".join(cur_week_topics)}</div>', unsafe_allow_html=True)
        # also fetch log for this week to show what student has already covered
        if cur_week_start:
            log, _ = api_get(f"/weekly-log/{student['id']}/{cur_week_start}")
            if log and log.get("exists"):
                covered = [t.get("topic") for t in log.get("topics_covered", [])]
                if covered:
                    st.markdown(f'<div class="tipbox">✅ Topics you logged this week: {", ".join(covered)}</div>', unsafe_allow_html=True)
    # if user hasn't picked anything yet but we know a covered topic, auto-select it
    if covered and not st.session_state.get("exam_subject"):
        # map topic to subject via syllabus sections
        syl = st.session_state.get("syllabus_data", {}).get("sections", {})
        for t in covered:
            for s, t_list in syl.items():
                if t in t_list:
                    st.session_state["exam_subject"] = s
                    st.session_state["exam_topic"] = t
                    st.rerun()
                    break
            if st.session_state.get("exam_subject"):
                break

    exam_tag_cls = "badge b-blue" if exam_target=="CAT" else ("badge b-purple" if exam_target=="IPMAT" else "badge b-red")
    st.markdown(f'<div class="hero-bar"><div style="font-size:11px;opacity:.7;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;"><span class="{exam_tag_cls}">{exam_target}</span> Adaptive Practice</div><div style="font-size:22px;font-weight:800;font-family:\'Sora\',sans-serif;">Mock Tests</div><div style="font-size:13px;opacity:.8;margin-top:4px;">Topic-focused tests · results saved to dashboard</div></div>', unsafe_allow_html=True)

    exam_res = st.session_state.get("exam_test_result")
    exam_td  = st.session_state.get("exam_test_data")

    if exam_res:
        score=exam_res.get("score",0); grade=exam_res.get("grade",""); gc=grade_color(grade); sc=score_color(score)
        st.markdown(f'<div class="score-hero"><div style="font-size:11px;opacity:.7;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;">{exam_res.get("subject","").split("(")[0].strip()} · {exam_res.get("topic","")}</div><div class="score-num" style="color:{sc};">{score:.0f}<span style="font-size:26px;opacity:.5;">%</span></div><div style="font-size:14px;margin:8px 0;opacity:.8;">{exam_res.get("correct_answers",0)}/{exam_res.get("total_questions",0)} correct</div><div style="background:{gc};display:inline-block;padding:4px 20px;border-radius:20px;font-size:16px;font-weight:800;font-family:\'Sora\',sans-serif;">Grade: {grade}</div></div>', unsafe_allow_html=True)
        if exam_res.get("adaptive_message"): st.markdown(f'<div class="tipbox">🤖 <b>AI Coach:</b> {exam_res["adaptive_message"]}</div>', unsafe_allow_html=True)
        if exam_res.get("next_recommended_topic"): st.markdown(f'<div class="successbox">➡️ <b>Next Recommended:</b> {exam_res["next_recommended_topic"]}</div>', unsafe_allow_html=True)

        st.markdown("### 🔍 Answer Review")
        user_ans=st.session_state.get("exam_test_answers",{})
        for dr in exam_res.get("detailed_results",[]):
            qid=dr.get("question_id",""); ok=dr.get("is_correct",False); icon="✅" if ok else "❌"
            q_obj=next((q for q in (exam_td or {}).get("questions",[]) if q["id"]==qid),{})
            st.markdown(f'<div class="question-card"><div class="q-header"><span>{icon}</span><span class="q-num">{qid.upper()}</span></div>', unsafe_allow_html=True)
            render_question_text(dr.get("question",""))
            for ok2,ov in q_obj.get("options",{}).items():
                ca=dr.get("correct_answer",""); ua=dr.get("user_answer","")
                if ok2==ca: cls,pre="correct-opt","✅ "
                elif ok2==ua and ua!=ca: cls,pre="wrong-opt","❌ "
                else: cls,pre="neutral-opt",""
                st.markdown(f'<div class="{cls}">{pre}<b>{ok2}.</b> {ov}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tipbox" style="margin-top:8px;">💡 {dr.get("explanation","")}</div></div>', unsafe_allow_html=True)

        b1,b2=st.columns(2)
        with b1:
            if st.button("🔄 Retry",use_container_width=True):
                st.session_state["exam_test_data"]=None; st.session_state["exam_test_result"]=None; st.session_state["exam_test_answers"]={}; st.rerun()
        with b2:
            if st.button("🆕 New Topic",use_container_width=True):
                for k in ["exam_test_data","exam_test_result","exam_test_answers","exam_subject","exam_topic"]:
                    st.session_state[k]=None
                st.rerun()

    elif exam_td:
        questions=exam_td.get("questions",[]); answers=st.session_state.get("exam_test_answers",{})
        total_q=len(questions); answered=sum(1 for a in answers.values() if a); pct_done=int(answered/total_q*100) if total_q else 0
        st.markdown(f'<div class="accent-bar"><div style="display:flex;justify-content:space-between;align-items:center;"><div><div style="font-size:15px;font-weight:700;color:#E2E4EE;">{exam_td.get("topic","")}</div><div style="font-size:12px;color:#4B5563;margin-top:2px;">{exam_td.get("subject","").split("(")[0].strip()} · {exam_td.get("difficulty","")} · {exam_td.get("exam_target","")}</div></div><div style="text-align:right;"><div style="font-size:22px;font-weight:800;font-family:\'Sora\',sans-serif;color:#A5B4FC;">{answered}/{total_q}</div></div></div><div style="margin-top:10px;"><div class="progress-wrap"><div style="background:linear-gradient(135deg,#4338CA,#6D28D9);height:10px;width:{pct_done}%;border-radius:8px;"></div></div></div></div>', unsafe_allow_html=True)
        for q in questions:
            qid=str(q["id"])
            st.markdown(f'<div class="question-card"><div class="q-header"><span class="q-num">{qid.upper()}</span><span class="badge b-teal">{q.get("topic","")}</span></div>', unsafe_allow_html=True)
            render_question_text(q.get("question",""))
            st.markdown('</div>', unsafe_allow_html=True)
            sel=st.radio(f"exa_{qid}",options=[f"{k}. {v}" for k,v in q.get("options",{}).items()],key=f"etest_{qid}",label_visibility="collapsed")
            if sel: answers[qid]=sel[0]
            st.markdown("<br>",unsafe_allow_html=True)
        st.session_state["exam_test_answers"]=answers
        rem=total_q-len(answers)
        if rem>0: st.info(f"📋 {rem} question(s) remaining.")
        if st.button("✅ Submit Test",type="primary",use_container_width=True,disabled=(len(answers)<total_q)):
            with st.spinner("Evaluating..."):
                result,err=api_post("/exam-mock-test/evaluate",{"student_id":student["id"],"exam_target":exam_td.get("exam_target"),"subject":exam_td.get("subject"),"topic":exam_td.get("topic"),"difficulty":exam_td.get("difficulty"),"questions":questions,"user_answers":answers},timeout=60)
            if err: st.error(f"❌ {err}")
            else:
                st.session_state["exam_test_result"]=result
                st.session_state["dashboard_data"]=None
                st.rerun()
    else:
        # Load syllabus
        chosen_exam=st.session_state.get("chosen_exam_for_test",exam_target)
        if not st.session_state.get("syllabus_data"):
            with st.spinner("Loading syllabus..."):
                syl,_=api_get(f"/syllabus/{chosen_exam}")
            if syl: st.session_state["syllabus_data"]=syl

        syl=st.session_state.get("syllabus_data") or {}
        sections=syl.get("sections",{})

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:14px;font-weight:700;margin-bottom:10px;">🎯 Choose Topic</div>', unsafe_allow_html=True)
        ec1,ec2,ec3=st.columns([1,1,1])
        with ec1:
            if st.button("📘 CAT",use_container_width=True,key="ch_cat"):
                st.session_state["chosen_exam_for_test"]="CAT"; st.session_state["syllabus_data"]=None; st.session_state["exam_subject"]=None; st.session_state["exam_topic"]=None; st.rerun()
        with ec2:
            if st.button("📗 IPMAT",use_container_width=True,key="ch_ipm"):
                st.session_state["chosen_exam_for_test"]="IPMAT"; st.session_state["syllabus_data"]=None; st.session_state["exam_subject"]=None; st.session_state["exam_topic"]=None; st.rerun()
        with ec3:
            if st.button("📕 CLAT",use_container_width=True,key="ch_clat"):
                st.session_state["chosen_exam_for_test"]="CLAT"; st.session_state["syllabus_data"]=None; st.session_state["exam_subject"]=None; st.session_state["exam_topic"]=None; st.rerun()
        st.markdown(f'<div style="font-size:12px;color:#6B7280;margin:6px 0;">Showing <b style="color:#A5B4FC;">{chosen_exam}</b> syllabus</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if sections:
            left,right=st.columns([1,2],gap="large")
            with left:
                st.markdown('<div style="font-size:12px;font-weight:700;color:#6B7280;text-transform:uppercase;margin-bottom:8px;">Subjects</div>', unsafe_allow_html=True)
                for subj in sections:
                    is_sel=st.session_state.get("exam_subject")==subj
                    if st.button(("✅ " if is_sel else "")+subj.split("(")[0].strip(),key=f"subj_{subj[:20]}",use_container_width=True):
                        st.session_state["exam_subject"]=subj; st.session_state["exam_topic"]=None; st.rerun()
            with right:
                sel_subj=st.session_state.get("exam_subject")
                if not sel_subj:
                    st.markdown('<div style="background:#0B0D14;border:1px solid #1E2130;border-radius:14px;padding:48px;text-align:center;"><div style="font-size:32px;margin-bottom:10px;">👈</div><div style="font-size:14px;color:#4B5563;">Select a subject</div></div>', unsafe_allow_html=True)
                else:
                    topic_list=sections.get(sel_subj,[])
                    st.markdown(f'<div class="accent-bar"><div style="font-size:13px;font-weight:700;color:#A5B4FC;">{sel_subj.split("(")[0].strip()}</div><div style="font-size:11px;color:#4B5563;margin-top:2px;">{len(topic_list)} topics</div></div>', unsafe_allow_html=True)
                    t_cols=st.columns(2); sel_t=st.session_state.get("exam_topic")
                    for i,topic in enumerate(topic_list):
                        icon = ""
                        if topic in covered:
                            icon = "✅ "
                        elif topic in cur_week_topics:
                            icon = "🗓️ "
                        # keep selection checkmark as highest priority
                        if sel_t == topic:
                            icon = "✅ "
                        with t_cols[i%2]:
                            if st.button(icon + topic, key=f"tp_{topic[:24]}_{i}", use_container_width=True):
                                st.session_state["exam_topic"] = topic; st.rerun()
                    if sel_t:
                        st.markdown(f'<div class="successbox" style="margin:10px 0;">📌 <b>{sel_t}</b></div>', unsafe_allow_html=True)
                        d1,d2,d3=st.columns(3)
                        cur_diff=st.session_state.get("exam_diff","Intermediate")
                        with d1:
                            if st.button("🟢 Beginner",use_container_width=True,key="db"): st.session_state["exam_diff"]="Beginner"; st.rerun()
                        with d2:
                            if st.button("🟡 Intermediate",use_container_width=True,key="di"): st.session_state["exam_diff"]="Intermediate"; st.rerun()
                        with d3:
                            if st.button("🔴 Advanced",use_container_width=True,key="da"): st.session_state["exam_diff"]="Advanced"; st.rerun()
                        st.markdown(f'<div style="font-size:12px;color:#9CA3AF;margin:6px 0;">Difficulty: <b style="color:#A5B4FC;">{cur_diff}</b></div>', unsafe_allow_html=True)
                        n_qs=st.slider("Questions",5,20,10,key="exam_nqs")
                        if st.button(f"🚀 Generate {chosen_exam} Test — {sel_t}",type="primary",use_container_width=True,key="gen_ex"):
                            with st.spinner(f"Generating {cur_diff} questions on {sel_t}..."):
                                result,err=api_post("/exam-mock-test/generate",{"student_id":student["id"],"exam_target":chosen_exam,"subject":sel_subj,"topic":sel_t,"difficulty":cur_diff,"num_questions":n_qs},timeout=90)
                            if err: st.error(f"❌ {err}")
                            else:
                                st.session_state["exam_test_data"]=result; st.session_state["exam_test_answers"]={}; st.session_state["exam_test_result"]=None; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: FLASHCARDS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "flashcards":
    st.markdown('<div class="hero-bar"><div style="font-size:22px;font-weight:800;font-family:\'Sora\',sans-serif;">🃏 Flashcards</div><div style="font-size:13px;opacity:.8;margin-top:4px;">AI concept cards for every topic in the syllabus</div></div>', unsafe_allow_html=True)

    if not st.session_state.get("fc_topics"):
        try:
            r=requests.get(f"{API}/flashcards/topics",timeout=10); r.raise_for_status()
            st.session_state["fc_topics"]=r.json().get("topics",{})
        except Exception as e:
            st.error(f"❌ Could not load topics: {e}")

    topics_tree=st.session_state.get("fc_topics") or {}
    if not topics_tree:
        st.info("Topics unavailable — ensure backend is running.")
    else:
        # display schedule hint on flashcards page as well
        covered = []
        if not st.session_state.get("schedule_data"):
            sched,_ = api_get(f"/schedule/{student['id']}")
            if sched:
                st.session_state["schedule_data"] = sched
        cur_week_topics = []
        cur_week_start = None
        sched = st.session_state.get("schedule_data", {})
        if sched.get("exists"):
            today_str = date.today().strftime("%Y-%m-%d")
            for w in sched.get("weeks", []):
                ws = w.get("week_start", "")
                if ws:
                    try:
                        we = (datetime.strptime(ws, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")
                        if ws <= today_str <= we:
                            cur_week_topics = [t.get("topic", "") for t in w.get("topics", [])]
                            cur_week_start = ws
                            break
                    except Exception:
                        pass
        if cur_week_topics:
            st.markdown(f'<div class="tipbox">📝 This week’s scheduled topics: {", ".join(cur_week_topics)}</div>', unsafe_allow_html=True)
            if cur_week_start:
                log, _ = api_get(f"/weekly-log/{student['id']}/{cur_week_start}")
                if log and log.get("exists"):
                    covered = [t.get("topic") for t in log.get("topics_covered", [])]
                    if covered:
                        st.markdown(f'<div class="tipbox">✅ Topics you logged this week: {", ".join(covered)}</div>', unsafe_allow_html=True)
        # auto pick first covered topic if nothing chosen yet
        if covered and not st.session_state.get("fc_subject"):
            syl = st.session_state.get("fc_topics", {})
            for t in covered:
                for s, t_list in syl.items():
                    if t in t_list:
                        st.session_state["fc_subject"] = s
                        st.session_state["fc_topic"] = t
                        st.session_state["fc_cards"] = None
                        st.session_state["fc_card_idx"] = 0
                        st.session_state["fc_flipped"] = False
                        st.rerun()
                        break
                if st.session_state.get("fc_subject"):
                    break
        subjects=list(topics_tree.keys())
        sb_cols=st.columns(len(subjects))
        for i,subj in enumerate(subjects):
            em,col,bg=SUBJECT_COLORS.get(subj,("📚","#818CF8","#1A1730"))
            with sb_cols[i]:
                if st.button(f"{em} {subj.replace(' (IPMAT)','')[:16]}",key=f"fcs_{i}",use_container_width=True):
                    st.session_state["fc_subject"]=subj; st.session_state["fc_category"]=None
                    st.session_state["fc_topic"]=None; st.session_state["fc_cards"]=None
                    st.session_state["fc_card_idx"]=0; st.session_state["fc_flipped"]=False
        st.markdown("---")
        sel_subj=st.session_state.get("fc_subject")
        if not sel_subj:
            st.markdown('<div style="text-align:center;padding:40px;color:#4B5563;">👆 Select a subject to get started</div>', unsafe_allow_html=True)
        else:
            subj_data=topics_tree.get(sel_subj,{}); em,col,bg=SUBJECT_COLORS.get(sel_subj,("📚","#818CF8","#1A1730"))
            fc_left,fc_right=st.columns([1,2],gap="large")
            with fc_left:
                st.markdown(f'<div style="background:{bg};border:1px solid {col}44;border-radius:10px;padding:12px;margin-bottom:10px;"><div style="font-size:13px;font-weight:700;color:#E2E4EE;">{em} {sel_subj}</div></div>', unsafe_allow_html=True)
                for cat,t_list in subj_data.items():
                    st.markdown(f'<div style="font-size:10px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;margin:8px 0 4px;">{cat}</div>', unsafe_allow_html=True)
                    for t in t_list:
                        icon=""
                        if t in covered:
                            icon="✅ "
                        elif t in cur_week_topics:
                            icon="🗓️ "
                        is_s=st.session_state.get("fc_topic")==t
                        if is_s:
                            icon="✅ "
                        if st.button(icon + t,key=f"fct_{t[:24]}",use_container_width=True):
                            st.session_state["fc_topic"]=t; st.session_state["fc_category"]=cat
                            st.session_state["fc_cards"]=None; st.session_state["fc_card_idx"]=0; st.session_state["fc_flipped"]=False
            with fc_right:
                sel_t=st.session_state.get("fc_topic")
                if not sel_t:
                    st.markdown(f'<div style="background:{bg};border:1px solid {col}44;border-radius:14px;padding:48px;text-align:center;"><div style="font-size:36px;margin-bottom:10px;">{em}</div><div style="font-size:14px;color:#4B5563;">Pick a topic from the left</div></div>', unsafe_allow_html=True)
                else:
                    cards=st.session_state.get("fc_cards")
                    if cards is None:
                        with st.spinner(f"Generating cards for '{sel_t}'..."):
                            try:
                                resp=requests.post(f"{API}/flashcards/generate",json={"topic":sel_t,"subject":sel_subj,"num_cards":6},timeout=45); resp.raise_for_status()
                                data=resp.json(); st.session_state["fc_cards"]=data.get("cards",[]); st.session_state["fc_card_idx"]=0; st.session_state["fc_flipped"]=False; cards=st.session_state["fc_cards"]
                            except Exception as e:
                                st.error(f"❌ {e}"); cards=[]
                    if cards:
                        idx=st.session_state.get("fc_card_idx",0); flipped=st.session_state.get("fc_flipped",False)
                        total=len(cards); card=cards[idx]; pct_fc=int(((idx+1)/total)*100)

                        st.markdown(f'<div style="background:{bg};border:1px solid {col}44;border-radius:14px;padding:14px 18px;margin-bottom:12px;"><div style="display:flex;justify-content:space-between;align-items:center;"><div><div style="font-size:10px;opacity:.7;text-transform:uppercase;letter-spacing:.05em;">{em} {sel_subj}</div><div style="font-size:16px;font-weight:800;font-family:\'Sora\',sans-serif;margin-top:3px;">{sel_t}</div></div><div style="font-size:24px;font-weight:800;font-family:\'Sora\',sans-serif;color:{col};">{idx+1}<span style="font-size:14px;opacity:.6;">/{total}</span></div></div><div style="margin-top:8px;background:rgba(255,255,255,.1);border-radius:6px;height:6px;overflow:hidden;"><div style="background:{col};height:6px;width:{pct_fc}%;border-radius:6px;"></div></div></div>', unsafe_allow_html=True)

                        if not flipped:
                            front_text=card.get("front","")
                            pm=_re.search(r'\[PASSAGE\](.*?)\[/PASSAGE\](.*)',front_text,_re.DOTALL|_re.IGNORECASE)
                            if pm:
                                passage=pm.group(1).strip(); question=pm.group(2).strip().lstrip('\n').strip()
                                st.markdown(f'<div class="fc-front"><div style="font-size:10px;opacity:.6;text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px;">Card {idx+1} · RC</div><div style="background:rgba(0,0,0,.3);border-left:3px solid #A5B4FC;border-radius:0 7px 7px 0;padding:10px 14px;margin-bottom:12px;font-size:13px;color:#C7D2FE;line-height:1.8;font-style:italic;">{passage}</div><div class="fc-q" style="font-size:15px;">{question}</div></div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="fc-front"><div style="font-size:10px;opacity:.6;text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px;">Card {idx+1} of {total}</div><div class="fc-q">{front_text}</div><div style="margin-top:16px;font-size:11px;opacity:.5;">👆 Click Reveal to flip</div></div>', unsafe_allow_html=True)
                            st.markdown("<br>",unsafe_allow_html=True)
                            if st.button("👁️ Reveal Answer",type="primary",use_container_width=True,key="fc_flip"):
                                st.session_state["fc_flipped"]=True; st.rerun()
                        else:
                            eg_html=f'<div class="fc-example">📌 <b>Example:</b> {card.get("example","")}</div>' if card.get("example") else ""
                            tip_html=f'<div class="fc-tip">💡 <b>Tip:</b> {card.get("tip","")}</div>' if card.get("tip") else ""
                            st.markdown(f'<div class="fc-back"><div style="font-size:10px;font-weight:700;color:#4B5563;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;">Answer</div><div class="fc-answer">{card.get("back","")}</div>{eg_html}{tip_html}</div>', unsafe_allow_html=True)
                            st.markdown("<br>",unsafe_allow_html=True)

                        n1,n2,n3,n4=st.columns(4)
                        with n1:
                            if st.button("⬅️ Prev",use_container_width=True,disabled=(idx==0),key="fc_prev"):
                                st.session_state["fc_card_idx"]=idx-1; st.session_state["fc_flipped"]=False; st.rerun()
                        with n2:
                            if st.button("➡️ Next",use_container_width=True,disabled=(idx==total-1),key="fc_next"):
                                st.session_state["fc_card_idx"]=idx+1; st.session_state["fc_flipped"]=False; st.rerun()
                        with n3:
                            if st.button("🔄 Restart",use_container_width=True,key="fc_restart"):
                                st.session_state["fc_card_idx"]=0; st.session_state["fc_flipped"]=False; st.rerun()
                        with n4:
                            if st.button("🔁 New Set",use_container_width=True,key="fc_regen"):
                                st.session_state["fc_cards"]=None; st.session_state["fc_card_idx"]=0; st.session_state["fc_flipped"]=False; st.rerun()

                        if idx==total-1 and flipped:
                            st.markdown('<div class="successbox" style="text-align:center;margin-top:10px;">🎉 Deck complete! Click <b>🔁 New Set</b> for fresh cards.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ASK AI
# ══════════════════════════════════════════════════════════════════════════════
elif page == "ask":
    st.markdown('<div class="hero-bar"><div style="font-size:22px;font-weight:800;font-family:\'Sora\',sans-serif;">🤖 Ask AI</div><div style="font-size:13px;opacity:.8;margin-top:4px;">Instant answers from Knowledge Base · new answers auto-saved</div></div>', unsafe_allow_html=True)

    SAMPLES=["Explain Percentages with examples.","What is Para Jumble strategy?","How to solve Time and Work problems?","What is CAT exam pattern?","Explain Reading Comprehension approach.","How to solve Data Interpretation sets?"]
    sc=st.columns(3)
    for i,q in enumerate(SAMPLES):
        if sc[i%3].button(q[:38]+("..." if len(q)>38 else ""),key=f"sq{i}",use_container_width=True):
            st.session_state["ask_query"]=q
            st.session_state["ask_result"]=None
            st.session_state["ask_cache_hit"]=None
            st.rerun()

    ask_q = st.text_area("Your question:", value=st.session_state.get("ask_query",""), placeholder="Ask anything about CAT, IPMAT, CLAT concepts, strategies...", height=90, key="ask_query_input")
    prev  = st.text_input("Previously studied topics (optional):", placeholder="e.g. Arithmetic, Percentages")
    go    = st.button("Ask Question", type="primary", use_container_width=True, key="ask_go")

    if go and ask_q.strip():
        st.session_state["ask_query"]     = ask_q.strip()
        st.session_state["ask_result"]    = None
        st.session_state["ask_cache_hit"] = None
        st.session_state["ask_entry_id"]  = None

        # STEP 1: Check Knowledge Base first
        with st.spinner("Checking knowledge base..."):
            kb_hit, kb_err = api_post("/qa/ask", {"question": ask_q.strip(), "student_id": student["id"]})

        if kb_hit and kb_hit.get("from_cache"):
            st.session_state["ask_cache_hit"] = kb_hit
        else:
            # STEP 2: Not in DB — call AI
            with st.spinner("Not in knowledge base — asking AI..."):
                r_data, r_err = api_post("/full-analysis", {
                    "query":           ask_q.strip(),
                    "student_id":      str(student["id"]),
                    "previous_topics": [t.strip() for t in prev.split(",") if t.strip()],
                }, timeout=60)

            if r_err:
                st.session_state["ask_error"]  = r_err
                st.session_state["ask_result"] = None
            else:
                st.session_state["ask_result"] = r_data
                st.session_state["ask_error"]  = None

                # STEP 3: Auto-save AI answer to Knowledge Base
                qa_r   = r_data.get("query_analysis") or {}
                lp_r   = r_data.get("learning_path")  or {}
                parts  = [
                    qa_r.get("explanation",""),
                    lp_r.get("topic_explanation",""),
                    "\n".join(f"{i+1}. {s}" for i,s in enumerate(lp_r.get("recommended_path",[]))),
                ]
                full_answer = "\n\n".join(p for p in parts if p.strip())
                if full_answer.strip():
                    save_res, _ = api_post("/qa/ask", {
                        "question":   ask_q.strip(),
                        "student_id": student["id"],
                        "subject":    "General",
                        "topic":      qa_r.get("topic","General"),
                        "ai_answer":  full_answer.strip(),
                    })
                    if save_res:
                        st.session_state["ask_entry_id"] = save_res.get("entry_id")

    elif go:
        st.warning("Please type a question first.")

    # Render: cache hit
    cache = st.session_state.get("ask_cache_hit")
    if cache:
        score_pct = int(cache.get("match_score",0)*100)
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#021208,#031A0F);border:1px solid #16A34A55;
                    border-radius:14px;padding:14px 20px;margin-bottom:14px;display:flex;align-items:center;gap:12px;">
            <div style="font-size:28px;">⚡</div>
            <div>
                <div style="font-size:13px;font-weight:700;color:#86EFAC;">Found in Knowledge Base — no API call needed</div>
                <div style="font-size:11px;color:#4B5563;margin-top:2px;">Match: <b style="color:#6EE7B7;">{score_pct}%</b> &nbsp;·&nbsp; Subject: <b style="color:#6EE7B7;">{cache.get("subject","General")}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#0D1117;border:1px solid #1E2130;border-radius:12px;padding:18px 22px;margin-bottom:12px;">
            <div style="font-size:11px;font-weight:700;color:#4B5563;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">Matched Question</div>
            <div style="font-size:14px;color:#9CA3AF;font-style:italic;margin-bottom:14px;">"{cache.get("question","")}"</div>
            <div style="font-size:11px;font-weight:700;color:#4B5563;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">Answer</div>
            <div style="font-size:15px;color:#E2E4EE;line-height:1.9;white-space:pre-wrap;">{cache.get("answer","")}</div>
        </div>
        """, unsafe_allow_html=True)

        hcol, _, forcecol = st.columns([1,3,1])
        with hcol:
            if st.button("Helpful", key="helpful_btn", use_container_width=True):
                api_post(f"/qa/{cache['entry_id']}/helpful", {})
                st.success("Thanks!")
        with forcecol:
            if st.button("Ask AI instead", key="force_ai_btn", use_container_width=True):
                st.session_state["ask_cache_hit"] = None
                ask_q2 = st.session_state.get("ask_query","")
                if ask_q2:
                    with st.spinner("Asking AI..."):
                        r_data, r_err = api_post("/full-analysis", {"query": ask_q2, "student_id": str(student["id"]), "previous_topics": []}, timeout=60)
                    if not r_err:
                        st.session_state["ask_result"] = r_data
                st.rerun()

    # Render: full AI result
    if st.session_state.get("ask_error"):
        st.error(f"Error: {st.session_state['ask_error']}")

    if st.session_state.get("ask_result"):
        res     = st.session_state["ask_result"]
        qa_r    = res.get("query_analysis",{})
        lp      = res.get("learning_path",{})
        entry_id= st.session_state.get("ask_entry_id")
        topic   = qa_r.get("topic","")
        intent  = qa_r.get("intent","")
        conf    = int(qa_r.get("confidence",0)*100)
        expl    = qa_r.get("explanation","")
        keywords= qa_r.get("keywords",[])
        topic_ex= lp.get("topic_explanation","")
        steps   = lp.get("recommended_path",[])
        prereqs = lp.get("prerequisites",[])
        nexts   = lp.get("next_topics",[])
        est     = lp.get("estimated_completion","")
        tip     = lp.get("personalized_tip","")
        resources=lp.get("resources",[])
        ie      = INTENT_EMOJI.get(intent,"📚")
        bc      = "#10B981" if conf>70 else "#F59E0B" if conf>40 else "#EF4444"

        if entry_id:
            st.markdown(f'<div class="successbox">Answer automatically saved to Knowledge Base (ID #{entry_id}) — future students get instant answers.</div>', unsafe_allow_html=True)

        c1,c2=st.columns(2,gap="medium")
        with c1:
            expl_html = f'<div class="expbox">💬 {expl}</div>' if expl else ""
            kw_html = "".join(f'<span class="badge b-gray">{k}</span>' for k in keywords)
            conf_bar = f'<div style="flex:1;background:#1A1D27;border-radius:6px;height:7px;overflow:hidden;"><div style="background:{bc};height:7px;width:{conf}%;border-radius:6px;"></div></div>'
            st.markdown(f'''
            <div class="card">
                <div style="font-size:14px;font-weight:700;margin-bottom:10px;">🧠 Query Analysis</div>
                <span class="badge b-blue">{ie} {intent}</span>
                <span class="badge b-purple">📌 {topic}</span>
                <div style="margin:10px 0;">
                    <div style="font-size:11px;color:#4B5563;margin-bottom:4px;">Confidence</div>
                    <div style="display:flex;align-items:center;gap:8px;">
                        {conf_bar}
                        <span style="font-size:12px;font-weight:700;color:{bc};">{conf}%</span>
                    </div>
                </div>
                {expl_html}
                <div style="margin-top:8px;">{kw_html}</div>
            </div>
            ''', unsafe_allow_html=True)
        with c2:
            prereq_html = "".join(f'<span class="badge b-red">{p}</span>' for p in prereqs)
            next_html   = "".join(f'<span class="badge b-green">-> {t}</span>' for t in nexts)
            prereq_sec  = f'<div style="font-size:11px;color:#4B5563;margin:8px 0 4px;">Prerequisites</div>{prereq_html}' if prereqs else ""
            next_sec    = f'<div style="font-size:11px;color:#4B5563;margin:8px 0 4px;">What to Learn Next</div>{next_html}' if nexts else ""
            topicex_sec = f'<div class="meaning-box" style="font-size:13px;line-height:1.8;">{topic_ex}</div>' if topic_ex else ""
            st.markdown(f'''
            <div class="card">
                <div style="font-size:14px;font-weight:700;margin-bottom:10px;">📖 {topic}</div>
                {topicex_sec}
                {prereq_sec}
                {next_sec}
            </div>
            ''', unsafe_allow_html=True)

        if steps:
            steps_html = "".join(f'<div class="step"><div class="stepn">{i}</div><div style="font-size:13px;color:#D1D5DB;padding-top:2px;line-height:1.6;">{s}</div></div>' for i,s in enumerate(steps,1))
            tip_html   = f'<div class="tipbox">{tip}</div>' if tip else ""
            st.markdown(f'''
            <div class="card">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                    <div style="font-size:14px;font-weight:700;">🗺️ Learning Path</div>
                    <span class="badge b-gray">⏱️ {est}</span>
                </div>
                {tip_html}
                {steps_html}
            </div>
            ''', unsafe_allow_html=True)

            rc_cols=st.columns(min(len(resources),3))
            for i,rv in enumerate(resources):
                url=rv.get("url",""); vid_id=url.split("watch?v=")[-1].split("&")[0] if "watch?v=" in url else ""
                thumb=f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg" if vid_id else ""
                with rc_cols[i%3]:
                    img_html=f'<img src="{thumb}" style="width:100%;height:130px;object-fit:cover;">' if thumb else '<div style="height:130px;background:#0B0D14;display:flex;align-items:center;justify-content:center;">🎬</div>'
                    btn_html=f'<a href="{url}" target="_blank" style="background:#DC2626;color:white;padding:4px 12px;border-radius:5px;font-size:12px;font-weight:600;text-decoration:none;">Watch</a>' if url else ""
                    st.markdown(f'<div style="background:#0B0D14;border:1px solid #1E2130;border-radius:10px;overflow:hidden;margin-bottom:8px;">{img_html}<div style="padding:10px;"><div style="font-size:12px;font-weight:700;color:#E2E4EE;margin-bottom:4px;">{rv.get("title","")[:60]}</div><div style="font-size:11px;color:#4B5563;margin-bottom:6px;">{rv.get("description","")[:80]}</div>{btn_html}</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: NEWS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "news":
    CATEGORIES=["editorial","top_stories","india","world","business","technology","education","sports"]
    if st.session_state.get("reading_article"):
        art=st.session_state["reading_article"]; content=art.get("content",art.get("summary","")); title=art.get("title","")
        words=len(content.split()); num_q=compute_num_questions(content); easy,medium,hard=difficulty_split(num_q)
        if st.button("← Back"):
            st.session_state["reading_article"]=None; st.rerun()
        st.markdown(f'<div class="hero-bar"><div style="font-size:10px;opacity:.7;text-transform:uppercase;margin-bottom:5px;">📰 {art.get("source","")} · {art.get("category","").replace("_"," ").title()}</div><div style="font-size:19px;font-weight:800;font-family:\'Sora\',sans-serif;line-height:1.3;">{title}</div></div>', unsafe_allow_html=True)
        read_col,word_col=st.columns([3,1],gap="medium")
        with read_col:
            st.markdown('<div class="article-full">', unsafe_allow_html=True); st.markdown(content); st.markdown('</div>', unsafe_allow_html=True)
        with word_col:
            st.markdown('<div class="card"><div style="font-size:13px;font-weight:700;margin-bottom:8px;">💬 Word Lookup</div>', unsafe_allow_html=True)
            wrd=st.text_input("Word:",key="rw",placeholder="e.g. ephemeral"); ctx=st.text_input("Context:",key="rc_ctx")
            if st.button("🔍 Explain",key="rwb",use_container_width=True):
                if wrd.strip():
                    wr,we=api_post("/word-assist",{"word":wrd.strip(),"sentence_context":ctx.strip()},timeout=30)
                    if we: st.error(we)
                    else: st.session_state["reader_word_result"]=wr
            if st.session_state.get("reader_word_result"):
                wd=st.session_state["reader_word_result"]
                st.markdown(f'<div style="background:linear-gradient(135deg,#1E1B4B,#2E1065);border-radius:8px;padding:10px;color:white;margin:8px 0;"><div style="font-size:16px;font-weight:800;font-family:\'Sora\',sans-serif;">{wd.get("word","").upper()}</div><div style="font-size:11px;opacity:.7;">{wd.get("word_type","")}</div></div>', unsafe_allow_html=True)
                st.markdown(f"**Meaning:** {wd.get('meaning','')}")
                if wd.get("synonyms"): st.markdown(" ".join(f'<span class="syn-tag">{s}</span>' for s in wd["synonyms"][:3]), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="card"><div style="font-size:13px;font-weight:700;margin-bottom:8px;">📝 Test on Article</div>', unsafe_allow_html=True)
            st.markdown(f'<span class="diff-easy">🟢{easy}</span> <span class="diff-medium">🟡{medium}</span> <span class="diff-hard">🔴{hard}</span> = <b>{num_q}q</b>', unsafe_allow_html=True)
            if st.button("🚀 Start Test",type="primary",use_container_width=True,key="rst"):
                with st.spinner(f"Generating {num_q} questions..."):
                    tr,te=api_post("/mock-test/generate",{"article_content":content,"article_title":title,"difficulty":"Mixed","num_questions":num_q},timeout=90)
                if te: st.error(f"❌ {te}")
                else:
                    st.session_state["test_data"]=tr; st.session_state["test_answers"]={}; st.session_state["test_result"]=None; st.session_state["test_article"]=art
                    st.session_state["page"]="mock"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="hero-bar"><div style="font-size:22px;font-weight:800;font-family:\'Sora\',sans-serif;">📰 News & Articles</div><div style="font-size:13px;opacity:.8;margin-top:4px;">Read · study · test yourself</div></div>', unsafe_allow_html=True)
        fc1,fc2=st.columns([2,1])
        with fc1: category=st.selectbox("Category",CATEGORIES,format_func=lambda x:x.replace("_"," ").title())
        with fc2: max_a=st.slider("Articles",3,10,5)
        if st.button("🔄 Load Articles",type="primary",use_container_width=True):
            with st.spinner("Fetching articles (~20s)..."):
                nd,ne=api_get("/news",{"category":category,"max_articles":max_a},timeout=90)
            st.session_state["news_data"]=nd; st.session_state["news_error"]=ne
        if st.session_state.get("news_error"): st.error(f"❌ {st.session_state['news_error']}")
        if st.session_state.get("news_data"):
            articles=st.session_state["news_data"].get("articles",[])
            for idx,art in enumerate(articles):
                cp=art.get("content",art.get("summary","")); words=len(cp.split()); num_q=compute_num_questions(cp); easy,medium,hard=difficulty_split(num_q)
                st.markdown(f'<div class="news-card"><div class="news-title">{art.get("title","")}</div><div class="news-meta">📰 {art.get("source","")} · ~{words} words · <span class="diff-easy">{easy}E</span> <span class="diff-medium">{medium}M</span> <span class="diff-hard">{hard}H</span></div><div class="news-summary">{cp[:180]}{"…" if len(cp)>180 else ""}</div></div>', unsafe_allow_html=True)
                bc1,bc2,bc3=st.columns([2,1,1])
                with bc1:
                    if st.button("📖 Read & Study",key=f"rd_{idx}",use_container_width=True):
                        st.session_state["reading_article"]=art; st.session_state["reader_word_result"]=None; st.rerun()
                with bc2: st.markdown(f'<a href="{art.get("url","#")}" target="_blank" style="display:block;text-align:center;background:#13161F;border:1px solid #1E2130;border-radius:7px;padding:7px;font-size:12px;color:#9CA3AF;text-decoration:none;">🔗 Source</a>', unsafe_allow_html=True)
                with bc3:
                    if st.button("📝 Test",key=f"tt_{idx}",use_container_width=True):
                        nq=compute_num_questions(cp)
                        with st.spinner(f"Generating {nq}q..."):
                            tr,te=api_post("/mock-test/generate",{"article_content":cp,"article_title":art.get("title",""),"difficulty":"Mixed","num_questions":nq},timeout=90)
                        if te: st.error(f"❌ {te}")
                        else:
                            st.session_state["test_data"]=tr; st.session_state["test_answers"]={}; st.session_state["test_result"]=None; st.session_state["test_article"]=art
                            st.session_state["page"]="mock"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: WORD ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "word":
    st.markdown('<div class="hero-bar"><div style="font-size:22px;font-weight:800;font-family:\'Sora\',sans-serif;">💬 Word Assistant</div><div style="font-size:13px;opacity:.8;margin-top:4px;">Meaning · synonyms · antonyms · origin · examples</div></div>', unsafe_allow_html=True)
    SAMPLE_WORDS=["Ephemeral","Ubiquitous","Pragmatic","Ameliorate","Juxtaposition","Perspicacious","Laconic","Equivocal","Vociferous","Benevolent"]
    st.markdown('<div class="card">', unsafe_allow_html=True)
    wc=st.columns(5)
    for i,w in enumerate(SAMPLE_WORDS):
        if wc[i%5].button(w,key=f"sw_{i}",use_container_width=True): st.session_state["word_input"]=w
    word=st.text_input("Enter a word:",value=st.session_state.get("word_input",""),placeholder="e.g. ephemeral",key="word_input")
    ctx=st.text_input("Context sentence (optional):",placeholder='"The ephemeral nature of fame..."')
    look=st.button("🔍 Explain This Word",type="primary",use_container_width=True,key="word_go")
    st.markdown('</div>', unsafe_allow_html=True)

    if look and word.strip():
        with st.spinner(f"Looking up '{word}'..."):
            wd_data,wd_err=api_post("/word-assist",{"word":word.strip(),"sentence_context":ctx.strip()},timeout=30)
        st.session_state["word_result"]=wd_data; st.session_state["word_error"]=wd_err
    elif look: st.warning("Enter a word.")

    if st.session_state.get("word_error"): st.error(f"❌ {st.session_state['word_error']}")
    if st.session_state.get("word_result"):
        wd=st.session_state["word_result"]
        st.markdown(f'<div class="word-hero"><div class="word-title">{wd.get("word","").upper()}</div><span class="word-type">{wd.get("word_type","").capitalize()}</span></div>', unsafe_allow_html=True)
        c1,c2=st.columns([3,2],gap="medium")
        with c1:
            st.markdown('<div class="card"><div style="font-size:14px;font-weight:700;margin-bottom:10px;">📖 Meaning</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="meaning-box"><b>Dictionary:</b> {wd.get("meaning","")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="expbox">🧒 <b>Simply:</b> {wd.get("simple_explanation","")}</div>', unsafe_allow_html=True)
            if wd.get("origin"): st.markdown(f'<div class="tipbox">🌍 <b>Origin:</b> {wd.get("origin","")}</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:13px;font-weight:700;margin:12px 0 6px;">📝 Examples</div>', unsafe_allow_html=True)
            for i,ex in enumerate(wd.get("example_sentences",[]),1):
                st.markdown(f'<div style="background:#0B0D14;border-left:3px solid #4338CA;border-radius:0 7px 7px 0;padding:8px 12px;margin-bottom:6px;font-size:13px;color:#9CA3AF;font-style:italic;">{i}. "{ex}"</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="card"><div style="font-size:14px;font-weight:700;margin-bottom:10px;">🔄 Synonyms</div>', unsafe_allow_html=True)
            if wd.get("synonyms"): st.markdown("".join(f'<span class="syn-tag">{s}</span>' for s in wd["synonyms"]), unsafe_allow_html=True)
            st.markdown('<div style="font-size:14px;font-weight:700;margin:14px 0 8px;">↔️ Antonyms</div>', unsafe_allow_html=True)
            if wd.get("antonyms"): st.markdown("".join(f'<span class="ant-tag">{a}</span>' for a in wd["antonyms"]), unsafe_allow_html=True)
            st.markdown('<div class="tipbox" style="margin-top:14px;">🧠 Use this word in a sentence today!</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ARTICLE MOCK TEST
# ══════════════════════════════════════════════════════════════════════════════
elif page == "mock":
    st.markdown('<div class="hero-bar"><div style="font-size:22px;font-weight:800;font-family:\'Sora\',sans-serif;">📝 Article Mock Test</div><div style="font-size:13px;opacity:.8;margin-top:4px;">Test your comprehension on news articles</div></div>', unsafe_allow_html=True)
    test_art=st.session_state.get("test_article"); td=st.session_state.get("test_data")

    if not td:
        st.markdown('<div class="card" style="text-align:center;padding:40px;"><div style="font-size:40px;margin-bottom:12px;">📰</div><div style="font-size:16px;font-weight:700;margin-bottom:8px;">No Test Generated Yet</div><div style="font-size:13px;color:#4B5563;">Go to <b>📰 News & Articles</b> and click <b>📝 Test</b> on any article.</div></div>', unsafe_allow_html=True)
    else:
        if test_art:
            content=test_art.get("content",test_art.get("summary","")); words=len(content.split()); num_q_gen=td.get("total_questions",0); easy,medium,hard=difficulty_split(num_q_gen)
            st.markdown(f'<div class="hero-bar" style="padding:16px 22px;"><div style="font-size:10px;opacity:.7;text-transform:uppercase;margin-bottom:4px;">Testing on Article</div><div style="font-size:15px;font-weight:700;font-family:\'Sora\',sans-serif;">{test_art.get("title","")}</div><div style="font-size:12px;opacity:.7;margin-top:4px;">~{words} words · {num_q_gen}q · 🟢{easy} 🟡{medium} 🔴{hard}</div></div>', unsafe_allow_html=True)

        if not st.session_state.get("test_result"):
            answers=st.session_state.get("test_answers",{}); total_q=td.get("total_questions",0)
            answered=sum(1 for a in answers.values() if a); pct_done=int(answered/total_q*100) if total_q else 0
            c1,c2,c3=st.columns(3)
            c1.metric("Questions",total_q); c2.metric("Answered",f"{answered}/{total_q}"); c3.metric("Time",td.get("estimated_time","—"))
            st.markdown(f'<div style="margin:8px 0 14px;"><div class="progress-wrap"><div style="background:linear-gradient(135deg,#4338CA,#6D28D9);height:10px;width:{pct_done}%;border-radius:8px;"></div></div></div>', unsafe_allow_html=True)
            st.markdown("---")
            for q in td.get("questions",[]):
                qid=str(q["question_id"]); dtag=q.get("difficulty_tag","Medium"); skill=q.get("skill_tested","comprehension")
                dcls=DIFF_CLASS.get(dtag,"diff-medium"); scls=SKILL_BADGE.get(skill,"b-gray"); opts=q.get("options",[])
                st.markdown(f'<div class="question-card"><div class="q-header"><span class="q-num">Q{q["question_id"]}</span><span class="{dcls}">{dtag}</span><span class="badge {scls}">{skill.title()}</span></div>', unsafe_allow_html=True)
                render_question_text(q.get("question",""))
                st.markdown('</div>', unsafe_allow_html=True)
                sel=st.radio(f"Q{q['question_id']}",options=[f"{o['option_id']}. {o['text']}" for o in opts],key=f"q_{qid}",label_visibility="collapsed")
                if sel: answers[qid]=sel[0]
                st.markdown("<br>",unsafe_allow_html=True)
            st.session_state["test_answers"]=answers
            rem=total_q-len(answers)
            if rem>0: st.info(f"📋 {rem} question(s) remaining.")
            if st.button("✅ Submit & See Results",type="primary",use_container_width=True,disabled=(len(answers)<total_q)):
                with st.spinner("Evaluating..."):
                    sub,se=api_post("/mock-test/evaluate",{"questions":td["questions"],"user_answers":answers},timeout=30)
                if se: st.error(f"❌ {se}")
                else: st.session_state["test_result"]=sub; st.rerun()
        else:
            res=st.session_state["test_result"]; pct=res.get("percentage",0); grade=res.get("grade",""); gc=grade_color(grade)
            st.markdown(f'<div class="score-hero"><div style="font-size:11px;opacity:.7;text-transform:uppercase;margin-bottom:6px;">Your Score</div><div class="score-num">{res.get("score",0)}<span style="font-size:26px;opacity:.6;">/{res.get("total",0)}</span></div><div style="font-size:18px;margin:6px 0;">{pct}%</div><div style="background:{gc};display:inline-block;padding:4px 20px;border-radius:20px;font-size:18px;font-weight:800;font-family:\'Sora\',sans-serif;">Grade: {grade}</div></div>', unsafe_allow_html=True)
            r1,r2=st.columns(2)
            with r1:
                st.markdown('<div class="card"><div style="font-size:14px;font-weight:700;margin-bottom:10px;">📊 Skill Breakdown</div>', unsafe_allow_html=True)
                for skill,spct in res.get("skill_breakdown",{}).items():
                    sc2=score_color(spct)
                    st.markdown(f'<div style="margin-bottom:10px;"><div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px;"><span style="color:#D1D5DB;">{skill.title()}</span><span style="color:{sc2};font-weight:700;">{spct}%</span></div><div class="skill-bar-bg"><div style="background:{sc2};height:8px;width:{spct}%;border-radius:5px;"></div></div></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with r2:
                st.markdown('<div class="card"><div style="font-size:14px;font-weight:700;margin-bottom:10px;">💡 Feedback</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="expbox">💬 {res.get("feedback","")}</div>', unsafe_allow_html=True)
                for tip in res.get("improvement_tips",[]): st.markdown(f'<div class="tipbox">💡 {tip}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("### 🔍 Review")
            user_ans=st.session_state.get("test_answers",{})
            for q in td.get("questions",[]):
                qid=str(q["question_id"]); ua=user_ans.get(qid,""); ca=q.get("correct_answer",""); ok=ua.upper()==ca.upper(); icon="✅" if ok else "❌"
                dtag=q.get("difficulty_tag","Medium"); dcls=DIFF_CLASS.get(dtag,"diff-medium")
                st.markdown(f'<div class="question-card"><div class="q-header"><span>{icon}</span><span class="q-num">Q{q["question_id"]}</span><span class="{dcls}">{dtag}</span></div>', unsafe_allow_html=True)
                render_question_text(q.get("question",""))
                for opt in q.get("options",[]):
                    oid=opt["option_id"]
                    if oid==ca: cls,pre="correct-opt","✅ "
                    elif oid==ua and ua!=ca: cls,pre="wrong-opt","❌ "
                    else: cls,pre="neutral-opt",""
                    st.markdown(f'<div class="{cls}">{pre}<b>{oid}.</b> {opt["text"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="tipbox" style="margin-top:8px;">💡 {q.get("explanation","")}</div></div>', unsafe_allow_html=True)
            b1,b2=st.columns(2)
            with b1:
                if st.button("🔄 Retake",use_container_width=True):
                    st.session_state["test_data"]=None; st.session_state["test_result"]=None; st.session_state["test_answers"]={}; st.rerun()
            with b2:
                if st.button("📰 New Article",use_container_width=True):
                    st.session_state.update({"test_data":None,"test_result":None,"test_answers":{},"test_article":None})
                    st.session_state["page"]="news"; st.rerun()
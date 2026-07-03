import os
import sys
import streamlit as st
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whisper_util import VoiceProcessor
from qwen_utils import ScamAnalyzer

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Jhol-Check",
    page_icon="🧐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Design tokens ──────────────────────────────────────────────────────────
# Palette: deep navy background, off-white surface, red danger, amber warning,
# emerald safe, electric-blue accent. One signature: the animated scan-line
# that runs across the evidence card on load — forensic instrument aesthetic.
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset & base ── */
html, body, .stApp { background: #0d1117; color: #e6edf3; }
*, *::before, *::after { box-sizing: border-box; }

/* ── Typography ── */
h1, h2, h3, h4 { font-family: 'Inter', sans-serif; letter-spacing: -0.02em; }
code, .mono      { font-family: 'IBM Plex Mono', monospace; }

/* ── Hide streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.block-container { padding: 1.5rem 2rem 2rem; max-width: 1400px; }

/* ── Masthead ── */
.masthead {
    display: flex; align-items: center; gap: 14px;
    border-bottom: 1px solid #21262d;
    padding-bottom: 18px; margin-bottom: 28px;
}
.masthead-logo {
    width: 44px; height: 44px; border-radius: 10px;
    background: linear-gradient(135deg, #ef4444, #b91c1c);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
}
.masthead-title {
    font-size: 1.5rem; font-weight: 700; color: #f0f6fc;
    font-family: 'Inter', sans-serif;
}
.masthead-sub {
    font-size: 0.78rem; color: #8b949e;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.04em;
}
.masthead-badge {
    margin-left: auto;
    background: #161b22; border: 1px solid #30363d;
    border-radius: 6px; padding: 4px 12px;
    font-size: 0.72rem; color: #58a6ff;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Panel cards ── */
.panel {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 22px 24px;
    height: 100%;
}
.panel-title {
    font-size: 0.75rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: #8b949e; margin-bottom: 18px;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Input tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0; background: #0d1117;
    border-radius: 8px; padding: 3px;
    border: 1px solid #21262d;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 0.82rem; font-weight: 500;
    color: #8b949e; background: transparent;
    border: none;
    font-family: 'Inter', sans-serif;
}
.stTabs [aria-selected="true"] {
    background: #21262d !important;
    color: #f0f6fc !important;
    box-shadow: none !important;
}

/* ── Textarea ── */
.stTextArea textarea {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    resize: vertical !important;
}
.stTextArea textarea:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.12) !important;
}
.stTextArea textarea::placeholder { color: #484f58 !important; }

/* ── File uploader ── */
.stFileUploader {
    background: #0d1117 !important;
    border: 1px dashed #30363d !important;
    border-radius: 8px !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: #ef4444 !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 10px 0 !important;
    font-family: 'Inter', sans-serif !important;
    transition: background 0.15s ease, transform 0.1s ease !important;
    width: 100% !important;
}
.stButton > button[kind="primary"]:hover {
    background: #dc2626 !important;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"]:active { transform: translateY(0); }

/* ── Verdict banner ── */
.verdict-scam {
    background: linear-gradient(135deg, #2d1010, #1f0808);
    border: 1px solid #ef4444;
    border-radius: 10px;
    padding: 16px 20px;
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 20px;
}
.verdict-safe {
    background: linear-gradient(135deg, #0d2218, #091a12);
    border: 1px solid #22c55e;
    border-radius: 10px;
    padding: 16px 20px;
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 20px;
}
.verdict-icon { font-size: 1.6rem; }
.verdict-label {
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.1em; color: #8b949e;
    font-family: 'IBM Plex Mono', monospace;
    margin-bottom: 2px;
}
.verdict-text-scam {
    font-size: 1.1rem; font-weight: 700; color: #fca5a5;
    font-family: 'Inter', sans-serif;
}
.verdict-text-safe {
    font-size: 1.1rem; font-weight: 700; color: #86efac;
    font-family: 'Inter', sans-serif;
}

/* ── Metric cards ── */
.metric-row { display: flex; gap: 10px; margin-bottom: 20px; }
.metric-card {
    flex: 1;
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px 16px;
}
.metric-label {
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em;
    color: #8b949e; font-family: 'IBM Plex Mono', monospace;
    margin-bottom: 4px;
}
.metric-value {
    font-size: 1.3rem; font-weight: 700; font-family: 'Inter', sans-serif;
}
.metric-scam { color: #ef4444; }
.metric-safe { color: #22c55e; }
.metric-warn { color: #f59e0b; }
.metric-info { color: #58a6ff; }
.metric-neutral { color: #e6edf3; }

/* ── Confidence bar ── */
.conf-bar-bg {
    height: 5px; background: #21262d; border-radius: 3px;
    margin-top: 6px;
}
.conf-bar-fill {
    height: 100%; border-radius: 3px;
    transition: width 0.6s ease;
}

/* ── Section headers inside output ── */
.section-label {
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.1em; color: #58a6ff;
    font-family: 'IBM Plex Mono', monospace;
    margin: 18px 0 10px;
    padding-left: 8px;
    border-left: 2px solid #58a6ff;
}

/* ── Technique chips ── */
.chip-row { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 4px; }
.chip {
    padding: 4px 11px; border-radius: 20px;
    font-size: 0.77rem; font-weight: 500;
    font-family: 'IBM Plex Mono', monospace;
}
.chip-fear    { background: #2d1010; color: #fca5a5; border: 1px solid #ef4444; }
.chip-urgency { background: #2d1a0a; color: #fdba74; border: 1px solid #f97316; }
.chip-authority { background: #0d1a2d; color: #93c5fd; border: 1px solid #3b82f6; }
.chip-greed   { background: #1a2d0d; color: #86efac; border: 1px solid #22c55e; }
.chip-scarcity { background: #2d2210; color: #fde68a; border: 1px solid #f59e0b; }
.chip-trust   { background: #1a0d2d; color: #d8b4fe; border: 1px solid #a855f7; }
.chip-curiosity { background: #0d2a2d; color: #67e8f9; border: 1px solid #06b6d4; }
.chip-emotional { background: #2d0d1a; color: #fbcfe8; border: 1px solid #ec4899; }
.chip-social  { background: #1a2d1a; color: #a7f3d0; border: 1px solid #10b981; }
.chip-reciprocity { background: #2d250d; color: #fef08a; border: 1px solid #eab308; }
.chip-default { background: #161b22; color: #8b949e; border: 1px solid #30363d; }

/* ── Evidence cards ── */
.evidence-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 8px;
    position: relative;
    overflow: hidden;
}
.evidence-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.ev-authority::before  { background: #3b82f6; }
.ev-fear::before       { background: #ef4444; }
.ev-urgency::before    { background: #f97316; }
.ev-credential::before { background: #a855f7; }
.ev-suspicious::before { background: #f59e0b; }
.ev-greed::before      { background: #22c55e; }
.ev-default::before    { background: #30363d; }

.ev-phrase {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem; color: #e6edf3;
    margin-bottom: 5px;
}
.ev-label-row { display: flex; align-items: center; gap: 6px; }
.ev-arrow { color: #484f58; font-size: 0.8rem; }
.ev-badge {
    font-size: 0.68rem; font-weight: 600;
    padding: 2px 8px; border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace;
    text-transform: uppercase; letter-spacing: 0.05em;
}
.badge-authority   { background: #1d3a6e; color: #93c5fd; }
.badge-fear        { background: #3d1010; color: #fca5a5; }
.badge-urgency     { background: #3d2210; color: #fdba74; }
.badge-credential  { background: #2d1a3d; color: #d8b4fe; }
.badge-suspicious  { background: #3d2e10; color: #fde68a; }
.badge-link        { background: #3d2e10; color: #fde68a; }
.badge-greed       { background: #1a3d1a; color: #86efac; }
.badge-default     { background: #21262d; color: #8b949e; }

/* ── Reasoning steps ── */
.reasoning-step {
    display: flex; gap: 12px; align-items: flex-start;
    margin-bottom: 10px;
}
.step-num {
    min-width: 24px; height: 24px; border-radius: 50%;
    background: #21262d; border: 1px solid #30363d;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.72rem; font-weight: 600; color: #58a6ff;
    font-family: 'IBM Plex Mono', monospace;
}
.step-text {
    font-size: 0.86rem; color: #c9d1d9; line-height: 1.55;
    font-family: 'Inter', sans-serif; padding-top: 2px;
}

/* ── Info requested pills ── */
.info-pill {
    display: inline-block;
    background: #161b22; border: 1px solid #30363d;
    border-radius: 5px; padding: 3px 10px;
    font-size: 0.77rem; color: #fca5a5;
    font-family: 'IBM Plex Mono', monospace;
    margin: 3px;
}

/* ── Action checklist ── */
.action-item {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 12px; border-radius: 7px;
    background: #0d1117; border: 1px solid #21262d;
    margin-bottom: 7px;
}
.action-icon { font-size: 1rem; margin-top: 1px; }
.action-text {
    font-size: 0.85rem; color: #c9d1d9;
    font-family: 'Inter', sans-serif; line-height: 1.4;
}

/* ── Transcript box ── */
.transcript-box {
    background: #0d1117; border: 1px solid #21262d;
    border-radius: 8px; padding: 14px 16px;
    font-size: 0.83rem; color: #8b949e;
    font-family: 'Inter', sans-serif;
    line-height: 1.6; max-height: 120px;
    overflow-y: auto;
    border-left: 3px solid #30363d;
    margin-bottom: 4px;
}

/* ── JSON viewer ── */
.stJson { background: #0d1117 !important; }

/* ── Divider ── */
.out-divider {
    border: none; border-top: 1px solid #21262d;
    margin: 16px 0;
}

/* ── Empty state ── */
.empty-state {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    min-height: 320px; text-align: center;
    color: #484f58;
}
.empty-icon { font-size: 3rem; margin-bottom: 14px; opacity: 0.4; }
.empty-text { font-size: 0.88rem; font-family: 'IBM Plex Mono', monospace; }

/* ── Streamlit element overrides ── */
.stSpinner > div { border-top-color: #ef4444 !important; }
div[data-testid="stMetricValue"] { color: #e6edf3; }
.stAlert { border-radius: 8px; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #161b22; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #484f58; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ─── Helpers ────────────────────────────────────────────────────────────────
TECHNIQUE_CLASSES = {
    "fear":               ("chip-fear",      "⚠️ Fear"),
    "urgency":            ("chip-urgency",   "⏱ Urgency"),
    "authority":          ("chip-authority", "🏛 Authority"),
    "greed":              ("chip-greed",     "💰 Greed"),
    "scarcity":           ("chip-scarcity",  "⏳ Scarcity"),
    "trust exploitation": ("chip-trust",     "🤝 Trust Exploit"),
    "curiosity":          ("chip-curiosity", "🔍 Curiosity"),
    "emotional manipulation": ("chip-emotional", "💔 Emotional Manip."),
    "social proof":       ("chip-social",    "👥 Social Proof"),
    "reciprocity":        ("chip-reciprocity","↩ Reciprocity"),
    "mlm":                ("chip-default",   "🔄 MLM"),
}

LABEL_CLASSES = {
    "authority":          ("badge-authority",   "ev-authority"),
    "fear":               ("badge-fear",        "ev-fear"),
    "urgency":            ("badge-urgency",     "ev-urgency"),
    "credential theft":   ("badge-credential",  "ev-credential"),
    "suspicious link":    ("badge-link",        "ev-suspicious"),
    "suspicious contact": ("badge-suspicious",  "ev-suspicious"),
    "suspicious upi":     ("badge-suspicious",  "ev-suspicious"),
    "advance fee":        ("badge-greed",       "ev-greed"),
    "greed":              ("badge-greed",       "ev-greed"),
    "isolation":          ("badge-credential",  "ev-credential"),
    "extortion":          ("badge-fear",        "ev-fear"),
}

RISK_COLORS = {
    "CRITICAL": ("#ef4444", "metric-scam"),
    "HIGH":     ("#f97316", "metric-warn"),
    "MEDIUM":   ("#f59e0b", "metric-warn"),
    "LOW":      ("#22c55e", "metric-safe"),
}

ACTION_ICONS = {
    "do not":  "🚫",
    "report":  "📢",
    "block":   "🔒",
    "verify":  "✅",
    "call":    "📞",
    "visit":   "🌐",
    "never":   "❌",
    "safe":    "✅",
}

def get_action_icon(action_text):
    low = action_text.lower()
    for kw, icon in ACTION_ICONS.items():
        if kw in low:
            return icon
    return "•"

def render_techniques(techniques):
    if not techniques:
        return '<div class="chip-row"><span class="chip chip-default">None detected</span></div>'
    chips = []
    for t in techniques:
        key = t.lower()
        cls, label = TECHNIQUE_CLASSES.get(key, ("chip-default", t))
        chips.append(f'<span class="chip {cls}">{label}</span>')
    return f'<div class="chip-row">{"".join(chips)}</div>'

def render_evidence_card(ev):
    phrase = ev.get("text", "")
    label  = ev.get("label", "")
    key    = label.lower()
    badge_cls, card_cls = LABEL_CLASSES.get(key, ("badge-default", "ev-default"))
    return f"""<div class="evidence-card {card_cls}">
  <div class="ev-phrase">"{phrase}"</div>
  <div class="ev-label-row">
    <span class="ev-arrow">→</span>
    <span class="ev-badge {badge_cls}">{label}</span>
  </div>
</div>"""

def render_metric(label, value, color_cls, conf=None, bar_color=None):
    bar_html = ""
    if conf is not None:
        pct = min(max(int(conf), 0), 100)
        bar_html = f"""<div class="conf-bar-bg">
  <div class="conf-bar-fill" style="width:{pct}%; background:{bar_color or '#58a6ff'};"></div>
</div>"""
    return f"""<div class="metric-card">
  <div class="metric-label">{label}</div>
  <div class="metric-value {color_cls}">{value}</div>
  {bar_html}
</div>"""

def get_risk_color_hex(risk):
    return RISK_COLORS.get(risk.upper(), ("#8b949e", "metric-neutral"))[0]

# ─── Model loading ───────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_pipelines():
    voice    = VoiceProcessor(model_name="openai/whisper-small")
    analyzer = ScamAnalyzer(repo_id="PrachiSandipkumar/qwen_scam_high_accuracy")
    return voice, analyzer

# ─── Masthead ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="masthead">
  <div class="masthead-logo">🧐</div>
  <div>
    <div class="masthead-title">Jhol-Check</div>
    <div class="masthead-sub">Cybercrime & Fraud Intelligence Terminal</div>
  </div>
  <div class="masthead-badge">Qwen2.5-3B · LoRA · Whisper-small</div>
</div>
""", unsafe_allow_html=True)

# ─── Load models ─────────────────────────────────────────────────────────────
with st.spinner("Loading AI pipelines…"):
    voice_engine, analyzer_engine = load_pipelines()

# ─── Layout ──────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1.4], gap="large")

# ── Session state init ───────────────────────────────────────────────────────
# "txt_input"        = the textarea value (Streamlit owns this key)
# "pending_example"  = text injected by a quick-test button click
# "pending_trigger"  = True when we want to auto-run analysis on page reload
if "pending_example" not in st.session_state:
    st.session_state["pending_example"] = ""
if "pending_trigger" not in st.session_state:
    st.session_state["pending_trigger"] = False

# If a quick-test button was clicked last cycle, push the text into the
# textarea's session_state key BEFORE the widget renders, then clear the flag.
if st.session_state["pending_example"]:
    st.session_state["txt_input"]       = st.session_state["pending_example"]
    st.session_state["pending_example"] = ""

# ════════════════════════════════════════════════════════════════════════════
# LEFT — INPUT PANEL
# ════════════════════════════════════════════════════════════════════════════
with col_left:
    st.markdown('<div class="panel-title">Input</div>', unsafe_allow_html=True)

    tab_text, tab_voice = st.tabs(["💬 Text Message", "🎙 Call Recording"])

    target_text = ""
    trigger     = False

    with tab_text:
        st.markdown("<br>", unsafe_allow_html=True)
        text_input = st.text_area(
            label="",
            placeholder="Paste a suspicious SMS, email, WhatsApp message, or call transcript here…",
            height=220,
            key="txt_input",          # Streamlit stores the live value in st.session_state["txt_input"]
            label_visibility="collapsed",
        )
        # Consume the pending_trigger flag set by quick-test buttons
        if st.session_state.get("pending_trigger", False):
            st.session_state["pending_trigger"] = False
            if text_input.strip():
                target_text = text_input.strip()
                trigger     = True

        if st.button("Analyze Message", type="primary", use_container_width=True, key="btn_text"):
            if text_input.strip():
                target_text = text_input.strip()
                trigger     = True
            else:
                st.warning("Paste a message first.")

    with tab_voice:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Upload a recorded scam call. Whisper will transcribe it before analysis.")
        audio_file = st.file_uploader(
            label="",
            type=["mp3", "wav", "m4a", "ogg"],
            key="audio_upload",
            label_visibility="collapsed",
        )
        if st.button("Transcribe & Analyze", type="primary", use_container_width=True, key="btn_audio"):
            if audio_file:
                tmp = f"/tmp/upload_{audio_file.name}"
                with open(tmp, "wb") as f:
                    f.write(audio_file.getbuffer())
                with st.spinner("Whisper is transcribing the call…"):
                    target_text = voice_engine.process_large_audio(tmp)
                if os.path.exists(tmp):
                    os.remove(tmp)
                if target_text.strip():
                    trigger = True
                    st.info(f"**Transcribed:** {target_text[:200]}{'…' if len(target_text)>200 else ''}")
                else:
                    st.error("Transcription returned empty. Check the audio file.")
            else:
                st.warning("Upload an audio file first.")

    # ── Quick-test examples ──────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Quick Tests</div>', unsafe_allow_html=True)

    EXAMPLES = [
        ("🔴 OTP Scam",
         "SBI fraud dept here. We detected suspicious Rs.49,000 transaction. Share the OTP you just received to cancel it."),
        ("🔴 UPI Scam",
         "Someone sent you Rs.5,000 on Google Pay. Accept payment by entering UPI PIN here: http://gpay-accept.co/receive/5000"),
        ("🟠 Govt. Impersonation",
         "CBI officer speaking: Your Aadhaar is linked to money laundering. Pay Rs.50,000 settlement to avoid immediate arrest."),
        ("🟢 Legit Bank SMS",
         "HDFC Bank: OTP for NetBanking login is 847291. Valid 10 min. HDFC NEVER asks for OTP. Do NOT share with anyone."),
    ]

    cols = st.columns(2)
    for i, (label, txt) in enumerate(EXAMPLES):
        with cols[i % 2]:
            if st.button(label, use_container_width=True, key=f"ex_{i}"):
                # Write the example into the textarea's session_state key.
                # Streamlit will re-render the textarea with this value on the
                # next cycle (which the rerun below triggers immediately).
                st.session_state["pending_example"] = txt
                st.session_state["pending_trigger"] = True   # auto-run analysis too
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# RIGHT — OUTPUT PANEL
# ════════════════════════════════════════════════════════════════════════════
with col_right:
    st.markdown('<div class="panel-title">Intelligence Report</div>', unsafe_allow_html=True)

    if not trigger:
        st.markdown("""
        <div class="empty-state">
          <div class="empty-icon">🛡️</div>
          <div class="empty-text">Submit a message or call recording<br>to generate a fraud intelligence report.</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        with st.spinner("Analyzing with fine-tuned Qwen…"):
            t0     = time.time()
            report = analyzer_engine.analyze_text(target_text)
            elapsed = time.time() - t0

        scam      = report.get("scam", "NO")
        scam_type = report.get("scam_type", "Other")
        risk      = report.get("risk_level", "LOW").upper()
        conf      = report.get("confidence", 90)
        techniques= report.get("techniques", [])
        evidence  = report.get("evidence", [])
        requested = report.get("requested_information", [])
        reasoning = report.get("reasoning", [])
        actions   = report.get("recommended_action", [])

        risk_hex, _ = RISK_COLORS.get(risk, ("#8b949e", "metric-neutral"))

        # ── Verdict banner ──────────────────────────────────────────────────
        if scam == "YES":
            st.markdown(f"""
            <div class="verdict-scam">
              <span class="verdict-icon">🚨</span>
              <div>
                <div class="verdict-label">Threat Detected</div>
                <div class="verdict-text-scam">{scam_type}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="verdict-safe">
              <span class="verdict-icon">✅</span>
              <div>
                <div class="verdict-label">Status</div>
                <div class="verdict-text-safe">No Fraud Indicators Detected</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Metric cards ────────────────────────────────────────────────────
        m_classification = "SCAM" if scam == "YES" else "CLEAN"
        m_cls_color = "metric-scam" if scam == "YES" else "metric-safe"

        st.markdown(f"""
        <div class="metric-row">
          {render_metric("Classification", m_classification, m_cls_color)}
          {render_metric("Risk Level", risk, _, )}
          {render_metric("Confidence", f"{conf}%", "metric-info", conf, risk_hex)}
        </div>
        """.replace(_, "metric-warn" if risk in ("HIGH","CRITICAL") else "metric-safe"), unsafe_allow_html=True)

        # ── Tabs ─────────────────────────────────────────────────────────────
        tab_ev, tab_reason, tab_json = st.tabs([
            "🔬 Evidence & Techniques",
            "🧠 Reasoning & Actions",
            "📄 Full JSON",
        ])

        # ── TAB 1: Evidence & Techniques ─────────────────────────────────────
        with tab_ev:
            # Message preview
            st.markdown('<div class="section-label">Analyzed Message</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="transcript-box">{target_text}</div>', unsafe_allow_html=True)
            st.caption(f"Analysis completed in {elapsed:.1f}s")

            # Techniques
            st.markdown('<div class="section-label">Manipulation Techniques</div>', unsafe_allow_html=True)
            st.markdown(render_techniques(techniques), unsafe_allow_html=True)

            # Evidence extraction
            st.markdown('<div class="section-label">Extracted Evidence Fragments</div>', unsafe_allow_html=True)
            if evidence:
                cards_html = "".join(render_evidence_card(ev) for ev in evidence)
                st.markdown(cards_html, unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#484f58;font-size:0.84rem;font-family:\'IBM Plex Mono\',monospace;">No specific phrases flagged.</p>', unsafe_allow_html=True)

            # Information requested
            if requested and requested != ["None"]:
                st.markdown('<div class="section-label">Information Being Targeted</div>', unsafe_allow_html=True)
                pills = "".join(f'<span class="info-pill">{r}</span>' for r in requested if r != "None")
                st.markdown(f"<div>{pills}</div>", unsafe_allow_html=True)

        # ── TAB 2: Reasoning & Actions ────────────────────────────────────────
        with tab_reason:
            st.markdown('<div class="section-label">Step-by-Step Reasoning</div>', unsafe_allow_html=True)
            if reasoning:
                steps_html = ""
                for i, step in enumerate(reasoning, 1):
                    steps_html += f"""<div class="reasoning-step">
  <div class="step-num">{i}</div>
  <div class="step-text">{step}</div>
</div>"""
                st.markdown(steps_html, unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#484f58;font-size:0.84rem;">No reasoning steps available.</p>', unsafe_allow_html=True)

            if actions:
                st.markdown('<hr class="out-divider">', unsafe_allow_html=True)
                st.markdown('<div class="section-label">Recommended Actions</div>', unsafe_allow_html=True)
                items_html = ""
                for action in actions:
                    icon = get_action_icon(action)
                    items_html += f"""<div class="action-item">
  <span class="action-icon">{icon}</span>
  <span class="action-text">{action}</span>
</div>"""
                st.markdown(items_html, unsafe_allow_html=True)

        # ── TAB 3: Full JSON ──────────────────────────────────────────────────
        with tab_json:
            display_report = {k: v for k, v in report.items() if k != "raw_output"}
            st.json(display_report)
            st.caption("raw_output field excluded for readability. Available in the report dict.")
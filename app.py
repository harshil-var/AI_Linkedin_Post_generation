import os
import sys
import uuid
import time
import streamlit as st
from dotenv import load_dotenv
from langgraph.types import Command

# Reconfigure stdout for UTF-8 encoding on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure current directory is in sys.path for relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import both compiled graph apps
from iterative_tools import app as ai_app
from humanintheloop import app as hitl_app

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="LinkedIn Post Studio",
    page_icon="https://cdn-icons-png.flaticon.com/512/174/174857.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphic CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Ambient Dark Backdrop with Glass Gradient */
    .stApp {
        background: radial-gradient(circle at 15% 15%, rgba(10, 102, 194, 0.2) 0%, transparent 45%),
                    radial-gradient(circle at 85% 85%, rgba(139, 92, 246, 0.18) 0%, transparent 45%),
                    linear-gradient(135deg, #070a12 0%, #0b1120 50%, #0f172a 100%);
        color: #f3f4f6;
    }

    /* Glassmorphic Cards */
    .glass-card {
        background: rgba(17, 25, 40, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.12);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .glass-card:hover {
        border-color: rgba(10, 102, 194, 0.45);
        box-shadow: 0 16px 44px rgba(10, 102, 194, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }

    /* Hero Banner Header */
    .hero-banner {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(10, 102, 194, 0.4);
        border-radius: 24px;
        padding: 26px 36px;
        margin-bottom: 24px;
        backdrop-filter: blur(20px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5), 0 0 30px rgba(10, 102, 194, 0.2);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
    }

    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #0a66c2 0%, #38bdf8 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.98rem;
        font-weight: 400;
        margin: 0;
    }

    /* Visual Workflow Indicator */
    .workflow-diagram {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 16px 22px;
        margin-bottom: 24px;
        backdrop-filter: blur(14px);
    }

    .wf-step {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #94a3b8;
        padding: 10px 16px;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        transition: all 0.3s ease;
    }

    .wf-step.active {
        background: rgba(10, 102, 194, 0.3);
        border-color: rgba(56, 189, 248, 0.6);
        color: #38bdf8;
        box-shadow: 0 0 18px rgba(56, 189, 248, 0.25);
    }

    .wf-arrow {
        color: #475569;
        font-weight: 700;
    }

    /* LinkedIn Card Preview */
    .linkedin-preview-card {
        background: rgba(15, 23, 42, 0.88);
        border: 1px solid rgba(10, 102, 194, 0.4);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(18px);
    }

    .linkedin-header {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 18px;
    }

    .linkedin-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0a66c2 0%, #0284c7 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 14px rgba(10, 102, 194, 0.5);
    }

    .linkedin-author-name {
        font-weight: 700;
        font-size: 1.05rem;
        color: #f8fafc;
    }

    .linkedin-author-title {
        font-size: 0.82rem;
        color: #94a3b8;
    }

    .linkedin-post-content {
        font-size: 0.98rem;
        line-height: 1.65;
        color: #e2e8f0;
        white-space: pre-wrap;
        background: rgba(255, 255, 255, 0.03);
        padding: 20px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        margin-bottom: 16px;
    }

    /* Status Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .badge-awaiting {
        background: rgba(234, 179, 8, 0.18);
        color: #fde047;
        border: 1px solid rgba(234, 179, 8, 0.4);
    }

    .badge-approved {
        background: rgba(34, 197, 94, 0.18);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.4);
    }

    .badge-rejected {
        background: rgba(239, 68, 68, 0.18);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }

    /* KPI metric cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 14px;
        text-align: center;
    }

    .metric-val {
        font-size: 1.3rem;
        font-weight: 700;
        color: #38bdf8;
    }

    .metric-lbl {
        font-size: 0.78rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Styled Radio & Form Controls */
    div[data-testid="stRadio"] > label {
        font-weight: 700 !important;
        color: #38bdf8 !important;
        font-size: 1.02rem !important;
        margin-bottom: 8px !important;
    }

    div[role="radiogroup"] {
        gap: 12px !important;
    }

    div[role="radiogroup"] label {
        background: rgba(15, 23, 42, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        padding: 12px 18px !important;
        border-radius: 14px !important;
        transition: all 0.25s ease !important;
    }

    div[role="radiogroup"] label:hover {
        border-color: rgba(56, 189, 248, 0.5) !important;
        background: rgba(10, 102, 194, 0.15) !important;
    }

    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
    }

    .stTextArea textarea, .stTextInput input {
        background-color: rgba(15, 23, 42, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #f8fafc !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)


# Session state initialization
if "workflow_choice" not in st.session_state:
    st.session_state.workflow_choice = "Interactive Human Review"

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "history" not in st.session_state:
    st.session_state.history = []

if "topic" not in st.session_state:
    st.session_state.topic = ""

if "custom_feedback_val" not in st.session_state:
    st.session_state.custom_feedback_val = ""


def on_workflow_change():
    """Clear stale execution state when toggling reviewer mode to prevent lag and state mismatch."""
    st.session_state.current_result = None
    st.session_state.history = []
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.custom_feedback_val = ""


def reset_session():
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.current_result = None
    st.session_state.history = []
    st.session_state.topic = ""
    st.session_state.custom_feedback_val = ""


# Helper function to execute human rewrite feedback
def execute_human_rewrite(feedback_str: str):
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    if st.session_state.history:
        st.session_state.history[-1]["feedback"] = feedback_str
        st.session_state.history[-1]["status"] = "rejected"

    status_box = st.status("🔄 AI Writer is processing your rewrite request...", expanded=True)
    with status_box:
        st.write("📥 Feedback received:", feedback_str)
        st.write("🔍 Tavily Search & Writer LLM generating revised draft...")
        time.sleep(0.3)
        
        next_result = hitl_app.invoke(Command(resume=feedback_str), config=config)
        st.session_state.current_result = next_result

        if "__interrupt__" in next_result:
            new_data = next_result["__interrupt__"][0].value
            st.session_state.history.append({
                "attempt": new_data.get("attempt", 2),
                "draft": new_data.get("draft", ""),
                "feedback": None,
                "status": "awaiting_review"
            })
            status_box.update(label="✅ Revised Draft Ready for Your Review!", state="complete", expanded=False)
        else:
            status_box.update(label="✅ Workflow Completed!", state="complete", expanded=False)

    st.session_state.custom_feedback_val = ""
    st.rerun()


# Hero Header Banner
st.markdown("""
<div class="hero-banner">
    <div style="display: flex; align-items: center; gap: 20px;">
        <svg width="52" height="52" viewBox="0 0 24 24" fill="#0a66c2">
            <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
        </svg>
        <div>
            <div class="hero-title">LinkedIn Post Studio</div>
            <div class="hero-subtitle">Multi-Agent LangGraph System with Tavily Web Search, AI Reviewer & Interactive Human-in-the-Loop workflows</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# Sidebar Configuration Panel
with st.sidebar:
    st.header("⚙️ System Controls")
    
    st.caption("Active Session Thread:")
    st.code(st.session_state.thread_id[:16] + "...", language="text")

    st.markdown("---")
    
    st.subheader("💡 Topic Ideas")
    preset_topics = [
        "How Generative AI is Transforming Software Development",
        "Building Resilient Engineering Teams in Remote Environments",
        "Key Lessons from Deploying LangGraph Agents to Production",
        "The Future of Data Engineering & Real-Time Analytics"
    ]
    for pt in preset_topics:
        if st.button(pt, use_container_width=True):
            st.session_state.topic = pt

    st.markdown("---")
    if st.button("🔄 Reset / New Post", type="secondary", use_container_width=True):
        reset_session()
        st.rerun()


# Workflow Selector & Pipeline Diagram
current_res = st.session_state.current_result
is_interrupted = current_res and "__interrupt__" in current_res
is_completed = current_res and "__interrupt__" not in current_res

step1_cls = "active" if not current_res else ""
step2_cls = "active" if current_res and not is_completed else ""
step3_cls = "active" if is_completed else ""

review_label = "HUMAN REVIEW" if "Human" in st.session_state.workflow_choice else "AI REVIEWER"

st.markdown(f"""
<div class="workflow-diagram">
    <div class="wf-step {step1_cls}">
        <span>1. WRITER AGENT</span>
    </div>
    <div class="wf-arrow">➔</div>
    <div class="wf-step {step1_cls}">
        <span>2. TAVILY SEARCH TOOL</span>
    </div>
    <div class="wf-arrow">➔</div>
    <div class="wf-step {step2_cls}">
        <span>3. {review_label}</span>
    </div>
    <div class="wf-arrow">➔</div>
    <div class="wf-step {step3_cls}">
        <span>4. APPROVED POST</span>
    </div>
</div>
""", unsafe_allow_html=True)


# Main Content Layout (Two Columns)
col_controls, col_preview = st.columns([1.15, 0.85], gap="large")

with col_controls:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📝 1. Topic & Workflow Selection")
    
    # Select Reviewer System Mode directly bound to session state with instant callback
    st.radio(
        "Choose Reviewer Workflow:",
        options=[
            "Interactive Human Review",
            "Autonomous AI Reviewer"
        ],
        key="workflow_choice",
        horizontal=True,
        on_change=on_workflow_change,
        captions=[
            "Human-in-the-Loop — Uses Tavily Search + interactive interrupts for your approval or feedback.",
            "Autonomous AI — Uses Tavily Search + AI Reviewer node to iterate automatically until publish-ready."
        ]
    )

    st.write("")
    # Topic Input
    topic_input = st.text_input(
        "What topic would you like a LinkedIn post about?",
        value=st.session_state.topic,
        placeholder="e.g. Why Python is essential for AI Engineers in 2026...",
        key="topic_input_field"
    )

    st.write("")
    gen_btn = st.button("✨ Generate Post Draft", type="primary", use_container_width=True, disabled=not topic_input.strip())
    st.markdown('</div>', unsafe_allow_html=True)

    if gen_btn and topic_input.strip():
        st.session_state.topic = topic_input
        st.session_state.history = []
        st.session_state.thread_id = str(uuid.uuid4())

        is_hitl = "Human" in st.session_state.workflow_choice
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        
        initial_state = {
            "topic": topic_input,
            "messages": [],
            "draft": "",
            "review_feedback": "",
            "is_approved": False,
            "attempt": 0,
        }

        mode_name = "Interactive Human Review" if is_hitl else "Autonomous AI Reviewer"
        status_box = st.status(f"🤖 Running workflow using {mode_name}...", expanded=True)
        
        with status_box:
            st.write("🎯 Topic:", topic_input)
            st.write("🔍 Writer Node checking Tavily search & generating draft...")
            
            if is_hitl:
                result = hitl_app.invoke(initial_state, config=config)
            else:
                result = ai_app.invoke(initial_state)

            st.session_state.current_result = result
            
            if "__interrupt__" in result:
                data = result["__interrupt__"][0].value
                st.session_state.history.append({
                    "attempt": data.get("attempt", 1),
                    "draft": data.get("draft", ""),
                    "feedback": None,
                    "status": "awaiting_review"
                })
                status_box.update(label="✅ Initial Draft Ready for Your Review!", state="complete", expanded=False)
            else:
                final_draft = result.get("draft", "")
                st.session_state.history.append({
                    "attempt": result.get("attempt", 1),
                    "draft": final_draft,
                    "feedback": result.get("review_feedback", ""),
                    "status": "approved" if result.get("is_approved") else "ended"
                })
                status_box.update(label="✅ Autonomous Workflow Complete!", state="complete", expanded=False)

        st.rerun()

    # Active Review Controls Section
    if st.session_state.current_result:
        res = st.session_state.current_result
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        if "__interrupt__" in res:
            # Human-in-the-Loop Interrupt Active
            interrupt_data = res["__interrupt__"][0].value
            current_attempt = interrupt_data.get("attempt", 1)

            st.subheader(f"🙋‍♂️ 2. Human Review Controls (Attempt {current_attempt}/3)")
            st.markdown("""
            <div class="badge badge-awaiting" style="margin-bottom: 12px;">
                🟡 Status: Paused at Interrupt — Awaiting Human Decision
            </div>
            """, unsafe_allow_html=True)

            st.write("Review the generated draft on the right. Approve it to publish, or choose feedback for a rewrite.")

            # Approve Button
            if st.button("✅ Approve & Publish Post", type="primary", use_container_width=True):
                if st.session_state.history:
                    st.session_state.history[-1]["feedback"] = "Approved by human."
                    st.session_state.history[-1]["status"] = "approved"

                status_box = st.status("🎉 Finalizing post approval...", expanded=True)
                with status_box:
                    st.write("Sending approval signal to workflow engine...")
                    next_result = hitl_app.invoke(Command(resume="approved"), config=config)
                    st.session_state.current_result = next_result
                    status_box.update(label="🟢 Post Approved!", state="complete", expanded=False)
                st.rerun()

            st.markdown("---")
            st.markdown("### 🔄 Or Request a Rewrite:")
            
            st.caption("⚡ One-Click Feedback Presets:")
            p1, p2 = st.columns(2)
            p3, p4 = st.columns(2)

            with p1:
                if st.button("✂️ Make it more concise", use_container_width=True):
                    execute_human_rewrite("Please make the post more concise with shorter paragraphs.")

            with p2:
                if st.button("🪝 Add a punchier hook", use_container_width=True):
                    execute_human_rewrite("Make the opening hook line punchier and more intriguing.")

            with p3:
                if st.button("📢 Stronger Call-To-Action", use_container_width=True):
                    execute_human_rewrite("End with a stronger, clearer question or Call To Action.")

            with p4:
                if st.button("🤝 Conversational tone", use_container_width=True):
                    execute_human_rewrite("Adjust the tone to be warmer, more conversational and relatable.")

            st.write("")
            custom_input = st.text_area(
                "Enter custom review feedback:",
                value=st.session_state.custom_feedback_val,
                placeholder="Specify exact changes (e.g. mention Tavily search data, focus on business ROI...)",
                height=100,
                key="custom_feedback_textarea"
            )

            if st.button("🔄 Request Rewrite with Custom Feedback", type="secondary", use_container_width=True, disabled=not custom_input.strip()):
                execute_human_rewrite(custom_input.strip())

        else:
            # Workflow Finished (AI mode or Approved HITL)
            is_approved = res.get("is_approved", False)
            attempts = res.get("attempt", 0)

            st.subheader("🏁 2. Workflow Completed")
            if is_approved:
                st.markdown("""
                <div class="badge badge-approved" style="font-size: 0.95rem; padding: 8px 18px;">
                    🟢 Status: Approved & Ready to Publish!
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
            else:
                st.markdown("""
                <div class="badge badge-rejected" style="font-size: 0.95rem; padding: 8px 18px;">
                    🔴 Status: Finished (Reached 3 Attempt Limit)
                </div>
                """, unsafe_allow_html=True)

            st.write(f"Total attempts made: **{attempts}**")
            if res.get("review_feedback"):
                st.info(f"**Last Reviewer Feedback:** {res.get('review_feedback')}")

        st.markdown('</div>', unsafe_allow_html=True)


with col_preview:
    st.subheader("📱 Live Post Preview")

    if st.session_state.current_result:
        res = st.session_state.current_result
        
        if "__interrupt__" in res:
            data = res["__interrupt__"][0].value
            display_draft = data.get("draft", "")
            attempt_num = data.get("attempt", 1)
            status_badge = f'<span class="badge badge-awaiting">Attempt #{attempt_num} (Under Review)</span>'
        else:
            display_draft = res.get("draft", "")
            attempt_num = res.get("attempt", 1)
            if res.get("is_approved"):
                status_badge = '<span class="badge badge-approved">Final Approved Post</span>'
            else:
                status_badge = '<span class="badge badge-rejected">Latest Draft</span>'

        # LinkedIn Feed Card
        st.markdown(f"""
        <div class="linkedin-preview-card">
            <div class="linkedin-header">
                <div class="linkedin-avatar">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="#ffffff">
                        <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
                    </svg>
                </div>
                <div style="flex-grow: 1;">
                    <div class="linkedin-author-name">LinkedIn Content Creator</div>
                    <div class="linkedin-author-title">Automated Post Studio • 🌐</div>
                </div>
                <div>{status_badge}</div>
            </div>
            <div class="linkedin-post-content">{display_draft}</div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        # Metrics KPI Grid
        words = len(display_draft.split())
        chars = len(display_draft)
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{words}</div>
                <div class="metric-lbl">Words</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{chars}</div>
                <div class="metric-lbl">Characters</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{attempt_num} / 3</div>
                <div class="metric-lbl">Attempt</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.caption("📋 Copy Raw Text:")
        st.code(display_draft, language="markdown")

        # History Expander
        if len(st.session_state.history) > 0:
            with st.expander("📜 Draft Revision History", expanded=False):
                for idx, h in enumerate(st.session_state.history, start=1):
                    st.markdown(f"**Attempt #{h['attempt']}** ({h['status'].upper()})")
                    st.text_area(f"Draft #{h['attempt']}", h['draft'], height=110, disabled=True, key=f"history_item_{idx}")
                    if h.get("feedback"):
                        st.info(f"**Feedback:** {h['feedback']}")
                    st.markdown("---")

    else:
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 48px 24px;">
            <div style="margin-bottom: 16px;">
                <svg width="56" height="56" viewBox="0 0 24 24" fill="#0a66c2">
                    <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
                </svg>
            </div>
            <h3 style="color: #94a3b8; font-weight: 600; margin-bottom: 8px;">No Draft Generated Yet</h3>
            <p style="color: #64748b; font-size: 0.92rem; margin: 0;">
                Select a Reviewer Workflow system above, enter a topic, and click <b>Generate Post Draft</b>.
            </p>
        </div>
        """, unsafe_allow_html=True)

import streamlit as st
import os
from tools.app_mcp_client import (
    research_agent_mcp_sync,
    reviewer_agent_mcp_sync,
    evaluator_agent_mcp_sync,
    generate_pdf_mcp_sync,
    generate_ppt_mcp_sync,
)
from utils.logger import log

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Agentic Research Assistant", layout="wide")

st.title("🧠 Agentic Research Assistant")

# ------------------------
# SESSION STATE INIT
# ------------------------
if "logs" not in st.session_state:
    st.session_state.logs = []

if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None

if "ppt_path" not in st.session_state:
    st.session_state.ppt_path = None

if "final_score" not in st.session_state:
    st.session_state.final_score = None

if "iterations" not in st.session_state:
    st.session_state.iterations = 0

if "sources" not in st.session_state:
    st.session_state.sources = []

# ------------------------
# INPUT
# ------------------------
topic = st.text_input("Enter research topic")

# ------------------------
# GENERATE BUTTON
# ------------------------
if st.button("Generate Report"):

    if not topic or not topic.strip():
        st.error("Please enter a research topic.")
        st.stop()

    # Reset state for new run
    st.session_state.logs = []
    st.session_state.pdf_path = None
    st.session_state.ppt_path = None
    st.session_state.sources = []

    def update(msg):
        st.session_state.logs.append(msg)
        log(msg)

    def score_vector(eval_result):
        keys = ["clarity", "structure", "depth", "usefulness"]
        return round(sum(float(eval_result.get(k, 0.0)) for k in keys), 4)

    def score_breakdown(eval_result):
        return (
            f"clarity={eval_result.get('clarity', 'NA')}, "
            f"structure={eval_result.get('structure', 'NA')}, "
            f"depth={eval_result.get('depth', 'NA')}, "
            f"usefulness={eval_result.get('usefulness', 'NA')}"
        )

    with st.spinner("Running agent..."):
        try:
            update("🔍 Searching web sources...")
            update("🌐 Scraping top articles...")
            update("🧠 Generating structured research report...")

            research_result = research_agent_mcp_sync(topic)

            if isinstance(research_result, dict):
                draft = research_result.get("report", {})
                st.session_state.sources = research_result.get("sources", [])
            else:
                draft = research_result
                st.session_state.sources = []

            update(f"🔗 Sources captured: {len(st.session_state.sources)}")

            working_version = draft
            best_version = draft
            initial_eval = evaluator_agent_mcp_sync(draft)
            best_score = initial_eval["overall"]
            best_eval = initial_eval

            if initial_eval.get("fallback_used"):
                update("⚠️ Evaluator used fallback score parsing. Scores may be less reliable.")

            update(f"📊 Initial Score: {best_score}")
            update(f"📐 Initial Breakdown: {score_breakdown(initial_eval)}")
            if initial_eval.get("issues"):
                update("🧪 Evaluator Issues:")
                for issue in initial_eval.get("issues", [])[:4]:
                    update(f"   • {issue}")

            MIN_ACCEPTABLE_SCORE = 8.0
            MAX_ATTEMPTS = 4

            if best_score >= MIN_ACCEPTABLE_SCORE:
                update("✅ Score already high → skipping improvement loop")

            else:
                for i in range(MAX_ATTEMPTS):

                    st.session_state.iterations = i + 1

                    update(f"\n🔁 Iteration {i+1}")

                    weak_areas = [
                        k for k in ["clarity", "structure", "depth", "usefulness"]
                        if float(best_eval.get(k, 0.0)) < 8.0
                    ]

                    update("🛠️ Reviewing content and applying improvements...")
                    improved, feedback = reviewer_agent_mcp_sync(working_version, focus_areas=weak_areas)

                    update("🧠 Suggested Improvements:")
                    for line in feedback.split("\n"):
                        if line.strip():
                            update(f"   • {line}")

                    eval_result = evaluator_agent_mcp_sync(improved)
                    new_score = eval_result["overall"]

                    if eval_result.get("fallback_used"):
                        update("⚠️ Evaluator used fallback score parsing for this iteration.")

                    update(f"📊 New Score: {new_score}")
                    update(f"📐 New Breakdown: {score_breakdown(eval_result)}")
                    if eval_result.get("issues"):
                        update("🧪 Evaluator Issues:")
                        for issue in eval_result.get("issues", [])[:4]:
                            update(f"   • {issue}")

                    # Improvement
                    better_overall = new_score > best_score
                    better_vector = score_vector(eval_result) > score_vector(best_eval)

                    if better_overall or (new_score == best_score and better_vector):
                        update(f"✅ Improvement accepted (+{round(new_score - best_score, 2)})")

                        best_version = improved
                        best_score = new_score
                        best_eval = eval_result

                        if best_score >= MIN_ACCEPTABLE_SCORE:
                            update("🎯 Target score reached → stopping early")
                            break

                    # No improvement → keep rewritten version and continue
                    else:
                        update("⚠️ No improvement → forcing stronger rewrite...")

                    # Continue iterating from latest rewrite, while preserving best_version
                    working_version = improved

            update(f"\n📈 Final Score: {best_score}")
            update(f"🔁 Total Iterations: {st.session_state.iterations}")

            update("📄 Generating PDF...")
            pdf_path = generate_pdf_mcp_sync(best_version, topic)

            update("📊 Generating PPT...")
            ppt_path = generate_ppt_mcp_sync(best_version, topic)

            update("✅ Done!")

            # Save outputs
            st.session_state.pdf_path = pdf_path
            st.session_state.ppt_path = ppt_path
            st.session_state.final_score = best_score

        except Exception as e:
            update(f"❌ Error: {e}")
            st.error("Report generation failed. Check logs for details.")

# ------------------------
# DISPLAY LOGS (PERSISTENT)
# ------------------------
st.subheader("📜 Logs")

log_container = st.container()
with log_container:
    for log_msg in st.session_state.logs:
        st.write(log_msg)

# ------------------------
# SOURCES
# ------------------------
if st.session_state.sources:
    st.subheader("🔗 Sources")
    for i, url in enumerate(st.session_state.sources, start=1):
        if isinstance(url, str) and url.startswith("http"):
            st.markdown(f"{i}. [{url}]({url})")

# ------------------------
# METRICS
# ------------------------
if st.session_state.final_score is not None:
    col1, col2 = st.columns(2)

    col1.metric("Final Score", st.session_state.final_score)
    col2.metric("Iterations", st.session_state.iterations)

# ------------------------
# DOWNLOAD BUTTONS (PERSISTENT)
# ------------------------
if st.session_state.pdf_path and st.session_state.ppt_path:

    st.subheader("📥 Downloads")

    col1, col2 = st.columns(2)

    with col1:
        with open(st.session_state.pdf_path, "rb") as f:
            st.download_button(
                "Download PDF",
                f,
                file_name=os.path.basename(st.session_state.pdf_path),
                key="pdf_download"
            )

    with col2:
        with open(st.session_state.ppt_path, "rb") as f:
            st.download_button(
                "Download PPT",
                f,
                file_name=os.path.basename(st.session_state.ppt_path),
                key="ppt_download"
            )
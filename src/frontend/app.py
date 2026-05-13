"""
app.py — CiteSense Streamlit entry point.

Run with:
    streamlit run src/frontend/app.py
"""

import streamlit as st

from data import mock_recommend
from components import render_paper_card

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CiteSense — Citation Recommendation",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Load CSS ─────────────────────────────────────────────────────────────────
def load_css(path: str = "src/frontend/style.css") -> None:
    try:
        with open(path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

# ─── Layout ───────────────────────────────────────────────────────────────────
main_left, main_right = st.columns([1, 2], gap="large")

# ── Left panel: query input (stays fixed) ─────────────────────────────────────
with main_left:
    st.markdown(
        """
        <div style="padding-bottom: 1.5rem;">
            <h1 style="font-size: 2.2rem; font-weight: 800; margin-bottom: 0.5rem; line-height: 1.1;">
                Cite<span class="gradient-text">Sense</span>
            </h1>
            <p style="color: var(--text-secondary); font-size: 0.85rem; line-height: 1.5;">
                Minimalist citation discovery.
                Enter your research topic or abstract to find relevant literature.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="input-label">📄 Query</div>', unsafe_allow_html=True)
    query_text = st.text_area(
        "Query",
        placeholder="e.g. We propose a new transformer architecture for citation recommendation...",
        height=200,
        label_visibility="collapsed",
        key="query_input",
    )

    st.markdown(
        '<div class="input-label" style="margin-top: 2rem;">🗓️ Year Range</div>',
        unsafe_allow_html=True,
    )
    year_range = st.slider(
        "Publication year",
        min_value=2015,
        max_value=2026,
        value=(2017, 2024),
        step=1,
        label_visibility="collapsed",
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        search_btn = st.button("Search", type="primary", use_container_width=True)
    with col_btn2:
        clear_btn = st.button("Clear", use_container_width=True)

    if clear_btn:
        st.session_state["query_input"] = ""
        st.session_state.pop("results", None)
        st.rerun()

    # ── Search execution ──────────────────────────────────────────────────────
    if search_btn:
        if not query_text.strip():
            st.warning("⚠️ Please enter a query.")
        else:
            with st.spinner("🔎 Analysing..."):
                results = mock_recommend(query_text, year_range, top_k=10)
            st.session_state["results"] = results
            st.session_state["query_used"] = query_text

# ── Right panel: scrollable results ───────────────────────────────────────────
with main_right:
    if "results" in st.session_state:
        results = st.session_state["results"]

        if not results:
            st.markdown(
                '<div class="no-results">😔 No papers matched your filters.</div>',
                unsafe_allow_html=True,
            )
        else:
            query_preview = st.session_state["query_used"][:80]
            st.markdown(
                f"""
                <div class="results-header">
                    <span class="results-count">{len(results)} papers found</span>
                    <span class="results-query">for: <em>"{query_preview}…"</em></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            for i, paper in enumerate(results):
                render_paper_card(paper, i)
    else:
        st.markdown(
            """
            <div style="height:100%;min-height:60vh;display:flex;flex-direction:column;
                        align-items:center;justify-content:center;color:var(--text-muted);">
                <div style="font-size:3rem;margin-bottom:1rem;">📚</div>
                <h3 style="color:var(--text-secondary);margin-bottom:0.5rem;">Ready to discover</h3>
                <p>Your recommended papers and summaries will appear here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

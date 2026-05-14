"""
components.py — Reusable Streamlit UI components for CiteSense.

Exports
-------
paper_detail_dialog  :  @st.dialog popout with full paper details
render_paper_card    :  paper widget using st.container(border=True)
"""

import time
import streamlit as st
from utils import score_color, score_label, format_authors, apa_citation


# ─── Mock Summarization ──────────────────────────────────────────────────────

def _mock_summarize(paper: dict) -> str:
    """
    Placeholder summarization — replace with a real LLM call.
    Returns a short summary of the paper.
    """
    time.sleep(1.2)  # Simulate API latency
    # Return a mock summary based on the paper data
    return (
        f"This paper introduces {paper['title'].split(':')[0].lower()} and presents "
        f"key contributions in the area of {', '.join(paper['keywords'][:2])}. "
        f"Published at {paper['venue']} in {paper['year']}, it has been cited "
        f"{paper['citations']:,} times, demonstrating significant impact in the field. "
        f"The authors propose novel methods that address limitations of prior work."
    )


# ─── Detail Dialog ────────────────────────────────────────────────────────────

@st.dialog("📄 Paper Details", width="large")
def paper_detail_dialog() -> None:
    """Full-detail modal dialog for a single paper."""
    paper = st.session_state.get("_dialog_paper")
    if paper is None:
        return

    sc = paper["score"]
    color = score_color(sc)
    label = score_label(sc)

    st.markdown(f"### [{paper['title']}]({paper['url']})")
    st.markdown(
        f'<span style="display:inline-block;background:{color}15;border:1px solid {color}44;'
        f'color:{color};border-radius:999px;padding:0.18rem 0.7rem;font-size:0.72rem;'
        f'font-weight:700;">{sc:.0%} — {label}</span>',
        unsafe_allow_html=True,
    )
    st.divider()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📅 Year",      paper["year"])
    m2.metric("📍 Venue",     paper["venue"])
    m3.metric("🔗 Citations", f"{paper['citations']:,}")
    m4.metric("🎯 Score",     f"{sc:.0%}")
    st.caption("**Authors:** " + ", ".join(paper["authors"]))
    st.divider()

    st.markdown("**Abstract**")
    st.markdown(paper["abstract"])

    st.markdown("**Keywords**")
    st.markdown("  ".join(f"`{kw}`" for kw in paper["keywords"]))
    st.divider()

    st.markdown("**APA Citation**")
    st.code(apa_citation(paper), language=None)


# ─── Paper Widget Card ───────────────────────────────────────────────────────

def render_paper_card(paper: dict, index: int) -> None:
    """
    Render one paper as a self-contained widget.

    Uses st.container(border=True) for the card, with:
    - Rank + score badge
    - Title, authors, meta
    - Keywords
    - Collapsible abstract
    - Summarize button with inline summary display
    - Like + Details buttons
    """
    sc    = paper["score"]
    color = score_color(sc)
    label = score_label(sc)
    authors_display = format_authors(paper["authors"])

    # ── Session state keys
    like_key       = f"like_{paper['id']}"
    like_count_key = f"like_count_{paper['id']}"
    summary_key    = f"summary_{paper['id']}"

    if like_key not in st.session_state:
        st.session_state[like_key] = False
    if like_count_key not in st.session_state:
        st.session_state[like_count_key] = 0

    liked      = st.session_state[like_key]
    like_count = st.session_state[like_count_key]

    # ── Widget container
    with st.container(border=True):
        # Rank + score badge
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.5rem;">'
            f'<span style="font-size:0.64rem;font-weight:800;color:var(--text-muted);'
            f'background:rgba(255,255,255,0.05);padding:0.1rem 0.4rem;border-radius:5px;">'
            f'#{index + 1}</span>'
            f'<span style="font-size:0.68rem;font-weight:700;color:{color};'
            f'background:{color}15;border:1px solid {color}44;'
            f'border-radius:999px;padding:0.1rem 0.55rem;">'
            f'{sc:.0%} · {label}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Title
        st.markdown(f"**[{paper['title']}]({paper['url']})**")

        # Meta
        st.caption(
            f"👤 {authors_display}  ·  📍 {paper['venue']}  ·  "
            f"📅 {paper['year']}  ·  🔗 {paper['citations']:,} cites"
        )

        # Keywords
        st.markdown("  ".join(f"`{kw}`" for kw in paper["keywords"]))

        # Abstract (collapsible)
        with st.expander("Abstract", expanded=False):
            st.markdown(paper["abstract"])

        # ── Summarize section
        sum_col, like_col, detail_col, _ = st.columns([1.5, 1.3, 1.2, 2.0])

        with sum_col:
            if st.button(
                "✨ Summarize" if summary_key not in st.session_state else "🔄 Re-summarize",
                key=f"sum_{paper['id']}_btn",
                use_container_width=True,
            ):
                with st.spinner("Summarizing..."):
                    summary = _mock_summarize(paper)
                st.session_state[summary_key] = summary
                st.rerun()

        with like_col:
            like_txt = f"💖 Liked · {like_count}" if liked else f"❤️ Like · {like_count}"
            if st.button(like_txt, key=f"like_{paper['id']}_btn", use_container_width=True):
                if liked:
                    st.session_state[like_key] = False
                    st.session_state[like_count_key] = max(0, like_count - 1)
                else:
                    st.session_state[like_key] = True
                    st.session_state[like_count_key] = like_count + 1
                st.rerun()

        with detail_col:
            if st.button("📄 Details", key=f"details_{paper['id']}", use_container_width=True):
                st.session_state["_dialog_paper"] = paper
                paper_detail_dialog()

        # ── Display summary if available
        if summary_key in st.session_state:
            st.markdown(
                f'<div class="summary-box">'
                f'<strong>✨ AI Summary</strong><br>'
                f'{st.session_state[summary_key]}'
                f'</div>',
                unsafe_allow_html=True,
            )

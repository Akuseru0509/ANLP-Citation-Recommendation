import time
import streamlit as st
from utils.utils import score_color, score_label

def render_paper_card(paper: dict, index: int) -> None:
    sc = paper["score"]
    color = score_color(sc)
    label = score_label(sc)

    like_key = f"like_{paper['id']}"
    like_count_key = f"like_count_{paper['id']}"

    st.session_state.setdefault(like_key, False)
    st.session_state.setdefault(like_count_key, 0)

    liked = st.session_state[like_key]
    like_count = st.session_state[like_count_key]

    with st.container(border=True):
        top_col1, top_col2 = st.columns([0.8, 0.2])
        
        with top_col1:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">'
                f'<span style="font-size:0.64rem;font-weight:800;color:var(--text-muted);'
                f'background:rgba(255,255,255,0.05);padding:0.1rem 0.4rem;border-radius:5px;">'
                f'#{index + 1}</span>'
                f'<span style="font-size:0.68rem;font-weight:700;color:{color};'
                f'background:{color}15;border:1px solid {color}44;'
                f'border-radius:999px;padding:0.1rem 0.55rem;">'
                f'{sc:.2f}% · {label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**{paper['metadata'].get('title')}**")
            
        with top_col2:
            like_txt = f"Liked: {like_count}" if liked else f"Like: {like_count}"
            if st.button(like_txt, key=f"like_{paper['id']}_btn", use_container_width=True):
                if liked:
                    st.session_state[like_key] = False
                    st.session_state[like_count_key] = max(0, like_count - 1)
                else:
                    st.session_state[like_key] = True
                    st.session_state[like_count_key] = like_count + 1
                st.rerun()

        author_col, year_col = st.columns([0.8, 0.2])

        with author_col:
            st.caption(f"Authors: {paper['metadata'].get('authors')}", text_alignment="left")

        with year_col:
            st.caption(f"Year: {paper['metadata'].get('year')}", text_alignment="right")

        summary = paper["summary"]

        if summary:
            st.markdown("### Summary")
            st.write(summary)
        else:
            st.info("No summary available.")

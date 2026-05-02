"""
VibeFinder AI — Streamlit web interface.

Usage:
    streamlit run src/app.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from src.recommender import load_songs, recommend_songs
from src.agent import run_agent

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="VibeFinder AI",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* Dark background throughout */
    .stApp { background-color: #0d1117; }

    /* Song cards */
    .song-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    .song-rank {
        font-size: 11px;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 2px;
    }
    .song-title {
        font-size: 17px;
        font-weight: 700;
        color: #e6edf3;
        margin-bottom: 2px;
    }
    .song-artist {
        font-size: 13px;
        color: #8b949e;
        margin-bottom: 6px;
    }
    .song-tags {
        font-size: 12px;
        color: #58a6ff;
    }
    .song-reason {
        font-size: 12px;
        color: #8b949e;
        margin-top: 6px;
        font-style: italic;
    }
    .song-score {
        font-size: 12px;
        color: #3fb950;
        font-weight: 600;
    }

    /* Interpretation card */
    .interp-card {
        background: #1f2937;
        border: 1px solid #1f6feb;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 16px;
    }

    /* Explanation box */
    .explanation-box {
        background: #161b22;
        border-left: 3px solid #58a6ff;
        border-radius: 0 8px 8px 0;
        padding: 14px 18px;
        margin-top: 4px;
        font-size: 15px;
        color: #e6edf3;
        line-height: 1.6;
    }

    /* Confidence bar color override */
    .stProgress > div > div { background-color: #58a6ff; }

    /* Hide Streamlit chrome */
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_songs():
    return load_songs(str(Path(__file__).parent.parent / "data" / "songs.csv"))

songs = get_songs()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎵 VibeFinder AI")
    st.caption("Natural language music recommendations\npowered by Claude")
    st.divider()

    st.markdown("### API Key")
    env_key = os.getenv("ANTHROPIC_API_KEY", "")
    api_key_input = st.text_input(
        "Anthropic API Key",
        value=env_key,
        type="password",
        placeholder="sk-ant-...",
        help="Get yours at console.anthropic.com",
    )
    if api_key_input:
        os.environ["ANTHROPIC_API_KEY"] = api_key_input

    st.divider()
    st.markdown("### Settings")
    k = st.slider("Results to show", min_value=1, max_value=10, value=5)
    show_steps = st.checkbox("Show agent steps", value=False)

    st.divider()
    st.markdown(f"**Catalog**: {len(songs)} songs")
    genres = sorted({s["genre"] for s in songs})
    st.caption("Genres: " + ", ".join(genres))

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_ai, tab_classic = st.tabs(["🤖  AI Mode", "🎛️  Classic Mode"])

# ═══════════════════════════════════════════════════════════════════════════════
# Tab 1 — AI Mode
# ═══════════════════════════════════════════════════════════════════════════════

with tab_ai:
    st.markdown("## Tell me what you're in the mood for")
    st.caption("Describe anything — an activity, a feeling, a time of day. Claude interprets it.")

    query = st.text_input(
        label="query",
        label_visibility="collapsed",
        placeholder="e.g.  something chill for late night coding  /  pump-up gym music  /  rainy Sunday vibes",
        key="ai_query",
    )

    col_btn, col_hint = st.columns([1, 6])
    with col_btn:
        go = st.button("Find music", type="primary", use_container_width=True)

    if go and query.strip():
        if not os.getenv("ANTHROPIC_API_KEY"):
            st.error("Add your Anthropic API key in the sidebar to use AI mode.")
        elif len(query) > 500:
            st.warning("Query too long — please keep it under 500 characters.")
        else:
            with st.spinner("Claude is thinking..."):
                try:
                    result = run_agent(query.strip(), songs, k=k)
                except EnvironmentError as e:
                    st.error(str(e))
                    st.stop()
                except Exception as e:
                    st.error(f"Something went wrong: {e}")
                    st.stop()

            # ── Interpretation ────────────────────────────────────────────
            conf = result["confidence"]
            prefs = result["preferences"]

            conf_color = "#3fb950" if conf >= 0.75 else ("#d29922" if conf >= 0.5 else "#f85149")
            st.markdown(
                f"""
                <div class="interp-card">
                    <div style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">
                        Claude's interpretation
                    </div>
                    <div style="display:flex;gap:24px;flex-wrap:wrap;align-items:center">
                        <span style="color:#e6edf3;font-size:14px">
                            <b>Genre</b>&nbsp; <span style="color:#58a6ff">{prefs['genre']}</span>
                        </span>
                        <span style="color:#e6edf3;font-size:14px">
                            <b>Mood</b>&nbsp; <span style="color:#58a6ff">{prefs['mood']}</span>
                        </span>
                        <span style="color:#e6edf3;font-size:14px">
                            <b>Energy</b>&nbsp; <span style="color:#58a6ff">{prefs['energy']:.0%}</span>
                        </span>
                        <span style="color:#e6edf3;font-size:14px">
                            <b>Tempo</b>&nbsp; <span style="color:#58a6ff">{prefs['tempo_bpm']:.0f} BPM</span>
                        </span>
                        <span style="color:{conf_color};font-size:14px;font-weight:700">
                            {conf:.0%} confident
                        </span>
                    </div>
                    {"<div style='margin-top:8px;font-size:12px;color:#8b949e;font-style:italic'>" + result.get("reasoning","") + "</div>" if result.get("reasoning") else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )

            if conf < 0.6:
                st.warning("Low confidence — the interpretation may not match your intent. Try rephrasing.")

            # ── Agent steps ───────────────────────────────────────────────
            if show_steps and result.get("steps"):
                with st.expander("Agent reasoning steps"):
                    for step in result["steps"]:
                        st.markdown(f"**Step {step['step']}** — `{step['action']}`")
                        st.json(step["result"])

            # ── Song results ──────────────────────────────────────────────
            recs = result["recommendations"]
            if not recs:
                st.info("No matching songs found. Try a different query.")
            else:
                st.markdown(f"### Top {len(recs)} picks")
                col_a, col_b = st.columns(2)
                for i, rec in enumerate(recs):
                    col = col_a if i % 2 == 0 else col_b
                    with col:
                        st.markdown(
                            f"""
                            <div class="song-card">
                                <div class="song-rank">#{i+1}</div>
                                <div class="song-title">{rec['title']}</div>
                                <div class="song-artist">{rec['artist']}</div>
                                <div class="song-tags">{rec['genre']} &nbsp;·&nbsp; {rec['mood']}</div>
                                <div class="song-reason">{rec['explanation']}</div>
                                <div class="song-score">Score: {rec['score']:.3f}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            # ── Claude explanation ────────────────────────────────────────
            st.markdown("### Claude says")
            st.markdown(
                f'<div class="explanation-box">{result["explanation"]}</div>',
                unsafe_allow_html=True,
            )

    elif go and not query.strip():
        st.warning("Type something first!")

# ═══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Classic Mode
# ═══════════════════════════════════════════════════════════════════════════════

with tab_classic:
    st.markdown("## Classic rule-based recommender")
    st.caption("Set your audio preferences manually — no API key needed.")

    col1, col2 = st.columns(2)

    with col1:
        genre_opts = sorted({s["genre"] for s in songs})
        mood_opts = sorted({s["mood"] for s in songs})
        sel_genre = st.selectbox("Preferred genre", genre_opts)
        sel_mood = st.selectbox("Preferred mood", mood_opts)

    with col2:
        sel_energy = st.slider("Energy", 0.0, 1.0, 0.7, 0.01)
        sel_tempo = st.slider("Tempo (BPM)", 60, 180, 100)
        sel_valence = st.slider("Positivity (valence)", 0.0, 1.0, 0.6, 0.01)

    col3, col4 = st.columns(2)
    with col3:
        sel_dance = st.slider("Danceability", 0.0, 1.0, 0.6, 0.01)
    with col4:
        sel_acoustic = st.slider("Acousticness", 0.0, 1.0, 0.4, 0.01)

    if st.button("Get recommendations", type="primary"):
        user_prefs = {
            "genre": sel_genre, "mood": sel_mood,
            "energy": sel_energy, "tempo_bpm": float(sel_tempo),
            "valence": sel_valence, "danceability": sel_dance,
            "acousticness": sel_acoustic,
        }
        recs = recommend_songs(user_prefs, songs, k=k)

        st.markdown(f"### Top {len(recs)} results")
        col_a, col_b = st.columns(2)
        for i, (song, score, expl) in enumerate(recs):
            col = col_a if i % 2 == 0 else col_b
            with col:
                st.markdown(
                    f"""
                    <div class="song-card">
                        <div class="song-rank">#{i+1}</div>
                        <div class="song-title">{song['title']}</div>
                        <div class="song-artist">{song['artist']}</div>
                        <div class="song-tags">{song['genre']} &nbsp;·&nbsp; {song['mood']} &nbsp;·&nbsp; energy {song['energy']:.0%}</div>
                        <div class="song-reason">{expl}</div>
                        <div class="song-score">Score: {score:.3f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

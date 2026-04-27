import streamlit as st
import os
from dotenv import load_dotenv
from auth import get_auth_url, handle_callback, get_spotify_client, is_logged_in, logout
from spotify import get_user_profile, get_all_playlists, get_recommendations, create_spotify_playlist
from agent import build_mood_playlist, score_recommendations

load_dotenv()

st.set_page_config(
    page_title="Musara",
    page_icon="🎵",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0a;
    color: #ffffff;
}
.stApp { background-color: #0a0a0a; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container {
    padding: 3rem 4rem;
    max-width: 1200px;
}

h1 {
    font-size: 3rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    letter-spacing: -0.03em !important;
    margin-bottom: 0 !important;
}

h3 {
    font-size: 1rem !important;
    font-weight: 300 !important;
    color: #666666 !important;
    margin-top: 0.25rem !important;
}

.spotify-btn {
    background: #1DB954;
    color: white;
    padding: 14px 32px;
    border-radius: 50px;
    font-weight: 600;
    font-size: 1rem;
    text-decoration: none;
    display: inline-block;
    margin-top: 1rem;
    letter-spacing: 0.02em;
}

.mood-card {
    background: #141414;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    cursor: pointer;
    text-align: center;
}

.mood-card-selected {
    background: #0d2818;
    border: 2px solid #1DB954;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    text-align: center;
}

.mood-emoji { font-size: 2rem; margin-bottom: 0.5rem; }
.mood-label { font-size: 0.9rem; font-weight: 600; color: #ffffff; }

.track-card {
    background: #141414;
    border: 1px solid #1e1e1e;
    border-radius: 10px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}

.track-num {
    font-size: 0.75rem;
    color: #444;
    font-weight: 600;
    min-width: 20px;
    text-align: right;
}

.track-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: #ffffff;
}

.track-artist {
    font-size: 0.8rem;
    color: #888;
}

.playlist-header {
    background: linear-gradient(135deg, #0d2818, #1a1a2e);
    border: 1px solid #1DB954;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
}

.playlist-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.25rem;
}

.playlist-desc {
    font-size: 0.95rem;
    color: #888;
    margin-bottom: 1rem;
}

.playlist-meta {
    font-size: 0.8rem;
    color: #1DB954;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.rec-card {
    background: #141414;
    border: 1px solid #1e1e1e;
    border-radius: 10px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.5rem;
}

.section-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: #1DB954;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 0.75rem;
}

.user-badge {
    background: #141414;
    border: 1px solid #222;
    border-radius: 50px;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    color: #aaa;
    display: inline-block;
}

hr { border-color: #1e1e1e !important; margin: 2rem 0 !important; }

.stButton > button {
    background: #1DB954 !important;
    color: #000 !important;
    border: none !important;
    border-radius: 50px !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 2rem !important;
}

.stButton > button:hover {
    background: #1ed760 !important;
}

.stTextInput > div > div > input {
    background: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-size: 0.95rem !important;
}

.stMultiSelect > div {
    background: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}

.stCheckbox label { color: #aaaaaa !important; }

[data-testid="column"] { padding: 0 0.4rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Handle OAuth callback ──────────────────────────────────────────────────
params = st.query_params
if "code" in params and not is_logged_in():
    code = params["code"]
    try:
        handle_callback(code)
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

# ── Not logged in ──────────────────────────────────────────────────────────
if not is_logged_in():
    st.markdown('<h1>Musara</h1>', unsafe_allow_html=True)
    st.markdown('<h3>Your mood. Your music. Curated by AI.</h3>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div style="margin-top:2rem;">
            <div style="font-size:0.65rem; font-weight:700; color:#1DB954;
            text-transform:uppercase; letter-spacing:0.15em; margin-bottom:1rem;">
            How it works</div>
            <div style="font-size:1rem; color:#888; line-height:2;">
            1 → Connect your Spotify account<br>
            2 → Pick your current mood<br>
            3 → AI scans your playlists and builds the perfect mix<br>
            4 → Discover new songs that match your vibe<br>
            5 → Export directly to your Spotify
            </div>
        </div>
        """, unsafe_allow_html=True)

        auth_url = get_auth_url()
        st.markdown(
            f'<a href="{auth_url}" class="spotify-btn">🎵 Connect with Spotify</a>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("""
        <div style="background:#141414; border:1px solid #222; border-radius:16px;
        padding:2rem; margin-top:2rem; text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">🎵</div>
            <div style="font-size:1rem; font-weight:600; color:#fff; margin-bottom:0.5rem;">
            Mood-powered playlists</div>
            <div style="font-size:0.85rem; color:#666; line-height:1.75;">
            Musara reads your existing Spotify library and uses Claude AI to build
            a perfectly curated playlist for how you feel right now.
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ── Logged in ──────────────────────────────────────────────────────────────
user = get_user_profile()

col_title, col_user = st.columns([4, 1])
with col_title:
    st.markdown('<h1>Musara</h1>', unsafe_allow_html=True)
    st.markdown('<h3>Your mood. Your music. Curated by AI.</h3>', unsafe_allow_html=True)
with col_user:
    if user:
        st.markdown(
            f'<div class="user-badge" style="margin-top:2rem;">👤 {user["display_name"]}</div>',
            unsafe_allow_html=True
        )
        if st.button("Log out"):
            logout()
            st.rerun()

st.markdown('<hr>', unsafe_allow_html=True)

# ── Step 1: Pick mood ──────────────────────────────────────────────────────
st.markdown('<div class="section-label">Step 01 — How are you feeling?</div>',
            unsafe_allow_html=True)

MOODS = [
    {"emoji": "🔥", "label": "Hype",      "desc": "High energy, pumped up"},
    {"emoji": "😌", "label": "Chill",     "desc": "Relaxed, laid back"},
    {"emoji": "🧠", "label": "Focus",     "desc": "Deep work, concentration"},
    {"emoji": "💔", "label": "Sad",       "desc": "Melancholic, reflective"},
    {"emoji": "🌅", "label": "Nostalgic", "desc": "Warm memories, throwbacks"},
    {"emoji": "💜", "label": "Romantic",  "desc": "Love, soft energy"},
]

if "selected_mood" not in st.session_state:
    st.session_state["selected_mood"] = None

cols = st.columns(6)
for i, mood in enumerate(MOODS):
    with cols[i]:
        is_selected = st.session_state["selected_mood"] == mood["label"]
        card_class = "mood-card-selected" if is_selected else "mood-card"
        st.markdown(
            f'<div class="{card_class}">'
            f'<div class="mood-emoji">{mood["emoji"]}</div>'
            f'<div class="mood-label">{mood["label"]}</div>'
            f'<div style="font-size:0.72rem; color:#666; margin-top:0.25rem;">'
            f'{mood["desc"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        if st.button(mood["label"], key=f"mood_{i}"):
            st.session_state["selected_mood"] = mood["label"]
            st.rerun()

st.markdown('<br>', unsafe_allow_html=True)
custom_mood = st.text_input(
    "Or describe your mood in your own words",
    placeholder="e.g. driving at night feeling reflective, pre-game hype, Sunday morning coffee..."
)

active_mood = custom_mood.strip() if custom_mood.strip() else st.session_state.get("selected_mood")

st.markdown('<hr>', unsafe_allow_html=True)

# ── Step 2: Select playlists ───────────────────────────────────────────────
st.markdown('<div class="section-label">Step 02 — Choose playlists to pull from</div>',
            unsafe_allow_html=True)

if "playlists" not in st.session_state:
    with st.spinner("Loading your playlists..."):
        st.session_state["playlists"] = get_all_playlists()

playlists = st.session_state["playlists"]

if not playlists:
    st.warning("No playlists found. Make sure you have playlists created in your Spotify account.")
    st.stop()

playlist_options = {p["name"]: p["id"] for p in playlists}

selected_names = st.multiselect(
    "Select playlists",
    options=list(playlist_options.keys()),
    default=None,
    placeholder="Choose your playlists...",
    help="Select playlists you created in Spotify"
)

selected_ids = [playlist_options[name] for name in selected_names] if selected_names else []

st.markdown('<hr>', unsafe_allow_html=True)

# ── Step 3: Build ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Step 03 — Build your playlist</div>',
            unsafe_allow_html=True)

build_btn = st.button("✨ Build Mood Playlist", type="primary")

if build_btn:
    if not active_mood:
        st.warning("Please select or type a mood first.")
        st.stop()
    if not selected_ids:
        st.warning("Please select at least one playlist.")
        st.stop()

    with st.spinner("Pulling tracks from your playlists..."):
        sp = get_spotify_client()
        all_tracks = []
        seen_ids = set()
        for pid in selected_ids:
            try:
                results = sp.playlist_tracks(pid, limit=50)
                count = 0
                while results and count < 150:
                    for item in results["items"]:
                        if count >= 150:
                            break
                        if not item:
                            continue
                        track = item.get("track") or item.get("item")
                        if not track or not track.get("id"):
                            continue
                        if track["id"] not in seen_ids:
                            seen_ids.add(track["id"])
                            all_tracks.append({
                                "id": track["id"],
                                "name": track["name"],
                                "artist": track["artists"][0]["name"] if track.get("artists") else "Unknown",
                                "album": track["album"]["name"] if track.get("album") else "Unknown",
                                "image": track["album"]["images"][0]["url"] if track.get("album") and track["album"].get("images") else None,
                                "uri": track["uri"],
                                "preview_url": track.get("preview_url"),
                                "popularity": track.get("popularity", 0)
                            })
                            count += 1
                    if results["next"] and count < 150:
                        results = sp.next(results)
                    else:
                        break
            except Exception as e:
                st.warning(f"Skipped a playlist: {e}")
                continue

    if not all_tracks:
        st.error("No tracks found. Try selecting different playlists.")
        st.stop()

    with st.spinner(f"Claude is curating your {active_mood} playlist..."):
        result = build_mood_playlist(all_tracks, active_mood)

    selected_indices = result.get("selected_indices", [])
    playlist_tracks = []
    for idx in selected_indices:
        if 0 <= idx < len(all_tracks):
            playlist_tracks.append(all_tracks[idx])

    if not playlist_tracks:
        playlist_tracks = all_tracks[:20]

    st.session_state["playlist_tracks"] = playlist_tracks
    st.session_state["playlist_name"]   = result.get("playlist_name", f"{active_mood} Mix")
    st.session_state["playlist_desc"]   = result.get("playlist_description", "")
    st.session_state["mood_summary"]    = result.get("mood_summary", "")
    st.session_state["active_mood"]     = active_mood
    st.session_state["all_tracks"]      = all_tracks
    st.session_state["playlist_built"]  = True
    st.session_state["recommendations"] = []
    st.session_state["selected_recs"]   = []

# ── Show playlist ──────────────────────────────────────────────────────────
if st.session_state.get("playlist_built"):
    playlist_tracks = st.session_state["playlist_tracks"]
    playlist_name   = st.session_state["playlist_name"]
    playlist_desc   = st.session_state["playlist_desc"]
    mood_summary    = st.session_state["mood_summary"]
    active_mood     = st.session_state["active_mood"]

    st.markdown(
        f'<div class="playlist-header">'
        f'<div class="playlist-meta">Generated playlist · {active_mood}</div>'
        f'<div class="playlist-title">{playlist_name}</div>'
        f'<div class="playlist-desc">{playlist_desc}</div>'
        f'<div style="font-size:0.85rem; color:#aaa; line-height:1.75;">'
        f'{mood_summary}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    col_tracks, col_actions = st.columns([3, 1])

    with col_tracks:
        st.markdown('<div class="section-label">Tracks</div>', unsafe_allow_html=True)
        for i, track in enumerate(playlist_tracks):
            img_html = ""
            if track.get("image"):
                img_html = (
                    f'<img src="{track["image"]}" width="40" height="40" '
                    f'style="border-radius:4px; flex-shrink:0;"/>'
                )
            st.markdown(
                f'<div class="track-card">'
                f'{img_html}'
                f'<div class="track-num">{i+1}</div>'
                f'<div style="flex:1;">'
                f'<div class="track-name">{track["name"]}</div>'
                f'<div class="track-artist">{track["artist"]} · {track["album"]}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    with col_actions:
        st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.85rem; color:#888; margin-bottom:1rem; line-height:1.75;">'
            f'{len(playlist_tracks)} tracks ready to export to your Spotify account.</div>',
            unsafe_allow_html=True
        )

        if st.button("🎵 Export to Spotify"):
            with st.spinner("Creating playlist in Spotify..."):
                track_uris = [t["uri"] for t in playlist_tracks]
                exported = create_spotify_playlist(
                    name=playlist_name,
                    description=f"Created by Musara · Mood: {active_mood}",
                    track_uris=track_uris
                )
            if exported:
                st.success("Playlist created!")
                st.markdown(
                    f'<a href="{exported["url"]}" target="_blank" class="spotify-btn">'
                    f'▶ Open in Spotify</a>',
                    unsafe_allow_html=True
                )
            else:
                st.error("Something went wrong exporting.")

        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Discover new tracks</div>',
                    unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.85rem; color:#888; margin-bottom:1rem; line-height:1.75;">'
            'Get AI-curated song recommendations based on your playlist.</div>',
            unsafe_allow_html=True
        )

        if st.button("🔍 Get Recommendations"):
            with st.spinner("Finding songs you might love..."):
                seed_ids = [t["id"] for t in playlist_tracks[:5]]
                raw_recs = get_recommendations(seed_ids, active_mood)
                if raw_recs:
                    scored = score_recommendations(
                        raw_recs, active_mood, playlist_tracks
                    )
                    selected_rec_indices = scored.get("selected_indices", [])
                    final_recs = []
                    for idx in selected_rec_indices:
                        if 0 <= idx < len(raw_recs):
                            final_recs.append(raw_recs[idx])
                    st.session_state["recommendations"] = final_recs
                    st.session_state["rec_reasoning"]   = scored.get("reasoning", "")

    # ── Recommendations ────────────────────────────────────────────────────
    if st.session_state.get("recommendations"):
        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Recommended tracks</div>',
                    unsafe_allow_html=True)

        rec_reasoning = st.session_state.get("rec_reasoning", "")
        if rec_reasoning:
            st.markdown(
                f'<div style="font-size:0.85rem; color:#888; margin-bottom:1.5rem;">'
                f'{rec_reasoning}</div>',
                unsafe_allow_html=True
            )

        recs = st.session_state["recommendations"]
        selected_recs = st.session_state.get("selected_recs", [])

        for i, track in enumerate(recs):
            col_rec, col_add = st.columns([5, 1])
            with col_rec:
                img_html = ""
                if track.get("image"):
                    img_html = (
                        f'<img src="{track["image"]}" width="36" height="36" '
                        f'style="border-radius:4px; flex-shrink:0;"/>'
                    )
                st.markdown(
                    f'<div class="rec-card" style="display:flex; align-items:center; gap:1rem;">'
                    f'{img_html}'
                    f'<div>'
                    f'<div class="track-name">{track["name"]}</div>'
                    f'<div class="track-artist">{track["artist"]} · {track["album"]}</div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col_add:
                is_added = track["id"] in [r["id"] for r in selected_recs]
                if is_added:
                    st.markdown(
                        '<div style="color:#1DB954; font-size:0.85rem; '
                        'padding-top:0.75rem; text-align:center;">✓ Added</div>',
                        unsafe_allow_html=True
                    )
                else:
                    if st.button("+ Add", key=f"add_rec_{i}"):
                        if "selected_recs" not in st.session_state:
                            st.session_state["selected_recs"] = []
                        st.session_state["selected_recs"].append(track)
                        st.session_state["playlist_tracks"].append(track)
                        st.rerun()

        if selected_recs:
            st.markdown('<br>', unsafe_allow_html=True)
            if st.button("🎵 Export Updated Playlist to Spotify"):
                with st.spinner("Exporting updated playlist..."):
                    all_uris = [t["uri"] for t in st.session_state["playlist_tracks"]]
                    exported = create_spotify_playlist(
                        name=f"{playlist_name} (Updated)",
                        description=f"Created by Musara · Mood: {active_mood} · With recommendations",
                        track_uris=all_uris
                    )
                if exported:
                    st.success("Updated playlist created!")
                    st.markdown(
                        f'<a href="{exported["url"]}" target="_blank" class="spotify-btn">'
                        f'▶ Open in Spotify</a>',
                        unsafe_allow_html=True
                    )
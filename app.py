import streamlit as st
import os
from dotenv import load_dotenv
from auth import get_auth_url, handle_callback, get_spotify_client, is_logged_in, logout
from spotify import get_user_profile, get_all_playlists, create_spotify_playlist, enrich_tracks_with_audio_features
from agent import build_mood_playlist

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

.audio-bar {
    display: flex;
    gap: 4px;
    align-items: center;
    margin-top: 4px;
}

.audio-tag {
    font-size: 0.62rem;
    color: #333;
    background: #1a1a1a;
    border-radius: 3px;
    padding: 1px 5px;
    font-family: monospace;
}

.audio-tag.high { color: #1DB954; }
.audio-tag.mid  { color: #888; }
.audio-tag.low  { color: #444; }

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

.pref-card {
    background: #141414;
    border: 1px solid #1e1e1e;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
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

.stSelectbox > div > div {
    background: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}

.stMultiSelect > div {
    background: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}

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
            3 → Set your preferences — activity, energy, language<br>
            4 → AI scans your playlists using real audio data<br>
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
            Musara uses Spotify audio features — energy, valence, BPM, danceability —
            to match tracks to your exact mood and preferences.
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

# ── Step 2: Preferences ────────────────────────────────────────────────────
st.markdown('<div class="section-label">Step 02 — Set your preferences</div>',
            unsafe_allow_html=True)

st.markdown('<div class="pref-card">', unsafe_allow_html=True)

pref_col1, pref_col2 = st.columns(2)

with pref_col1:
    activity = st.selectbox(
        "What are you doing?",
        options=["", "Driving", "Working out / Gym", "Studying / Focus",
                 "Party / Going out", "Cooking", "Relaxing at home",
                 "Running", "Working", "Getting ready"],
        index=0
    )
    language = st.selectbox(
        "Language preference",
        options=["No preference", "Spanish", "English",
                 "Mixed (Spanish + English)", "Portuguese", "French"],
        index=0
    )
    include_artists = st.text_input(
        "Artists to prioritize",
        placeholder="e.g. Bad Bunny, J Balvin, Drake"
    )

with pref_col2:
    energy = st.slider(
        "Energy level",
        min_value=1,
        max_value=10,
        value=5
    )
    energy_label = (
        "🔇 Very calm"    if energy <= 2 else
        "🎵 Laid back"    if energy <= 4 else
        "🎶 Moderate"     if energy <= 6 else
        "🔥 High energy"  if energy <= 8 else
        "⚡ Maximum energy"
    )
    st.markdown(
        f'<div style="font-size:0.75rem; color:#555; margin-top:-0.5rem; '
        f'margin-bottom:1rem;">{energy_label}</div>',
        unsafe_allow_html=True
    )
    exclude_artists = st.text_input(
        "Artists to exclude",
        placeholder="e.g. Reggaeton artists, EDM"
    )
    extra_prefs = st.text_input(
        "Anything else?",
        placeholder="e.g. only 2000s throwbacks, no explicit lyrics..."
    )

st.markdown('</div>', unsafe_allow_html=True)

preferences = {
    "activity":        activity,
    "energy":          str(energy),
    "language":        language if language != "No preference" else "",
    "include_artists": include_artists,
    "exclude_artists": exclude_artists,
    "extra":           extra_prefs
}

st.markdown('<hr>', unsafe_allow_html=True)

# ── Step 3: Select playlists ───────────────────────────────────────────────
st.markdown('<div class="section-label">Step 03 — Choose playlists to pull from</div>',
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

# ── Step 4: Build ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Step 04 — Build your playlist</div>',
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
                while results and count < 400:
                    for item in results["items"]:
                        if count >= 400:
                            break
                        if not item:
                            continue
                        track = item.get("track") or item.get("item")
                        if not track or not track.get("id"):
                            continue
                        if track["id"] not in seen_ids:
                            seen_ids.add(track["id"])
                            all_tracks.append({
                                "id":          track["id"],
                                "name":        track["name"],
                                "artist":      track["artists"][0]["name"] if track.get("artists") else "Unknown",
                                "album":       track["album"]["name"] if track.get("album") else "Unknown",
                                "image":       track["album"]["images"][0]["url"] if track.get("album") and track["album"].get("images") else None,
                                "uri":         track["uri"],
                                "preview_url": track.get("preview_url"),
                                "popularity":  track.get("popularity", 0)
                            })
                            count += 1
                    if results["next"] and count < 400:
                        results = sp.next(results)
                    else:
                        break
            except Exception as e:
                st.warning(f"Skipped a playlist: {e}")
                continue

    if not all_tracks:
        st.error("No tracks found. Try selecting different playlists.")
        st.stop()

    with st.spinner(f"Analyzing audio features for {len(all_tracks)} tracks..."):
        all_tracks = enrich_tracks_with_audio_features(all_tracks)

    with st.spinner("Claude is curating your playlist..."):
        result = build_mood_playlist(all_tracks, active_mood, preferences=preferences)

    selected_indices = result.get("selected_indices", [])
    playlist_tracks = []
    for idx in selected_indices:
        if 0 <= idx < len(all_tracks):
            playlist_tracks.append(all_tracks[idx])

    if not playlist_tracks:
        playlist_tracks = all_tracks[:80]

    st.session_state["playlist_tracks"] = playlist_tracks
    st.session_state["playlist_name"]   = result.get("playlist_name", f"{active_mood} Mix")
    st.session_state["playlist_desc"]   = result.get("playlist_description", "")
    st.session_state["mood_summary"]    = result.get("mood_summary", "")
    st.session_state["active_mood"]     = active_mood
    st.session_state["playlist_built"]  = True

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

            energy_val   = track.get("energy")
            valence_val  = track.get("valence")
            bpm_val      = track.get("tempo")

            audio_html = ""
            if energy_val is not None:
                e_class = "high" if energy_val > 0.7 else "mid" if energy_val > 0.4 else "low"
                v_class = "high" if valence_val > 0.6 else "mid" if valence_val > 0.3 else "low"
                audio_html = (
                    f'<div class="audio-bar">'
                    f'<span class="audio-tag {e_class}">⚡{energy_val}</span>'
                    f'<span class="audio-tag {v_class}">♡{valence_val}</span>'
                    f'<span class="audio-tag mid">♩{bpm_val}bpm</span>'
                    f'</div>'
                )

            st.markdown(
                f'<div class="track-card">'
                f'{img_html}'
                f'<div class="track-num">{i+1}</div>'
                f'<div style="flex:1;">'
                f'<div class="track-name">{track["name"]}</div>'
                f'<div class="track-artist">{track["artist"]} · {track["album"]}</div>'
                f'{audio_html}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    with col_actions:
        st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.85rem; color:#888; margin-bottom:1rem; line-height:1.75;">'
            f'{len(playlist_tracks)} tracks curated using real audio data.</div>',
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
        st.markdown(
            '<div style="font-size:0.75rem; color:#333; line-height:1.75;">'
            'Each track shows energy ⚡, mood ♡, and BPM ♩ — '
            'pulled directly from Spotify audio analysis.</div>',
            unsafe_allow_html=True
        )
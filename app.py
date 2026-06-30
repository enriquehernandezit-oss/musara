import streamlit as st
import os
from dotenv import load_dotenv
from auth import get_auth_url, handle_callback, get_spotify_client, is_logged_in, logout
from spotify import (
    get_user_profile, get_all_playlists, create_spotify_playlist,
    enrich_tracks_with_audio_features, enrich_tracks_with_genres
)
from agent import build_mood_playlist

load_dotenv()

st.set_page_config(
    page_title="Musara",
    page_icon="M",
    layout="wide"
)

st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fontsource/bebas-neue@4.5.0/index.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fontsource/space-grotesk@5.0.8/index.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fontsource/dm-mono@5.0.8/index.min.css">
""", unsafe_allow_html=True)

st.markdown("""
<style>
:root {
    --bg:          #090907;
    --surface:     #0f0f0c;
    --surface2:    #141412;
    --border:      #1e1e1a;
    --border-hi:   #3a3a34;
    --text:        #f0ede4;
    --text-2:      #9a9890;
    --text-3:      #585852;
    --green:       #1DB954;
    --green-dim:   rgba(29,185,84,0.07);
    --green-border:rgba(29,185,84,0.2);
}

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: var(--bg);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
}
.stApp { background-color: var(--bg); }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container {
    padding: 2.5rem 4rem;
    max-width: 1240px;
}

h1 {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 5rem !important;
    font-weight: 400 !important;
    color: var(--text) !important;
    letter-spacing: 0.04em !important;
    margin-bottom: 0 !important;
    line-height: 0.9 !important;
}

[class*="bebas"], .wordmark, .pl-title, .mood-name,
.track-idx, .export-count, .pl-stat-val, .how-num,
.sidebar-stat-val, .label, .export-stat-val {
    font-family: 'Bebas Neue', Impact, sans-serif !important;
}

h3 {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.65rem !important;
    font-weight: 400 !important;
    color: var(--text-3) !important;
    margin-top: 0.75rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}

.spotify-btn {
    background: var(--green);
    color: #000;
    padding: 0.65rem 1.75rem;
    border-radius: 3px;
    font-weight: 600;
    font-size: 0.875rem;
    text-decoration: none;
    display: inline-block;
    margin-top: 2rem;
    letter-spacing: 0.01em;
    font-family: 'Space Grotesk', sans-serif;
    transition: opacity 0.12s;
}
.spotify-btn:hover { opacity: 0.88; }

.mood-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.5rem 1rem 1.25rem;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: border-color 0.12s;
}
.mood-card::before {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: var(--green);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.2s;
}
.mood-card:hover::before { transform: scaleX(1); }
.mood-card:hover { border-color: var(--border-hi); }

.mood-card-selected {
    background: var(--green);
    border: 1px solid var(--green);
    border-radius: 4px;
    padding: 1.5rem 1rem 1.25rem;
    position: relative;
}

.mood-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.3rem;
    color: var(--text);
    letter-spacing: 0.05em;
    line-height: 1;
    margin-bottom: 0.4rem;
}
.mood-card-selected .mood-name { color: #090907; }

.mood-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    color: var(--text-3);
    line-height: 1.4;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.mood-card-selected .mood-sub { color: rgba(9,9,7,0.55); }

.track-row {
    display: grid;
    grid-template-columns: 44px 1fr auto;
    align-items: center;
    gap: 1rem;
    padding: 0.85rem 0;
    border-bottom: 1px solid var(--border);
    transition: background 0.1s, padding 0.1s;
}
.track-row:first-of-type { border-top: 1px solid var(--border); }
.track-row:hover {
    background: var(--surface);
    padding-left: 0.5rem;
    padding-right: 0.5rem;
    border-radius: 3px;
    margin: 0 -0.5rem;
}

.track-idx {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    color: var(--text-3);
    letter-spacing: 0.05em;
    line-height: 1;
    text-align: right;
    transition: color 0.1s;
}
.track-row:hover .track-idx { color: var(--green); }

.track-name {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.track-artist {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-2);
    margin-top: 2px;
    letter-spacing: 0.03em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.track-tags {
    display: flex;
    gap: 4px;
    align-items: center;
}
.tag {
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    color: var(--text-3);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 2px 6px;
    letter-spacing: 0.03em;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
.tag-hi {
    color: var(--green);
    border-color: var(--green-border);
    background: var(--green-dim);
}

.pl-header {
    border-top: 2px solid var(--green);
    padding: 2.5rem 0;
    margin-bottom: 2.5rem;
}
.pl-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    color: var(--green);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.pl-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.5rem;
    color: var(--text);
    letter-spacing: 0.03em;
    line-height: 0.95;
    margin-bottom: 1rem;
}
.pl-desc {
    font-size: 0.8125rem;
    color: var(--text-2);
    line-height: 1.75;
    max-width: 600px;
}
.pl-stats {
    display: flex;
    gap: 2.5rem;
    margin-top: 1.75rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
}
.pl-stat-val {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    color: var(--text);
    letter-spacing: 0.03em;
    line-height: 1;
    white-space: nowrap;
}
.pl-stat-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.55rem;
    color: var(--text-3);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 4px;
}

.label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.85rem;
    color: var(--text-3);
    letter-spacing: 0.2em;
    margin-bottom: 1.25rem;
}
.label-num {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    color: var(--green);
    letter-spacing: 0.05em;
    margin-right: 0.5rem;
}

.user-pill {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    color: var(--text-2);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 0.35rem 0.75rem;
    display: inline-block;
    margin-top: 1rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.pref-surface {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.75rem;
    margin-bottom: 1rem;
}

.export-sidebar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.5rem;
}
.export-count {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 5rem;
    color: var(--text);
    letter-spacing: -0.01em;
    line-height: 1;
    border-top: 2px solid var(--green);
    padding-top: 1rem;
}
.export-count-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-3);
    margin-top: 2px;
    margin-bottom: 1.5rem;
}
.export-stat-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 0.6rem 0;
    border-bottom: 1px solid var(--border);
}
.export-stat-key {
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    color: var(--text-3);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.export-stat-val {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1rem;
    color: var(--text-2);
    letter-spacing: 0.04em;
}
.export-note {
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    color: var(--text-3);
    line-height: 1.8;
    margin-top: 1rem;
    letter-spacing: 0.04em;
}

hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 2.5rem 0 !important;
}

.landing-desc {
    font-size: 0.9375rem;
    color: var(--text-2);
    line-height: 1.8;
    max-width: 440px;
    margin-top: 1.25rem;
}
.how-item {
    display: flex;
    gap: 1.25rem;
    align-items: flex-start;
    padding: 1.1rem 0;
    border-bottom: 1px solid var(--border);
}
.how-item:first-child { border-top: 1px solid var(--border); }
.how-num {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    color: var(--border-hi);
    letter-spacing: 0.04em;
    line-height: 1;
    min-width: 36px;
}
.how-text {
    font-size: 0.875rem;
    color: var(--text-2);
    line-height: 1.6;
    padding-top: 0.35rem;
}
.feature-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.75rem;
    margin-top: 2rem;
}
.feature-card-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-3);
    margin-bottom: 1rem;
}

.stButton > button {
    background: var(--green) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 3px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.65rem 1.75rem !important;
    letter-spacing: 0.01em !important;
    font-family: 'Space Grotesk', sans-serif !important;
    transition: opacity 0.12s !important;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    border: none !important;
}

.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
    font-size: 0.8125rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--green) !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input::placeholder { color: var(--text-3) !important; }

.stSelectbox > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
    font-size: 0.8125rem !important;
}

.stMultiSelect > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
    font-size: 0.8125rem !important;
}

.stSlider > div > div > div { background: var(--green) !important; }
.stSlider > div > div > div > div { background: var(--green) !important; }

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
    st.markdown('<h1>MUSARA</h1>', unsafe_allow_html=True)
    st.markdown('<h3>Mood-based playlist intelligence</h3>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <p class="landing-desc">
            Musara analyzes your Spotify library and curates playlists around your
            emotional state — using audio signal data, not genre tags.
            Energy. Valence. Tempo. Danceability. Real numbers, real results.
        </p>
        """, unsafe_allow_html=True)
        auth_url = get_auth_url()
        st.markdown(
            f'<a href="{auth_url}" class="spotify-btn">Connect Spotify</a>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="font-family:\'DM Mono\',monospace; font-size:0.6rem; '
            'color:var(--text-3); letter-spacing:0.08em; text-transform:uppercase; '
            'margin-top:0.75rem;">Requires Spotify account</div>',
            unsafe_allow_html=True
        )
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-card-title">How it works</div>
            <div class="how-item">
                <div class="how-num">01</div>
                <div class="how-text">Connect your Spotify account via OAuth</div>
            </div>
            <div class="how-item">
                <div class="how-num">02</div>
                <div class="how-text">Set your mood and listening context</div>
            </div>
            <div class="how-item">
                <div class="how-num">03</div>
                <div class="how-text">AI scores up to 400 tracks against your parameters</div>
            </div>
            <div class="how-item">
                <div class="how-num">04</div>
                <div class="how-text">Export directly to your Spotify library</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ── Logged in ──────────────────────────────────────────────────────────────
user = get_user_profile()

col_title, col_user = st.columns([4, 1])
with col_title:
    st.markdown('<h1>MUSARA</h1>', unsafe_allow_html=True)
    st.markdown('<h3>Mood-based playlist intelligence</h3>', unsafe_allow_html=True)
with col_user:
    if user:
        st.markdown(
            f'<div class="user-pill">{user["display_name"]}</div>',
            unsafe_allow_html=True
        )
        if st.button("Sign out"):
            logout()
            st.rerun()

st.markdown('<hr>', unsafe_allow_html=True)

# ── Step 1: Mood ───────────────────────────────────────────────────────────
st.markdown(
    '<div class="label"><span class="label-num">01</span> Select mood</div>',
    unsafe_allow_html=True
)

MOODS = [
    {"label": "Hype",      "display": "Energized",  "desc": "High drive"},
    {"label": "Chill",     "display": "Unwinding",  "desc": "Low tempo"},
    {"label": "Focus",     "display": "Focused",    "desc": "Deep work"},
    {"label": "Sad",       "display": "Reflective", "desc": "Introspective"},
    {"label": "Nostalgic", "display": "Nostalgic",  "desc": "Memory-driven"},
    {"label": "Romantic",  "display": "Romantic",   "desc": "Soft, intimate"},
]

if "selected_mood" not in st.session_state:
    st.session_state["selected_mood"] = None

cols = st.columns(6)
for i, mood in enumerate(MOODS):
    with cols[i]:
        is_selected = st.session_state["selected_mood"] == mood["label"]
        card_class  = "mood-card-selected" if is_selected else "mood-card"
        st.markdown(
            f'<div class="{card_class}">'
            f'<div class="mood-name">{mood["display"]}</div>'
            f'<div class="mood-sub">{mood["desc"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        if st.button(mood["display"], key=f"mood_{i}"):
            st.session_state["selected_mood"] = mood["label"]
            st.rerun()

st.markdown('<br>', unsafe_allow_html=True)
custom_mood = st.text_input(
    "Or describe your current state",
    placeholder="Late-night drive, pre-match warmup, slow Sunday morning..."
)

active_mood = custom_mood.strip() if custom_mood.strip() else st.session_state.get("selected_mood")

st.markdown('<hr>', unsafe_allow_html=True)

# ── Step 2: Preferences ────────────────────────────────────────────────────
st.markdown(
    '<div class="label"><span class="label-num">02</span> Preferences</div>',
    unsafe_allow_html=True
)

st.markdown('<div class="pref-surface">', unsafe_allow_html=True)
pref_col1, pref_col2 = st.columns(2)

with pref_col1:
    activity = st.selectbox(
        "Current activity",
        options=["", "Driving", "Working out / Gym", "Studying / Focus",
                 "Party / Going out", "Cooking", "Relaxing at home",
                 "Running", "Working", "Getting ready"],
        index=0
    )
    language = st.selectbox(
        "Language",
        options=["No preference", "Spanish", "English",
                 "Mixed (Spanish + English)", "Portuguese", "French"],
        index=0
    )
    include_artists = st.text_input(
        "Featured artists",
        placeholder="Bad Bunny, Drake, Frank Ocean"
    )

with pref_col2:
    energy = st.slider("Energy intensity", min_value=1, max_value=10, value=5)
    energy_label = (
        "Very calm" if energy <= 2 else
        "Calm"      if energy <= 4 else
        "Moderate"  if energy <= 6 else
        "High"      if energy <= 8 else
        "Peak"
    )
    st.markdown(
        f'<div style="font-family:\'DM Mono\',monospace; font-size:0.6rem; '
        f'color:var(--text-3); margin-top:-0.5rem; margin-bottom:1rem; '
        f'text-transform:uppercase; letter-spacing:0.08em;">{energy_label}</div>',
        unsafe_allow_html=True
    )
    exclude_artists = st.text_input(
        "Excluded artists",
        placeholder="Leave blank to include all"
    )
    extra_prefs = st.text_input(
        "Additional filters",
        placeholder="No explicit content, instrumentals only..."
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

# ── Step 3: Source playlists ───────────────────────────────────────────────
st.markdown(
    '<div class="label"><span class="label-num">03</span> Source playlists</div>',
    unsafe_allow_html=True
)

if "playlists" not in st.session_state:
    with st.spinner("Loading playlists..."):
        st.session_state["playlists"] = get_all_playlists()

playlists = st.session_state["playlists"]

if not playlists:
    st.warning("No playlists found. Make sure you have playlists created in your Spotify account.")
    st.stop()

playlist_options = {p["name"]: p["id"] for p in playlists}

selected_names = st.multiselect(
    "Playlists to scan",
    options=list(playlist_options.keys()),
    default=None,
    placeholder="Choose playlists...",
    help="Select playlists you created in Spotify"
)

selected_ids = [playlist_options[name] for name in selected_names] if selected_names else []

st.markdown('<hr>', unsafe_allow_html=True)

# ── Step 4: Generate ───────────────────────────────────────────────────────
st.markdown(
    '<div class="label"><span class="label-num">04</span> Generate</div>',
    unsafe_allow_html=True
)

build_btn = st.button("Generate Playlist", type="primary")

if build_btn:
    if not active_mood:
        st.warning("Select or describe a mood first.")
        st.stop()
    if not selected_ids:
        st.warning("Select at least one playlist.")
        st.stop()

    with st.spinner("Pulling tracks..."):
        sp = get_spotify_client()
        all_tracks = []
        seen_ids   = set()
        for pid in selected_ids:
            try:
                results = sp.playlist_tracks(pid, limit=50)
                count   = 0
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
                                "artist_id":   track["artists"][0]["id"]   if track.get("artists") else None,
                                "album":       track["album"]["name"] if track.get("album") else "Unknown",
                                "image":       track["album"]["images"][0]["url"] if track.get("album") and track["album"].get("images") else None,
                                "uri":         track["uri"],
                                "preview_url": track.get("preview_url"),
                                "popularity":  track.get("popularity", 0),
                                "explicit":    track.get("explicit", False)
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

    with st.spinner("Fetching genre data..."):
        all_tracks = enrich_tracks_with_genres(all_tracks)

    with st.spinner("Curating your playlist..."):
        result = build_mood_playlist(all_tracks, active_mood, preferences=preferences)

    playlist_tracks = result.get("tracks", all_tracks[:80])

    st.session_state["playlist_tracks"] = playlist_tracks
    st.session_state["playlist_name"]   = result.get("playlist_name",   f"{active_mood} Mix")
    st.session_state["playlist_desc"]   = result.get("playlist_description", "")
    st.session_state["mood_summary"]    = result.get("mood_summary",    "")
    st.session_state["active_mood"]     = active_mood
    st.session_state["playlist_built"]  = True

# ── Show playlist ──────────────────────────────────────────────────────────
if st.session_state.get("playlist_built"):
    playlist_tracks = st.session_state["playlist_tracks"]
    playlist_name   = st.session_state["playlist_name"]
    playlist_desc   = st.session_state["playlist_desc"]
    mood_summary    = st.session_state["mood_summary"]
    active_mood     = st.session_state["active_mood"]

    energies = [t.get("energy")  for t in playlist_tracks if t.get("energy")  is not None]
    valences = [t.get("valence") for t in playlist_tracks if t.get("valence") is not None]
    tempos   = [t.get("tempo")   for t in playlist_tracks if t.get("tempo")   is not None]
    avg_e    = f"{sum(energies)/len(energies):.2f}" if energies else "—"
    avg_v    = f"{sum(valences)/len(valences):.2f}" if valences else "—"
    avg_t    = f"{int(sum(tempos)/len(tempos))}"    if tempos   else "—"

    st.markdown(
        f'<div class="pl-header">'
        f'<div class="pl-eyebrow">{active_mood}</div>'
        f'<div class="pl-title">{playlist_name.upper()}</div>'
        f'<div class="pl-desc">{playlist_desc}</div>'
        f'<div class="pl-desc" style="margin-top:0.5rem;">{mood_summary}</div>'
        f'<div class="pl-stats">'
        f'<div><div class="pl-stat-val">{len(playlist_tracks)}</div>'
        f'<div class="pl-stat-label">Tracks</div></div>'
        f'<div><div class="pl-stat-val">{avg_e}</div>'
        f'<div class="pl-stat-label">Avg Energy</div></div>'
        f'<div><div class="pl-stat-val">{avg_v}</div>'
        f'<div class="pl-stat-label">Avg Valence</div></div>'
        f'<div><div class="pl-stat-val">{avg_t}</div>'
        f'<div class="pl-stat-label">Avg BPM</div></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    col_tracks, col_actions = st.columns([3, 1])

    with col_tracks:
        st.markdown(
            '<div class="label"><span class="label-num">—</span> Tracklist</div>',
            unsafe_allow_html=True
        )
        for i, track in enumerate(playlist_tracks):
            img_html = (
                f'<img src="{track["image"]}" width="36" height="36" '
                f'style="border-radius:3px; object-fit:cover; border:1px solid var(--border);"/>'
                if track.get("image") else
                '<div style="width:36px;height:36px;border-radius:3px;'
                'background:var(--surface2);border:1px solid var(--border);"></div>'
            )

            energy_val  = track.get("energy")
            valence_val = track.get("valence")
            bpm_val     = track.get("tempo")

            tags_html = ""
            if energy_val is not None:
                e_cls = "tag tag-hi" if energy_val > 0.7 else "tag"
                v_cls = "tag tag-hi" if valence_val > 0.6 else "tag"
                tags_html = (
                    f'<div class="track-tags">'
                    f'<span class="{e_cls}">{energy_val:.2f} E</span>'
                    f'<span class="{v_cls}">{valence_val:.2f} V</span>'
                    f'<span class="tag">{int(bpm_val)} BPM</span>'
                    f'</div>'
                )

            st.markdown(
                f'<div class="track-row">'
                f'<div class="track-idx">{i+1:02d}</div>'
                f'<div style="min-width:0;">'
                f'<div class="track-name">{track["name"]}</div>'
                f'<div class="track-artist">{track["artist"]} — {track["album"]}</div>'
                f'</div>'
                f'{tags_html}'
                f'</div>',
                unsafe_allow_html=True
            )

    with col_actions:
        st.markdown(
            f'<div class="export-sidebar">'
            f'<div class="export-count">{len(playlist_tracks)}</div>'
            f'<div class="export-count-label">Tracks selected</div>',
            unsafe_allow_html=True
        )

        if st.button("Save to Spotify"):
            with st.spinner("Creating playlist..."):
                track_uris = [t["uri"] for t in playlist_tracks]
                exported   = create_spotify_playlist(
                    name=playlist_name,
                    description=f"Created by Musara · Mood: {active_mood}",
                    track_uris=track_uris
                )
            if exported:
                st.success("Playlist saved.")
                st.markdown(
                    f'<a href="{exported["url"]}" target="_blank" class="spotify-btn">'
                    f'Open in Spotify</a>',
                    unsafe_allow_html=True
                )
            else:
                st.error("Export failed. Please try again.")

        st.markdown(
            f'<div class="export-stat-row">'
            f'<span class="export-stat-key">Avg Energy</span>'
            f'<span class="export-stat-val">{avg_e}</span></div>'
            f'<div class="export-stat-row">'
            f'<span class="export-stat-key">Avg Valence</span>'
            f'<span class="export-stat-val">{avg_v}</span></div>'
            f'<div class="export-stat-row">'
            f'<span class="export-stat-key">Avg BPM</span>'
            f'<span class="export-stat-val">{avg_t}</span></div>'
            f'<div class="export-note">E = Energy · V = Valence'
            f'<br>Data via Spotify Audio Analysis API</div>'
            f'</div>',
            unsafe_allow_html=True
        )
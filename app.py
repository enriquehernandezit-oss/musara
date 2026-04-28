import streamlit as st
import os
from dotenv import load_dotenv
from auth import get_auth_url, handle_callback, get_spotify_client, is_logged_in, logout
from spotify import get_user_profile, get_all_playlists, create_spotify_playlist, enrich_tracks_with_audio_features
from agent import build_mood_playlist

load_dotenv()

st.set_page_config(
    page_title="Musara",
    page_icon="M",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:           #060606;
    --surface:      #0d0d0d;
    --border:       #191919;
    --border-hi:    #242424;
    --text:         #f0f0f0;
    --text-2:       #666;
    --text-3:       #2e2e2e;
    --green:        #1DB954;
    --green-dim:    rgba(29,185,84,0.08);
    --green-border: rgba(29,185,84,0.25);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
}
.stApp { background-color: var(--bg); }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container {
    padding: 3rem 4rem;
    max-width: 1160px;
}

h1 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 2.75rem !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    letter-spacing: -0.04em !important;
    margin-bottom: 0 !important;
    line-height: 1 !important;
}

h3 {
    font-size: 0.875rem !important;
    font-weight: 400 !important;
    color: var(--text-3) !important;
    margin-top: 0.5rem !important;
    letter-spacing: 0.01em !important;
}

/* ── Spotify connect button ── */
.spotify-btn {
    background: var(--green);
    color: #000;
    padding: 10px 22px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.8125rem;
    text-decoration: none;
    display: inline-block;
    margin-top: 1.5rem;
    letter-spacing: 0.01em;
    transition: opacity 0.12s;
}
.spotify-btn:hover { opacity: 0.88; }

/* ── Mood cards ── */
.mood-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem 1rem 1rem;
    cursor: pointer;
    position: relative;
    transition: border-color 0.12s, background 0.12s;
}
.mood-card:hover {
    border-color: var(--border-hi);
    background: #111;
}
.mood-card-selected {
    background: var(--green-dim);
    border: 1px solid var(--green-border);
    border-radius: 8px;
    padding: 1.25rem 1rem 1rem;
    position: relative;
}
.mood-card-selected::before {
    content: '';
    position: absolute;
    left: 0; top: 8px; bottom: 8px;
    width: 2px;
    background: var(--green);
    border-radius: 0 2px 2px 0;
}

.mood-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.01em;
    margin-bottom: 0.3rem;
}
.mood-sub {
    font-size: 0.68rem;
    color: var(--text-3);
    line-height: 1.4;
}
.mood-card-selected .mood-sub { color: rgba(29,185,84,0.45); }

/* ── Track rows ── */
.track-row {
    display: grid;
    grid-template-columns: 28px 36px 1fr auto;
    align-items: center;
    gap: 12px;
    padding: 0.6rem 0.75rem;
    border-radius: 6px;
    margin-bottom: 2px;
    transition: background 0.1s;
}
.track-row:hover { background: #0f0f0f; }

.track-idx {
    font-size: 0.7rem;
    color: var(--text-3);
    text-align: right;
    font-variant-numeric: tabular-nums;
    font-weight: 500;
    font-family: 'Space Grotesk', sans-serif;
}
.track-name {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.track-meta {
    font-size: 0.7rem;
    color: var(--text-2);
    margin-top: 1px;
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
    font-size: 0.58rem;
    color: var(--text-3);
    background: #111;
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 1px 6px;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 0.02em;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
.tag-hi {
    color: var(--green);
    background: var(--green-dim);
    border-color: var(--green-border);
}

/* ── Playlist header ── */
.playlist-header {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 2.25rem 2.5rem;
    margin-bottom: 2.25rem;
    position: relative;
    overflow: hidden;
}
.playlist-header::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(120deg, rgba(29,185,84,0.03) 0%, transparent 50%);
    pointer-events: none;
}
.pl-eyebrow {
    font-size: 0.62rem;
    font-weight: 600;
    color: var(--green);
    text-transform: uppercase;
    letter-spacing: 0.18em;
    margin-bottom: 0.75rem;
}
.pl-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: 0.5rem;
}
.pl-desc {
    font-size: 0.8125rem;
    color: var(--text-2);
    line-height: 1.7;
    max-width: 600px;
}
.pl-stat-row {
    display: flex;
    gap: 2rem;
    margin-top: 1.25rem;
}
.pl-stat-val {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.02em;
    white-space: nowrap;
}
.pl-stat-label {
    font-size: 0.6rem;
    color: var(--text-3);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 2px;
}

/* ── Section label ── */
.label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.6rem;
    font-weight: 600;
    color: var(--text-3);
    text-transform: uppercase;
    letter-spacing: 0.18em;
    margin-bottom: 1.25rem;
}

/* ── User pill ── */
.user-pill {
    font-size: 0.75rem;
    color: var(--text-2);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.3rem 0.75rem;
    display: inline-block;
    margin-top: 1rem;
}

/* ── Pref surface ── */
.pref-surface {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* ── Export sidebar ── */
.export-sidebar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.5rem;
}
.export-count {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.05em;
    line-height: 1;
}
.export-count-label {
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-3);
    margin-top: 4px;
    margin-bottom: 1.5rem;
}
.export-stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-top: 1px solid var(--border);
}
.export-stat-key {
    font-size: 0.65rem;
    color: var(--text-3);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.export-stat-val {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.8rem;
    color: var(--text-2);
    font-weight: 600;
}
.export-note {
    font-size: 0.65rem;
    color: var(--text-3);
    line-height: 1.8;
    margin-top: 1rem;
}

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 2.25rem 0 !important;
}

/* ── Landing feature card ── */
.feature-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.75rem;
    margin-top: 2rem;
}
.feature-card-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.01em;
    margin-bottom: 1rem;
}
.how-step {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 0.65rem 0;
    border-bottom: 1px solid var(--border);
}
.how-step:last-child { border-bottom: none; }
.how-step-num {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.6rem;
    font-weight: 600;
    color: var(--green);
    letter-spacing: 0.1em;
    min-width: 18px;
    padding-top: 2px;
}
.how-step-text { font-size: 0.78rem; color: var(--text-3); line-height: 1.5; }

/* ── Streamlit overrides ── */
.stButton > button {
    background: var(--green) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.8125rem !important;
    padding: 0.6rem 1.5rem !important;
    letter-spacing: 0.01em !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: opacity 0.12s !important;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    border: none !important;
}

.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-size: 0.8125rem !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--border-hi) !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input::placeholder { color: var(--text-3) !important; }

.stSelectbox > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-size: 0.8125rem !important;
}

.stMultiSelect > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
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
    st.markdown('<h1>Musara</h1>', unsafe_allow_html=True)
    st.markdown('<h3>Playlist intelligence.</h3>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div style="font-size:0.9rem; color:#666; line-height:1.8; max-width:460px; margin-top:0.5rem;">
            Musara analyzes your Spotify library and builds playlists calibrated
            to your mood using real audio data — energy, valence, BPM, and
            danceability — not genre tags.
        </div>
        """, unsafe_allow_html=True)

        auth_url = get_auth_url()
        st.markdown(
            f'<a href="{auth_url}" class="spotify-btn">Connect Spotify</a>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-card-title">How it works</div>
            <div class="how-step">
                <span class="how-step-num">01</span>
                <span class="how-step-text">Connect your Spotify account</span>
            </div>
            <div class="how-step">
                <span class="how-step-num">02</span>
                <span class="how-step-text">Select a mood and set preferences</span>
            </div>
            <div class="how-step">
                <span class="how-step-num">03</span>
                <span class="how-step-text">AI scores and ranks tracks from your playlists</span>
            </div>
            <div class="how-step">
                <span class="how-step-num">04</span>
                <span class="how-step-text">Save the result directly to Spotify</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ── Logged in ──────────────────────────────────────────────────────────────
user = get_user_profile()

col_title, col_user = st.columns([4, 1])
with col_title:
    st.markdown('<h1>Musara</h1>', unsafe_allow_html=True)
    st.markdown('<h3>Playlist intelligence.</h3>', unsafe_allow_html=True)
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
st.markdown('<div class="label">Mood</div>', unsafe_allow_html=True)

MOODS = [
    {"label": "Hype",      "display": "Energized",   "desc": "High-intensity, driven"},
    {"label": "Chill",     "display": "Unwinding",    "desc": "Low tempo, relaxed"},
    {"label": "Focus",     "display": "Focused",      "desc": "Deep concentration"},
    {"label": "Sad",       "display": "Reflective",   "desc": "Introspective, melancholic"},
    {"label": "Nostalgic", "display": "Nostalgic",    "desc": "Memory-forward warmth"},
    {"label": "Romantic",  "display": "Romantic",     "desc": "Soft, intimate energy"},
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
    "Or describe your current state of mind",
    placeholder="Late-night drive, pre-match warmup, slow Sunday morning..."
)

active_mood = custom_mood.strip() if custom_mood.strip() else st.session_state.get("selected_mood")

st.markdown('<hr>', unsafe_allow_html=True)

# ── Step 2: Preferences ────────────────────────────────────────────────────
st.markdown('<div class="label">Preferences</div>', unsafe_allow_html=True)

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
        placeholder="Frank Ocean, Bon Iver, Rex Orange County"
    )

with pref_col2:
    energy = st.slider(
        "Energy level",
        min_value=1,
        max_value=10,
        value=5
    )
    energy_label = (
        "Very calm"      if energy <= 2 else
        "Calm"           if energy <= 4 else
        "Moderate"       if energy <= 6 else
        "High"           if energy <= 8 else
        "Peak"
    )
    st.markdown(
        f'<div style="font-size:0.7rem; color:var(--text-3); margin-top:-0.5rem; '
        f'margin-bottom:1rem; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;">'
        f'{energy_label}</div>',
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
st.markdown('<div class="label">Source playlists</div>', unsafe_allow_html=True)

if "playlists" not in st.session_state:
    with st.spinner("Loading playlists..."):
        st.session_state["playlists"] = get_all_playlists()

playlists = st.session_state["playlists"]

if not playlists:
    st.warning("No playlists found. Make sure you have playlists created in your Spotify account.")
    st.stop()

playlist_options = {p["name"]: p["id"] for p in playlists}

selected_names = st.multiselect(
    "Select playlists to pull tracks from",
    options=list(playlist_options.keys()),
    default=None,
    placeholder="Choose playlists...",
    help="Select playlists you created in Spotify"
)

selected_ids = [playlist_options[name] for name in selected_names] if selected_names else []

st.markdown('<hr>', unsafe_allow_html=True)

# ── Step 4: Generate ───────────────────────────────────────────────────────
st.markdown('<div class="label">Generate</div>', unsafe_allow_html=True)

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

    with st.spinner("Curating your playlist..."):
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

    # Compute avg stats
    energies  = [t.get("energy") for t in playlist_tracks if t.get("energy") is not None]
    valences  = [t.get("valence") for t in playlist_tracks if t.get("valence") is not None]
    tempos    = [t.get("tempo") for t in playlist_tracks if t.get("tempo") is not None]
    avg_e = f"{sum(energies)/len(energies):.2f}" if energies else "—"
    avg_v = f"{sum(valences)/len(valences):.2f}" if valences else "—"
    avg_t = f"{int(sum(tempos)/len(tempos))}" if tempos else "—"

    st.markdown(
        f'<div class="playlist-header">'
        f'<div class="pl-eyebrow">{active_mood}</div>'
        f'<div class="pl-title">{playlist_name}</div>'
        f'<div class="pl-desc">{playlist_desc}</div>'
        f'<div class="pl-desc" style="margin-top:0.5rem;">{mood_summary}</div>'
        f'<div class="pl-stat-row">'
        f'<div><div class="pl-stat-val">{len(playlist_tracks)}</div><div class="pl-stat-label">Tracks</div></div>'
        f'<div><div class="pl-stat-val">{avg_e}</div><div class="pl-stat-label">Avg Energy</div></div>'
        f'<div><div class="pl-stat-val">{avg_v}</div><div class="pl-stat-label">Avg Valence</div></div>'
        f'<div><div class="pl-stat-val">{avg_t}</div><div class="pl-stat-label">Avg BPM</div></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    col_tracks, col_actions = st.columns([3, 1])

    with col_tracks:
        st.markdown('<div class="label">Tracks</div>', unsafe_allow_html=True)
        for i, track in enumerate(playlist_tracks):
            img_html = ""
            if track.get("image"):
                img_html = (
                    f'<img src="{track["image"]}" width="36" height="36" '
                    f'style="border-radius:4px; flex-shrink:0; object-fit:cover; border:1px solid #191919;"/>'
                )
            else:
                img_html = '<div style="width:36px;height:36px;border-radius:4px;background:#141414;border:1px solid #191919;flex-shrink:0;"></div>'

            energy_val  = track.get("energy")
            valence_val = track.get("valence")
            bpm_val     = track.get("tempo")

            tags_html = ""
            if energy_val is not None:
                e_class = "tag" if energy_val <= 0.4 else ("tag tag-hi" if energy_val > 0.7 else "tag")
                v_class = "tag tag-hi" if valence_val > 0.6 else "tag"
                tags_html = (
                    f'<div class="track-tags">'
                    f'<span class="{e_class}">{energy_val:.2f} E</span>'
                    f'<span class="{v_class}">{valence_val:.2f} V</span>'
                    f'<span class="tag">{int(bpm_val)} BPM</span>'
                    f'</div>'
                )

            st.markdown(
                f'<div class="track-row">'
                f'<div class="track-idx">{i+1}</div>'
                f'{img_html}'
                f'<div style="min-width:0;">'
                f'<div class="track-name">{track["name"]}</div>'
                f'<div class="track-meta">{track["artist"]} — {track["album"]}</div>'
                f'</div>'
                f'{tags_html}'
                f'</div>',
                unsafe_allow_html=True
            )

    with col_actions:
        st.markdown(
            f'<div class="export-sidebar">'
            f'<div class="label">Export</div>'
            f'<div class="export-count">{len(playlist_tracks)}</div>'
            f'<div class="export-count-label">Tracks selected</div>',
            unsafe_allow_html=True
        )

        if st.button("Save to Spotify"):
            with st.spinner("Creating playlist..."):
                track_uris = [t["uri"] for t in playlist_tracks]
                exported = create_spotify_playlist(
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
            f'<div class="export-stat-row"><span class="export-stat-key">Avg Energy</span>'
            f'<span class="export-stat-val">{avg_e}</span></div>'
            f'<div class="export-stat-row"><span class="export-stat-key">Avg Valence</span>'
            f'<span class="export-stat-val">{avg_v}</span></div>'
            f'<div class="export-stat-row"><span class="export-stat-key">Avg BPM</span>'
            f'<span class="export-stat-val">{avg_t}</span></div>'
            f'<div class="export-note">E = Energy · V = Valence<br>Source: Spotify Audio Analysis API</div>'
            f'</div>',
            unsafe_allow_html=True
        )

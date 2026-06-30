import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
MODEL = "claude-haiku-4-5-20251001"

LANGUAGE_GENRE_MAP = {
    "spanish": [
        "latin", "reggaeton", "latin pop", "cumbia", "salsa", "bachata",
        "latin trap", "urbano latino", "latin hip hop", "tropical",
        "latin r&b", "latin alternative", "corrido", "norteno",
        "musica mexicana", "latin rock", "flamenco", "latin soul",
        "reggaeton colombiano", "latin arena pop", "spanish pop",
        "latin viral pop", "mexican pop", "dominican pop"
    ],
    "english": [
        "pop", "rock", "hip hop", "r&b", "soul", "country", "indie",
        "alternative", "electronic", "dance", "edm", "house", "metal",
        "jazz", "blues", "folk", "punk", "rap", "trap", "drill",
        "uk pop", "australian pop", "canadian pop", "irish pop"
    ],
    "portuguese": [
        "mpb", "bossa nova", "samba", "forro", "axe", "pagode",
        "sertanejo", "brazilian", "funk carioca", "pagodao"
    ],
    "french": [
        "french pop", "chanson", "variete francaise", "french hip hop",
        "french electronic", "french indie", "french rock"
    ],
}

NON_ENGLISH_MARKERS = (
    LANGUAGE_GENRE_MAP["spanish"] +
    LANGUAGE_GENRE_MAP["portuguese"] +
    LANGUAGE_GENRE_MAP["french"] +
    ["k-pop", "j-pop", "afrobeats", "afropop", "korean", "japanese",
     "arab", "turkish pop", "italian pop", "german pop"]
)

def detect_language_from_genres(genres, language_pref):
    if not language_pref or language_pref.lower() in ("no preference", ""):
        return True
    if not genres:
        return True

    lang = language_pref.lower()
    genres_lower = [g.lower() for g in genres]

    if "mixed" in lang:
        return True

    if "spanish" in lang and "english" in lang:
        return True

    if "spanish" in lang:
        markers = LANGUAGE_GENRE_MAP["spanish"]
        return any(
            any(m in g for m in markers)
            for g in genres_lower
        )

    if "english" in lang:
        if any(
            any(m in g for m in NON_ENGLISH_MARKERS)
            for g in genres_lower
        ):
            return False
        return True

    if "portuguese" in lang:
        markers = LANGUAGE_GENRE_MAP["portuguese"]
        return any(
            any(m in g for m in markers)
            for g in genres_lower
        )

    if "french" in lang:
        markers = LANGUAGE_GENRE_MAP["french"]
        return any(
            any(m in g for m in markers)
            for g in genres_lower
        )

    return True


def interpret_mood(mood, preferences):
    energy_level = int(preferences.get("energy", 5)) if preferences else 5
    activity     = preferences.get("activity", "") if preferences else ""
    extra        = preferences.get("extra", "") if preferences else ""

    prompt = f"""You are a music data analyst. A user wants a playlist for: "{mood}"

Context:
- Energy slider: {energy_level}/10 (1=very calm, 10=maximum energy)
- Activity: {activity or "not specified"}
- Extra notes: {extra or "none"}

Spotify audio feature ranges:
- energy: 0.0 (silent/ambient) → 1.0 (intense/loud/fast)
- valence: 0.0 (sad/dark/tense) → 1.0 (happy/euphoric/bright)
- danceability: 0.0 (not danceable) → 1.0 (very danceable)
- tempo: BPM — 60=slow ballad, 90=mid, 120=upbeat, 150+=fast/dance
- acousticness: 0.0 (electronic/produced) → 1.0 (acoustic/raw)
- instrumentalness_max: max allowed instrumental ratio (0.0=needs vocals, 1.0=anything)
- speechiness_max: max allowed speech ratio (keep low for music, high for rap/spoken)

Reference calibrations:
- Party/pregame/hype: energy 0.75-1.0, valence 0.65-1.0, dance 0.65-1.0, tempo 115-180
- Chill/relax/lounge: energy 0.0-0.45, valence 0.3-0.75, dance 0.2-0.6, tempo 60-105
- Sad/heartbreak/cry: energy 0.0-0.45, valence 0.0-0.38, acoustic 0.25-1.0, tempo 50-100
- Focus/study/work: energy 0.3-0.62, valence 0.2-0.7, speech_max 0.1, tempo 70-120
- Romantic/date/love: energy 0.1-0.55, valence 0.35-0.75, dance 0.3-0.65, tempo 60-110
- Nostalgic/throwback: energy 0.25-0.65, valence 0.35-0.72, acoustic 0.1-0.75, tempo 70-130
- Driving/road trip: energy 0.55-0.9, valence 0.4-0.85, tempo 100-150
- Gym/workout: energy 0.78-1.0, valence 0.5-1.0, dance 0.55-1.0, tempo 120-180

Return ONLY this JSON — be precise, not generic:
{{
  "energy_min": 0.0,
  "energy_max": 1.0,
  "valence_min": 0.0,
  "valence_max": 1.0,
  "danceability_min": 0.0,
  "danceability_max": 1.0,
  "tempo_min": 60,
  "tempo_max": 200,
  "acousticness_min": 0.0,
  "acousticness_max": 1.0,
  "instrumentalness_max": 0.6,
  "speechiness_max": 0.5,
  "mood_interpretation": "one sentence describing what kind of music this calls for"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text
    start = raw.find("{")
    end = raw.rfind("}") + 1
    return json.loads(raw[start:end])


def score_track(track, targets):
    e   = track.get("energy")
    v   = track.get("valence")
    d   = track.get("danceability")
    bpm = track.get("tempo")
    ac  = track.get("acousticness")
    ins = track.get("instrumentalness")
    sp  = track.get("speechiness")

    if e is None:
        return track.get("popularity", 50) / 100 * 2

    score = 0.0

    def range_score(val, vmin, vmax, weight):
        if val is None:
            return weight * 0.5
        if vmin <= val <= vmax:
            return weight
        dist = min(abs(val - vmin), abs(val - vmax))
        return max(0.0, weight - dist * weight * 3)

    score += range_score(e,   targets["energy_min"],       targets["energy_max"],       4.0)
    score += range_score(v,   targets["valence_min"],      targets["valence_max"],       3.0)
    score += range_score(d,   targets["danceability_min"], targets["danceability_max"],  2.0)
    score += range_score(ac,  targets["acousticness_min"], targets["acousticness_max"],  1.0)

    if bpm is not None:
        score += range_score(bpm, targets["tempo_min"], targets["tempo_max"], 1.5)

    if ins is not None and ins > targets.get("instrumentalness_max", 0.6):
        score -= 2.0
    if sp is not None and sp > targets.get("speechiness_max", 0.5):
        score -= 1.5

    score += track.get("popularity", 0) / 200
    return score


def select_and_order(tracks, targets, preferences, n=80):
    include    = [a.strip().lower() for a in (preferences.get("include_artists") or "").split(",") if a.strip()]
    exclude    = [a.strip().lower() for a in (preferences.get("exclude_artists") or "").split(",") if a.strip()]
    language   = preferences.get("language", "")
    extra_text = (preferences.get("extra") or "").lower()
    no_explicit = "explicit" in extra_text or "clean" in extra_text

    scored = []
    for track in tracks:
        artist_lower = track.get("artist", "").lower()

        if exclude and any(ex in artist_lower for ex in exclude):
            continue

        if no_explicit and track.get("explicit", False):
            continue

        if language and language.lower() not in ("no preference", ""):
            genres = track.get("genres", [])
            if not detect_language_from_genres(genres, language):
                continue

        s = score_track(track, targets)

        if include and any(inc in artist_lower for inc in include):
            s += 3.0

        scored.append((s, track))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [t for _, t in scored[:n]]

    if not top:
        return tracks[:n]

    n3    = max(1, len(top) // 3)
    build = sorted(top[:n3],     key=lambda t: t.get("energy") or 0.5)
    peak  = sorted(top[n3:2*n3], key=lambda t: -(t.get("energy") or 0.5))
    end   = sorted(top[2*n3:],   key=lambda t: t.get("energy") or 0.5)

    return build + peak + end


def name_playlist(mood, preferences, playlist_tracks, mood_interpretation):
    track_sample = "\n".join([
        f"- {t['name']} by {t['artist']}"
        for t in playlist_tracks[:15]
    ])
    prefs_text = ""
    if preferences:
        activity = preferences.get("activity", "")
        language = preferences.get("language", "")
        extra    = preferences.get("extra", "")
        if activity: prefs_text += f"Activity: {activity}. "
        if language: prefs_text += f"Language: {language}. "
        if extra:    prefs_text += f"Notes: {extra}."

    prompt = f"""A playlist was built for: "{mood}"
{f'Context: {prefs_text}' if prefs_text else ''}
Vibe: {mood_interpretation}

Sample tracks:
{track_sample}

Write a creative name and description.
Return ONLY this JSON:
{{
  "playlist_name": "2-4 word creative name",
  "playlist_description": "one punchy sentence describing the vibe",
  "mood_summary": "2 sentences on the listening experience and energy arc"
}}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {
            "playlist_name": f"{mood} Mix",
            "playlist_description": "A curated playlist for your current mood.",
            "mood_summary": mood_interpretation
        }


def build_mood_playlist(tracks, mood, preferences=None):
    if preferences is None:
        preferences = {}

    targets              = interpret_mood(mood, preferences)
    mood_interpretation  = targets.get("mood_interpretation", "")
    playlist_tracks      = select_and_order(tracks, targets, preferences, n=80)
    naming               = name_playlist(mood, preferences, playlist_tracks, mood_interpretation)
    naming["tracks"]     = playlist_tracks
    return naming
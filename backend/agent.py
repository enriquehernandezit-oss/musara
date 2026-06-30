"""
Claude-powered curation logic — no Streamlit, no session state.
Identical scoring/ordering to the original, adapted to work with
Pydantic Track objects instead of plain dicts.
"""

from __future__ import annotations
import os
import json
import anthropic
from dotenv import load_dotenv
from models import Track, Preferences, PlaylistResult

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL  = "claude-haiku-4-5-20251001"

# ── Language / genre maps (unchanged) ────────────────────────────────────────

LANGUAGE_GENRE_MAP = {
    "spanish": [
        "latin", "reggaeton", "latin pop", "cumbia", "salsa", "bachata",
        "latin trap", "urbano latino", "latin hip hop", "tropical",
        "latin r&b", "latin alternative", "corrido", "norteno",
        "musica mexicana", "latin rock", "flamenco", "latin soul",
        "reggaeton colombiano", "latin arena pop", "spanish pop",
        "latin viral pop", "mexican pop", "dominican pop",
    ],
    "english": [
        "pop", "rock", "hip hop", "r&b", "soul", "country", "indie",
        "alternative", "electronic", "dance", "edm", "house", "metal",
        "jazz", "blues", "folk", "punk", "rap", "trap", "drill",
        "uk pop", "australian pop", "canadian pop", "irish pop",
    ],
    "portuguese": [
        "mpb", "bossa nova", "samba", "forro", "axe", "pagode",
        "sertanejo", "brazilian", "funk carioca", "pagodao",
    ],
    "french": [
        "french pop", "chanson", "variete francaise", "french hip hop",
        "french electronic", "french indie", "french rock",
    ],
}

NON_ENGLISH_MARKERS = (
    LANGUAGE_GENRE_MAP["spanish"]
    + LANGUAGE_GENRE_MAP["portuguese"]
    + LANGUAGE_GENRE_MAP["french"]
    + ["k-pop", "j-pop", "afrobeats", "afropop", "korean", "japanese",
       "arab", "turkish pop", "italian pop", "german pop"]
)


def _language_passes(genres: list[str], language_pref: str) -> bool:
    if not language_pref or language_pref.lower() in ("no preference", ""):
        return True
    if not genres:
        return True
    lang = language_pref.lower()
    genres_lower = [g.lower() for g in genres]
    if "mixed" in lang or ("spanish" in lang and "english" in lang):
        return True
    if "spanish" in lang:
        markers = LANGUAGE_GENRE_MAP["spanish"]
        return any(any(m in g for m in markers) for g in genres_lower)
    if "english" in lang:
        return not any(any(m in g for m in NON_ENGLISH_MARKERS) for g in genres_lower)
    if "portuguese" in lang:
        markers = LANGUAGE_GENRE_MAP["portuguese"]
        return any(any(m in g for m in markers) for g in genres_lower)
    if "french" in lang:
        markers = LANGUAGE_GENRE_MAP["french"]
        return any(any(m in g for m in markers) for g in genres_lower)
    return True


# ── Mood → audio feature targets (Claude call) ───────────────────────────────

def interpret_mood(mood: str, preferences: Preferences) -> dict:
    energy_level = int(preferences.energy) if preferences.energy else 5
    prompt = f"""You are a music data analyst. A user wants a playlist for: "{mood}"

Context:
- Energy slider: {energy_level}/10 (1=very calm, 10=maximum energy)
- Activity: {preferences.activity or "not specified"}
- Extra notes: {preferences.extra or "none"}

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
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    return json.loads(raw[raw.find("{"):raw.rfind("}") + 1])


# ── Per-track scoring ─────────────────────────────────────────────────────────

def _score(track: Track, targets: dict) -> float:
    if track.energy is None:
        return track.popularity / 100 * 2

    def range_score(val, vmin, vmax, weight):
        if val is None:
            return weight * 0.5
        if vmin <= val <= vmax:
            return weight
        dist = min(abs(val - vmin), abs(val - vmax))
        return max(0.0, weight - dist * weight * 3)

    score = 0.0
    score += range_score(track.energy,       targets["energy_min"],       targets["energy_max"],       4.0)
    score += range_score(track.valence,      targets["valence_min"],      targets["valence_max"],       3.0)
    score += range_score(track.danceability, targets["danceability_min"], targets["danceability_max"],  2.0)
    score += range_score(track.acousticness, targets["acousticness_min"], targets["acousticness_max"],  1.0)
    if track.tempo is not None:
        score += range_score(track.tempo, targets["tempo_min"], targets["tempo_max"], 1.5)
    if track.instrumentalness is not None and track.instrumentalness > targets.get("instrumentalness_max", 0.6):
        score -= 2.0
    if track.speechiness is not None and track.speechiness > targets.get("speechiness_max", 0.5):
        score -= 1.5
    score += track.popularity / 200
    return score


# ── Select + order tracks ─────────────────────────────────────────────────────

def select_and_order(
    tracks: list[Track],
    targets: dict,
    preferences: Preferences,
    n: int = 80,
) -> list[Track]:
    include    = [a.strip().lower() for a in preferences.include_artists.split(",") if a.strip()]
    exclude    = [a.strip().lower() for a in preferences.exclude_artists.split(",") if a.strip()]
    language   = preferences.language
    extra_text = preferences.extra.lower()
    no_explicit = "explicit" in extra_text or "clean" in extra_text

    scored: list[tuple[float, Track]] = []
    for track in tracks:
        artist_lower = track.artist.lower()
        if exclude and any(ex in artist_lower for ex in exclude):
            continue
        if no_explicit and track.explicit:
            continue
        if language and language.lower() not in ("no preference", ""):
            if not _language_passes(track.genres, language):
                continue
        s = _score(track, targets)
        if include and any(inc in artist_lower for inc in include):
            s += 3.0
        scored.append((s, track))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [t for _, t in scored[:n]]
    if not top:
        return tracks[:n]

    n3    = max(1, len(top) // 3)
    build = sorted(top[:n3],     key=lambda t: t.energy or 0.5)
    peak  = sorted(top[n3:2*n3], key=lambda t: -(t.energy or 0.5))
    end   = sorted(top[2*n3:],   key=lambda t: t.energy or 0.5)
    return build + peak + end


# ── Name the playlist ─────────────────────────────────────────────────────────

def name_playlist(
    mood: str,
    preferences: Preferences,
    playlist_tracks: list[Track],
    mood_interpretation: str,
) -> dict:
    sample = "\n".join(f"- {t.name} by {t.artist}" for t in playlist_tracks[:15])
    prefs_text = " ".join(filter(None, [
        f"Activity: {preferences.activity}." if preferences.activity else "",
        f"Language: {preferences.language}."  if preferences.language else "",
        f"Notes: {preferences.extra}."        if preferences.extra    else "",
    ]))

    prompt = f"""A playlist was built for: "{mood}"
{f'Context: {prefs_text}' if prefs_text else ''}
Vibe: {mood_interpretation}

Sample tracks:
{sample}

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
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text
        return json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
    except Exception:
        return {
            "playlist_name":        f"{mood} Mix",
            "playlist_description": "A curated playlist for your current mood.",
            "mood_summary":         mood_interpretation,
        }


# ── Public entry point ────────────────────────────────────────────────────────

def build_mood_playlist(
    tracks: list[Track],
    mood: str,
    preferences: Preferences,
) -> PlaylistResult:
    targets             = interpret_mood(mood, preferences)
    mood_interpretation = targets.get("mood_interpretation", "")
    playlist_tracks     = select_and_order(tracks, targets, preferences, n=80)
    naming              = name_playlist(mood, preferences, playlist_tracks, mood_interpretation)
    return PlaylistResult(
        playlist_name=naming["playlist_name"],
        playlist_description=naming["playlist_description"],
        mood_summary=naming["mood_summary"],
        tracks=playlist_tracks,
    )

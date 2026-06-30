"""
Claude-powered curation logic.

Since Spotify's audio-features endpoint is restricted for apps created after
Nov 27 2024, this module does NOT rely on audio features at all.

Instead Claude selects and ranks tracks using its knowledge of songs/artists
combined with mood, preferences, and genre metadata from the Spotify Artists API
(which is still available).
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

# ── Language / genre filtering (works without audio features) ─────────────────

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
        return any(any(m in g for m in LANGUAGE_GENRE_MAP["spanish"]) for g in genres_lower)
    if "english" in lang:
        return not any(any(m in g for m in NON_ENGLISH_MARKERS) for g in genres_lower)
    if "portuguese" in lang:
        return any(any(m in g for m in LANGUAGE_GENRE_MAP["portuguese"]) for g in genres_lower)
    if "french" in lang:
        return any(any(m in g for m in LANGUAGE_GENRE_MAP["french"]) for g in genres_lower)
    return True


# ── Hard-constraint pre-filter (no audio features needed) ────────────────────

def _prefilter(tracks: list[Track], preferences: Preferences) -> list[Track]:
    include    = [a.strip().lower() for a in preferences.include_artists.split(",") if a.strip()]
    exclude    = [a.strip().lower() for a in preferences.exclude_artists.split(",") if a.strip()]
    language   = preferences.language
    extra_text = preferences.extra.lower()
    no_explicit = "explicit" in extra_text or "clean" in extra_text

    filtered = []
    for t in tracks:
        artist_lower = t.artist.lower()
        if exclude and any(ex in artist_lower for ex in exclude):
            continue
        if no_explicit and t.explicit:
            continue
        if language and language.lower() not in ("no preference", ""):
            if not _language_passes(t.genres, language):
                continue
        filtered.append(t)

    return filtered


# ── Claude: select + rank tracks by mood ─────────────────────────────────────

def _claude_select(
    tracks: list[Track],
    mood: str,
    preferences: Preferences,
    n: int = 80,
) -> tuple[list[Track], str]:
    """
    Ask Claude to pick and rank the best `n` tracks from `tracks` for the mood.
    Returns (selected_tracks, mood_interpretation).
    Falls back to popularity sort if Claude fails.
    """
    energy_level = int(preferences.energy) if preferences.energy else 5

    # Build a compact track list for the prompt
    # Format: INDEX | Song Name — Artist | genres
    lines = []
    for i, t in enumerate(tracks):
        genre_str = ", ".join(t.genres[:4]) if t.genres else "unknown"
        lines.append(f"{i} | {t.name} — {t.artist} | {genre_str}")

    track_list = "\n".join(lines)

    include_hint = ""
    if preferences.include_artists.strip():
        include_hint = f"\nPrioritize tracks by: {preferences.include_artists}"

    prompt = f"""You are a music curator. Select the best tracks for this mood/context.

Mood: "{mood}"
Energy level: {energy_level}/10 (1=very calm, 10=maximum energy)
Activity: {preferences.activity or "not specified"}
Extra notes: {preferences.extra or "none"}{include_hint}

Track list (index | name — artist | genres):
{track_list}

Instructions:
- Pick the {n} tracks that best fit the mood, energy level, and activity
- Order them for a great listening experience (build up, peak, wind down)
- Use your knowledge of each song's actual sound and feel
- Prefer variety over clustering the same artist repeatedly
- If fewer than {n} tracks fit well, return only the good ones

Return ONLY this JSON (no other text):
{{
  "indices": [0, 5, 12, ...],
  "mood_interpretation": "one sentence describing what kind of music this calls for"
}}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text
        data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
        indices = [int(i) for i in data.get("indices", []) if 0 <= int(i) < len(tracks)]
        selected = [tracks[i] for i in indices]
        mood_interp = data.get("mood_interpretation", "")

        # If Claude returned too few, pad with popularity-sorted remainder
        if len(selected) < min(n, len(tracks)):
            selected_ids = {t.id for t in selected}
            remainder = sorted(
                [t for t in tracks if t.id not in selected_ids],
                key=lambda t: t.popularity,
                reverse=True,
            )
            selected = selected + remainder[:n - len(selected)]

        return selected[:n], mood_interp

    except Exception as e:
        print(f"[claude_select] failed: {e}", flush=True)
        # Fallback: sort by popularity
        fallback = sorted(tracks, key=lambda t: t.popularity, reverse=True)[:n]
        return fallback, "A curated selection for your mood."


# ── Name the playlist ─────────────────────────────────────────────────────────

def _name_playlist(
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
    # 1. Hard filters (language, explicit, excluded artists) — no audio features needed
    filtered = _prefilter(tracks, preferences)
    if not filtered:
        filtered = tracks  # if all tracks were filtered out, use everything

    # 2. Claude picks + ranks from the filtered pool
    playlist_tracks, mood_interpretation = _claude_select(filtered, mood, preferences, n=80)

    # 3. Name + describe the playlist
    naming = _name_playlist(mood, preferences, playlist_tracks, mood_interpretation)

    return PlaylistResult(
        playlist_name=naming["playlist_name"],
        playlist_description=naming["playlist_description"],
        mood_summary=naming["mood_summary"],
        tracks=playlist_tracks,
    )

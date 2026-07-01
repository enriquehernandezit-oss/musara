"""
Claude-powered curation logic.

Since Spotify's audio-features endpoint is restricted for apps created after
Nov 27 2024, this module does NOT rely on audio features at all.

Instead Claude selects and ranks tracks using its knowledge of songs/artists
combined with mood, preferences, and genre metadata from the Spotify Artists API
(which is still available).

Language preference is NOT enforced via genre-tag filtering — that metadata is
too sparse/unreliable (most tracks have few or no genres) and silently made the
filter a no-op. Instead it's passed to Claude as an explicit instruction so it
can judge a track's actual language from its own knowledge of the song/artist.
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

# ── Hard-constraint pre-filter (no audio features needed) ────────────────────

def _prefilter(tracks: list[Track], preferences: Preferences) -> list[Track]:
    """
    Only apply filters here that are unambiguous and safe to enforce blindly:
    excluded artists and explicit-content exclusion. Language is intentionally
    NOT hard-filtered — genre tags are too sparse/unreliable to gate on, and
    doing so let almost every track through regardless of preference. Instead
    language is handed to Claude as an instruction (see _claude_select), which
    can actually judge a song's language from its own knowledge of the track.
    """
    exclude    = [a.strip().lower() for a in preferences.exclude_artists.split(",") if a.strip()]
    extra_text = preferences.extra.lower()
    no_explicit = "explicit" in extra_text or "clean" in extra_text

    filtered = []
    for t in tracks:
        artist_lower = t.artist.lower()
        if exclude and any(ex in artist_lower for ex in exclude):
            continue
        if no_explicit and t.explicit:
            continue
        filtered.append(t)

    return filtered


# ── Claude: select + rank tracks by mood, and name the playlist ──────────────
#
# This used to be two sequential Claude calls: one to pick/rank tracks, then
# a second to write the name/description/summary from the result of the
# first. Claude already has everything it needs to do both in the same
# response (it just decided the tracks and can justify them in the same
# breath), so this is now a single call — cuts a full network round trip off
# every /generate request.

def _claude_curate(
    tracks: list[Track],
    mood: str,
    preferences: Preferences,
    n: int = 80,
) -> tuple[list[Track], dict]:
    """
    Ask Claude to pick and rank the best `n` tracks from `tracks` for the mood,
    and name/describe the resulting playlist in the same call.
    Returns (selected_tracks, naming_dict) where naming_dict has
    playlist_name / playlist_description / mood_summary.
    """
    energy_level = int(preferences.energy) if preferences.energy else 5

    # Cap how many tracks we ask Claude to pick — always force real filtering
    target = min(n, max(10, int(len(tracks) * 0.65)))

    # Build compact track list: INDEX | Song — Artist | genres
    lines = []
    for i, t in enumerate(tracks):
        genre_str = ", ".join(t.genres[:3]) if t.genres else ""
        lines.append(f"{i} | {t.name} — {t.artist}{' | ' + genre_str if genre_str else ''}")

    track_list = "\n".join(lines)

    include_hint = ""
    if preferences.include_artists.strip():
        include_hint = f"\nPrioritize tracks by: {preferences.include_artists}"

    # Precise per-level calibration instead of coarse 5-way buckets — this
    # gives Claude concrete reference points for tempo/production/intensity
    # at each of the 10 levels so the slider actually moves the needle.
    ENERGY_CALIBRATION = {
        1:  "extremely low energy — sparse, hushed, almost ambient (think: solo piano, whispered vocals, minimal percussion)",
        2:  "very low energy — slow, intimate, soft dynamics (think: quiet acoustic ballads)",
        3:  "low energy — relaxed and mellow, gentle groove, no urgency",
        4:  "low-moderate energy — laid-back but with some rhythmic movement (think: chill R&B, soft indie)",
        5:  "moderate energy — comfortable mid-tempo, present but not driving",
        6:  "moderate-high energy — clear rhythmic drive, upbeat but not aggressive",
        7:  "high energy — upbeat, propulsive, strong beat, makes you want to move",
        8:  "very high energy — fast, punchy, dense production, hard-hitting drums/bass",
        9:  "intense energy — aggressive, loud, high tempo, adrenaline-driving",
        10: "maximum intensity — full-throttle, hardest-hitting, most explosive tracks available",
    }
    energy_desc = ENERGY_CALIBRATION[max(1, min(10, energy_level))]

    language_pref = (preferences.language or "").strip()
    language_section = ""
    if language_pref and language_pref.lower() not in ("no preference", ""):
        language_section = f"""
LANGUAGE: {language_pref}
   - Only select tracks whose vocals/lyrics match this language preference.
   - Judge this from your own knowledge of the actual song and artist — do
     NOT rely on the genre tags shown below, they are unreliable and often
     missing. Genre tags are only a weak supporting hint, never decisive.
   - If you don't recognize a track well enough to know its language with
     confidence, leave it out rather than guessing.
   - If the preference says "mixed" or names two+ languages, tracks in any
     of those languages are acceptable."""

    prompt = f"""You are a music curator building a mood playlist. Be selective and opinionated.

MOOD (from the user, verbatim): "{mood}"
   - If this reads as a short label (e.g. "Hype", "Chill", "Sad"), interpret it directly.
   - If this reads as a descriptive phrase or sentence (e.g. "late-night drive",
     "pre-match warmup", "slow Sunday morning coffee"), treat it as richer context:
     infer the implied setting, time of day, activity, and emotional arc, and let
     those inferences drive track choice as much as the literal words do. Prioritize
     the *feeling* the description is going for over keyword-matching individual words.
ENERGY: {energy_level}/10 — {energy_desc}
   - Treat this as a hard constraint, not a suggestion: reject tracks whose actual
     tempo/production intensity clearly doesn't match this level, even if the mood
     otherwise fits.
ACTIVITY: {preferences.activity or "not specified"}
NOTES: {preferences.extra or "none"}{include_hint}{language_section}

TRACK POOL ({len(tracks)} tracks):
{track_list}

YOUR TASK:
1. Pick EXACTLY {target} tracks that genuinely fit the mood, energy level, and
   language preference above.
   - REJECT tracks that don't match — be ruthless, not every track belongs.
   - Use your knowledge of each song's actual sound, tempo, language, and emotional feel.
   - Do NOT just keep them in the order they appear — the input order is meaningless.

2. ORDER the selected tracks intentionally:
   - Start with tracks that ease the listener in
   - Build to the most fitting tracks in the middle
   - Wind down or peak at the end depending on the mood
   - Never cluster the same artist back-to-back

3. Name and describe the playlist you just built.

Return ONLY valid JSON, no other text:
{{
  "indices": [14, 3, 27, 8, ...],
  "mood_interpretation": "one sentence on what this mood calls for musically",
  "playlist_name": "2-4 word creative name",
  "playlist_description": "one punchy sentence describing the vibe",
  "mood_summary": "2 sentences on the listening experience and energy arc"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    print(f"[claude_curate] raw response: {raw[:400]}", flush=True)

    data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
    indices = [int(i) for i in data.get("indices", []) if 0 <= int(i) < len(tracks)]
    print(f"[claude_curate] selected {len(indices)} tracks from {len(tracks)}", flush=True)

    selected = [tracks[i] for i in indices]
    mood_interp = data.get("mood_interpretation", "")

    # Pad only if drastically short
    min_acceptable = max(5, target // 2)
    if len(selected) < min_acceptable:
        selected_ids = {t.id for t in selected}
        remainder = sorted(
            [t for t in tracks if t.id not in selected_ids],
            key=lambda t: t.popularity,
            reverse=True,
        )
        selected = selected + remainder[:target - len(selected)]

    naming = {
        "playlist_name":        data.get("playlist_name") or f"{mood} Mix",
        "playlist_description": data.get("playlist_description") or "A curated playlist for your current mood.",
        "mood_summary":         data.get("mood_summary") or mood_interp,
    }

    return selected[:target], naming


# ── Public entry point ────────────────────────────────────────────────────────

def build_mood_playlist(
    tracks: list[Track],
    mood: str,
    preferences: Preferences,
) -> PlaylistResult:
    # 1. Hard filters (explicit, excluded artists) — no audio features needed
    filtered = _prefilter(tracks, preferences)
    if not filtered:
        filtered = tracks  # if all tracks were filtered out, use everything

    # 2. Claude picks + ranks from the filtered pool, and names the result
    playlist_tracks, naming = _claude_curate(filtered, mood, preferences, n=80)

    return PlaylistResult(
        playlist_name=naming["playlist_name"],
        playlist_description=naming["playlist_description"],
        mood_summary=naming["mood_summary"],
        tracks=playlist_tracks,
    )

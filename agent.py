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

def build_mood_playlist(tracks, mood, preferences=None):
    track_list = ""
    for i, track in enumerate(tracks):
        energy       = track.get("energy")
        valence      = track.get("valence")
        danceability = track.get("danceability")
        tempo        = track.get("tempo")
        acousticness = track.get("acousticness")
        instrumental = track.get("instrumentalness")

        audio_str = ""
        if energy is not None:
            audio_str = (
                f" [energy:{energy} valence:{valence} "
                f"dance:{danceability} bpm:{tempo} "
                f"acoustic:{acousticness} instrumental:{instrumental}]"
            )

        track_list += (
            f"{i}. {track['name']} by {track['artist']}"
            f" (album: {track['album']}, popularity: {track['popularity']})"
            f"{audio_str}\n"
        )

    prefs_text = ""
    if preferences:
        activity    = preferences.get("activity", "")
        energy_lvl  = preferences.get("energy", "")
        language    = preferences.get("language", "")
        include     = preferences.get("include_artists", "")
        exclude     = preferences.get("exclude_artists", "")
        extra       = preferences.get("extra", "")

        if activity:    prefs_text += f"- Activity: {activity}\n"
        if energy_lvl:  prefs_text += f"- Energy level requested: {energy_lvl}/10\n"
        if language:    prefs_text += f"- Language preference: {language}\n"
        if include:     prefs_text += f"- Prioritize tracks by: {include}\n"
        if exclude:     prefs_text += f"- Exclude tracks by: {exclude}\n"
        if extra:       prefs_text += f"- Additional: {extra}\n"

    prompt = f"""You are a professional music curator AI with deep knowledge of music theory, audio characteristics, and mood psychology.

A user is feeling: "{mood}"

User preferences:
{prefs_text if prefs_text else "No additional preferences provided."}

Here is their track library with Spotify audio features:
- energy: 0.0 (very calm) to 1.0 (very intense)
- valence: 0.0 (sad/dark) to 1.0 (happy/euphoric)
- dance: 0.0 (not danceable) to 1.0 (very danceable)
- bpm: beats per minute
- acoustic: 0.0 (electronic) to 1.0 (fully acoustic)
- instrumental: 0.0 (vocal) to 1.0 (fully instrumental)

TRACKS:
{track_list}

CURATION RULES:

Mood to audio feature mapping:
- Hype/Party: energy > 0.7, valence > 0.5, dance > 0.6, bpm > 120
- Chill/Relax: energy < 0.5, valence 0.3-0.7, bpm < 100
- Focus/Study: instrumental > 0.3, energy 0.3-0.6, speechiness < 0.1
- Sad/Melancholic: valence < 0.4, energy < 0.5, acoustic > 0.3
- Nostalgic: valence 0.4-0.7, energy 0.3-0.6, acoustic > 0.2
- Romantic: valence 0.4-0.7, energy 0.2-0.5, dance 0.3-0.6

Energy level mapping (user requested {preferences.get('energy', '5') if preferences else '5'}/10):
- 1-2: energy < 0.3
- 3-4: energy 0.3-0.5
- 5-6: energy 0.5-0.7
- 7-8: energy 0.7-0.85
- 9-10: energy > 0.85

Instructions:
1. Use the audio features as your PRIMARY filter — they are objective measurements
2. Select exactly 80 tracks (or all tracks if fewer than 80 available)
3. Order them for the best listening experience — start at medium energy, build to peak, cool down
4. Respect ALL user preferences strictly
5. If audio features are missing for a track, use your knowledge of the artist/song to estimate
6. Return ONLY a JSON object

Return this exact structure:
{{
  "playlist_name": "creative name reflecting mood and activity",
  "playlist_description": "one sentence describing the vibe",
  "selected_indices": [list of integer indices in playback order],
  "mood_summary": "2-3 sentences explaining the curation logic and how the playlist flows"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text
    start = raw.find("{")
    end = raw.rfind("}") + 1
    parsed = json.loads(raw[start:end])
    return parsed
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

def build_mood_playlist(tracks, mood, custom_mood=None):
    mood_description = custom_mood if custom_mood else mood

    track_list = ""
    for i, track in enumerate(tracks):
        track_list += f"{i}. {track['name']} by {track['artist']} (album: {track['album']}, popularity: {track['popularity']})\n"

    prompt = f"""You are a music curator AI. A user is feeling: "{mood_description}"

Here is their full track library pulled from their Spotify playlists:

{track_list}

Your job:
1. Select the 20-30 tracks that best match the mood "{mood_description}"
2. Order them for the best listening experience — consider energy flow, tempo progression, emotional arc
3. For each selected track return the original index number from the list above

Rules:
- Only select tracks from the list above — no invented tracks
- Think about the emotional energy of each song name and artist
- Consider how songs flow together — don't just pick randomly
- Return ONLY a JSON object, no markdown, no explanation

Return this exact JSON structure:
{{
  "playlist_name": "a creative playlist name that reflects the mood",
  "playlist_description": "a one sentence description of the vibe",
  "selected_indices": [list of integer indices in the order they should be played],
  "mood_summary": "2-3 sentences explaining why these tracks fit this mood and how the playlist flows"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text
    start = raw.find("{")
    end = raw.rfind("}") + 1
    parsed = json.loads(raw[start:end])
    return parsed

def score_recommendations(recommendations, mood, existing_tracks):
    mood_description = mood

    existing_sample = ", ".join([
        f"{t['name']} by {t['artist']}"
        for t in existing_tracks[:10]
    ])

    rec_list = ""
    for i, track in enumerate(recommendations):
        rec_list += f"{i}. {track['name']} by {track['artist']} (album: {track['album']})\n"

    prompt = f"""You are a music curator AI. A user is feeling: "{mood_description}"

Their current mood playlist already includes tracks like:
{existing_sample}

Here are Spotify's recommended tracks that could be added:
{rec_list}

Select the 8-10 recommendations that would best complement the existing playlist and match the mood.
Order them from best fit to least fit.

Return ONLY a JSON object:
{{
  "selected_indices": [list of integer indices ordered by fit],
  "reasoning": "one sentence explaining the overall recommendation logic"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text
    start = raw.find("{")
    end = raw.rfind("}") + 1
    parsed = json.loads(raw[start:end])
    return parsed
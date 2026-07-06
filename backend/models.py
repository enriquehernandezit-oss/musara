from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


# ── Auth ──────────────────────────────────────────────────────────────────────

class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int          # unix timestamp


# ── Spotify entities ──────────────────────────────────────────────────────────

class UserProfile(BaseModel):
    id: str
    display_name: str
    email: Optional[str] = None
    image_url: Optional[str] = None


class Playlist(BaseModel):
    id: str
    name: str
    image: Optional[str] = None
    owner: str


class Track(BaseModel):
    id: str
    name: str
    artist: str
    artist_id: Optional[str] = None
    album: str
    image: Optional[str] = None
    uri: str
    preview_url: Optional[str] = None
    popularity: int = 0
    explicit: bool = False
    # audio features (populated after enrichment)
    energy: Optional[float] = None
    valence: Optional[float] = None
    danceability: Optional[float] = None
    tempo: Optional[float] = None
    acousticness: Optional[float] = None
    instrumentalness: Optional[float] = None
    loudness: Optional[float] = None
    speechiness: Optional[float] = None
    genres: list[str] = []


# ── Generate request / response ───────────────────────────────────────────────

class Preferences(BaseModel):
    activity: str = ""
    energy: str = "5"          # "1"–"10" as string (matches existing agent contract)
    language: str = ""
    include_artists: str = ""
    exclude_artists: str = ""
    extra: str = ""


class GenerateRequest(BaseModel):
    mood: str
    playlist_ids: list[str]
    preferences: Preferences = Preferences()


class PlaylistResult(BaseModel):
    playlist_name: str
    playlist_description: str
    mood_summary: str
    tracks: list[Track]


# ── Guest generate (no Spotify account required) ──────────────────────────────
# Claude builds a playlist purely from its own music knowledge — no Spotify
# track pool involved, so there's no library to filter from. The extra
# filters exist to narrow down what Claude picks since there's no real
# tracklist to constrain it.

class GuestPreferences(BaseModel):
    activity: str = ""
    energy: str = "5"
    language: str = ""
    genre: str = ""
    decade: str = ""           # e.g. "2010s", "90s", "no preference"
    include_artists: str = ""
    exclude_artists: str = ""
    extra: str = ""
    track_count: int = 20


class GuestGenerateRequest(BaseModel):
    mood: str
    preferences: GuestPreferences = GuestPreferences()


# ── Export request / response ─────────────────────────────────────────────────

class ExportRequest(BaseModel):
    name: str
    description: str
    track_uris: list[str]


class ExportResult(BaseModel):
    id: str
    url: str
    name: str

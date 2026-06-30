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


# ── Export request / response ─────────────────────────────────────────────────

class ExportRequest(BaseModel):
    name: str
    description: str
    track_uris: list[str]


class ExportResult(BaseModel):
    id: str
    url: str
    name: str

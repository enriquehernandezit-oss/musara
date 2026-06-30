"""
Musara – FastAPI backend

Endpoints
─────────
GET  /auth/login-url          → { url }
GET  /auth/callback           → redirects to frontend with token params
POST /auth/refresh            → { access_token, expires_at }
GET  /me                      → UserProfile
GET  /playlists               → list[Playlist]
POST /generate                → PlaylistResult
POST /export                  → ExportResult

Auth
────
After the OAuth callback the frontend receives access_token, refresh_token,
and expires_at as query params and stores them in localStorage.
Subsequent requests include:
  Authorization: Bearer <access_token>
The /auth/refresh endpoint accepts the refresh_token in the request body and
returns a new access_token.
"""

from __future__ import annotations
import os
import time
from urllib.parse import urlencode

import spotipy
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

import auth as oauth
import spotify as sp_api
import agent as ai
from models import (
    Playlist, UserProfile,
    GenerateRequest, PlaylistResult,
    ExportRequest, ExportResult,
)

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app = FastAPI(title="Musara API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer = HTTPBearer()


def get_spotify(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> spotipy.Spotify:
    return oauth.make_spotify_client(creds.credentials)


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.get("/auth/login-url")
def login_url() -> dict:
    """Return the Spotify OAuth authorize URL."""
    return {"url": oauth.get_login_url()}


@app.get("/auth/callback")
def callback(code: str):
    """
    Spotify redirects here after the user authorizes.
    Exchange the code, then redirect to the frontend with tokens in the query string.
    """
    try:
        token_info = oauth.exchange_code(code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {exc}")

    params = urlencode({
        "access_token":  token_info["access_token"],
        "refresh_token": token_info["refresh_token"],
        "expires_at":    token_info.get("expires_at", int(time.time()) + 3600),
    })
    return RedirectResponse(url=f"{FRONTEND_URL}/callback?{params}")


@app.post("/auth/refresh")
def refresh(body: dict) -> dict:
    """
    Body: { "refresh_token": "..." }
    Returns: { "access_token": "...", "expires_at": 1234567890 }
    """
    refresh_tok = body.get("refresh_token")
    if not refresh_tok:
        raise HTTPException(status_code=400, detail="refresh_token required")
    try:
        token_info = oauth.refresh_token(refresh_tok)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Refresh failed: {exc}")
    return {
        "access_token": token_info["access_token"],
        "expires_at":   token_info.get("expires_at", int(time.time()) + 3600),
    }


# ── User ──────────────────────────────────────────────────────────────────────

@app.get("/me", response_model=UserProfile)
def me(sp: spotipy.Spotify = Depends(get_spotify)) -> UserProfile:
    try:
        return sp_api.get_user_profile(sp)
    except spotipy.SpotifyException as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail=str(exc))


# ── Playlists ─────────────────────────────────────────────────────────────────

@app.get("/playlists", response_model=list[Playlist])
def playlists(sp: spotipy.Spotify = Depends(get_spotify)) -> list[Playlist]:
    try:
        return sp_api.get_all_playlists(sp)
    except spotipy.SpotifyException as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail=str(exc))


# ── Generate ──────────────────────────────────────────────────────────────────

@app.post("/generate", response_model=PlaylistResult)
def generate(
    body: GenerateRequest,
    sp: spotipy.Spotify = Depends(get_spotify),
) -> PlaylistResult:
    if not body.mood:
        raise HTTPException(status_code=422, detail="mood is required")
    if not body.playlist_ids:
        raise HTTPException(status_code=422, detail="playlist_ids must not be empty")

    # 1. Fetch raw tracks
    try:
        tracks = sp_api.fetch_tracks_from_playlists(sp, body.playlist_ids, max_total=400)
    except spotipy.SpotifyException as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail=str(exc))

    if not tracks:
        raise HTTPException(status_code=404, detail="No tracks found in the selected playlists")

    print(f"[generate] fetched {len(tracks)} tracks, enriching...", flush=True)

    # 2. Enrich with genres (audio features skipped — deprecated for new Spotify apps)
    tracks = sp_api.enrich_with_genres(sp, tracks)

    # 3. Claude curation
    try:
        result = ai.build_mood_playlist(tracks, body.mood, body.preferences)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Curation failed: {exc}")

    return result


# ── Export ────────────────────────────────────────────────────────────────────

@app.post("/export", response_model=ExportResult)
def export(
    body: ExportRequest,
    sp: spotipy.Spotify = Depends(get_spotify),
) -> ExportResult:
    if not body.track_uris:
        raise HTTPException(status_code=422, detail="track_uris must not be empty")
    try:
        result = sp_api.create_playlist(sp, body.name, body.description, body.track_uris)
    except spotipy.SpotifyException as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail=str(exc))
    return ExportResult(**result)


# ── Debug ─────────────────────────────────────────────────────────────────────

@app.get("/debug/audio-features")
def debug_audio_features(
    track_id: str = "3n3Ppam7vgaVa1iaRUIOKE",  # default: Mr. Brightside
    sp: spotipy.Spotify = Depends(get_spotify),
) -> dict:
    """
    Hit audio-features for one track and return the raw result.
    Use this to verify whether your Spotify app can access the endpoint.
    GET /debug/audio-features?track_id=<spotify_track_id>
    """
    return sp_api.probe_audio_features(sp, track_id)


# ── Dev entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

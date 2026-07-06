"""
Spotify OAuth helpers — stateless, no Streamlit.

Token flow:
  1. Frontend calls GET /auth/login-url  → receives the Spotify authorize URL
  2. Spotify redirects to REDIRECT_URI   → GET /auth/callback?code=...
  3. Backend exchanges code, then HTTP-redirects to FRONTEND_URL with
     token params in the query string:
       ?access_token=...&refresh_token=...&expires_at=...
  4. Frontend stores tokens (localStorage) and passes them as
       Authorization: Bearer <access_token>
     on every subsequent API request.
"""

import os
import time
from typing import Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()

SCOPE = (
    "playlist-read-private "
    "playlist-read-collaborative "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-library-read"
)


def _make_oauth() -> SpotifyOAuth:
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("REDIRECT_URI"),
        scope=SCOPE,
        cache_path=None,    # no file cache — tokens travel with the request
        show_dialog=True,
    )


def get_login_url() -> str:
    return _make_oauth().get_authorize_url()


def exchange_code(code: str) -> dict:
    """Exchange an auth code for token_info dict."""
    oauth = _make_oauth()
    token_info = oauth.get_access_token(code, as_dict=True)
    return token_info


def refresh_token(refresh_tok: str) -> dict:
    """Use a refresh token to get a new access token."""
    oauth = _make_oauth()
    token_info = oauth.refresh_access_token(refresh_tok)
    return token_info


def is_expired(token_info: dict) -> bool:
    return token_info.get("expires_at", 0) < time.time() + 60


def make_spotify_client(access_token: str) -> spotipy.Spotify:
    return spotipy.Spotify(auth=access_token)


# ── App-only client (no user login) ───────────────────────────────────────────
# Client Credentials flow — used for guest mode, where there's no logged-in
# user to authorize as. Only grants access to public catalog data (search,
# tracks, albums, artists) — no playlist read/write or user data.

_app_client: Optional[spotipy.Spotify] = None


def get_app_spotify_client() -> spotipy.Spotify:
    global _app_client
    if _app_client is None:
        creds = SpotifyClientCredentials(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        )
        _app_client = spotipy.Spotify(client_credentials_manager=creds)
    return _app_client

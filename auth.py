import os
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

SCOPE = (
    "playlist-read-private "
    "playlist-read-collaborative "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-library-read"
)

def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("REDIRECT_URI"),
        scope=SCOPE,
        cache_path=".spotify_cache",
        show_dialog=True
    )

def get_auth_url():
    sp_oauth = get_spotify_oauth()
    return sp_oauth.get_authorize_url()

def handle_callback(code):
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.get_access_token(code)
    st.session_state["token_info"] = token_info
    return token_info

def get_spotify_client():
    if "token_info" not in st.session_state:
        return None
    sp_oauth = get_spotify_oauth()
    token_info = st.session_state["token_info"]
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(
            token_info["refresh_token"]
        )
        st.session_state["token_info"] = token_info
    return spotipy.Spotify(auth=token_info["access_token"])

def is_logged_in():
    return "token_info" in st.session_state

def logout():
    if "token_info" in st.session_state:
        del st.session_state["token_info"]
    if os.path.exists(".spotify_cache"):
        os.remove(".spotify_cache")
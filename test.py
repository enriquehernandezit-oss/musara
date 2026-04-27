import os
from dotenv import load_dotenv
load_dotenv()
import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
    redirect_uri=os.getenv('REDIRECT_URI'),
    scope='playlist-read-private playlist-read-collaborative',
    cache_path='.spotify_cache'
))

try:
    results = sp.playlist_tracks("4mO3IsHVg72mdHoPjVAnCk", limit=3)
    print("tracks:", len(results['items']))
    for item in results['items']:
        if item.get('track'):
            print(" -", item['track']['name'])
except Exception as e:
    print("ERROR:", e)

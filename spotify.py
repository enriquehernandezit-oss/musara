import streamlit as st
from auth import get_spotify_client

def get_user_profile():
    sp = get_spotify_client()
    if not sp:
        return None
    return sp.current_user()

def get_all_playlists():
    sp = get_spotify_client()
    if not sp:
        return []
    try:
        current_user = sp.current_user()
        user_id = current_user["id"]
    except Exception as e:
        st.error(f"Could not get user profile: {e}")
        return []
    playlists = []
    try:
        results = sp.current_user_playlists(limit=50)
    except Exception as e:
        st.error(f"Could not load playlists: {e}")
        return []
    while results:
        for item in results["items"]:
            if item:
                owner_id = item.get("owner", {}).get("id", "")
                if owner_id == user_id:
                    playlists.append({
                        "id": item["id"],
                        "name": item["name"],
                        "image": item["images"][0]["url"] if item["images"] else None,
                        "owner": item["owner"]["display_name"]
                    })
        if results["next"]:
            try:
                results = sp.next(results)
            except Exception:
                break
        else:
            break
    return playlists

def get_recommendations(seed_track_ids, mood_description, limit=20):
    sp = get_spotify_client()
    if not sp:
        return []
    seed_tracks = seed_track_ids[:5]
    try:
        results = sp.recommendations(
            seed_tracks=seed_tracks,
            limit=limit
        )
        recommendations = []
        for track in results["tracks"]:
            recommendations.append({
                "id": track["id"],
                "name": track["name"],
                "artist": track["artists"][0]["name"] if track["artists"] else "Unknown",
                "album": track["album"]["name"],
                "image": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                "uri": track["uri"],
                "preview_url": track.get("preview_url"),
                "popularity": track.get("popularity", 0)
            })
        return recommendations
    except Exception:
        return []

def create_spotify_playlist(name, description, track_uris):
    sp = get_spotify_client()
    if not sp:
        return None
    user = sp.current_user()
    user_id = user["id"]
    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
        description=description
    )
    playlist_id = playlist["id"]
    for i in range(0, len(track_uris), 100):
        batch = track_uris[i:i+100]
        sp.playlist_add_items(playlist_id, batch)
    return {
        "id": playlist_id,
        "url": playlist["external_urls"]["spotify"],
        "name": name
    }
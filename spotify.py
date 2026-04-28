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

def enrich_tracks_with_audio_features(tracks):
    sp = get_spotify_client()
    if not sp or not tracks:
        return tracks
    track_ids = [t["id"] for t in tracks]
    features_map = {}
    # fetch in batches of 100 (Spotify limit)
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        try:
            features = sp.audio_features(batch)
            if features:
                for f in features:
                    if f and f.get("id"):
                        features_map[f["id"]] = {
                            "energy":           round(f.get("energy", 0), 2),
                            "valence":          round(f.get("valence", 0), 2),
                            "danceability":     round(f.get("danceability", 0), 2),
                            "tempo":            round(f.get("tempo", 0)),
                            "acousticness":     round(f.get("acousticness", 0), 2),
                            "instrumentalness": round(f.get("instrumentalness", 0), 2),
                            "loudness":         round(f.get("loudness", 0), 1),
                            "speechiness":      round(f.get("speechiness", 0), 2),
                        }
        except Exception:
            continue
    # merge features into tracks
    enriched = []
    for track in tracks:
        t = track.copy()
        f = features_map.get(track["id"], {})
        t["energy"]           = f.get("energy", None)
        t["valence"]          = f.get("valence", None)
        t["danceability"]     = f.get("danceability", None)
        t["tempo"]            = f.get("tempo", None)
        t["acousticness"]     = f.get("acousticness", None)
        t["instrumentalness"] = f.get("instrumentalness", None)
        t["loudness"]         = f.get("loudness", None)
        t["speechiness"]      = f.get("speechiness", None)
        enriched.append(t)
    return enriched

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
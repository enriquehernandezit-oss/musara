"""
Pure Spotify API wrappers — no Streamlit, no session state.
Every function receives a spotipy.Spotify client (already authenticated).
"""

from __future__ import annotations
import spotipy
from models import Track, Playlist, UserProfile


# ── User ──────────────────────────────────────────────────────────────────────

def get_user_profile(sp: spotipy.Spotify) -> UserProfile:
    data = sp.current_user()
    image_url = None
    if data.get("images"):
        image_url = data["images"][0].get("url")
    return UserProfile(
        id=data["id"],
        display_name=data.get("display_name") or data["id"],
        email=data.get("email"),
        image_url=image_url,
    )


# ── Playlists ─────────────────────────────────────────────────────────────────

def get_all_playlists(sp: spotipy.Spotify) -> list[Playlist]:
    current_user = sp.current_user()
    user_id = current_user["id"]

    playlists: list[Playlist] = []
    results = sp.current_user_playlists(limit=50)
    while results:
        for item in results["items"]:
            if not item:
                continue
            if item.get("owner", {}).get("id") == user_id:
                playlists.append(Playlist(
                    id=item["id"],
                    name=item["name"],
                    image=item["images"][0]["url"] if item.get("images") else None,
                    owner=item["owner"].get("display_name", user_id),
                ))
        if results["next"]:
            results = sp.next(results)
        else:
            break
    return playlists


# ── Track fetching ────────────────────────────────────────────────────────────

def fetch_tracks_from_playlists(
    sp: spotipy.Spotify,
    playlist_ids: list[str],
    max_total: int = 400,
) -> list[Track]:
    tracks: list[Track] = []
    seen: set[str] = set()

    for pid in playlist_ids:
        results = sp.playlist_tracks(pid, limit=50)
        count = 0
        while results and len(tracks) < max_total:
            for item in results["items"]:
                if len(tracks) >= max_total:
                    break
                if not item:
                    continue
                raw = item.get("track") or item.get("item")
                if not raw or not raw.get("id"):
                    continue
                if raw["id"] in seen:
                    continue
                seen.add(raw["id"])
                artists = raw.get("artists") or []
                album   = raw.get("album") or {}
                images  = album.get("images") or []
                tracks.append(Track(
                    id=raw["id"],
                    name=raw["name"],
                    artist=artists[0]["name"] if artists else "Unknown",
                    artist_id=artists[0]["id"] if artists else None,
                    album=album.get("name", "Unknown"),
                    image=images[0]["url"] if images else None,
                    uri=raw["uri"],
                    preview_url=raw.get("preview_url"),
                    popularity=raw.get("popularity", 0),
                    explicit=raw.get("explicit", False),
                ))
                count += 1
            if results["next"] and len(tracks) < max_total:
                results = sp.next(results)
            else:
                break

    return tracks


# ── Audio features ────────────────────────────────────────────────────────────

def enrich_with_audio_features(
    sp: spotipy.Spotify,
    tracks: list[Track],
) -> tuple[list[Track], str | None]:
    """
    Returns (enriched_tracks, error_message).
    error_message is None on success, a human-readable string if the API call failed.
    """
    ids = [t.id for t in tracks]
    features_map: dict[str, dict] = {}
    last_error: str | None = None

    for i in range(0, len(ids), 100):
        batch = ids[i:i + 100]
        try:
            features = sp.audio_features(batch)
            if features:
                for f in features:
                    if f and f.get("id"):
                        features_map[f["id"]] = {
                            "energy":           round(f.get("energy",           0), 2),
                            "valence":          round(f.get("valence",          0), 2),
                            "danceability":     round(f.get("danceability",     0), 2),
                            "tempo":            round(f.get("tempo",            0)),
                            "acousticness":     round(f.get("acousticness",     0), 2),
                            "instrumentalness": round(f.get("instrumentalness", 0), 2),
                            "loudness":         round(f.get("loudness",         0), 1),
                            "speechiness":      round(f.get("speechiness",      0), 2),
                        }
            else:
                last_error = "Spotify returned an empty audio-features response"
                print(f"[audio_features] empty response for batch {i//100}", flush=True)
        except Exception as e:
            last_error = str(e)
            print(f"[audio_features] error on batch {i//100}: {e}", flush=True)
            continue

    print(f"[audio_features] populated features for {len(features_map)}/{len(ids)} tracks", flush=True)

    enriched: list[Track] = []
    for t in tracks:
        f = features_map.get(t.id, {})
        enriched.append(t.model_copy(update={
            "energy":           f.get("energy"),
            "valence":          f.get("valence"),
            "danceability":     f.get("danceability"),
            "tempo":            f.get("tempo"),
            "acousticness":     f.get("acousticness"),
            "instrumentalness": f.get("instrumentalness"),
            "loudness":         f.get("loudness"),
            "speechiness":      f.get("speechiness"),
        }))
    return enriched, last_error if not features_map else None


def probe_audio_features(sp: spotipy.Spotify, track_id: str) -> dict:
    """Hit the API with a single track and return the raw result — for debugging."""
    try:
        result = sp.audio_features([track_id])
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e), "type": type(e).__name__}

    enriched: list[Track] = []
    for t in tracks:
        f = features_map.get(t.id, {})
        enriched.append(t.model_copy(update={
            "energy":           f.get("energy"),
            "valence":          f.get("valence"),
            "danceability":     f.get("danceability"),
            "tempo":            f.get("tempo"),
            "acousticness":     f.get("acousticness"),
            "instrumentalness": f.get("instrumentalness"),
            "loudness":         f.get("loudness"),
            "speechiness":      f.get("speechiness"),
        }))
    return enriched


# ── Genre enrichment ──────────────────────────────────────────────────────────

def enrich_with_genres(sp: spotipy.Spotify, tracks: list[Track]) -> list[Track]:
    artist_ids = list({t.artist_id for t in tracks if t.artist_id})
    genres_map: dict[str, list[str]] = {}

    for i in range(0, len(artist_ids), 50):
        batch = [aid for aid in artist_ids[i:i + 50] if aid]
        if not batch:
            continue
        try:
            result = sp.artists(batch)
            for artist in result.get("artists", []):
                if artist:
                    genres_map[artist["id"]] = artist.get("genres", [])
        except Exception:
            continue

    return [
        t.model_copy(update={"genres": genres_map.get(t.artist_id, [])})
        for t in tracks
    ]


# ── Export ────────────────────────────────────────────────────────────────────

def create_playlist(
    sp: spotipy.Spotify,
    name: str,
    description: str,
    track_uris: list[str],
) -> dict:
    user = sp.current_user()
    playlist = sp.user_playlist_create(
        user=user["id"],
        name=name,
        public=False,
        description=description,
    )
    pid = playlist["id"]
    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(pid, track_uris[i:i + 100])
    return {
        "id":   pid,
        "url":  playlist["external_urls"]["spotify"],
        "name": name,
    }

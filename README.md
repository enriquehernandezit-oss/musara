# Musara

🔗 Live app → [musara.up.railway.app](https://musara.up.railway.app)

## Demo

`Musara.Demo.mp4`

**Turn your Spotify library into a mood-matched playlist.**

Musara reads your Spotify playlists, asks how you're feeling and what energy level you're after, and has Claude curate and reorder a brand-new playlist from your own tracks that actually fits — then exports it straight back to your Spotify account.

## What Problem It Solves

Spotify's own audio-features API — the thing most mood-playlist tools relied on to score tracks by energy, valence, and tempo — was deprecated for apps created after November 27, 2024. Most "mood playlist" projects built after that date are stuck with either genre tags (unreliable) or no scoring at all.

Musara works around this by not needing audio features in the first place: Claude curates using its own knowledge of each track's actual sound, tempo, and emotional feel, combined with your stated mood, energy level, activity, and language preference — no deprecated endpoint required.

## What It Produces

For any combination of playlists and a mood, Musara outputs:

- **A curated tracklist** — pulled and filtered from your own playlists, not a generic recommendation engine
- **An intentional track order** — eased in, built up, and wound down instead of shuffled or left in original playlist order
- **A generated name + description** — written by Claude to match the vibe it just built
- **A one-click export** — pushes the result directly into a new playlist on your Spotify account

## How It Works

1. **OAuth** — you connect your Spotify account (playlist read/write scopes only)
2. **Fetch** — Musara pulls every track from your selected playlists (up to 100 tracks per playlist, fetched concurrently)
3. **Enrich** — artist genres are pulled from Spotify's Artists API and cached in-memory for repeat generations
4. **Curate** — a single Claude call picks, ranks, and reorders tracks against your mood, energy (1–10, precisely calibrated per level), activity, language preference, and free-text description — then names the resulting playlist in the same response
5. **Export** — the finished playlist is created directly in your Spotify library

| Component | Job |
|---|---|
| Spotify Web API | Playlist + track + genre data, OAuth, playlist creation |
| Claude API (Haiku 4.5) | Track selection, ranking, and playlist naming |
| FastAPI backend | Stateless OAuth flow, Spotify wrapper, curation orchestration |
| React + Vite frontend | Mood/energy/preferences UI, results view, export flow |

## Tech Stack

| Tool | Purpose |
|---|---|
| Python + FastAPI | Backend API |
| Spotipy | Spotify Web API client |
| Claude API (Haiku 4.5) | Mood-based track curation + naming |
| React + Vite + TypeScript | Frontend |
| React Router | Client-side routing |
| Railway | Backend + frontend deployment |

## Run Locally

**Backend**

```bash
git clone https://github.com/enriquehernandezit-oss/musara.git
cd musara/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URI=http://127.0.0.1:8000/auth/callback
FRONTEND_URL=http://localhost:5173
ANTHROPIC_API_KEY=your_anthropic_key
```

```bash
python main.py
```

**Frontend**

```bash
cd ../frontend
npm install
```

Create a `.env.local` file:

```
VITE_API_URL=http://localhost:8000
```

```bash
npm run dev
```

## Example Moods

- "late-night drive"
- pre-match warmup
- slow Sunday morning coffee
- Focus
- Nostalgic
- Romantic

---

Built by Enrique C. Hernandez — [LinkedIn](your-linkedin-url-here)

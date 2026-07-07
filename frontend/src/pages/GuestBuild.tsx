import { useState } from 'react'
import { Link } from 'react-router-dom'
import { guestGenerate, type PlaylistResult, type GuestPreferences, type Track } from '../api'

const GENRES  = ['', 'Pop', 'Hip-Hop / Rap', 'R&B', 'Rock', 'Indie', 'Electronic', 'Reggaeton', 'Latin', 'Country', 'Jazz', 'Classical']
const DECADES = ['No preference', '2020s', '2010s', '2000s', '90s', '80s', '70s', 'Older']
const LANGUAGES = ['No preference', 'Spanish', 'English', 'Mixed (Spanish + English)', 'Portuguese', 'French']

type Phase = 'idle' | 'generating' | 'done'

// ── Generated cover ──────────────────────────────────────────────────────────
// Guest mode has no reliable per-track Spotify art (not every Claude pick
// resolves via search), so instead of patchy real photos we derive a
// deterministic abstract gradient from the playlist's own name + description
// — same playlist always renders the same cover, different playlists look
// distinct from one another.
function hashString(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

function gradientFor(seed: string): string {
  const h1 = hashString(seed) % 360
  const h2 = (h1 + 45 + (hashString(seed.split('').reverse().join('')) % 140)) % 360
  return `linear-gradient(135deg, hsl(${h1}, 70%, 42%), hsl(${h2}, 65%, 28%))`
}

function GuestNav() {
  return (
    <nav className="nav">
      <div className="nav-inner">
        <Link to="/" style={{ textDecoration: 'none' }}>
          <span className="wordmark">MUS<span>A</span>RA</span>
        </Link>
        <div className="nav-right">
          <Link to="/" className="btn btn-ghost" style={{ height: 34, padding: '0 1rem', fontSize: '0.75rem' }}>
            Connect Spotify
          </Link>
        </div>
      </div>
    </nav>
  )
}

export default function GuestBuild() {
  const [mood, setMood] = useState('')
  const [energy, setEnergy] = useState(5)
  const [activity, setActivity] = useState('')
  const [language, setLanguage] = useState('No preference')
  const [genre, setGenre] = useState('')
  const [decade, setDecade] = useState('No preference')
  const [includeArt, setIncludeArt] = useState('')
  const [excludeArt, setExcludeArt] = useState('')
  const [extra, setExtra] = useState('')
  const [trackCount, setTrackCount] = useState(20)

  const [phase, setPhase] = useState<Phase>('idle')
  const [statusMsg, setStatusMsg] = useState('')
  const [result, setResult] = useState<PlaylistResult | null>(null)
  const [error, setError] = useState('')

  const energyLabel = energy <= 2 ? 'Very calm' : energy <= 4 ? 'Calm' : energy <= 6 ? 'Moderate' : energy <= 8 ? 'High' : 'Peak'

  const handleGenerate = async () => {
    if (!mood.trim()) return
    setPhase('generating'); setError(''); setResult(null)
    const prefs: GuestPreferences = {
      activity, energy: String(energy),
      language: language === 'No preference' ? '' : language,
      genre, decade,
      include_artists: includeArt, exclude_artists: excludeArt, extra,
      track_count: trackCount,
    }
    const steps = ['Interpreting your mood…', 'Selecting tracks from Claude\'s knowledge…', 'Ordering the arc…', 'Naming the playlist…']
    let idx = 0; setStatusMsg(steps[0])
    const ticker = setInterval(() => { idx = Math.min(idx + 1, steps.length - 1); setStatusMsg(steps[idx]) }, 3000)
    try {
      const res = await guestGenerate({ mood, preferences: prefs })
      setResult(res); setPhase('done')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Generation failed'); setPhase('idle')
    } finally { clearInterval(ticker) }
  }

  return (
    <>
      <GuestNav />
      <main style={{ paddingTop: 'calc(var(--nav-h) + 2.5rem)', paddingBottom: '4rem' }}>
        <div className="page">

          {/* 01 Mood */}
          <section>
            <div className="step-label">
              <span className="step-num">01</span>
              <span className="step-title">Describe your mood</span>
            </div>
            <input
              className="input"
              placeholder="late-night drive, pre-match warmup, slow Sunday morning coffee..."
              value={mood}
              onChange={e => setMood(e.target.value)}
            />
            <p style={{ fontFamily: "'DM Mono',monospace", fontSize: '0.6rem', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-3)', marginTop: '0.75rem' }}>
              No Spotify account needed — Claude builds this from its own music knowledge
            </p>
          </section>

          <div className="divider" />

          {/* 02 Filters */}
          <section>
            <div className="step-label">
              <span className="step-num">02</span>
              <span className="step-title">Filters</span>
            </div>
            <div className="prefs-grid">
              <div>
                <label className="field-label">Activity</label>
                <input className="input" placeholder="Driving, working out, studying..." value={activity} onChange={e => setActivity(e.target.value)} />
              </div>
              <div>
                <label className="field-label">Language</label>
                <select className="select" value={language} onChange={e => setLanguage(e.target.value)}>
                  {LANGUAGES.map(l => <option key={l}>{l}</option>)}
                </select>
              </div>
              <div>
                <label className="field-label">Energy intensity</label>
                <div className="slider-wrap">
                  <div className="slider-row">
                    <input type="range" className="slider" min={1} max={10} value={energy} onChange={e => setEnergy(Number(e.target.value))} />
                    <span className="slider-val">{energy}</span>
                  </div>
                  <span style={{ fontFamily: "'DM Mono',monospace", fontSize: '0.58rem', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-3)' }}>{energyLabel}</span>
                </div>
              </div>
              <div>
                <label className="field-label">Genre preference</label>
                <select className="select" value={genre} onChange={e => setGenre(e.target.value)}>
                  {GENRES.map(g => <option key={g} value={g}>{g || 'No preference'}</option>)}
                </select>
              </div>
              <div>
                <label className="field-label">Era / decade</label>
                <select className="select" value={decade} onChange={e => setDecade(e.target.value)}>
                  {DECADES.map(d => <option key={d}>{d}</option>)}
                </select>
              </div>
              <div>
                <label className="field-label">Track count</label>
                <div className="slider-wrap">
                  <div className="slider-row">
                    <input type="range" className="slider" min={5} max={50} value={trackCount} onChange={e => setTrackCount(Number(e.target.value))} />
                    <span className="slider-val">{trackCount}</span>
                  </div>
                </div>
              </div>
              <div>
                <label className="field-label">Featured artists</label>
                <input className="input" placeholder="Bad Bunny, Drake, Frank Ocean" value={includeArt} onChange={e => setIncludeArt(e.target.value)} />
              </div>
              <div>
                <label className="field-label">Excluded artists</label>
                <input className="input" placeholder="Leave blank to include all" value={excludeArt} onChange={e => setExcludeArt(e.target.value)} />
              </div>
              <div>
                <label className="field-label">Additional notes</label>
                <input className="input" placeholder="No explicit, instrumentals only..." value={extra} onChange={e => setExtra(e.target.value)} />
              </div>
            </div>
          </section>

          <div className="divider" />

          {/* 03 Generate */}
          <section>
            <div className="step-label">
              <span className="step-num">03</span>
              <span className="step-title">Generate</span>
            </div>
            {error && <p style={{ color: '#ff4444', fontFamily: "'DM Mono',monospace", fontSize: '0.75rem', marginBottom: '1rem' }}>{error}</p>}
            {phase === 'generating' ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxWidth: 360 }}>
                <div className="status-pill">
                  <div className="spinner" style={{ width: 12, height: 12, borderWidth: 1.5 }} />
                  {statusMsg}
                </div>
                <div className="loading-bar"><div className="loading-bar-fill" /></div>
              </div>
            ) : (
              <button className="btn btn-primary btn-lg" onClick={handleGenerate} disabled={!mood.trim()}>
                Generate Playlist
              </button>
            )}
            {!mood.trim() && phase === 'idle' && (
              <p style={{ fontFamily: "'DM Mono',monospace", fontSize: '0.6rem', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-3)', marginTop: '0.75rem' }}>
                Describe a mood to continue
              </p>
            )}
          </section>

          {/* Results */}
          {phase === 'done' && result && (
            <>
              <div className="divider" />
              <GuestResults result={result} activeMood={mood} />
            </>
          )}

        </div>
      </main>
    </>
  )
}

function GuestResults({ result, activeMood }: { result: PlaylistResult; activeMood: string }) {
  const tracks = result.tracks
  const uniqueArtists = new Set(tracks.map(t => t.artist)).size
  const cover = gradientFor(result.playlist_name + result.playlist_description)

  return (
    <section>
      <div className="pl-header" style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
        <div style={{
          width: 120, height: 120, borderRadius: 'var(--radius)', flexShrink: 0,
          background: cover, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: '3rem', color: 'rgba(255,255,255,0.35)' }}>
            {result.playlist_name.charAt(0).toUpperCase()}
          </span>
        </div>
        <div>
        <div className="pl-eyebrow">{activeMood}</div>
        <div className="pl-title">{result.playlist_name.toUpperCase()}</div>
        <p className="pl-desc">{result.playlist_description}</p>
        {result.mood_summary && <p className="pl-desc" style={{ marginTop: '0.5rem' }}>{result.mood_summary}</p>}

        <div className="pl-stats">
          <div>
            <div className="pl-stat-val">{tracks.length}</div>
            <div className="pl-stat-key">Tracks</div>
          </div>
          <div>
            <div className="pl-stat-val">{uniqueArtists}</div>
            <div className="pl-stat-key">Artists</div>
          </div>
        </div>
        </div>
      </div>

      <div className="results-grid">
        <div className="track-list">
          <div className="track-header">
            <span className="track-header-label">#</span>
            <span className="track-header-label">Title</span>
            <span className="track-header-label">Genre</span>
          </div>
          {tracks.map((track, i) => <GuestTrackRow key={track.id} track={track} index={i} cover={cover} />)}
        </div>

        <div>
          <div className="export-card">
            <div className="export-count-wrap">
              <div className="export-count">{tracks.length}</div>
              <div className="export-count-label">Tracks selected</div>
            </div>
            <p className="export-note">
              This playlist is built from Claude's own music knowledge — no Spotify library involved.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

function GuestTrackRow({ track, index, cover }: { track: Track; index: number; cover: string }) {
  const genre = track.genres[0] ?? null
  return (
    <div className="track-row">
      <div className="track-num-wrap">
        <span className="track-num">{String(index + 1).padStart(2, '0')}</span>
      </div>

      <div className="track-info">
        <div className="track-thumb-placeholder" style={{ background: cover }} />
        <div className="track-text">
          <div className="track-name">{track.name}</div>
          <div className="track-artist">{track.artist}</div>
        </div>
      </div>

      <div className="track-tags">
        {genre && <span className="tag">{genre}</span>}
      </div>
    </div>
  )
}

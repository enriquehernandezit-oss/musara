import { useEffect, useState } from 'react'
import { getLoginUrl } from '../api'

export default function Landing() {
  const [authUrl, setAuthUrl] = useState<string | null>(null)

  useEffect(() => {
    getLoginUrl().then(setAuthUrl).catch(console.error)
  }, [])

  return (
    <div className="landing-wrap">
      {/* ── Left: Hero ──────────────────────────────────────────── */}
      <div className="landing-left">
        <p className="landing-sub">Mood-based playlist intelligence</p>
        <h1 className="landing-hero">
          MUS<span>A</span>RA
        </h1>

        <p className="landing-desc">
          Musara analyzes your Spotify library and curates playlists around
          your emotional state — using audio signal data, not genre tags.
          Energy. Valence. Tempo. Danceability. Real numbers, real results.
        </p>

        {authUrl ? (
          <a href={authUrl} className="btn btn-primary btn-lg">
            <SpotifyIcon />
            Connect with Spotify
          </a>
        ) : (
          <button className="btn btn-primary btn-lg" disabled>
            <div className="spinner" />
            Loading...
          </button>
        )}

        <p className="landing-disclaimer">Requires a Spotify account</p>
      </div>

      {/* ── Right: How it works ─────────────────────────────────── */}
      <div className="landing-right">
        <p className="how-title">How it works</p>
        {[
          'Connect your Spotify account via OAuth',
          'Select a mood or describe your current state',
          'AI scores up to 400 tracks against audio feature targets',
          'Export the curated playlist directly to your Spotify library',
        ].map((text, i) => (
          <div className="how-item" key={i}>
            <div className="how-num">{String(i + 1).padStart(2, '0')}</div>
            <div className="how-text">{text}</div>
          </div>
        ))}

        <div style={{ marginTop: '3rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {['Energy scoring', 'Valence mapping', 'Tempo matching', 'Genre filtering'].map(f => (
            <div key={f} style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
              <div className="dot-green" />
              <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '0.65rem', letterSpacing: '0.06em', color: 'var(--text-3)', textTransform: 'uppercase' }}>{f}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function SpotifyIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
    </svg>
  )
}

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthCtx } from '../App'
import {
  getPlaylists, generate, exportPlaylist,
  type Playlist, type Track, type PlaylistResult, type Preferences,
} from '../api'

const MOODS = [
  { key: 'Hype',      label: 'Energized',  sub: 'High drive',     emoji: '⚡' },
  { key: 'Chill',     label: 'Unwinding',  sub: 'Low tempo',      emoji: '🌊' },
  { key: 'Focus',     label: 'Focused',    sub: 'Deep work',      emoji: '🎯' },
  { key: 'Sad',       label: 'Reflective', sub: 'Introspective',  emoji: '🌧' },
  { key: 'Nostalgic', label: 'Nostalgic',  sub: 'Memory-driven',  emoji: '📼' },
  { key: 'Romantic',  label: 'Romantic',   sub: 'Soft, intimate', emoji: '🕯' },
]
const ACTIVITIES = ['','Driving','Working out / Gym','Studying / Focus','Party / Going out','Cooking','Relaxing at home','Running','Working','Getting ready']
const LANGUAGES  = ['No preference','Spanish','English','Mixed (Spanish + English)','Portuguese','French']

type Phase = 'idle' | 'generating' | 'done'
function avg(arr: (number|undefined)[]): string {
  const v = arr.filter((x): x is number => x != null)
  return v.length ? (v.reduce((a,b)=>a+b,0)/v.length).toFixed(2) : '—'
}
function avgInt(arr: (number|undefined)[]): string {
  const v = arr.filter((x): x is number => x != null)
  return v.length ? String(Math.round(v.reduce((a,b)=>a+b,0)/v.length)) : '—'
}

function Nav({ onLogout }: { onLogout: () => void }) {
  const { user } = useAuthCtx()
  const initials = user?.display_name?.slice(0,2).toUpperCase() ?? '??'
  return (
    <nav className="nav">
      <div className="nav-inner">
        <span className="wordmark">MUS<span>A</span>RA</span>
        <div className="nav-right">
          <div className="user-chip">
            <div className="user-avatar">{initials}</div>
            {user?.display_name}
          </div>
          <button className="btn btn-ghost" style={{height:34,padding:'0 1rem',fontSize:'0.75rem'}} onClick={onLogout}>
            Sign out
          </button>
        </div>
      </div>
    </nav>
  )
}

export default function Build() {
  const { logout }   = useAuthCtx()
  const navigate     = useNavigate()

  const [playlists,    setPlaylists]    = useState<Playlist[]>([])
  const [playlistsErr, setPlaylistsErr] = useState('')
  const [loadingPl,    setLoadingPl]    = useState(true)
  const [selectedMood, setSelectedMood] = useState<string|null>(null)
  const [customMood,   setCustomMood]   = useState('')
  const [energy,       setEnergy]       = useState(5)
  const [activity,     setActivity]     = useState('')
  const [language,     setLanguage]     = useState('No preference')
  const [includeArt,   setIncludeArt]   = useState('')
  const [excludeArt,   setExcludeArt]   = useState('')
  const [extra,        setExtra]        = useState('')
  const [selectedPls,  setSelectedPls]  = useState<string[]>([])
  const [phase,        setPhase]        = useState<Phase>('idle')
  const [statusMsg,    setStatusMsg]    = useState('')
  const [result,       setResult]       = useState<PlaylistResult|null>(null)
  const [error,        setError]        = useState('')
  const [exporting,    setExporting]    = useState(false)
  const [exportUrl,    setExportUrl]    = useState<string|null>(null)
  const [toast,        setToast]        = useState('')

  const activeMood = customMood.trim() || selectedMood

  useEffect(() => {
    getPlaylists()
      .then(setPlaylists)
      .catch((e: Error) => setPlaylistsErr(e.message))
      .finally(() => setLoadingPl(false))
  }, [])

  const togglePlaylist = useCallback((id: string) => {
    setSelectedPls(prev => prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id])
  }, [])

  const handleLogout = () => { logout(); navigate('/', { replace: true }) }

  const handleGenerate = async () => {
    if (!activeMood || !selectedPls.length) return
    setPhase('generating'); setError(''); setResult(null); setExportUrl(null)
    const prefs: Preferences = {
      activity, energy: String(energy),
      language: language === 'No preference' ? '' : language,
      include_artists: includeArt, exclude_artists: excludeArt, extra,
    }
    const steps = ['Pulling tracks…','Analyzing audio features…','Fetching genre data…','Curating your playlist…']
    let idx = 0; setStatusMsg(steps[0])
    const ticker = setInterval(() => { idx = Math.min(idx+1,steps.length-1); setStatusMsg(steps[idx]) }, 3500)
    try {
      const res = await generate({ mood: activeMood, playlist_ids: selectedPls, preferences: prefs })
      setResult(res); setPhase('done')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Generation failed'); setPhase('idle')
    } finally { clearInterval(ticker) }
  }

  const handleExport = async () => {
    if (!result) return
    setExporting(true)
    try {
      const exp = await exportPlaylist(result.playlist_name, `Created by Musara · Mood: ${activeMood}`, result.tracks.map(t=>t.uri))
      setExportUrl(exp.url); setToast('Playlist saved to Spotify')
      setTimeout(() => setToast(''), 4000)
    } catch (e: unknown) {
      setToast(e instanceof Error ? e.message : 'Export failed')
      setTimeout(() => setToast(''), 4000)
    } finally { setExporting(false) }
  }

  const energyLabel = energy<=2?'Very calm':energy<=4?'Calm':energy<=6?'Moderate':energy<=8?'High':'Peak'

  return (
    <>
      <Nav onLogout={handleLogout} />
      <main style={{paddingTop:'calc(var(--nav-h) + 2.5rem)',paddingBottom:'4rem'}}>
        <div className="page">

          {/* 01 Mood */}
          <section>
            <div className="step-label">
              <span className="step-num">01</span>
              <span className="step-title">Select mood</span>
            </div>
            <div className="mood-grid">
              {MOODS.map(m => (
                <button
                  key={m.key}
                  className={`mood-card${selectedMood===m.key?' active':''}`}
                  onClick={() => setSelectedMood(prev => prev===m.key ? null : m.key)}
                >
                  <div className="mood-emoji">{m.emoji}</div>
                  <div className="mood-name">{m.label}</div>
                  <div className="mood-sub">{m.sub}</div>
                </button>
              ))}
            </div>
            <div style={{marginTop:'1rem'}}>
              <input
                className="input"
                placeholder="Or describe your state — late-night drive, pre-match warmup..."
                value={customMood}
                onChange={e => { setCustomMood(e.target.value); if (e.target.value) setSelectedMood(null) }}
              />
            </div>
          </section>

          <div className="divider" />

          {/* 02 Preferences */}
          <section>
            <div className="step-label">
              <span className="step-num">02</span>
              <span className="step-title">Preferences</span>
            </div>
            <div className="prefs-grid">
              <div>
                <label className="field-label">Activity</label>
                <select className="select" value={activity} onChange={e=>setActivity(e.target.value)}>
                  {ACTIVITIES.map(a=><option key={a} value={a}>{a||'Not specified'}</option>)}
                </select>
              </div>
              <div>
                <label className="field-label">Language</label>
                <select className="select" value={language} onChange={e=>setLanguage(e.target.value)}>
                  {LANGUAGES.map(l=><option key={l}>{l}</option>)}
                </select>
              </div>
              <div>
                <label className="field-label">Energy intensity</label>
                <div className="slider-wrap">
                  <div className="slider-row">
                    <input type="range" className="slider" min={1} max={10} value={energy} onChange={e=>setEnergy(Number(e.target.value))} />
                    <span className="slider-val">{energy}</span>
                  </div>
                  <span style={{fontFamily:"'DM Mono',monospace",fontSize:'0.58rem',letterSpacing:'0.08em',textTransform:'uppercase',color:'var(--text-3)'}}>{energyLabel}</span>
                </div>
              </div>
              <div>
                <label className="field-label">Additional filters</label>
                <input className="input" placeholder="No explicit, instrumentals only..." value={extra} onChange={e=>setExtra(e.target.value)} />
              </div>
              <div>
                <label className="field-label">Featured artists</label>
                <input className="input" placeholder="Bad Bunny, Drake, Frank Ocean" value={includeArt} onChange={e=>setIncludeArt(e.target.value)} />
              </div>
              <div>
                <label className="field-label">Excluded artists</label>
                <input className="input" placeholder="Leave blank to include all" value={excludeArt} onChange={e=>setExcludeArt(e.target.value)} />
              </div>
            </div>
          </section>

          <div className="divider" />

          {/* 03 Playlists */}
          <section>
            <div className="step-label">
              <span className="step-num">03</span>
              <span className="step-title">Source playlists</span>
              {selectedPls.length > 0 && (
                <span style={{fontFamily:"'DM Mono',monospace",fontSize:'0.6rem',color:'var(--green)',marginLeft:'0.5rem'}}>
                  {selectedPls.length} selected
                </span>
              )}
            </div>
            {loadingPl ? (
              <div className="flex items-center gap-2" style={{color:'var(--text-3)',fontFamily:"'DM Mono',monospace",fontSize:'0.75rem'}}>
                <div className="spinner" />Loading playlists…
              </div>
            ) : playlistsErr ? (
              <p style={{color:'#ff4444',fontSize:'0.8125rem'}}>{playlistsErr}</p>
            ) : (
              <div className="playlist-grid">
                {playlists.map(pl => (
                  <button key={pl.id} className={`playlist-card${selectedPls.includes(pl.id)?' selected':''}`} onClick={()=>togglePlaylist(pl.id)}>
                    {pl.image
                      ? <img src={pl.image} alt={pl.name} className="playlist-art" />
                      : <div className="playlist-art-placeholder">♪</div>}
                    <span className="playlist-name">{pl.name}</span>
                    <div className="check-ring">
                      <svg width="8" height="6" viewBox="0 0 8 6" fill="none">
                        <path d="M1 3l2 2 4-4" stroke="#000" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </section>

          <div className="divider" />

          {/* 04 Generate */}
          <section>
            <div className="step-label">
              <span className="step-num">04</span>
              <span className="step-title">Generate</span>
            </div>
            {error && <p style={{color:'#ff4444',fontFamily:"'DM Mono',monospace",fontSize:'0.75rem',marginBottom:'1rem'}}>{error}</p>}
            {phase==='generating' ? (
              <div style={{display:'flex',flexDirection:'column',gap:'0.75rem',maxWidth:360}}>
                <div className="status-pill">
                  <div className="spinner" style={{width:12,height:12,borderWidth:1.5}} />
                  {statusMsg}
                </div>
                <div className="loading-bar"><div className="loading-bar-fill" /></div>
              </div>
            ) : (
              <button className="btn btn-primary btn-lg" onClick={handleGenerate} disabled={!activeMood||selectedPls.length===0}>
                Generate Playlist
              </button>
            )}
            {!activeMood && phase==='idle' && (
              <p style={{fontFamily:"'DM Mono',monospace",fontSize:'0.6rem',letterSpacing:'0.08em',textTransform:'uppercase',color:'var(--text-3)',marginTop:'0.75rem'}}>
                Select or describe a mood to continue
              </p>
            )}
          </section>

          {/* Results */}
          {phase==='done' && result && (
            <>
              <div className="divider" />
              <Results result={result} activeMood={activeMood??''} exporting={exporting} exportUrl={exportUrl} onExport={handleExport} />
            </>
          )}

        </div>
      </main>

      {toast && (
        <div className="toast">
          <div className="dot-green" />
          {toast}
          {exportUrl && (
            <a href={exportUrl} target="_blank" rel="noreferrer" className="btn btn-primary" style={{height:28,padding:'0 0.875rem',fontSize:'0.7rem',marginLeft:'0.5rem'}}>
              Open ↗
            </a>
          )}
        </div>
      )}
    </>
  )
}

function Results({ result, activeMood, exporting, exportUrl, onExport }: {
  result: PlaylistResult; activeMood: string; exporting: boolean; exportUrl: string|null; onExport: ()=>void
}) {
  const tracks = result.tracks
  const avgE   = avg(tracks.map(t=>t.energy))
  const avgV   = avg(tracks.map(t=>t.valence))
  const avgBpm = avgInt(tracks.map(t=>t.tempo))

  return (
    <section>
      <div className="pl-header">
        <div className="pl-eyebrow">{activeMood}</div>
        <div className="pl-title">{result.playlist_name.toUpperCase()}</div>
        <p className="pl-desc">{result.playlist_description}</p>
        {result.mood_summary && <p className="pl-desc" style={{marginTop:'0.5rem'}}>{result.mood_summary}</p>}
        <div className="pl-stats">
          {[['Tracks',String(tracks.length)],['Avg Energy',avgE],['Avg Valence',avgV],['Avg BPM',avgBpm]].map(([k,v])=>(
            <div key={k}><div className="pl-stat-val">{v}</div><div className="pl-stat-key">{k}</div></div>
          ))}
        </div>
      </div>

      <div className="results-grid">
        <div className="track-list">
          <div className="track-header">
            <span className="track-header-label">#</span>
            <span className="track-header-label">Title</span>
            <span className="track-header-label">Signals</span>
          </div>
          {tracks.map((track,i) => <TrackRow key={track.id} track={track} index={i} />)}
        </div>

        <div>
          <div className="export-card">
            <div className="export-count-wrap">
              <div className="export-count">{tracks.length}</div>
              <div className="export-count-label">Tracks selected</div>
            </div>
            <div className="export-stats">
              {[['Avg Energy',avgE],['Avg Valence',avgV],['Avg BPM',avgBpm]].map(([k,v])=>(
                <div className="export-stat-row" key={k}>
                  <span className="export-stat-key">{k}</span>
                  <span className="export-stat-val">{v}</span>
                </div>
              ))}
            </div>
            {exportUrl ? (
              <a href={exportUrl} target="_blank" rel="noreferrer" className="btn btn-primary w-full" style={{justifyContent:'center'}}>
                Open in Spotify ↗
              </a>
            ) : (
              <button className="btn btn-primary w-full" style={{justifyContent:'center'}} onClick={onExport} disabled={exporting}>
                {exporting ? <><div className="spinner" style={{width:14,height:14,borderWidth:1.5}} /> Saving…</> : 'Save to Spotify'}
              </button>
            )}
            <p className="export-note">E = Energy · V = Valence<br/>Data via Spotify Audio Features API</p>
          </div>
        </div>
      </div>
    </section>
  )
}

function TrackRow({ track, index }: { track: Track; index: number }) {
  const has = track.energy != null
  return (
    <div className="track-row">
      <div className="track-num-wrap">
        <span className="track-num">{String(index+1).padStart(2,'0')}</span>
        <span className="track-play">▶</span>
      </div>
      <div className="track-info">
        {track.image
          ? <img src={track.image} alt={track.album} className="track-thumb" />
          : <div className="track-thumb-placeholder" />}
        <div className="track-text">
          <div className="track-name">{track.name}</div>
          <div className="track-artist">{track.artist} — {track.album}</div>
        </div>
      </div>
      {has && (
        <div className="track-tags">
          <span className={`tag${(track.energy??0)>0.7?' tag-green':''}`}>{track.energy!.toFixed(2)} E</span>
          <span className={`tag${(track.valence??0)>0.6?' tag-green':''}`}>{track.valence!.toFixed(2)} V</span>
          <span className="tag">{Math.round(track.tempo??0)} BPM</span>
        </div>
      )}
    </div>
  )
}

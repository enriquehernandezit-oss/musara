import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthCtx } from '../App'

export default function Callback() {
  const { login } = useAuthCtx()
  const navigate   = useNavigate()
  const ran        = useRef(false)

  useEffect(() => {
    if (ran.current) return
    ran.current = true

    const params       = new URLSearchParams(window.location.search)
    const accessToken  = params.get('access_token')
    const refreshToken = params.get('refresh_token')
    const expiresAt    = Number(params.get('expires_at') ?? 0)

    if (!accessToken || !refreshToken) {
      navigate('/', { replace: true })
      return
    }

    login(accessToken, refreshToken, expiresAt).then(() => {
      navigate('/build', { replace: true })
    })
  }, [login, navigate])

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg)',
      flexDirection: 'column',
      gap: '1.5rem',
    }}>
      <div style={{
        fontFamily: "'Bebas Neue', sans-serif",
        fontSize: '2.5rem',
        letterSpacing: '0.08em',
        color: 'var(--text)',
      }}>
        MUSARA
      </div>
      <div className="spinner" />
      <p style={{
        fontFamily: "'DM Mono', monospace",
        fontSize: '0.6rem',
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        color: 'var(--text-3)',
      }}>
        Connecting to Spotify...
      </p>
    </div>
  )
}

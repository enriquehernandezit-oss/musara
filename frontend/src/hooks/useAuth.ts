import { useState, useEffect, useCallback } from 'react'
import { refreshAccessToken, getMe, type UserProfile } from '../api'

const KEYS = {
  accessToken:  'musara_access_token',
  refreshToken: 'musara_refresh_token',
  expiresAt:    'musara_expires_at',
}

function read(key: string) { return localStorage.getItem(key) }
function write(key: string, val: string) { localStorage.setItem(key, val) }
function clear() { Object.values(KEYS).forEach(k => localStorage.removeItem(k)) }

export function useAuth() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [ready, setReady] = useState(false)   // finished initial check
  const [loading, setLoading] = useState(true)

  const isExpired = () => {
    const exp = Number(read(KEYS.expiresAt) ?? 0)
    return Date.now() / 1000 > exp - 60
  }

  // Ensure we have a fresh access token, refreshing if needed
  const ensureFreshToken = useCallback(async (): Promise<boolean> => {
    const rt = read(KEYS.refreshToken)
    if (!rt) return false
    if (!isExpired()) return true
    try {
      const { access_token, expires_at } = await refreshAccessToken(rt)
      write(KEYS.accessToken, access_token)
      write(KEYS.expiresAt, String(expires_at))
      return true
    } catch {
      clear()
      return false
    }
  }, [])

  // Called by Callback page after OAuth completes
  const login = useCallback(
    async (accessToken: string, refreshToken: string, expiresAt: number) => {
      write(KEYS.accessToken, accessToken)
      write(KEYS.refreshToken, refreshToken)
      write(KEYS.expiresAt, String(expiresAt))
      try {
        const me = await getMe()
        setUser(me)
      } catch { /* token invalid */ }
    },
    [],
  )

  const logout = useCallback(() => {
    clear()
    setUser(null)
  }, [])

  // On mount: check stored tokens.
  // Skip entirely on /callback — that page is the authoritative source of
  // truth right after an OAuth login and calls login() itself. Without this
  // guard, this effect's own /me call (using whatever old token was already
  // in localStorage) races Callback's /me call (using the fresh token), and
  // whichever resolves last wins — sometimes leaving the previous account's
  // profile active even though a new account just logged in.
  useEffect(() => {
    if (window.location.pathname.startsWith('/callback')) {
      setReady(true)
      setLoading(false)
      return
    }
    ;(async () => {
      const ok = await ensureFreshToken()
      if (ok) {
        try {
          const me = await getMe()
          setUser(me)
        } catch {
          clear()
        }
      }
      setLoading(false)
      setReady(true)
    })()
  }, [ensureFreshToken])

  return {
    user,
    ready,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    ensureFreshToken,
  }
}

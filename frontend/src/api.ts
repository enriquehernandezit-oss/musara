// In production (Railway) set VITE_API_URL to your backend Railway URL.
// In local dev the Vite proxy rewrites /api → http://localhost:8000, so no env var needed.
const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api'

// ── Types (mirror backend models) ─────────────────────────────────────────────

export interface UserProfile {
  id: string
  display_name: string
  email?: string
  image_url?: string
}

export interface Playlist {
  id: string
  name: string
  image?: string
  owner: string
}

export interface Track {
  id: string
  name: string
  artist: string
  artist_id?: string
  album: string
  image?: string
  uri: string
  preview_url?: string
  popularity: number
  explicit: boolean
  energy?: number
  valence?: number
  danceability?: number
  tempo?: number
  acousticness?: number
  instrumentalness?: number
  loudness?: number
  speechiness?: number
  genres: string[]
}

export interface Preferences {
  activity?: string
  energy?: string
  language?: string
  include_artists?: string
  exclude_artists?: string
  extra?: string
}

export interface GenerateRequest {
  mood: string
  playlist_ids: string[]
  preferences: Preferences
}

export interface PlaylistResult {
  playlist_name: string
  playlist_description: string
  mood_summary: string
  tracks: Track[]
}

export interface ExportResult {
  id: string
  url: string
  name: string
}

// ── Client ────────────────────────────────────────────────────────────────────

function getToken(): string | null {
  return localStorage.getItem('musara_access_token')
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function getLoginUrl(): Promise<string> {
  const data = await request<{ url: string }>('/auth/login-url')
  return data.url
}

export async function refreshAccessToken(refreshToken: string): Promise<{ access_token: string; expires_at: number }> {
  return request('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
}

// ── Spotify ───────────────────────────────────────────────────────────────────

export async function getMe(): Promise<UserProfile> {
  return request<UserProfile>('/me')
}

export async function getPlaylists(): Promise<Playlist[]> {
  return request<Playlist[]>('/playlists')
}

export async function generate(body: GenerateRequest): Promise<PlaylistResult> {
  return request<PlaylistResult>('/generate', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function exportPlaylist(
  name: string,
  description: string,
  track_uris: string[],
): Promise<ExportResult> {
  return request<ExportResult>('/export', {
    method: 'POST',
    body: JSON.stringify({ name, description, track_uris }),
  })
}

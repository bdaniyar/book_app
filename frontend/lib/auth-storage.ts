export type AuthSession = {
    accessToken: string
    refreshToken?: string
}

// In-memory access token (preferred). This resets on full page reload.
let memoryAccessToken: string | null = null

const ACCESS_KEY = 'book_app.access_token'
// Refresh is now stored in HttpOnly cookie (server-set). Keeping key only for backward compatibility.
const REFRESH_KEY = 'book_app.refresh_token'

export function getSession(): AuthSession | null {
    // Backward-compatible read from localStorage (only if present)
    if (typeof window === 'undefined') return null
    const accessToken = memoryAccessToken ?? window.localStorage.getItem(ACCESS_KEY)
    const refreshToken = window.localStorage.getItem(REFRESH_KEY) ?? undefined
    if (!accessToken) return null
    return { accessToken, refreshToken }
}

export function setSession(session: AuthSession) {
    // Prefer memory access token; optionally mirror to localStorage if needed
    memoryAccessToken = session.accessToken
    if (typeof window === 'undefined') return
    // Keep access token in localStorage only if it was previously used; comment out to be strict.
    window.localStorage.setItem(ACCESS_KEY, session.accessToken)
    if (session.refreshToken) window.localStorage.setItem(REFRESH_KEY, session.refreshToken)
}

export function clearSession() {
    memoryAccessToken = null
    if (typeof window === 'undefined') return
    window.localStorage.removeItem(ACCESS_KEY)
    window.localStorage.removeItem(REFRESH_KEY)
}

export function getAccessToken(): string | null {
    return memoryAccessToken
}

export function setAccessToken(token: string | null) {
    memoryAccessToken = token
}

export function clearAccessToken() {
    memoryAccessToken = null
}

export type AuthSession = {
    accessToken: string
    refreshToken: string
}

const ACCESS_KEY = 'book_app.access_token'
const REFRESH_KEY = 'book_app.refresh_token'

export function getSession(): AuthSession | null {
    if (typeof window === 'undefined') return null
    const accessToken = window.localStorage.getItem(ACCESS_KEY)
    const refreshToken = window.localStorage.getItem(REFRESH_KEY)
    if (!accessToken || !refreshToken) return null
    return { accessToken, refreshToken }
}

export function setSession(session: AuthSession) {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(ACCESS_KEY, session.accessToken)
    window.localStorage.setItem(REFRESH_KEY, session.refreshToken)
}

export function clearSession() {
    if (typeof window === 'undefined') return
    window.localStorage.removeItem(ACCESS_KEY)
    window.localStorage.removeItem(REFRESH_KEY)
}

export function getAccessToken(): string | null {
    return getSession()?.accessToken ?? null
}

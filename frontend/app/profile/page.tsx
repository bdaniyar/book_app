'use client'

import { useEffect, useMemo, useState } from 'react'

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Award, BookOpen, Calendar, Settings, Star } from 'lucide-react'

import { BookCard } from '@/components/book-card'
import { authService } from '@/lib/api-services'
import { clearSession, getSession, setSession } from '@/lib/auth-storage'
import { trendingBooks } from '@/lib/books-data'

type Mode = 'login' | 'register'

type MeUser = {
  id: string
  email: string
  name?: string | null
}

function getInitials(nameOrEmail: string) {
  const s = (nameOrEmail || '').trim()
  if (!s) return 'U'
  const parts = s.split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return s.slice(0, 2).toUpperCase()
}

export default function ProfilePage() {
  const [mode, setMode] = useState<Mode>('register')

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [session, setSessionState] = useState<ReturnType<typeof getSession>>(null)
  const [me, setMe] = useState<MeUser | null>(null)
  const [meLoading, setMeLoading] = useState(false)

  useEffect(() => {
    // Client-only: read localStorage after hydration
    setSessionState(getSession())
  }, [])

  useEffect(() => {
    // If we have a token, try to load current user
    const run = async () => {
      if (!session) return
      setMeLoading(true)
      try {
        const res = await authService.me()
        if (res.success) {
          setMe(res.data as any)
        } else {
          setMe(null)
        }
      } finally {
        setMeLoading(false)
      }
    }
    run()
  }, [session])

  const displayName = useMemo(() => {
    if (me?.name && me.name.trim()) return me.name.trim()
    if (me?.email) return me.email
    return 'User'
  }, [me])

  const initials = useMemo(() => getInitials(displayName), [displayName])

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      if (mode === 'register') {
        // 1) Register user
        const regRes = await authService.register(email, password, name)

        // If backend already returns tokens - use them.
        if (regRes.success && regRes.data && (regRes.data as any).access_token) {
          const { access_token, refresh_token } = regRes.data as any
          setSession({ accessToken: access_token, refreshToken: refresh_token })
          setSessionState(getSession())
        } else {
          // 2) Otherwise auto-login right after register
          if (!regRes.success) {
            setError(regRes.error || 'Registration failed')
            return
          }
          const loginRes = await authService.login(email, password)
          if (!loginRes.success || !loginRes.data) {
            setError(loginRes.error || 'Auto-login failed after registration')
            return
          }
          const { access_token, refresh_token } = loginRes.data as any
          setSession({ accessToken: access_token, refreshToken: refresh_token })
          setSessionState(getSession())
        }
      } else {
        // Login
        const res = await authService.login(email, password)
        if (!res.success || !res.data) {
          setError(res.error || 'Login failed')
          return
        }
        const { access_token, refresh_token } = res.data as any
        if (!access_token || !refresh_token) {
          setError('Login response does not contain tokens')
          return
        }
        setSession({ accessToken: access_token, refreshToken: refresh_token })
        setSessionState(getSession())
      }

      // Immediately load /auth/me and show profile
      setMeLoading(true)
      const meRes = await authService.me()
      if (meRes.success && meRes.data) {
        setMe(meRes.data as any)
      } else {
        setMe(null)
        setError(meRes.error || 'Failed to load profile')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Auth failed')
    } finally {
      setLoading(false)
      setMeLoading(false)
    }
  }

  const onLogout = () => {
    clearSession()
    setSessionState(null)
    setMe(null)
    setEmail('')
    setPassword('')
    setName('')
    setMode('login')
  }

  // Logged in view (beautiful/original-ish UI)
  if (session) {
    const user = {
      name: me?.name?.trim() || displayName,
      username: me?.email ? `@${me.email.split('@')[0]}` : '@user',
      avatar: '/placeholder-user.jpg',
      bio: me?.email
        ? `Reader profile for ${me.email}. (Bio placeholder — wire this to backend later.)`
        : 'Avid reader and book enthusiast. Always looking for the next great story to dive into.',
      joinDate: 'January 2026',
      stats: {
        booksRead: 24,
        reviews: 15,
        followers: 38,
        following: 42,
      },
    }

    const recentlyRead = [trendingBooks[0], trendingBooks[1], trendingBooks[2]].filter(Boolean)
    const favoriteGenres = ['Fiction', 'Mystery', 'Science Fiction', 'Biography']

    return (
      <div className="w-full">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-7xl space-y-8">
          {/* Profile Header */}
          <Card className="border-border/50">
            <CardContent className="p-8">
              <div className="flex flex-col md:flex-row gap-8 items-start">
                <Avatar className="h-32 w-32 border-4 border-primary/10">
                  <AvatarImage src={user.avatar || '/placeholder.svg'} alt={user.name} />
                  <AvatarFallback className="text-3xl">{initials}</AvatarFallback>
                </Avatar>

                <div className="flex-1 space-y-4">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-3">
                      <h1 className="font-sans text-3xl font-bold">{user.name}</h1>
                      <Badge variant="secondary" className="rounded-full">
                        <Award className="h-3 w-3 mr-1" />
                        Top Reader
                      </Badge>
                      {meLoading ? (
                        <Badge variant="outline" className="rounded-full">
                          Loading…
                        </Badge>
                      ) : null}
                    </div>
                    <p className="text-muted-foreground">{user.username}</p>
                  </div>

                  <p className="text-muted-foreground leading-relaxed max-w-2xl">{user.bio}</p>

                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>Joined {user.joinDate}</span>
                  </div>

                  {error ? (
                    <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3">
                      <p className="text-sm text-destructive">{error}</p>
                    </div>
                  ) : null}

                  <div className="flex flex-wrap gap-4 pt-2">
                    <div className="text-center">
                      <div className="font-bold text-2xl">{user.stats.booksRead}</div>
                      <div className="text-sm text-muted-foreground">Books Read</div>
                    </div>
                    <Separator orientation="vertical" className="h-12" />
                    <div className="text-center">
                      <div className="font-bold text-2xl">{user.stats.reviews}</div>
                      <div className="text-sm text-muted-foreground">Reviews</div>
                    </div>
                    <Separator orientation="vertical" className="h-12" />
                    <div className="text-center">
                      <div className="font-bold text-2xl">{user.stats.followers}</div>
                      <div className="text-sm text-muted-foreground">Followers</div>
                    </div>
                    <Separator orientation="vertical" className="h-12" />
                    <div className="text-center">
                      <div className="font-bold text-2xl">{user.stats.following}</div>
                      <div className="text-sm text-muted-foreground">Following</div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-3 pt-2">
                    <Button className="rounded-xl" disabled>
                      <Settings className="h-4 w-4 mr-2" />
                      Edit Profile
                    </Button>
                    <Button variant="outline" className="rounded-xl bg-transparent" onClick={onLogout}>
                      Logout
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Reading Stats */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="border-border/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-primary" />
                  Reading Activity
                </CardTitle>
                <CardDescription>Your reading journey this year</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">2026 Reading Goal</span>
                    <span className="font-semibold">24 books</span>
                  </div>
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: '80%' }} />
                  </div>
                </div>

                <Separator />

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Pages Read</span>
                    <span className="font-semibold">7,842</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Avg. Rating</span>
                    <div className="flex items-center gap-1">
                      <Star className="h-4 w-4 fill-accent text-accent" />
                      <span className="font-semibold">4.3</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Reading Streak</span>
                    <span className="font-semibold">7 days</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/50">
              <CardHeader>
                <CardTitle>Favorite Genres</CardTitle>
                <CardDescription>Your most-read categories</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {favoriteGenres.map((genre) => (
                    <Badge key={genre} variant="secondary" className="px-4 py-2 text-sm rounded-full">
                      {genre}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recently Read */}
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="font-sans text-2xl font-semibold">Recently Read</h2>
              <Button variant="ghost" disabled>
                View All
              </Button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-6">
              {recentlyRead.map((book) => (
                <BookCard key={(book as any).id} book={book as any} />
              ))}
            </div>
          </section>
        </div>
      </div>
    )
  }

  // Auth form view
  return (
    <div className="w-full">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-10 max-w-xl">
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle>{mode === 'register' ? 'Create account' : 'Welcome back'}</CardTitle>
            <CardDescription>
              Test auth flow. Backend endpoints: <code>/api/v1/auth/register</code>, <code>/api/v1/auth/login</code>,{' '}
              <code>/api/v1/auth/me</code>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 mb-4">
              <Button
                type="button"
                variant={mode === 'register' ? 'default' : 'outline'}
                onClick={() => setMode('register')}
              >
                Register
              </Button>
              <Button type="button" variant={mode === 'login' ? 'default' : 'outline'} onClick={() => setMode('login')}>
                Login
              </Button>
            </div>

            <form onSubmit={onSubmit} className="space-y-4">
              {mode === 'register' ? (
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
                </div>
              ) : null}

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min 8 chars"
                  required
                />
                <p className="text-xs text-muted-foreground">Passwords must be short ASCII for now (bcrypt 72-byte limit).</p>
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Please wait...' : mode === 'register' ? 'Create account' : 'Sign in'}
              </Button>

              {error ? <p className="text-sm text-destructive">{error}</p> : null}
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

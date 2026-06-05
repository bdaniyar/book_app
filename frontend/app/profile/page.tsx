'use client'

import { useEffect, useMemo, useState } from 'react'

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Award, BookOpen, Calendar, Clock, Settings, Star } from 'lucide-react'

import { BookCard } from '@/components/book-card'
import {
  authService,
  libraryService,
  profileService,
  type InferredGenre,
  type ProfileStats,
  type ReadingActivity,
} from '@/lib/api-services'
import { clearSession, setAccessToken } from '@/lib/auth-storage'
import type { Book } from '@/lib/books-data'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'

type Mode = 'login' | 'register'

type MeUser = {
  id: string
  email: string
  username?: string | null
  first_name?: string | null
  last_name?: string | null
  bio?: string | null
  avatar_url?: string | null
  created_at?: string
}

const emptyStats: ProfileStats = {
  booksRead: 0,
  pagesRead: 0,
  avgRating: 0,
  reviewsWritten: 0,
  readingStreak: 0,
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

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [isAuthed, setIsAuthed] = useState(false)
  const [me, setMe] = useState<MeUser | null>(null)
  const [meLoading, setMeLoading] = useState(false)

  const [editOpen, setEditOpen] = useState(false)
  const [editUsername, setEditUsername] = useState('')
  const [editFirstName, setEditFirstName] = useState('')
  const [editLastName, setEditLastName] = useState('')
  const [editBio, setEditBio] = useState('')
  const [editEmail, setEditEmail] = useState('')

  const [privacy, setPrivacy] = useState<'public' | 'private'>('public')
  const [notifyEmail, setNotifyEmail] = useState(true)
  const [notifyPush, setNotifyPush] = useState(false)

  const [newPassword, setNewPassword] = useState('')
  const [newPassword2, setNewPassword2] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [passwordSaving, setPasswordSaving] = useState(false)

  const [editSaving, setEditSaving] = useState(false)

  const [username, setUsername] = useState('')
  const [stats, setStats] = useState<ProfileStats>(emptyStats)
  const [activity, setActivity] = useState<ReadingActivity[]>([])
  const [recentlyRead, setRecentlyRead] = useState<Book[]>([])
  const [favoriteGenres, setFavoriteGenres] = useState<InferredGenre[]>([])
  const [dashboardLoading, setDashboardLoading] = useState(false)

  const loadDashboard = async () => {
    setDashboardLoading(true)
    try {
      const [statsRes, activityRes, readRes, genreRes] = await Promise.all([
        profileService.getStats(),
        profileService.getReadingActivity(),
        libraryService.getRead(),
        profileService.getInferredGenres(),
      ])
      setStats(statsRes.success && statsRes.data ? statsRes.data : emptyStats)
      setActivity(activityRes.success && activityRes.data ? activityRes.data : [])
      setRecentlyRead(readRes.success && readRes.data ? readRes.data.slice(0, 6) : [])
      setFavoriteGenres(genreRes.success && genreRes.data ? genreRes.data : [])
    } finally {
      setDashboardLoading(false)
    }
  }

  useEffect(() => {
    // On page load try silent refresh (if refresh cookie exists)
    const run = async () => {
      setMeLoading(true)
      try {
        const r = await authService.refresh()
        if (r.success && r.data?.access_token) {
          setAccessToken(r.data.access_token)
          setIsAuthed(true)

          const res = await authService.me()
          if (res.success) {
            setMe(res.data as any)
            await loadDashboard()
          }
        }
      } finally {
        setMeLoading(false)
      }
    }

    run()
  }, [])

  useEffect(() => {
    if (!me) return
    setEditUsername(me.username ?? '')
    setEditFirstName(me.first_name ?? '')
    setEditLastName(me.last_name ?? '')
    setEditEmail(me.email ?? '')
    setEditBio(me.bio ?? '')
  }, [me])

  const displayName = useMemo(() => {
    const full = `${me?.first_name ?? ''} ${me?.last_name ?? ''}`.trim()
    if (full) return full
    if (me?.username && me.username.trim()) return me.username.trim()
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
        const regRes = await authService.register(email, password, username)
        if (!regRes.success || !regRes.data?.access_token) {
          setError(regRes.error || 'Registration failed')
          return
        }
        setAccessToken(regRes.data.access_token)
        setIsAuthed(true)
      } else {
        const res = await authService.login(email, password)
        if (!res.success || !res.data?.access_token) {
          setError(res.error || 'Login failed')
          return
        }
        setAccessToken(res.data.access_token)
        setIsAuthed(true)
      }

      setMeLoading(true)
      const meRes = await authService.me()
      if (meRes.success && meRes.data) {
        setMe(meRes.data as any)
        await loadDashboard()
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

  const onLogout = async () => {
    try {
      await authService.logout()
    } finally {
      clearSession()
      setAccessToken(null)
      setIsAuthed(false)
      setMe(null)
      setEmail('')
      setPassword('')
      setUsername('')
      setMode('login')
      setStats(emptyStats)
      setActivity([])
      setRecentlyRead([])
      setFavoriteGenres([])
    }
  }

  const onSaveProfile = async () => {
    setError(null)
    setEditSaving(true)
    try {
      const res = await profileService.update({
        username: editUsername.trim() ? editUsername.trim() : null,
        first_name: editFirstName.trim() ? editFirstName.trim() : null,
        last_name: editLastName.trim() ? editLastName.trim() : null,
        bio: editBio.trim() ? editBio.trim() : null,
        email: editEmail.trim() ? editEmail.trim() : null,
      })

      if (!res.success || !res.data) {
        setError(res.error || 'Failed to update profile')
        return
      }
      setMe(res.data)
      setEditOpen(false)
    } finally {
      setEditSaving(false)
    }
  }

  const onChangePassword = async () => {
    setError(null)

    if (!currentPassword.trim() || !newPassword.trim() || !newPassword2.trim()) {
      setError('Please fill current password and new password fields')
      return
    }

    setPasswordSaving(true)
    try {
      const res = await profileService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password2: newPassword2,
      })

      if (!res.success) {
        setError(res.error || 'Failed to change password')
        return
      }

      setCurrentPassword('')
      setNewPassword('')
      setNewPassword2('')
    } finally {
      setPasswordSaving(false)
    }
  }

  const onForgotPassword = async () => {
    setError(null)
    if (!email.trim()) {
      setError('Enter your email above first (the email on your account)')
      return
    }

    try {
      const res = await authService.forgotPassword(email.trim())
      if (!res.success) {
        setError(res.error || 'Failed to send reset link')
        return
      }
      setError('If this email exists, a reset link was generated. (Dev: check backend logs)')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to send reset link')
    }
  }

  // Logged in view (beautiful/original-ish UI)
  if (isAuthed) {
    const user = {
      displayName,
      username: me?.username ? `@${me.username}` : me?.email ? `@${me.email.split('@')[0]}` : '@user',
      avatar: me?.avatar_url || '/placeholder-user.jpg',
      bio:
        me?.bio?.trim() ||
        (me?.email ? `Reader profile for ${me.email}.` : 'Avid reader and book enthusiast. Always looking for the next great story to dive into.'),
      joinDate: me?.created_at
        ? new Intl.DateTimeFormat('en', { month: 'long', year: 'numeric' }).format(new Date(me.created_at))
        : 'January 2026',
      stats: {
        booksRead: stats.booksRead,
        reviews: stats.reviewsWritten,
        pagesRead: stats.pagesRead,
        avgRating: stats.avgRating,
        readingStreak: stats.readingStreak,
      },
    }

    return (
      <div className="w-full">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-7xl space-y-8">
          {/* Profile Header */}
          <Card className="border-border/50">
            <CardContent className="p-8">
              <div className="flex flex-col md:flex-row gap-8 items-start">
                <Avatar className="h-32 w-32 border-4 border-primary/10">
                  <AvatarImage src={user.avatar || '/placeholder.svg'} alt={displayName} />
                  <AvatarFallback className="text-3xl">{initials}</AvatarFallback>
                </Avatar>

                <div className="flex-1 space-y-4">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-3">
                      <h1 className="font-sans text-3xl font-bold">{user.displayName}</h1>
                      <Badge variant="secondary" className="rounded-full">
                        <Award className="h-3 w-3 mr-1" />
                        Top Reader
                      </Badge>
                      {meLoading ? (
                        <Badge variant="outline" className="rounded-full">
                          Loading…
                        </Badge>
                      ) : null}
                      {dashboardLoading ? (
                        <Badge variant="outline" className="rounded-full">
                          Syncing stats…
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
                      <div className="font-bold text-2xl">{user.stats.pagesRead.toLocaleString()}</div>
                      <div className="text-sm text-muted-foreground">Pages</div>
                    </div>
                    <Separator orientation="vertical" className="h-12" />
                    <div className="text-center">
                      <div className="font-bold text-2xl">{user.stats.avgRating.toFixed(1)}</div>
                      <div className="text-sm text-muted-foreground">Avg Rating</div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-3 pt-2">
                    <Button className="rounded-xl" onClick={() => setEditOpen(true)}>
                      <Settings className="h-4 w-4 mr-2" />
                      Edit Profile
                    </Button>
                    <Button variant="outline" className="rounded-xl bg-transparent" onClick={onLogout}>
                      Logout
                    </Button>
                  </div>

                  {/* Edit profile modal */}
                  <Dialog open={editOpen} onOpenChange={setEditOpen}>
                    <DialogContent className="sm:max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Edit profile</DialogTitle>
                        <DialogDescription>Обнови профиль. Настройки ниже пока без бэкенда.</DialogDescription>
                      </DialogHeader>

                      <Tabs defaultValue="profile" className="w-full">
                        <TabsList className="w-full grid grid-cols-2">
                          <TabsTrigger value="profile">Профиль</TabsTrigger>
                          <TabsTrigger value="settings">Настройки</TabsTrigger>
                        </TabsList>

                        <TabsContent value="profile" className="pt-4">
                          <div className="grid gap-4">
                            <div className="grid gap-2">
                              <Label htmlFor="edit-username">Username</Label>
                              <Input
                                id="edit-username"
                                value={editUsername}
                                onChange={(e) => setEditUsername(e.target.value)}
                                placeholder="alexreads"
                              />
                              <p className="text-xs text-muted-foreground">Должен быть уникальным.</p>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                              <div className="grid gap-2">
                                <Label htmlFor="edit-first">First name</Label>
                                <Input id="edit-first" value={editFirstName} onChange={(e) => setEditFirstName(e.target.value)} />
                              </div>
                              <div className="grid gap-2">
                                <Label htmlFor="edit-last">Last name</Label>
                                <Input id="edit-last" value={editLastName} onChange={(e) => setEditLastName(e.target.value)} />
                              </div>
                            </div>

                            <div className="grid gap-2">
                              <Label htmlFor="edit-email">Email</Label>
                              <Input
                                id="edit-email"
                                type="email"
                                value={editEmail}
                                onChange={(e) => setEditEmail(e.target.value)}
                                placeholder="you@example.com"
                              />
                            </div>

                            <div className="grid gap-2">
                              <Label htmlFor="edit-bio">Bio</Label>
                              <Textarea
                                id="edit-bio"
                                value={editBio}
                                onChange={(e) => setEditBio(e.target.value)}
                                placeholder="Расскажи о себе"
                              />
                            </div>
                          </div>
                        </TabsContent>

                        <TabsContent value="settings" className="pt-4">
                          <div className="grid gap-6">
                            <div className="rounded-lg border border-border/50 p-4">
                              <p className="text-sm font-medium mb-2">Privacy (placeholder)</p>
                              <div className="flex gap-2">
                                <Button
                                  type="button"
                                  variant={privacy === 'public' ? 'default' : 'outline'}
                                  onClick={() => setPrivacy('public')}
                                >
                                  Public
                                </Button>
                                <Button
                                  type="button"
                                  variant={privacy === 'private' ? 'default' : 'outline'}
                                  onClick={() => setPrivacy('private')}
                                >
                                  Private
                                </Button>
                              </div>
                              <p className="text-xs text-muted-foreground mt-2">Пока не сохраняется (нужны поля в модели и endpoint).</p>
                            </div>

                            <div className="rounded-lg border border-border/50 p-4">
                              <p className="text-sm font-medium mb-2">Notifications (placeholder)</p>
                              <div className="grid gap-3">
                                <label className="flex items-center gap-2 text-sm">
                                  <input
                                    type="checkbox"
                                    checked={notifyEmail}
                                    onChange={(e) => setNotifyEmail(e.target.checked)}
                                  />
                                  Email notifications
                                </label>
                                <label className="flex items-center gap-2 text-sm">
                                  <input
                                    type="checkbox"
                                    checked={notifyPush}
                                    onChange={(e) => setNotifyPush(e.target.checked)}
                                  />
                                  Push notifications
                                </label>
                              </div>
                              <p className="text-xs text-muted-foreground mt-2">Пока не сохраняется (нужны поля/таблица).</p>
                            </div>

                            <div className="rounded-lg border border-border/50 p-4">
                              <p className="text-sm font-medium mb-2">Change password</p>
                              <div className="grid gap-3">
                                <div className="grid gap-2">
                                  <Label htmlFor="current-password">Current password</Label>
                                  <Input
                                    id="current-password"
                                    type="password"
                                    value={currentPassword}
                                    onChange={(e) => setCurrentPassword(e.target.value)}
                                  />
                                </div>

                                <div className="grid gap-2">
                                  <Label htmlFor="new-password">New password</Label>
                                  <Input
                                    id="new-password"
                                    type="password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                  />
                                </div>

                                <div className="grid gap-2">
                                  <Label htmlFor="new-password2">Repeat new password</Label>
                                  <Input
                                    id="new-password2"
                                    type="password"
                                    value={newPassword2}
                                    onChange={(e) => setNewPassword2(e.target.value)}
                                  />
                                </div>

                                <div className="flex flex-wrap items-center gap-3 pt-1">
                                  <Button type="button" onClick={onChangePassword} disabled={passwordSaving}>
                                    {passwordSaving ? 'Saving…' : 'Update password'}
                                  </Button>
                                  <Button
                                    type="button"
                                    variant="outline"
                                    className="bg-transparent"
                                    onClick={onForgotPassword}
                                  >
                                    Forgot password
                                  </Button>
                                </div>

                                <p className="text-xs text-muted-foreground">
                                  Endpoint: <code>PUT /api/v1/profile/password</code>
                                </p>
                              </div>
                            </div>
                          </div>
                        </TabsContent>
                      </Tabs>

                      {error ? <p className="text-sm text-destructive">{error}</p> : null}

                      <DialogFooter>
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => {
                            setEditUsername(me?.username ?? '')
                            setEditFirstName(me?.first_name ?? '')
                            setEditLastName(me?.last_name ?? '')
                            setEditEmail(me?.email ?? '')
                            setEditBio(me?.bio ?? '')
                            setEditOpen(false)
                          }}
                          disabled={editSaving}
                        >
                          Cancel
                        </Button>
                        <Button type="button" onClick={onSaveProfile} disabled={editSaving}>
                          {editSaving ? 'Saving…' : 'Save changes'}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
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
                    <span className="font-semibold">{user.stats.booksRead}/30 books</span>
                  </div>
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${Math.min(100, Math.round((user.stats.booksRead / 30) * 100))}%` }}
                    />
                  </div>
                </div>

                <Separator />

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Pages Read</span>
                    <span className="font-semibold">{user.stats.pagesRead.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Avg. Rating</span>
                    <div className="flex items-center gap-1">
                      <Star className="h-4 w-4 fill-accent text-accent" />
                      <span className="font-semibold">{user.stats.avgRating.toFixed(1)}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Reading Streak</span>
                    <span className="font-semibold">{user.stats.readingStreak} days</span>
                  </div>
                </div>
                <Separator />
                <div className="space-y-3">
                  {activity.length > 0 ? (
                    activity.slice(0, 5).map((item) => (
                      <div key={`${item.date}-${item.title}`} className="flex items-start gap-3 rounded-lg bg-muted/40 p-3">
                        <Clock className="mt-0.5 h-4 w-4 text-muted-foreground" />
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">{item.title}</p>
                          <p className="text-xs text-muted-foreground">
                            {item.action.replaceAll('-', ' ')} ·{' '}
                            {new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(new Date(item.date))}
                          </p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No reading activity yet.</p>
                  )}
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
                  {favoriteGenres.length > 0 ? favoriteGenres.map((genre) => (
                    <Badge key={genre.name} variant="secondary" className="px-4 py-2 text-sm rounded-full">
                      {genre.name}
                      <span className="ml-2 rounded-full bg-background/80 px-2 py-0.5 text-xs text-muted-foreground">
                        {genre.count}
                      </span>
                    </Badge>
                  )) : (
                    <p className="text-sm text-muted-foreground">
                      Add books as Reading, Read, or Favorite to build this automatically.
                    </p>
                  )}
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
            {recentlyRead.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-6">
                {recentlyRead.map((book) => (
                  <BookCard key={book.id} book={book} />
                ))}
              </div>
            ) : (
              <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                Mark a book as read and it will appear here.
              </div>
            )}
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
                  <Label htmlFor="username">Username</Label>
                  <Input id="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="alexreads" />
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

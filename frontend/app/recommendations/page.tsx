"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import { BookOpen, RefreshCw, Sparkles, Star, TrendingUp } from "lucide-react"

import { BookCard } from "@/components/book-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  profileService,
  recommendationService,
  type InferredGenre,
  type ProfileStats,
} from "@/lib/api-services"
import type { Book } from "@/lib/books-data"

export default function RecommendationsPage() {
  const [books, setBooks] = useState<Book[]>([])
  const [stats, setStats] = useState<ProfileStats | null>(null)
  const [genres, setGenres] = useState<InferredGenre[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [needsAuth, setNeedsAuth] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setNeedsAuth(false)

    const [recommendations, statsResponse, genresResponse] = await Promise.all([
      recommendationService.getPersonalized(16),
      profileService.getStats(),
      profileService.getInferredGenres(),
    ])

    if (!recommendations.success) {
      setBooks([])
      setNeedsAuth(recommendations.status === 401)
      setError(recommendations.status === 401
        ? "Sign in so recommendations can use your reading history."
        : recommendations.error || "Could not load recommendations.")
    } else {
      setBooks(recommendations.data ?? [])
    }
    setStats(statsResponse.success && statsResponse.data ? statsResponse.data : null)
    setGenres(genresResponse.success ? genresResponse.data ?? [] : [])
    setLoading(false)
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="w-full">
      <div className="container mx-auto max-w-7xl space-y-10 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl space-y-4 text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
            <Sparkles className="h-4 w-4" /> Personalized for You
          </div>
          <h1 className="text-balance text-3xl font-bold md:text-4xl">Your Book Recommendations</h1>
          <p className="text-pretty text-lg text-muted-foreground">
            Real suggestions based on the genres and books in your library.
          </p>
        </div>

        {error ? (
          <div className="mx-auto flex max-w-2xl flex-col items-center gap-4 rounded-xl border border-border bg-card p-8 text-center">
            <p className="text-muted-foreground">{error}</p>
            {needsAuth ? (
              <Button asChild><Link href="/profile">Sign in</Link></Button>
            ) : (
              <Button variant="outline" onClick={() => void load()}>
                <RefreshCw className="mr-2 h-4 w-4" /> Try again
              </Button>
            )}
          </div>
        ) : null}

        {!error ? (
          <section className="space-y-6">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
              <div className="space-y-1">
                <h2 className="flex items-center gap-2 text-2xl font-semibold">
                  <Sparkles className="h-5 w-5 text-primary" /> Picked for You
                </h2>
                <p className="text-muted-foreground">Each result comes from your current reading profile.</p>
              </div>
              <Button variant="outline" asChild>
                <Link href="/assistant">Refine with AI Librarian</Link>
              </Button>
            </div>

            {loading ? (
              <p className="py-16 text-center text-muted-foreground">Building your recommendations…</p>
            ) : books.length ? (
              <div className="grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4">
                {books.map((book) => (
                  <div key={book.id} className="space-y-2">
                    <BookCard book={book} />
                    {book.recommendationReason ? (
                      <p className="px-1 text-xs leading-relaxed text-muted-foreground">
                        {book.recommendationReason}
                      </p>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed p-10 text-center">
                <BookOpen className="mx-auto mb-4 h-10 w-10 text-muted-foreground" />
                <h2 className="font-semibold">Your profile needs a little more signal</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Add books to your library and mark what you have read to receive recommendations.
                </p>
                <Button asChild className="mt-5"><Link href="/discover">Discover books</Link></Button>
              </div>
            )}
          </section>
        ) : null}

        {!needsAuth ? (
          <section className="grid gap-6 md:grid-cols-2">
            <Card className="border-border/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" /> Your Reading Profile
                </CardTitle>
                <CardDescription>Calculated from your actual activity</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between gap-4">
                  <span className="text-sm text-muted-foreground">Top genres</span>
                  <div className="flex flex-wrap justify-end gap-1">
                    {genres.length ? genres.slice(0, 3).map((genre) => (
                      <Badge key={genre.name} variant="secondary">{genre.name}</Badge>
                    )) : <span className="text-sm">Not enough data</span>}
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Books read</span>
                  <span className="font-semibold">{stats?.booksRead ?? "—"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Average rating given</span>
                  <span className="flex items-center gap-1 font-semibold">
                    <Star className="h-4 w-4 fill-accent text-accent" /> {stats ? stats.avgRating.toFixed(1) : "—"}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" /> Reading Activity
                </CardTitle>
                <CardDescription>Your current totals</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-3 gap-3 text-center">
                <Stat value={stats ? stats.pagesRead.toLocaleString() : "—"} label="Pages" />
                <Stat value={stats ? String(stats.reviewsWritten) : "—"} label="Reviews" />
                <Stat value={stats ? String(stats.readingStreak) : "—"} label="Day streak" />
              </CardContent>
            </Card>
          </section>
        ) : null}
      </div>
    </div>
  )
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-xl bg-muted/50 p-4">
      <div className="text-xl font-bold text-primary">{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{label}</div>
    </div>
  )
}

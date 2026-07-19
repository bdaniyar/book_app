"use client"

import { useCallback, useEffect, useMemo, useState, type ElementType } from "react"
import { Ban, BookMarked, BookOpen, CheckCircle2, Heart, RefreshCw } from "lucide-react"

import { BookCard } from "@/components/book-card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { libraryService, type LibraryEntry, type LibraryStatus } from "@/lib/api-services"

type LibraryTab = "all" | LibraryStatus | "favorites"

const tabs: Array<{ value: LibraryTab; label: string; shortLabel: string; icon: ElementType }> = [
  { value: "all", label: "All Books", shortLabel: "All", icon: BookOpen },
  { value: "reading", label: "Reading", shortLabel: "Now", icon: BookMarked },
  { value: "want-to-read", label: "Want to Read", shortLabel: "Later", icon: BookOpen },
  { value: "favorites", label: "Favorites", shortLabel: "Fav", icon: Heart },
  { value: "read", label: "Read", shortLabel: "Done", icon: CheckCircle2 },
  { value: "dropped", label: "Dropped", shortLabel: "Drop", icon: Ban },
]

export default function LibraryPage() {
  const [entries, setEntries] = useState<LibraryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    const response = await libraryService.getAll()
    if (response.success) {
      setEntries(response.data ?? [])
    } else {
      setEntries([])
      setError(response.status === 401 ? "Sign in to view your library." : response.error || "Could not load your library.")
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const groups = useMemo<Record<LibraryTab, LibraryEntry[]>>(() => ({
    all: entries,
    reading: entries.filter((entry) => entry.status === "reading"),
    "want-to-read": entries.filter((entry) => entry.status === "want-to-read"),
    favorites: entries.filter((entry) => entry.isFavorite),
    read: entries.filter((entry) => entry.status === "read"),
    dropped: entries.filter((entry) => entry.status === "dropped"),
  }), [entries])

  const updateEntry = useCallback((updated: LibraryEntry) => {
    setEntries((current) => current.map((entry) =>
      entry.id === updated.id ? updated : entry,
    ))
  }, [])

  return (
    <div className="w-full">
      <div className="container mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
        <div className="space-y-2">
          <h1 className="font-sans text-3xl font-bold md:text-4xl">My Library</h1>
          <p className="text-lg text-muted-foreground">
            {loading ? "Loading your personal collection…" : "Track every book, favorite, and reading milestone."}
          </p>
        </div>

        {error ? (
          <div className="flex flex-col items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-5">
            <p className="text-sm text-destructive">{error}</p>
            <Button variant="outline" size="sm" onClick={() => void load()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Try again
            </Button>
          </div>
        ) : null}

        {!error ? (
          <Tabs defaultValue="all" className="space-y-6">
            <TabsList className="grid h-auto w-full grid-cols-3 gap-1 rounded-xl lg:inline-grid lg:w-auto lg:grid-cols-6">
              {tabs.map(({ value, label, shortLabel, icon: Icon }) => (
                <TabsTrigger key={value} value={value} className="rounded-lg py-2">
                  <Icon className="mr-2 h-4 w-4" />
                  <span className="hidden sm:inline">{label}</span>
                  <span className="sm:hidden">{shortLabel}</span>
                  <span className="ml-2 rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                    {groups[value].length}
                  </span>
                </TabsTrigger>
              ))}
            </TabsList>

            {tabs.map(({ value, label, icon }) => (
              <TabsContent key={value} value={value} className="space-y-6">
                <LibraryGrid
                  entries={groups[value]}
                  loading={loading}
                  icon={icon}
                  title={`No ${label.toLowerCase()} yet`}
                  onEntryChanged={updateEntry}
                />
              </TabsContent>
            ))}
          </Tabs>
        ) : null}
      </div>
    </div>
  )
}

function LibraryGrid({
  entries,
  loading,
  icon: Icon,
  title,
  onEntryChanged,
}: {
  entries: LibraryEntry[]
  loading: boolean
  icon: ElementType
  title: string
  onEntryChanged: (entry: LibraryEntry) => void
}) {
  if (loading) {
    return <p className="py-12 text-center text-muted-foreground">Loading books…</p>
  }

  if (!entries.length) {
    return (
      <div className="flex flex-col items-center justify-center space-y-4 py-16 text-center">
        <Icon className="h-14 w-14 text-muted-foreground" />
        <div className="space-y-2">
          <h2 className="text-xl font-semibold">{title}</h2>
          <p className="max-w-md text-muted-foreground">Discover a book and add it to start building this collection.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      {entries.map((entry) => (
        <div key={entry.id} className="space-y-2">
          <BookCard
            book={entry.book}
            libraryStatus={entry.status}
            isFavorite={entry.isFavorite}
            onLibraryChanged={onEntryChanged}
          />
          {entry.status === "reading" && (entry.book.pages ?? 0) > 0 ? (
            <div className="space-y-1 px-1">
              <Progress value={Math.min(100, (entry.progressPages / (entry.book.pages ?? 1)) * 100)} />
              <p className="text-xs text-muted-foreground">
                {entry.progressPages} of {entry.book.pages} pages
              </p>
            </div>
          ) : null}
        </div>
      ))}
    </div>
  )
}

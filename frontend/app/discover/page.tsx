"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { AlertCircle, RefreshCw, Search, SlidersHorizontal } from "lucide-react"

import { BookCard } from "@/components/book-card"
import { CategoryChips } from "@/components/category-chips"
import { FilterPanel } from "@/components/filter-panel"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { bookService, categoryService } from "@/lib/api-services"
import type { Book, Category } from "@/lib/books-data"

export default function DiscoverPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [showFilters, setShowFilters] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [minRating, setMinRating] = useState(0)
  const [minYear, setMinYear] = useState(1900)
  const [books, setBooks] = useState<Book[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [categoryError, setCategoryError] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setCategoryError(false)

    const [booksResponse, genresResponse] = await Promise.all([
      bookService.getAll({ limit: 100 }),
      categoryService.getAll(),
    ])

    if (booksResponse.success) {
      setBooks(booksResponse.data ?? [])
    } else {
      setBooks([])
      setError(booksResponse.error || "Could not load the catalog.")
    }

    if (genresResponse.success) {
      setCategories((genresResponse.data ?? []).map((genre) => ({
        id: genre.id,
        name: genre.name,
        slug: genre.name.toLowerCase().replace(/\s+/g, "-"),
      })))
    } else {
      setCategories([])
      setCategoryError(true)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    setSearchQuery(params.get("q")?.trim() ?? "")
    void load()
  }, [load])

  useEffect(() => {
    const categorySlug = new URLSearchParams(window.location.search).get("category")
    if (!categorySlug || !categories.length) return
    const match = categories.find((category) => category.slug === categorySlug)
    if (match) setSelectedCategory(match.name)
  }, [categories])

  const filteredBooks = useMemo(() => books.filter((book) => {
    const query = searchQuery.toLocaleLowerCase()
    const matchesSearch = !query
      || book.title.toLocaleLowerCase().includes(query)
      || book.author.toLocaleLowerCase().includes(query)
      || book.isbn?.toLocaleLowerCase().includes(query)
    const matchesCategory = !selectedCategory
      || book.genres.includes(selectedCategory)
      || book.genre === selectedCategory
    const matchesRating = book.rating >= minRating
    const matchesYear = !book.publishedYear || book.publishedYear >= minYear
    return matchesSearch && matchesCategory && matchesRating && matchesYear
  }), [books, searchQuery, selectedCategory, minRating, minYear])

  const clearFilters = () => {
    setSearchQuery("")
    setSelectedCategory(null)
    setMinRating(0)
    setMinYear(1900)
    window.history.replaceState(null, "", "/discover")
  }

  return (
    <div className="w-full">
      <div className="container mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
        <div className="space-y-4">
          <h1 className="font-sans text-3xl font-bold md:text-4xl">Discover Books</h1>
          <p className="text-lg text-muted-foreground">
            {loading ? "Loading the catalog…" : `Explore ${books.length.toLocaleString()} available books`}
          </p>
        </div>

        {error ? (
          <div className="flex flex-col items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-5">
            <p className="flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" /> {error}
            </p>
            <Button variant="outline" size="sm" onClick={() => void load()}>
              <RefreshCw className="mr-2 h-4 w-4" /> Try again
            </Button>
          </div>
        ) : null}

        <div className="flex flex-col gap-4 md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search by title, author, or ISBN…"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              className="h-12 rounded-xl pl-12 text-base"
              aria-label="Search catalog"
            />
          </div>
          <Button
            variant="outline"
            size="lg"
            onClick={() => setShowFilters((visible) => !visible)}
            className="rounded-xl bg-transparent"
          >
            <SlidersHorizontal className="mr-2 h-5 w-5" /> Filters
          </Button>
        </div>

        {showFilters ? (
          <FilterPanel
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            categories={categories}
            minRating={minRating}
            onMinRatingChange={setMinRating}
            minYear={minYear}
            onMinYearChange={setMinYear}
          />
        ) : null}

        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Browse by Genre</h2>
          {categoryError ? (
            <p className="text-sm text-muted-foreground">Genres are temporarily unavailable.</p>
          ) : (
            <CategoryChips
              categories={categories}
              selectedCategory={selectedCategory}
              onCategorySelect={setSelectedCategory}
            />
          )}
        </div>

        {!error ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <p className="text-muted-foreground">
                {loading ? "Searching…" : `${filteredBooks.length} ${filteredBooks.length === 1 ? "book" : "books"} found`}
              </p>
              {(searchQuery || selectedCategory || minRating > 0 || minYear > 1900) ? (
                <Button variant="ghost" onClick={clearFilters}>Clear filters</Button>
              ) : null}
            </div>

            {!loading && filteredBooks.length ? (
              <div className="grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                {filteredBooks.map((book) => <BookCard key={book.id} book={book} />)}
              </div>
            ) : !loading ? (
              <div className="flex flex-col items-center justify-center space-y-4 py-16 text-center">
                <Search className="h-14 w-14 text-muted-foreground" />
                <div className="space-y-2">
                  <h2 className="text-xl font-semibold">No books found</h2>
                  <p className="text-muted-foreground">
                    {books.length ? "Try changing your search or filters." : "The catalog is empty."}
                  </p>
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  )
}

"use client"

import { useEffect, useMemo, useState } from "react"
import { Search, SlidersHorizontal } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { BookCard } from "@/components/book-card"
import { CategoryChips } from "@/components/category-chips"
import { FilterPanel } from "@/components/filter-panel"
import type { Book, Category } from "@/lib/books-data"
import { categories as fallbackCategories, recommendedBooks, trendingBooks } from "@/lib/books-data"
import { bookService, categoryService } from "@/lib/api-services"

export default function DiscoverPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [showFilters, setShowFilters] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [minRating, setMinRating] = useState(0)
  const [minYear, setMinYear] = useState(1900)
  const [books, setBooks] = useState<Book[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true

    async function load() {
      const [booksRes, genresRes] = await Promise.all([
        bookService.getAll({ limit: 60 }),
        categoryService.getAll(),
      ])
      if (!mounted) return
      if (booksRes.success && booksRes.data?.length) {
        setBooks(booksRes.data)
      } else {
        setBooks([...trendingBooks, ...recommendedBooks])
      }
      if (genresRes.success && genresRes.data) {
        const nextCategories = genresRes.data.map((genre: any) => ({
            id: genre.id,
            name: genre.name,
            slug: genre.slug || genre.name.toLowerCase().replace(/\s+/g, "-"),
          }))
        setCategories(nextCategories)
        const params = new URLSearchParams(window.location.search)
        const categorySlug = params.get("category")
        if (categorySlug) {
          const match = nextCategories.find((category) => category.slug === categorySlug)
          if (match) setSelectedCategory(match.name)
        }
      } else {
        setCategories(fallbackCategories)
      }
      setLoading(false)
    }

    load()
    return () => {
      mounted = false
    }
  }, [])

  const filteredBooks = useMemo(() => books.filter((book) => {
    const matchesSearch =
      searchQuery === "" ||
      book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      book.author.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesCategory = !selectedCategory || book.genre === selectedCategory
    const matchesRating = book.rating >= minRating
    const matchesYear = !book.publishedYear || book.publishedYear >= minYear

    return matchesSearch && matchesCategory && matchesRating && matchesYear
  }), [books, searchQuery, selectedCategory, minRating, minYear])

  return (
    <div className="w-full">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 max-w-7xl">
        {/* Header */}
        <div className="space-y-4">
          <h1 className="font-sans text-3xl md:text-4xl font-bold">Discover Books</h1>
          <p className="text-muted-foreground text-lg">
            {loading ? "Loading the catalog..." : `Explore our collection of ${books.length.toLocaleString()} books`}
          </p>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search by title or author..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 h-12 text-base rounded-xl"
            />
          </div>
          <Button
            variant="outline"
            size="lg"
            onClick={() => setShowFilters(!showFilters)}
            className="rounded-xl bg-transparent md:w-auto"
          >
            <SlidersHorizontal className="h-5 w-5 mr-2" />
            Filters
          </Button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <FilterPanel
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            categories={categories}
            minRating={minRating}
            onMinRatingChange={setMinRating}
            minYear={minYear}
            onMinYearChange={setMinYear}
          />
        )}

        {/* Categories */}
        <div className="space-y-4">
          <h2 className="font-sans text-xl font-semibold">Browse by Genre</h2>
          <CategoryChips
            categories={categories}
            selectedCategory={selectedCategory}
            onCategorySelect={setSelectedCategory}
          />
        </div>

        {/* Results */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-muted-foreground">
              {filteredBooks.length} {filteredBooks.length === 1 ? "book" : "books"} found
            </p>
            {(searchQuery || selectedCategory || minRating > 0 || minYear > 1900) && (
              <Button
                variant="ghost"
                onClick={() => {
                  setSearchQuery("")
                  setSelectedCategory(null)
                  setMinRating(0)
                  setMinYear(1900)
                }}
              >
                Clear filters
              </Button>
            )}
          </div>

          {filteredBooks.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {filteredBooks.map((book) => (
                <BookCard key={book.id} book={book} />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
              <Search className="h-16 w-16 text-muted-foreground" />
              <div className="space-y-2">
                <h3 className="font-sans text-xl font-semibold">No books found</h3>
                <p className="text-muted-foreground">
                  Try adjusting your search or filters to find what you're looking for
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

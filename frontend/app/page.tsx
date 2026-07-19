import Link from "next/link"
import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { BookCard } from "@/components/book-card"
import { CategoryChips } from "@/components/category-chips"
import { getCategories, getTrendingBooks } from "@/lib/public-api"

export const dynamic = "force-dynamic"

export default async function HomePage() {
  const [trendingBooks, categories] = await Promise.all([
    getTrendingBooks(12),
    getCategories(),
  ])

  return (
    <div className="w-full">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12 max-w-7xl">
        {/* Hero Section */}
        <section className="space-y-6 text-center max-w-3xl mx-auto">
          <h1 className="font-sans text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-balance">
            Discover Your Next
            <span className="text-primary"> Great Read</span>
          </h1>
          <p className="text-lg text-muted-foreground text-pretty">
            Explore the catalog, track your reading, and get recommendations shaped by your own library.
          </p>

          {/* Search Bar */}
          <form action="/discover" method="get" className="flex max-w-2xl gap-2 mx-auto">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                name="q"
                type="search"
                placeholder="Search by title, author, or ISBN..."
                className="pl-12 h-12 text-base rounded-xl"
                aria-label="Search books"
              />
            </div>
            <Button type="submit" size="lg" className="h-12 rounded-xl">Search</Button>
          </form>
        </section>

        {/* Categories */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="font-sans text-2xl font-semibold">Browse by Category</h2>
            <Button variant="ghost" asChild>
              <Link href="/discover">View all</Link>
            </Button>
          </div>
          <CategoryChips categories={categories} />
        </section>

        {/* Trending Books */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-sans text-2xl font-semibold">Trending Now</h2>
              <p className="text-muted-foreground mt-1">Popular books based on catalog ratings</p>
            </div>
          </div>
          {trendingBooks.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-6">
              {trendingBooks.map((book) => (
                <BookCard key={book.id} book={book} />
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No books are available yet.</p>
          )}
        </section>

        {/* CTA Section */}
        <section className="bg-gradient-to-br from-primary/10 via-accent/10 to-primary/5 rounded-2xl p-8 md:p-12 text-center space-y-4">
          <h2 className="font-sans text-3xl font-semibold text-balance">Get Personalized Recommendations</h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto text-pretty">
            Tell us what you like and we'll suggest books tailored just for you
          </p>
          <Button size="lg" className="rounded-xl" asChild>
            <Link href="/recommendations">Get Started</Link>
          </Button>
        </section>
      </div>
    </div>
  )
}

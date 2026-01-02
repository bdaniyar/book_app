import { notFound } from "next/navigation"
import Image from "next/image"
import { Star, BookmarkPlus, Share2, Clock, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { BookCard } from "@/components/book-card"
import { ReviewList } from "@/components/review-list"
import { trendingBooks, recommendedBooks } from "@/lib/books-data"

type PageProps = {
  params: Promise<{ id: string }>
}

export default async function BookDetailPage({ params }: PageProps) {
  const { id } = await params

  // Find book in both arrays
  const book = [...trendingBooks, ...recommendedBooks].find((b) => b.id === id)

  if (!book) {
    notFound()
  }

  // Get similar books (same genre, excluding current book)
  const similarBooks = [...trendingBooks, ...recommendedBooks]
    .filter((b) => b.genre === book.genre && b.id !== book.id)
    .slice(0, 4)

  return (
    <div className="w-full">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-7xl space-y-12">
        {/* Book Header */}
        <div className="grid md:grid-cols-[300px_1fr] gap-8 lg:gap-12">
          {/* Book Cover */}
          <div className="space-y-4">
            <div className="relative aspect-[2/3] overflow-hidden rounded-xl bg-muted shadow-2xl">
              <Image
                src={book.coverUrl || "/placeholder.svg"}
                alt={`${book.title} cover`}
                fill
                className="object-cover"
                priority
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button className="flex-1 rounded-xl" size="lg">
                <BookmarkPlus className="h-4 w-4 mr-2" />
                Save to Library
              </Button>
              <Button variant="outline" size="lg" className="rounded-xl bg-transparent">
                <Share2 className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Book Info */}
          <div className="space-y-6">
            <div className="space-y-3">
              <Badge variant="secondary" className="rounded-full">
                {book.genre}
              </Badge>
              <h1 className="font-sans text-4xl md:text-5xl font-bold tracking-tight text-balance">{book.title}</h1>
              <p className="text-xl text-muted-foreground">by {book.author}</p>
            </div>

            {/* Rating */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="flex">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`h-5 w-5 ${i < Math.floor(book.rating) ? "fill-accent text-accent" : "text-muted"}`}
                    />
                  ))}
                </div>
                <span className="font-semibold text-lg">{book.rating}</span>
              </div>
              <Separator orientation="vertical" className="h-6" />
              <span className="text-muted-foreground">{book.reviewCount.toLocaleString()} reviews</span>
            </div>

            {/* Book Details */}
            <div className="flex flex-wrap gap-6 text-sm">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Pages:</span>
                <span className="font-medium">{book.pages}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Published:</span>
                <span className="font-medium">{book.publishedYear}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">ISBN:</span>
                <span className="font-medium font-mono text-xs">{book.isbn}</span>
              </div>
            </div>

            <Separator />

            {/* Description */}
            <div className="space-y-3">
              <h2 className="font-sans text-xl font-semibold">About this book</h2>
              <p className="text-muted-foreground leading-relaxed text-pretty">{book.description}</p>
            </div>
          </div>
        </div>

        <Separator />

        {/* Reviews Section */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="font-sans text-2xl font-semibold">Reader Reviews</h2>
            <Button variant="outline" className="rounded-xl bg-transparent">
              Write a Review
            </Button>
          </div>
          <ReviewList bookId={book.id} />
        </section>

        {/* Similar Books */}
        {similarBooks.length > 0 && (
          <>
            <Separator />
            <section className="space-y-6">
              <h2 className="font-sans text-2xl font-semibold">Similar Books</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {similarBooks.map((similarBook) => (
                  <BookCard key={similarBook.id} book={similarBook} />
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  )
}

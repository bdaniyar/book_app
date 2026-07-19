import { notFound } from "next/navigation"
import Image from "next/image"
import Link from "next/link"
import { Star, Clock, FileText, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { BookCard } from "@/components/book-card"
import { BookReviews } from "@/components/book-reviews"
import { BookActions } from "@/components/book-actions"
import { getBook, getSimilarBooks } from "@/lib/public-api"

type PageProps = {
  params: Promise<{ id: string }>
}

export default async function BookDetailPage({ params }: PageProps) {
  const { id } = await params

  const book = await getBook(id)

  if (!book) {
    notFound()
  }

  const similarBooks = await getSimilarBooks(book.id, 4)

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
            <div className="flex flex-col gap-2 sm:flex-row">
              <BookActions bookId={book.id} className="flex-1" />
              <Button variant="outline" className="rounded-xl bg-transparent" asChild>
                <Link href={`/assistant?bookId=${encodeURIComponent(book.id)}`}>
                  <Sparkles className="mr-2 h-4 w-4" /> Ask AI
                </Link>
              </Button>
            </div>
          </div>

          {/* Book Info */}
          <div className="space-y-6">
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {book.genres.map((genre) => (
                  <Badge key={genre} variant="secondary" className="rounded-full">{genre}</Badge>
                ))}
              </div>
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
                <span className="font-medium">{book.pages ?? "Unknown"}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Published:</span>
                <span className="font-medium">{book.publishedYear ?? "Unknown"}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">ISBN:</span>
                <span className="font-medium font-mono text-xs">{book.isbn ?? "Not available"}</span>
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
        <BookReviews bookId={book.id} />

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

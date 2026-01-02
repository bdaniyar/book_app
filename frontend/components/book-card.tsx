import Link from "next/link"
import Image from "next/image"
import { Star } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import type { Book } from "@/lib/books-data"
import { cn } from "@/lib/utils"

type BookCardProps = {
  book: Book
  className?: string
}

export function BookCard({ book, className }: BookCardProps) {
  return (
    <Link href={`/book/${book.id}`} prefetch={false}>
      <Card
        className={cn("group overflow-hidden border-0 bg-card hover:shadow-lg transition-all duration-300", className)}
      >
        <CardContent className="p-0">
          <div className="relative aspect-[2/3] overflow-hidden rounded-t-lg bg-muted">
            <Image
              src={book.coverUrl || "/placeholder.svg"}
              alt={`${book.title} cover`}
              fill
              className="object-cover transition-transform duration-300 group-hover:scale-105"
              loading="lazy"
              sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 16vw"
            />
          </div>
          <div className="p-4 space-y-2">
            <h3 className="font-semibold text-sm line-clamp-2 leading-snug text-balance">{book.title}</h3>
            <p className="text-xs text-muted-foreground line-clamp-1">{book.author}</p>
            <div className="flex items-center gap-1">
              <Star className="h-3.5 w-3.5 fill-accent text-accent" />
              <span className="text-xs font-medium">{book.rating}</span>
              <span className="text-xs text-muted-foreground">({book.reviewCount.toLocaleString()})</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}

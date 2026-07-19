import Link from "next/link"
import { BookOpen, Database } from "lucide-react"

import { BookCard } from "@/components/book-card"
import { Badge } from "@/components/ui/badge"
import type { AssistantCitation } from "@/lib/assistant-api"
import type { Book } from "@/lib/books-data"

export function BookResults({ books, citations }: { books: Book[]; citations: AssistantCitation[] }) {
  if (!books.length && !citations.length) return null

  return (
    <div className="mt-4 space-y-4">
      {books.length ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {books.map((book) => <BookCard key={book.id} book={book} />)}
        </div>
      ) : null}

      {citations.length ? (
        <div className="rounded-lg border border-border/60 bg-background/60 p-3">
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <Database className="h-3.5 w-3.5" /> Catalog facts used
          </div>
          <div className="flex flex-wrap gap-2">
            {citations.map((citation) => (
              <Badge key={`${citation.bookId}-${citation.fields.join("-")}`} variant="outline" asChild>
                <Link href={`/book/${citation.bookId}`}>
                  <BookOpen className="mr-1 h-3 w-3" />
                  {citation.fields.length ? citation.fields.join(", ") : "book record"}
                </Link>
              </Badge>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}

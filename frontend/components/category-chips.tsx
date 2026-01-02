import Link from "next/link"
import { memo } from "react"
import type { Category } from "@/lib/books-data"
import { Badge } from "@/components/ui/badge"

type CategoryChipsProps = {
  categories: Category[]
}

export const CategoryChips = memo(function CategoryChips({ categories }: CategoryChipsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {categories.map((category) => (
        <Link key={category.id} href={`/discover?category=${category.slug}`} prefetch={false}>
          <Badge
            variant="secondary"
            className="px-4 py-2 text-sm font-medium rounded-full hover:bg-primary hover:text-primary-foreground transition-colors cursor-pointer"
          >
            {category.name}
          </Badge>
        </Link>
      ))}
    </div>
  )
})

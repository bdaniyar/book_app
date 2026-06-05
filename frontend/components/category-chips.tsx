"use client"

import Link from "next/link"
import { memo } from "react"
import type { Category } from "@/lib/books-data"
import { Badge } from "@/components/ui/badge"

type CategoryChipsProps = {
  categories: Category[]
  selectedCategory?: string | null
  onCategorySelect?: (category: string | null) => void
}

export const CategoryChips = memo(function CategoryChips({
  categories,
  selectedCategory,
  onCategorySelect,
}: CategoryChipsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {onCategorySelect ? (
        <Badge
          variant={!selectedCategory ? "default" : "secondary"}
          className="px-4 py-2 text-sm font-medium rounded-full transition-colors cursor-pointer"
          onClick={() => onCategorySelect(null)}
        >
          All
        </Badge>
      ) : null}
      {categories.map((category) => (
        <Link
          key={category.id}
          href={`/discover?category=${category.slug}`}
          prefetch={false}
          onClick={(event) => {
            if (!onCategorySelect) return
            event.preventDefault()
            onCategorySelect(category.name)
          }}
        >
          <Badge
            variant={selectedCategory === category.name ? "default" : "secondary"}
            className="px-4 py-2 text-sm font-medium rounded-full hover:bg-primary hover:text-primary-foreground transition-colors cursor-pointer"
          >
            {category.name}
          </Badge>
        </Link>
      ))}
    </div>
  )
})

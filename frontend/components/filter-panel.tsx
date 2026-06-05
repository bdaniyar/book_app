"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Slider } from "@/components/ui/slider"
import type { Category } from "@/lib/books-data"

type FilterPanelProps = {
  selectedCategory: string | null
  onCategoryChange: (category: string | null) => void
  categories: Category[]
  minRating: number
  onMinRatingChange: (rating: number) => void
  minYear: number
  onMinYearChange: (year: number) => void
}

export function FilterPanel({
  selectedCategory,
  onCategoryChange,
  categories,
  minRating,
  onMinRatingChange,
  minYear,
  onMinYearChange,
}: FilterPanelProps) {
  return (
    <Card className="border-border/50">
      <CardContent className="grid gap-6 p-6 md:grid-cols-3">
        <div className="space-y-4">
          <h3 className="font-semibold">Genre</h3>
          <RadioGroup
            value={selectedCategory || "all"}
            onValueChange={(value) => onCategoryChange(value === "all" ? null : value)}
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="all" id="all" />
              <Label htmlFor="all" className="cursor-pointer">
                All Genres
              </Label>
            </div>
            {categories.map((category) => (
              <div key={category.id} className="flex items-center space-x-2">
                <RadioGroupItem value={category.name} id={category.id} />
                <Label htmlFor={category.id} className="cursor-pointer">
                  {category.name}
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Minimum Rating: {minRating.toFixed(1)}</Label>
            <Slider
              value={[minRating]}
              max={5}
              step={0.5}
              className="w-full"
              onValueChange={([value]) => onMinRatingChange(value ?? 0)}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0</span>
              <span>5</span>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Publication Year: {minYear}+</Label>
            <Slider
              value={[minYear]}
              min={1900}
              max={2026}
              step={1}
              className="w-full"
              onValueChange={([value]) => onMinYearChange(value ?? 1900)}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>1900</span>
              <span>2026</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

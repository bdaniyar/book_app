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
}

export function FilterPanel({ selectedCategory, onCategoryChange, categories }: FilterPanelProps) {
  return (
    <Card className="border-border/50">
      <CardContent className="p-6 space-y-6">
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
            <Label>Minimum Rating</Label>
            <Slider defaultValue={[0]} max={5} step={0.5} className="w-full" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0</span>
              <span>5</span>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Publication Year</Label>
            <Slider defaultValue={[2000]} min={1900} max={2024} step={1} className="w-full" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>1900</span>
              <span>2024</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

"use client"

import { useState } from "react"
import { Loader2, Star } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { reviewService } from "@/lib/api-services"
import { cn } from "@/lib/utils"

export function ReviewDialog({ bookId, onCreated }: { bookId: string; onCreated: () => void }) {
  const [open, setOpen] = useState(false)
  const [rating, setRating] = useState(0)
  const [text, setText] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    setError(null)
    if (!rating) {
      setError("Choose a rating from 1 to 5 stars.")
      return
    }
    if (!text.trim()) {
      setError("Write a short review before submitting.")
      return
    }

    setSubmitting(true)
    const response = await reviewService.create(bookId, rating, text.trim())
    setSubmitting(false)
    if (!response.success) {
      setError(response.status === 401 ? "Sign in before writing a review." : response.error || "Could not publish review.")
      return
    }

    setOpen(false)
    setRating(0)
    setText("")
    onCreated()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="rounded-xl bg-transparent">Write a Review</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Write a review</DialogTitle>
          <DialogDescription>Your rating and review will be visible to other readers.</DialogDescription>
        </DialogHeader>
        <div className="space-y-5 py-2">
          <div className="space-y-2">
            <Label>Rating</Label>
            <div className="flex gap-1" role="radiogroup" aria-label="Book rating">
              {Array.from({ length: 5 }, (_, index) => {
                const value = index + 1
                return (
                  <button
                    key={value}
                    type="button"
                    role="radio"
                    aria-checked={rating === value}
                    aria-label={`${value} star${value === 1 ? "" : "s"}`}
                    className="rounded-md p-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    onClick={() => setRating(value)}
                  >
                    <Star className={cn("h-7 w-7", value <= rating ? "fill-accent text-accent" : "text-muted-foreground")} />
                  </button>
                )
              })}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="review-text">Review</Label>
            <Textarea
              id="review-text"
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="What did you think about this book?"
              maxLength={5000}
              rows={6}
            />
            <p className="text-right text-xs text-muted-foreground">{text.length}/5000</p>
          </div>
          {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={submitting}>Cancel</Button>
          <Button onClick={() => void submit()} disabled={submitting}>
            {submitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Publish review
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

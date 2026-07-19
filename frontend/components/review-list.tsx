"use client"

import { useEffect, useState } from "react"
import { Star } from "lucide-react"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card, CardContent } from "@/components/ui/card"
import { reviewService, type Review } from "@/lib/api-services"

export function ReviewList({ bookId, refreshKey = 0 }: { bookId: string; refreshKey?: number }) {
  const [reviews, setReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    void reviewService.getByBookId(bookId).then((response) => {
      if (!active) return
      if (response.success) {
        setReviews(response.data ?? [])
      } else {
        setReviews([])
        setError(response.error || "Could not load reviews.")
      }
      setLoading(false)
    })

    return () => {
      active = false
    }
  }, [bookId, refreshKey])

  if (loading) return <p className="text-muted-foreground">Loading reviews…</p>
  if (error) return <p className="text-sm text-destructive">{error}</p>
  if (!reviews.length) return <p className="text-muted-foreground">No reviews yet. Be the first to share your thoughts.</p>

  return (
    <div className="space-y-4">
      {reviews.map((review) => (
        <Card key={review.id} className="border-border/50">
          <CardContent className="space-y-4 p-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <Avatar>
                  <AvatarImage src={review.userAvatar || "/placeholder.svg"} alt={review.userName} />
                  <AvatarFallback>{review.userName.charAt(0).toUpperCase()}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-semibold">{review.userName}</p>
                  <p className="text-sm text-muted-foreground">
                    {new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(review.createdAt))}
                  </p>
                </div>
              </div>
              <div className="flex" aria-label={`${review.rating} out of 5 stars`}>
                {Array.from({ length: 5 }, (_, index) => (
                  <Star
                    key={index}
                    className={`h-4 w-4 ${index < review.rating ? "fill-accent text-accent" : "text-muted"}`}
                  />
                ))}
              </div>
            </div>
            <p className="text-pretty leading-relaxed text-muted-foreground">{review.text}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

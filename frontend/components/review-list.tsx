"use client"

import { useEffect, useState } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Star } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { reviewService } from "@/lib/api-services"

type Review = {
  id: string
  userName: string
  userAvatar?: string
  rating: number
  createdAt: string
  text: string
  helpful: number
}

type ReviewListProps = {
  bookId: string
}

export function ReviewList({ bookId }: ReviewListProps) {
  const [reviews, setReviews] = useState<Review[]>([])

  useEffect(() => {
    let mounted = true

    async function load() {
      const res = await reviewService.getByBookId(bookId)
      if (mounted && res.success && res.data) setReviews(res.data as Review[])
    }

    load()
    return () => {
      mounted = false
    }
  }, [bookId])

  return (
    <div className="space-y-4">
      {reviews.length === 0 && (
        <p className="text-muted-foreground">No reviews yet.</p>
      )}
      {reviews.map((review) => (
        <Card key={review.id} className="border-border/50">
          <CardContent className="p-6 space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <Avatar>
                  <AvatarImage src={review.userAvatar || "/placeholder.svg"} alt={review.userName} />
                  <AvatarFallback>{review.userName.charAt(0)}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-semibold">{review.userName}</p>
                  <p className="text-sm text-muted-foreground">
                    {new Date(review.createdAt).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className={`h-4 w-4 ${i < review.rating ? "fill-accent text-accent" : "text-muted"}`} />
                ))}
              </div>
            </div>
            <p className="text-muted-foreground leading-relaxed text-pretty">{review.text}</p>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <button className="hover:text-foreground transition-colors">Helpful ({review.helpful})</button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

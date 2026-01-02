import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Star } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"

type Review = {
  id: string
  userName: string
  userAvatar: string
  rating: number
  date: string
  content: string
  helpful: number
}

type ReviewListProps = {
  bookId: string
}

// Mock reviews data
const mockReviews: Review[] = [
  {
    id: "1",
    userName: "Sarah Mitchell",
    userAvatar: "/placeholder.svg?height=40&width=40",
    rating: 5,
    date: "2 weeks ago",
    content:
      "Absolutely captivating from start to finish! The author has a unique way of weaving complex characters into an engaging narrative. I couldn't put it down and finished it in just two days. Highly recommend to anyone looking for a thought-provoking read.",
    helpful: 24,
  },
  {
    id: "2",
    userName: "James Chen",
    userAvatar: "/placeholder.svg?height=40&width=40",
    rating: 4,
    date: "1 month ago",
    content:
      "A solid read with great character development. The pacing was a bit slow in the middle, but the ending made up for it. The themes explored are relevant and made me think long after I finished the book.",
    helpful: 18,
  },
  {
    id: "3",
    userName: "Emily Rodriguez",
    userAvatar: "/placeholder.svg?height=40&width=40",
    rating: 5,
    date: "1 month ago",
    content:
      "One of the best books I've read this year! The writing is beautiful and the story is both heartbreaking and hopeful. I've already recommended it to all my friends.",
    helpful: 31,
  },
  {
    id: "4",
    userName: "Michael Thompson",
    userAvatar: "/placeholder.svg?height=40&width=40",
    rating: 4,
    date: "2 months ago",
    content:
      "Great storytelling and well-developed characters. Some parts felt a bit predictable, but overall a very enjoyable read. The author's style is engaging and easy to follow.",
    helpful: 12,
  },
]

export function ReviewList({ bookId }: ReviewListProps) {
  return (
    <div className="space-y-4">
      {mockReviews.map((review) => (
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
                  <p className="text-sm text-muted-foreground">{review.date}</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className={`h-4 w-4 ${i < review.rating ? "fill-accent text-accent" : "text-muted"}`} />
                ))}
              </div>
            </div>
            <p className="text-muted-foreground leading-relaxed text-pretty">{review.content}</p>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <button className="hover:text-foreground transition-colors">Helpful ({review.helpful})</button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

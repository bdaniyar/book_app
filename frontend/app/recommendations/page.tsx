import { Sparkles, TrendingUp, Users, Zap } from "lucide-react"
import { BookCard } from "@/components/book-card"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { recommendedBooks, trendingBooks } from "@/lib/books-data"

export default function RecommendationsPage() {
  // Mock personalized recommendations based on different criteria
  const forYou = [recommendedBooks[0], recommendedBooks[1], trendingBooks[0], trendingBooks[2]]
  const trending = [trendingBooks[1], trendingBooks[4], trendingBooks[5]]
  const basedOnReading = [recommendedBooks[2], recommendedBooks[3], trendingBooks[3]]
  const popularInGenre = [trendingBooks[0], trendingBooks[2], recommendedBooks[0]]

  return (
    <div className="w-full">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-7xl space-y-12">
        {/* Header */}
        <div className="space-y-4 text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium">
            <Sparkles className="h-4 w-4" />
            Personalized for You
          </div>
          <h1 className="font-sans text-3xl md:text-4xl font-bold text-balance">Your Book Recommendations</h1>
          <p className="text-muted-foreground text-lg text-pretty">
            Discover your next favorite book with recommendations tailored to your reading preferences
          </p>
        </div>

        {/* Recommendation Sections */}
        <section className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center h-10 w-10 rounded-lg bg-primary/10">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="font-sans text-2xl font-semibold">Picked For You</h2>
              <p className="text-muted-foreground">Based on your reading history and preferences</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {forYou.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </section>

        <section className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center h-10 w-10 rounded-lg bg-primary/10">
              <TrendingUp className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="font-sans text-2xl font-semibold">Trending in Your Genres</h2>
              <p className="text-muted-foreground">Popular books in genres you love</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {trending.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </section>

        <section className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center h-10 w-10 rounded-lg bg-primary/10">
              <Zap className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="font-sans text-2xl font-semibold">Because You Read</h2>
              <p className="text-muted-foreground">Similar to books you've enjoyed</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {basedOnReading.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </section>

        <section className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center h-10 w-10 rounded-lg bg-primary/10">
              <Users className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="font-sans text-2xl font-semibold">Readers Like You Enjoyed</h2>
              <p className="text-muted-foreground">Popular with readers who share your taste</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {popularInGenre.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </section>

        {/* Recommendation Insights */}
        <section className="grid md:grid-cols-3 gap-6">
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Your Reading Profile
              </CardTitle>
              <CardDescription>Based on your activity</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Favorite Genre</span>
                <Badge variant="secondary">Fiction</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Books Read</span>
                <span className="font-semibold">24</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Avg. Rating Given</span>
                <span className="font-semibold">4.3</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Reading Streak
              </CardTitle>
              <CardDescription>Keep up the great work</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-center py-4">
                <div className="text-4xl font-bold text-primary">7</div>
                <div className="text-sm text-muted-foreground mt-1">days in a row</div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                Community
              </CardTitle>
              <CardDescription>Connect with readers</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Following</span>
                <span className="font-semibold">42</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Followers</span>
                <span className="font-semibold">38</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Reviews Written</span>
                <span className="font-semibold">15</span>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  )
}

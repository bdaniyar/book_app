import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { BookOpen, Star, Award, Calendar, Settings } from "lucide-react"
import { BookCard } from "@/components/book-card"
import { trendingBooks } from "@/lib/books-data"

export default function ProfilePage() {
  // Mock user data
  const user = {
    name: "Alex Johnson",
    username: "@alexreads",
    avatar: "/placeholder.svg?height=120&width=120",
    bio: "Avid reader and book enthusiast. Always looking for the next great story to dive into.",
    joinDate: "January 2023",
    stats: {
      booksRead: 24,
      reviews: 15,
      followers: 38,
      following: 42,
    },
  }

  const recentlyRead = [trendingBooks[0], trendingBooks[1], trendingBooks[2]]
  const favoriteGenres = ["Fiction", "Mystery", "Science Fiction", "Biography"]

  return (
    <div className="w-full">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-7xl space-y-8">
        {/* Profile Header */}
        <Card className="border-border/50">
          <CardContent className="p-8">
            <div className="flex flex-col md:flex-row gap-8 items-start">
              <Avatar className="h-32 w-32 border-4 border-primary/10">
                <AvatarImage src={user.avatar || "/placeholder.svg"} alt={user.name} />
                <AvatarFallback className="text-3xl">{user.name.charAt(0)}</AvatarFallback>
              </Avatar>

              <div className="flex-1 space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <h1 className="font-sans text-3xl font-bold">{user.name}</h1>
                    <Badge variant="secondary" className="rounded-full">
                      <Award className="h-3 w-3 mr-1" />
                      Top Reader
                    </Badge>
                  </div>
                  <p className="text-muted-foreground">{user.username}</p>
                </div>

                <p className="text-muted-foreground leading-relaxed max-w-2xl">{user.bio}</p>

                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span>Joined {user.joinDate}</span>
                </div>

                <div className="flex flex-wrap gap-4 pt-2">
                  <div className="text-center">
                    <div className="font-bold text-2xl">{user.stats.booksRead}</div>
                    <div className="text-sm text-muted-foreground">Books Read</div>
                  </div>
                  <Separator orientation="vertical" className="h-12" />
                  <div className="text-center">
                    <div className="font-bold text-2xl">{user.stats.reviews}</div>
                    <div className="text-sm text-muted-foreground">Reviews</div>
                  </div>
                  <Separator orientation="vertical" className="h-12" />
                  <div className="text-center">
                    <div className="font-bold text-2xl">{user.stats.followers}</div>
                    <div className="text-sm text-muted-foreground">Followers</div>
                  </div>
                  <Separator orientation="vertical" className="h-12" />
                  <div className="text-center">
                    <div className="font-bold text-2xl">{user.stats.following}</div>
                    <div className="text-sm text-muted-foreground">Following</div>
                  </div>
                </div>

                <div className="flex gap-3 pt-2">
                  <Button className="rounded-xl">
                    <Settings className="h-4 w-4 mr-2" />
                    Edit Profile
                  </Button>
                  <Button variant="outline" className="rounded-xl bg-transparent">
                    Share Profile
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Reading Stats */}
        <div className="grid md:grid-cols-2 gap-6">
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-primary" />
                Reading Activity
              </CardTitle>
              <CardDescription>Your reading journey this year</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">2024 Reading Goal</span>
                  <span className="font-semibold">24 / 30 books</span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: "80%" }} />
                </div>
              </div>
              <Separator />
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Pages Read</span>
                  <span className="font-semibold">7,842</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Avg. Rating</span>
                  <div className="flex items-center gap-1">
                    <Star className="h-4 w-4 fill-accent text-accent" />
                    <span className="font-semibold">4.3</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Reading Streak</span>
                  <span className="font-semibold">7 days</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/50">
            <CardHeader>
              <CardTitle>Favorite Genres</CardTitle>
              <CardDescription>Your most-read categories</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {favoriteGenres.map((genre) => (
                  <Badge key={genre} variant="secondary" className="px-4 py-2 text-sm rounded-full">
                    {genre}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recently Read */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="font-sans text-2xl font-semibold">Recently Read</h2>
            <Button variant="ghost">View All</Button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-6">
            {recentlyRead.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

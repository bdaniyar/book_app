"use client"

import type React from "react"
import { BookCard } from "@/components/book-card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BookOpen, BookMarked, Clock, Heart } from "lucide-react"
import { trendingBooks, recommendedBooks } from "@/lib/books-data"

export default function LibraryPage() {
  // Mock saved books - in a real app, this would come from a database or state management
  const savedBooks = [trendingBooks[0], trendingBooks[2], recommendedBooks[0], recommendedBooks[1]]
  const currentlyReading = [trendingBooks[1]]
  const wantToRead = [trendingBooks[3], recommendedBooks[2]]
  const favorites = [trendingBooks[0], recommendedBooks[0]]

  return (
    <div className="w-full">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-7xl space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="font-sans text-3xl md:text-4xl font-bold">My Library</h1>
          <p className="text-muted-foreground text-lg">Your personal collection of books</p>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="all" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:inline-grid rounded-xl">
            <TabsTrigger value="all" className="rounded-lg">
              <BookOpen className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">All Books</span>
              <span className="sm:hidden">All</span>
              <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                {savedBooks.length}
              </span>
            </TabsTrigger>
            <TabsTrigger value="reading" className="rounded-lg">
              <BookMarked className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">Reading</span>
              <span className="sm:hidden">Now</span>
              <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                {currentlyReading.length}
              </span>
            </TabsTrigger>
            <TabsTrigger value="want" className="rounded-lg">
              <Clock className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">Want to Read</span>
              <span className="sm:hidden">Later</span>
              <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                {wantToRead.length}
              </span>
            </TabsTrigger>
            <TabsTrigger value="favorites" className="rounded-lg">
              <Heart className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">Favorites</span>
              <span className="sm:hidden">Fav</span>
              <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">{favorites.length}</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-6">
            {savedBooks.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                {savedBooks.map((book) => (
                  <BookCard key={book.id} book={book} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={BookOpen}
                title="No books in your library"
                description="Start adding books to build your personal collection"
              />
            )}
          </TabsContent>

          <TabsContent value="reading" className="space-y-6">
            {currentlyReading.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                {currentlyReading.map((book) => (
                  <BookCard key={book.id} book={book} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={BookMarked}
                title="No books currently reading"
                description="Mark a book as currently reading to track your progress"
              />
            )}
          </TabsContent>

          <TabsContent value="want" className="space-y-6">
            {wantToRead.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                {wantToRead.map((book) => (
                  <BookCard key={book.id} book={book} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={Clock}
                title="No books in your reading list"
                description="Add books you want to read later to keep track of them"
              />
            )}
          </TabsContent>

          <TabsContent value="favorites" className="space-y-6">
            {favorites.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                {favorites.map((book) => (
                  <BookCard key={book.id} book={book} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={Heart}
                title="No favorite books yet"
                description="Mark your favorite books to easily find them later"
              />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

type EmptyStateProps = {
  icon: React.ElementType
  title: string
  description: string
}

function EmptyState({ icon: Icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
      <Icon className="h-16 w-16 text-muted-foreground" />
      <div className="space-y-2">
        <h3 className="font-sans text-xl font-semibold">{title}</h3>
        <p className="text-muted-foreground max-w-md">{description}</p>
      </div>
    </div>
  )
}

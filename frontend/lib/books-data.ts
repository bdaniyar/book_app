export type Book = {
  id: string
  title: string
  author: string
  coverUrl: string | null
  rating: number
  reviewCount: number
  externalRating?: number
  externalReviewCount?: number
  localRating?: number
  localReviewCount?: number
  description: string
  genre: string
  genres: string[]
  publishedYear: number | null
  pages: number | null
  isbn: string | null
  externalSource?: string | null
  externalId?: string | null
  recommendationReason?: string | null
}

export type Category = {
  id: string
  name: string
  slug: string
}

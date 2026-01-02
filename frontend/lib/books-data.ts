export type Book = {
  id: string
  title: string
  author: string
  coverUrl: string
  rating: number
  reviewCount: number
  description: string
  genre: string
  publishedYear: number
  pages: number
  isbn: string
}

export type Category = {
  id: string
  name: string
  slug: string
}

export const categories: Category[] = [
  { id: "1", name: "Fiction", slug: "fiction" },
  { id: "2", name: "Mystery", slug: "mystery" },
  { id: "3", name: "Science Fiction", slug: "sci-fi" },
  { id: "4", name: "Romance", slug: "romance" },
  { id: "5", name: "Biography", slug: "biography" },
  { id: "6", name: "Self-Help", slug: "self-help" },
  { id: "7", name: "History", slug: "history" },
  { id: "8", name: "Fantasy", slug: "fantasy" },
]

export const trendingBooks: Book[] = [
  {
    id: "1",
    title: "The Midnight Library",
    author: "Matt Haig",
    coverUrl: "/midnight-library-cover.png",
    rating: 4.5,
    reviewCount: 12453,
    description:
      "Between life and death there is a library, and within that library, the shelves go on forever. Every book provides a chance to try another life you could have lived.",
    genre: "Fiction",
    publishedYear: 2020,
    pages: 304,
    isbn: "9780525559474",
  },
  {
    id: "2",
    title: "Project Hail Mary",
    author: "Andy Weir",
    coverUrl: "/project-hail-mary-cover.png",
    rating: 4.7,
    reviewCount: 18920,
    description:
      "A lone astronaut must save the earth from disaster in this incredible new science-based thriller from the author of The Martian.",
    genre: "Science Fiction",
    publishedYear: 2021,
    pages: 496,
    isbn: "9780593135204",
  },
  {
    id: "3",
    title: "The Seven Husbands of Evelyn Hugo",
    author: "Taylor Jenkins Reid",
    coverUrl: "/the-seven-husbands-of-evelyn-hugo-book-cover.jpg",
    rating: 4.6,
    reviewCount: 25678,
    description:
      "Aging and reclusive Hollywood movie icon Evelyn Hugo is finally ready to tell the truth about her glamorous and scandalous life.",
    genre: "Fiction",
    publishedYear: 2017,
    pages: 400,
    isbn: "9781501161933",
  },
  {
    id: "4",
    title: "Atomic Habits",
    author: "James Clear",
    coverUrl: "/atomic-habits-inspired-cover.png",
    rating: 4.8,
    reviewCount: 34521,
    description:
      "An easy and proven way to build good habits and break bad ones with tiny changes that deliver remarkable results.",
    genre: "Self-Help",
    publishedYear: 2018,
    pages: 320,
    isbn: "9780735211292",
  },
  {
    id: "5",
    title: "The Silent Patient",
    author: "Alex Michaelides",
    coverUrl: "/the-silent-patient-book-cover.jpg",
    rating: 4.4,
    reviewCount: 19834,
    description:
      "A woman shoots her husband and then never speaks another word. A criminal psychotherapist is determined to uncover the truth.",
    genre: "Mystery",
    publishedYear: 2019,
    pages: 336,
    isbn: "9781250301697",
  },
  {
    id: "6",
    title: "Where the Crawdads Sing",
    author: "Delia Owens",
    coverUrl: "/where-the-crawdads-sing-book-cover.jpg",
    rating: 4.5,
    reviewCount: 28945,
    description:
      'For years, rumors of the "Marsh Girl" have haunted Barkley Cove, a quiet town on the North Carolina coast.',
    genre: "Fiction",
    publishedYear: 2018,
    pages: 384,
    isbn: "9780735219090",
  },
]

export const recommendedBooks: Book[] = [
  {
    id: "7",
    title: "The Song of Achilles",
    author: "Madeline Miller",
    coverUrl: "/the-song-of-achilles-book-cover.jpg",
    rating: 4.6,
    reviewCount: 15234,
    description:
      "A tale of gods, kings, immortal fame and the human heart, The Song of Achilles is a dazzling literary feat.",
    genre: "Fantasy",
    publishedYear: 2011,
    pages: 352,
    isbn: "9780062060624",
  },
  {
    id: "8",
    title: "Educated",
    author: "Tara Westover",
    coverUrl: "/educated-memoir-book-cover.jpg",
    rating: 4.7,
    reviewCount: 22156,
    description:
      "A memoir about a young girl who, kept out of school, leaves her survivalist family and goes on to earn a PhD from Cambridge.",
    genre: "Biography",
    publishedYear: 2018,
    pages: 352,
    isbn: "9780399590504",
  },
  {
    id: "9",
    title: "The Invisible Life of Addie LaRue",
    author: "V.E. Schwab",
    coverUrl: "/the-invisible-life-of-addie-larue-book-cover.jpg",
    rating: 4.3,
    reviewCount: 17892,
    description:
      "A life no one will remember. A story you will never forget. France, 1714: in a moment of desperation, a young woman makes a Faustian bargain.",
    genre: "Fantasy",
    publishedYear: 2020,
    pages: 448,
    isbn: "9780765387561",
  },
  {
    id: "10",
    title: "Circe",
    author: "Madeline Miller",
    coverUrl: "/circe-book-cover.jpg",
    rating: 4.5,
    reviewCount: 19567,
    description:
      "In the house of Helios, god of the sun and mightiest of the Titans, a daughter is born. But Circe is a strange child.",
    genre: "Fantasy",
    publishedYear: 2018,
    pages: 400,
    isbn: "9780316556347",
  },
]

import { API_ENDPOINTS } from "./api-config"
import {
  categories as fallbackCategories,
  recommendedBooks as fallbackRecommendedBooks,
  trendingBooks as fallbackTrendingBooks,
  type Book,
  type Category,
} from "./books-data"

async function getJson<T>(url: string): Promise<T | null> {
  try {
    const response = await fetch(url, {
      headers: { Accept: "application/json" },
      next: { revalidate: 30 },
    })
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getTrendingBooks(limit = 12): Promise<Book[]> {
  const books = await getJson<Book[]>(`${API_ENDPOINTS.BOOKS.TRENDING}?limit=${limit}`)
  return books?.length ? books : fallbackTrendingBooks.slice(0, limit)
}

export async function getRecommendedBooks(limit = 12): Promise<Book[]> {
  const books = await getJson<Book[]>(`${API_ENDPOINTS.BOOKS.RECOMMENDED}?limit=${limit}`)
  return books?.length ? books : fallbackRecommendedBooks.slice(0, limit)
}

export async function getBooks(limit = 40): Promise<Book[]> {
  const books = await getJson<Book[]>(`${API_ENDPOINTS.BOOKS.LIST}?limit=${limit}`)
  return books?.length ? books : [...fallbackTrendingBooks, ...fallbackRecommendedBooks].slice(0, limit)
}

export async function getBook(id: string): Promise<Book | null> {
  return getJson<Book>(API_ENDPOINTS.BOOKS.GET(id))
}

export async function getSimilarBooks(id: string, limit = 4): Promise<Book[]> {
  const books = await getJson<Book[]>(`${API_ENDPOINTS.BOOKS.SIMILAR(id)}?limit=${limit}`)
  return books?.length ? books : fallbackRecommendedBooks.slice(0, limit)
}

export async function getCategories(): Promise<Category[]> {
  const genres = await getJson<Array<{ id: string; name: string }>>(API_ENDPOINTS.CATEGORIES.LIST)
  if (!genres?.length) return fallbackCategories
  return (genres ?? []).map((genre) => ({
    id: genre.id,
    name: genre.name,
    slug: genre.name.toLowerCase().replace(/\s+/g, "-"),
  }))
}

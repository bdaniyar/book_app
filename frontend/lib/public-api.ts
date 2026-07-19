import { API_ENDPOINTS } from "./api-config"
import type { Book, Category } from "./books-data"

export class PublicApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message)
    this.name = "PublicApiError"
  }
}

async function getJson<T>(url: string, allowNotFound = false): Promise<T | null> {
  let response: Response
  try {
    response = await fetch(url, {
      headers: { Accept: "application/json" },
      next: { revalidate: 30 },
    })
  } catch {
    throw new PublicApiError("The book service is currently unavailable.")
  }

  if (allowNotFound && response.status === 404) return null
  if (!response.ok) {
    throw new PublicApiError("The book service returned an error.", response.status)
  }
  return response.json() as Promise<T>
}

export async function getTrendingBooks(limit = 12): Promise<Book[]> {
  return (await getJson<Book[]>(`${API_ENDPOINTS.BOOKS.TRENDING}?limit=${limit}`)) ?? []
}

export async function getRecommendedBooks(limit = 12): Promise<Book[]> {
  return (await getJson<Book[]>(`${API_ENDPOINTS.BOOKS.RECOMMENDED}?limit=${limit}`)) ?? []
}

export async function getBooks(limit = 40): Promise<Book[]> {
  return (await getJson<Book[]>(`${API_ENDPOINTS.BOOKS.LIST}?limit=${limit}`)) ?? []
}

export async function getBook(id: string): Promise<Book | null> {
  return getJson<Book>(API_ENDPOINTS.BOOKS.GET(id), true)
}

export async function getSimilarBooks(id: string, limit = 4): Promise<Book[]> {
  return (await getJson<Book[]>(`${API_ENDPOINTS.BOOKS.SIMILAR(id)}?limit=${limit}`)) ?? []
}

export async function getCategories(): Promise<Category[]> {
  const genres = await getJson<Array<{ id: string; name: string }>>(API_ENDPOINTS.CATEGORIES.LIST)
  return (genres ?? []).map((genre) => ({
    id: genre.id,
    name: genre.name,
    slug: genre.name.toLowerCase().replace(/\s+/g, "-"),
  }))
}

import { apiClient, type QueryValue } from "./api-client"
import { API_ENDPOINTS } from "./api-config"
import type { Book } from "./books-data"

export type Review = {
  id: string
  bookId: string
  userId: string
  userName: string
  userAvatar?: string | null
  rating: number
  text: string
  createdAt: string
  helpful: number
}

export type Genre = {
  id: string
  name: string
  created_at: string
}

export type UserProfile = {
  id: string
  email: string
  username?: string | null
  first_name?: string | null
  last_name?: string | null
  bio?: string | null
  avatar_url?: string | null
  created_at?: string
}

export type ProfileUpdate = {
  username?: string | null
  first_name?: string | null
  last_name?: string | null
  bio?: string | null
  email?: string | null
}

export type ChangePasswordPayload = {
  current_password: string
  new_password: string
  new_password2: string
}

export type ResetPasswordPayload = {
  token: string
  new_password: string
  new_password2: string
}

export type LibraryStatus = "reading" | "want-to-read" | "read" | "dropped"

export type LibraryEntry = {
  id: string
  book: Book
  status: LibraryStatus
  progressPages: number
  isFavorite: boolean
  startedAt: string | null
  finishedAt: string | null
  createdAt: string
  updatedAt: string
}

export type LibraryEntryUpdate = {
  status?: LibraryStatus
  progressPages?: number
  isFavorite?: boolean
}

export type ProfileStats = {
  booksRead: number
  pagesRead: number
  avgRating: number
  reviewsWritten: number
  readingStreak: number
}

export type ReadingActivity = {
  date: string
  action: string
  title: string
}

export type InferredGenre = {
  name: string
  count: number
}

export type AuthTokens = {
  access_token: string
  token_type: string
}

type SearchFilters = Record<string, QueryValue>

export const bookService = {
  getAll: (params?: { page?: number; limit?: number }) =>
    apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.LIST, { params }),

  getById: (id: string) => apiClient.get<Book>(API_ENDPOINTS.BOOKS.GET(id)),

  search: (query: string, filters?: SearchFilters) =>
    apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.SEARCH, { params: { q: query, ...filters } }),

  getTrending: (limit?: number) =>
    apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.TRENDING, {
      params: limit ? { limit } : undefined,
    }),

  getRecommended: (limit?: number) =>
    apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.RECOMMENDED, {
      params: limit ? { limit } : undefined,
    }),

  getByCategory: (category: string, params?: { page?: number; limit?: number }) =>
    apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.BY_CATEGORY(category), { params }),

  getSimilar: (bookId: string, limit?: number) =>
    apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.SIMILAR(bookId), {
      params: limit ? { limit } : undefined,
    }),
}

export const categoryService = {
  getAll: () => apiClient.get<Genre[]>(API_ENDPOINTS.CATEGORIES.LIST),
  getById: (id: string) => apiClient.get<Genre>(API_ENDPOINTS.CATEGORIES.GET(id)),
}

export const libraryService = {
  getAll: () => apiClient.get<LibraryEntry[]>(API_ENDPOINTS.LIBRARY.GET_ALL),
  getReading: () => apiClient.get<LibraryEntry[]>(API_ENDPOINTS.LIBRARY.GET_READING),
  getWantToRead: () => apiClient.get<LibraryEntry[]>(API_ENDPOINTS.LIBRARY.GET_WANT_TO_READ),
  getRead: () => apiClient.get<LibraryEntry[]>(API_ENDPOINTS.LIBRARY.GET_READ),
  getFavorites: () => apiClient.get<LibraryEntry[]>(API_ENDPOINTS.LIBRARY.GET_FAVORITES),

  addBook: (
    bookId: string,
    status?: LibraryStatus,
    options?: Omit<LibraryEntryUpdate, "status">,
  ) => apiClient.post<LibraryEntry>(API_ENDPOINTS.LIBRARY.ADD_BOOK, {
    bookId,
    ...(status ? { status } : {}),
    ...options,
  }),

  removeBook: (bookId: string) => apiClient.delete(API_ENDPOINTS.LIBRARY.REMOVE_BOOK(bookId)),

  updateEntry: (bookId: string, data: LibraryEntryUpdate) =>
    apiClient.patch<LibraryEntry>(API_ENDPOINTS.LIBRARY.UPDATE_STATUS(bookId), data),

  updateStatus: (bookId: string, status: LibraryStatus, progressPages?: number) =>
    apiClient.patch<LibraryEntry>(API_ENDPOINTS.LIBRARY.UPDATE_STATUS(bookId), {
      status,
      ...(progressPages === undefined ? {} : { progressPages }),
    }),

  setFavorite: (bookId: string, isFavorite: boolean) =>
    apiClient.patch<LibraryEntry>(API_ENDPOINTS.LIBRARY.UPDATE_STATUS(bookId), { isFavorite }),
}

export const reviewService = {
  getByBookId: (bookId: string, params?: { page?: number; limit?: number }) =>
    apiClient.get<Review[]>(API_ENDPOINTS.REVIEWS.LIST(bookId), { params }),

  create: (bookId: string, rating: number, text: string) =>
    apiClient.post<Review>(API_ENDPOINTS.REVIEWS.CREATE, { bookId, rating, text }),

  update: (reviewId: string, rating: number, text: string) =>
    apiClient.put<Review>(API_ENDPOINTS.REVIEWS.UPDATE(reviewId), { rating, text }),

  delete: (reviewId: string) => apiClient.delete(API_ENDPOINTS.REVIEWS.DELETE(reviewId)),
}

export const profileService = {
  get: () => apiClient.get<UserProfile>(API_ENDPOINTS.AUTH.ME),
  update: (data: ProfileUpdate) => apiClient.patch<UserProfile>(API_ENDPOINTS.PROFILE.UPDATE, data),
  changePassword: (data: ChangePasswordPayload) =>
    apiClient.put(API_ENDPOINTS.PROFILE.CHANGE_PASSWORD, data),
  getStats: () => apiClient.get<ProfileStats>(API_ENDPOINTS.PROFILE.STATS),
  getReadingActivity: () =>
    apiClient.get<ReadingActivity[]>(API_ENDPOINTS.PROFILE.READING_ACTIVITY),
  getInferredGenres: () =>
    apiClient.get<InferredGenre[]>(API_ENDPOINTS.PROFILE.INFERRED_GENRES),
}

export const recommendationService = {
  getPersonalized: (limit?: number) =>
    apiClient.get<Book[]>(API_ENDPOINTS.RECOMMENDATIONS.PERSONALIZED, {
      params: limit ? { limit } : undefined,
    }),
  getBasedOnBook: (bookId: string, limit?: number) =>
    apiClient.get<Book[]>(API_ENDPOINTS.RECOMMENDATIONS.BASED_ON_BOOK(bookId), {
      params: limit ? { limit } : undefined,
    }),
  getPopularInGenre: (genre: string, limit?: number) =>
    apiClient.get<Book[]>(API_ENDPOINTS.RECOMMENDATIONS.POPULAR_IN_GENRE(genre), {
      params: limit ? { limit } : undefined,
    }),
  getNewReleases: (limit?: number) =>
    apiClient.get<Book[]>(API_ENDPOINTS.RECOMMENDATIONS.NEW_RELEASES, {
      params: limit ? { limit } : undefined,
    }),
}

export const searchService = {
  books: (query: string, filters?: SearchFilters) =>
    apiClient.get<Book[]>(API_ENDPOINTS.SEARCH.BOOKS, { params: { q: query, ...filters } }),
  authors: (query: string) =>
    apiClient.get<unknown[]>(API_ENDPOINTS.SEARCH.AUTHORS, { params: { q: query } }),
  advanced: (filters: SearchFilters) =>
    apiClient.get<Book[]>(API_ENDPOINTS.SEARCH.ADVANCED, { params: filters }),
}

export const authService = {
  login: (email: string, password: string) =>
    apiClient.post<AuthTokens>(API_ENDPOINTS.AUTH.LOGIN, { email, password }),
  register: (email: string, password: string, username: string) =>
    apiClient.post<AuthTokens>(API_ENDPOINTS.AUTH.REGISTER, { email, password, username }),
  refresh: () => apiClient.post<AuthTokens>(API_ENDPOINTS.AUTH.REFRESH),
  logout: () => apiClient.post(API_ENDPOINTS.AUTH.LOGOUT),
  forgotPassword: (email: string) =>
    apiClient.post(API_ENDPOINTS.AUTH.FORGOT_PASSWORD, { email }),
  resetPassword: (data: ResetPasswordPayload) =>
    apiClient.post(API_ENDPOINTS.AUTH.RESET_PASSWORD, data),
  me: () => apiClient.get<UserProfile>(API_ENDPOINTS.AUTH.ME),
}

/**
 * API Services
 * High-level service functions for interacting with the API
 */

import { apiClient } from './api-client'
import { API_ENDPOINTS } from './api-config'
import type { Book, Category } from './books-data'

/**
 * Review type
 */
export type Review = {
    id: string
    bookId: string
    userId: string
    userName: string
    userAvatar?: string
    rating: number
    text: string
    createdAt: string
    helpful: number
}

/**
 * User Profile type
 */
export type UserProfile = {
    id: string
    name: string
    email: string
    avatar?: string
    bio?: string
    joinedAt: string
    stats: {
        booksRead: number
        pagesRead: number
        avgRating: number
        reviewsWritten: number
        readingStreak: number
    }
}

/**
 * Library Status type
 */
export type LibraryStatus = 'reading' | 'want-to-read' | 'read' | 'favorite'

/**
 * Auth Tokens type
 */
export type AuthTokens = {
    access_token: string
    refresh_token: string
    token_type: string
}

/**
 * Book Services
 */
export const bookService = {
    /**
     * Get all books with optional pagination
     */
    getAll: async (params?: { page?: number; limit?: number }) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.LIST, { params })
    },

    /**
     * Get a single book by ID
     */
    getById: async (id: string) => {
        return apiClient.get<Book>(API_ENDPOINTS.BOOKS.GET(id))
    },

    /**
     * Search books
     */
    search: async (query: string, filters?: Record<string, any>) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.SEARCH, {
            params: { q: query, ...filters },
        })
    },

    /**
     * Get trending books
     */
    getTrending: async (limit?: number) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.TRENDING, {
            params: limit ? { limit } : undefined,
        })
    },

    /**
     * Get recommended books
     */
    getRecommended: async (limit?: number) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.RECOMMENDED, {
            params: limit ? { limit } : undefined,
        })
    },

    /**
     * Get books by category
     */
    getByCategory: async (category: string, params?: { page?: number; limit?: number }) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.BY_CATEGORY(category), { params })
    },

    /**
     * Get similar books
     */
    getSimilar: async (bookId: string, limit?: number) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.BOOKS.SIMILAR(bookId), {
            params: limit ? { limit } : undefined,
        })
    },
}

/**
 * Category Services
 */
export const categoryService = {
    /**
     * Get all categories
     */
    getAll: async () => {
        return apiClient.get<Category[]>(API_ENDPOINTS.CATEGORIES.LIST)
    },

    /**
     * Get category by ID
     */
    getById: async (id: string) => {
        return apiClient.get<Category>(API_ENDPOINTS.CATEGORIES.GET(id))
    },
}

/**
 * Library Services
 */
export const libraryService = {
    /**
     * Get all books in library
     */
    getAll: async () => {
        return apiClient.get<Book[]>(API_ENDPOINTS.LIBRARY.GET_ALL)
    },

    /**
     * Get currently reading books
     */
    getReading: async () => {
        return apiClient.get<Book[]>(API_ENDPOINTS.LIBRARY.GET_READING)
    },

    /**
     * Get want to read books
     */
    getWantToRead: async () => {
        return apiClient.get<Book[]>(API_ENDPOINTS.LIBRARY.GET_WANT_TO_READ)
    },

    /**
     * Get favorite books
     */
    getFavorites: async () => {
        return apiClient.get<Book[]>(API_ENDPOINTS.LIBRARY.GET_FAVORITES)
    },

    /**
     * Add book to library
     */
    addBook: async (bookId: string, status: LibraryStatus) => {
        return apiClient.post(API_ENDPOINTS.LIBRARY.ADD_BOOK, { bookId, status })
    },

    /**
     * Remove book from library
     */
    removeBook: async (bookId: string) => {
        return apiClient.delete(API_ENDPOINTS.LIBRARY.REMOVE_BOOK(bookId))
    },

    /**
     * Update book status in library
     */
    updateStatus: async (bookId: string, status: LibraryStatus) => {
        return apiClient.patch(API_ENDPOINTS.LIBRARY.UPDATE_STATUS(bookId), { status })
    },
}

/**
 * Review Services
 */
export const reviewService = {
    /**
     * Get reviews for a book
     */
    getByBookId: async (bookId: string, params?: { page?: number; limit?: number }) => {
        return apiClient.get<Review[]>(API_ENDPOINTS.REVIEWS.LIST(bookId), { params })
    },

    /**
     * Create a review
     */
    create: async (bookId: string, rating: number, text: string) => {
        return apiClient.post<Review>(API_ENDPOINTS.REVIEWS.CREATE, {
            bookId,
            rating,
            text,
        })
    },

    /**
     * Update a review
     */
    update: async (reviewId: string, rating: number, text: string) => {
        return apiClient.put<Review>(API_ENDPOINTS.REVIEWS.UPDATE(reviewId), {
            rating,
            text,
        })
    },

    /**
     * Delete a review
     */
    delete: async (reviewId: string) => {
        return apiClient.delete(API_ENDPOINTS.REVIEWS.DELETE(reviewId))
    },
}

/**
 * Profile Services
 */
export const profileService = {
    /**
     * Get user profile
     */
    get: async () => {
        return apiClient.get<UserProfile>(API_ENDPOINTS.PROFILE.GET)
    },

    /**
     * Update user profile
     */
    update: async (data: Partial<UserProfile>) => {
        return apiClient.put<UserProfile>(API_ENDPOINTS.PROFILE.UPDATE, data)
    },

    /**
     * Get user stats
     */
    getStats: async () => {
        return apiClient.get(API_ENDPOINTS.PROFILE.STATS)
    },

    /**
     * Get reading activity
     */
    getReadingActivity: async () => {
        return apiClient.get(API_ENDPOINTS.PROFILE.READING_ACTIVITY)
    },
}

/**
 * Recommendation Services
 */
export const recommendationService = {
    /**
     * Get personalized recommendations
     */
    getPersonalized: async (limit?: number) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.RECOMMENDATIONS.PERSONALIZED, {
            params: limit ? { limit } : undefined,
        })
    },

    /**
     * Get recommendations based on a book
     */
    getBasedOnBook: async (bookId: string, limit?: number) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.RECOMMENDATIONS.BASED_ON_BOOK(bookId), {
            params: limit ? { limit } : undefined,
        })
    },

    /**
     * Get popular books in a genre
     */
    getPopularInGenre: async (genre: string, limit?: number) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.RECOMMENDATIONS.POPULAR_IN_GENRE(genre), {
            params: limit ? { limit } : undefined,
        })
    },

    /**
     * Get new releases
     */
    getNewReleases: async (limit?: number) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.RECOMMENDATIONS.NEW_RELEASES, {
            params: limit ? { limit } : undefined,
        })
    },
}

/**
 * Search Services
 */
export const searchService = {
    /**
     * Search books
     */
    books: async (query: string, filters?: Record<string, any>) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.SEARCH.BOOKS, {
            params: { q: query, ...filters },
        })
    },

    /**
     * Search authors
     */
    authors: async (query: string) => {
        return apiClient.get(API_ENDPOINTS.SEARCH.AUTHORS, {
            params: { q: query },
        })
    },

    /**
     * Advanced search
     */
    advanced: async (filters: Record<string, any>) => {
        return apiClient.get<Book[]>(API_ENDPOINTS.SEARCH.ADVANCED, { params: filters })
    },
}

/**
 * Authentication Services (для будущего)
 */
export const authService = {
    /**
     * Login
     */
    login: async (email: string, password: string) => {
        return apiClient.post<AuthTokens>(API_ENDPOINTS.AUTH.LOGIN, { email, password })
    },

    /**
     * Register
     */
    register: async (email: string, password: string, name: string) => {
        return apiClient.post<AuthTokens>(API_ENDPOINTS.AUTH.REGISTER, { email, password, name })
    },

    /**
     * Logout
     */
    logout: async () => {
        return apiClient.post(API_ENDPOINTS.AUTH.LOGOUT)
    },

    /**
     * Get current user
     */
    me: async () => {
        return apiClient.get(API_ENDPOINTS.AUTH.ME)
    },
}

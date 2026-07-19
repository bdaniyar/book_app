/**
 * API Configuration
 * Central configuration for all API endpoints
 */

// API Base URL - change this to your backend URL
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// API Version
export const API_VERSION = 'v1'

// Full API URL
export const API_URL = `${API_BASE_URL}/api/${API_VERSION}`

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
    // Books
    BOOKS: {
        LIST: `${API_URL}/books`,
        GET: (id: string) => `${API_URL}/books/${id}`,
        SEARCH: `${API_URL}/books/search`,
        TRENDING: `${API_URL}/books/trending`,
        RECOMMENDED: `${API_URL}/books/recommended`,
        BY_CATEGORY: (category: string) => `${API_URL}/books/category/${category}`,
        SIMILAR: (id: string) => `${API_URL}/books/${id}/similar`,
    },

    // Categories
    CATEGORIES: {
        LIST: `${API_URL}/genres`,
        GET: (id: string) => `${API_URL}/genres/${id}`,
    },

    // User Library
    LIBRARY: {
        GET_ALL: `${API_URL}/library`,
        GET_READING: `${API_URL}/library/reading`,
        GET_WANT_TO_READ: `${API_URL}/library/want-to-read`,
        GET_READ: `${API_URL}/library/read`,
        GET_FAVORITES: `${API_URL}/library/favorites`,
        ADD_BOOK: `${API_URL}/library/add`,
        REMOVE_BOOK: (id: string) => `${API_URL}/library/remove/${id}`,
        UPDATE_STATUS: (id: string) => `${API_URL}/library/update/${id}`,
    },

    // Reviews
    REVIEWS: {
        LIST: (bookId: string) => `${API_URL}/reviews/book/${bookId}`,
        CREATE: `${API_URL}/reviews`,
        UPDATE: (id: string) => `${API_URL}/reviews/${id}`,
        DELETE: (id: string) => `${API_URL}/reviews/${id}`,
    },

    // User Profile
    PROFILE: {
        GET: `${API_URL}/profile`,
        UPDATE: `${API_URL}/profile`,
        CHANGE_PASSWORD: `${API_URL}/profile/password`,
        STATS: `${API_URL}/profile/stats`,
        READING_ACTIVITY: `${API_URL}/profile/reading-activity`,
        INFERRED_GENRES: `${API_URL}/profile/inferred-genres`,
    },

    // Recommendations
    RECOMMENDATIONS: {
        PERSONALIZED: `${API_URL}/recommendations/personalized`,
        BASED_ON_BOOK: (id: string) => `${API_URL}/recommendations/book/${id}`,
        POPULAR_IN_GENRE: (genre: string) => `${API_URL}/recommendations/genre/${genre}`,
        NEW_RELEASES: `${API_URL}/recommendations/new-releases`,
    },

    // AI Librarian
    ASSISTANT: {
        STATUS: `${API_URL}/assistant/status`,
        CONVERSATIONS: `${API_URL}/assistant/conversations`,
        CONVERSATION: (id: string) => `${API_URL}/assistant/conversations/${id}`,
        MESSAGES: (id: string) => `${API_URL}/assistant/conversations/${id}/messages`,
        CONFIRM_ACTION: (id: string) => `${API_URL}/assistant/actions/${id}/confirm`,
        REJECT_ACTION: (id: string) => `${API_URL}/assistant/actions/${id}/reject`,
    },

    // Search
    SEARCH: {
        BOOKS: `${API_URL}/search/books`,
        AUTHORS: `${API_URL}/search/authors`,
        ADVANCED: `${API_URL}/search/advanced`,
    },

    // Authentication (для будущего)
    AUTH: {
        LOGIN: `${API_URL}/auth/login`,
        REGISTER: `${API_URL}/auth/register`,
        LOGOUT: `${API_URL}/auth/logout`,
        REFRESH: `${API_URL}/auth/refresh`,
        ME: `${API_URL}/auth/me`,
        FORGOT_PASSWORD: `${API_URL}/auth/forgot-password`,
        RESET_PASSWORD: `${API_URL}/auth/reset-password`,
    },
} as const

/**
 * API Request Configuration
 */
export const API_CONFIG = {
    // Request timeout in milliseconds
    TIMEOUT: 30000,

    // Default headers
    HEADERS: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },

    // Retry configuration
    RETRY: {
        MAX_RETRIES: 3,
        RETRY_DELAY: 1000, // ms
    },
} as const

/**
 * HTTP Methods
 */
export const HTTP_METHODS = {
    GET: 'GET',
    POST: 'POST',
    PUT: 'PUT',
    PATCH: 'PATCH',
    DELETE: 'DELETE',
} as const

export type HttpMethod = typeof HTTP_METHODS[keyof typeof HTTP_METHODS]

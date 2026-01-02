/**
 * API Types
 * Shared types for API communication
 */

/**
 * API Response type
 */
export type ApiResponse<T = any> = {
    data?: T
    error?: string
    message?: string
    status: number
    success: boolean
}

/**
 * API Error class
 */
export class ApiError extends Error {
    constructor(
        public status: number,
        public message: string,
        public data?: any
    ) {
        super(message)
        this.name = 'ApiError'
    }
}

/**
 * HTTP Methods
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

/**
 * Request options
 */
export type RequestOptions = {
    method?: HttpMethod
    headers?: HeadersInit
    body?: any
    params?: Record<string, string | number | boolean>
    signal?: AbortSignal
}

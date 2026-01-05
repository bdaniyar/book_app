/**
 * API Client
 * Centralized API client for making requests to the backend
 */

import { API_CONFIG } from './api-config'
import { getAccessToken } from './auth-storage'

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
 * HTTP Method type
 */
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

/**
 * Request options
 */
type RequestOptions = {
    method?: HttpMethod
    headers?: HeadersInit
    body?: any
    params?: Record<string, string | number | boolean>
    signal?: AbortSignal
}

/**
 * Build URL with query parameters
 */
function buildUrl(url: string, params?: Record<string, string | number | boolean>): string {
    if (!params) return url

    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
        searchParams.append(key, String(value))
    })

    const queryString = searchParams.toString()
    return queryString ? `${url}?${queryString}` : url
}

/**
 * Make API request
 */
async function request<T = any>(
    url: string,
    options: RequestOptions = {}
): Promise<ApiResponse<T>> {
    const {
        method = 'GET',
        headers = {},
        body,
        params,
        signal,
    } = options

    try {
        const fullUrl = buildUrl(url, params)

        const token = getAccessToken()

        const response = await fetch(fullUrl, {
            method,
            headers: {
                ...API_CONFIG.HEADERS,
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
                ...headers,
            },
            body: body ? JSON.stringify(body) : undefined,
            signal,
        })

        const data = await response.json()

        if (!response.ok) {
            throw new ApiError(
                response.status,
                data.message || data.error || 'Request failed',
                data
            )
        }

        return {
            data,
            status: response.status,
            success: true,
        }
    } catch (error) {
        if (error instanceof ApiError) {
            return {
                error: error.message,
                status: error.status,
                success: false,
            }
        }

        if (error instanceof Error) {
            return {
                error: error.message,
                status: 500,
                success: false,
            }
        }

        return {
            error: 'Unknown error occurred',
            status: 500,
            success: false,
        }
    }
}

/**
 * API Client methods
 */
export const apiClient = {
    /**
     * GET request
     */
    get: <T = any>(url: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
        request<T>(url, { ...options, method: 'GET' }),

    /**
     * POST request
     */
    post: <T = any>(url: string, body?: any, options?: Omit<RequestOptions, 'method'>) =>
        request<T>(url, { ...options, body, method: 'POST' }),

    /**
     * PUT request
     */
    put: <T = any>(url: string, body?: any, options?: Omit<RequestOptions, 'method'>) =>
        request<T>(url, { ...options, body, method: 'PUT' }),

    /**
     * PATCH request
     */
    patch: <T = any>(url: string, body?: any, options?: Omit<RequestOptions, 'method'>) =>
        request<T>(url, { ...options, body, method: 'PATCH' }),

    /**
     * DELETE request
     */
    delete: <T = any>(url: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
        request<T>(url, { ...options, method: 'DELETE' }),
}

/**
 * Export default client
 */
export default apiClient

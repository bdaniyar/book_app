/**
 * API Client
 * Centralized API client for making requests to the backend
 */

import { API_CONFIG, API_ENDPOINTS } from './api-config'
import { getAccessToken, setAccessToken, clearAccessToken } from './auth-storage'

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

    const doFetch = async (): Promise<Response> => {
        const fullUrl = buildUrl(url, params)
        const token = getAccessToken()

        return fetch(fullUrl, {
            method,
            credentials: 'include',
            headers: {
                ...API_CONFIG.HEADERS,
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
                ...headers,
            },
            body: body ? JSON.stringify(body) : undefined,
            signal,
        })
    }

    try {
        let response = await doFetch()

        // If access token expired, try refresh once (refresh cookie is HttpOnly)
        if ((response.status === 401 || response.status === 403) && url !== API_ENDPOINTS.AUTH.REFRESH) {
            const refreshResp = await fetch(API_ENDPOINTS.AUTH.REFRESH, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    ...API_CONFIG.HEADERS,
                },
            })

            if (refreshResp.ok) {
                const refreshData = await refreshResp.json()
                const newAccess = refreshData?.access_token
                if (newAccess) {
                    setAccessToken(newAccess)
                    response = await doFetch()
                }
            } else {
                clearAccessToken()
            }
        }

        // 204 No Content (or empty response body) should not be parsed as JSON
        if (response.status === 204) {
            return {
                data: undefined,
                status: response.status,
                success: true,
            }
        }

        const contentType = response.headers.get('content-type') || ''
        const hasJson = contentType.includes('application/json')

        const data = hasJson ? await response.json().catch(() => undefined) : undefined

        if (!response.ok) {
            const detail = (data as any)?.detail
            const message =
                (typeof detail === 'string' ? detail : undefined) ||
                (Array.isArray(detail) ? detail.map((item) => item.msg || item.message).filter(Boolean).join(', ') : undefined) ||
                (data as any)?.message ||
                (data as any)?.error ||
                'Request failed'
            throw new ApiError(response.status, message, data)
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

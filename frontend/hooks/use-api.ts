/**
 * React Hooks for API calls
 * Custom hooks for interacting with the API
 */

'use client'

import { useState, useEffect, useCallback } from 'react'
import type { ApiResponse } from '@/lib/api-client'

/**
 * Hook state type
 */
type UseApiState<T> = {
    data: T | null
    loading: boolean
    error: string | null
    refetch: () => Promise<void>
}

/**
 * Generic hook for API calls
 */
export function useApi<T>(
    apiCall: () => Promise<ApiResponse<T>>,
    dependencies: any[] = [],
    options?: {
        enabled?: boolean
        onSuccess?: (data: T) => void
        onError?: (error: string) => void
    }
): UseApiState<T> {
    const [data, setData] = useState<T | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const { enabled = true, onSuccess, onError } = options || {}

    const fetchData = useCallback(async () => {
        if (!enabled) return

        setLoading(true)
        setError(null)

        try {
            const response = await apiCall()

            if (response.success && response.data) {
                setData(response.data)
                onSuccess?.(response.data)
            } else {
                const errorMsg = response.error || 'Failed to fetch data'
                setError(errorMsg)
                onError?.(errorMsg)
            }
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'An error occurred'
            setError(errorMsg)
            onError?.(errorMsg)
        } finally {
            setLoading(false)
        }
    }, [apiCall, enabled, onSuccess, onError, ...dependencies])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    return { data, loading, error, refetch: fetchData }
}

/**
 * Hook for mutations (POST, PUT, DELETE)
 */
export function useMutation<TData, TVariables = void>(
    mutationFn: (variables: TVariables) => Promise<ApiResponse<TData>>,
    options?: {
        onSuccess?: (data: TData) => void
        onError?: (error: string) => void
    }
) {
    const [data, setData] = useState<TData | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const mutate = useCallback(
        async (variables: TVariables) => {
            setLoading(true)
            setError(null)

            try {
                const response = await mutationFn(variables)

                if (response.success && response.data) {
                    setData(response.data)
                    options?.onSuccess?.(response.data)
                    return response.data
                } else {
                    const errorMsg = response.error || 'Mutation failed'
                    setError(errorMsg)
                    options?.onError?.(errorMsg)
                    throw new Error(errorMsg)
                }
            } catch (err) {
                const errorMsg = err instanceof Error ? err.message : 'An error occurred'
                setError(errorMsg)
                options?.onError?.(errorMsg)
                throw err
            } finally {
                setLoading(false)
            }
        },
        [mutationFn, options]
    )

    const reset = useCallback(() => {
        setData(null)
        setError(null)
        setLoading(false)
    }, [])

    return { mutate, data, loading, error, reset }
}

/**
 * Hook for paginated data
 */
export function usePagination<T>(
    apiCall: (page: number, limit: number) => Promise<ApiResponse<T[]>>,
    initialPage = 1,
    initialLimit = 20
) {
    const [data, setData] = useState<T[]>([])
    const [page, setPage] = useState(initialPage)
    const [limit, setLimit] = useState(initialLimit)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [hasMore, setHasMore] = useState(true)

    const fetchData = useCallback(async () => {
        setLoading(true)
        setError(null)

        try {
            const response = await apiCall(page, limit)

            if (response.success && response.data) {
                setData(response.data)
                setHasMore(response.data.length === limit)
            } else {
                setError(response.error || 'Failed to fetch data')
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setLoading(false)
        }
    }, [apiCall, page, limit])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    const nextPage = () => setPage((p) => p + 1)
    const prevPage = () => setPage((p) => Math.max(1, p - 1))
    const goToPage = (newPage: number) => setPage(Math.max(1, newPage))
    const changeLimit = (newLimit: number) => {
        setLimit(newLimit)
        setPage(1)
    }

    return {
        data,
        loading,
        error,
        page,
        limit,
        hasMore,
        nextPage,
        prevPage,
        goToPage,
        changeLimit,
        refetch: fetchData,
    }
}

/**
 * Hook for infinite scroll
 */
export function useInfiniteScroll<T>(
    apiCall: (page: number, limit: number) => Promise<ApiResponse<T[]>>,
    limit = 20
) {
    const [data, setData] = useState<T[]>([])
    const [page, setPage] = useState(1)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [hasMore, setHasMore] = useState(true)

    const fetchMore = useCallback(async () => {
        if (loading || !hasMore) return

        setLoading(true)
        setError(null)

        try {
            const response = await apiCall(page, limit)

            if (response.success && response.data) {
                setData((prev) => [...prev, ...response.data!])
                setHasMore(response.data.length === limit)
                setPage((p) => p + 1)
            } else {
                setError(response.error || 'Failed to fetch data')
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setLoading(false)
        }
    }, [apiCall, page, limit, loading, hasMore])

    const reset = useCallback(() => {
        setData([])
        setPage(1)
        setHasMore(true)
        setError(null)
    }, [])

    return { data, loading, error, hasMore, fetchMore, reset }
}

/** A small JSON API client with cookie-based refresh-token rotation. */

import { API_CONFIG, API_ENDPOINTS } from "./api-config"
import { clearAccessToken, getAccessToken, setAccessToken } from "./auth-storage"

export type ApiResponse<T = unknown> = {
  data?: T
  error?: string
  message?: string
  status: number
  success: boolean
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE"
export type QueryValue = string | number | boolean | null | undefined

export type RequestOptions = {
  method?: HttpMethod
  headers?: HeadersInit
  body?: unknown
  params?: Record<string, QueryValue>
  signal?: AbortSignal
  timeoutMs?: number
}

function buildUrl(url: string, params?: Record<string, QueryValue>): string {
  if (!params) return url

  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      searchParams.append(key, String(value))
    }
  })

  const queryString = searchParams.toString()
  return queryString ? `${url}?${queryString}` : url
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}

function errorMessage(data: unknown): string {
  if (!isRecord(data)) return "Request failed"

  const detail = data.detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!isRecord(item)) return null
        return typeof item.msg === "string"
          ? item.msg
          : typeof item.message === "string"
            ? item.message
            : null
      })
      .filter((item): item is string => Boolean(item))
    if (messages.length) return messages.join(", ")
  }
  if (typeof data.message === "string") return data.message
  if (typeof data.error === "string") return data.error
  return "Request failed"
}

async function readJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? ""
  if (!contentType.includes("application/json")) return undefined
  return response.json().catch(() => undefined)
}

let refreshInFlight: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight

  refreshInFlight = (async () => {
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort("timeout"), API_CONFIG.TIMEOUT)

    try {
      const response = await fetch(API_ENDPOINTS.AUTH.REFRESH, {
        method: "POST",
        credentials: "include",
        headers: API_CONFIG.HEADERS,
        signal: controller.signal,
      })
      if (!response.ok) {
        clearAccessToken()
        return null
      }

      const data = await readJson(response)
      const accessToken = isRecord(data) && typeof data.access_token === "string" ? data.access_token : null
      if (accessToken) setAccessToken(accessToken)
      return accessToken
    } catch {
      return null
    } finally {
      window.clearTimeout(timeout)
      refreshInFlight = null
    }
  })()

  return refreshInFlight
}

async function request<T = unknown>(url: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
  const {
    method = "GET",
    headers = {},
    body,
    params,
    signal: externalSignal,
    timeoutMs = API_CONFIG.TIMEOUT,
  } = options

  const controller = new AbortController()
  let timedOut = false
  const timeout = window.setTimeout(() => {
    timedOut = true
    controller.abort("timeout")
  }, timeoutMs)
  const abortFromCaller = () => controller.abort(externalSignal?.reason)
  if (externalSignal?.aborted) abortFromCaller()
  externalSignal?.addEventListener("abort", abortFromCaller, { once: true })

  const doFetch = () => {
    const token = getAccessToken()
    return fetch(buildUrl(url, params), {
      method,
      credentials: "include",
      headers: {
        ...API_CONFIG.HEADERS,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    })
  }

  try {
    let response = await doFetch()

    // A 403 is an authorization decision, not an expired session.
    if (response.status === 401 && url !== API_ENDPOINTS.AUTH.REFRESH) {
      const refreshedToken = await refreshAccessToken()
      if (refreshedToken) response = await doFetch()
    }

    if (response.status === 204) {
      return { status: response.status, success: true }
    }

    const data = await readJson(response)
    if (!response.ok) throw new ApiError(response.status, errorMessage(data), data)

    return { data: data as T, status: response.status, success: true }
  } catch (error) {
    if (error instanceof ApiError) {
      return { error: error.message, status: error.status, success: false }
    }
    if (timedOut) {
      return { error: "The request timed out. Please try again.", status: 408, success: false }
    }
    if (externalSignal?.aborted) {
      return { error: "The request was cancelled.", status: 0, success: false }
    }
    return {
      error: typeof navigator !== "undefined" && !navigator.onLine
        ? "You appear to be offline. Check your connection."
        : "Unable to reach the server. Please try again.",
      status: 0,
      success: false,
    }
  } finally {
    window.clearTimeout(timeout)
    externalSignal?.removeEventListener("abort", abortFromCaller)
  }
}

export const apiClient = {
  get: <T = unknown>(url: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(url, { ...options, method: "GET" }),
  post: <T = unknown>(url: string, body?: unknown, options?: Omit<RequestOptions, "method">) =>
    request<T>(url, { ...options, body, method: "POST" }),
  put: <T = unknown>(url: string, body?: unknown, options?: Omit<RequestOptions, "method">) =>
    request<T>(url, { ...options, body, method: "PUT" }),
  patch: <T = unknown>(url: string, body?: unknown, options?: Omit<RequestOptions, "method">) =>
    request<T>(url, { ...options, body, method: "PATCH" }),
  delete: <T = unknown>(url: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(url, { ...options, method: "DELETE" }),
}

export default apiClient

import { apiClient } from "./api-client"
import { API_ENDPOINTS } from "./api-config"
import type { Book } from "./books-data"

export type AssistantStatus = {
  provider: string
  model: string
  configured: boolean
}

export type AssistantConversation = {
  id: string
  title: string
  createdAt: string
  updatedAt: string
}

export type AssistantRole = "user" | "assistant"

export type AssistantMessage = {
  id: string
  role: AssistantRole
  content: string
  bookIds: string[]
  createdAt: string
  books?: Book[]
  citations?: AssistantCitation[]
  proposedActions?: AssistantAction[]
}

export type AssistantCitation = {
  bookId: string
  fields: string[]
}

export type AssistantActionStatus = "pending" | "executed" | "rejected" | "expired"

export type AssistantAction = {
  id: string
  type: string
  payload: Record<string, unknown>
  status: AssistantActionStatus
  expiresAt: string
}

export type AssistantReply = {
  conversationId: string
  message: AssistantMessage
  books: Book[]
  citations: AssistantCitation[]
  proposedActions: AssistantAction[]
}

export type AssistantActionResult = {
  id: string
  status: Exclude<AssistantActionStatus, "pending">
  result: Record<string, unknown> | null
}

export const assistantService = {
  getStatus: () => apiClient.get<AssistantStatus>(API_ENDPOINTS.ASSISTANT.STATUS),
  listConversations: () =>
    apiClient.get<AssistantConversation[]>(API_ENDPOINTS.ASSISTANT.CONVERSATIONS),
  createConversation: (title?: string) =>
    apiClient.post<AssistantConversation>(API_ENDPOINTS.ASSISTANT.CONVERSATIONS, { title: title || null }),
  getMessages: (conversationId: string) =>
    apiClient.get<AssistantMessage[]>(API_ENDPOINTS.ASSISTANT.MESSAGES(conversationId)),
  sendMessage: (conversationId: string, message: string, bookId?: string) =>
    apiClient.post<AssistantReply>(API_ENDPOINTS.ASSISTANT.MESSAGES(conversationId), {
      message,
      ...(bookId ? { bookId } : {}),
    }),
  confirmAction: (actionId: string) =>
    apiClient.post<AssistantActionResult>(API_ENDPOINTS.ASSISTANT.CONFIRM_ACTION(actionId)),
  rejectAction: (actionId: string) =>
    apiClient.post<AssistantActionResult>(API_ENDPOINTS.ASSISTANT.REJECT_ACTION(actionId)),
}

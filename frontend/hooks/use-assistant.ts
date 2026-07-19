"use client"

import { useCallback, useEffect, useRef, useState } from "react"

import {
  assistantService,
  type AssistantActionResult,
  type AssistantConversation,
  type AssistantMessage,
  type AssistantStatus,
} from "@/lib/assistant-api"

function temporaryMessage(content: string): AssistantMessage {
  return {
    id: `pending-${crypto.randomUUID()}`,
    role: "user",
    content,
    bookIds: [],
    createdAt: new Date().toISOString(),
  }
}

export function useAssistant(bookId?: string) {
  const [status, setStatus] = useState<AssistantStatus | null>(null)
  const [conversations, setConversations] = useState<AssistantConversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<AssistantMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [actionInFlight, setActionInFlight] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const selectionVersion = useRef(0)

  const loadConversations = useCallback(async () => {
    setLoading(true)
    setError(null)
    const [statusResponse, conversationsResponse] = await Promise.all([
      assistantService.getStatus(),
      assistantService.listConversations(),
    ])
    if (statusResponse.success && statusResponse.data) setStatus(statusResponse.data)
    if (conversationsResponse.success) {
      setConversations(conversationsResponse.data ?? [])
    } else {
      setError(conversationsResponse.status === 401
        ? "Sign in to use AI Librarian."
        : conversationsResponse.error || "Could not load AI Librarian.")
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    void loadConversations()
  }, [loadConversations])

  const selectConversation = useCallback(async (conversationId: string) => {
    const version = ++selectionVersion.current
    setActiveConversationId(conversationId)
    setMessages([])
    setLoading(true)
    setError(null)
    const response = await assistantService.getMessages(conversationId)
    if (selectionVersion.current !== version) return
    if (response.success) {
      setMessages(response.data ?? [])
    } else {
      setError(response.error || "Could not load this conversation.")
    }
    setLoading(false)
  }, [])

  const startConversation = useCallback(() => {
    selectionVersion.current += 1
    setActiveConversationId(null)
    setMessages([])
    setError(null)
  }, [])

  const sendMessage = useCallback(async (rawMessage: string) => {
    const content = rawMessage.trim()
    if (!content || sending) return false

    setSending(true)
    setError(null)
    const requestVersion = selectionVersion.current
    const optimistic = temporaryMessage(content)
    setMessages((current) => [...current, optimistic])

    let conversationId = activeConversationId
    if (!conversationId) {
      const title = content.length > 54 ? `${content.slice(0, 51)}…` : content
      const created = await assistantService.createConversation(title)
      if (!created.success || !created.data) {
        if (selectionVersion.current === requestVersion) {
          setMessages((current) => current.filter((message) => message.id !== optimistic.id))
          setError(created.error || "Could not start a conversation.")
        }
        setSending(false)
        return false
      }
      const newConversation = created.data
      conversationId = newConversation.id
      setConversations((current) => [newConversation, ...current])
      if (selectionVersion.current === requestVersion) {
        setActiveConversationId(conversationId)
      }
    }

    const response = await assistantService.sendMessage(conversationId, content, bookId)
    if (!response.success || !response.data) {
      if (selectionVersion.current === requestVersion) {
        setMessages((current) => current.filter((message) => message.id !== optimistic.id))
        setError(response.error || "AI Librarian could not answer.")
      }
      setSending(false)
      return false
    }

    const reply = response.data
    if (selectionVersion.current === requestVersion) {
      setMessages((current) => [
        ...current,
        {
          ...reply.message,
          books: reply.books,
          citations: reply.citations,
          proposedActions: reply.proposedActions,
        },
      ])
    }
    setConversations((current) => current.map((conversation) =>
      conversation.id === reply.conversationId
        ? { ...conversation, updatedAt: new Date().toISOString() }
        : conversation,
    ))
    setSending(false)
    return true
  }, [activeConversationId, bookId, sending])

  const resolveAction = useCallback(async (actionId: string, decision: "confirm" | "reject") => {
    setActionInFlight(actionId)
    setError(null)
    const response = decision === "confirm"
      ? await assistantService.confirmAction(actionId)
      : await assistantService.rejectAction(actionId)
    setActionInFlight(null)

    if (!response.success || !response.data) {
      setError(response.error || `Could not ${decision} this action.`)
      return null
    }

    const result: AssistantActionResult = response.data
    setMessages((current) => current.map((message) => ({
      ...message,
      proposedActions: message.proposedActions?.map((action) =>
        action.id === actionId
          ? { ...action, status: result.status }
          : action,
      ),
    })))
    return result
  }, [])

  return {
    status,
    conversations,
    activeConversationId,
    messages,
    loading,
    sending,
    actionInFlight,
    error,
    loadConversations,
    selectConversation,
    startConversation,
    sendMessage,
    resolveAction,
  }
}

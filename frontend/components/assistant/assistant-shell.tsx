"use client"

import Link from "next/link"
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react"
import { Bot, CheckCircle2, CircleAlert, Loader2, MessageSquarePlus, Send, Sparkles } from "lucide-react"

import { ChatMessage } from "@/components/assistant/chat-message"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useAssistant } from "@/hooks/use-assistant"
import { cn } from "@/lib/utils"

const suggestions = [
  "Recommend a thoughtful book under 350 pages",
  "What should I read after my latest finished book?",
  "Find a highly rated mystery without graphic violence",
]

export function AssistantShell({ bookId }: { bookId?: string }) {
  const assistant = useAssistant(bookId)
  const [draft, setDraft] = useState("")
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [assistant.messages, assistant.sending])

  const submit = async (event?: FormEvent) => {
    event?.preventDefault()
    const message = draft.trim()
    if (!message) return
    setDraft("")
    const sent = await assistant.sendMessage(message)
    if (!sent) setDraft(message)
  }

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      void submit()
    }
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid min-h-[calc(100vh-7rem)] overflow-hidden rounded-2xl border bg-card shadow-sm md:grid-cols-[260px_1fr]">
        <aside className="border-b bg-muted/30 p-4 md:border-b-0 md:border-r">
          <Button className="w-full justify-start" onClick={assistant.startConversation}>
            <MessageSquarePlus className="mr-2 h-4 w-4" /> New conversation
          </Button>
          <div className="mt-5 space-y-1">
            <p className="px-2 pb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Recent</p>
            {assistant.conversations.length ? assistant.conversations.map((conversation) => (
              <button
                key={conversation.id}
                type="button"
                onClick={() => void assistant.selectConversation(conversation.id)}
                className={cn(
                  "w-full truncate rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-muted",
                  assistant.activeConversationId === conversation.id && "bg-muted font-medium",
                )}
              >
                {conversation.title || "Untitled conversation"}
              </button>
            )) : (
              <p className="px-2 text-sm text-muted-foreground">No conversations yet.</p>
            )}
          </div>
        </aside>

        <section className="flex min-h-[620px] min-w-0 flex-col">
          <header className="flex flex-wrap items-center justify-between gap-3 border-b px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-primary/10 p-2 text-primary"><Bot className="h-5 w-5" /></div>
              <div>
                <h1 className="font-semibold">AI Librarian</h1>
                <p className="text-xs text-muted-foreground">Catalog-grounded recommendations</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {bookId ? <Badge variant="secondary">Book context attached</Badge> : null}
              {assistant.status ? (
                <Badge variant={assistant.status.configured ? "outline" : "secondary"}>
                  {assistant.status.configured ? <CheckCircle2 className="mr-1 h-3 w-3" /> : <CircleAlert className="mr-1 h-3 w-3" />}
                  {assistant.status.provider} · {assistant.status.model}
                </Badge>
              ) : null}
            </div>
          </header>

          <div className="flex-1 space-y-5 overflow-y-auto p-5 md:p-7">
            {assistant.loading ? (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading conversation…
              </div>
            ) : !assistant.messages.length ? (
              <div className="mx-auto flex h-full max-w-2xl flex-col items-center justify-center space-y-6 text-center">
                <div className="rounded-2xl bg-primary/10 p-4 text-primary"><Sparkles className="h-8 w-8" /></div>
                <div className="space-y-2">
                  <h2 className="text-2xl font-semibold">What would you like to read?</h2>
                  <p className="text-muted-foreground">
                    Ask for recommendations, compare books, or attach a book and explore similar options.
                  </p>
                </div>
                <div className="grid w-full gap-2 sm:grid-cols-3">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => setDraft(suggestion)}
                      className="rounded-xl border p-3 text-left text-sm transition-colors hover:bg-muted"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              assistant.messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  actionInFlight={assistant.actionInFlight}
                  onResolveAction={(actionId, decision) => void assistant.resolveAction(actionId, decision)}
                />
              ))
            )}
            {assistant.sending ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> AI Librarian is thinking…
              </div>
            ) : null}
            <div ref={endRef} />
          </div>

          <footer className="border-t bg-background/80 p-4">
            {assistant.error ? (
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <span>{assistant.error}</span>
                {assistant.error.includes("Sign in") ? <Link href="/profile" className="font-medium underline">Sign in</Link> : null}
              </div>
            ) : null}
            <form className="flex items-end gap-2" onSubmit={(event) => void submit(event)}>
              <Textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Ask for a book recommendation…"
                rows={2}
                maxLength={2000}
                className="min-h-12 resize-none rounded-xl"
                aria-label="Message AI Librarian"
              />
              <Button type="submit" size="icon" className="h-12 w-12 shrink-0 rounded-xl" disabled={!draft.trim() || assistant.sending}>
                {assistant.sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                <span className="sr-only">Send message</span>
              </Button>
            </form>
            <p className="mt-2 text-center text-xs text-muted-foreground">AI can make mistakes. Book facts are linked to catalog fields when available.</p>
          </footer>
        </section>
      </div>
    </div>
  )
}

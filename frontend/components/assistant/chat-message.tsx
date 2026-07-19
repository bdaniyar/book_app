"use client"

import { Bot, User } from "lucide-react"

import { ActionConfirmation } from "@/components/assistant/action-confirmation"
import { BookResults } from "@/components/assistant/book-results"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import type { AssistantMessage } from "@/lib/assistant-api"
import { cn } from "@/lib/utils"

export function ChatMessage({
  message,
  actionInFlight,
  onResolveAction,
}: {
  message: AssistantMessage
  actionInFlight: string | null
  onResolveAction: (actionId: string, decision: "confirm" | "reject") => void
}) {
  const assistant = message.role === "assistant"

  return (
    <article className={cn("flex gap-3", !assistant && "flex-row-reverse")}>
      <Avatar className="h-8 w-8 shrink-0 border">
        <AvatarFallback>{assistant ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}</AvatarFallback>
      </Avatar>
      <div className={cn("max-w-[88%] rounded-2xl px-4 py-3", assistant ? "bg-muted/70" : "bg-primary text-primary-foreground")}>
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
        {assistant ? (
          <>
            <BookResults books={message.books ?? []} citations={message.citations ?? []} />
            {message.proposedActions?.map((action) => (
              <ActionConfirmation
                key={action.id}
                action={action}
                bookTitle={message.books?.find((book) => book.id === action.payload.bookId)?.title}
                loading={actionInFlight === action.id}
                onConfirm={() => onResolveAction(action.id, "confirm")}
                onReject={() => onResolveAction(action.id, "reject")}
              />
            ))}
          </>
        ) : null}
      </div>
    </article>
  )
}

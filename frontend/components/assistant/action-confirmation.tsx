"use client"

import { Check, Clock3, Loader2, ShieldCheck, X } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { AssistantAction } from "@/lib/assistant-api"

function actionTitle(action: AssistantAction, bookTitle?: string) {
  const readableType = action.type.replaceAll("_", " ").replaceAll("-", " ")
  const title = bookTitle ?? action.payload.title ?? action.payload.bookTitle
  return typeof title === "string" ? `${readableType}: ${title}` : readableType
}

function actionChange(action: AssistantAction) {
  if (typeof action.payload.status === "string") {
    return `Reading status: ${action.payload.status.replaceAll("-", " ")}`
  }
  if (typeof action.payload.isFavorite === "boolean") {
    return action.payload.isFavorite ? "Add to favorites" : "Remove from favorites"
  }
  return "Library update"
}

export function ActionConfirmation({
  action,
  bookTitle,
  loading,
  onConfirm,
  onReject,
}: {
  action: AssistantAction
  bookTitle?: string
  loading: boolean
  onConfirm: () => void
  onReject: () => void
}) {
  if (action.status !== "pending") {
    return (
      <div className="mt-3 flex items-center gap-2 rounded-lg border bg-background/60 p-3 text-sm">
        {action.status === "executed" ? <Check className="h-4 w-4 text-emerald-500" /> : <X className="h-4 w-4 text-muted-foreground" />}
        <span className="capitalize">{actionTitle(action, bookTitle)}</span>
        <Badge variant="secondary" className="ml-auto capitalize">{action.status}</Badge>
      </div>
    )
  }

  return (
    <div className="mt-3 space-y-3 rounded-lg border border-primary/20 bg-primary/5 p-4">
      <div className="flex items-start gap-3">
        <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
        <div className="min-w-0">
          <p className="font-medium capitalize">{actionTitle(action, bookTitle)}</p>
          <p className="mt-1 text-sm">{actionChange(action)}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Nothing will change until you confirm this action.
          </p>
          <p className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
            <Clock3 className="h-3 w-3" /> Expires {new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(action.expiresAt))}
          </p>
        </div>
      </div>
      <div className="flex gap-2">
        <Button size="sm" onClick={onConfirm} disabled={loading}>
          {loading ? <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" /> : <Check className="mr-2 h-3.5 w-3.5" />}
          Confirm
        </Button>
        <Button size="sm" variant="outline" onClick={onReject} disabled={loading}>
          <X className="mr-2 h-3.5 w-3.5" /> Reject
        </Button>
      </div>
    </div>
  )
}

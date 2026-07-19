"use client"

import { Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Loader2 } from "lucide-react"

import { AssistantShell } from "@/components/assistant/assistant-shell"

export default function AssistantPage() {
  return (
    <Suspense fallback={<AssistantLoading />}>
      <AssistantPageContent />
    </Suspense>
  )
}

function AssistantPageContent() {
  const params = useSearchParams()
  return <AssistantShell bookId={params.get("bookId") ?? undefined} />
}

function AssistantLoading() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center text-muted-foreground">
      <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading AI Librarian…
    </div>
  )
}

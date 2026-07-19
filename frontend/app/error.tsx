"use client"

import { useEffect } from "react"
import { AlertCircle, RotateCcw } from "lucide-react"

import { Button } from "@/components/ui/button"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="container mx-auto flex min-h-[65vh] max-w-2xl items-center justify-center px-4 py-16">
      <div className="space-y-5 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold">We could not load this page</h1>
          <p className="text-muted-foreground">
            {error.message || "The server is unavailable. Please try again in a moment."}
          </p>
        </div>
        <Button onClick={reset} className="rounded-xl">
          <RotateCcw className="mr-2 h-4 w-4" />
          Try again
        </Button>
      </div>
    </div>
  )
}

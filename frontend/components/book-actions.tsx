"use client"

import { useState } from "react"
import type { ElementType, MouseEvent } from "react"
import { BookCheck, BookMarked, BookOpen, Check, Heart, Library, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { libraryService, type LibraryStatus } from "@/lib/api-services"
import { cn } from "@/lib/utils"

type BookActionsProps = {
  bookId: string
  compact?: boolean
  className?: string
  onChanged?: (status: LibraryStatus) => void
}

const statuses: Array<{
  status: LibraryStatus
  label: string
  icon: ElementType
}> = [
  { status: "want-to-read", label: "Want to Read", icon: BookMarked },
  { status: "reading", label: "Reading", icon: BookOpen },
  { status: "read", label: "Read", icon: BookCheck },
  { status: "favorite", label: "Favorite", icon: Heart },
]

export function BookActions({ bookId, compact = false, className, onChanged }: BookActionsProps) {
  const [saving, setSaving] = useState<LibraryStatus | null>(null)
  const [savedStatus, setSavedStatus] = useState<LibraryStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  const saveStatus = async (status: LibraryStatus) => {
    setSaving(status)
    setError(null)
    try {
      const res = await libraryService.addBook(bookId, status)
      if (!res.success) {
        setError(res.error || "Sign in to save books")
        return
      }
      setSavedStatus(status)
      onChanged?.(status)
    } finally {
      setSaving(null)
    }
  }

  const stop = (event: MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()
  }

  const currentLabel = savedStatus
    ? statuses.find((item) => item.status === savedStatus)?.label
    : compact
      ? "Add"
      : "Add to Library"

  return (
    <div className={cn("space-y-1", className)} onClick={stop}>
      <div className="flex gap-2">
        <Button
          type="button"
          size={compact ? "sm" : "default"}
          className={cn("min-w-0 flex-1 rounded-lg", compact && "h-8 px-2 text-xs")}
          disabled={saving !== null}
          onClick={() => saveStatus("want-to-read")}
        >
          {saving === "want-to-read" ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : savedStatus ? (
            <Check className="h-4 w-4" />
          ) : (
            <Library className="h-4 w-4" />
          )}
          <span className={cn("ml-2 truncate", compact && "ml-1")}>{currentLabel}</span>
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              variant="outline"
              size={compact ? "sm" : "default"}
              className={cn("rounded-lg bg-background/80", compact && "h-8 px-2")}
              disabled={saving !== null}
            >
              <BookOpen className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44">
            <DropdownMenuLabel>Set status</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {statuses.map(({ status, label, icon: Icon }) => (
              <DropdownMenuItem key={status} onClick={() => saveStatus(status)}>
                <Icon className="h-4 w-4" />
                <span>{label}</span>
                {savedStatus === status ? <Check className="ml-auto h-4 w-4 text-primary" /> : null}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      {error ? <p className="text-[11px] leading-snug text-destructive">{error}</p> : null}
    </div>
  )
}

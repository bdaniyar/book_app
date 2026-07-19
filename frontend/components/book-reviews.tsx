"use client"

import { useState } from "react"

import { ReviewDialog } from "@/components/review-dialog"
import { ReviewList } from "@/components/review-list"

export function BookReviews({ bookId }: { bookId: string }) {
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-2xl font-semibold">Reader Reviews</h2>
        <ReviewDialog bookId={bookId} onCreated={() => setRefreshKey((value) => value + 1)} />
      </div>
      <ReviewList bookId={bookId} refreshKey={refreshKey} />
    </section>
  )
}

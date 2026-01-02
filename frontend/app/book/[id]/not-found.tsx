import Link from "next/link"
import { BookX } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <div className="container flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6">
      <BookX className="h-24 w-24 text-muted-foreground" />
      <div className="space-y-2">
        <h1 className="font-sans text-3xl font-bold">Book Not Found</h1>
        <p className="text-muted-foreground text-lg">Sorry, we couldn't find the book you're looking for.</p>
      </div>
      <Button asChild size="lg" className="rounded-xl">
        <Link href="/">Back to Home</Link>
      </Button>
    </div>
  )
}

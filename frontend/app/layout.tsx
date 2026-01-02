import type React from "react"
import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import { Analytics } from "@vercel/analytics/next"
import { ThemeProvider } from "@/components/theme-provider"
import { Navigation } from "@/components/navigation"
import { Suspense } from "react"
import "./globals.css"

export const metadata: Metadata = {
  title: "BookHaven - Discover Your Next Great Read",
  description: "A modern book discovery and recommendation platform",
  generator: "v0.app",
  keywords: ["books", "reading", "recommendations", "book discovery", "literature"],
  authors: [{ name: "BookHaven Team" }],
  openGraph: {
    title: "BookHaven - Discover Your Next Great Read",
    description: "A modern book discovery and recommendation platform",
    type: "website",
  },
}

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable} antialiased min-h-screen w-full overflow-x-hidden`}>
        <ThemeProvider defaultTheme="dark" storageKey="book-app-theme">
          <Suspense fallback={null}>
            <Navigation />
            <main className="min-h-screen pb-20 md:pb-0 w-full">{children}</main>
          </Suspense>
        </ThemeProvider>
        <Analytics />
      </body>
    </html>
  )
}

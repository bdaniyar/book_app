"use client"

import Link from "next/link"
import { FormEvent, Suspense, useState } from "react"
import { useSearchParams } from "next/navigation"
import { CheckCircle2, KeyRound, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { authService } from "@/lib/api-services"

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<ResetPasswordLoading />}>
      <ResetPasswordForm />
    </Suspense>
  )
}

function ResetPasswordForm() {
  const searchParams = useSearchParams()
  const token = searchParams.get("token")?.trim() ?? ""
  const [password, setPassword] = useState("")
  const [confirmation, setConfirmation] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [complete, setComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    if (!token) {
      setError("This reset link does not contain a token. Request a new link from your profile page.")
      return
    }
    if (password.length < 8 || password.length > 72) {
      setError("Your password must contain between 8 and 72 characters.")
      return
    }
    if (password !== confirmation) {
      setError("The passwords do not match.")
      return
    }

    setSubmitting(true)
    const response = await authService.resetPassword({
      token,
      new_password: password,
      new_password2: confirmation,
    })
    setSubmitting(false)

    if (!response.success) {
      setError(response.error || "The reset link is invalid or has expired.")
      return
    }
    setComplete(true)
  }

  return (
    <div className="container mx-auto flex min-h-[70vh] max-w-lg items-center px-4 py-12">
      <Card className="w-full border-border/60">
        <CardHeader className="space-y-3 text-center">
          {complete
            ? <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-500" />
            : <KeyRound className="mx-auto h-10 w-10 text-primary" />}
          <CardTitle>{complete ? "Password updated" : "Choose a new password"}</CardTitle>
          <CardDescription>
            {complete
              ? "Your old sessions have been closed. You can now sign in with the new password."
              : "Use a unique password between 8 and 72 characters."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {complete ? (
            <Button asChild className="w-full"><Link href="/profile">Go to sign in</Link></Button>
          ) : (
            <form className="space-y-4" onSubmit={submit}>
              <div className="space-y-2">
                <Label htmlFor="new-password">New password</Label>
                <Input
                  id="new-password"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  maxLength={72}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm-password">Confirm new password</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  maxLength={72}
                  value={confirmation}
                  onChange={(event) => setConfirmation(event.target.value)}
                  required
                />
              </div>
              {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
              <Button type="submit" className="w-full" disabled={submitting || !token}>
                {submitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Update password
              </Button>
              {!token ? (
                <p className="text-center text-sm text-muted-foreground">
                  Missing token. <Link className="underline" href="/profile">Request another reset link</Link>.
                </p>
              ) : null}
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function ResetPasswordLoading() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center text-muted-foreground">
      <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading reset link…
    </div>
  )
}

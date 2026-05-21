"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import Aurora from "@/components/Aurora"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { fetchCurrentUser, logoutCurrentUser } from "@/lib/auth-client"

type AuthMode = "login" | "signup"

const blankSignup = {
  firstName: "",
  lastName: "",
  dateOfBirth: "",
  address: "",
  phone: "",
  email: "",
  password: "",
  organizationName: "",
}

export default function AuthPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const nextPath = useMemo(() => searchParams.get("next") || "/presentation", [searchParams])
  const [mode, setMode] = useState<AuthMode>("signup")
  const [loginEmail, setLoginEmail] = useState("")
  const [loginPassword, setLoginPassword] = useState("")
  const [signup, setSignup] = useState(blankSignup)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    let isActive = true

    const loadUser = async () => {
      const currentUser = await fetchCurrentUser()
      if (currentUser?.user && isActive) {
        router.replace(nextPath)
      }
    }

    void loadUser()

    return () => {
      isActive = false
    }
  }, [nextPath, router])

  const submitSignup = async () => {
    setIsSubmitting(true)
    setError(null)

    try {
      const response = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(signup),
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.error || "Signup failed")
      }

      router.replace(nextPath)
      router.refresh()
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Signup failed")
    } finally {
      setIsSubmitting(false)
    }
  }

  const submitLogin = async () => {
    setIsSubmitting(true)
    setError(null)

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.error || "Login failed")
      }

      router.replace(nextPath)
      router.refresh()
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Login failed")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleLogout = async () => {
    await logoutCurrentUser()
    router.refresh()
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#09090f] text-white">
      <div className="absolute inset-0">
        <Aurora colorStops={["#1d1836", "#4c1d95", "#312e81"]} amplitude={1.15} blend={0.58} speed={0.8} />
      </div>

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-10 md:px-8 lg:flex-row lg:items-center lg:gap-10 lg:py-16">
        <div className="max-w-2xl flex-1 space-y-8 pb-10 lg:pb-0">
          <div className="inline-flex items-center rounded-full border border-white/15 bg-white/10 px-4 py-2 text-sm text-foreground opacity-80 backdrop-blur-xl">
            Platform access
          </div>
          <div className="space-y-4">
            <h1 className="text-5xl font-semibold tracking-tight sm:text-6xl">
              One account for the whole ScaleUp platform.
            </h1>
            <p className="max-w-xl text-base leading-7 text-foreground opacity-80 sm:text-lg">
              Create your account once, then use pitch evaluation, BMC, legal, SRS, marketing and FiskoBot tools without re-entering your details.
            </p>
          </div>

            <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl">
              <p className="text-sm text-foreground opacity-75">Plan</p>
              <p className="mt-2 text-xl font-medium text-foreground">Free access</p>
              <p className="mt-2 text-sm text-foreground opacity-70">Signup defaults to a free plan with full platform access for now.</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl">
              <p className="text-sm text-foreground opacity-75">Protected tools</p>
              <p className="mt-2 text-xl font-medium text-foreground">All business modules</p>
              <p className="mt-2 text-sm text-foreground opacity-70">The public landing page stays open, but the app tools require sign-in.</p>
            </div>
          </div>

          <div className="text-sm text-white/45">
            Back to <Link href="/" className="text-white underline decoration-white/30 underline-offset-4">homepage</Link>
          </div>
        </div>

        <Card className="w-full max-w-xl border-white/10 bg-white/5 text-white shadow-2xl shadow-black/40 backdrop-blur-2xl">
          <CardHeader className="space-y-2 border-b border-white/10 pb-6">
            <CardTitle className="text-2xl">{mode === "signup" ? "Create account" : "Sign in"}</CardTitle>
            <CardDescription className="text-white/60">
              {mode === "signup"
                ? "Add your basic profile details, then create your free account."
                : "Use your email and password to continue."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 p-6">
            <div className="flex rounded-full border border-white/10 bg-black/20 p-1">
              <button
                type="button"
                onClick={() => setMode("signup")}
                className={`flex-1 rounded-full px-4 py-2 text-sm font-medium transition ${mode === "signup" ? "bg-white text-black" : "text-white/65"}`}
              >
                Sign up
              </button>
              <button
                type="button"
                onClick={() => setMode("login")}
                className={`flex-1 rounded-full px-4 py-2 text-sm font-medium transition ${mode === "login" ? "bg-white text-black" : "text-white/65"}`}
              >
                Sign in
              </button>
            </div>

            {error ? (
              <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                {error}
              </div>
            ) : null}

            {mode === "signup" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First name</Label>
                  <Input id="firstName" value={signup.firstName} onChange={(event) => setSignup((prev) => ({ ...prev, firstName: event.target.value }))} className="border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="Sofia" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last name</Label>
                  <Input id="lastName" value={signup.lastName} onChange={(event) => setSignup((prev) => ({ ...prev, lastName: event.target.value }))} className="border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="Ben Ali" />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="organizationName">Organization / startup name</Label>
                  <Input id="organizationName" value={signup.organizationName} onChange={(event) => setSignup((prev) => ({ ...prev, organizationName: event.target.value }))} className="border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="ScaleUp Studio" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dateOfBirth">Date of birth</Label>
                  <Input id="dateOfBirth" type="date" value={signup.dateOfBirth} onChange={(event) => setSignup((prev) => ({ ...prev, dateOfBirth: event.target.value }))} className="border-white/10 bg-white/5 text-white" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input id="phone" value={signup.phone} onChange={(event) => setSignup((prev) => ({ ...prev, phone: event.target.value }))} className="border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="+216 12 345 678" />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="address">Address</Label>
                  <Input id="address" value={signup.address} onChange={(event) => setSignup((prev) => ({ ...prev, address: event.target.value }))} className="border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="Tunis, Tunisia" />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="signupEmail">Email</Label>
                  <Input id="signupEmail" type="email" value={signup.email} onChange={(event) => setSignup((prev) => ({ ...prev, email: event.target.value }))} className="border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="you@example.com" />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="signupPassword">Password</Label>
                  <Input id="signupPassword" type="password" value={signup.password} onChange={(event) => setSignup((prev) => ({ ...prev, password: event.target.value }))} className="border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="Minimum 8 characters" />
                </div>
                <Button className="sm:col-span-2 h-11 rounded-xl bg-white text-black hover:bg-white/90" disabled={isSubmitting} onClick={submitSignup}>
                  {isSubmitting ? "Creating account..." : "Create free account"}
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="loginEmail">Email</Label>
                  <Input id="loginEmail" type="email" value={loginEmail} onChange={(event) => setLoginEmail(event.target.value)} className="border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="you@example.com" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="loginPassword">Password</Label>
                  <Input id="loginPassword" type="password" value={loginPassword} onChange={(event) => setLoginPassword(event.target.value)} className="border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="Your password" />
                </div>
                <Button className="h-11 w-full rounded-xl bg-white text-black hover:bg-white/90" disabled={isSubmitting} onClick={submitLogin}>
                  {isSubmitting ? "Signing in..." : "Sign in"}
                </Button>
              </div>
            )}

            <div className="flex items-center justify-between border-t border-white/10 pt-4 text-sm text-white/55">
              <span>Need to switch accounts?</span>
              <button type="button" onClick={handleLogout} className="text-white underline decoration-white/30 underline-offset-4">Clear session</button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

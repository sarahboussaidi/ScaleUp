import { NextRequest, NextResponse } from "next/server"
import { AUTH_COOKIE_NAME, readCookieValue, verifySessionToken } from "@/lib/session"

const PUBLIC_PATHS = ["/", "/auth"]

const PROTECTED_PREFIXES = [
  "/presentation",
  "/bmc",
  "/bmc-generation",
  "/financial",
  "/financial-advisor",
  "/fiskobot",
  "/legal-analysis",
  "/marketing-analysis",
  "/srs",
]

const PROTECTED_API_PREFIXES = ["/api/fiskobot"]

function isProtectedPath(pathname: string) {
  if (PUBLIC_PATHS.includes(pathname)) {
    return false
  }

  if (PROTECTED_API_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return true
  }

  return PROTECTED_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))
}

export async function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl

  if (!isProtectedPath(pathname)) {
    return NextResponse.next()
  }

  const token = readCookieValue(request.headers.get("cookie"), AUTH_COOKIE_NAME)
  const session = token ? await verifySessionToken(token) : null

  if (session) {
    return NextResponse.next()
  }

  if (pathname.startsWith("/api/")) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 })
  }

  const authUrl = new URL("/auth", request.url)
  const nextPath = `${pathname}${search}`
  authUrl.searchParams.set("next", nextPath)

  return NextResponse.redirect(authUrl)
}

export const config = {
  matcher: [
    "/presentation/:path*",
    "/bmc/:path*",
    "/bmc-generation/:path*",
    "/financial/:path*",
    "/financial-advisor/:path*",
    "/fiskobot/:path*",
    "/legal-analysis/:path*",
    "/marketing-analysis/:path*",
    "/srs/:path*",
    "/api/fiskobot/:path*",
  ],
}

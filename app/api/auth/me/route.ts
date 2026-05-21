import { NextRequest, NextResponse } from "next/server"
import { AUTH_COOKIE_NAME, readCookieValue, verifySessionToken } from "@/lib/session"

export async function GET(req: NextRequest) {
  const token = readCookieValue(req.headers.get("cookie"), AUTH_COOKIE_NAME)

  if (!token) {
    return NextResponse.json({ user: null }, { status: 401 })
  }

  const payload = await verifySessionToken(token)
  if (!payload) {
    return NextResponse.json({ user: null }, { status: 401 })
  }

  return NextResponse.json({
    user: {
      id: payload.sub,
      email: payload.email,
      firstName: payload.firstName,
      lastName: payload.lastName,
      plan: payload.plan,
    },
  })
}

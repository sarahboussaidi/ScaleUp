import { NextRequest, NextResponse } from "next/server"
import { createSessionToken, AUTH_COOKIE_NAME } from "@/lib/session"
import { findUserByEmail, toPublicUser, verifyPassword } from "@/lib/user-store"

type LoginBody = {
  email?: string
  password?: string
}

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as LoginBody
    const email = body.email?.trim() || ""
    const password = body.password || ""

    if (!email || !password) {
      return NextResponse.json({ error: "Email and password are required." }, { status: 400 })
    }

    const user = await findUserByEmail(email)
    if (!user || !verifyPassword(password, user.passwordSalt, user.passwordHash)) {
      return NextResponse.json({ error: "Invalid email or password." }, { status: 401 })
    }

    const token = await createSessionToken({
      sub: user.id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      plan: user.plan,
      iat: Date.now(),
      exp: Date.now() + 1000 * 60 * 60 * 24 * 30,
    })

    const response = NextResponse.json({ user: toPublicUser(user) })
    response.cookies.set({
      name: AUTH_COOKIE_NAME,
      value: token,
      path: "/",
      sameSite: "lax",
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
    })

    return response
  } catch (error) {
    const message = error instanceof Error ? error.message : "Login failed."
    return NextResponse.json({ error: message }, { status: 400 })
  }
}

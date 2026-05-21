import { NextRequest, NextResponse } from "next/server"
import { createSessionToken, AUTH_COOKIE_NAME } from "@/lib/session"
import { createUser, toPublicUser } from "@/lib/user-store"

type SignupBody = {
  firstName?: string
  lastName?: string
  dateOfBirth?: string
  address?: string
  phone?: string
  email?: string
  password?: string
  organizationName?: string
}

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as SignupBody
    const firstName = body.firstName?.trim() || ""
    const lastName = body.lastName?.trim() || ""
    const dateOfBirth = body.dateOfBirth?.trim() || ""
    const address = body.address?.trim() || ""
    const phone = body.phone?.trim() || ""
    const email = body.email?.trim() || ""
    const password = body.password || ""

    if (!firstName || !lastName || !dateOfBirth || !address || !phone || !email || !password) {
      return NextResponse.json({ error: "Please complete all required fields." }, { status: 400 })
    }

    if (password.length < 8) {
      return NextResponse.json({ error: "Password must be at least 8 characters." }, { status: 400 })
    }

    const user = await createUser({
      firstName,
      lastName,
      dateOfBirth,
      address,
      phone,
      email,
      organizationName: body.organizationName,
      password,
      plan: "free",
    })

    const token = await createSessionToken({
      sub: user.id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      plan: user.plan,
      iat: Date.now(),
      exp: Date.now() + 1000 * 60 * 60 * 24 * 30,
    })

    const response = NextResponse.json({ user: toPublicUser(user) }, { status: 201 })
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
    const message = error instanceof Error ? error.message : "Signup failed."
    return NextResponse.json({ error: message }, { status: 400 })
  }
}

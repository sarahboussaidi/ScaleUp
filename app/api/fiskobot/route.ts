import { NextRequest, NextResponse } from "next/server"
import { AUTH_COOKIE_NAME, readCookieValue, verifySessionToken } from "@/lib/session"

export async function POST(req: NextRequest) {
  try {
    const token = readCookieValue(req.headers.get("cookie"), AUTH_COOKIE_NAME)
    const session = token ? await verifySessionToken(token) : null
    if (!session) {
      return NextResponse.json({ error: "Authentication required." }, { status: 401 })
    }

    const { messages } = await req.json()

    const { Client } = await import("@gradio/client")
    const app = await Client.connect("ferdaouskachouri/fiskobot-api")

    const lastMessage = messages[messages.length - 1]?.content ?? ""

    const history = messages.slice(0, -1).map((m: any) => ({
      role: m.role,
      metadata: null,
      content: [{ type: "text", text: m.content }],
    }))

    const result = await app.predict("/respond_1", {
      message: lastMessage,
      history: history,
    })

    const data = (result as any).data
    const updatedHistory = data[1] as any[]
    const lastMsg = updatedHistory[updatedHistory.length - 1]
    const answer = lastMsg?.content?.[0]?.text ?? lastMsg?.content ?? "No response"

    return NextResponse.json({ message: answer })

  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
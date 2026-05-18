import { NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  try {
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
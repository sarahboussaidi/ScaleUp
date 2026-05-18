"use client"

import { useState, useRef, useEffect } from "react"
import { GlassmorphismNav } from "@/components/glassmorphism-nav"
import Aurora from "@/components/Aurora"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Send, Bot, User, Loader2, Trash2,
  Sparkles, TrendingUp, FileText,
} from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
}

const SUGGESTED = [
  "What are the tax benefits for a labeled startup?",
  "How to obtain the Startup Act label in Tunisia?",
  "What is the 100k TND technology card?",
  "What are the SME measures in Finance Law 2026?",
]

export default function FiskoBotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hello! I'm **FiskoBot**, your AI financial assistant specialized in the Tunisian startup ecosystem.\n\nI can help you with:\n• The Startup Act and its benefits\n• Finance Law 2026\n• Tunisian taxation (CIT, VAT, withholding)\n• Financing and investment\n\nWhat is your question?",
    },
  ])
  const [input, setInput]       = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [history, setHistory]   = useState<{ role: string; content: string }[]>([])
  const messagesEndRef          = useRef<HTMLDivElement>(null)
  const inputRef                = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isTyping) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
    }

    const newHistory = [...history, { role: "user", content: input.trim() }]
    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setIsTyping(true)

    try {
      const res = await fetch("/api/fiskobot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newHistory }),
      })

      const data = await res.json()
      if (data.error) throw new Error(data.error)

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.message,
      }

      setMessages((prev) => [...prev, assistantMsg])
      setHistory([...newHistory, { role: "assistant", content: data.message }])

    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), role: "assistant", content: `❌ Error: ${err.message}` },
      ])
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const clearChat = () => {
    setHistory([])
    setMessages([{
      id: "welcome",
      role: "assistant",
      content: "Chat reset. How can I help you?",
    }])
  }

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      <main className="min-h-screen relative overflow-hidden">
        <div className="fixed inset-0 w-full h-full">
          <Aurora colorStops={["#1e1b4b", "#4c1d95", "#312e81"]} amplitude={1.2} blend={0.6} speed={0.8} />
        </div>

        <div className="relative z-10">
          <GlassmorphismNav />

          <section className="pt-32 pb-16 px-4">
            <div className="max-w-4xl mx-auto space-y-8">

              {/* Header */}
              <div className="text-center space-y-4">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-300 text-sm font-medium">
                  <Sparkles className="w-4 h-4 mr-2" />
                  FiskoBot · Tunisian Financial Assistant
                </div>
                <h1 className="text-4xl sm:text-5xl font-bold text-white">
                  Fisko<span className="bg-gradient-to-r from-orange-400 to-amber-400 bg-clip-text text-transparent">Bot</span>
                </h1>
                <p className="text-white/50 max-w-xl mx-auto text-sm">
                  Expert in Startup Act, Tunisian taxation and Finance Law 2026
                </p>
              </div>

              {/* Navigation */}
              <div className="flex flex-wrap items-center justify-center gap-3">
                <a href="/financial-advisor" className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm font-medium hover:bg-emerald-500/20 transition-all">
                  <FileText className="w-4 h-4" /> Document Classification
                </a>
                <a href="/financial" className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-violet-500/10 border border-violet-500/30 text-violet-300 text-sm font-medium hover:bg-violet-500/20 transition-all">
                  <TrendingUp className="w-4 h-4" /> Financial Prediction
                </a>
                <a href="/fiskobot" className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-orange-500/20 border border-orange-500/40 text-orange-300 text-sm font-medium ring-1 ring-orange-500/40">
                  <Bot className="w-4 h-4" /> FiskoBot
                </a>
              </div>

              {/* Suggested Questions */}
              {messages.length <= 1 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {SUGGESTED.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => { setInput(q); inputRef.current?.focus() }}
                      className="p-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all text-left text-white/70 text-sm hover:text-white"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}

              {/* Chat */}
              <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                <CardContent className="p-0">
                  {/* Messages */}
                  <div className="h-[500px] overflow-y-auto p-4 space-y-4">
                    {messages.map((msg) => (
                      <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === "assistant" ? "bg-orange-500/20" : "bg-violet-500/20"}`}>
                          {msg.role === "assistant"
                            ? <Bot className="w-4 h-4 text-orange-400" />
                            : <User className="w-4 h-4 text-violet-400" />
                          }
                        </div>
                        <div className={`max-w-[80%] p-4 rounded-2xl text-sm ${msg.role === "assistant"
                          ? "bg-white/5 border border-white/10 text-white/80"
                          : "bg-gradient-to-r from-violet-500/20 to-purple-500/20 border border-violet-500/30 text-white"
                        }`}>
                          {msg.content.split("\n").map((line, i) =>
                            line ? <p key={i} className="mb-1">{line.replace(/\*\*/g, "")}</p> : null
                          )}
                        </div>
                      </div>
                    ))}

                    {isTyping && (
                      <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-orange-400" />
                        </div>
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-4 flex items-center gap-2">
                          <Loader2 className="w-4 h-4 text-orange-400 animate-spin" />
                          <span className="text-white/60 text-sm">FiskoBot is thinking...</span>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input */}
                  <div className="border-t border-white/10 p-4">
                    <div className="flex items-end gap-3">
                      <Button variant="ghost" size="icon" onClick={clearChat}
                        className="text-white/40 hover:text-white hover:bg-white/10">
                        <Trash2 className="w-5 h-5" />
                      </Button>
                      <div className="flex-1">
                        <textarea
                          ref={inputRef}
                          value={input}
                          onChange={(e) => setInput(e.target.value)}
                          onKeyDown={handleKeyDown}
                          placeholder="Ask your question about the Startup Act, taxation..."
                          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-orange-500/50 resize-none min-h-[48px] max-h-[120px] text-sm"
                          rows={1}
                        />
                      </div>
                      <Button
                        onClick={handleSend}
                        disabled={!input.trim() || isTyping}
                        className="bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white rounded-xl px-6"
                      >
                        <Send className="w-5 h-5" />
                      </Button>
                    </div>
                    <p className="text-white/30 text-xs mt-2 text-center">
                      Powered by Groq · Llama 3.3 70B · Official Tunisian sources
                    </p>
                  </div>
                </CardContent>
              </Card>

            </div>
          </section>
          <Footer />
        </div>
      </main>
    </div>
  )
}
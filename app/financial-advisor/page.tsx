"use client"

import { useState, useRef, useCallback } from "react"
import Link from "next/link"
// @ts-ignore
import { GlassmorphismNav } from "@/components/glassmorphism-nav"
import Aurora from "@/components/Aurora"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Bot,
  User,
  DollarSign,
  Loader2,
  Trash2,
  Upload,
  FileSpreadsheet,
  TrendingUp,
  X,
  ScanLine,
  CheckCircle2,
  AlertCircle,
} from "lucide-react"

// ── Types ────────────────────────────────────────────────────
interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  attachedFile?: {
    name: string
    type: string
    classification?: DocumentClassification
  }
}

interface DocumentClassification {
  predicted_class: string
  confidence: number
  all_probs: Record<string, number>
}

// ── Classes labels ────────────────────────────────────────────
const CLASS_LABELS: Record<string, { label: string; color: string; icon: string }> = {
  Bank_Statement: { label: "Bank Statement", color: "text-blue-400",   icon: "🏦" },
  Check:          { label: "Check / Chèque", color: "text-purple-400", icon: "📄" },
  ITR_Form_16:    { label: "ITR / Form 16",  color: "text-yellow-400", icon: "📋" },
  Salary_Slip:    { label: "Salary Slip",    color: "text-green-400",  icon: "💼" },
  Utility:        { label: "Utility Bill",   color: "text-orange-400", icon: "⚡" },
}

// ── Call Gradio API ───────────────────────────────────────────
async function classifyDocument(file: File): Promise<DocumentClassification> {
  const { Client } = await import("@gradio/client")
  const app = await Client.connect("ferdaouskachouri/document-classifier-api")
  
  // ICI : On envoie l'image ET la clé dans l'ordre attendu par ton modèle
  const result = await app.predict("/predict", { 
    image: file, 
    api_key: "mon-api-key-secret-2004", // C'est ici que tu mets ta clé !
  }) as any

  const predicted_class = result.data[0]
  const all_probs = result.data[1]
  const confidence = all_probs?.[predicted_class] ?? 0

  return { predicted_class, confidence, all_probs: all_probs ?? {} }
}

// ── Component ────────────────────────────────────────────────
export default function FinancialAdvisorPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: `Welcome to the Document Classifier!\n\nUpload an image of a financial document and I'll identify it instantly:\n• 🏦 Bank Statement\n• 📄 Check / Chèque\n• 📋 ITR / Form 16\n• 💼 Salary Slip\n• ⚡ Utility Bill`,
      timestamp: new Date(),
    },
  ])
  const [isClassifying, setIsClassifying] = useState(false)
  const [uploadedFile, setUploadedFile]   = useState<File | null>(null)
  const [isDragging, setIsDragging]       = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef   = useRef<HTMLInputElement>(null)

  const handleDragOver  = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragging(true) }, [])
  const handleDragLeave = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragging(false) }, [])
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) setUploadedFile(f)
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) setUploadedFile(f)
  }

  const handleClassify = async () => {
    if (!uploadedFile) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: `Document uploaded: ${uploadedFile.name}`,
      timestamp: new Date(),
      attachedFile: { name: uploadedFile.name, type: uploadedFile.type },
    }
    setMessages((prev) => [...prev, userMessage])
    const currentFile = uploadedFile
    setUploadedFile(null)
    setIsClassifying(true)

    try {
      const classification = await classifyDocument(currentFile)
      const info = CLASS_LABELS[classification.predicted_class] ?? { label: classification.predicted_class, icon: "📄" }
      const confidencePercent = (classification.confidence * 100).toFixed(1)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Document identified as ${info.label} with ${confidencePercent}% confidence.`,
        timestamp: new Date(),
        attachedFile: {
          name: currentFile.name,
          type: currentFile.type,
          classification,
        },
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `❌ Classification failed. Make sure the Space is running.`,
          timestamp: new Date(),
        },
      ])
    } finally {
      setIsClassifying(false)
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100)
    }
  }

  const clearChat = () => {
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: `Upload a new document to classify it.`,
        timestamp: new Date(),
      },
    ])
  }

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      <main className="min-h-screen relative overflow-hidden">
        <div className="fixed inset-0 w-full h-full">
          <Aurora colorStops={["#1e1b4b", "#4c1d95", "#312e81"]} amplitude={1.2} blend={0.6} speed={0.8} />
        </div>

        <div className="relative z-10">
          <GlassmorphismNav />

          <section className="pt-32 pb-8 px-4">
            <div className="max-w-4xl mx-auto">
              {/* Header */}
             <div className="max-w-4xl mx-auto text-center">
  {/* Header : Conteneur principal vertical */}
{/* Ligne des Badges : Alignés horizontalement */}
<div className="flex flex-wrap items-center justify-center gap-3 mb-6">
  <Link
    href="/financial-advisor"
    className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-green-300 text-sm font-semibold"
  >
    <FileSpreadsheet className="w-4 h-4" />
    Document Classification
  </Link>

  <Link
    href="/financial"
    className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-violet-500/10 border border-violet-500/30 text-violet-300 text-sm font-semibold hover:bg-violet-500/20 transition-all"
  >
    <TrendingUp className="w-4 h-4" />
    Financial Prediction · GRU Model
  </Link>

  <Link
    href="/fiskobot"
    className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-orange-500/10 border border-orange-500/30 text-orange-300 text-sm font-semibold hover:bg-orange-500/20 transition-all"
  >
    <Bot className="w-4 h-4" />
    FiskoBot
  </Link>
</div>

    {/* Titre principal juste en dessous */}
    <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
      AI <span className="bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">Document Classifier</span>
    </h1>
  </div>

              {/* Chat Card */}
              <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                <CardContent className="p-0">
                  <div
                    className="h-[500px] overflow-y-auto p-4 space-y-4 relative"
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    {isDragging && (
                      <div className="absolute inset-0 bg-green-500/10 border-2 border-dashed border-green-400 rounded-xl flex items-center justify-center z-10 backdrop-blur-sm">
                        <Upload className="w-12 h-12 text-green-400 mx-auto mb-2" />
                      </div>
                    )}

                    {messages.map((message) => (
                      <div key={message.id} className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${message.role === "assistant" ? "bg-green-500/20" : "bg-purple-500/20"}`}>
                          {message.role === "assistant" ? <Bot className="w-4 h-4 text-green-400" /> : <User className="w-4 h-4 text-purple-400" />}
                        </div>
                        <div className={`max-w-[80%] p-4 rounded-2xl ${message.role === "assistant" ? "bg-white/5 border border-white/10 text-white/80" : "bg-gradient-to-r from-purple-500/20 to-indigo-500/20 border border-purple-500/30 text-white"}`}>
                          {message.attachedFile?.classification && <ClassificationCard classification={message.attachedFile.classification} />}
                          <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                        </div>
                      </div>
                    ))}
                    {isClassifying && <Loader2 className="w-6 h-6 text-green-400 animate-spin mx-auto" />}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Footer Actions */}
                  <div className="border-t border-white/10 p-4">
                    <div className="flex items-center gap-3">
                      <Button variant="ghost" size="icon" onClick={clearChat} className="text-white/40"><Trash2 className="w-5 h-5" /></Button>
                      <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileSelect} className="hidden" />
                      <Button variant="ghost" size="icon" onClick={() => fileInputRef.current?.click()} className="text-white/40"><Upload className="w-5 h-5" /></Button>
                      <div className="flex-1 text-white/40 text-sm">{uploadedFile ? uploadedFile.name : "Select a document..."}</div>
                      <Button onClick={handleClassify} disabled={!uploadedFile || isClassifying} className="bg-green-500">Classify</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

// ── Classification Card ───────────────────────────────────────
function ClassificationCard({ classification }: { classification: DocumentClassification }) {
  const info = CLASS_LABELS[classification.predicted_class] ?? { label: classification.predicted_class, color: "text-white", icon: "📄" }
  return (
    <div className="mb-4 p-4 bg-white/5 rounded-xl border border-white/10">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center text-2xl">{info.icon}</div>
        <div>
          <p className={`text-lg font-bold ${info.color}`}>{info.label}</p>
          <p className="text-white/60 text-sm">{(classification.confidence * 100).toFixed(1)}% confidence</p>
        </div>
      </div>
      {/* Tu peux rajouter les barres de probabilité ici si tu veux */}
    </div>
  )
}
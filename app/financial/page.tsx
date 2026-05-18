"use client"

import { useState, useRef, useCallback } from "react"
import { GlassmorphismNav } from "@/components/glassmorphism-nav"
import Aurora from "@/components/Aurora"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  TrendingUp,
  Upload,
  FileText,
  Loader2,
  AlertCircle,
  CheckCircle2,
  BarChart3,
  Wallet,
  PackageSearch,
  ArrowUpRight,
  ArrowDownRight,
  Bot,
  Sparkles,
  ChevronRight,
} from "lucide-react"

// ── Types ────────────────────────────────────────────────────
interface PredictionResult {
  statut: string
  tables_trouvees: string[]
  previsions: {
    "2025": Record<string, number>
    "2026": Record<string, number>
  }
  resume: {
    "2025": Record<string, string>
    "2026": Record<string, string>
  }
  targets: string[]
  erreur?: string
}

// ── Helpers ──────────────────────────────────────────────────
function formatDT(val: number): string {
  if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(2)}M DT`
  if (val >= 1_000)     return `${(val / 1_000).toFixed(1)}K DT`
  return `${val.toFixed(0)} DT`
}

function growthRate(v2025: number, v2026: number): number {
  if (!v2025) return 0
  return ((v2026 - v2025) / Math.abs(v2025)) * 100
}

// ── Call Gradio API ───────────────────────────────────────────
async function predictFromPDF(file: File): Promise<PredictionResult> {
  const { Client } = await import("@gradio/client")
  const app = await Client.connect("ferdaouskachouri/financial-app")

  // Forcer le type MIME PDF
  const pdfFile = new File([file], file.name, { type: "application/pdf" })

  const result = await app.predict("/process_pdf", [pdfFile])
  const data = (result as any).data[0] as PredictionResult
  if (data?.erreur) throw new Error(data.erreur)
  return data
}
// ── Sections ──────────────────────────────────────────────────
const SECTIONS = [
  {
    id: "classification",
    label: "Document Classification",
    icon: <FileText className="w-5 h-5" />,
    href: "/financial-advisor",
    description: "Identify financial document types instantly using EfficientNet-B0",
    badge: "Live",
    badgeColor: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    gradient: "from-emerald-500/20 to-teal-500/20",
    border: "border-emerald-500/20 hover:border-emerald-500/40",
  },
  {
    id: "prediction",
    label: "Financial Prediction",
    icon: <TrendingUp className="w-5 h-5" />,
    href: "/financial",
    description: "Upload a PDF — GRU model predicts revenue, results & cash flow 2025-2026",
    badge: "Live",
    badgeColor: "bg-violet-500/20 text-violet-400 border-violet-500/30",
    gradient: "from-violet-500/20 to-purple-500/20",
    border: "border-violet-500/20 hover:border-violet-500/40",
  },
  {
    id: "fiskobot",
    label: "FiskoBot",
    icon: <Bot className="w-5 h-5" />,
    href: "#",
    description: "AI financial assistant — ask questions about your statements and forecasts",
    badge: "Coming soon",
    badgeColor: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    gradient: "from-orange-500/20 to-amber-500/20",
    border: "border-orange-500/20 hover:border-orange-500/40",
  },
]

// ── Metric Card ───────────────────────────────────────────────
interface MetricCardProps {
  icon: React.ReactNode
  label: string
  value2025: number
  value2026: number
  color: string
}

function MetricCard({ icon, label, value2025, value2026, color }: MetricCardProps) {
  const growth     = growthRate(value2025, value2026)
  const isUp       = growth >= 0
  const GrowthIcon = isUp ? ArrowUpRight : ArrowDownRight

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-5 hover:border-white/20 transition-all duration-300 hover:scale-[1.02] group">
      <div className={`absolute -top-6 -right-6 w-24 h-24 rounded-full blur-2xl opacity-20 group-hover:opacity-30 transition-opacity ${color}`} />

      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center bg-white/10 ${color}`}>
          {icon}
        </div>
        <span className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full ${isUp ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
          <GrowthIcon className="w-3 h-3" />
          {Math.abs(growth).toFixed(1)}%
        </span>
      </div>

      <p className="text-white/50 text-xs font-medium uppercase tracking-wider mb-3">{label}</p>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-white/40 text-xs">2025</span>
          <span className="text-white font-bold text-sm">{formatDT(value2025)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-white/40 text-xs">2026</span>
          <span className={`font-bold text-sm ${isUp ? "text-emerald-400" : "text-red-400"}`}>{formatDT(value2026)}</span>
        </div>
      </div>

      <div className="mt-4 h-1 rounded-full bg-white/10 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${isUp ? "bg-emerald-400" : "bg-red-400"}`}
          style={{ width: `${Math.min(100, Math.abs(growth) * 3)}%` }}
        />
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────
export default function FinancialPage() {
  const [file, setFile]             = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isLoading, setIsLoading]   = useState(false)
  const [result, setResult]         = useState<PredictionResult | null>(null)
  const [error, setError]           = useState<string | null>(null)
  const fileInputRef                = useRef<HTMLInputElement>(null)
  const resultRef                   = useRef<HTMLDivElement>(null)

  const handleDragOver  = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragging(true) }, [])
  const handleDragLeave = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragging(false) }, [])
  const handleDrop      = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setIsDragging(false)
    const f = e.dataTransfer.files[0]
    if (f?.name.endsWith(".pdf")) { setFile(f); setResult(null); setError(null) }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) { setFile(f); setResult(null); setError(null) }
  }

  const handleAnalyze = async () => {
    if (!file) return
    setIsLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await predictFromPDF(file)
      setResult(data)
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 200)
    } catch (err: any) {
      setError(err.message ?? "Analysis failed. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const metrics = result ? [
    {
      icon: <BarChart3 className="w-5 h-5" />,
      label: "Revenue",
      value2025: result.previsions["2025"]["resultats_revenus"] ?? 0,
      value2026: result.previsions["2026"]["resultats_revenus"] ?? 0,
      color: "text-violet-400",
    },
    {
      icon: <TrendingUp className="w-5 h-5" />,
      label: "Operating Result",
      value2025: result.previsions["2025"]["resultats_résultat d'exploitation"] ?? 0,
      value2026: result.previsions["2026"]["resultats_résultat d'exploitation"] ?? 0,
      color: "text-blue-400",
    },
    {
      icon: <PackageSearch className="w-5 h-5" />,
      label: "Stocks",
      value2025: result.previsions["2025"]["actif_stocks"] ?? 0,
      value2026: result.previsions["2026"]["actif_stocks"] ?? 0,
      color: "text-emerald-400",
    },
    {
      icon: <Wallet className="w-5 h-5" />,
      label: "Cash Flow",
      value2025: result.previsions["2025"]["flux_variation de trésorerie"] ?? 0,
      value2026: result.previsions["2026"]["flux_variation de trésorerie"] ?? 0,
      color: "text-amber-400",
    },
  ] : []

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      <main className="min-h-screen relative overflow-hidden">
        <div className="fixed inset-0 w-full h-full">
          <Aurora colorStops={["#1e1b4b", "#4c1d95", "#312e81"]} amplitude={1.2} blend={0.6} speed={0.8} />
        </div>

        <div className="relative z-10">
          <GlassmorphismNav />

          <section className="pt-32 pb-16 px-4">
            <div className="max-w-5xl mx-auto space-y-16">

              {/* Hero */}
              <div className="text-center space-y-4">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 text-sm font-medium">
                  <Sparkles className="w-4 h-4 mr-2" />
                  AI Financial Intelligence · GRU Model
                </div>
                <h1 className="text-4xl sm:text-5xl font-bold text-white">
                  Financial{" "}
                  <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
                    Predictions
                  </span>
                </h1>
                <p className="text-white/50 max-w-xl mx-auto text-sm leading-relaxed">
                  Upload any financial PDF — our pipeline extracts tables, reads figures with OCR,
                  and predicts your 2025–2026 performance with a trained GRU neural network.
                </p>
              </div>

              {/* 3 Sections Navigator */}
{/* Navigation Buttons */}
<div className="flex flex-wrap items-center justify-center gap-3">
                <a
                  href="/financial-advisor"
                  className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm font-medium hover:bg-emerald-500/20 transition-all duration-300"
                >
                  <FileText className="w-4 h-4" />
                  Document Classification
                </a>

                <a
                  href="/financial"
                  className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-violet-500/10 border border-violet-500/30 text-violet-300 text-sm font-medium hover:bg-violet-500/20 transition-all duration-300 ring-1 ring-violet-500/40"
                >
                  <TrendingUp className="w-4 h-4" />
                  Financial Prediction · GRU Model
                </a>

                <a href="/fiskobot"
                className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-violet-500/10 border border-violet-500/30 text-orange-300 text-sm font-medium hover:bg-orange-500/20 transition-all duration-300 ring-1 ring-orange-500/40"
  >
    <Bot className="w-4 h-4" />
    FiskoBot 
  </a>
</div>

              {/* Upload Zone */}
              <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                <CardContent className="p-6 space-y-5">
                  <div className="flex items-center gap-2 mb-1">
                    <Upload className="w-4 h-4 text-violet-400" />
                    <span className="text-white font-semibold text-sm">Upload Financial PDF</span>
                  </div>

                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`relative flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-300 py-10
                      ${isDragging
                        ? "border-violet-400 bg-violet-500/10"
                        : file
                          ? "border-emerald-400/50 bg-emerald-500/5"
                          : "border-white/20 hover:border-violet-400/50 hover:bg-white/5"
                      }`}
                  >
                    <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleFileSelect} className="hidden" />
                    {file ? (
                      <>
                        <CheckCircle2 className="w-10 h-10 text-emerald-400" />
                        <div className="text-center">
                          <p className="text-white font-medium text-sm">{file.name}</p>
                          <p className="text-white/40 text-xs mt-1">{(file.size / 1024).toFixed(1)} KB · Click to change</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="w-14 h-14 rounded-2xl bg-violet-500/20 border border-violet-500/30 flex items-center justify-center">
                          <FileText className="w-7 h-7 text-violet-400" />
                        </div>
                        <div className="text-center">
                          <p className="text-white/70 text-sm font-medium">Drop your PDF here</p>
                          <p className="text-white/30 text-xs mt-1">or click to browse · PDF only</p>
                        </div>
                      </>
                    )}
                  </div>

                  <Button
                    onClick={handleAnalyze}
                    disabled={!file || isLoading}
                    className="w-full bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white font-semibold py-3 rounded-xl transition-all duration-300 disabled:opacity-40"
                  >
                    {isLoading ? (
                      <span className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Analyzing PDF…
                      </span>
                    ) : (
                      <span className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4" />
                        Run GRU Analysis
                      </span>
                    )}
                  </Button>

                  {error && (
                    <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-sm">
                      <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      {error}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Results Dashboard */}
              {result && (
                <div ref={resultRef} className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

                  <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    <div>
                      <p className="text-emerald-300 font-semibold text-sm">Analysis Complete</p>
                      <p className="text-white/40 text-xs mt-0.5">
                        Tables detected: {result.tables_trouvees.join(", ")} · GRU predicted 2025 & 2026
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-violet-400" />
                    <h2 className="text-white font-bold text-lg">Predictions 2025 – 2026</h2>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {metrics.map((m) => (
                      <MetricCard key={m.label} {...m} />
                    ))}
                  </div>

                  {/* Summary Table */}
                  <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                    <CardContent className="p-5">
                      <p className="text-white/50 text-xs uppercase tracking-wider font-medium mb-4">Detailed Summary</p>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-white/10">
                              <th className="text-left text-white/40 font-medium pb-3 pr-4">Indicator</th>
                              <th className="text-right text-white/40 font-medium pb-3 pr-4">2025</th>
                              <th className="text-right text-white/40 font-medium pb-3 pr-4">2026</th>
                              <th className="text-right text-white/40 font-medium pb-3">Growth</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-white/5">
                            {metrics.map((m) => {
                              const g = growthRate(m.value2025, m.value2026)
                              return (
                                <tr key={m.label} className="hover:bg-white/5 transition-colors">
                                  <td className="py-3 pr-4">
                                    <div className="flex items-center gap-2">
                                      <span className={m.color}>{m.icon}</span>
                                      <span className="text-white/70">{m.label}</span>
                                    </div>
                                  </td>
                                  <td className="py-3 pr-4 text-right text-white font-medium">{formatDT(m.value2025)}</td>
                                  <td className="py-3 pr-4 text-right text-white font-medium">{formatDT(m.value2026)}</td>
                                  <td className="py-3 text-right">
                                    <span className={`text-xs font-semibold ${g >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                                      {g >= 0 ? "+" : ""}{g.toFixed(1)}%
                                    </span>
                                  </td>
                                </tr>
                              )
                            })}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>

                </div>
              )}

            </div>
          </section>

          <Footer />
        </div>
      </main>
    </div>
  )
}
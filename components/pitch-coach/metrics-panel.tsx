"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { API_CONFIG } from "@/lib/pitch-analyzer-config"
import { AlertCircle, CheckCircle, Loader2, ShieldCheck, Sparkles, TrendingUp } from "lucide-react"

type MetricsPanelProps = {
  isActive: boolean
  isRecording: boolean
}

export function MetricsPanel({ isActive, isRecording }: MetricsPanelProps) {
  const [health, setHealth] = useState<null | { emotion: boolean; stress: boolean }>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadHealth = async () => {
      try {
        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.HEALTH}`)
        const data = await response.json()
        setHealth(data.models_loaded || { emotion: false, stress: false })
      } catch {
        setHealth({ emotion: false, stress: false })
      } finally {
        setLoading(false)
      }
    }

    loadHealth()
  }, [])

  const metrics = [
    { label: "Camera", value: isActive ? "Active" : "Idle", tone: isActive ? "text-emerald-300" : "text-slate-400" },
    { label: "Recording", value: isRecording ? "Live" : "Off", tone: isRecording ? "text-fuchsia-300" : "text-slate-400" },
    { label: "Emotion model", value: health?.emotion ? "Loaded" : "Missing", tone: health?.emotion ? "text-emerald-300" : "text-amber-300" },
    { label: "Stress model", value: health?.stress ? "Loaded" : "Missing", tone: health?.stress ? "text-emerald-300" : "text-amber-300" },
  ]

  return (
    <Card className="border-white/10 bg-white/[0.03] backdrop-blur-xl text-white shadow-2xl shadow-black/20">
      <CardHeader className="border-b border-white/10 bg-white/[0.02]">
        <CardTitle className="flex items-center gap-2 text-lg font-medium">
          <TrendingUp className="h-5 w-5 text-purple-300" />
          Live Analysis
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4 p-4 md:p-5">
        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <ShieldCheck className="h-4 w-4 text-purple-300" />
            Backend health
          </div>
          <div className="mt-3 flex items-center gap-2 text-sm">
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                <span className="text-slate-400">Checking app.py...</span>
              </>
            ) : health?.emotion && health?.stress ? (
              <>
                <CheckCircle className="h-4 w-4 text-emerald-300" />
                <span className="text-emerald-300">Models loaded from backend/app.py</span>
              </>
            ) : (
              <>
                <AlertCircle className="h-4 w-4 text-amber-300" />
                <span className="text-amber-300">Start Flask backend to load the models</span>
              </>
            )}
          </div>
        </div>

        <div className="grid gap-3">
          {metrics.map((metric) => (
            <div key={metric.label} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3">
              <span className="text-sm text-slate-300">{metric.label}</span>
              <span className={`text-sm font-medium ${metric.tone}`}>{metric.value}</span>
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-4 text-sm text-slate-300">
          <div className="flex items-center gap-2 text-slate-100">
            <Sparkles className="h-4 w-4 text-fuchsia-300" />
            Model relation
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            This panel reflects the same Flask models used by <span className="text-slate-200">backend/app.py</span>: emotion and stress are analyzed from webcam frames sent by the camera feed.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

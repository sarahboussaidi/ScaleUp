"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { X, Download } from "lucide-react"

export interface RecordingAnalysisData {
  emotion: Record<string, number>
  stress: Record<string, number>
  posture: Record<string, number>
  voiceEmotion: Record<string, number>
  safety: Record<string, number>
  transcript: string
  duration: number
  timestamp: Date
}

interface AnalysisSummaryProps {
  data: RecordingAnalysisData
  voiceEmotionStatus?: string | null
  onClose: () => void
}

export function AnalysisSummary({ data, voiceEmotionStatus, onClose }: AnalysisSummaryProps) {
  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${minutes}m ${secs}s`
  }

  const getTopEmotion = () => {
    if (Object.keys(data.emotion).length === 0) return { emotion: "No data", count: 0 }
    const [emotion, count] = Object.entries(data.emotion).reduce((a, b) =>
      b[1] > a[1] ? b : a
    )
    return { emotion, count }
  }

  const getTopStress = () => {
    if (Object.keys(data.stress).length === 0) return { stress: "No data", count: 0 }
    const [stress, count] = Object.entries(data.stress).reduce((a, b) =>
      b[1] > a[1] ? b : a
    )
    return { stress, count }
  }

  const getTopPosture = () => {
    if (Object.keys(data.posture).length === 0) return { posture: "No data", count: 0 }
    const [posture, count] = Object.entries(data.posture).reduce((a, b) =>
      b[1] > a[1] ? b : a
    )
    return { posture, count }
  }

  const getTopVoiceEmotion = () => {
    if (Object.keys(data.voiceEmotion).length === 0) return { emotion: "No data", count: 0 }
    const [emotion, count] = Object.entries(data.voiceEmotion).reduce((a, b) =>
      b[1] > a[1] ? b : a
    )
    return { emotion, count }
  }

  const getTopSafety = () => {
    if (Object.keys(data.safety).length === 0) return { label: "No data", count: 0 }
    const [label, count] = Object.entries(data.safety).reduce((a, b) =>
      b[1] > a[1] ? b : a
    )
    return { label, count }
  }

  const downloadReport = () => {
    const report = {
      timestamp: data.timestamp.toISOString(),
      duration: formatDuration(data.duration),
      transcript: data.transcript,
      analysis: {
        facial_emotions: data.emotion,
        voice_emotions: data.voiceEmotion,
        stress_levels: data.stress,
        postures: data.posture,
          safety_checks: data.safety,
      },
      summary: {
        dominant_facial_emotion: getTopEmotion().emotion,
        dominant_voice_emotion: getTopVoiceEmotion().emotion,
        dominant_stress: getTopStress().stress,
        dominant_posture: getTopPosture().posture,
          dominant_safety: getTopSafety().label,
        word_count: data.transcript.split(/\s+/).filter((w) => w).length,
      },
    }

    const element = document.createElement("a")
    element.setAttribute("href", "data:text/plain;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2)))
    element.setAttribute("download", `pitch-analysis-${Date.now()}.json`)
    element.style.display = "none"
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  const topEmotion = getTopEmotion()
  const topVoiceEmotion = getTopVoiceEmotion()
  const topStress = getTopStress()
  const topPosture = getTopPosture()
  const topSafety = getTopSafety()

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden border-white/10 bg-gradient-to-br from-slate-900 to-slate-950 text-white shadow-2xl">
        <CardHeader className="relative border-b border-white/10 bg-white/[0.02]">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <CardTitle className="text-2xl font-bold">Recording Analysis Summary</CardTitle>
              <CardDescription className="text-slate-400">
                Session recorded on {data.timestamp.toLocaleString()}
              </CardDescription>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-2 transition-colors hover:bg-white/10"
              aria-label="Back to page"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </CardHeader>

        <CardContent className="max-h-[calc(90vh-88px)] space-y-6 overflow-y-auto p-6">
          {/* Duration */}
          <div className="rounded-lg border border-purple-500/20 bg-purple-500/10 p-4">
            <p className="text-sm text-slate-400">Recording Duration</p>
            <p className="mt-1 text-3xl font-bold text-purple-300">
              {formatDuration(data.duration)}
            </p>
          </div>

          {/* Grid of main metrics */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
            {/* Dominant Facial Emotion */}
            <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4">
              <p className="text-xs uppercase tracking-wider text-slate-400">Facial Emotion</p>
              <p className="mt-2 text-2xl font-bold capitalize text-blue-300">
                {topEmotion.emotion}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {topEmotion.count} times
              </p>
            </div>

            {/* Dominant Voice Emotion */}
            <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4">
              <p className="text-xs uppercase tracking-wider text-slate-400">Voice Emotion</p>
              <p className="mt-2 text-2xl font-bold capitalize text-rose-300">
                {topVoiceEmotion.emotion}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {topVoiceEmotion.count} times
              </p>
            </div>

            {/* Dominant Stress */}
            <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4">
              <p className="text-xs uppercase tracking-wider text-slate-400">Stress Level</p>
              <p className="mt-2 text-2xl font-bold capitalize text-orange-300">
                {topStress.stress}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {topStress.count} times
              </p>
            </div>

            {/* Dominant Posture */}
            <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4">
              <p className="text-xs uppercase tracking-wider text-slate-400">Best Posture</p>
              <p className="mt-2 text-2xl font-bold capitalize text-green-300">
                {topPosture.posture}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {topPosture.count} times
              </p>
            </div>

            <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4">
              <p className="text-xs uppercase tracking-wider text-slate-400">Bad Words</p>
              <p className="mt-2 text-2xl font-bold capitalize text-red-300">
                {topSafety.label}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {topSafety.count} times
              </p>
            </div>
          </div>

          {/* Detailed breakdown */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Facial Emotions breakdown */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-300">Facial Emotions</h3>
              <div className="space-y-1 rounded-lg border border-slate-700/30 bg-slate-800/20 p-3">
                {Object.entries(data.emotion).length > 0 ? (
                  Object.entries(data.emotion)
                    .sort(([, a], [, b]) => b - a)
                    .map(([emotion, count]) => (
                      <div
                        key={emotion}
                        className="flex items-center justify-between text-xs text-slate-300"
                      >
                        <span className="capitalize">{emotion}</span>
                        <span className="rounded-full bg-blue-500/20 px-2 py-0.5 text-blue-200">
                          {count}x
                        </span>
                      </div>
                    ))
                ) : (
                  <p className="text-xs text-slate-500">No data collected</p>
                )}
              </div>
            </div>

            {/* Voice Emotions breakdown */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-300">Voice Emotions</h3>
              <div className="space-y-1 rounded-lg border border-slate-700/30 bg-slate-800/20 p-3">
                {Object.entries(data.voiceEmotion).length > 0 ? (
                  Object.entries(data.voiceEmotion)
                    .sort(([, a], [, b]) => b - a)
                    .map(([emotion, count]) => (
                      <div
                        key={emotion}
                        className="flex items-center justify-between text-xs text-slate-300"
                      >
                        <span className="capitalize">{emotion}</span>
                        <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-rose-200">
                          {count}x
                        </span>
                      </div>
                    ))
                ) : (
                  <p className="text-xs text-slate-500">
                    {voiceEmotionStatus || "No data collected"}
                  </p>
                )}
              </div>
            </div>

            {/* Stress breakdown */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-300">Stress Levels</h3>
              <div className="space-y-1 rounded-lg border border-slate-700/30 bg-slate-800/20 p-3">
                {Object.entries(data.stress).length > 0 ? (
                  Object.entries(data.stress)
                    .sort(([, a], [, b]) => b - a)
                    .map(([stress, count]) => (
                      <div
                        key={stress}
                        className="flex items-center justify-between text-xs text-slate-300"
                      >
                        <span className="capitalize">{stress}</span>
                        <span className="rounded-full bg-orange-500/20 px-2 py-0.5 text-orange-200">
                          {count}x
                        </span>
                      </div>
                    ))
                ) : (
                  <p className="text-xs text-slate-500">No data collected</p>
                )}
              </div>
            </div>

            {/* Posture breakdown */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-300">Postures Detected</h3>
              <div className="space-y-1 rounded-lg border border-slate-700/30 bg-slate-800/20 p-3">
                {Object.entries(data.posture).length > 0 ? (
                  Object.entries(data.posture)
                    .sort(([, a], [, b]) => b - a)
                    .map(([posture, count]) => (
                      <div
                        key={posture}
                        className="flex items-center justify-between text-xs text-slate-300"
                      >
                        <span className="capitalize">{posture}</span>
                        <span className="rounded-full bg-green-500/20 px-2 py-0.5 text-green-200">
                          {count}x
                        </span>
                      </div>
                    ))
                ) : (
                  <p className="text-xs text-slate-500">No data collected</p>
                )}
              </div>
            </div>
          </div>

          {/* Transcript */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-300">Speech Transcript</h3>
              <span className="text-xs text-slate-500">
                {data.transcript.split(/\s+/).filter((w) => w).length} words
              </span>
            </div>
            <div className="rounded-lg border border-slate-700/50 bg-slate-900/30 p-4 max-h-[200px] overflow-y-auto">
              <p className="text-sm leading-relaxed text-slate-300">
                {data.transcript || "No transcript recorded"}
              </p>
            </div>
            {data.transcript && (
              <button
                onClick={() => {
                  navigator.clipboard.writeText(data.transcript)
                  alert("Transcript copied to clipboard!")
                }}
                className="w-full text-xs text-slate-400 hover:text-slate-200 transition-colors p-2 rounded hover:bg-slate-800/30"
              >
                Copy Transcript
              </button>
            )}
          </div>

          {/* Recommendations */}
          <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-4">
            <h3 className="text-sm font-semibold text-green-300 mb-2">Recommendations</h3>
            <ul className="space-y-1 text-sm text-slate-300">
              {topEmotion.emotion === "nervous" && (
                <li>• Try to relax your facial expressions - take deep breaths before presenting</li>
              )}
              {topStress.stress === "stressed" && (
                <li>• Work on stress management techniques - practice more presentations</li>
              )}
              {topPosture.posture && topPosture.posture !== "good" && (
                <li>• Maintain an upright posture throughout your pitch - practice standing straight</li>
              )}
              <li>• Consider doing more practice runs to improve confidence</li>
            </ul>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              onClick={downloadReport}
              variant="outline"
              className="flex-1 border-white/20 hover:bg-white/10"
            >
              <Download className="mr-2 h-4 w-4" />
              Download Report
            </Button>
            <Button
              onClick={onClose}
              className="flex-1 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
            >
              Back to page
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

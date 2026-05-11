"use client"

import { useState, useCallback, useRef, useEffect, useMemo } from "react"
import dynamic from "next/dynamic"
import { GlassmorphismNav } from "@/components/glassmorphism-nav"
import { CameraFeed } from "@/components/pitch-coach/camera-feed"
import { MetricsPanel } from "@/components/pitch-coach/metrics-panel"
import { PosturePanel } from "@/components/pitch-coach/posture-panel"
import { SpeechTranscription } from "@/components/pitch-coach/speech-transcription"
import { AnalysisDataPoint } from "@/components/pitch-coach/recording-controls"
import { PitchHero } from "@/components/pitch-coach/pitch-hero"
import { AnalysisSummary, RecordingAnalysisData } from "@/components/pitch-coach/analysis-summary"
import { Footer } from "@/components/footer"
import { analyzeVoiceEmotion, analyzeSpeechStrength } from "@/lib/pitch-analyzer-config"

const Aurora = dynamic(() => import("@/components/Aurora"), {
  ssr: false,
})

// ── Slide definitions matching backend SLIDE_TASKS keys exactly ──────────────
const SLIDE_DEFS = [
  { key: "problem",        title: "Problem" },
  { key: "solution",       title: "Solution" },
  { key: "market",         title: "Market" },
  { key: "product",        title: "Product" },
  { key: "business_model", title: "Business Model" },
  { key: "competition",    title: "Competition" },
  { key: "team",           title: "Team" },
  { key: "ask",            title: "Ask" },
]

// Placeholder text shown before generation
const SLIDE_PLACEHOLDERS: Record<string, string> = {
  problem:        "Who has the problem, what is the pain, why does it matter.",
  solution:       "What the product does, how it works, key differentiator.",
  market:         "Who is the target market and why now.",
  product:        "Core features and how users use it.",
  business_model: "How the company makes money.",
  competition:    "Alternatives and why this product wins.",
  team:           "Why this team can build it.",
  ask:            "What support, funding, or partners are needed.",
}

export default function PitchCoachPage() {
  const [activeView, setActiveView] = useState<"pitch-evaluation" | "pitch-deck">("pitch-evaluation")
  const [startupName, setStartupName] = useState("")
  const [industry, setIndustry] = useState("")
  const [startupDescription, setStartupDescription] = useState("")

  // ── FIX: store slides as a key→text record matching backend keys ──────────
  const [generatedSlides, setGeneratedSlides] = useState<Record<string, string>>({})
  const [isGenerating, setIsGenerating] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)

  const [deckEvaluation, setDeckEvaluation] = useState<{ score: number; label: string; feedback: string[] } | null>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [postureData, setPostureData] = useState({ posture: "waiting", confidence: 0 })
  const [recordingAnalysis, setRecordingAnalysis] = useState<RecordingAnalysisData | null>(null)
  const [recordingDuration, setRecordingDuration] = useState(0)
  const [transcription, setTranscription] = useState("")
  const [finalTranscript, setFinalTranscript] = useState("")
  const [speechStrength, setSpeechStrength] = useState<{ label: string; score: number } | null>(null)
  const [speechSafety, setSpeechSafety] = useState<{ label: string; confidence: number } | null>(null)
  const [voiceEmotionStatus, setVoiceEmotionStatus] = useState<string | null>(null)

  const analysisDataRef = useRef<AnalysisDataPoint[]>([])
  const isRecordingRef = useRef(false)
  const recordingStartTimeRef = useRef<number>(0)
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const voiceAudioStreamRef = useRef<MediaStream | null>(null)

  useEffect(() => { isRecordingRef.current = isRecording }, [isRecording])

  useEffect(() => {
    if (isRecording) {
      recordingStartTimeRef.current = Date.now()
      recordingTimerRef.current = setInterval(() => setRecordingDuration((p) => p + 1), 1000)
    } else {
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current)
    }
    return () => { if (recordingTimerRef.current) clearInterval(recordingTimerRef.current) }
  }, [isRecording])

  const handleStreamReady = useCallback((mediaStream: MediaStream) => setStream(mediaStream), [])

  const handleStreamEnd = useCallback(() => {
    setStream(null)
    setIsRecording(false)
    if (voiceAudioStreamRef.current) {
      voiceAudioStreamRef.current.getTracks().forEach((t) => t.stop())
      voiceAudioStreamRef.current = null
    }
  }, [])

  const handleRecordingStart = useCallback(() => {
    setIsRecording(true)
    setRecordingDuration(0)
    setTranscription("")
    setFinalTranscript("")
    setSpeechStrength(null)
    setSpeechSafety(null)
    setVoiceEmotionStatus(null)
    analysisDataRef.current = []
    audioChunksRef.current = []

    if (stream) {
      try {
        const cameraAudioTracks = stream.getAudioTracks()
        const audioStream = cameraAudioTracks.length > 0 ? new MediaStream(cameraAudioTracks) : null

        const startRecorder = (sourceStream: MediaStream) => {
          const preferredMimeTypes = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"]
          const mimeType = preferredMimeTypes.find((t) => MediaRecorder.isTypeSupported(t))
          const mediaRecorder = mimeType ? new MediaRecorder(sourceStream, { mimeType }) : new MediaRecorder(sourceStream)
          mediaRecorderRef.current = mediaRecorder
          mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data) }
          mediaRecorder.start()
        }

        if (audioStream) {
          voiceAudioStreamRef.current = audioStream
          startRecorder(audioStream)
        } else {
          navigator.mediaDevices.getUserMedia({ audio: true, video: false }).then((micStream) => {
            voiceAudioStreamRef.current = micStream
            startRecorder(micStream)
          }).catch((e) => console.error("Microphone access failed:", e))
        }
      } catch (e) {
        console.error("Failed to start MediaRecorder:", e)
      }
    }
  }, [stream])

  const handleRecordingStop = useCallback(async () => {
    setIsRecording(false)
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      await new Promise<void>((resolve) => {
        const recorder = mediaRecorderRef.current
        if (!recorder) { resolve(); return }
        recorder.onstop = () => resolve()
        recorder.stop()
      })
    }
    if (voiceAudioStreamRef.current) {
      voiceAudioStreamRef.current.getTracks().forEach((t) => t.stop())
      voiceAudioStreamRef.current = null
    }

    const analysisData = analysisDataRef.current
    const emotionCounts: Record<string, number> = {}
    const stressCounts: Record<string, number> = {}
    const postureCounts: Record<string, number> = {}
    let safetyCounts: Record<string, number> = {}

    analysisData.forEach((dp) => {
      if (dp.emotion) emotionCounts[dp.emotion] = (emotionCounts[dp.emotion] || 0) + 1
      if (dp.stress) stressCounts[dp.stress] = (stressCounts[dp.stress] || 0) + 1
      if (dp.posture) postureCounts[dp.posture] = (postureCounts[dp.posture] || 0) + 1
    })

    let voiceEmotionAnalysis: Record<string, number> = {}
    let transcriptFromAnalysis = transcription

    if (audioChunksRef.current && audioChunksRef.current.length > 0) {
      try {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })
        const [voiceEmotionResult, speechStrengthResult] = await Promise.allSettled([
          analyzeVoiceEmotion(audioBlob, 15000),
          analyzeSpeechStrength(audioBlob, 45000),
        ])

        if (voiceEmotionResult.status === "fulfilled" && voiceEmotionResult.value && !voiceEmotionResult.value.error) {
          if (voiceEmotionResult.value.emotion) {
            voiceEmotionAnalysis[voiceEmotionResult.value.emotion] = 1
          }
        } else if (voiceEmotionResult.status === "rejected") {
          setVoiceEmotionStatus("Voice emotion analysis failed: request timed out or was aborted.")
        }

        if (speechStrengthResult.status === "fulfilled" && speechStrengthResult.value && !speechStrengthResult.value.error) {
          if (speechStrengthResult.value.prediction) {
            setSpeechStrength({ label: speechStrengthResult.value.prediction.label, score: speechStrengthResult.value.prediction.final_score })
          }
          if (speechStrengthResult.value.bad_words) {
            const safetyResult = { label: speechStrengthResult.value.bad_words.label, confidence: speechStrengthResult.value.bad_words.confidence }
            setSpeechSafety(safetyResult)
            safetyCounts = safetyResult.label ? { [safetyResult.label]: 1 } : {}
          }
          if (speechStrengthResult.value.transcript) {
            transcriptFromAnalysis = speechStrengthResult.value.transcript
            setTranscription(speechStrengthResult.value.transcript)
            setFinalTranscript(speechStrengthResult.value.transcript)
          }
        }
      } catch (e) {
        console.error("Failed to analyze voice audio:", e)
      }
    } else {
      setVoiceEmotionStatus("No audio was captured. Check microphone permission.")
    }

    setRecordingAnalysis({
      emotion: emotionCounts,
      stress: stressCounts,
      posture: postureCounts,
      voiceEmotion: voiceEmotionAnalysis,
      safety: safetyCounts,
      transcript: transcriptFromAnalysis,
      duration: recordingDuration * 1000,
      timestamp: new Date(),
    })
  }, [recordingDuration, transcription])

  const handleAnalysisUpdate = useCallback((payload: {
    emotion?: string
    emotionConfidence?: number
    stress?: string
    stressConfidence?: number
    posture?: string
    postureConfidence?: number
    modelStatus?: string
  }) => {
    const normalizeStress = (v?: string) => {
      if (!v) return undefined
      if (v === "stress") return "stressed"
      if (v === "not_stress") return "not stressed"
      return v
    }
    if (payload.posture && payload.postureConfidence !== undefined) {
      setPostureData({ posture: payload.posture, confidence: payload.postureConfidence })
    }
    if (isRecordingRef.current) {
      analysisDataRef.current.push({
        emotion: payload.emotion === "no_face" ? undefined : payload.emotion,
        stress: payload.stress === "unknown" ? undefined : normalizeStress(payload.stress),
        posture: payload.posture,
        timestamp: Date.now() - recordingStartTimeRef.current,
      })
    }
  }, [])

  // ── FIX: handleGeneratePitchDeck — calls real backend, stores slides by key ─
  const handleGeneratePitchDeck = useCallback(async () => {
    const company = startupName.trim() || "Your Startup"
    const sector = industry.trim() || "your industry"
    const desc = startupDescription.trim() || "a clear solution to a real problem"

    setIsGenerating(true)
    setGenerateError(null)
    setGeneratedSlides({})
    setDeckEvaluation(null)

    try {
      const API_BASE = `http://${window.location.hostname}:5000`
      const res = await fetch(`${API_BASE}/api/pitch/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company, industry: sector, description: desc }),
      })

      if (!res.ok) throw new Error(`Server error ${res.status}: ${res.statusText}`)

      const data = await res.json()
      if (data.error) throw new Error(data.error)
      if (!data.slides || typeof data.slides !== "object") throw new Error("No slides returned from server")

      // data.slides is already { problem: "...", solution: "...", ... }
      setGeneratedSlides(data.slides as Record<string, string>)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error"
      setGenerateError(msg)
      console.error("Pitch deck generation failed:", msg)
    } finally {
      setIsGenerating(false)
    }
  }, [startupName, industry, startupDescription])

  // ── FIX: handleDownloadPptx — calls /api/pitch/download and triggers download
  const handleDownloadPptx = useCallback(async () => {
    const company = startupName.trim() || "Your Startup"
    const sector = industry.trim() || "your industry"
    const desc = startupDescription.trim() || "a clear solution to a real problem"

    setIsDownloading(true)
    setGenerateError(null)

    try {
      const API_BASE = `http://${window.location.hostname}:5000`
      const res = await fetch(`${API_BASE}/api/pitch/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company, industry: sector, description: desc }),
      })

      if (!res.ok) throw new Error(`Download failed: ${res.status}`)

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${company.replace(/\s+/g, "_")}_pitch_deck.pptx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Download failed"
      setGenerateError(msg)
    } finally {
      setIsDownloading(false)
    }
  }, [startupName, industry, startupDescription])

  const handleEvaluatePitchDeck = useCallback(() => {
    const hasSlides = Object.keys(generatedSlides).length > 0
    const checks = [
      startupName.trim().length > 2,
      industry.trim().length > 2,
      startupDescription.trim().length > 20,
      hasSlides,
    ]
    const score = Math.round((checks.filter(Boolean).length / checks.length) * 100)
    const label = score >= 80 ? "Strong" : score >= 50 ? "Moderate" : "Weak"
    const feedback: string[] = []
    if (!startupName.trim()) feedback.push("Add your startup name.")
    if (!industry.trim()) feedback.push("Specify the industry.")
    if (!startupDescription.trim()) feedback.push("Add a short description of the problem and solution.")
    if (!hasSlides) feedback.push("Generate the pitch deck first.")
    if (feedback.length === 0) {
      feedback.push("Your pitch deck inputs look complete.")
      feedback.push("You can now refine the wording of each slide.")
    }
    setDeckEvaluation({ score, label, feedback })
  }, [generatedSlides, industry, startupDescription, startupName])

  const hasSlides = Object.keys(generatedSlides).length > 0

  return (
    <div className="relative min-h-screen overflow-auto bg-[#0a0a14]">
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a1033] via-[#0f0a1f] to-[#0a0a14]" />
        <div className="absolute top-0 left-1/4 h-[600px] w-[600px] rounded-full bg-purple-600/20 blur-[120px]" />
        <div className="absolute right-1/4 top-1/4 h-[400px] w-[400px] rounded-full bg-violet-500/15 blur-[100px]" />
        <div className="absolute bottom-1/3 left-1/3 h-[300px] w-[300px] rounded-full bg-fuchsia-600/10 blur-[80px]" />
        <Aurora colorStops={["#12091f", "#27123d", "#0d0b18"]} amplitude={1.15} blend={0.58} speed={0.75} />
      </div>

      <GlassmorphismNav />

      <main className="relative z-10">
        <PitchHero />

        {/* View toggle */}
        <section className="px-4 pb-6 md:px-8">
          <div className="mx-auto flex max-w-3xl items-center justify-center gap-3 rounded-full border border-white/[0.08] bg-white/[0.04] p-2 backdrop-blur-sm">
            <button
              type="button"
              onClick={() => setActiveView("pitch-evaluation")}
              className={`rounded-full px-5 py-2 text-sm font-medium transition-all ${
                activeView === "pitch-evaluation"
                  ? "bg-purple-500 text-white shadow-lg shadow-purple-500/20"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              Pitch Evaluation
            </button>
            <button
              type="button"
              onClick={() => setActiveView("pitch-deck")}
              className={`rounded-full px-5 py-2 text-sm font-medium transition-all ${
                activeView === "pitch-deck"
                  ? "bg-purple-500 text-white shadow-lg shadow-purple-500/20"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              Pitch Deck
            </button>
          </div>
        </section>

        {/* ── Pitch Evaluation view ── */}
        {activeView === "pitch-evaluation" ? (
          <section className="px-4 pb-20 md:px-8">
            <div className="mx-auto max-w-7xl">
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                <div className="space-y-4 lg:col-span-2">
                  <CameraFeed
                    onStreamReady={handleStreamReady}
                    onStreamEnd={handleStreamEnd}
                    isRecording={isRecording}
                    onAnalysisUpdate={handleAnalysisUpdate}
                  />
                  <SpeechTranscription
                    isRecording={isRecording}
                    onTranscriptionUpdate={setTranscription}
                    onFinalTranscript={setTranscription}
                    stream={stream}
                    onRecordingStart={handleRecordingStart}
                    onRecordingStop={handleRecordingStop}
                    recordingDuration={recordingDuration}
                    speechStrength={speechStrength}
                    speechSafety={speechSafety}
                  />
                </div>
                <div className="lg:col-span-1">
                  <div className="lg:sticky lg:top-28 space-y-4">
                    <h3 className="mb-4 flex items-center gap-2 text-sm font-medium text-slate-200">
                      <span className="relative flex h-2 w-2">
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-purple-400 opacity-75" />
                        <span className="relative inline-flex h-2 w-2 rounded-full bg-purple-500" />
                      </span>
                      Live Analysis
                    </h3>
                    <MetricsPanel isActive={!!stream} isRecording={isRecording} />
                    <PosturePanel isActive={!!stream} isRecording={isRecording} postureData={postureData} />
                  </div>
                </div>
              </div>
            </div>
          </section>

        ) : (
          /* ── Pitch Deck view ── */
          <section className="px-4 pb-20 md:px-8">
            <div className="mx-auto max-w-7xl">
              <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 backdrop-blur-sm md:p-8">

                {/* Header */}
                <div className="mb-8 flex items-center justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-semibold text-white md:text-3xl">Pitch Deck Generator</h2>
                    <p className="mt-2 max-w-2xl text-sm text-slate-400">
                      Fill in your startup details and click Generate. The AI model will write each slide.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setActiveView("pitch-evaluation")}
                    className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-200 transition hover:bg-white/5"
                  >
                    Back to evaluation
                  </button>
                </div>

                {/* Form */}
                <div className="mb-8 grid grid-cols-1 gap-4 rounded-2xl border border-white/[0.08] bg-black/20 p-5 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-200">Startup name</label>
                    <input
                      value={startupName}
                      onChange={(e) => setStartupName(e.target.value)}
                      placeholder="e.g. ScaleUp"
                      className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-purple-500/50"
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-200">Industry</label>
                    <input
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                      placeholder="e.g. AI, HealthTech, FinTech"
                      className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-purple-500/50"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="mb-2 block text-sm font-medium text-slate-200">Short description</label>
                    <textarea
                      value={startupDescription}
                      onChange={(e) => setStartupDescription(e.target.value)}
                      placeholder="Write a short sentence about the problem you solve..."
                      rows={4}
                      className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-purple-500/50"
                    />
                  </div>

                  {/* Error message */}
                  {generateError && (
                    <div className="md:col-span-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                      ⚠ {generateError}
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="md:col-span-2 flex flex-wrap items-center justify-end gap-3">
                    {/* Download PPTX — only shown after slides are generated */}
                    {hasSlides && (
                      <button
                        type="button"
                        onClick={handleDownloadPptx}
                        disabled={isDownloading}
                        className="flex items-center gap-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-5 py-3 text-sm font-semibold text-purple-200 transition hover:bg-purple-500/20 disabled:opacity-50"
                      >
                        {isDownloading ? (
                          <>
                            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-purple-300 border-t-transparent" />
                            Exporting…
                          </>
                        ) : (
                          "⬇ Download PPTX"
                        )}
                      </button>
                    )}

                    {/* Generate button */}
                    <button
                      type="button"
                      onClick={handleGeneratePitchDeck}
                      disabled={isGenerating}
                      className="flex items-center gap-2 rounded-full bg-purple-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-purple-400 disabled:opacity-60"
                    >
                      {isGenerating ? (
                        <>
                          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                          Generating… (this may take a minute)
                        </>
                      ) : (
                        "Generate Pitch Deck"
                      )}
                    </button>
                  </div>
                </div>

                {/* ── Slide cards — FIX: use generatedSlides[key] directly ── */}
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {/* Cover slide always shown first, built from inputs */}
                  <div className="rounded-xl border border-purple-500/20 bg-black/20 p-5">
                    <p className="text-xs uppercase tracking-[0.2em] text-purple-300">Slide — Cover</p>
                    <h3 className="mt-2 text-lg font-semibold text-white">
                      {startupName.trim() || "Your Startup"}
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-slate-400">
                      {startupName.trim()
                        ? `${startupName.trim()} · ${industry.trim() || "Industry"}`
                        : "Add your startup name and industry above."}
                      {startupDescription.trim() ? ` — ${startupDescription.trim().slice(0, 100)}…` : ""}
                    </p>
                  </div>

                  {/* AI-generated slides */}
                  {SLIDE_DEFS.map((slide) => {
                    const text = generatedSlides[slide.key]
                    const isReady = !!text
                    return (
                      <div
                        key={slide.key}
                        className={`rounded-xl border p-5 transition-all ${
                          isReady
                            ? "border-purple-500/30 bg-black/20"
                            : "border-white/[0.08] bg-black/20"
                        }`}
                      >
                        <p className="text-xs uppercase tracking-[0.2em] text-purple-300">
                          Slide — {slide.title}
                        </p>
                        <h3 className="mt-2 text-lg font-semibold text-white">{slide.title}</h3>

                        {isGenerating && !isReady ? (
                          <div className="mt-3 flex items-center gap-2 text-sm text-slate-500">
                            <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-purple-400 border-t-transparent" />
                            Generating…
                          </div>
                        ) : (
                          <p className={`mt-2 text-sm leading-relaxed ${isReady ? "text-slate-200" : "text-slate-500"}`}>
                            {text || SLIDE_PLACEHOLDERS[slide.key]}
                          </p>
                        )}
                      </div>
                    )
                  })}
                </div>

                {/* Evaluate section */}
                <div className="mt-8 rounded-2xl border border-white/[0.08] bg-black/20 p-5">
                  <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.2em] text-purple-300">Evaluate</p>
                      <h3 className="mt-2 text-xl font-semibold text-white">Pitch deck evaluation</h3>
                      <p className="mt-2 text-sm text-slate-400">
                        Check whether the essential inputs are ready before you present.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handleEvaluatePitchDeck}
                      className="rounded-full border border-purple-500/30 bg-purple-500/10 px-5 py-3 text-sm font-semibold text-purple-200 transition hover:bg-purple-500/20"
                    >
                      Evaluate Pitch Deck
                    </button>
                  </div>

                  {deckEvaluation ? (
                    <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-[220px_1fr]">
                      <div className={`rounded-2xl p-5 text-center ${
                        deckEvaluation.label === "Weak"
                          ? "bg-red-600/20"
                          : deckEvaluation.label === "Moderate"
                          ? "bg-orange-500/20"
                          : "bg-green-600/20"
                      }`}>
                        <p className="text-sm text-slate-300">Overall score</p>
                        <p className="mt-2 text-4xl font-bold text-white">{deckEvaluation.score}</p>
                        <p className="mt-2 text-sm font-semibold text-white">{deckEvaluation.label}</p>
                      </div>
                      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                        <p className="text-sm font-medium text-slate-200">Feedback</p>
                        <ul className="mt-3 space-y-2 text-sm text-slate-400">
                          {deckEvaluation.feedback.map((item) => (
                            <li key={item} className="rounded-lg bg-black/20 px-3 py-2">{item}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ) : (
                    <p className="mt-5 text-sm text-slate-500">
                      Click <span className="text-slate-200">Evaluate Pitch Deck</span> to see the assessment.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </section>
        )}

        {/* How it works */}
        <section className="px-4 py-20 md:px-8">
          <div className="mx-auto max-w-5xl">
            <h2 className="mb-4 text-center text-2xl font-semibold text-white md:text-3xl">How It Works</h2>
            <p className="mx-auto mb-12 max-w-xl text-center text-slate-400">
              Three simple steps to perfect your investor pitch with your Flask models.
            </p>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              {[
                { n: "1", title: "Enable Camera", desc: "Allow camera and microphone access to start your practice session." },
                { n: "2", title: "Practice Your Pitch", desc: "Deliver your pitch while webcam frames are analyzed by backend/app.py." },
                { n: "3", title: "Review & Improve", desc: "Use emotion and stress models to review and improve your performance over time." },
              ].map(({ n, title, desc }) => (
                <div key={n} className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-6 text-center backdrop-blur-sm transition-all hover:border-purple-500/30 hover:bg-white/[0.05]">
                  <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl border border-purple-500/20 bg-purple-500/10">
                    <span className="text-lg font-semibold text-purple-400">{n}</span>
                  </div>
                  <h3 className="mb-2 font-medium text-slate-200">{title}</h3>
                  <p className="text-sm leading-relaxed text-slate-400">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Model stack */}
        <section className="px-4 pb-20 md:px-8">
          <div className="mx-auto max-w-5xl">
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 backdrop-blur-sm md:p-8">
              <h2 className="text-center text-2xl font-semibold text-white md:text-3xl">Backend Model Stack</h2>
              <p className="mx-auto mt-4 max-w-2xl text-center text-slate-400">
                Connected to <span className="text-slate-200">backend/app.py</span> and <span className="text-slate-200">pitch_generator.py</span>.
              </p>
              <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[
                  { label: "Emotion", name: "emotion_model.h5", desc: "Face emotion classifier via /api/analyze/emotion." },
                  { label: "Stress", name: "stress_cnn_73.h5", desc: "Stress model via /api/analyze/stress." },
                  { label: "Pitch Gen", name: "didina01/pitch-deck-phi3", desc: "Fine-tuned Phi-3 model via /api/pitch/generate." },
                  { label: "Health", name: "/api/health", desc: "Checks if Flask models are loaded correctly." },
                ].map(({ label, name, desc }) => (
                  <div key={label} className="rounded-xl border border-white/[0.08] bg-black/20 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-purple-300">{label}</p>
                    <p className="mt-2 text-lg font-medium text-white">{name}</p>
                    <p className="mt-2 text-sm text-slate-400">{desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />

      {recordingAnalysis && (
        <AnalysisSummary
          data={recordingAnalysis}
          voiceEmotionStatus={voiceEmotionStatus}
          onClose={() => setRecordingAnalysis(null)}
        />
      )}
    </div>
  )
}

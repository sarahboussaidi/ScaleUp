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

const STYLING_PROFILE_FIELDS = [
  { key: "Hair Color", label: "Hair color", options: ["Black", "Blonde", "Brown", "Grey", "Red"] },
  { key: "Eye Color", label: "Eye color", options: ["Black", "Blue", "Brown", "Green", "Grey", "Hazel", "Light Blue", "Light Brown"] },
  { key: "Skin Tone", label: "Skin tone", options: ["Brown", "Fair", "Medium", "Olive", "Very Dark", "Very Fair"] },
  { key: "Under Tone", label: "Undertone", options: ["Cool", "Neutral", "Warm"] },
  { key: "Torso length", label: "Torso length", options: ["Balanced", "Long Torso", "Short Torso"] },
  { key: "Body Proportion", label: "Body proportion", options: ["Apple", "Hourglass", "Inverted Triangle", "Oval", "Rectangle", "Trapezoid", "Triangle"] },
]

const VOICE_EMOTION_ANALYSIS_TIMEOUT_MS = 45000

type StylingVerdictResult = {
  verdict: string
  is_good: boolean
  pitch_day_summary: string
  predictions: Record<string, string>
  confidence: Record<string, number>
  recommended_color_families: string[]
  reasons: string[]
  confidence_score?: number
  photo_analysis?: {
    face_detected?: boolean
    face_box?: { x: number; y: number; w: number; h: number }
    labels: string[]
    dominant_label: string
    brightness: number
    confidence: number
    reason: string
    regions?: {
      eyes?: { labels: string[]; dominant_label: string; brightness: number; confidence: number }
      skin?: { labels: string[]; dominant_label: string; brightness: number; confidence: number }
      clothes?: { labels: string[]; dominant_label: string; brightness: number; confidence: number }
    }
  }
  checks: Record<string, any>
}

export default function PitchCoachPage() {
  const [activeView, setActiveView] = useState<"pitch-evaluation" | "pitch-deck">("pitch-evaluation")
  const [startupName, setStartupName] = useState("")
  const [industry, setIndustry] = useState("")
  const [startupDescription, setStartupDescription] = useState("")
  const [stylingProfile, setStylingProfile] = useState({
    "Hair Color": "Brown",
    "Eye Color": "Hazel",
    "Skin Tone": "Medium",
    "Under Tone": "Warm",
    "Torso length": "Balanced",
    "Body Proportion": "Hourglass",
  })

  // ── FIX: store slides as a key→text record matching backend keys ──────────
  const [generatedSlides, setGeneratedSlides] = useState<Record<string, string>>({})
  const [isGenerating, setIsGenerating] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const [isStylingChecking, setIsStylingChecking] = useState(false)
  const [stylingError, setStylingError] = useState<string | null>(null)
  const [stylingResult, setStylingResult] = useState<StylingVerdictResult | null>(null)
  const [stylingPhotoPreview, setStylingPhotoPreview] = useState<string | null>(null)
  const [stylingPhotoFile, setStylingPhotoFile] = useState<File | null>(null)
  const [isStylingCameraOn, setIsStylingCameraOn] = useState(false)
  const [stylingCameraError, setStylingCameraError] = useState<string | null>(null)

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
  const stylingVideoRef = useRef<HTMLVideoElement | null>(null)
  const stylingCameraStreamRef = useRef<MediaStream | null>(null)
  const stylingPhotoInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    return () => {
      if (stylingCameraStreamRef.current) {
        stylingCameraStreamRef.current.getTracks().forEach((track) => track.stop())
        stylingCameraStreamRef.current = null
      }
      if (stylingPhotoPreview) {
        URL.revokeObjectURL(stylingPhotoPreview)
      }
    }
  }, [stylingPhotoPreview])

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
    isRecordingRef.current = true
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
        const startRecorder = (sourceStream: MediaStream) => {
          const preferredMimeTypes = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"]
          const mimeType = preferredMimeTypes.find((t) => MediaRecorder.isTypeSupported(t))
          const mediaRecorder = mimeType ? new MediaRecorder(sourceStream, { mimeType }) : new MediaRecorder(sourceStream)
          mediaRecorderRef.current = mediaRecorder
          mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
              audioChunksRef.current.push(e.data)
            }
          }
          // Emit chunks periodically so we don't depend on a single stop event.
          mediaRecorder.start(1000)
        }

        navigator.mediaDevices.getUserMedia({ audio: true, video: false })
          .then((micStream) => {
            voiceAudioStreamRef.current = micStream
            startRecorder(micStream)
            setVoiceEmotionStatus("Microphone recording started.")
          })
          .catch((e) => {
            console.error("Microphone access failed:", e)
            setVoiceEmotionStatus("Microphone access failed. Check mic permission.")
          })
      } catch (e) {
        console.error("Failed to start MediaRecorder:", e)
      }
    }
  }, [stream])

  const handleRecordingStop = useCallback(async () => {
    setIsRecording(false)
    isRecordingRef.current = false
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      await new Promise<void>((resolve) => {
        const recorder = mediaRecorderRef.current
        if (!recorder) { resolve(); return }
        try {
          // Force the last buffered chunk to be emitted before stopping.
          recorder.requestData()
        } catch (e) {
          console.warn("requestData() failed before stop:", e)
        }
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
          analyzeVoiceEmotion(audioBlob, VOICE_EMOTION_ANALYSIS_TIMEOUT_MS),
          analyzeSpeechStrength(audioBlob, 45000),
        ])

        if (voiceEmotionResult.status === "fulfilled" && voiceEmotionResult.value && !voiceEmotionResult.value.error) {
          if (voiceEmotionResult.value.emotion) {
            voiceEmotionAnalysis[voiceEmotionResult.value.emotion] = 1
          } else {
            setVoiceEmotionStatus("Voice emotion API returned no emotion.")
          }
        } else if (voiceEmotionResult.status === "rejected") {
          setVoiceEmotionStatus("Voice emotion analysis unavailable for this recording.")
        } else {
          setVoiceEmotionStatus("Voice emotion analysis returned an empty result.")
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
      voiceEmotionAnalysis["no audio captured"] = 1
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
        credentials: "include",
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
        credentials: "include",
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

  const clearStylingPhoto = useCallback(() => {
    if (stylingPhotoPreview) {
      URL.revokeObjectURL(stylingPhotoPreview)
    }
    setStylingPhotoPreview(null)
    setStylingPhotoFile(null)
    setStylingCameraError(null)
  }, [stylingPhotoPreview])

  const handleStylingCameraStart = useCallback(async () => {
    setStylingCameraError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      stylingCameraStreamRef.current = stream
      if (stylingVideoRef.current) {
        stylingVideoRef.current.srcObject = stream
        await stylingVideoRef.current.play().catch(() => undefined)
      }
      setIsStylingCameraOn(true)
    } catch (error) {
      console.error("Failed to start styling camera:", error)
      setStylingCameraError("Camera access failed. Use photo upload instead.")
      setIsStylingCameraOn(false)
    }
  }, [])

  const handleStylingCameraStop = useCallback(() => {
    if (stylingCameraStreamRef.current) {
      stylingCameraStreamRef.current.getTracks().forEach((track) => track.stop())
      stylingCameraStreamRef.current = null
    }
    if (stylingVideoRef.current) {
      stylingVideoRef.current.srcObject = null
    }
    setIsStylingCameraOn(false)
  }, [])

  const handleStylingUploadClick = useCallback(() => {
    stylingPhotoInputRef.current?.click()
  }, [])

  const handleStylingPhotoChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ""
    if (!file) return

    clearStylingPhoto()
    const previewUrl = URL.createObjectURL(file)
    setStylingPhotoPreview(previewUrl)
    setStylingPhotoFile(file)
  }, [clearStylingPhoto])

  const handleStylingCapture = useCallback(() => {
    const video = stylingVideoRef.current
    if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
      setStylingCameraError("Camera is not ready yet.")
      return
    }

    const canvas = document.createElement("canvas")
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const context = canvas.getContext("2d")
    if (!context) {
      setStylingCameraError("Unable to capture the camera frame.")
      return
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height)
    canvas.toBlob((blob) => {
      if (!blob) {
        setStylingCameraError("Unable to create a photo from the camera.")
        return
      }
      clearStylingPhoto()
      const capturedFile = new File([blob], `styling-photo-${Date.now()}.jpg`, { type: "image/jpeg" })
      const previewUrl = URL.createObjectURL(capturedFile)
      setStylingPhotoPreview(previewUrl)
      setStylingPhotoFile(capturedFile)
      handleStylingCameraStop()
    }, "image/jpeg", 0.92)
  }, [clearStylingPhoto, handleStylingCameraStop])

  const handleStylingCheck = useCallback(async () => {
    setIsStylingChecking(true)
    setStylingError(null)
    setStylingResult(null)

    try {
      const API_BASE = `http://${window.location.hostname}:5000`
      if (!stylingPhotoFile) throw new Error("Please upload or capture a photo first.")

      const formData = new FormData()
      formData.append("profile", JSON.stringify(stylingProfile))
      formData.append("image", stylingPhotoFile)

      const res = await fetch(`${API_BASE}/api/styling/pitch-day/check-photo`, {
        method: "POST",
        credentials: "include",
        body: formData,
      })

      if (!res.ok) throw new Error(`Server error ${res.status}: ${res.statusText}`)

      const data = await res.json()
      if (data.error) throw new Error(data.error)

      setStylingResult({
        verdict: data.verdict,
        is_good: data.is_good,
        pitch_day_summary: data.pitch_day_summary,
        predictions: data.predictions || {},
        confidence: data.confidence || {},
        recommended_color_families: data.recommended_color_families || [],
        reasons: data.reasons || [],
        checks: data.checks || {},
        confidence_score: data.confidence_score,
        photo_analysis: data.photo_analysis,
      })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error"
      setStylingError(msg)
      console.error("Styling verdict failed:", msg)
    } finally {
      setIsStylingChecking(false)
    }
  }, [stylingPhotoFile, stylingProfile])

  const hasSlides = Object.keys(generatedSlides).length > 0

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      <main className="min-h-screen relative overflow-hidden">
        <div className="fixed inset-0 w-full h-full">
          <Aurora colorStops={["#1e1b4b", "#4c1d95", "#312e81"]} amplitude={1.2} blend={0.6} speed={0.8} />
        </div>

        <div className="relative z-10">
          <GlassmorphismNav />
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

              <div className="mt-8 rounded-2xl border border-white/[0.08] bg-black/20 p-5">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-purple-300">Style</p>
                    <h3 className="mt-2 text-xl font-semibold text-white">Validate clothes before pitch</h3>
                    <p className="mt-2 text-sm text-slate-400">
                      Upload a photo or start the webcam, then validate if the outfit is good or not for pitch day.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleStylingCheck}
                    className="rounded-full border border-purple-500/30 bg-purple-500/10 px-5 py-3 text-sm font-semibold text-purple-200 transition hover:bg-purple-500/20 disabled:opacity-60"
                    disabled={isStylingChecking}
                  >
                    {isStylingChecking ? "Validating clothes…" : "Validate Clothes"}
                  </button>
                </div>

                <div className="mt-5 grid grid-cols-1 gap-6 lg:grid-cols-2">
                  <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                    <p className="text-sm font-medium text-slate-200">Profile inputs</p>
                    <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                      {STYLING_PROFILE_FIELDS.map((field) => (
                        <label key={field.key} className="block">
                          <span className="mb-2 block text-xs uppercase tracking-[0.16em] text-slate-400">{field.label}</span>
                          <select
                            value={stylingProfile[field.key as keyof typeof stylingProfile]}
                            onChange={(e) => setStylingProfile((prev) => ({ ...prev, [field.key]: e.target.value }))}
                            className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-3 text-sm text-white outline-none focus:border-purple-500/50"
                          >
                            {field.options.map((option) => (
                              <option key={option} value={option} className="bg-slate-900">
                                {option}
                              </option>
                            ))}
                          </select>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                    <p className="text-sm font-medium text-slate-200">Photo validation</p>
                    <p className="mt-2 text-sm text-slate-400">
                      Use the webcam or upload a photo. The model checks the colors in the image and tells you if the outfit is good or not.
                    </p>

                    <div className="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-black/30">
                      {stylingPhotoPreview ? (
                        <img
                          src={stylingPhotoPreview}
                          alt="Outfit preview"
                          className="h-64 w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-64 items-center justify-center px-6 text-center text-sm text-slate-500">
                          No outfit photo yet. Start the camera or upload an image to validate before pitching.
                        </div>
                      )}
                      <video ref={stylingVideoRef} className={`h-64 w-full object-cover ${isStylingCameraOn ? "block" : "hidden"}`} playsInline muted />

                        {stylingResult && (
                          <div className="mt-4 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                            <div className="flex items-center justify-between gap-3">
                              <div>
                                <p className="text-xs uppercase tracking-[0.18em] text-purple-300">Style report</p>
                                <p className="mt-1 text-sm text-slate-400">Camera and outfit validation in the first report panel.</p>
                              </div>
                              <div className={`rounded-full px-3 py-1 text-xs font-semibold ${stylingResult.is_good ? "bg-green-500/15 text-green-200" : "bg-red-500/15 text-red-200"}`}>
                                {stylingResult.is_good ? "Bon" : "Pas bon"}
                              </div>
                            </div>

                            <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
                              <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
                                <p className="text-xs uppercase tracking-[0.14em] text-slate-400">Verdict</p>
                                <p className="mt-1 text-sm text-white">{stylingResult.verdict}</p>
                              </div>
                              <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
                                <p className="text-xs uppercase tracking-[0.14em] text-slate-400">Confidence</p>
                                <p className="mt-1 text-sm text-white">
                                  {typeof stylingResult.confidence_score === "number" ? `${Math.round(stylingResult.confidence_score * 100)}%` : "n/a"}
                                </p>
                              </div>
                            </div>

                            <p className="mt-3 text-sm text-slate-400">{stylingResult.pitch_day_summary}</p>
                          </div>
                        )}
                    </div>

                    <input
                      ref={stylingPhotoInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleStylingPhotoChange}
                      className="hidden"
                    />

                    <div className="mt-4 flex flex-wrap gap-3">
                      <button
                        type="button"
                        onClick={handleStylingCameraStart}
                        className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-white transition hover:bg-white/[0.08]"
                      >
                        Start webcam
                      </button>
                      <button
                        type="button"
                        onClick={handleStylingCapture}
                        disabled={!isStylingCameraOn}
                        className="rounded-full border border-purple-500/30 bg-purple-500/10 px-4 py-2 text-sm font-semibold text-purple-200 transition hover:bg-purple-500/20 disabled:opacity-50"
                      >
                        Capture photo
                      </button>
                      <button
                        type="button"
                        onClick={handleStylingUploadClick}
                        className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-white transition hover:bg-white/[0.08]"
                      >
                        Upload photo
                      </button>
                      <button
                        type="button"
                        onClick={clearStylingPhoto}
                        className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-slate-300 transition hover:bg-white/[0.08]"
                      >
                        Clear
                      </button>
                      {isStylingCameraOn && (
                        <button
                          type="button"
                          onClick={handleStylingCameraStop}
                          className="rounded-full border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-200 transition hover:bg-red-500/20"
                        >
                          Stop camera
                        </button>
                      )}
                    </div>

                    {stylingCameraError && (
                      <p className="mt-3 text-sm text-red-300">{stylingCameraError}</p>
                    )}

                    <p className="mt-3 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {stylingPhotoFile ? `Selected file: ${stylingPhotoFile.name}` : "No file selected"}
                    </p>
                  </div>
                </div>

                {stylingError && (
                  <div className="mt-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                    ⚠ {stylingError}
                  </div>
                )}

                {stylingResult ? (
                  <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-[220px_1fr]">
                    <div className={`rounded-2xl p-5 text-center ${stylingResult.is_good ? "bg-green-600/20" : "bg-red-600/20"}`}>
                      <p className="text-sm text-slate-300">Verdict</p>
                      <p className="mt-2 text-4xl font-bold text-white">{stylingResult.is_good ? "Bon" : "Pas bon"}</p>
                      <p className="mt-2 text-sm font-semibold text-white">{stylingResult.verdict}</p>
                      {typeof stylingResult.confidence_score === "number" && (
                        <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-300">
                          Confidence {Math.round(stylingResult.confidence_score * 100)}%
                        </p>
                      )}
                    </div>
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                      <p className="text-sm font-medium text-slate-200">Why</p>
                      <p className="mt-2 text-sm text-slate-400">{stylingResult.pitch_day_summary}</p>
                      <ul className="mt-4 space-y-2 text-sm text-slate-400">
                        {stylingResult.reasons.map((item) => (
                          <li key={item} className="rounded-lg bg-black/20 px-3 py-2">{item}</li>
                        ))}
                      </ul>
                      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
                        {Object.entries(stylingResult.predictions).map(([label, value]) => (
                          <div key={label} className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
                            <p className="text-xs uppercase tracking-[0.16em] text-purple-300">{label}</p>
                            <p className="mt-1 text-sm text-white">{value}</p>
                          </div>
                        ))}
                      </div>
                      {stylingResult.photo_analysis && (
                        <div className="mt-4 rounded-xl border border-white/10 bg-black/20 px-3 py-3 text-sm text-slate-300">
                          <p className="text-xs uppercase tracking-[0.16em] text-purple-300">Photo analysis</p>
                            <p className="mt-2 text-slate-400">{stylingResult.photo_analysis.reason}</p>
                            {stylingResult.photo_analysis.face_detected !== undefined && (
                              <p className="mt-1 text-slate-400">
                                Face detected: {stylingResult.photo_analysis.face_detected ? "yes" : "no"}
                              </p>
                            )}
                            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
                              {[
                                { key: "eyes", title: "Eyes" },
                                { key: "skin", title: "Skin" },
                                { key: "clothes", title: "Clothes" },
                              ].map(({ key, title }) => {
                                const region = stylingResult.photo_analysis?.regions?.[key as "eyes" | "skin" | "clothes"]
                                return (
                                  <div key={key} className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2">
                                    <p className="text-xs uppercase tracking-[0.14em] text-purple-300">{title}</p>
                                    <p className="mt-1 text-sm text-white">{region?.dominant_label || "unknown"}</p>
                                    <p className="mt-1 text-xs text-slate-400">
                                      {(region?.labels || []).join(", ") || "No region colors detected"}
                                    </p>
                                  </div>
                                )
                              })}
                            </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <p className="mt-5 text-sm text-slate-500">
                    Click <span className="text-slate-200">Validate Clothes</span> after uploading or capturing a photo.
                  </p>
                )}
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

        </div>
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

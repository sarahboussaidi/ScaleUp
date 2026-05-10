"use client"

import { useState, useCallback, useRef, useEffect, useMemo } from "react"
import dynamic from "next/dynamic"
import { GlassmorphismNav } from "@/components/glassmorphism-nav"
import { CameraFeed } from "@/components/pitch-coach/camera-feed"
import { MetricsPanel } from "@/components/pitch-coach/metrics-panel"
import { PosturePanel } from "@/components/pitch-coach/posture-panel"
import { SpeechStrength } from "@/components/pitch-coach/speech-strength"
import { SpeechTranscription } from "@/components/pitch-coach/speech-transcription"
import { RecordingControls, AnalysisDataPoint } from "@/components/pitch-coach/recording-controls"
import { PitchHero } from "@/components/pitch-coach/pitch-hero"
import { AnalysisSummary, RecordingAnalysisData } from "@/components/pitch-coach/analysis-summary"
import { Footer } from "@/components/footer"
import { analyzeVoiceEmotion } from "@/lib/pitch-analyzer-config"

const Aurora = dynamic(() => import("@/components/Aurora"), {
  ssr: false,
})

export default function PitchCoachPage() {
  const [activeView, setActiveView] = useState<"pitch-evaluation" | "pitch-deck">("pitch-evaluation")
  const [startupName, setStartupName] = useState("")
  const [industry, setIndustry] = useState("")
  const [startupDescription, setStartupDescription] = useState("")
  const [generatedPitchDeck, setGeneratedPitchDeck] = useState<Array<{ title: string; text: string }>>([])
  const [deckEvaluation, setDeckEvaluation] = useState<{ score: number; label: string; feedback: string[] } | null>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [postureData, setPostureData] = useState({
    posture: "waiting",
    confidence: 0,
  })
  const [recordingAnalysis, setRecordingAnalysis] = useState<RecordingAnalysisData | null>(null)
  const [recordingDuration, setRecordingDuration] = useState(0)
  const [transcription, setTranscription] = useState("")
  const [speechStrength, setSpeechStrength] = useState<{ label: string; score: number } | null>(null)
  
  // Refs for recording analysis data
  const analysisDataRef = useRef<AnalysisDataPoint[]>([])
  const isRecordingRef = useRef(false)
  const recordingStartTimeRef = useRef<number>(0)
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)

  // Update refs when state changes
  useEffect(() => {
    isRecordingRef.current = isRecording
  }, [isRecording])

  // Update recording duration and cleanup
  useEffect(() => {
    if (isRecording) {
      recordingStartTimeRef.current = Date.now()
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1)
      }, 1000)
    } else {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
      }
    }

    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
      }
    }
  }, [isRecording])

  const handleStreamReady = useCallback((mediaStream: MediaStream) => {
    setStream(mediaStream)
  }, [])

  const handleStreamEnd = useCallback(() => {
    setStream(null)
    setIsRecording(false)
  }, [])

  const handleRecordingStart = useCallback(() => {
    setIsRecording(true)
    setRecordingDuration(0)
    setTranscription("")
    analysisDataRef.current = []
    audioChunksRef.current = []
    
    // Start audio capture
    if (stream) {
      try {
        const mediaRecorder = new MediaRecorder(stream)
        mediaRecorderRef.current = mediaRecorder
        
        mediaRecorder.ondataavailable = (event) => {
          audioChunksRef.current.push(event.data)
        }
        
        mediaRecorder.start()
      } catch (error) {
        console.error("Failed to start MediaRecorder:", error)
      }
    }
  }, [stream])

  const handleRecordingStop = useCallback(async () => {
    setIsRecording(false)
    
    // Stop media recorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop()
    }
    
    const analysisData = analysisDataRef.current
    if (analysisData && analysisData.length > 0) {
      // Process analysis data into summary format
      const emotionCounts: Record<string, number> = {}
      const stressCounts: Record<string, number> = {}
      const postureCounts: Record<string, number> = {}
      const voiceEmotionCounts: Record<string, number> = {}

      analysisData.forEach((dataPoint) => {
        if (dataPoint.emotion) {
          emotionCounts[dataPoint.emotion] = (emotionCounts[dataPoint.emotion] || 0) + 1
        }
        if (dataPoint.stress) {
          stressCounts[dataPoint.stress] = (stressCounts[dataPoint.stress] || 0) + 1
        }
        if (dataPoint.posture) {
          postureCounts[dataPoint.posture] = (postureCounts[dataPoint.posture] || 0) + 1
        }
      })

      // Analyze audio if chunks are available
      let voiceEmotionAnalysis: Record<string, number> = {}
      if (audioChunksRef.current && audioChunksRef.current.length > 0) {
        try {
          const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })
          const result = await analyzeVoiceEmotion(audioBlob)
          
          if (result && !result.error) {
            // If we got a single result, add it to counts
            if (result.emotion) {
              voiceEmotionAnalysis[result.emotion] = 1
            }
          }
        } catch (error) {
          console.error("Failed to analyze voice emotion:", error)
        }
      }

      setRecordingAnalysis({
        emotion: emotionCounts,
        stress: stressCounts,
        posture: postureCounts,
        voiceEmotion: voiceEmotionAnalysis,
        transcript: transcription,
        duration: recordingDuration * 1000,
        timestamp: new Date(),
      })
    }
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
    if (payload.posture && payload.postureConfidence !== undefined) {
      setPostureData({
        posture: payload.posture,
        confidence: payload.postureConfidence,
      })
    }

    // Record analysis data if recording
    if (isRecordingRef.current) {
      const dataPoint: AnalysisDataPoint = {
        emotion: payload.emotion,
        stress: payload.stress,
        posture: payload.posture,
        timestamp: Date.now() - recordingStartTimeRef.current,
      }
      analysisDataRef.current.push(dataPoint)
    }
  }, [])

  const handleGeneratePitchDeck = useCallback(() => {
    const company = startupName.trim() || "Your Startup"
    const sector = industry.trim() || "your industry"
    const description = startupDescription.trim() || "a clear solution to a real problem"

    setGeneratedPitchDeck([
      {
        title: "Problem",
        text: `${company} operates in ${sector}. The problem is that customers still struggle with ${description.toLowerCase()}.`,
      },
      {
        title: "Solution",
        text: `${company} solves this with a focused product that makes the value proposition simple, fast, and scalable.`,
      },
      {
        title: "Why Now",
        text: `The market is ready because ${sector} is evolving quickly and users expect better experiences.`,
      },
      {
        title: "Business Model",
        text: `${company} can monetize through subscriptions, usage fees, or premium services depending on customer demand.`,
      },
      {
        title: "Traction",
        text: `Use this slide to highlight pilots, users, revenue, or any validation you already have for ${company}.`,
      },
      {
        title: "Ask",
        text: `Clearly state what you need next: funding, partners, pilots, or hiring support.`,
      },
    ])

    setDeckEvaluation(null)
  }, [industry, startupDescription, startupName])

  const handleEvaluatePitchDeck = useCallback(() => {
    const checks = [
      startupName.trim().length > 2,
      industry.trim().length > 2,
      startupDescription.trim().length > 20,
      generatedPitchDeck.length > 0,
    ]

    const score = Math.round((checks.filter(Boolean).length / checks.length) * 100)
    const label = score >= 80 ? "Strong" : score >= 50 ? "Moderate" : "Weak"

    const feedback: string[] = []
    if (!startupName.trim()) feedback.push("Add your startup name.")
    if (!industry.trim()) feedback.push("Specify the industry.")
    if (!startupDescription.trim()) feedback.push("Add a short description of the problem and solution.")
    if (generatedPitchDeck.length === 0) feedback.push("Generate the pitch deck first.")

    if (feedback.length === 0) {
      feedback.push("Your pitch deck inputs look complete.")
      feedback.push("You can now refine the wording of each slide.")
    }

    setDeckEvaluation({ score, label, feedback })
  }, [generatedPitchDeck.length, industry, startupDescription, startupName])

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#0a0a14]">
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
                    speechStrength={speechStrength}
                  />

                  <RecordingControls
                    stream={stream}
                    onRecordingStart={handleRecordingStart}
                    onRecordingStop={handleRecordingStop}
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
                    <div className="mt-4">
                      <SpeechStrength onResult={(result) => setSpeechStrength(result.prediction)} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        ) : (
          <section className="px-4 pb-20 md:px-8">
            <div className="mx-auto max-w-7xl">
              <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 backdrop-blur-sm md:p-8">
                <div className="mb-8 flex items-center justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-semibold text-white md:text-3xl">Pitch Deck Template</h2>
                    <p className="mt-2 max-w-2xl text-sm text-slate-400">
                      Add your startup details, generate a pitch deck, and keep everything on the same page.
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
                  <div className="md:col-span-2 flex justify-end">
                    <button
                      type="button"
                      onClick={handleGeneratePitchDeck}
                      className="rounded-full bg-purple-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-purple-400"
                    >
                      Generate Pitch Deck
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {(generatedPitchDeck.length > 0
                    ? generatedPitchDeck
                    : [
                        { title: "Problem", text: "Fill the form above and click Generate Pitch Deck." },
                        { title: "Solution", text: "The generated slides will appear here." },
                        { title: "Market", text: "You can customize them by changing the startup inputs." },
                      ]
                  ).map((slide) => (
                    <div key={slide.title} className="rounded-xl border border-white/[0.08] bg-black/20 p-5">
                      <p className="text-xs uppercase tracking-[0.2em] text-purple-300">Slide</p>
                      <h3 className="mt-2 text-lg font-semibold text-white">{slide.title}</h3>
                      <p className="mt-2 text-sm leading-relaxed text-slate-400">{slide.text}</p>
                    </div>
                  ))}
                </div>

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
                      <div className={`rounded-2xl p-5 text-center ${deckEvaluation.label === "Weak" ? "bg-red-600/20" : deckEvaluation.label === "Moderate" ? "bg-orange-500/20" : "bg-green-600/20"}`}>
                        <p className="text-sm text-slate-300">Overall score</p>
                        <p className="mt-2 text-4xl font-bold text-white">{deckEvaluation.score}</p>
                        <p className="mt-2 text-sm font-semibold text-white">{deckEvaluation.label}</p>
                      </div>
                      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                        <p className="text-sm font-medium text-slate-200">Feedback</p>
                        <ul className="mt-3 space-y-2 text-sm text-slate-400">
                          {deckEvaluation.feedback.map((item) => (
                            <li key={item} className="rounded-lg bg-black/20 px-3 py-2">
                              {item}
                            </li>
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

        <section className="px-4 py-20 md:px-8">
          <div className="mx-auto max-w-5xl">
            <h2 className="mb-4 text-center text-2xl font-semibold text-white md:text-3xl">
              How It Works
            </h2>
            <p className="mx-auto mb-12 max-w-xl text-center text-slate-400">
              Three simple steps to perfect your investor pitch with your Flask models.
            </p>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-6 text-center backdrop-blur-sm transition-all hover:border-purple-500/30 hover:bg-white/[0.05]">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl border border-purple-500/20 bg-purple-500/10">
                  <span className="text-lg font-semibold text-purple-400">1</span>
                </div>
                <h3 className="mb-2 font-medium text-slate-200">Enable Camera</h3>
                <p className="text-sm leading-relaxed text-slate-400">
                  Allow camera and microphone access to start your practice session.
                </p>
              </div>

              <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-6 text-center backdrop-blur-sm transition-all hover:border-purple-500/30 hover:bg-white/[0.05]">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl border border-purple-500/20 bg-purple-500/10">
                  <span className="text-lg font-semibold text-purple-400">2</span>
                </div>
                <h3 className="mb-2 font-medium text-slate-200">Practice Your Pitch</h3>
                <p className="text-sm leading-relaxed text-slate-400">
                  Deliver your pitch while the webcam frames are analyzed by backend/app.py.
                </p>
              </div>

              <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-6 text-center backdrop-blur-sm transition-all hover:border-purple-500/30 hover:bg-white/[0.05]">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl border border-purple-500/20 bg-purple-500/10">
                  <span className="text-lg font-semibold text-purple-400">3</span>
                </div>
                <h3 className="mb-2 font-medium text-slate-200">Review & Improve</h3>
                <p className="text-sm leading-relaxed text-slate-400">
                  Use the emotion and stress models to review and improve your performance over time.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="px-4 pb-20 md:px-8">
          <div className="mx-auto max-w-5xl">
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 backdrop-blur-sm md:p-8">
              <h2 className="text-center text-2xl font-semibold text-white md:text-3xl">
                Backend Model Stack
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-center text-slate-400">
                This interface is connected to the same model structure used in <span className="text-slate-200">backend/app.py</span>.
              </p>

              <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border border-white/[0.08] bg-black/20 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-purple-300">Emotion</p>
                  <p className="mt-2 text-lg font-medium text-white">emotion_model.h5</p>
                  <p className="mt-2 text-sm text-slate-400">Face emotion classifier used by `/api/analyze/emotion`.</p>
                </div>
                <div className="rounded-xl border border-white/[0.08] bg-black/20 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-purple-300">Stress</p>
                  <p className="mt-2 text-lg font-medium text-white">best_final_stress_cnn_73.h5</p>
                  <p className="mt-2 text-sm text-slate-400">Stress model used by `/api/analyze/stress`.</p>
                </div>
                <div className="rounded-xl border border-white/[0.08] bg-black/20 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-purple-300">Health</p>
                  <p className="mt-2 text-lg font-medium text-white">/api/health</p>
                  <p className="mt-2 text-sm text-slate-400">Checks if the Flask models are loaded correctly.</p>
                </div>
                <div className="rounded-xl border border-white/[0.08] bg-black/20 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-purple-300">Frontend</p>
                  <p className="mt-2 text-lg font-medium text-white">ScaleUp UI</p>
                  <p className="mt-2 text-sm text-slate-400">Captures webcam frames and sends them to Flask.</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />

      {recordingAnalysis && (
        <AnalysisSummary
          data={recordingAnalysis}
          onClose={() => setRecordingAnalysis(null)}
        />
      )}
    </div>
  )
}

"use client"

import { useState, useRef, useEffect } from "react"
import { GlassmorphismNav } from "@/components/glassmorphism-nav"
import Aurora from "@/components/Aurora"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  Play,
  Square,
  FileText,
  Smile,
  Frown,
  Meh,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Volume2,
  User,
  Loader2,
  Sparkles,
} from "lucide-react"

interface PresentationFeedback {
  speechClarity: number
  pace: string
  fillerWords: number
  posture: string
  eyeContact: string
  emotion: "confident" | "nervous" | "neutral" | "enthusiastic"
  transcript: string
  suggestions: string[]
}

interface DeckSlide {
  title: string
  content: string
  speakerNotes: string
}

export default function PresentationPage() {
  const [activeTab, setActiveTab] = useState<"practice" | "generate">("practice")
  const [isRecording, setIsRecording] = useState(false)
  const [isCameraOn, setIsCameraOn] = useState(false)
  const [isMicOn, setIsMicOn] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [feedback, setFeedback] = useState<PresentationFeedback | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  // Deck generation state
  const [topic, setTopic] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedDeck, setGeneratedDeck] = useState<DeckSlide[] | null>(null)

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      setIsCameraOn(true)
      setIsMicOn(true)
    } catch (error) {
      console.error("Error accessing camera:", error)
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setIsCameraOn(false)
    setIsMicOn(false)
  }

  const toggleMic = () => {
    if (streamRef.current) {
      const audioTrack = streamRef.current.getAudioTracks()[0]
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled
        setIsMicOn(audioTrack.enabled)
      }
    }
  }

  const startRecording = () => {
    if (!isCameraOn) {
      startCamera()
    }
    setIsRecording(true)
    setRecordingTime(0)
    timerRef.current = setInterval(() => {
      setRecordingTime((prev) => prev + 1)
    }, 1000)
  }

  const stopRecording = async () => {
    setIsRecording(false)
    if (timerRef.current) {
      clearInterval(timerRef.current)
    }
    setIsAnalyzing(true)

    // Simulate AI analysis
    await new Promise((resolve) => setTimeout(resolve, 3000))

    const mockFeedback: PresentationFeedback = {
      speechClarity: 82,
      pace: "Good pace overall, slightly fast during the introduction",
      fillerWords: 7,
      posture: "Good posture maintained. Try to avoid leaning to one side.",
      eyeContact: "Excellent eye contact with the camera. Keep it up!",
      emotion: "confident",
      transcript:
        "Hello everyone, today I want to talk about our startup's vision. We are building an AI-powered platform that helps entrepreneurs validate their business ideas. Our key features include... um... business model canvas generation, legal document analysis, and financial planning tools. We believe this will revolutionize how startups operate in Tunisia.",
      suggestions: [
        "Reduce filler words like 'um' and 'uh' - try pausing instead",
        "Slow down slightly during key points for emphasis",
        "Add more hand gestures to appear more engaging",
        "Consider varying your vocal tone for important statements",
        "Practice the introduction until it flows naturally",
      ],
    }

    setFeedback(mockFeedback)
    setIsAnalyzing(false)
  }

  const generateDeck = async () => {
    if (!topic.trim()) return
    setIsGenerating(true)

    // Simulate AI generation
    await new Promise((resolve) => setTimeout(resolve, 2500))

    const mockDeck: DeckSlide[] = [
      {
        title: "Introduction",
        content: `Presenting: ${topic}\n\n- Problem Statement\n- Market Opportunity\n- Our Solution`,
        speakerNotes: "Start with a compelling hook. Make eye contact with the audience.",
      },
      {
        title: "The Problem",
        content: "- Current market challenges\n- Pain points for customers\n- Inefficiencies in existing solutions",
        speakerNotes: "Use specific examples and statistics. Pause after key points.",
      },
      {
        title: "Our Solution",
        content:
          "- Unique value proposition\n- Key features and benefits\n- Technology differentiators",
        speakerNotes: "Demonstrate enthusiasm. This is your chance to shine!",
      },
      {
        title: "Market Opportunity",
        content: "- Total Addressable Market: $X billion\n- Target segments\n- Growth projections",
        speakerNotes: "Use concrete numbers. Investors love data-backed claims.",
      },
      {
        title: "Business Model",
        content: "- Revenue streams\n- Pricing strategy\n- Unit economics",
        speakerNotes: "Be clear and confident about monetization.",
      },
      {
        title: "Traction",
        content: "- Key milestones achieved\n- Customer testimonials\n- Growth metrics",
        speakerNotes: "Show momentum and validation.",
      },
      {
        title: "Team",
        content: "- Founding team backgrounds\n- Key advisors\n- Why we're the right team",
        speakerNotes: "Highlight relevant experience and passion.",
      },
      {
        title: "The Ask",
        content: "- Funding requirements\n- Use of funds\n- Call to action",
        speakerNotes: "Be specific about what you need and why.",
      },
    ]

    setGeneratedDeck(mockDeck)
    setIsGenerating(false)
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const getEmotionIcon = (emotion: string) => {
    switch (emotion) {
      case "confident":
      case "enthusiastic":
        return <Smile className="w-6 h-6 text-green-400" />
      case "nervous":
        return <Frown className="w-6 h-6 text-yellow-400" />
      default:
        return <Meh className="w-6 h-6 text-white/60" />
    }
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
            <div className="max-w-6xl mx-auto">
              {/* Header */}
              <div className="text-center mb-12">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 text-sm font-medium mb-6">
                  <Mic className="w-4 h-4 mr-2" />
                  Presentation Coach
                </div>
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
                  AI{" "}
                  <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
                    Presentation Coach
                  </span>
                </h1>
                <p className="text-lg text-white/70 max-w-2xl mx-auto">
                  Practice your pitch with real-time AI feedback on speech, posture, and emotions. 
                  Or generate a professional speech deck instantly.
                </p>
              </div>

              {/* Tabs */}
              <div className="flex gap-2 p-1 bg-white/5 backdrop-blur-xl rounded-xl border border-white/10 max-w-md mx-auto mb-8">
                <button
                  onClick={() => setActiveTab("practice")}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all duration-300 ${
                    activeTab === "practice"
                      ? "bg-gradient-to-r from-violet-500 to-purple-600 text-white"
                      : "text-white/60 hover:text-white hover:bg-white/10"
                  }`}
                >
                  <Video className="w-4 h-4" />
                  Practice Mode
                </button>
                <button
                  onClick={() => setActiveTab("generate")}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all duration-300 ${
                    activeTab === "generate"
                      ? "bg-gradient-to-r from-violet-500 to-purple-600 text-white"
                      : "text-white/60 hover:text-white hover:bg-white/10"
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  Generate Deck
                </button>
              </div>

              {activeTab === "practice" ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Video Section */}
                  <div className="space-y-6">
                    <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                      <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                          <Video className="w-5 h-5 text-violet-400" />
                          Live Preview
                        </CardTitle>
                        <CardDescription className="text-white/60">
                          Practice your presentation with real-time feedback
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="relative aspect-video bg-black/50 rounded-xl overflow-hidden mb-4">
                          {isCameraOn ? (
                            <video
                              ref={videoRef}
                              autoPlay
                              muted
                              playsInline
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <User className="w-24 h-24 text-white/20" />
                            </div>
                          )}
                          {isRecording && (
                            <div className="absolute top-4 left-4 flex items-center gap-2 px-3 py-1.5 bg-red-500 rounded-full">
                              <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                              <span className="text-white text-sm font-medium">{formatTime(recordingTime)}</span>
                            </div>
                          )}
                          {isAnalyzing && (
                            <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                              <div className="text-center">
                                <Loader2 className="w-12 h-12 text-violet-400 animate-spin mx-auto mb-4" />
                                <p className="text-white font-medium">Analyzing your presentation...</p>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Controls */}
                        <div className="flex items-center justify-center gap-4">
                          <Button
                            variant="outline"
                            size="icon"
                            onClick={isCameraOn ? stopCamera : startCamera}
                            className={`rounded-full ${isCameraOn ? "bg-violet-500/20 border-violet-500/50" : "bg-white/5 border-white/20"}`}
                          >
                            {isCameraOn ? (
                              <Video className="w-5 h-5 text-violet-400" />
                            ) : (
                              <VideoOff className="w-5 h-5 text-white/60" />
                            )}
                          </Button>
                          <Button
                            variant="outline"
                            size="icon"
                            onClick={toggleMic}
                            disabled={!isCameraOn}
                            className={`rounded-full ${isMicOn ? "bg-violet-500/20 border-violet-500/50" : "bg-white/5 border-white/20"}`}
                          >
                            {isMicOn ? (
                              <Mic className="w-5 h-5 text-violet-400" />
                            ) : (
                              <MicOff className="w-5 h-5 text-white/60" />
                            )}
                          </Button>
                          {!isRecording ? (
                            <Button
                              onClick={startRecording}
                              className="bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-full px-8"
                            >
                              <Play className="w-5 h-5 mr-2" />
                              Start Recording
                            </Button>
                          ) : (
                            <Button
                              onClick={stopRecording}
                              className="bg-red-500 hover:bg-red-600 text-white rounded-full px-8"
                            >
                              <Square className="w-5 h-5 mr-2" />
                              Stop & Analyze
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Feedback Section */}
                  <div className="space-y-6">
                    {feedback ? (
                      <>
                        {/* Quick Stats */}
                        <div className="grid grid-cols-2 gap-4">
                          <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                            <CardContent className="p-4">
                              <div className="flex items-center gap-3">
                                <Volume2 className="w-8 h-8 text-violet-400" />
                                <div>
                                  <p className="text-white/60 text-xs">Speech Clarity</p>
                                  <p className="text-white font-bold text-xl">{feedback.speechClarity}%</p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                          <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                            <CardContent className="p-4">
                              <div className="flex items-center gap-3">
                                <AlertCircle className="w-8 h-8 text-yellow-400" />
                                <div>
                                  <p className="text-white/60 text-xs">Filler Words</p>
                                  <p className="text-white font-bold text-xl">{feedback.fillerWords}</p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                          <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                            <CardContent className="p-4">
                              <div className="flex items-center gap-3">
                                {getEmotionIcon(feedback.emotion)}
                                <div>
                                  <p className="text-white/60 text-xs">Detected Emotion</p>
                                  <p className="text-white font-bold text-lg capitalize">{feedback.emotion}</p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                          <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                            <CardContent className="p-4">
                              <div className="flex items-center gap-3">
                                <CheckCircle className="w-8 h-8 text-green-400" />
                                <div>
                                  <p className="text-white/60 text-xs">Eye Contact</p>
                                  <p className="text-white font-bold text-lg">Good</p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        </div>

                        {/* Detailed Feedback */}
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader>
                            <CardTitle className="text-white">Detailed Feedback</CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            <div className="p-3 bg-white/5 rounded-lg">
                              <p className="text-white/60 text-xs mb-1">Pace</p>
                              <p className="text-white text-sm">{feedback.pace}</p>
                            </div>
                            <div className="p-3 bg-white/5 rounded-lg">
                              <p className="text-white/60 text-xs mb-1">Posture</p>
                              <p className="text-white text-sm">{feedback.posture}</p>
                            </div>
                            <div className="p-3 bg-white/5 rounded-lg">
                              <p className="text-white/60 text-xs mb-1">Transcript</p>
                              <p className="text-white/80 text-sm">{feedback.transcript}</p>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Suggestions */}
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader>
                            <CardTitle className="text-white flex items-center gap-2">
                              <TrendingUp className="w-5 h-5 text-violet-400" />
                              Improvement Tips
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <ul className="space-y-2">
                              {feedback.suggestions.map((tip, index) => (
                                <li key={index} className="flex items-start gap-2 text-white/70 text-sm">
                                  <span className="text-violet-400">•</span>
                                  {tip}
                                </li>
                              ))}
                            </ul>
                          </CardContent>
                        </Card>
                      </>
                    ) : (
                      <Card className="bg-white/5 backdrop-blur-xl border-white/10 h-full min-h-[400px] flex items-center justify-center">
                        <CardContent className="text-center p-8">
                          <Mic className="w-16 h-16 text-white/20 mx-auto mb-4" />
                          <h3 className="text-xl font-semibold text-white/60 mb-2">No Recording Yet</h3>
                          <p className="text-white/40">
                            Start recording to get AI feedback on your presentation skills
                          </p>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </div>
              ) : (
                /* Generate Deck Tab */
                <div className="max-w-4xl mx-auto space-y-8">
                  <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-violet-400" />
                        Generate Speech Deck
                      </CardTitle>
                      <CardDescription className="text-white/60">
                        Enter your presentation topic and let AI generate a professional pitch deck
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <Textarea
                        placeholder="Enter your presentation topic... (e.g., 'AI-powered startup platform for Tunisian entrepreneurs')"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        className="bg-white/5 border-white/10 text-white placeholder:text-white/40 min-h-[100px]"
                      />
                      <Button
                        onClick={generateDeck}
                        disabled={isGenerating || !topic.trim()}
                        className="w-full bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white"
                      >
                        {isGenerating ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Generating Deck...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4 mr-2" />
                            Generate Deck
                          </>
                        )}
                      </Button>
                    </CardContent>
                  </Card>

                  {generatedDeck && (
                    <div className="space-y-4">
                      <h3 className="text-xl font-bold text-white">Generated Slides</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {generatedDeck.map((slide, index) => (
                          <Card key={index} className="bg-white/5 backdrop-blur-xl border-white/10">
                            <CardHeader className="pb-2">
                              <div className="flex items-center gap-2">
                                <span className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center text-violet-400 font-bold text-sm">
                                  {index + 1}
                                </span>
                                <CardTitle className="text-white text-lg">{slide.title}</CardTitle>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-3">
                              <div className="p-3 bg-white/5 rounded-lg">
                                <p className="text-white/80 text-sm whitespace-pre-line">{slide.content}</p>
                              </div>
                              <div className="p-3 bg-violet-500/10 rounded-lg border border-violet-500/20">
                                <p className="text-violet-300 text-xs font-medium mb-1">Speaker Notes</p>
                                <p className="text-white/60 text-sm">{slide.speakerNotes}</p>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}
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

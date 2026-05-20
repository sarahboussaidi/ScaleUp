"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Smile,
  Frown,
  AlertCircle,
  CheckCircle,
  Loader2,
  Video,
  VideoOff,
  Zap,
} from "lucide-react"
import { API_CONFIG, analyzeFrame, checkBackendHealth } from "@/lib/pitch-analyzer-config"

interface AnalysisResult {
  emotion?: string
  confidence?: number
  scores?: Record<string, number>
  stress?: string
  error?: string
}

export function PitchAnalyzerSection() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const [isRecording, setIsRecording] = useState(false)
  const [isCameraOn, setIsCameraOn] = useState(false)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [emotionResult, setEmotionResult] = useState<AnalysisResult | null>(null)
  const [stressResult, setStressResult] = useState<AnalysisResult | null>(null)
  const [analysisHistory, setAnalysisHistory] = useState<any[]>([])
  const [backendHealth, setBackendHealth] = useState<boolean | null>(null)

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      const isHealthy = await checkBackendHealth()
      setBackendHealth(isHealthy)
    }
    checkHealth()
  }, [])

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: true,
      })
      setCameraError(null)
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      setIsCameraOn(true)
    } catch (error) {
      console.error("Error accessing camera:", error)
      setCameraError((error as Error)?.message || String(error))
    }
  }

  // Stop camera
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setIsCameraOn(false)
  }

  // Capture frame from video
  const captureFrame = (): string | null => {
    if (!videoRef.current || !canvasRef.current) return null

    const ctx = canvasRef.current.getContext("2d")
    if (!ctx) return null

    canvasRef.current.width = videoRef.current.videoWidth
    canvasRef.current.height = videoRef.current.videoHeight
    ctx.drawImage(videoRef.current, 0, 0)

    return canvasRef.current.toDataURL("image/jpeg")
  }

  // Analyze emotion
  const analyzeEmotion = async () => {
    const frame = captureFrame()
    if (!frame) {
      alert("Could not capture frame")
      return
    }

    setIsAnalyzing(true)
    try {
      const data = await analyzeFrame(API_CONFIG.ENDPOINTS.ANALYZE_EMOTION, frame)
      setEmotionResult(data)

      // Add to history
      setAnalysisHistory((prev) => [
        ...prev,
        { type: "emotion", timestamp: new Date().toLocaleTimeString(), result: data },
      ])
    } catch (error) {
      console.error("Error analyzing emotion:", error)
      setEmotionResult({ error: "Failed to analyze emotion. Make sure the backend is running." })
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Analyze stress
  const analyzeStress = async () => {
    const frame = captureFrame()
    if (!frame) {
      alert("Could not capture frame")
      return
    }

    setIsAnalyzing(true)
    try {
      const data = await analyzeFrame(API_CONFIG.ENDPOINTS.ANALYZE_STRESS, frame)
      setStressResult(data)

      // Add to history
      setAnalysisHistory((prev) => [
        ...prev,
        { type: "stress", timestamp: new Date().toLocaleTimeString(), result: data },
      ])
    } catch (error) {
      console.error("Error analyzing stress:", error)
      setStressResult({ error: "Failed to analyze stress. Make sure the backend is running." })
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Analyze both
  const analyzeAll = async () => {
    await analyzeEmotion()
    await analyzeStress()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 pt-20 pb-12">
      <div className="container max-w-6xl mx-auto px-4">
        {/* Backend Health Warning */}
        {backendHealth === false && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <div>
              <p className="text-red-400 font-medium">Backend Not Connected</p>
              <p className="text-red-300/80 text-sm">The Flask backend is not running. Follow the setup guide to start it.</p>
            </div>
          </div>
        )}

        {/* Backend Health Success */}
        {backendHealth === true && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
            <p className="text-green-400 font-medium">Backend Connected</p>
          </div>
        )}
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Zap className="w-8 h-8 text-yellow-400" />
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Pitch Analyzer Pro
            </h1>
          </div>
          <p className="text-gray-400 text-lg">Real-time emotion & stress detection for presentations</p>
        </div>

        <Tabs defaultValue="analyzer" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-8 bg-gray-800/50 border border-gray-700">
            <TabsTrigger value="analyzer" className="data-[state=active]:bg-purple-600">
              Live Analysis
            </TabsTrigger>
            <TabsTrigger value="history" className="data-[state=active]:bg-purple-600">
              History
            </TabsTrigger>
          </TabsList>

          <TabsContent value="analyzer" className="space-y-6">
            {/* Video Feed */}
            <Card className="bg-gray-900/50 border-gray-700">
              <CardHeader>
                <CardTitle>Video Feed</CardTitle>
                <CardDescription>Position your face in the center for best results</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="relative bg-black rounded-lg overflow-hidden">
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-80 object-cover"
                    />
                    <canvas ref={canvasRef} className="hidden" />
                  </div>

                  <div className="flex gap-2">
                    {!isCameraOn ? (
                      <Button onClick={startCamera} className="flex-1 bg-blue-600 hover:bg-blue-700">
                        <Video className="w-4 h-4 mr-2" />
                        Start Camera
                      </Button>
                    ) : (
                      <Button onClick={stopCamera} className="flex-1 bg-red-600 hover:bg-red-700">
                        <VideoOff className="w-4 h-4 mr-2" />
                        Stop Camera
                      </Button>
                    )}
                  </div>
                  {cameraError && (
                    <div className="mt-2 text-sm text-red-400">Camera error: {cameraError}</div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Analysis Controls */}
            <Card className="bg-gray-900/50 border-gray-700">
              <CardHeader>
                <CardTitle>Real-time Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Button
                    onClick={analyzeEmotion}
                    disabled={!isCameraOn || isAnalyzing}
                    className="bg-blue-600 hover:bg-blue-700 h-12"
                  >
                    {isAnalyzing && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                    Analyze Emotion
                  </Button>
                  <Button
                    onClick={analyzeStress}
                    disabled={!isCameraOn || isAnalyzing}
                    className="bg-orange-600 hover:bg-orange-700 h-12"
                  >
                    {isAnalyzing && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                    Analyze Stress
                  </Button>
                  <Button
                    onClick={analyzeAll}
                    disabled={!isCameraOn || isAnalyzing}
                    className="bg-purple-600 hover:bg-purple-700 h-12"
                  >
                    {isAnalyzing && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                    Analyze All
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Results Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Emotion Result */}
              <Card className="bg-gray-900/50 border-gray-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Smile className="w-5 h-5 text-yellow-400" />
                    Emotion Detection
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {emotionResult?.error ? (
                    <div className="flex items-center gap-2 text-red-400">
                      <AlertCircle className="w-5 h-5" />
                      <span>{emotionResult.error}</span>
                    </div>
                  ) : emotionResult?.emotion ? (
                    <div className="space-y-4">
                      <div className="text-center">
                        <div className="text-4xl font-bold text-blue-400 mb-2">
                          {emotionResult.emotion}
                        </div>
                        <div className="text-sm text-gray-400">
                          Confidence: {((emotionResult.confidence || 0) * 100).toFixed(1)}%
                        </div>
                      </div>

                      {emotionResult.scores && (
                        <div className="space-y-2">
                          {Object.entries(emotionResult.scores).map(([emotion, score]: [string, any]) => (
                            <div key={emotion} className="flex items-center gap-2">
                              <span className="w-20 text-sm text-gray-400 capitalize">{emotion}</span>
                              <div className="flex-1 bg-gray-700 rounded h-2 overflow-hidden">
                                <div
                                  className="bg-blue-500 h-full transition-all"
                                  style={{ width: `${(score as number) * 100}%` }}
                                />
                              </div>
                              <span className="w-12 text-right text-xs text-gray-500">
                                {((score as number) * 100).toFixed(0)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-gray-500 text-center py-8">Click "Analyze Emotion" to get started</div>
                  )}
                </CardContent>
              </Card>

              {/* Stress Result */}
              <Card className="bg-gray-900/50 border-gray-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Frown className="w-5 h-5 text-red-400" />
                    Stress Detection
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {stressResult?.error ? (
                    <div className="flex items-center gap-2 text-red-400">
                      <AlertCircle className="w-5 h-5" />
                      <span>{stressResult.error}</span>
                    </div>
                  ) : stressResult?.stress ? (
                    <div className="space-y-4">
                      <div className="text-center">
                        <div className={`text-4xl font-bold mb-2 ${
                          stressResult.stress === "stressed" ? "text-red-400" : "text-green-400"
                        }`}>
                          {stressResult.stress === "stressed" ? "⚠️ Stressed" : "✓ Calm"}
                        </div>
                        <div className="text-sm text-gray-400">
                          Confidence: {((stressResult.confidence || 0) * 100).toFixed(1)}%
                        </div>
                      </div>

                      <div className="bg-gray-700 rounded-lg p-4">
                        <div className="text-sm text-gray-400 mb-2">Stress Level</div>
                        <div className="flex-1 bg-gray-600 rounded h-4 overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              stressResult.stress === "stressed"
                                ? "bg-red-500"
                                : "bg-green-500"
                            }`}
                            style={{
                              width: `${(stressResult.confidence || 0) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-gray-500 text-center py-8">Click "Analyze Stress" to get started</div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history">
            <Card className="bg-gray-900/50 border-gray-700">
              <CardHeader>
                <CardTitle>Analysis History</CardTitle>
                <CardDescription>Recent analysis results</CardDescription>
              </CardHeader>
              <CardContent>
                {analysisHistory.length === 0 ? (
                  <div className="text-gray-500 text-center py-8">No analysis history yet</div>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {analysisHistory.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 bg-gray-800/50 rounded border border-gray-700"
                      >
                        <div className="flex items-center gap-3 flex-1">
                          {item.type === "emotion" ? (
                            <Smile className="w-5 h-5 text-yellow-400" />
                          ) : (
                            <Frown className="w-5 h-5 text-red-400" />
                          )}
                          <div>
                            <div className="font-medium capitalize">{item.type} Detection</div>
                            <div className="text-sm text-gray-500">{item.timestamp}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-medium">
                            {item.result.emotion || item.result.stress || "Unknown"}
                          </div>
                          <div className="text-sm text-gray-500">
                            {((item.result.confidence || 0) * 100).toFixed(1)}%
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

"use client"

import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { analyzeFrame, API_CONFIG } from "@/lib/pitch-analyzer-config"
import { AlertCircle, Camera, CameraOff, Loader2, Play, Square } from "lucide-react"

type CameraFeedProps = {
  onStreamReady: (mediaStream: MediaStream) => void
  onStreamEnd: () => void
  isRecording: boolean
  onAnalysisUpdate?: (payload: {
    emotion?: string
    emotionConfidence?: number
    stress?: string
    stressConfidence?: number
    posture?: string
    postureConfidence?: number
    modelStatus?: string
  }) => void
}

export function CameraFeed({ onStreamReady, onStreamEnd, isRecording, onAnalysisUpdate }: CameraFeedProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const overlayRef = useRef<HTMLDivElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const [isCameraOn, setIsCameraOn] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [lastEmotion, setLastEmotion] = useState<string>("waiting")
  const [lastStress, setLastStress] = useState<string>("waiting")
  const [lastResponses, setLastResponses] = useState<{ emotion?: any; stress?: any; posture?: any } | null>(null)
  const [emotionBox, setEmotionBox] = useState<{ x: number; y: number; w: number; h: number } | null>(null)
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null)

  const formatEmotionLabel = (value: string) => {
    if (!value || value === "waiting") return "Waiting"
    if (value === "no_face") return "No face"
    return value
      .replace(/_/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .replace(/^./, (char) => char.toUpperCase())
  }

  const formatStressLabel = (value: string) => {
    if (!value || value === "waiting") return "Waiting"
    if (value === "unknown") return "Unknown"
    return value
      .replace(/_/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .replace(/^./, (char) => char.toUpperCase())
  }

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.HEALTH}`)
        setBackendHealthy(response.ok)
      } catch {
        setBackendHealthy(false)
      }
    }

    checkBackend()

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
    }
  }, [])

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: API_CONFIG.CAMERA.WIDTH, height: API_CONFIG.CAMERA.HEIGHT },
        audio: true,
      })

      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }

      setIsCameraOn(true)
      onStreamReady(stream)

      intervalRef.current = setInterval(async () => {
        if (!videoRef.current || !canvasRef.current || isAnalyzing) return

        const ctx = canvasRef.current.getContext("2d")
        if (!ctx) return

        const video = videoRef.current
        if (!video.videoWidth || !video.videoHeight) return

        canvasRef.current.width = video.videoWidth
        canvasRef.current.height = video.videoHeight
        ctx.drawImage(video, 0, 0, canvasRef.current.width, canvasRef.current.height)
        const frame = canvasRef.current.toDataURL("image/jpeg", 0.8)


        setIsAnalyzing(true)
        try {
          const emotionResponse = await analyzeFrame(API_CONFIG.ENDPOINTS.ANALYZE_EMOTION, frame)
          const stressResponse = await analyzeFrame(API_CONFIG.ENDPOINTS.ANALYZE_STRESS, frame)
          const postureResponse = await analyzeFrame(API_CONFIG.ENDPOINTS.ANALYZE_POSTURE, frame)

          // DEBUG: log raw responses to help diagnose constant predictions
          console.debug('analyzeFrame emotion response:', emotionResponse)
          console.debug('analyzeFrame stress response:', stressResponse)
          console.debug('analyzeFrame posture response:', postureResponse)

          // expose last raw responses to the UI for easier debugging
          setLastResponses({ emotion: emotionResponse, stress: stressResponse, posture: postureResponse })

          // Always update displayed lastEmotion/lastStress so UI reflects 'no_face' or 'unknown'
          if (emotionResponse && typeof emotionResponse.emotion !== 'undefined') {
            setLastEmotion(emotionResponse.emotion)
          } else {
            setLastEmotion('waiting')
          }

          if (stressResponse && typeof stressResponse.stress !== 'undefined') {
            setLastStress(stressResponse.stress)
          } else {
            setLastStress('waiting')
          }

          setEmotionBox(emotionResponse?.emotion && emotionResponse.emotion !== "no_face" ? emotionResponse.face_box || null : null)
          onAnalysisUpdate?.({
            emotion: emotionResponse?.emotion,
            emotionConfidence: emotionResponse?.confidence,
            stress: stressResponse?.stress,
            stressConfidence: stressResponse?.confidence,
            posture: postureResponse?.posture,
            postureConfidence: postureResponse?.confidence,
            modelStatus: backendHealthy === false ? "offline" : "online",
          })
        } catch (error) {
          console.error("Live analysis failed:", error)
        } finally {
          setIsAnalyzing(false)
        }
      }, 2500)
    } catch (error) {
      console.error("Error accessing camera:", error)
      // show a visible error to the user by setting backendHealthy to false and logging
      setBackendHealthy(false)
      // Optionally, bubble up a toast or call onStreamEnd
    }
  }

  const stopCamera = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null
    }

    setIsCameraOn(false)
    setEmotionBox(null)
    onStreamEnd()
  }

  const getOverlayStyle = () => {
    const video = videoRef.current
    const box = emotionBox

    if (!video || !box || !video.videoWidth || !video.videoHeight) {
      return null
    }

    const container = video.getBoundingClientRect()
    if (!container.width || !container.height) {
      return null
    }

    const scaleX = container.width / video.videoWidth
    const scaleY = container.height / video.videoHeight

    return {
      left: `${box.x * scaleX}px`,
      top: `${Math.max(0, box.y * scaleY - 42)}px`,
      width: `${box.w * scaleX}px`,
    }
  }

  return (
    <Card className="border-white/10 bg-white/[0.03] backdrop-blur-xl text-white shadow-2xl shadow-black/20">
      <CardHeader className="space-y-2 border-b border-white/10 bg-white/[0.02]">
        <CardTitle className="flex items-center gap-2 text-lg font-medium">
          <Camera className="h-5 w-5 text-purple-300" />
          Camera Feed
        </CardTitle>
        <CardDescription className="text-slate-400">
          {backendHealthy === false
            ? "Backend is offline. Start Flask in backend/app.py."
            : "Your webcam feed is analyzed against the models loaded in backend/app.py."}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4 p-4 md:p-6">
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-black/40">
          <video ref={videoRef} autoPlay playsInline muted className="h-[320px] w-full object-cover md:h-[440px]" />
          <canvas ref={canvasRef} className="hidden" />

          {emotionBox && isCameraOn && (
            <div
              ref={overlayRef}
              className="pointer-events-none absolute z-20 rounded-full border border-purple-300/40 bg-black/70 px-3 py-1 text-xs font-semibold text-white shadow-lg shadow-purple-950/40 backdrop-blur-md"
              style={getOverlayStyle() || undefined}
            >
              Emotion: {formatEmotionLabel(lastEmotion)}
            </div>
          )}

          {!isCameraOn && (
            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-b from-black/30 to-black/60">
              <div className="text-center">
                <CameraOff className="mx-auto mb-3 h-12 w-12 text-white/30" />
                <p className="text-sm text-slate-300">Camera is off</p>
              </div>
            </div>
          )}

          {isRecording && (
            <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/20 px-3 py-1.5 text-xs font-medium text-red-100 backdrop-blur-md">
              <span className="h-2 w-2 animate-pulse rounded-full bg-red-400" />
              Recording live analysis
            </div>
          )}

          {isAnalyzing && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/40">
              <div className="flex items-center gap-2 rounded-full border border-white/10 bg-slate-950/80 px-4 py-2 text-sm text-slate-100 backdrop-blur-md">
                <Loader2 className="h-4 w-4 animate-spin text-purple-300" />
                Reading model output...
              </div>
            </div>
          )}
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <Button
            onClick={isCameraOn ? stopCamera : startCamera}
            className="h-12 rounded-xl bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white hover:from-purple-500 hover:to-fuchsia-500"
          >
            {isCameraOn ? <Square className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />}
            {isCameraOn ? "Stop Camera" : "Start Camera"}
          </Button>

          <div className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-300">
            <div className="flex items-center justify-between">
              <span>Emotion</span>
              <span className="font-medium text-white">{formatEmotionLabel(lastEmotion)}</span>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <span>Stress</span>
              <span className="font-medium text-white">{formatStressLabel(lastStress)}</span>
            </div>
          </div>
        </div>

        {/* Debug panel showing last raw model responses */}
        {lastResponses && (
          <div className="mt-3 rounded-lg border border-white/10 bg-black/60 p-3 text-xs text-slate-200">
            <div className="flex items-center justify-between mb-2">
              <div className="font-medium">Last Model Responses (debug)</div>
              <div className="text-xs text-slate-400">Updated live</div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              <pre className="whitespace-pre-wrap overflow-auto max-h-40 p-2 bg-slate-900/40 rounded">{JSON.stringify(lastResponses.emotion, null, 2)}</pre>
              <pre className="whitespace-pre-wrap overflow-auto max-h-40 p-2 bg-slate-900/40 rounded">{JSON.stringify(lastResponses.stress, null, 2)}</pre>
              <pre className="whitespace-pre-wrap overflow-auto max-h-40 p-2 bg-slate-900/40 rounded">{JSON.stringify(lastResponses.posture, null, 2)}</pre>
            </div>
          </div>
        )}

        <div className="rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3 text-xs text-slate-400">
          The camera feed sends frames to <span className="text-slate-200">{API_CONFIG.BASE_URL}</span> and queries <span className="text-slate-200">/api/analyze/emotion</span> and <span className="text-slate-200">/api/analyze/stress</span>.
        </div>

        {backendHealthy === false && (
          <div className="flex items-start gap-2 rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-amber-100">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <p className="text-sm">Backend not detected. Make sure Flask is running from backend/app.py before starting the camera.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

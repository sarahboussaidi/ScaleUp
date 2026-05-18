"use client"

import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Mic, MicOff, Play, Square, Volume2 } from "lucide-react"

interface SpeechTranscriptionProps {
  isRecording: boolean
  onTranscriptionUpdate?: (transcript: string) => void
  onFinalTranscript?: (transcript: string) => void
  stream?: MediaStream | null
  onRecordingStart?: () => void | Promise<void>
  onRecordingStop?: () => void | Promise<void>
  recordingDuration?: number
  speechStrength?: {
    label: string
    score: number
  } | null
  speechSafety?: {
    label: string
    confidence: number
  } | null
}

export function SpeechTranscription({
  isRecording,
  onTranscriptionUpdate,
  onFinalTranscript,
  stream,
  onRecordingStart,
  onRecordingStop,
  recordingDuration = 0,
  speechStrength,
  speechSafety,
}: SpeechTranscriptionProps) {
  const recognitionRef = useRef<any>(null)
  const [transcript, setTranscript] = useState("")
  const [interimTranscript, setInterimTranscript] = useState("")
  const [isListening, setIsListening] = useState(false)
  const [isBrowserSupported, setIsBrowserSupported] = useState(true)
  const finalTranscriptRef = useRef("")
  const [isMicMuted, setIsMicMuted] = useState(false)

  const toggleMic = () => {
    if (!stream) return

    const audioTrack = stream.getAudioTracks()[0]
    if (!audioTrack) return

    audioTrack.enabled = !audioTrack.enabled
    setIsMicMuted(!audioTrack.enabled)
  }

  useEffect(() => {
    // Check browser support
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

    if (!SpeechRecognition) {
      setIsBrowserSupported(false)
      return
    }

    const recognition = new SpeechRecognition()
    recognitionRef.current = recognition

    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = "en-US"

    recognition.onstart = () => {
      setIsListening(true)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error)
    }

    recognition.onresult = (event: any) => {
      let interim = ""
      let final = ""

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript

        if (event.results[i].isFinal) {
          final += transcript + " "
        } else {
          interim += transcript
        }
      }

      setInterimTranscript(interim)

      if (final) {
        // Use the ref to avoid stale closure over `transcript`
        const newTranscript = finalTranscriptRef.current + final
        setTranscript(newTranscript)
        finalTranscriptRef.current = newTranscript
        onTranscriptionUpdate?.(newTranscript)
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
    }
  }, [onTranscriptionUpdate])

  useEffect(() => {
    if (isRecording && recognitionRef.current && isBrowserSupported) {
      // Reset transcript
      setTranscript("")
      setInterimTranscript("")
      finalTranscriptRef.current = ""

      try {
        recognitionRef.current.start()
      } catch (error) {
        console.error("Error starting speech recognition:", error)
      }
    } else if (!isRecording && recognitionRef.current) {
      recognitionRef.current.stop()

      // Emit final transcript
      if (finalTranscriptRef.current) {
        onFinalTranscript?.(finalTranscriptRef.current)
      }
    }
  }, [isRecording, isBrowserSupported, onFinalTranscript])

  if (!isBrowserSupported) {
    return (
      <Card className="border-yellow-500/20 bg-yellow-500/5 p-4 text-sm text-yellow-600">
        Speech recognition not supported in your browser. Please use Chrome, Edge, or Safari.
      </Card>
    )
  }

  return (
    <Card className="border-white/10 bg-white/[0.03] p-4 backdrop-blur-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isListening ? (
            <Mic className="h-4 w-4 animate-pulse text-red-400" />
          ) : (
            <MicOff className="h-4 w-4 text-slate-400" />
          )}
          <span className="text-sm font-medium text-slate-200">
            {isRecording ? "Listening..." : "Speech Recognition"}
          </span>
        </div>
        <span
          className={`text-xs font-semibold ${
            isListening ? "text-green-400" : "text-slate-500"
          }`}
        >
          {isListening ? "● Active" : "○ Inactive"}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-white/10 bg-black/20 p-3">
        <Button
          onClick={isRecording ? onRecordingStop : onRecordingStart}
          disabled={!stream}
          className="rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white hover:from-fuchsia-500 hover:to-purple-500"
        >
          {isRecording ? <Square className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />}
          {isRecording ? "Stop Recording" : "Start Recording"}
        </Button>

        <Button
          onClick={toggleMic}
          disabled={!stream}
          variant="outline"
          className="rounded-xl border-white/10 bg-white/[0.04] text-slate-100 hover:bg-white/[0.08] hover:text-white"
        >
          {isMicMuted ? <MicOff className="mr-2 h-4 w-4" /> : <Mic className="mr-2 h-4 w-4" />}
          {isMicMuted ? "Unmute Mic" : "Mute Mic"}
        </Button>

        <div className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-sm text-slate-300">
          <span className="text-slate-500">Duration</span> <span className="ml-2 font-medium text-white">{Math.floor(recordingDuration / 60).toString().padStart(2, "0")}:{(recordingDuration % 60).toString().padStart(2, "0")}</span>
        </div>
      </div>

      <div className="rounded-lg bg-slate-900/50 p-3 min-h-[80px] max-h-[150px] overflow-y-auto">
        <div className="space-y-1">
          {transcript && (
            <p className="text-sm text-slate-200 leading-relaxed">
              {transcript}
              {interimTranscript && (
                <span className="text-slate-500 italic ml-1">{interimTranscript}</span>
              )}
            </p>
          )}
          {!transcript && interimTranscript && (
            <p className="text-sm text-slate-400 italic">{interimTranscript}</p>
          )}
          {!transcript && !interimTranscript && (
            <p className="text-xs text-slate-500">
              {isRecording ? "Start speaking..." : "Speech will appear here"}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 rounded-lg bg-slate-800/30 px-3 py-2 text-xs text-slate-400">
        <Volume2 className="h-3 w-3" />
        <span>Words detected: {transcript.split(/\s+/).filter((w) => w).length}</span>
      </div>

      <div className="flex items-center justify-between rounded-lg bg-slate-800/30 px-3 py-2 text-xs">
        <span className="text-slate-400">Speech strength</span>
        {speechStrength ? (
          <span
            className={`rounded-full px-3 py-1 font-semibold ${
              speechStrength.label === "weak"
                ? "bg-red-600 text-white"
                : speechStrength.label === "moderate"
                  ? "bg-orange-400 text-black"
                  : "bg-green-600 text-white"
            }`}
          >
            {speechStrength.label.toUpperCase()} ({speechStrength.score.toFixed(2)})
          </span>
        ) : (
          <span className="text-slate-500">Waiting for analysis</span>
        )}
      </div>

      <div className="flex items-center justify-between rounded-lg bg-slate-800/30 px-3 py-2 text-xs">
        <span className="text-slate-400">Bad words</span>
        {speechSafety ? (
          <span
            className={`rounded-full px-3 py-1 font-semibold ${
              speechSafety.label === "toxic"
                ? "bg-red-600 text-white"
                : "bg-emerald-600 text-white"
            }`}
          >
            {speechSafety.label.toUpperCase()} ({speechSafety.confidence.toFixed(2)})
          </span>
        ) : (
          <span className="text-slate-500">Waiting for analysis</span>
        )}
      </div>
    </Card>
  )
}

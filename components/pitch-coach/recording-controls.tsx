"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Mic, MicOff, Pause, Play, Square } from "lucide-react"

export interface AnalysisDataPoint {
  emotion?: string
  stress?: string
  posture?: string
  timestamp: number
}

type RecordingControlsProps = {
  stream: MediaStream | null
  onRecordingStart: () => void
  onRecordingStop: () => void
}

export function RecordingControls({ stream, onRecordingStart, onRecordingStop }: RecordingControlsProps) {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const [isRecording, setIsRecording] = useState(false)
  const [isMicMuted, setIsMicMuted] = useState(false)
  const [duration, setDuration] = useState(0)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (!stream) {
      setIsRecording(false)
      setDuration(0)
    }
  }, [stream])

  const toggleMic = () => {
    if (!stream) return

    const audioTrack = stream.getAudioTracks()[0]
    if (!audioTrack) return

    audioTrack.enabled = !audioTrack.enabled
    setIsMicMuted(!audioTrack.enabled)
  }

  const startRecording = () => {
    if (!stream) return

    chunksRef.current = []
    const recorder = new MediaRecorder(stream, { mimeType: "video/webm" })
    mediaRecorderRef.current = recorder

    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data)
      }
    }

    recorder.start()
    setIsRecording(true)
    onRecordingStart()
    setDuration(0)

    timerRef.current = setInterval(() => {
      setDuration((value) => value + 1)
    }, 1000)
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
    onRecordingStop()

    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  const timeLabel = useMemo(() => {
    const minutes = Math.floor(duration / 60)
    const seconds = duration % 60
    return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`
  }, [duration])

  return (
    <Card className="border-white/10 bg-white/[0.03] backdrop-blur-xl text-white shadow-2xl shadow-black/20">
      <CardContent className="p-4 md:p-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-medium text-slate-100">Recording Controls</p>
            <p className="mt-1 text-xs text-slate-400">Capture your pitch and keep the webcam active for live analysis.</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              onClick={isRecording ? stopRecording : startRecording}
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
              <span className="text-slate-500">Duration</span> <span className="ml-2 font-medium text-white">{timeLabel}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

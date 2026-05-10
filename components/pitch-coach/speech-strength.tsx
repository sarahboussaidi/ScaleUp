"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { API_CONFIG } from "@/lib/pitch-analyzer-config"

type SpeechStrengthValue = {
  label: string
  score: number
}

type SpeechStrengthProps = {
  onResult?: (result: { transcript: string; prediction: SpeechStrengthValue | null }) => void
}

export function SpeechStrength({ onResult }: SpeechStrengthProps) {
  const [transcript, setTranscript] = useState("")
  const [prediction, setPrediction] = useState<SpeechStrengthValue | null>(null)
  const [loading, setLoading] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      audioChunksRef.current = []
      mr.ondataavailable = (e) => audioChunksRef.current.push(e.data)
      mr.start()
      mediaRecorderRef.current = mr
    } catch (e) {
      console.error("Microphone access denied", e)
    }
  }

  const stopRecordingAndAnalyze = async () => {
    if (!mediaRecorderRef.current) return
    const mr = mediaRecorderRef.current
    mr.onstop = async () => {
      const blob = new Blob(audioChunksRef.current, { type: "audio/webm" })
      await analyzeBlob(blob)
      audioChunksRef.current = []
    }
    mr.stop()
    mediaRecorderRef.current = null
  }

  async function analyzeBlob(blob: Blob) {
    setLoading(true)
    try {
      const reader = new FileReader()
      reader.onload = async () => {
        const base64 = reader.result as string
        const res = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ANALYZE_SPEECH_STRENGTH}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ audio: base64 }),
        })
        const json = await res.json()
        setTranscript(json.transcript || "")
        if (json.prediction) {
          setPrediction({ label: json.prediction.label, score: json.prediction.final_score })
          onResult?.({
            transcript: json.transcript || "",
            prediction: { label: json.prediction.label, score: json.prediction.final_score },
          })
        } else {
          onResult?.({ transcript: json.transcript || "", prediction: null })
        }
      }
      reader.readAsDataURL(blob)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files && e.target.files[0]
    if (!f) return
    await analyzeBlob(f)
  }

  return (
    <div className="rounded-xl border p-4 bg-white/[0.03]">
      <h4 className="mb-2 text-sm font-medium text-slate-200">Speech Strength</h4>
      <div className="flex gap-2 mb-3">
        <Button onClick={startRecording} size="sm">Start Mic</Button>
        <Button onClick={stopRecordingAndAnalyze} size="sm">Stop & Analyze</Button>
        <label className="flex items-center gap-2">
          <input type="file" accept="audio/*" onChange={onUpload} />
        </label>
      </div>

      <div className="mb-2 text-sm text-slate-300">Transcription:</div>
      <div className="mb-3 min-h-[48px] text-sm text-white bg-black/20 p-2 rounded">{transcript || "(no transcription yet)"}</div>

      <div className="mb-2 text-sm text-slate-300">Prediction:</div>
      <div className="p-2 rounded">
        {prediction ? (
          <div className={`inline-block px-3 py-1 rounded font-semibold ${prediction.label === 'weak' ? 'bg-red-600 text-white' : prediction.label === 'moderate' ? 'bg-orange-400 text-black' : 'bg-green-600 text-white'}`}>
            {prediction.label} ({(prediction.score || 0).toFixed(2)})
          </div>
        ) : (
          <div className="text-sm text-slate-400">No prediction yet</div>
        )}
      </div>
    </div>
  )
}

export default SpeechStrength

/**
 * Audio Recording Utility
 * Captures audio chunks from MediaStream and provides voice emotion analysis
 */

export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null
  private audioChunks: Blob[] = []
  private stream: MediaStream | null = null
  private isRecording = false
  private audioContext: AudioContext | null = null
  private processor: ScriptProcessorNode | null = null

  constructor(stream: MediaStream) {
    this.stream = stream
  }

  /**
   * Start recording audio from the stream
   */
  start() {
    if (this.stream) {
      try {
        this.mediaRecorder = new MediaRecorder(this.stream)
        this.audioChunks = []
        this.isRecording = true

        this.mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            this.audioChunks.push(event.data)
          }
        }

        this.mediaRecorder.start()
      } catch (error) {
        console.error("Error starting audio recording:", error)
      }
    }
  }

  /**
   * Stop recording and return audio blob
   */
  stop(): Blob | null {
    return new Promise((resolve) => {
      if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.onstop = () => {
          const audioBlob = new Blob(this.audioChunks, { type: "audio/webm" })
          this.audioChunks = []
          this.isRecording = false
          resolve(audioBlob)
        }
        this.mediaRecorder.stop()
      } else {
        resolve(null)
      }
    })
  }

  /**
   * Get audio chunks periodically for analysis (every ~2.5 seconds)
   */
  getAudioChunk(): Blob | null {
    if (this.audioChunks.length > 0) {
      const chunk = new Blob(this.audioChunks, { type: "audio/webm" })
      this.audioChunks = [] // Reset for next chunk
      return chunk
    }
    return null
  }

  /**
   * Convert audio blob to base64 for API transmission
   */
  static async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        const base64 = reader.result as string
        resolve(base64)
      }
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
  }

  /**
   * Send audio chunk for voice emotion analysis
   */
  static async analyzeVoiceEmotion(
    audioBlob: Blob,
    backendUrl: string = "http://localhost:5000"
  ): Promise<{
    emotion: string
    confidence: number
    scores: Record<string, number>
  } | null> {
    try {
      const base64Audio = await this.blobToBase64(audioBlob)

      const response = await fetch(`${backendUrl}/api/analyze/voice-emotion`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          audio: base64Audio,
        }),
      })

      if (!response.ok) {
        console.error("Voice emotion analysis failed:", response.statusText)
        return null
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error("Error analyzing voice emotion:", error)
      return null
    }
  }

  /**
   * Check if browser supports audio recording
   */
  static isSupported(): boolean {
    return typeof MediaRecorder !== "undefined"
  }
}

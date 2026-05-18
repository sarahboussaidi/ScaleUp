"use client"

import { useEffect, useState } from "react"

interface PostureData {
  posture: string
  confidence: number
  landmarks_count?: number
}

interface PosturePanelProps {
  isActive: boolean
  isRecording: boolean
  postureData?: PostureData
}

export function PosturePanel({
  isActive,
  isRecording,
  postureData,
}: PosturePanelProps) {
  const [displayData, setDisplayData] = useState<PostureData>({
    posture: "waiting",
    confidence: 0,
  })

  useEffect(() => {
    if (postureData) {
      setDisplayData(postureData)
    }
  }, [postureData])

  const getPostureColor = (posture: string) => {
    switch (posture?.toLowerCase()) {
      case "good":
      case "correct":
      case "upright":
        return "text-green-400"
      case "bad":
      case "slouch":
      case "bent":
        return "text-red-400"
      case "neutral":
        return "text-yellow-400"
      default:
        return "text-slate-400"
    }
  }

  const getPostureIcon = (posture: string) => {
    switch (posture?.toLowerCase()) {
      case "good":
      case "correct":
      case "upright":
        return "✓"
      case "bad":
      case "slouch":
      case "bent":
        return "✗"
      default:
        return "○"
    }
  }

  return (
    <div className="space-y-4 rounded-lg border border-slate-700/50 bg-slate-900/50 p-4 backdrop-blur">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-slate-300">Posture</h4>
        <span
          className={`text-xs font-semibold ${
            isActive ? "text-green-400" : "text-slate-500"
          }`}
        >
          {isActive ? "●" : "○"} {isActive ? "Analyzing" : "Inactive"}
        </span>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-slate-800/50 px-3 py-2">
          <span className="text-xs text-slate-400">Position</span>
          <span
            className={`text-sm font-semibold capitalize ${getPostureColor(displayData.posture)}`}
          >
            {getPostureIcon(displayData.posture)} {displayData.posture}
          </span>
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Confidence</span>
            <span className="font-mono">
              {(displayData.confidence * 100).toFixed(0)}%
            </span>
          </div>
          <div className="h-1 overflow-hidden rounded-full bg-slate-700">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-300"
              style={{
                width: `${(displayData.confidence || 0) * 100}%`,
              }}
            />
          </div>
        </div>

        {displayData.landmarks_count && (
          <div className="flex items-center justify-between rounded-lg bg-slate-800/30 px-3 py-2 text-xs text-slate-400">
            <span>Landmarks Detected</span>
            <span className="font-mono text-blue-400">
              {displayData.landmarks_count}
            </span>
          </div>
        )}
      </div>

      {isRecording && (
        <div className="flex items-center gap-2 rounded-lg bg-red-900/20 px-3 py-2 text-xs text-red-300">
          <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-red-500" />
          Recording posture analysis
        </div>
      )}
    </div>
  )
}

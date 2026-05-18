"use client"

import { useState, useCallback } from "react"
import { GlassmorphismNav } from "@/components/glassmorphism-nav"
import Aurora from "@/components/Aurora"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Upload,
  Image as ImageIcon,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  TrendingUp,
  Target,
  Loader2,
  X,
  Instagram,
  Facebook,
  Twitter,
  Linkedin,
} from "lucide-react"

interface AnalysisResult {
  overallScore: number
  engagement: {
    score: number
    feedback: string
  }
  visualAppeal: {
    score: number
    feedback: string
  }
  copywriting: {
    score: number
    feedback: string
  }
  callToAction: {
    score: number
    feedback: string
  }
  suggestions: string[]
  platform: string
  raw: any
}

export default function MarketingAnalysisPage() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [fileInputKey, setFileInputKey] = useState(0)
  const [isDragging, setIsDragging] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [selectedPlatform, setSelectedPlatform] = useState<string>("instagram")
  const [analysisError, setAnalysisError] = useState<string | null>(null)

  const marketingApiBase = (process.env.NEXT_PUBLIC_MARKETING_API_URL || "http://127.0.0.1:5000").replace(/\/$/, "")
  const marketingEvaluateEndpoint = `${marketingApiBase}/api/marketing/analyze`

  const formatFeatureValue = (value: unknown) => {
    if (typeof value === "number") {
      return Number.isInteger(value) ? value.toString() : value.toFixed(1)
    }

    if (typeof value === "string") {
      return value
    }

    if (typeof value === "boolean") {
      return value ? "Yes" : "No"
    }

    if (value && typeof value === "object") {
      const objectValue = value as Record<string, unknown>
      const score = objectValue.score ?? objectValue.value ?? objectValue.overall_score

      if (typeof score === "number") {
        return Number.isInteger(score) ? score.toString() : score.toFixed(1)
      }

      if (typeof score === "string") {
        return score
      }

      return "Available"
    }

    return "N/A"
  }

  const mapBackendResultToUi = (result: any): AnalysisResult => {
    const textEvaluation = result?.text_evaluation || {}
    const visualEvaluation = result?.visual_evaluation || {}
    const textXai = result?.text_xai || {}
    const visualXai = result?.visual_xai || {}
    const overallEngagement = result?.overall_engagement || {}

    const textScore = Number(textEvaluation.overall_score ?? textXai.overall_score ?? 0)
    const visualScore = Number(visualEvaluation.overall_score ?? result?.visual_features?.score_0_10 ?? visualXai.visual_prediction?.score_0_10 ?? 0)
    const overallScore = Number(overallEngagement.score ?? overallEngagement.overall_score_0_10 ?? ((textScore + visualScore) / 2))

    const featureMetrics = textXai.feature_metrics || {}
    const hasCta = Boolean(featureMetrics.has_cta)
    const issues = textEvaluation.issues || textXai.issues_detected || {}
    const dimensionScores = textEvaluation.dimensions || textEvaluation.dimension_scores || textXai.dimension_scores || {}

    const textLabel = textXai.interpretation || textEvaluation.overall_label || "unknown"
    const visualLabel = visualEvaluation.class_label || result?.visual_features?.class_label || visualXai.visual_prediction?.class_label || "unknown"
    const engagementLabel = overallEngagement.verdict || "Mixed"

    const textSummary = `Text quality rated as "${textLabel}". ` +
      (textScore >= 7 ? "Strong copywriting with good structure." : textScore >= 5 ? "Moderate text quality." : "Text could be improved for better engagement.")

    const visualSummary = `Visual quality rated as "${visualLabel}". ` +
      (visualScore >= 9 ? "Excellent visual composition and design." : visualScore >= 7 ? "Good visual appeal." : "Visual could benefit from better composition.")

    const suggestions = [
      issues.low_readability ? "Simplify the text for better readability. Consider shorter sentences and clearer language." : null,
      issues.too_short ? "The text is too short. Add more context to improve engagement." : null,
      issues.too_long ? "The text is quite long. Consider breaking it into shorter, punchier segments." : null,
      issues.too_many_hashtags ? "Too many hashtags detected. Consider reducing to 5-10 most relevant ones." : null,
      issues.weak_cta ? "Strengthen the call-to-action to make it more compelling." : null,
      !hasCta ? "Consider adding a clear call-to-action to guide audience engagement." : null,
      dimensionScores.readability < 3 ? "Improve readability by using simpler vocabulary and shorter sentences." : null,
      dimensionScores.sentiment && dimensionScores.sentiment < 4 ? "Consider adding more positive sentiment to the copy." : null,
      visualScore < 7 ? "Enhance visual composition: improve contrast, balance, and focal points." : null,
      visualScore >= 9 && textScore >= 7 ? "Excellent balance! Keep this format for future posts." : null,
    ].filter((item): item is string => Boolean(item))

    return {
      overallScore: Math.round(overallScore),
      engagement: {
        score: Math.round(overallScore),
        feedback: `Engagement outlook: ${engagementLabel}. ${textSummary}`,
      },
      visualAppeal: {
        score: Number(visualScore.toFixed(1)),
        feedback: visualSummary,
      },
      copywriting: {
        score: Number(textScore.toFixed(1)),
        feedback: textSummary,
      },
      callToAction: {
        score: hasCta ? 8.5 : 4,
        feedback: hasCta
          ? "A call-to-action is present in the text."
          : "No clear call-to-action detected. Consider adding one.",
      },
      suggestions: suggestions.length > 0 ? suggestions : ["The post looks great! Continue testing variations to maintain engagement."],
      platform: result?.platform_selected || result?.platform || selectedPlatform,
      raw: result,
    }
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && droppedFile.type.startsWith("image/")) {
      setFile(droppedFile)
      setPreview(URL.createObjectURL(droppedFile))
      setAnalysisResult(null)
      setAnalysisError(null)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setPreview(URL.createObjectURL(selectedFile))
      setAnalysisResult(null)
      setAnalysisError(null)
      setFileInputKey((value) => value + 1)
    }
  }

  const analyzePost = async () => {
    if (!file) return
    setIsAnalyzing(true)
    setAnalysisError(null)

    try {
      const formData = new FormData()
      formData.append("screenshot", file)
      formData.append("platform", selectedPlatform)

      const response = await fetch(marketingEvaluateEndpoint, {
        method: "POST",
        body: formData,
      })

      const contentType = response.headers.get("content-type") || ""
      const responseText = await response.text()
      const payload = contentType.includes("application/json")
        ? JSON.parse(responseText)
        : null

      if (!response.ok || payload?.success === false) {
        throw new Error(payload?.error || responseText || "Marketing analysis failed")
      }

      setAnalysisResult(mapBackendResultToUi(payload))
    } catch (error) {
      const message = error instanceof Error ? error.message : "Marketing analysis failed"
      
      // Check if it's a connection error
      if (error instanceof TypeError && error.message.includes("fetch")) {
        setAnalysisError(
          "⚠️ Cannot connect to backend. Please ensure:\n" +
          "1. The ScaleUp backend is running: python backend/app.py\n" +
          "2. Backend is accessible at http://127.0.0.1:5000\n" +
          "3. The evaluation route exists at /evaluate\n" +
          "4. Check browser console for more details"
        )
      } else {
        setAnalysisError(message)
      }
      setAnalysisResult(null)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const clearFile = () => {
    setFile(null)
    setPreview(null)
    setAnalysisResult(null)
    setAnalysisError(null)
    setFileInputKey((value) => value + 1)
  }

  const getScoreColor = (score: number) => {
    if (score >= 8) return "text-green-400"
    if (score >= 6) return "text-yellow-400"
    return "text-red-400"
  }

  const getScoreBg = (score: number) => {
    if (score >= 8) return "bg-green-500/20 border-green-500/30"
    if (score >= 6) return "bg-yellow-500/20 border-yellow-500/30"
    return "bg-red-500/20 border-red-500/30"
  }

  const platforms = [
    { id: "instagram", name: "Instagram", icon: Instagram },
    { id: "facebook", name: "Facebook", icon: Facebook },
    { id: "twitter", name: "Twitter/X", icon: Twitter },
    { id: "linkedin", name: "LinkedIn", icon: Linkedin },
  ]

  const textFeatureEntries = Object.entries(analysisResult?.raw?.text_evaluation?.dimensions || {})

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
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium mb-6">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Social Media Analysis
                </div>
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
                  AI-Powered{" "}
                  <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                    Marketing Feedback
                  </span>
                </h1>
                <p className="text-lg text-white/70 max-w-2xl mx-auto">
                  Upload screenshots of your social media posts and get instant AI feedback on engagement potential,
                  visual appeal, copywriting, and more.
                </p>
                {analysisError ? (
                  <div className="mt-4 text-sm text-red-300 max-w-2xl mx-auto bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 whitespace-pre-wrap">
                    {analysisError}
                  </div>
                ) : null}

                {/* Brand Guidelines CTA */}
                <div className="mt-8 flex justify-center">
                  <a href="/branding-generator">
                    <Button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-8 py-3 rounded-lg transition-all">
                      ✨ Create Brand Guidelines
                    </Button>
                  </a>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Upload Section */}
                <div className="space-y-6">
                  {/* Platform Selection */}
                  <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Target className="w-5 h-5 text-indigo-400" />
                        Select Platform
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        {platforms.map((platform) => (
                          <button
                            key={platform.id}
                            onClick={() => setSelectedPlatform(platform.id)}
                            className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition-all duration-300 ${
                              selectedPlatform === platform.id
                                ? "bg-indigo-500/20 border-indigo-500/50"
                                : "bg-white/5 border-white/10 hover:border-indigo-500/30"
                            }`}
                          >
                            <platform.icon
                              className={`w-6 h-6 ${selectedPlatform === platform.id ? "text-indigo-400" : "text-white/60"}`}
                            />
                            <span
                              className={`text-sm font-medium ${selectedPlatform === platform.id ? "text-white" : "text-white/60"}`}
                            >
                              {platform.name}
                            </span>
                          </button>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Upload Area */}
                  <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Upload className="w-5 h-5 text-indigo-400" />
                        Upload Screenshot
                      </CardTitle>
                      <CardDescription className="text-white/60">
                        Upload a screenshot of your social media post
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {!file ? (
                        <div
                          onDragOver={handleDragOver}
                          onDragLeave={handleDragLeave}
                          onDrop={handleDrop}
                          className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
                            isDragging
                              ? "border-indigo-400 bg-indigo-500/10"
                              : "border-white/20 hover:border-indigo-400/50"
                          }`}
                        >
                          <ImageIcon className="w-12 h-12 text-indigo-400 mx-auto mb-4" />
                          <p className="text-white/70 mb-4">Drag and drop your screenshot here, or</p>
                          <label className="cursor-pointer">
                            <input
                              key={fileInputKey}
                              type="file"
                              accept="image/*"
                              onChange={handleFileSelect}
                              className="hidden"
                            />
                            <span className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-full font-medium transition-all duration-300 hover:scale-105">
                              Browse Files
                            </span>
                          </label>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          <div className="relative rounded-xl overflow-hidden border border-white/10">
                            <img
                              src={preview || ""}
                              alt="Post preview"
                              className="w-full h-auto max-h-80 object-contain bg-black/20"
                            />
                            <button
                              onClick={clearFile}
                              className="absolute top-2 right-2 p-2 bg-black/50 rounded-full hover:bg-black/70 transition-colors"
                            >
                              <X className="w-4 h-4 text-white" />
                            </button>
                          </div>
                          <Button
                            onClick={analyzePost}
                            disabled={isAnalyzing}
                            className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                          >
                            {isAnalyzing ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Analyzing Post...
                              </>
                            ) : (
                              <>
                                <TrendingUp className="w-4 h-4 mr-2" />
                                Analyze Post
                              </>
                            )}
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Results Section */}
                <div className="space-y-6">
                  {analysisResult ? (
                    <>
                      {/* Overall Score */}
                      <Card className={`border ${getScoreBg(analysisResult.overallScore)}`}>
                        <CardContent className="p-6">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-white/60 text-sm mb-1">Overall Score</p>
                              <p className={`text-4xl font-bold ${getScoreColor(analysisResult.overallScore)}`}>
                                {analysisResult.overallScore}/10
                              </p>
                            </div>
                            <div
                              className={`w-20 h-20 rounded-full border-4 flex items-center justify-center ${
                                analysisResult.overallScore >= 8
                                  ? "border-green-400"
                                  : analysisResult.overallScore >= 6
                                    ? "border-yellow-400"
                                    : "border-red-400"
                              }`}
                            >
                              {analysisResult.overallScore >= 7 ? (
                                <ThumbsUp className={`w-8 h-8 ${getScoreColor(analysisResult.overallScore)}`} />
                              ) : (
                                <ThumbsDown className={`w-8 h-8 ${getScoreColor(analysisResult.overallScore)}`} />
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      {/* Detailed Scores */}
                      <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                        <CardHeader>
                          <CardTitle className="text-white">Detailed Analysis</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          {[
                            { label: "Engagement Potential", data: analysisResult.engagement },
                            { label: "Visual Appeal", data: analysisResult.visualAppeal },
                            { label: "Copywriting", data: analysisResult.copywriting },
                            { label: "Call to Action", data: analysisResult.callToAction },
                          ].map((item, index) => (
                            <div key={index} className="p-4 bg-white/5 rounded-xl border border-white/10">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-white font-medium">{item.label}</span>
                                <span className={`font-bold ${getScoreColor(item.data.score)}`}>
                                  {item.data.score}/10
                                </span>
                              </div>
                              <div className="w-full bg-white/10 rounded-full h-2 mb-3">
                                <div
                                  className={`h-2 rounded-full transition-all duration-500 ${
                                    item.data.score >= 8
                                      ? "bg-green-400"
                                      : item.data.score >= 6
                                        ? "bg-yellow-400"
                                        : "bg-red-400"
                                  }`}
                                    style={{ width: `${Math.min(Number(item.data.score) * 10, 100)}%` }}
                                />
                              </div>
                              <p className="text-white/60 text-sm">{item.data.feedback}</p>
                            </div>
                          ))}
                        </CardContent>
                      </Card>

                      {/* Dimension Scores */}
                      {Object.keys(analysisResult.raw?.text_evaluation?.dimension_scores || {}).length > 0 && (
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader>
                            <CardTitle className="text-white">Text Analysis Dimensions</CardTitle>
                            <CardDescription className="text-white/60">
                              Detailed breakdown of text quality metrics
                            </CardDescription>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            {Object.entries(analysisResult.raw?.text_evaluation?.dimension_scores || {}).map(([dimension, score]: [string, any], index) => (
                              <div key={index} className="p-3 bg-white/5 rounded-lg border border-white/10">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-white/80 capitalize text-sm font-medium">{dimension}</span>
                                  <span className={`text-sm font-bold ${Number(score) >= 7 ? 'text-green-400' : Number(score) >= 5 ? 'text-yellow-400' : 'text-red-400'}`}>
                                    {Number(score).toFixed(1)}/10
                                  </span>
                                </div>
                                <div className="w-full bg-white/10 rounded-full h-1.5">
                                  <div
                                    className={`h-1.5 rounded-full transition-all ${
                                      Number(score) >= 7 ? 'bg-green-400' : Number(score) >= 5 ? 'bg-yellow-400' : 'bg-red-400'
                                    }`}
                                    style={{ width: `${Math.min(Number(score), 10)}%` }}
                                  />
                                </div>
                              </div>
                            ))}
                          </CardContent>
                        </Card>
                      )}

                      {/* Suggestions */}
                      <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                        <CardHeader>
                          <CardTitle className="text-white flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-indigo-400" />
                            Improvement Suggestions
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ul className="space-y-3">
                            {analysisResult.suggestions.map((suggestion, index) => (
                              <li key={index} className="flex items-start gap-3">
                                <div className="w-6 h-6 rounded-full bg-indigo-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                  <span className="text-indigo-400 text-xs font-bold">{index + 1}</span>
                                </div>
                                <span className="text-white/70">{suggestion}</span>
                              </li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>

                      {/* Notebook Output Details */}
                      <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                        <CardHeader>
                          <CardTitle className="text-white">Notebook Output Details</CardTitle>
                          <CardDescription className="text-white/60">
                            Full outputs from the original notebooks marketing pipeline
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                          <div className="grid grid-cols-1 gap-4">
                            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                              <h4 className="text-white font-medium mb-2">Extracted Text</h4>
                              <p className="text-white/70 text-sm whitespace-pre-wrap">
                                {analysisResult.raw?.text_evaluation?.ocr_text_full || analysisResult.raw?.text_evaluation?.ocr_text || "No OCR text returned."}
                              </p>
                            </div>

                            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                              <h4 className="text-white font-medium mb-2">Backend Extracted Image</h4>
                              {analysisResult.raw?.visual_evaluation?.extracted_image ? (
                                <img
                                  src={`data:image/png;base64,${analysisResult.raw?.visual_evaluation?.extracted_image}`}
                                  alt="Extracted visual content"
                                  className="w-full rounded-lg border border-white/10 bg-black/20"
                                />
                              ) : (
                                <p className="text-white/50 text-sm">No extracted crop was returned by the backend.</p>
                              )}
                            </div>
                          </div>

                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            <div className="p-4 bg-white/5 rounded-xl border border-white/10 overflow-hidden">
                              <h4 className="text-white font-medium mb-3">Text Feature Scores</h4>
                              {textFeatureEntries.length > 0 ? (
                                <div className="space-y-3">
                                  {textFeatureEntries.map(([feature, value]) => (
                                    <div key={feature} className="flex items-center justify-between gap-4 rounded-lg border border-white/10 bg-black/20 px-4 py-3">
                                      <span className="text-sm text-white/80 capitalize">
                                        {feature.replace(/_/g, " ")}
                                      </span>
                                      <span className="text-sm font-medium text-indigo-300">
                                        {formatFeatureValue(value)}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-white/50">No text feature scores available.</p>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </>
                  ) : (
                    <Card className="bg-white/5 backdrop-blur-xl border-white/10 h-full min-h-[400px] flex items-center justify-center">
                      <CardContent className="text-center p-8">
                        <MessageSquare className="w-16 h-16 text-white/20 mx-auto mb-4" />
                        <h3 className="text-xl font-semibold text-white/60 mb-2">No Analysis Yet</h3>
                        <p className="text-white/40">
                          Upload a screenshot of your social media post to get AI-powered feedback
                        </p>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </div>
            </div>
          </section>

          <Footer />
        </div>
      </main>
    </div>
  )
}

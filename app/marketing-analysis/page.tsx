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
}

export default function MarketingAnalysisPage() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [selectedPlatform, setSelectedPlatform] = useState<string>("instagram")

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
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setPreview(URL.createObjectURL(selectedFile))
      setAnalysisResult(null)
    }
  }

  const analyzePost = async () => {
    if (!file) return
    setIsAnalyzing(true)

    // Simulate AI analysis
    await new Promise((resolve) => setTimeout(resolve, 2500))

    const mockResult: AnalysisResult = {
      overallScore: 78,
      engagement: {
        score: 82,
        feedback:
          "Good use of engaging elements. The visual hierarchy draws attention effectively. Consider adding more interactive elements like polls or questions in your caption.",
      },
      visualAppeal: {
        score: 85,
        feedback:
          "Strong color contrast and composition. The image is well-lit and professionally edited. Consider using more brand-consistent colors for better recognition.",
      },
      copywriting: {
        score: 72,
        feedback:
          "Caption is decent but could be more compelling. Try starting with a hook or question. Use more action verbs and emotional triggers.",
      },
      callToAction: {
        score: 65,
        feedback:
          "CTA is present but could be stronger. Consider using urgency words like 'now' or 'today'. Make the action clear and specific.",
      },
      suggestions: [
        "Add relevant hashtags (8-15 recommended for Instagram)",
        "Include a clear call-to-action in the first line",
        "Consider using carousel format for higher engagement",
        "Add location tag to increase discoverability",
        "Post during peak hours (6-9 PM for your audience)",
        "Use brand colors consistently across all posts",
      ],
      platform: selectedPlatform,
    }

    setAnalysisResult(mockResult)
    setIsAnalyzing(false)
  }

  const clearFile = () => {
    setFile(null)
    setPreview(null)
    setAnalysisResult(null)
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-400"
    if (score >= 60) return "text-yellow-400"
    return "text-red-400"
  }

  const getScoreBg = (score: number) => {
    if (score >= 80) return "bg-green-500/20 border-green-500/30"
    if (score >= 60) return "bg-yellow-500/20 border-yellow-500/30"
    return "bg-red-500/20 border-red-500/30"
  }

  const platforms = [
    { id: "instagram", name: "Instagram", icon: Instagram },
    { id: "facebook", name: "Facebook", icon: Facebook },
    { id: "twitter", name: "Twitter/X", icon: Twitter },
    { id: "linkedin", name: "LinkedIn", icon: Linkedin },
  ]

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
                                {analysisResult.overallScore}/100
                              </p>
                            </div>
                            <div
                              className={`w-20 h-20 rounded-full border-4 flex items-center justify-center ${
                                analysisResult.overallScore >= 80
                                  ? "border-green-400"
                                  : analysisResult.overallScore >= 60
                                    ? "border-yellow-400"
                                    : "border-red-400"
                              }`}
                            >
                              {analysisResult.overallScore >= 70 ? (
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
                                  {item.data.score}/100
                                </span>
                              </div>
                              <div className="w-full bg-white/10 rounded-full h-2 mb-3">
                                <div
                                  className={`h-2 rounded-full transition-all duration-500 ${
                                    item.data.score >= 80
                                      ? "bg-green-400"
                                      : item.data.score >= 60
                                        ? "bg-yellow-400"
                                        : "bg-red-400"
                                  }`}
                                  style={{ width: `${item.data.score}%` }}
                                />
                              </div>
                              <p className="text-white/60 text-sm">{item.data.feedback}</p>
                            </div>
                          ))}
                        </CardContent>
                      </Card>

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

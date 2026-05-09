"use client"

import { useState, useCallback } from "react"
import { GlassmorphismNav } from "@/components/glassmorphism-nav"
import Aurora from "@/components/Aurora"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import {
  Upload,
  Image as ImageIcon,
  Layers,
  Sparkles,
  Loader2,
  X,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Users,
  DollarSign,
  Heart,
  Package,
  Truck,
  MessageSquare,
  Handshake,
  Cog,
} from "lucide-react"

interface BMCBox {
  id: string
  name: string
  icon: React.ElementType
  score: number
  content: string
  feedback: string
  suggestions: string[]
}

interface BMCAnalysis {
  overallScore: number
  boxes: BMCBox[]
  strengths: string[]
  weaknesses: string[]
}

interface GeneratedBMC {
  keyPartners: string
  keyActivities: string
  keyResources: string
  valuePropositions: string
  customerRelationships: string
  channels: string
  customerSegments: string
  costStructure: string
  revenueStreams: string
}

export default function BMCPage() {
  const [activeTab, setActiveTab] = useState<"analyze" | "generate">("analyze")

  // Analysis state
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<BMCAnalysis | null>(null)

  // Generation state
  const [businessIdea, setBusinessIdea] = useState("")
  const [industry, setIndustry] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedBMC, setGeneratedBMC] = useState<GeneratedBMC | null>(null)

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
      setAnalysis(null)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setPreview(URL.createObjectURL(selectedFile))
      setAnalysis(null)
    }
  }

  const analyzeBMC = async () => {
    if (!file) return
    setIsAnalyzing(true)

    await new Promise((resolve) => setTimeout(resolve, 3000))

    const mockAnalysis: BMCAnalysis = {
      overallScore: 74,
      boxes: [
        {
          id: "key-partners",
          name: "Key Partners",
          icon: Handshake,
          score: 72,
          content: "Technology vendors, Local incubators, Government agencies",
          feedback: "Good partner identification but lacking strategic depth.",
          suggestions: ["Add financial institutions for funding partnerships", "Consider academic partnerships"],
        },
        {
          id: "key-activities",
          name: "Key Activities",
          icon: Cog,
          score: 68,
          content: "Platform development, Customer support, Marketing",
          feedback: "Activities are generic. Need more specificity.",
          suggestions: ["Define core differentiating activities", "Add quality assurance processes"],
        },
        {
          id: "key-resources",
          name: "Key Resources",
          icon: Package,
          score: 75,
          content: "AI technology, Development team, Brand",
          feedback: "Resources are identified but intellectual property not mentioned.",
          suggestions: ["Include IP and proprietary algorithms", "Add human capital details"],
        },
        {
          id: "value-propositions",
          name: "Value Propositions",
          icon: Heart,
          score: 82,
          content: "AI-powered business validation, Time savings, Expert-level insights",
          feedback: "Strong value propositions well articulated.",
          suggestions: ["Quantify the value (e.g., '80% faster')", "Add competitive differentiation"],
        },
        {
          id: "customer-relationships",
          name: "Customer Relationships",
          icon: MessageSquare,
          score: 70,
          content: "Self-service platform, Email support, Community forum",
          feedback: "Adequate but could be more personalized.",
          suggestions: ["Add onboarding assistance", "Consider dedicated success managers for enterprise"],
        },
        {
          id: "channels",
          name: "Channels",
          icon: Truck,
          score: 78,
          content: "Website, Social media, Partner referrals, Events",
          feedback: "Multi-channel approach is good.",
          suggestions: ["Add mobile app channel", "Consider B2B partnerships for distribution"],
        },
        {
          id: "customer-segments",
          name: "Customer Segments",
          icon: Users,
          score: 80,
          content: "Early-stage startups, Student entrepreneurs, SMEs",
          feedback: "Well-defined segments with clear focus.",
          suggestions: ["Define personas for each segment", "Identify highest-value segment"],
        },
        {
          id: "cost-structure",
          name: "Cost Structure",
          icon: DollarSign,
          score: 65,
          content: "Development costs, Marketing, Infrastructure",
          feedback: "Cost categories identified but no prioritization.",
          suggestions: ["Add fixed vs variable cost breakdown", "Include customer acquisition cost"],
        },
        {
          id: "revenue-streams",
          name: "Revenue Streams",
          icon: TrendingUp,
          score: 73,
          content: "Subscription fees, Enterprise licenses, Premium features",
          feedback: "Multiple revenue streams identified.",
          suggestions: ["Add pricing tiers details", "Consider freemium conversion metrics"],
        },
      ],
      strengths: [
        "Strong value proposition clarity",
        "Well-defined customer segments",
        "Multi-channel distribution strategy",
      ],
      weaknesses: [
        "Cost structure needs more detail",
        "Key activities are too generic",
        "Customer relationships could be more personalized",
      ],
    }

    setAnalysis(mockAnalysis)
    setIsAnalyzing(false)
  }

  const generateBMC = async () => {
    if (!businessIdea.trim()) return
    setIsGenerating(true)

    await new Promise((resolve) => setTimeout(resolve, 2500))

    const mockBMC: GeneratedBMC = {
      keyPartners: `• Technology infrastructure providers (AWS, Google Cloud)
• Local startup incubators and accelerators in Tunisia
• Tunisian government agencies (APII, Startup Tunisia)
• Academic institutions for talent and research
• Payment processors (local and international)
• Industry-specific consultants`,
      keyActivities: `• AI model development and training
• Platform development and maintenance
• Customer success and onboarding
• Content creation for startup education
• Partnership development
• Continuous product improvement based on feedback`,
      keyResources: `• Proprietary AI algorithms and models
• Technical development team
• Customer success team
• Brand and market presence
• Data assets and training datasets
• Intellectual property (patents, trade secrets)`,
      valuePropositions: `• 80% faster business validation vs traditional methods
• AI-powered insights at a fraction of consulting costs
• 24/7 availability for busy entrepreneurs
• Localized for Tunisian market and regulations
• All-in-one platform for startup needs
• Expert-level analysis accessible to anyone`,
      customerRelationships: `• Self-service platform with guided onboarding
• Email and chat support
• Community forum for peer learning
• Dedicated account managers for enterprise
• Regular webinars and educational content
• Feedback loops for product improvement`,
      channels: `• Direct website and web app
• Mobile application (iOS/Android)
• Social media (LinkedIn, Facebook, Instagram)
• Startup events and competitions
• Partner referral networks
• Content marketing (blog, YouTube)`,
      customerSegments: `• Early-stage startups (0-2 years)
• Student entrepreneurs at universities
• Small and medium enterprises looking to innovate
• Corporate innovation teams
• Freelancers and solopreneurs
• Startup incubator programs`,
      costStructure: `• Cloud infrastructure and hosting (30%)
• Development team salaries (35%)
• Marketing and customer acquisition (20%)
• Customer support operations (10%)
• Legal and compliance (5%)
• Fixed costs: Office, licenses, tools`,
      revenueStreams: `• Freemium subscription model
  - Free: Basic features
  - Startup: $49/month
  - Enterprise: $199/month
• One-time consulting packages
• API access for B2B clients
• White-label solutions for incubators`,
    }

    setGeneratedBMC(mockBMC)
    setIsGenerating(false)
  }

  const clearFile = () => {
    setFile(null)
    setPreview(null)
    setAnalysis(null)
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

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      <main className="min-h-screen relative overflow-hidden">
        <div className="fixed inset-0 w-full h-full">
          <Aurora colorStops={["#1e1b4b", "#4c1d95", "#312e81"]} amplitude={1.2} blend={0.6} speed={0.8} />
        </div>
        <div className="relative z-10">
          <GlassmorphismNav />

          <section className="pt-32 pb-16 px-4">
            <div className="max-w-7xl mx-auto">
              {/* Header */}
              <div className="text-center mb-12">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm font-medium mb-6">
                  <Layers className="w-4 h-4 mr-2" />
                  Business Model Canvas
                </div>
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
                  AI-Powered{" "}
                  <span className="bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
                    BMC Tools
                  </span>
                </h1>
                <p className="text-lg text-white/70 max-w-2xl mx-auto">
                  Upload your Business Model Canvas for detailed feedback, or generate a new one from your business
                  idea.
                </p>
              </div>

              {/* Tabs */}
              <div className="flex gap-2 p-1 bg-white/5 backdrop-blur-xl rounded-xl border border-white/10 max-w-md mx-auto mb-8">
                <button
                  onClick={() => setActiveTab("analyze")}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all duration-300 ${
                    activeTab === "analyze"
                      ? "bg-gradient-to-r from-purple-500 to-indigo-600 text-white"
                      : "text-white/60 hover:text-white hover:bg-white/10"
                  }`}
                >
                  <Upload className="w-4 h-4" />
                  Analyze BMC
                </button>
                <button
                  onClick={() => setActiveTab("generate")}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all duration-300 ${
                    activeTab === "generate"
                      ? "bg-gradient-to-r from-purple-500 to-indigo-600 text-white"
                      : "text-white/60 hover:text-white hover:bg-white/10"
                  }`}
                >
                  <Sparkles className="w-4 h-4" />
                  Generate BMC
                </button>
              </div>

              {activeTab === "analyze" ? (
                <div className="space-y-8">
                  {/* Upload Section */}
                  <Card className="bg-white/5 backdrop-blur-xl border-white/10 max-w-2xl mx-auto">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Upload className="w-5 h-5 text-purple-400" />
                        Upload Your BMC
                      </CardTitle>
                      <CardDescription className="text-white/60">
                        Upload a picture or screenshot of your Business Model Canvas
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
                              ? "border-purple-400 bg-purple-500/10"
                              : "border-white/20 hover:border-purple-400/50"
                          }`}
                        >
                          <ImageIcon className="w-12 h-12 text-purple-400 mx-auto mb-4" />
                          <p className="text-white/70 mb-4">Drag and drop your BMC image here, or</p>
                          <label className="cursor-pointer">
                            <input type="file" accept="image/*" onChange={handleFileSelect} className="hidden" />
                            <span className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white rounded-full font-medium transition-all duration-300 hover:scale-105">
                              Browse Files
                            </span>
                          </label>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          <div className="relative rounded-xl overflow-hidden border border-white/10">
                            <img
                              src={preview || ""}
                              alt="BMC preview"
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
                            onClick={analyzeBMC}
                            disabled={isAnalyzing}
                            className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white"
                          >
                            {isAnalyzing ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Analyzing BMC...
                              </>
                            ) : (
                              <>
                                <Layers className="w-4 h-4 mr-2" />
                                Analyze BMC
                              </>
                            )}
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Analysis Results */}
                  {analysis && (
                    <div className="space-y-6">
                      {/* Overall Score */}
                      <Card className={`border ${getScoreBg(analysis.overallScore)} max-w-2xl mx-auto`}>
                        <CardContent className="p-6">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-white/60 text-sm mb-1">Overall BMC Score</p>
                              <p className={`text-4xl font-bold ${getScoreColor(analysis.overallScore)}`}>
                                {analysis.overallScore}/100
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-white/60 text-sm mb-2">Key Findings</p>
                              <div className="flex items-center gap-2 text-sm">
                                <CheckCircle className="w-4 h-4 text-green-400" />
                                <span className="text-green-400">{analysis.strengths.length} Strengths</span>
                                <AlertTriangle className="w-4 h-4 text-yellow-400 ml-2" />
                                <span className="text-yellow-400">{analysis.weaknesses.length} Areas to Improve</span>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      {/* Box-by-Box Analysis */}
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {analysis.boxes.map((box) => (
                          <Card key={box.id} className="bg-white/5 backdrop-blur-xl border-white/10">
                            <CardHeader className="pb-2">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <box.icon className="w-5 h-5 text-purple-400" />
                                  <CardTitle className="text-white text-base">{box.name}</CardTitle>
                                </div>
                                <span className={`font-bold ${getScoreColor(box.score)}`}>{box.score}</span>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-3">
                              <div className="w-full bg-white/10 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full transition-all duration-500 ${
                                    box.score >= 80
                                      ? "bg-green-400"
                                      : box.score >= 60
                                        ? "bg-yellow-400"
                                        : "bg-red-400"
                                  }`}
                                  style={{ width: `${box.score}%` }}
                                />
                              </div>
                              <p className="text-white/60 text-sm">{box.feedback}</p>
                              <div className="pt-2 border-t border-white/10">
                                <p className="text-xs text-purple-300 mb-1">Suggestions:</p>
                                <ul className="space-y-1">
                                  {box.suggestions.map((sug, i) => (
                                    <li key={i} className="text-white/50 text-xs flex items-start gap-1">
                                      <span className="text-purple-400">•</span>
                                      {sug}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                /* Generate Tab */
                <div className="max-w-4xl mx-auto space-y-8">
                  <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-purple-400" />
                        Generate Business Model Canvas
                      </CardTitle>
                      <CardDescription className="text-white/60">
                        Enter your business idea and let AI generate a complete BMC
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <label className="text-white/70 text-sm mb-2 block">Business Idea</label>
                        <Textarea
                          placeholder="Describe your business idea... (e.g., 'An AI platform that helps Tunisian startups validate their business models')"
                          value={businessIdea}
                          onChange={(e) => setBusinessIdea(e.target.value)}
                          className="bg-white/5 border-white/10 text-white placeholder:text-white/40 min-h-[100px]"
                        />
                      </div>
                      <div>
                        <label className="text-white/70 text-sm mb-2 block">Industry (optional)</label>
                        <Input
                          placeholder="e.g., Technology, Healthcare, Education"
                          value={industry}
                          onChange={(e) => setIndustry(e.target.value)}
                          className="bg-white/5 border-white/10 text-white placeholder:text-white/40"
                        />
                      </div>
                      <Button
                        onClick={generateBMC}
                        disabled={isGenerating || !businessIdea.trim()}
                        className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white"
                      >
                        {isGenerating ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Generating BMC...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4 mr-2" />
                            Generate BMC
                          </>
                        )}
                      </Button>
                    </CardContent>
                  </Card>

                  {generatedBMC && (
                    <div className="space-y-4">
                      <h3 className="text-xl font-bold text-white">Generated Business Model Canvas</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Row 1 */}
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-white text-sm flex items-center gap-2">
                              <Handshake className="w-4 h-4 text-purple-400" />
                              Key Partners
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-white/70 text-sm whitespace-pre-line">{generatedBMC.keyPartners}</p>
                          </CardContent>
                        </Card>
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-white text-sm flex items-center gap-2">
                              <Cog className="w-4 h-4 text-purple-400" />
                              Key Activities
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-white/70 text-sm whitespace-pre-line">{generatedBMC.keyActivities}</p>
                          </CardContent>
                        </Card>
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-white text-sm flex items-center gap-2">
                              <Heart className="w-4 h-4 text-purple-400" />
                              Value Propositions
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-white/70 text-sm whitespace-pre-line">
                              {generatedBMC.valuePropositions}
                            </p>
                          </CardContent>
                        </Card>
                        {/* Row 2 */}
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-white text-sm flex items-center gap-2">
                              <Package className="w-4 h-4 text-purple-400" />
                              Key Resources
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-white/70 text-sm whitespace-pre-line">{generatedBMC.keyResources}</p>
                          </CardContent>
                        </Card>
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-white text-sm flex items-center gap-2">
                              <MessageSquare className="w-4 h-4 text-purple-400" />
                              Customer Relationships
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-white/70 text-sm whitespace-pre-line">
                              {generatedBMC.customerRelationships}
                            </p>
                          </CardContent>
                        </Card>
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-white text-sm flex items-center gap-2">
                              <Users className="w-4 h-4 text-purple-400" />
                              Customer Segments
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-white/70 text-sm whitespace-pre-line">
                              {generatedBMC.customerSegments}
                            </p>
                          </CardContent>
                        </Card>
                        {/* Row 3 */}
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-white text-sm flex items-center gap-2">
                              <Truck className="w-4 h-4 text-purple-400" />
                              Channels
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-white/70 text-sm whitespace-pre-line">{generatedBMC.channels}</p>
                          </CardContent>
                        </Card>
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-white text-sm flex items-center gap-2">
                              <DollarSign className="w-4 h-4 text-purple-400" />
                              Cost Structure
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-white/70 text-sm whitespace-pre-line">{generatedBMC.costStructure}</p>
                          </CardContent>
                        </Card>
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-white text-sm flex items-center gap-2">
                              <TrendingUp className="w-4 h-4 text-purple-400" />
                              Revenue Streams
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-white/70 text-sm whitespace-pre-line">{generatedBMC.revenueStreams}</p>
                          </CardContent>
                        </Card>
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

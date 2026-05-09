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
  FileCode,
  Sparkles,
  Loader2,
  Download,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  BookOpen,
  Target,
  Users,
  Settings,
  Server,
  Shield,
  Database,
  Upload,
  X,
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  FileText,
  BarChart3,
} from "lucide-react"

interface SRSSection {
  id: string
  title: string
  icon: React.ElementType
  content: string
  subsections?: { title: string; content: string }[]
}

interface GeneratedSRS {
  projectName: string
  version: string
  date: string
  sections: SRSSection[]
}

interface EvaluationResult {
  overallScore: number
  completeness: { score: number; feedback: string; missing: string[] }
  clarity: { score: number; feedback: string; issues: string[] }
  consistency: { score: number; feedback: string; conflicts: string[] }
  testability: { score: number; feedback: string; suggestions: string[] }
  feasibility: { score: number; feedback: string; concerns: string[] }
  recommendations: string[]
}

export default function SRSPage() {
  const [activeTab, setActiveTab] = useState<"generate" | "evaluate">("generate")
  
  // Generate state
  const [projectName, setProjectName] = useState("")
  const [projectDescription, setProjectDescription] = useState("")
  const [targetUsers, setTargetUsers] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedSRS, setGeneratedSRS] = useState<GeneratedSRS | null>(null)
  const [expandedSections, setExpandedSections] = useState<string[]>([])
  const [copied, setCopied] = useState(false)

  // Evaluate state
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResult | null>(null)
  const [srsText, setSrsText] = useState("")

  const generateSRS = async () => {
    if (!projectName.trim() || !projectDescription.trim()) return
    setIsGenerating(true)

    await new Promise((resolve) => setTimeout(resolve, 3000))

    const mockSRS: GeneratedSRS = {
      projectName,
      version: "1.0.0",
      date: new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }),
      sections: [
        {
          id: "introduction",
          title: "1. Introduction",
          icon: BookOpen,
          content: `This Software Requirements Specification (SRS) document provides a comprehensive description of ${projectName}. It includes the purpose, scope, and detailed requirements for the system.`,
          subsections: [
            {
              title: "1.1 Purpose",
              content: `The purpose of this document is to define the software requirements for ${projectName}. This document is intended for the development team, stakeholders, and quality assurance personnel.`,
            },
            {
              title: "1.2 Scope",
              content: projectDescription,
            },
            {
              title: "1.3 Definitions, Acronyms, and Abbreviations",
              content: `• SRS - Software Requirements Specification
• API - Application Programming Interface
• UI - User Interface
• UX - User Experience
• DB - Database`,
            },
          ],
        },
        {
          id: "overall",
          title: "2. Overall Description",
          icon: Target,
          content: "This section provides a high-level overview of the system and its context.",
          subsections: [
            {
              title: "2.1 Product Perspective",
              content: `${projectName} is a standalone application designed to ${projectDescription.toLowerCase().includes("help") ? projectDescription : "help users " + projectDescription.toLowerCase()}. The system will integrate with modern web technologies and follow best practices for scalability and security.`,
            },
            {
              title: "2.2 Product Functions",
              content: `The main functions of ${projectName} include:
• User registration and authentication
• Core feature implementation based on requirements
• Data management and storage
• Reporting and analytics
• User profile management`,
            },
            {
              title: "2.3 User Classes and Characteristics",
              content: targetUsers || `Primary users include entrepreneurs, business owners, and startup teams who need ${projectDescription.toLowerCase()}.`,
            },
            {
              title: "2.4 Operating Environment",
              content: `The system will operate on:
• Modern web browsers (Chrome, Firefox, Safari, Edge)
• Mobile devices (iOS and Android)
• Cloud infrastructure for scalability`,
            },
          ],
        },
        {
          id: "requirements",
          title: "3. Specific Requirements",
          icon: Settings,
          content: "This section contains all the specific requirements for the system.",
          subsections: [
            {
              title: "3.1 Functional Requirements",
              content: `FR-001: User Authentication
- The system shall allow users to register with email and password
- The system shall provide secure login functionality
- The system shall support password recovery

FR-002: Core Features
- The system shall implement the primary functionality as described
- The system shall provide intuitive user interface
- The system shall support data import/export

FR-003: Data Management
- The system shall store user data securely
- The system shall provide data backup capabilities
- The system shall allow users to manage their data`,
            },
            {
              title: "3.2 Non-Functional Requirements",
              content: `NFR-001: Performance
- Page load time shall not exceed 3 seconds
- API response time shall be under 500ms
- The system shall support 1000 concurrent users

NFR-002: Security
- All data transmission shall use HTTPS
- Passwords shall be hashed using bcrypt
- Sessions shall expire after 24 hours of inactivity

NFR-003: Usability
- The interface shall be responsive on all devices
- The system shall be accessible (WCAG 2.1 AA compliance)
- Error messages shall be clear and actionable`,
            },
          ],
        },
        {
          id: "users",
          title: "4. User Interface Requirements",
          icon: Users,
          content: "This section describes the user interface requirements.",
          subsections: [
            {
              title: "4.1 User Interface Design",
              content: `The user interface shall follow these principles:
• Clean, modern design with consistent branding
• Intuitive navigation structure
• Responsive layout for all screen sizes
• Dark/light mode support
• Accessibility compliance`,
            },
            {
              title: "4.2 Screen Layouts",
              content: `Key screens include:
• Landing/Home page
• User dashboard
• Feature-specific pages
• Settings and profile pages
• Help and documentation`,
            },
          ],
        },
        {
          id: "system",
          title: "5. System Features",
          icon: Server,
          content: "Detailed description of system features and capabilities.",
          subsections: [
            {
              title: "5.1 Feature 1: User Management",
              content: `Description: Comprehensive user management system
Inputs: User credentials, profile information
Processing: Authentication, authorization, profile updates
Outputs: User session, profile data`,
            },
            {
              title: "5.2 Feature 2: Core Functionality",
              content: `Description: ${projectDescription}
Inputs: User inputs and configurations
Processing: Business logic implementation
Outputs: Processed results and feedback`,
            },
          ],
        },
        {
          id: "data",
          title: "6. Data Requirements",
          icon: Database,
          content: "This section describes the data storage and management requirements.",
          subsections: [
            {
              title: "6.1 Data Model",
              content: `Key entities include:
• Users (id, email, password_hash, created_at)
• Profiles (user_id, name, settings)
• Content (id, user_id, data, timestamps)
• Logs (id, action, user_id, timestamp)`,
            },
            {
              title: "6.2 Data Retention",
              content: `Data retention policies:
• Active user data: Retained indefinitely
• Deleted accounts: 30-day grace period
• Logs: 90-day retention
• Backups: Daily for 30 days`,
            },
          ],
        },
        {
          id: "security",
          title: "7. Security Requirements",
          icon: Shield,
          content: "Security requirements and compliance considerations.",
          subsections: [
            {
              title: "7.1 Authentication & Authorization",
              content: `• Multi-factor authentication option
• Role-based access control
• Session management
• API key authentication for integrations`,
            },
            {
              title: "7.2 Data Protection",
              content: `• Encryption at rest and in transit
• Regular security audits
• Vulnerability scanning
• GDPR compliance where applicable`,
            },
          ],
        },
      ],
    }

    setGeneratedSRS(mockSRS)
    setExpandedSections(mockSRS.sections.map((s) => s.id))
    setIsGenerating(false)
  }

  const toggleSection = (id: string) => {
    setExpandedSections((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]))
  }

  const copyToClipboard = () => {
    if (!generatedSRS) return

    let text = `# Software Requirements Specification\n# ${generatedSRS.projectName}\n\n`
    text += `Version: ${generatedSRS.version}\nDate: ${generatedSRS.date}\n\n`

    generatedSRS.sections.forEach((section) => {
      text += `## ${section.title}\n\n${section.content}\n\n`
      section.subsections?.forEach((sub) => {
        text += `### ${sub.title}\n\n${sub.content}\n\n`
      })
    })

    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const downloadSRS = () => {
    if (!generatedSRS) return

    let content = `SOFTWARE REQUIREMENTS SPECIFICATION\n${"=".repeat(50)}\n\n`
    content += `Project: ${generatedSRS.projectName}\n`
    content += `Version: ${generatedSRS.version}\n`
    content += `Date: ${generatedSRS.date}\n\n`
    content += `${"=".repeat(50)}\n\n`

    generatedSRS.sections.forEach((section) => {
      content += `${section.title.toUpperCase()}\n${"-".repeat(section.title.length)}\n\n`
      content += `${section.content}\n\n`
      section.subsections?.forEach((sub) => {
        content += `${sub.title}\n${sub.content}\n\n`
      })
    })

    const blob = new Blob([content], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${generatedSRS.projectName.replace(/\s+/g, "_")}_SRS.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Evaluation functions
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
    if (droppedFile && (droppedFile.type === "application/pdf" || droppedFile.type === "text/plain" || droppedFile.name.endsWith(".md") || droppedFile.name.endsWith(".txt"))) {
      setUploadedFile(droppedFile)
      setEvaluationResult(null)
      
      // Read text files
      if (droppedFile.type === "text/plain" || droppedFile.name.endsWith(".md") || droppedFile.name.endsWith(".txt")) {
        const reader = new FileReader()
        reader.onload = (e) => {
          setSrsText(e.target?.result as string || "")
        }
        reader.readAsText(droppedFile)
      }
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setUploadedFile(selectedFile)
      setEvaluationResult(null)
      
      if (selectedFile.type === "text/plain" || selectedFile.name.endsWith(".md") || selectedFile.name.endsWith(".txt")) {
        const reader = new FileReader()
        reader.onload = (e) => {
          setSrsText(e.target?.result as string || "")
        }
        reader.readAsText(selectedFile)
      }
    }
  }

  const evaluateSRS = async () => {
    if (!uploadedFile && !srsText.trim()) return
    setIsEvaluating(true)

    await new Promise((resolve) => setTimeout(resolve, 3000))

    const mockEvaluation: EvaluationResult = {
      overallScore: 72,
      completeness: {
        score: 68,
        feedback: "The SRS covers most essential sections but is missing some important details.",
        missing: [
          "Detailed use case diagrams",
          "Error handling specifications",
          "Performance benchmarks with specific metrics",
          "Data migration requirements",
        ],
      },
      clarity: {
        score: 75,
        feedback: "Requirements are generally clear but some ambiguous language was detected.",
        issues: [
          "FR-003 uses vague term 'quickly' - specify exact time threshold",
          "NFR-002 mentions 'secure' without defining security standards",
          "User roles are mentioned but not fully defined",
        ],
      },
      consistency: {
        score: 80,
        feedback: "The document is mostly consistent with minor conflicts.",
        conflicts: [
          "Section 2.4 mentions mobile support but Section 4.2 only lists web screens",
          "Data retention policy in 6.2 conflicts with GDPR requirements in 7.2",
        ],
      },
      testability: {
        score: 65,
        feedback: "Many requirements lack specific, measurable criteria for testing.",
        suggestions: [
          "Add specific performance metrics (e.g., 'page load < 2s' instead of 'fast')",
          "Define clear acceptance criteria for each functional requirement",
          "Include edge cases and boundary conditions",
          "Add test scenarios for security requirements",
        ],
      },
      feasibility: {
        score: 78,
        feedback: "Most requirements are technically feasible with current resources.",
        concerns: [
          "Real-time sync feature may require significant infrastructure investment",
          "Multi-language support scope needs clarification",
          "Third-party API dependencies need fallback strategies",
        ],
      },
      recommendations: [
        "Add detailed use case diagrams for complex workflows",
        "Replace ambiguous terms with specific, measurable criteria",
        "Include a glossary section for technical terms",
        "Add traceability matrix linking requirements to test cases",
        "Define clear priority levels (Must-have, Should-have, Nice-to-have)",
        "Include assumptions and constraints section",
        "Add version history and change log",
        "Include stakeholder sign-off section",
      ],
    }

    setEvaluationResult(mockEvaluation)
    setIsEvaluating(false)
  }

  const clearUpload = () => {
    setUploadedFile(null)
    setSrsText("")
    setEvaluationResult(null)
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

  const getScoreIcon = (score: number) => {
    if (score >= 80) return CheckCircle
    if (score >= 60) return AlertCircle
    return AlertTriangle
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
            <div className="max-w-5xl mx-auto">
              {/* Header */}
              <div className="text-center mb-8">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium mb-6">
                  <FileCode className="w-4 h-4 mr-2" />
                  SRS Generator & Evaluator
                </div>
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
                  AI-Powered{" "}
                  <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                    SRS Tools
                  </span>
                </h1>
                <p className="text-lg text-white/70 max-w-2xl mx-auto">
                  Generate comprehensive Software Requirements Specifications or evaluate existing SRS documents for quality and completeness.
                </p>
              </div>

              {/* Tab Switcher */}
              <div className="flex justify-center mb-8">
                <div className="flex gap-2 p-1 bg-white/5 backdrop-blur-xl rounded-xl border border-white/10">
                  <button
                    onClick={() => setActiveTab("generate")}
                    className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
                      activeTab === "generate"
                        ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white"
                        : "text-white/60 hover:text-white hover:bg-white/10"
                    }`}
                  >
                    <Sparkles className="w-4 h-4" />
                    Generate SRS
                  </button>
                  <button
                    onClick={() => setActiveTab("evaluate")}
                    className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
                      activeTab === "evaluate"
                        ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white"
                        : "text-white/60 hover:text-white hover:bg-white/10"
                    }`}
                  >
                    <BarChart3 className="w-4 h-4" />
                    Evaluate SRS
                  </button>
                </div>
              </div>

              {activeTab === "generate" ? (
                /* Generate Tab */
                <>
                  {!generatedSRS ? (
                    <Card className="bg-white/5 backdrop-blur-xl border-white/10 max-w-2xl mx-auto">
                      <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                          <Sparkles className="w-5 h-5 text-indigo-400" />
                          Project Details
                        </CardTitle>
                        <CardDescription className="text-white/60">
                          Enter your project information to generate an SRS document
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <label className="text-white/70 text-sm mb-2 block">Project Name *</label>
                          <Input
                            placeholder="e.g., ScaleUp Platform"
                            value={projectName}
                            onChange={(e) => setProjectName(e.target.value)}
                            className="bg-white/5 border-white/10 text-white placeholder:text-white/40"
                          />
                        </div>
                        <div>
                          <label className="text-white/70 text-sm mb-2 block">Project Description *</label>
                          <Textarea
                            placeholder="Describe what your project does... (e.g., 'An AI-powered platform that helps Tunisian startups validate their business models and generate professional documentation')"
                            value={projectDescription}
                            onChange={(e) => setProjectDescription(e.target.value)}
                            className="bg-white/5 border-white/10 text-white placeholder:text-white/40 min-h-[120px]"
                          />
                        </div>
                        <div>
                          <label className="text-white/70 text-sm mb-2 block">Target Users (optional)</label>
                          <Textarea
                            placeholder="Describe your target users... (e.g., 'Early-stage startups, student entrepreneurs, and SMEs in Tunisia')"
                            value={targetUsers}
                            onChange={(e) => setTargetUsers(e.target.value)}
                            className="bg-white/5 border-white/10 text-white placeholder:text-white/40 min-h-[80px]"
                          />
                        </div>
                        <Button
                          onClick={generateSRS}
                          disabled={isGenerating || !projectName.trim() || !projectDescription.trim()}
                          className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                        >
                          {isGenerating ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Generating SRS Document...
                            </>
                          ) : (
                            <>
                              <FileCode className="w-4 h-4 mr-2" />
                              Generate SRS
                            </>
                          )}
                        </Button>
                      </CardContent>
                    </Card>
                  ) : (
                    <div className="space-y-6">
                      {/* Header Card */}
                      <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                        <CardContent className="p-6">
                          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                            <div>
                              <h2 className="text-2xl font-bold text-white mb-1">{generatedSRS.projectName}</h2>
                              <p className="text-white/60 text-sm">
                                Version {generatedSRS.version} | Generated on {generatedSRS.date}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={copyToClipboard}
                                className="bg-white/5 border-white/20 text-white hover:bg-white/10"
                              >
                                {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                                {copied ? "Copied!" : "Copy"}
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={downloadSRS}
                                className="bg-white/5 border-white/20 text-white hover:bg-white/10"
                              >
                                <Download className="w-4 h-4 mr-2" />
                                Download
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => setGeneratedSRS(null)}
                                className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white"
                              >
                                New SRS
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      {/* Sections */}
                      <div className="space-y-4">
                        {generatedSRS.sections.map((section) => (
                          <Card key={section.id} className="bg-white/5 backdrop-blur-xl border-white/10 overflow-hidden">
                            <button
                              onClick={() => toggleSection(section.id)}
                              className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors"
                            >
                              <div className="flex items-center gap-3">
                                <section.icon className="w-5 h-5 text-indigo-400" />
                                <span className="text-white font-medium">{section.title}</span>
                              </div>
                              {expandedSections.includes(section.id) ? (
                                <ChevronDown className="w-5 h-5 text-white/60" />
                              ) : (
                                <ChevronRight className="w-5 h-5 text-white/60" />
                              )}
                            </button>
                            {expandedSections.includes(section.id) && (
                              <CardContent className="pt-0 px-4 pb-4">
                                <p className="text-white/70 mb-4 pl-8">{section.content}</p>
                                {section.subsections && (
                                  <div className="space-y-4 pl-8">
                                    {section.subsections.map((sub, index) => (
                                      <div key={index} className="p-4 bg-white/5 rounded-lg border border-white/10">
                                        <h4 className="text-white font-medium mb-2">{sub.title}</h4>
                                        <p className="text-white/60 text-sm whitespace-pre-line">{sub.content}</p>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </CardContent>
                            )}
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                /* Evaluate Tab */
                <div className="space-y-6">
                  {/* Upload Section */}
                  <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Upload className="w-5 h-5 text-indigo-400" />
                        Upload or Paste Your SRS
                      </CardTitle>
                      <CardDescription className="text-white/60">
                        Upload an SRS document (PDF, TXT, MD) or paste the content to evaluate its quality
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {!uploadedFile ? (
                        <>
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
                            <Upload className="w-10 h-10 text-indigo-400 mx-auto mb-3" />
                            <p className="text-white/70 mb-3">Drag and drop your SRS document here, or</p>
                            <label className="cursor-pointer">
                              <input
                                type="file"
                                accept=".pdf,.txt,.md"
                                onChange={handleFileSelect}
                                className="hidden"
                              />
                              <span className="inline-flex items-center px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-full font-medium transition-all duration-300 hover:scale-105 text-sm">
                                Browse Files
                              </span>
                            </label>
                          </div>
                          
                          <div className="flex items-center gap-4">
                            <div className="flex-1 h-px bg-white/10" />
                            <span className="text-white/40 text-sm">or paste content</span>
                            <div className="flex-1 h-px bg-white/10" />
                          </div>

                          <Textarea
                            placeholder="Paste your SRS document content here..."
                            value={srsText}
                            onChange={(e) => setSrsText(e.target.value)}
                            className="bg-white/5 border-white/10 text-white placeholder:text-white/40 min-h-[200px] font-mono text-sm"
                          />

                          {srsText.trim() && (
                            <Button
                              onClick={evaluateSRS}
                              disabled={isEvaluating}
                              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                            >
                              {isEvaluating ? (
                                <>
                                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                  Evaluating SRS...
                                </>
                              ) : (
                                <>
                                  <BarChart3 className="w-4 h-4 mr-2" />
                                  Evaluate SRS
                                </>
                              )}
                            </Button>
                          )}
                        </>
                      ) : (
                        <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10">
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                              <FileText className="w-6 h-6 text-indigo-400" />
                            </div>
                            <div>
                              <p className="text-white font-medium">{uploadedFile.name}</p>
                              <p className="text-white/50 text-sm">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            {!evaluationResult && (
                              <Button
                                onClick={evaluateSRS}
                                disabled={isEvaluating}
                                className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                              >
                                {isEvaluating ? (
                                  <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Evaluating...
                                  </>
                                ) : (
                                  <>
                                    <BarChart3 className="w-4 h-4 mr-2" />
                                    Evaluate
                                  </>
                                )}
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={clearUpload}
                              className="text-white/60 hover:text-white hover:bg-white/10"
                            >
                              <X className="w-5 h-5" />
                            </Button>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Evaluation Results */}
                  {evaluationResult && (
                    <div className="space-y-6">
                      {/* Overall Score */}
                      <Card className={`border ${getScoreBg(evaluationResult.overallScore)}`}>
                        <CardContent className="p-6">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-white/60 text-sm mb-1">Overall SRS Quality Score</p>
                              <p className={`text-4xl font-bold ${getScoreColor(evaluationResult.overallScore)}`}>
                                {evaluationResult.overallScore}/100
                              </p>
                              <p className="text-white/50 text-sm mt-1">
                                {evaluationResult.overallScore >= 80
                                  ? "Excellent - Ready for development"
                                  : evaluationResult.overallScore >= 60
                                    ? "Good - Minor improvements needed"
                                    : "Needs Work - Significant gaps identified"}
                              </p>
                            </div>
                            <div
                              className={`w-24 h-24 rounded-full border-4 flex items-center justify-center ${
                                evaluationResult.overallScore >= 80
                                  ? "border-green-400"
                                  : evaluationResult.overallScore >= 60
                                    ? "border-yellow-400"
                                    : "border-red-400"
                              }`}
                            >
                              {(() => {
                                const Icon = getScoreIcon(evaluationResult.overallScore)
                                return <Icon className={`w-10 h-10 ${getScoreColor(evaluationResult.overallScore)}`} />
                              })()}
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      {/* Detailed Scores */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {[
                          { label: "Completeness", data: evaluationResult.completeness, list: "missing" },
                          { label: "Clarity", data: evaluationResult.clarity, list: "issues" },
                          { label: "Consistency", data: evaluationResult.consistency, list: "conflicts" },
                          { label: "Testability", data: evaluationResult.testability, list: "suggestions" },
                          { label: "Feasibility", data: evaluationResult.feasibility, list: "concerns" },
                        ].map((item, index) => (
                          <Card key={index} className="bg-white/5 backdrop-blur-xl border-white/10">
                            <CardContent className="p-4">
                              <div className="flex items-center justify-between mb-3">
                                <span className="text-white font-medium">{item.label}</span>
                                <span className={`font-bold text-lg ${getScoreColor(item.data.score)}`}>
                                  {item.data.score}%
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
                              <p className="text-white/60 text-sm mb-3">{item.data.feedback}</p>
                              {(item.data as Record<string, string[]>)[item.list]?.length > 0 && (
                                <div className="space-y-1">
                                  {(item.data as Record<string, string[]>)[item.list].slice(0, 3).map((point: string, i: number) => (
                                    <p key={i} className="text-white/50 text-xs flex items-start gap-2">
                                      <span className="text-white/30">•</span>
                                      {point}
                                    </p>
                                  ))}
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </div>

                      {/* Recommendations */}
                      <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                        <CardHeader>
                          <CardTitle className="text-white flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-indigo-400" />
                            Recommendations for Improvement
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {evaluationResult.recommendations.map((rec, index) => (
                              <div key={index} className="flex items-start gap-3 p-3 bg-white/5 rounded-lg border border-white/10">
                                <div className="w-6 h-6 rounded-full bg-indigo-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                  <span className="text-indigo-400 text-xs font-bold">{index + 1}</span>
                                </div>
                                <span className="text-white/70 text-sm">{rec}</span>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>

                      {/* Action Buttons */}
                      <div className="flex justify-center gap-4">
                        <Button
                          onClick={clearUpload}
                          variant="outline"
                          className="bg-white/5 border-white/20 text-white hover:bg-white/10"
                        >
                          Evaluate Another SRS
                        </Button>
                        <Button
                          onClick={() => setActiveTab("generate")}
                          className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                        >
                          Generate New SRS
                        </Button>
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

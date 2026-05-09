"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { GlassmorphismNav } from "@/components/glassmorphism-nav"
import Aurora from "@/components/Aurora"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Send,
  Bot,
  User,
  TrendingUp,
  DollarSign,
  PieChart,
  Calculator,
  Lightbulb,
  Loader2,
  Trash2,
  Upload,
  FileSpreadsheet,
  X,
  TrendingDown,
  Scale,
  FileText,
  BarChart3,
} from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  attachedFile?: {
    name: string
    type: string
    analysis?: FileAnalysis
  }
}

interface FileAnalysis {
  totalRevenue: number
  totalExpenses: number
  netProfit: number
  profitMargin: number
  status: "profit" | "loss" | "break-even"
  insights: string[]
  monthlyBreakdown?: { month: string; revenue: number; expenses: number }[]
}

const suggestedQuestions = [
  {
    icon: TrendingUp,
    text: "How do I calculate my startup's burn rate?",
    category: "Metrics",
  },
  {
    icon: DollarSign,
    text: "What's a good revenue model for SaaS?",
    category: "Revenue",
  },
  {
    icon: PieChart,
    text: "How should I allocate my seed funding?",
    category: "Budgeting",
  },
  {
    icon: Calculator,
    text: "What financial metrics do investors look for?",
    category: "Investors",
  },
]

export default function FinancialAdvisorPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: `Welcome to ScaleUp's Financial Advisor! I'm here to help you with financial planning, budgeting, investment strategies, and startup economics.

Ask me anything about:
• Burn rate and runway calculations
• Revenue models and pricing strategies
• Financial projections and forecasting
• Investment and funding advice
• Tunisian financial laws and regulations

You can also upload bills, invoices, or financial tables (CSV, Excel, PDF) and I'll analyze them to tell you if you're making profits or losses.

How can I help you today?`,
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [isAnalyzingFile, setIsAnalyzingFile] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

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
    if (droppedFile) {
      const validTypes = [
        "application/pdf",
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "image/png",
        "image/jpeg",
      ]
      if (validTypes.includes(droppedFile.type) || droppedFile.name.endsWith(".csv")) {
        setUploadedFile(droppedFile)
      }
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setUploadedFile(selectedFile)
    }
  }

  const analyzeFile = async (file: File): Promise<FileAnalysis> => {
    // Simulate file analysis
    await new Promise((resolve) => setTimeout(resolve, 2000))

    // Mock analysis based on file type
    const mockAnalysis: FileAnalysis = {
      totalRevenue: Math.floor(Math.random() * 100000) + 50000,
      totalExpenses: Math.floor(Math.random() * 80000) + 30000,
      netProfit: 0,
      profitMargin: 0,
      status: "profit",
      insights: [],
      monthlyBreakdown: [
        { month: "Jan", revenue: 12000, expenses: 8500 },
        { month: "Feb", revenue: 15000, expenses: 9200 },
        { month: "Mar", revenue: 18000, expenses: 11000 },
        { month: "Apr", revenue: 22000, expenses: 12500 },
        { month: "May", revenue: 25000, expenses: 14000 },
        { month: "Jun", revenue: 28000, expenses: 15800 },
      ],
    }

    mockAnalysis.netProfit = mockAnalysis.totalRevenue - mockAnalysis.totalExpenses
    mockAnalysis.profitMargin = (mockAnalysis.netProfit / mockAnalysis.totalRevenue) * 100

    if (mockAnalysis.netProfit > 0) {
      mockAnalysis.status = "profit"
      mockAnalysis.insights = [
        `Your business is profitable with a ${mockAnalysis.profitMargin.toFixed(1)}% profit margin`,
        "Revenue shows consistent month-over-month growth",
        "Consider reinvesting 30% of profits for expansion",
        "Your expense ratio is healthy at " + ((mockAnalysis.totalExpenses / mockAnalysis.totalRevenue) * 100).toFixed(1) + "%",
      ]
    } else if (mockAnalysis.netProfit < 0) {
      mockAnalysis.status = "loss"
      mockAnalysis.insights = [
        `Your business is operating at a loss of ${Math.abs(mockAnalysis.netProfit).toLocaleString()} TND`,
        "Consider reducing operational expenses",
        "Review your pricing strategy to improve margins",
        "Focus on increasing revenue streams",
      ]
    } else {
      mockAnalysis.status = "break-even"
      mockAnalysis.insights = [
        "Your business is at break-even point",
        "Focus on increasing revenue to achieve profitability",
        "Consider cost optimization strategies",
      ]
    }

    return mockAnalysis
  }

  const generateResponse = async (question: string): Promise<string> => {
    const lowerQuestion = question.toLowerCase()

    if (lowerQuestion.includes("tunisian law") || lowerQuestion.includes("tunisia") || lowerQuestion.includes("fiscal") || lowerQuestion.includes("tax")) {
      return `**Tunisian Financial Laws & Regulations**

Here's what you need to know about financial regulations in Tunisia:

**Corporate Tax (IS)**
• Standard rate: 15% for most companies
• Reduced rate: 10% for certain sectors
• Export companies: 0% for first 10 years

**VAT (TVA)**
• Standard rate: 19%
• Reduced rate: 7% for essential goods
• 13% for certain services

**Startup Act Benefits (2018)**
• 8-year tax exemption on profits
• Social security exemptions
• Salary support for founders
• Facilitated company creation

**Financial Reporting Requirements**
• Annual financial statements required
• Audit mandatory for companies with turnover > 300,000 TND
• Quarterly tax declarations

**Investment Incentives**
• FOPRODI fund for SMEs
• Regional development incentives
• Innovation subsidies through APII

Would you like more details on any specific regulation?`
    }

    if (lowerQuestion.includes("burn rate")) {
      return `**Calculating Your Burn Rate**

Burn rate is the rate at which your startup spends money before generating positive cash flow. Here's how to calculate it:

**Monthly Burn Rate = Monthly Operating Expenses - Monthly Revenue**

For example, if your monthly expenses are 15,000 TND and revenue is 5,000 TND, your burn rate is 10,000 TND/month.

**Runway = Cash in Bank / Monthly Burn Rate**

With 120,000 TND in the bank and a 10,000 TND burn rate, you have 12 months of runway.

**Tips for Tunisian Startups:**
• Keep at least 12-18 months of runway
• Track weekly, not just monthly
• Separate fixed vs variable costs
• Consider currency fluctuation impact

Would you like me to help you create a burn rate tracker?`
    }

    if (lowerQuestion.includes("revenue model") || lowerQuestion.includes("saas")) {
      return `**SaaS Revenue Models for Tunisian Startups**

Here are the most effective revenue models:

**1. Subscription Model (Most Common)**
• Monthly: 49-199 TND/month
• Annual: 15-20% discount
• Best for predictable revenue

**2. Freemium Model**
• Free tier with limited features
• Convert 2-5% to paid users
• Great for market penetration

**3. Usage-Based Pricing**
• Pay per API call, user, or transaction
• Scales with customer growth
• Common for B2B tools

**4. Tiered Pricing**
• Starter: Basic features
• Professional: Advanced features
• Enterprise: Custom solutions

**Key Metrics to Track:**
• MRR (Monthly Recurring Revenue)
• Churn Rate (aim for <5% monthly)
• LTV:CAC Ratio (should be >3:1)
• ARPU (Average Revenue Per User)

Want me to help you design a pricing strategy?`
    }

    if (lowerQuestion.includes("investor") || lowerQuestion.includes("metrics")) {
      return `**Financial Metrics Investors Look For**

When pitching to Tunisian or international investors, focus on these key metrics:

**Growth Metrics:**
• MoM Growth Rate: >15% is excellent
• Year-over-Year Growth: >100% for early stage
• User Growth Rate

**Unit Economics:**
• Customer Acquisition Cost (CAC)
• Lifetime Value (LTV)
• LTV:CAC Ratio (>3:1 is healthy)
• Payback Period (<12 months)

**Financial Health:**
• Gross Margin: >60% for SaaS
• Net Revenue Retention: >100%
• Burn Multiple: <2x is efficient

**Traction Indicators:**
• Paying customers count
• Revenue (MRR/ARR)
• Market share in Tunisia

**For Tunisian Investors (like Flat6Labs, Startup Tunisia):**
• Local market traction
• Regional expansion potential
• Team capabilities

Would you like me to explain any of these metrics in detail?`
    }

    if (lowerQuestion.includes("seed") || lowerQuestion.includes("funding") || lowerQuestion.includes("allocat")) {
      return `**Seed Funding Allocation Strategy**

Here's a recommended allocation for your seed round:

**Product Development: 40-50%**
• Engineering team
• Infrastructure costs
• Product tools and licenses

**Marketing & Sales: 25-30%**
• Digital marketing
• Content creation
• Sales team (if B2B)

**Operations: 15-20%**
• Legal & compliance
• Office/workspace
• Administrative tools

**Reserve: 10-15%**
• Emergency fund
• Opportunity buffer
• Currency hedging (important in Tunisia)

**Tips for Tunisian Startups:**
• Account for TND fluctuation
• Consider government grants (Startup Act benefits)
• Build relationships with local accelerators
• Keep 18 months runway minimum

**Common Mistakes to Avoid:**
• Over-hiring too early
• Expensive office space
• Ignoring unit economics
• Not tracking expenses closely

Need help creating a detailed budget?`
    }

    // Default response for other questions
    return `Great question! Let me help you with that.

Based on your query about "${question}", here are some key insights for Tunisian startups:

**Key Considerations:**
• Understand your local market dynamics
• Consider regulatory requirements
• Factor in currency considerations
• Leverage government support (Startup Act)

**Recommended Actions:**
1. Analyze your specific situation
2. Create financial projections
3. Consult with local mentors
4. Review similar startups' approaches

**Resources in Tunisia:**
• Startup Tunisia programs
• Flat6Labs incubator
• APII support
• Local investor networks

Would you like me to dive deeper into any specific aspect of this topic?`
  }

  const handleSend = async () => {
    if (!input.trim() && !uploadedFile) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: uploadedFile ? `[Uploaded: ${uploadedFile.name}] ${input.trim() || "Please analyze this file"}` : input.trim(),
      timestamp: new Date(),
      attachedFile: uploadedFile
        ? {
            name: uploadedFile.name,
            type: uploadedFile.type,
          }
        : undefined,
    }

    setMessages((prev) => [...prev, userMessage])
    const currentFile = uploadedFile
    setInput("")
    setUploadedFile(null)
    setIsTyping(true)

    if (currentFile) {
      setIsAnalyzingFile(true)
      const analysis = await analyzeFile(currentFile)
      setIsAnalyzingFile(false)

      const analysisMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: generateFileAnalysisResponse(analysis),
        timestamp: new Date(),
        attachedFile: {
          name: currentFile.name,
          type: currentFile.type,
          analysis,
        },
      }
      setMessages((prev) => [...prev, analysisMessage])
    } else {
      await new Promise((resolve) => setTimeout(resolve, 1500))
      const response = await generateResponse(userMessage.content)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    }

    setIsTyping(false)
  }

  const generateFileAnalysisResponse = (analysis: FileAnalysis): string => {
    const statusEmoji = analysis.status === "profit" ? "Profit" : analysis.status === "loss" ? "Loss" : "Break-even"
    
    return `**Financial Analysis Complete**

**Overall Status: ${statusEmoji}**

**Summary:**
• Total Revenue: ${analysis.totalRevenue.toLocaleString()} TND
• Total Expenses: ${analysis.totalExpenses.toLocaleString()} TND
• Net ${analysis.status === "loss" ? "Loss" : "Profit"}: ${Math.abs(analysis.netProfit).toLocaleString()} TND
• Profit Margin: ${analysis.profitMargin.toFixed(1)}%

**Key Insights:**
${analysis.insights.map((insight) => `• ${insight}`).join("\n")}

**Monthly Trend:**
${analysis.monthlyBreakdown?.map((m) => `• ${m.month}: Revenue ${m.revenue.toLocaleString()} TND, Expenses ${m.expenses.toLocaleString()} TND`).join("\n")}

**Recommendations:**
${analysis.status === "profit" 
  ? `• Consider reinvesting profits for growth
• Build emergency reserves (3-6 months expenses)
• Explore expansion opportunities`
  : `• Identify and reduce unnecessary expenses
• Review pricing strategy
• Focus on high-margin products/services
• Consider operational efficiency improvements`
}

Would you like me to provide more detailed analysis or recommendations?`
  }

  const handleSuggestedQuestion = (question: string) => {
    setInput(question)
    inputRef.current?.focus()
  }

  const clearChat = () => {
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: `Welcome back! I'm here to help you with financial planning, budgeting, investment strategies, and startup economics.

Upload bills, invoices, or financial data and I'll analyze them for you.

How can I assist you today?`,
        timestamp: new Date(),
      },
    ])
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      <main className="min-h-screen relative overflow-hidden">
        <div className="fixed inset-0 w-full h-full">
          <Aurora colorStops={["#1e1b4b", "#4c1d95", "#312e81"]} amplitude={1.2} blend={0.6} speed={0.8} />
        </div>
        <div className="relative z-10">
          <GlassmorphismNav />

          <section className="pt-32 pb-8 px-4">
            <div className="max-w-4xl mx-auto">
              {/* Header */}
              <div className="text-center mb-8">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-500/10 border border-green-500/20 text-green-300 text-sm font-medium mb-6">
                  <DollarSign className="w-4 h-4 mr-2" />
                  Financial Advisor
                </div>
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
                  AI{" "}
                  <span className="bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
                    Financial Advisor
                  </span>
                </h1>
                <p className="text-lg text-white/70 max-w-2xl mx-auto">
                  Get expert financial guidance. Ask about laws, budgeting, or upload bills and tables to analyze your profits and losses.
                </p>
              </div>

              {/* Suggested Questions */}
              {messages.length <= 1 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
                  {suggestedQuestions.map((q, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestedQuestion(q.text)}
                      className="flex items-center gap-3 p-4 bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl hover:bg-white/10 transition-all duration-300 text-left group"
                    >
                      <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center group-hover:bg-green-500/30 transition-colors">
                        <q.icon className="w-5 h-5 text-green-400" />
                      </div>
                      <div>
                        <p className="text-white/40 text-xs mb-0.5">{q.category}</p>
                        <p className="text-white text-sm">{q.text}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {/* Chat Container */}
              <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                <CardContent className="p-0">
                  {/* Messages */}
                  <div 
                    className="h-[500px] overflow-y-auto p-4 space-y-4"
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    {isDragging && (
                      <div className="absolute inset-0 bg-green-500/10 border-2 border-dashed border-green-400 rounded-xl flex items-center justify-center z-10 backdrop-blur-sm">
                        <div className="text-center">
                          <Upload className="w-12 h-12 text-green-400 mx-auto mb-2" />
                          <p className="text-green-300 font-medium">Drop your file here</p>
                          <p className="text-green-300/60 text-sm">CSV, Excel, PDF, or Images</p>
                        </div>
                      </div>
                    )}
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}
                      >
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                            message.role === "assistant"
                              ? "bg-green-500/20"
                              : "bg-purple-500/20"
                          }`}
                        >
                          {message.role === "assistant" ? (
                            <Bot className="w-4 h-4 text-green-400" />
                          ) : (
                            <User className="w-4 h-4 text-purple-400" />
                          )}
                        </div>
                        <div
                          className={`max-w-[80%] p-4 rounded-2xl ${
                            message.role === "assistant"
                              ? "bg-white/5 border border-white/10 text-white/80"
                              : "bg-gradient-to-r from-purple-500/20 to-indigo-500/20 border border-purple-500/30 text-white"
                          }`}
                        >
                          {/* File attachment indicator */}
                          {message.attachedFile && message.role === "user" && (
                            <div className="flex items-center gap-2 mb-2 p-2 bg-white/10 rounded-lg">
                              <FileSpreadsheet className="w-4 h-4 text-green-400" />
                              <span className="text-sm text-green-300">{message.attachedFile.name}</span>
                            </div>
                          )}
                          
                          {/* Analysis visualization */}
                          {message.attachedFile?.analysis && (
                            <div className="mb-4 p-4 bg-white/5 rounded-xl border border-white/10">
                              <div className="flex items-center gap-3 mb-4">
                                {message.attachedFile.analysis.status === "profit" ? (
                                  <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                                    <TrendingUp className="w-6 h-6 text-green-400" />
                                  </div>
                                ) : message.attachedFile.analysis.status === "loss" ? (
                                  <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                                    <TrendingDown className="w-6 h-6 text-red-400" />
                                  </div>
                                ) : (
                                  <div className="w-12 h-12 rounded-full bg-yellow-500/20 flex items-center justify-center">
                                    <Scale className="w-6 h-6 text-yellow-400" />
                                  </div>
                                )}
                                <div>
                                  <p className={`text-lg font-bold ${
                                    message.attachedFile.analysis.status === "profit" 
                                      ? "text-green-400" 
                                      : message.attachedFile.analysis.status === "loss"
                                        ? "text-red-400"
                                        : "text-yellow-400"
                                  }`}>
                                    {message.attachedFile.analysis.status === "profit" ? "Profitable" : message.attachedFile.analysis.status === "loss" ? "Operating at Loss" : "Break-even"}
                                  </p>
                                  <p className="text-white/60 text-sm">
                                    {message.attachedFile.analysis.profitMargin.toFixed(1)}% margin
                                  </p>
                                </div>
                              </div>
                              <div className="grid grid-cols-3 gap-3">
                                <div className="p-3 bg-white/5 rounded-lg text-center">
                                  <p className="text-white/60 text-xs mb-1">Revenue</p>
                                  <p className="text-green-400 font-bold">{message.attachedFile.analysis.totalRevenue.toLocaleString()}</p>
                                </div>
                                <div className="p-3 bg-white/5 rounded-lg text-center">
                                  <p className="text-white/60 text-xs mb-1">Expenses</p>
                                  <p className="text-red-400 font-bold">{message.attachedFile.analysis.totalExpenses.toLocaleString()}</p>
                                </div>
                                <div className="p-3 bg-white/5 rounded-lg text-center">
                                  <p className="text-white/60 text-xs mb-1">Net</p>
                                  <p className={`font-bold ${message.attachedFile.analysis.netProfit >= 0 ? "text-green-400" : "text-red-400"}`}>
                                    {message.attachedFile.analysis.netProfit.toLocaleString()}
                                  </p>
                                </div>
                              </div>
                            </div>
                          )}
                          
                          <div className="text-sm whitespace-pre-wrap prose prose-invert prose-sm max-w-none">
                            {message.content.split("\n").map((line, i) => {
                              if (line.startsWith("**") && line.endsWith("**")) {
                                return (
                                  <p key={i} className="font-bold text-white mb-2 mt-4 first:mt-0">
                                    {line.replace(/\*\*/g, "")}
                                  </p>
                                )
                              }
                              if (line.startsWith("•")) {
                                return (
                                  <p key={i} className="ml-4 mb-1">
                                    {line}
                                  </p>
                                )
                              }
                              return line ? (
                                <p key={i} className="mb-2">
                                  {line}
                                </p>
                              ) : null
                            })}
                          </div>
                        </div>
                      </div>
                    ))}
                    {isTyping && (
                      <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-green-400" />
                        </div>
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                          <div className="flex items-center gap-2">
                            <Loader2 className="w-4 h-4 text-green-400 animate-spin" />
                            <span className="text-white/60 text-sm">
                              {isAnalyzingFile ? "Analyzing your file..." : "Thinking..."}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Uploaded File Preview */}
                  {uploadedFile && (
                    <div className="px-4 pb-2">
                      <div className="flex items-center gap-3 p-3 bg-green-500/10 border border-green-500/30 rounded-xl">
                        <FileSpreadsheet className="w-5 h-5 text-green-400" />
                        <div className="flex-1">
                          <p className="text-white text-sm font-medium">{uploadedFile.name}</p>
                          <p className="text-white/50 text-xs">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
                        </div>
                        <button
                          onClick={() => setUploadedFile(null)}
                          className="p-1 hover:bg-white/10 rounded-full transition-colors"
                        >
                          <X className="w-4 h-4 text-white/60" />
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Input */}
                  <div className="border-t border-white/10 p-4">
                    <div className="flex items-end gap-3">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={clearChat}
                        className="text-white/40 hover:text-white hover:bg-white/10"
                        title="Clear chat"
                      >
                        <Trash2 className="w-5 h-5" />
                      </Button>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".csv,.xlsx,.xls,.pdf,image/*"
                        onChange={handleFileSelect}
                        className="hidden"
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => fileInputRef.current?.click()}
                        className="text-white/40 hover:text-green-400 hover:bg-green-500/10"
                        title="Upload file"
                      >
                        <Upload className="w-5 h-5" />
                      </Button>
                      <div className="flex-1 relative">
                        <textarea
                          ref={inputRef}
                          value={input}
                          onChange={(e) => setInput(e.target.value)}
                          onKeyDown={handleKeyDown}
                          placeholder="Ask about finances, laws, or upload bills to analyze..."
                          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 pr-12 text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-green-500/50 resize-none min-h-[48px] max-h-[120px]"
                          rows={1}
                        />
                        <div className="absolute right-2 bottom-2 flex items-center gap-1">
                          <Lightbulb className="w-4 h-4 text-white/30" />
                        </div>
                      </div>
                      <Button
                        onClick={handleSend}
                        disabled={(!input.trim() && !uploadedFile) || isTyping}
                        className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-xl px-6"
                      >
                        <Send className="w-5 h-5" />
                      </Button>
                    </div>
                    <p className="text-white/40 text-xs mt-2 text-center">
                      Drop files here or click upload. Supports CSV, Excel, PDF, and images.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>

          <Footer />
        </div>
      </main>
    </div>
  )
}

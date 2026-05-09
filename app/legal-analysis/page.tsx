"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { GlassmorphismNav } from "@/components/glassmorphism-nav"
import Aurora from "@/components/Aurora"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  FileText,
  Send,
  Bot,
  User,
  Loader2,
  Download,
  Copy,
  Check,
  Scale,
  Building,
  Users,
  Briefcase,
  Shield,
  FileSignature,
  Handshake,
  ScrollText,
  ChevronRight,
  Upload,
  X,
  Search,
  AlertTriangle,
  CheckCircle,
  Eye,
} from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  isQuestion?: boolean
  fieldName?: string
}

interface DocumentTemplate {
  id: string
  name: string
  icon: React.ElementType
  description: string
  fields: DocumentField[]
  template: string
}

interface DocumentField {
  name: string
  label: string
  type: "text" | "date" | "textarea" | "number" | "select"
  placeholder?: string
  options?: string[]
  required?: boolean
}

interface UploadedDocument {
  file: File
  preview?: string
}

interface AnalysisResult {
  extractedText: string
  summary: string
  keyClauses: { title: string; content: string; importance: "high" | "medium" | "low" }[]
  signatures: { location: string; status: "genuine" | "suspicious" | "unverified"; confidence: number }[]
}

const documentTemplates: DocumentTemplate[] = [
  {
    id: "nda",
    name: "Non-Disclosure Agreement",
    icon: Shield,
    description: "Protect confidential information shared between parties",
    fields: [
      { name: "disclosingParty", label: "Disclosing Party Name", type: "text", placeholder: "Company or person sharing information", required: true },
      { name: "receivingParty", label: "Receiving Party Name", type: "text", placeholder: "Company or person receiving information", required: true },
      { name: "effectiveDate", label: "Effective Date", type: "date", required: true },
      { name: "confidentialInfo", label: "Description of Confidential Information", type: "textarea", placeholder: "Describe what information is considered confidential", required: true },
      { name: "duration", label: "Duration (years)", type: "number", placeholder: "2", required: true },
      { name: "jurisdiction", label: "Jurisdiction", type: "text", placeholder: "Tunisia", required: true },
    ],
    template: `NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement ("Agreement") is entered into as of {effectiveDate} by and between:

DISCLOSING PARTY: {disclosingParty}
RECEIVING PARTY: {receivingParty}

1. DEFINITION OF CONFIDENTIAL INFORMATION
{confidentialInfo}

2. OBLIGATIONS OF RECEIVING PARTY
The Receiving Party agrees to:
a) Keep all Confidential Information strictly confidential
b) Not disclose any Confidential Information to third parties
c) Use Confidential Information only for agreed purposes
d) Take reasonable measures to protect confidentiality

3. DURATION
This Agreement shall remain in effect for {duration} years from the Effective Date.

4. GOVERNING LAW
This Agreement shall be governed by the laws of {jurisdiction}.

5. SIGNATURES

_________________________
{disclosingParty}
Date: _______________

_________________________
{receivingParty}
Date: _______________`,
  },
  {
    id: "employment",
    name: "Employment Contract",
    icon: Briefcase,
    description: "Standard employment agreement for hiring employees",
    fields: [
      { name: "employerName", label: "Employer/Company Name", type: "text", required: true },
      { name: "employeeName", label: "Employee Name", type: "text", required: true },
      { name: "position", label: "Job Position", type: "text", required: true },
      { name: "startDate", label: "Start Date", type: "date", required: true },
      { name: "salary", label: "Monthly Salary (TND)", type: "number", required: true },
      { name: "workHours", label: "Work Hours per Week", type: "number", placeholder: "40", required: true },
      { name: "probationPeriod", label: "Probation Period (months)", type: "number", placeholder: "3" },
      { name: "responsibilities", label: "Key Responsibilities", type: "textarea", required: true },
    ],
    template: `EMPLOYMENT CONTRACT

This Employment Contract is entered into between:

EMPLOYER: {employerName}
EMPLOYEE: {employeeName}

1. POSITION AND DUTIES
The Employee is hired as {position} with the following responsibilities:
{responsibilities}

2. START DATE
Employment begins on {startDate}.

3. COMPENSATION
Monthly salary: {salary} TND
Payment: End of each month via bank transfer

4. WORKING HOURS
Standard work week: {workHours} hours

5. PROBATION PERIOD
{probationPeriod} months from start date

6. BENEFITS
- Annual leave: 18 days
- Sick leave: As per Tunisian labor law
- Social security contributions

7. TERMINATION
Either party may terminate with 30 days written notice.

8. GOVERNING LAW
This contract is governed by Tunisian Labor Law.

SIGNATURES:

_________________________
Employer: {employerName}
Date: _______________

_________________________
Employee: {employeeName}
Date: _______________`,
  },
  {
    id: "service",
    name: "Service Agreement",
    icon: Handshake,
    description: "Contract for providing services to clients",
    fields: [
      { name: "providerName", label: "Service Provider Name", type: "text", required: true },
      { name: "clientName", label: "Client Name", type: "text", required: true },
      { name: "serviceDescription", label: "Description of Services", type: "textarea", required: true },
      { name: "startDate", label: "Start Date", type: "date", required: true },
      { name: "endDate", label: "End Date", type: "date" },
      { name: "totalFee", label: "Total Fee (TND)", type: "number", required: true },
      { name: "paymentTerms", label: "Payment Terms", type: "select", options: ["50% upfront, 50% on completion", "100% upfront", "100% on completion", "Monthly installments"], required: true },
      { name: "deliverables", label: "Key Deliverables", type: "textarea", required: true },
    ],
    template: `SERVICE AGREEMENT

This Service Agreement is made between:

SERVICE PROVIDER: {providerName}
CLIENT: {clientName}

1. SERVICES
The Provider agrees to deliver:
{serviceDescription}

2. DELIVERABLES
{deliverables}

3. TERM
Start Date: {startDate}
End Date: {endDate}

4. COMPENSATION
Total Fee: {totalFee} TND
Payment Terms: {paymentTerms}

5. INTELLECTUAL PROPERTY
All work product becomes Client property upon full payment.

6. CONFIDENTIALITY
Both parties agree to maintain confidentiality of proprietary information.

7. TERMINATION
Either party may terminate with 14 days written notice.

8. GOVERNING LAW
This Agreement is governed by Tunisian law.

SIGNATURES:

_________________________
Provider: {providerName}
Date: _______________

_________________________
Client: {clientName}
Date: _______________`,
  },
  {
    id: "partnership",
    name: "Partnership Agreement",
    icon: Users,
    description: "Agreement between business partners",
    fields: [
      { name: "partnershipName", label: "Partnership/Business Name", type: "text", required: true },
      { name: "partner1Name", label: "Partner 1 Name", type: "text", required: true },
      { name: "partner1Share", label: "Partner 1 Share (%)", type: "number", required: true },
      { name: "partner2Name", label: "Partner 2 Name", type: "text", required: true },
      { name: "partner2Share", label: "Partner 2 Share (%)", type: "number", required: true },
      { name: "businessPurpose", label: "Business Purpose", type: "textarea", required: true },
      { name: "initialCapital", label: "Initial Capital (TND)", type: "number", required: true },
      { name: "effectiveDate", label: "Effective Date", type: "date", required: true },
    ],
    template: `PARTNERSHIP AGREEMENT

This Partnership Agreement establishes:

PARTNERSHIP NAME: {partnershipName}
EFFECTIVE DATE: {effectiveDate}

PARTNERS:
1. {partner1Name} - {partner1Share}% ownership
2. {partner2Name} - {partner2Share}% ownership

1. BUSINESS PURPOSE
{businessPurpose}

2. CAPITAL CONTRIBUTION
Total Initial Capital: {initialCapital} TND
- {partner1Name}: {partner1Share}% = {initialCapital * partner1Share / 100} TND
- {partner2Name}: {partner2Share}% = {initialCapital * partner2Share / 100} TND

3. PROFIT AND LOSS DISTRIBUTION
Profits and losses shall be divided according to ownership percentages.

4. MANAGEMENT
Major decisions require unanimous consent of all partners.

5. WITHDRAWAL
Partners must provide 90 days notice to withdraw.

6. DISSOLUTION
Partnership may be dissolved by mutual agreement.

7. GOVERNING LAW
This Agreement is governed by Tunisian Commercial Law.

SIGNATURES:

_________________________
{partner1Name}
Date: _______________

_________________________
{partner2Name}
Date: _______________`,
  },
  {
    id: "lease",
    name: "Office Lease Agreement",
    icon: Building,
    description: "Commercial lease for office or business space",
    fields: [
      { name: "landlordName", label: "Landlord Name", type: "text", required: true },
      { name: "tenantName", label: "Tenant/Company Name", type: "text", required: true },
      { name: "propertyAddress", label: "Property Address", type: "textarea", required: true },
      { name: "monthlyRent", label: "Monthly Rent (TND)", type: "number", required: true },
      { name: "securityDeposit", label: "Security Deposit (TND)", type: "number", required: true },
      { name: "leaseStart", label: "Lease Start Date", type: "date", required: true },
      { name: "leaseDuration", label: "Lease Duration (months)", type: "number", required: true },
      { name: "purpose", label: "Purpose of Use", type: "text", placeholder: "Office space for startup operations", required: true },
    ],
    template: `COMMERCIAL LEASE AGREEMENT

This Lease Agreement is made between:

LANDLORD: {landlordName}
TENANT: {tenantName}

1. PROPERTY
Address: {propertyAddress}

2. PURPOSE
The premises shall be used for: {purpose}

3. LEASE TERM
Start Date: {leaseStart}
Duration: {leaseDuration} months

4. RENT
Monthly Rent: {monthlyRent} TND
Due: First of each month

5. SECURITY DEPOSIT
Amount: {securityDeposit} TND
Refundable at end of lease minus any damages.

6. MAINTENANCE
- Tenant: Daily cleaning and minor repairs
- Landlord: Structural repairs and major systems

7. UTILITIES
Tenant is responsible for all utilities.

8. TERMINATION
Either party may terminate with 60 days written notice.

9. GOVERNING LAW
This Agreement is governed by Tunisian Real Estate Law.

SIGNATURES:

_________________________
Landlord: {landlordName}
Date: _______________

_________________________
Tenant: {tenantName}
Date: _______________`,
  },
  {
    id: "terms",
    name: "Terms of Service",
    icon: ScrollText,
    description: "Terms and conditions for your app or service",
    fields: [
      { name: "companyName", label: "Company/App Name", type: "text", required: true },
      { name: "websiteUrl", label: "Website URL", type: "text", required: true },
      { name: "serviceDescription", label: "Description of Service", type: "textarea", required: true },
      { name: "userAge", label: "Minimum User Age", type: "number", placeholder: "18", required: true },
      { name: "contactEmail", label: "Contact Email", type: "text", required: true },
      { name: "effectiveDate", label: "Effective Date", type: "date", required: true },
    ],
    template: `TERMS OF SERVICE

Last Updated: {effectiveDate}

Welcome to {companyName}!

1. ACCEPTANCE OF TERMS
By accessing {websiteUrl}, you agree to these Terms of Service.

2. SERVICE DESCRIPTION
{serviceDescription}

3. ELIGIBILITY
You must be at least {userAge} years old to use this service.

4. USER ACCOUNTS
- You are responsible for maintaining account security
- You must provide accurate information
- One account per person

5. ACCEPTABLE USE
You agree NOT to:
- Violate any laws
- Infringe on intellectual property
- Distribute malware
- Harass other users

6. INTELLECTUAL PROPERTY
All content is owned by {companyName} or its licensors.

7. LIMITATION OF LIABILITY
{companyName} is not liable for indirect damages.

8. TERMINATION
We may terminate accounts that violate these terms.

9. CHANGES TO TERMS
We may update these terms with notice to users.

10. CONTACT
Questions? Email us at {contactEmail}

11. GOVERNING LAW
These Terms are governed by Tunisian law.`,
  },
]

export default function LegalAnalysisPage() {
  const [activeTab, setActiveTab] = useState<"generate" | "analyze">("generate")
  const [selectedTemplate, setSelectedTemplate] = useState<DocumentTemplate | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [currentFieldIndex, setCurrentFieldIndex] = useState(0)
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({})
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [generatedDocument, setGeneratedDocument] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  
  // Analysis state
  const [uploadedDoc, setUploadedDoc] = useState<UploadedDocument | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [analysisTab, setAnalysisTab] = useState<"summary" | "text" | "clauses" | "signatures">("summary")
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const selectTemplate = (template: DocumentTemplate) => {
    setSelectedTemplate(template)
    setCurrentFieldIndex(0)
    setFieldValues({})
    setGeneratedDocument(null)
    
    // Start the conversation
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: `Great! Let's create your **${template.name}**.\n\nI'll ask you a few questions to fill in the document. You can type your answers below.`,
        timestamp: new Date(),
      },
      {
        id: "question-0",
        role: "assistant",
        content: `**${template.fields[0].label}**${template.fields[0].required ? " *" : ""}\n\n${template.fields[0].placeholder ? `Example: ${template.fields[0].placeholder}` : ""}`,
        timestamp: new Date(),
        isQuestion: true,
        fieldName: template.fields[0].name,
      },
    ])
  }

  const handleSend = async () => {
    if (!input.trim() || !selectedTemplate) return

    const currentField = selectedTemplate.fields[currentFieldIndex]
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    
    // Save field value
    setFieldValues((prev) => ({ ...prev, [currentField.name]: input.trim() }))
    setInput("")
    setIsTyping(true)

    await new Promise((resolve) => setTimeout(resolve, 500))

    const nextIndex = currentFieldIndex + 1
    
    if (nextIndex < selectedTemplate.fields.length) {
      // Ask next question
      const nextField = selectedTemplate.fields[nextIndex]
      setCurrentFieldIndex(nextIndex)
      
      const questionMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Got it! Next question:\n\n**${nextField.label}**${nextField.required ? " *" : ""}\n\n${nextField.placeholder ? `Example: ${nextField.placeholder}` : ""}${nextField.options ? `\n\nOptions:\n${nextField.options.map((o, i) => `${i + 1}. ${o}`).join("\n")}` : ""}`,
        timestamp: new Date(),
        isQuestion: true,
        fieldName: nextField.name,
      }
      setMessages((prev) => [...prev, questionMessage])
    } else {
      // Generate document
      const allValues = { ...fieldValues, [currentField.name]: input.trim() }
      const document = generateDocument(selectedTemplate, allValues)
      setGeneratedDocument(document)
      
      const completeMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Your **${selectedTemplate.name}** is ready! You can preview it below, copy it, or download it as a text file.\n\nWould you like to create another document or make changes to this one?`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, completeMessage])
    }
    
    setIsTyping(false)
  }

  const generateDocument = (template: DocumentTemplate, values: Record<string, string>): string => {
    let doc = template.template
    Object.entries(values).forEach(([key, value]) => {
      doc = doc.replace(new RegExp(`{${key}}`, "g"), value)
    })
    return doc
  }

  const resetGenerator = () => {
    setSelectedTemplate(null)
    setMessages([])
    setCurrentFieldIndex(0)
    setFieldValues({})
    setGeneratedDocument(null)
  }

  const copyDocument = () => {
    if (generatedDocument) {
      navigator.clipboard.writeText(generatedDocument)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const downloadDocument = () => {
    if (generatedDocument && selectedTemplate) {
      const blob = new Blob([generatedDocument], { type: "text/plain" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${selectedTemplate.name.replace(/\s+/g, "_")}.txt`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleSend()
    }
  }

  // Analysis functions
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
    if (droppedFile && (droppedFile.type === "application/pdf" || droppedFile.type.startsWith("image/"))) {
      setUploadedDoc({ file: droppedFile })
      setAnalysisResult(null)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setUploadedDoc({ file: selectedFile })
      setAnalysisResult(null)
    }
  }

  const analyzeDocument = async () => {
    if (!uploadedDoc) return
    setIsAnalyzing(true)

    await new Promise((resolve) => setTimeout(resolve, 3000))

    const mockResult: AnalysisResult = {
      extractedText: `CONTRACT FOR SERVICES

This Agreement is entered into as of [Date] between:
Party A: [Company Name], a company incorporated under the laws of Tunisia
Party B: [Service Provider Name]

WHEREAS, Party A desires to engage Party B to provide certain services;
NOW, THEREFORE, in consideration of the mutual covenants herein contained, the parties agree as follows:

1. SERVICES
Party B shall provide the following services to Party A: [Description of services]

2. COMPENSATION
Party A agrees to pay Party B the sum of [Amount] TND for the services rendered.

3. TERM
This Agreement shall commence on [Start Date] and continue until [End Date].

4. CONFIDENTIALITY
Both parties agree to maintain the confidentiality of all proprietary information.

5. TERMINATION
Either party may terminate this Agreement with 30 days written notice.

IN WITNESS WHEREOF, the parties have executed this Agreement.`,
      summary:
        "This is a standard service agreement between two parties operating under Tunisian law. The contract establishes terms for service provision, compensation, duration, confidentiality obligations, and termination procedures. Key obligations include service delivery by Party B and payment by Party A, with mutual confidentiality requirements.",
      keyClauses: [
        {
          title: "Compensation Clause",
          content: "Party A agrees to pay Party B the sum of [Amount] TND for the services rendered.",
          importance: "high",
        },
        {
          title: "Confidentiality Clause",
          content: "Both parties agree to maintain the confidentiality of all proprietary information.",
          importance: "high",
        },
        {
          title: "Termination Clause",
          content: "Either party may terminate this Agreement with 30 days written notice.",
          importance: "medium",
        },
        {
          title: "Term Duration",
          content: "This Agreement shall commence on [Start Date] and continue until [End Date].",
          importance: "medium",
        },
      ],
      signatures: [
        { location: "Page 2, Bottom Left", status: "genuine", confidence: 94 },
        { location: "Page 2, Bottom Right", status: "suspicious", confidence: 67 },
      ],
    }

    setAnalysisResult(mockResult)
    setIsAnalyzing(false)
  }

  const clearUpload = () => {
    setUploadedDoc(null)
    setAnalysisResult(null)
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
              <div className="text-center mb-8">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm font-medium mb-6">
                  <Scale className="w-4 h-4 mr-2" />
                  Legal Document Center
                </div>
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
                  AI-Powered{" "}
                  <span className="bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
                    Legal Documents
                  </span>
                </h1>
                <p className="text-lg text-white/70 max-w-2xl mx-auto">
                  Generate professional legal documents through an interactive chat, or upload existing documents for AI analysis.
                </p>
              </div>

              {/* Tab Switcher */}
              <div className="flex justify-center mb-8">
                <div className="flex gap-2 p-1 bg-white/5 backdrop-blur-xl rounded-xl border border-white/10">
                  <button
                    onClick={() => setActiveTab("generate")}
                    className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
                      activeTab === "generate"
                        ? "bg-gradient-to-r from-purple-500 to-indigo-600 text-white"
                        : "text-white/60 hover:text-white hover:bg-white/10"
                    }`}
                  >
                    <FileSignature className="w-4 h-4" />
                    Generate Documents
                  </button>
                  <button
                    onClick={() => setActiveTab("analyze")}
                    className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
                      activeTab === "analyze"
                        ? "bg-gradient-to-r from-purple-500 to-indigo-600 text-white"
                        : "text-white/60 hover:text-white hover:bg-white/10"
                    }`}
                  >
                    <Search className="w-4 h-4" />
                    Analyze Documents
                  </button>
                </div>
              </div>

              {activeTab === "generate" ? (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                  {/* Sidebar - Document Templates */}
                  <div className="lg:col-span-4">
                    <Card className="bg-white/5 backdrop-blur-xl border-white/10 sticky top-24">
                      <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                          <FileText className="w-5 h-5 text-purple-400" />
                          Document Templates
                        </CardTitle>
                        <CardDescription className="text-white/60">
                          Select a document type to generate
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        {documentTemplates.map((template) => (
                          <button
                            key={template.id}
                            onClick={() => selectTemplate(template)}
                            className={`w-full flex items-center gap-3 p-4 rounded-xl border transition-all duration-300 text-left ${
                              selectedTemplate?.id === template.id
                                ? "bg-purple-500/20 border-purple-500/50"
                                : "bg-white/5 border-white/10 hover:border-purple-500/30 hover:bg-white/10"
                            }`}
                          >
                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                              selectedTemplate?.id === template.id
                                ? "bg-purple-500/30"
                                : "bg-white/10"
                            }`}>
                              <template.icon className={`w-5 h-5 ${
                                selectedTemplate?.id === template.id
                                  ? "text-purple-300"
                                  : "text-white/60"
                              }`} />
                            </div>
                            <div className="flex-1">
                              <p className={`font-medium ${
                                selectedTemplate?.id === template.id
                                  ? "text-white"
                                  : "text-white/80"
                              }`}>{template.name}</p>
                              <p className="text-white/50 text-xs">{template.description}</p>
                            </div>
                            <ChevronRight className={`w-4 h-4 ${
                              selectedTemplate?.id === template.id
                                ? "text-purple-400"
                                : "text-white/30"
                            }`} />
                          </button>
                        ))}
                      </CardContent>
                    </Card>
                  </div>

                  {/* Main Content - Chat Interface */}
                  <div className="lg:col-span-8">
                    {!selectedTemplate ? (
                      <Card className="bg-white/5 backdrop-blur-xl border-white/10 h-full min-h-[600px] flex items-center justify-center">
                        <CardContent className="text-center p-8">
                          <FileSignature className="w-16 h-16 text-white/20 mx-auto mb-4" />
                          <h3 className="text-xl font-semibold text-white/60 mb-2">Select a Document Type</h3>
                          <p className="text-white/40 max-w-md">
                            Choose a legal document template from the sidebar to start generating your customized document through our interactive chat.
                          </p>
                        </CardContent>
                      </Card>
                    ) : (
                      <div className="space-y-4">
                        {/* Chat Card */}
                        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                          <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                                  <selectedTemplate.icon className="w-5 h-5 text-purple-400" />
                                </div>
                                <div>
                                  <CardTitle className="text-white text-lg">{selectedTemplate.name}</CardTitle>
                                  <CardDescription className="text-white/50">
                                    {currentFieldIndex + 1} of {selectedTemplate.fields.length} fields completed
                                  </CardDescription>
                                </div>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={resetGenerator}
                                className="text-white/60 hover:text-white"
                              >
                                <X className="w-4 h-4 mr-2" />
                                Start Over
                              </Button>
                            </div>
                            {/* Progress bar */}
                            <div className="w-full bg-white/10 rounded-full h-1.5 mt-4">
                              <div
                                className="bg-gradient-to-r from-purple-500 to-indigo-500 h-1.5 rounded-full transition-all duration-500"
                                style={{ width: `${((currentFieldIndex + (generatedDocument ? 1 : 0)) / selectedTemplate.fields.length) * 100}%` }}
                              />
                            </div>
                          </CardHeader>
                          <CardContent className="p-0">
                            {/* Messages */}
                            <div className="h-[400px] overflow-y-auto p-4 space-y-4">
                              {messages.map((message) => (
                                <div
                                  key={message.id}
                                  className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}
                                >
                                  <div
                                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                                      message.role === "assistant"
                                        ? "bg-purple-500/20"
                                        : "bg-indigo-500/20"
                                    }`}
                                  >
                                    {message.role === "assistant" ? (
                                      <Bot className="w-4 h-4 text-purple-400" />
                                    ) : (
                                      <User className="w-4 h-4 text-indigo-400" />
                                    )}
                                  </div>
                                  <div
                                    className={`max-w-[80%] p-4 rounded-2xl ${
                                      message.role === "assistant"
                                        ? "bg-white/5 border border-white/10 text-white/80"
                                        : "bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 text-white"
                                    }`}
                                  >
                                    <div className="text-sm whitespace-pre-wrap">
                                      {message.content.split("\n").map((line, i) => {
                                        if (line.startsWith("**") && line.endsWith("**")) {
                                          return (
                                            <p key={i} className="font-bold text-white mb-1">
                                              {line.replace(/\*\*/g, "")}
                                            </p>
                                          )
                                        }
                                        return line ? (
                                          <p key={i} className="mb-1">
                                            {line}
                                          </p>
                                        ) : <br key={i} />
                                      })}
                                    </div>
                                  </div>
                                </div>
                              ))}
                              {isTyping && (
                                <div className="flex gap-3">
                                  <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                                    <Bot className="w-4 h-4 text-purple-400" />
                                  </div>
                                  <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                                    <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
                                  </div>
                                </div>
                              )}
                              <div ref={messagesEndRef} />
                            </div>

                            {/* Input */}
                            {!generatedDocument && (
                              <div className="border-t border-white/10 p-4">
                                <div className="flex items-center gap-3">
                                  <input
                                    ref={inputRef}
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Type your answer..."
                                    className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                                  />
                                  <Button
                                    onClick={handleSend}
                                    disabled={!input.trim() || isTyping}
                                    className="bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white rounded-xl px-6"
                                  >
                                    <Send className="w-5 h-5" />
                                  </Button>
                                </div>
                              </div>
                            )}
                          </CardContent>
                        </Card>

                        {/* Generated Document Preview */}
                        {generatedDocument && (
                          <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                            <CardHeader>
                              <div className="flex items-center justify-between">
                                <CardTitle className="text-white flex items-center gap-2">
                                  <Eye className="w-5 h-5 text-purple-400" />
                                  Document Preview
                                </CardTitle>
                                <div className="flex items-center gap-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={copyDocument}
                                    className="bg-white/5 border-white/20 text-white hover:bg-white/10"
                                  >
                                    {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                                    {copied ? "Copied!" : "Copy"}
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={downloadDocument}
                                    className="bg-white/5 border-white/20 text-white hover:bg-white/10"
                                  >
                                    <Download className="w-4 h-4 mr-2" />
                                    Download
                                  </Button>
                                </div>
                              </div>
                            </CardHeader>
                            <CardContent>
                              <pre className="text-white/80 whitespace-pre-wrap font-mono text-sm bg-white/5 p-6 rounded-xl border border-white/10 max-h-[500px] overflow-y-auto">
                                {generatedDocument}
                              </pre>
                            </CardContent>
                          </Card>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                /* Analyze Tab */
                <div className="max-w-6xl mx-auto">
                  {/* Upload Section */}
                  <Card className="bg-white/5 backdrop-blur-xl border-white/10 mb-8">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Upload className="w-5 h-5 text-purple-400" />
                        Upload Document for Analysis
                      </CardTitle>
                      <CardDescription className="text-white/60">
                        Upload a legal document (PDF, PNG, JPG) to extract text, identify key clauses, and verify signatures
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {!uploadedDoc ? (
                        <div
                          onDragOver={handleDragOver}
                          onDragLeave={handleDragLeave}
                          onDrop={handleDrop}
                          className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
                            isDragging
                              ? "border-purple-400 bg-purple-500/10"
                              : "border-white/20 hover:border-purple-400/50"
                          }`}
                        >
                          <Upload className="w-12 h-12 text-purple-400 mx-auto mb-4" />
                          <p className="text-white/70 mb-4">Drag and drop your document here, or</p>
                          <label className="cursor-pointer">
                            <input
                              type="file"
                              accept=".pdf,image/*"
                              onChange={handleFileSelect}
                              className="hidden"
                            />
                            <span className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white rounded-full font-medium transition-all duration-300 hover:scale-105">
                              Browse Files
                            </span>
                          </label>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10">
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center">
                              <FileText className="w-6 h-6 text-purple-400" />
                            </div>
                            <div>
                              <p className="text-white font-medium">{uploadedDoc.file.name}</p>
                              <p className="text-white/50 text-sm">{(uploadedDoc.file.size / 1024).toFixed(1)} KB</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            {!analysisResult && (
                              <Button
                                onClick={analyzeDocument}
                                disabled={isAnalyzing}
                                className="bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white"
                              >
                                {isAnalyzing ? (
                                  <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Analyzing...
                                  </>
                                ) : (
                                  <>
                                    <Search className="w-4 h-4 mr-2" />
                                    Analyze Document
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

                  {/* Analysis Results */}
                  {analysisResult && (
                    <div className="space-y-6">
                      {/* Tabs */}
                      <div className="flex gap-2 p-1 bg-white/5 backdrop-blur-xl rounded-xl border border-white/10">
                        {[
                          { id: "summary", label: "Summary", icon: FileText },
                          { id: "text", label: "Extracted Text", icon: Search },
                          { id: "clauses", label: "Key Clauses", icon: AlertTriangle },
                          { id: "signatures", label: "Signatures", icon: Shield },
                        ].map((tab) => (
                          <button
                            key={tab.id}
                            onClick={() => setAnalysisTab(tab.id as typeof analysisTab)}
                            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all duration-300 ${
                              analysisTab === tab.id
                                ? "bg-gradient-to-r from-purple-500 to-indigo-600 text-white"
                                : "text-white/60 hover:text-white hover:bg-white/10"
                            }`}
                          >
                            <tab.icon className="w-4 h-4" />
                            <span className="hidden sm:inline">{tab.label}</span>
                          </button>
                        ))}
                      </div>

                      {/* Tab Content */}
                      <Card className="bg-white/5 backdrop-blur-xl border-white/10">
                        <CardContent className="p-6">
                          {analysisTab === "summary" && (
                            <div>
                              <h3 className="text-xl font-bold text-white mb-4">Document Summary</h3>
                              <p className="text-white/80 leading-relaxed">{analysisResult.summary}</p>
                            </div>
                          )}

                          {analysisTab === "text" && (
                            <div>
                              <h3 className="text-xl font-bold text-white mb-4">Extracted Text</h3>
                              <pre className="text-white/80 whitespace-pre-wrap font-mono text-sm bg-white/5 p-4 rounded-lg border border-white/10 max-h-96 overflow-y-auto">
                                {analysisResult.extractedText}
                              </pre>
                            </div>
                          )}

                          {analysisTab === "clauses" && (
                            <div>
                              <h3 className="text-xl font-bold text-white mb-4">Key Clauses Identified</h3>
                              <div className="space-y-4">
                                {analysisResult.keyClauses.map((clause, index) => (
                                  <div
                                    key={index}
                                    className={`p-4 rounded-lg border ${
                                      clause.importance === "high"
                                        ? "bg-red-500/10 border-red-500/30"
                                        : clause.importance === "medium"
                                          ? "bg-yellow-500/10 border-yellow-500/30"
                                          : "bg-white/5 border-white/10"
                                    }`}
                                  >
                                    <div className="flex items-center gap-2 mb-2">
                                      <h4 className="font-semibold text-white">{clause.title}</h4>
                                      <span
                                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                          clause.importance === "high"
                                            ? "bg-red-500/20 text-red-300"
                                            : clause.importance === "medium"
                                              ? "bg-yellow-500/20 text-yellow-300"
                                              : "bg-white/10 text-white/60"
                                        }`}
                                      >
                                        {clause.importance} importance
                                      </span>
                                    </div>
                                    <p className="text-white/70 text-sm">{clause.content}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {analysisTab === "signatures" && (
                            <div>
                              <h3 className="text-xl font-bold text-white mb-4">Signature Analysis</h3>
                              <div className="space-y-4">
                                {analysisResult.signatures.map((sig, index) => (
                                  <div
                                    key={index}
                                    className={`p-4 rounded-lg border flex items-center justify-between ${
                                      sig.status === "genuine"
                                        ? "bg-green-500/10 border-green-500/30"
                                        : sig.status === "suspicious"
                                          ? "bg-red-500/10 border-red-500/30"
                                          : "bg-yellow-500/10 border-yellow-500/30"
                                    }`}
                                  >
                                    <div className="flex items-center gap-4">
                                      {sig.status === "genuine" ? (
                                        <CheckCircle className="w-8 h-8 text-green-400" />
                                      ) : sig.status === "suspicious" ? (
                                        <AlertTriangle className="w-8 h-8 text-red-400" />
                                      ) : (
                                        <Shield className="w-8 h-8 text-yellow-400" />
                                      )}
                                      <div>
                                        <p className="text-white font-medium">Signature #{index + 1}</p>
                                        <p className="text-white/60 text-sm">{sig.location}</p>
                                      </div>
                                    </div>
                                    <div className="text-right">
                                      <p
                                        className={`font-semibold ${
                                          sig.status === "genuine"
                                            ? "text-green-400"
                                            : sig.status === "suspicious"
                                              ? "text-red-400"
                                              : "text-yellow-400"
                                        }`}
                                      >
                                        {sig.status === "genuine"
                                          ? "Likely Genuine"
                                          : sig.status === "suspicious"
                                            ? "Potentially Forged"
                                            : "Unverified"}
                                      </p>
                                      <p className="text-white/60 text-sm">Confidence: {sig.confidence}%</p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
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

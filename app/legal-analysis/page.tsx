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
  file_name?: string
}

interface DocumentField {
  name: string
  label: string
  type: "text" | "date" | "textarea" | "number" | "select"
  placeholder?: string
  options?: string[]
  required?: boolean
  sourceToken?: string
  question?: string
  suggestions?: string[]
}

interface UploadedDocument {
  file: File
  preview?: string
}

interface AnalysisResult {
  sourceName?: string
  documentKind?: string
  extractedText: string
  summary: string
  summarySources?: string[]
  extractiveSummary?: string
  domainTags?: string[]
  riskFlags?: string[]
  openQuestions?: string[]
  startupSignals?: { title?: string; snippet?: string; category?: string; score?: number }[]
  keyClauses: {
    title: string
    content: string
    importance: "high" | "medium" | "low"
    category?: string
    score?: number
  }[]
  signatures: { location: string; status: "genuine" | "suspicious" | "unverified"; confidence: number }[]
  ocrAnnotatedImageUrl?: string
  signatureAnnotatedImageUrl?: string
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

const getTemplateIcon = (name: string): React.ElementType => {
  const lowerName = name.toLowerCase()
  if (lowerName.includes("employment")) return Briefcase
  if (lowerName.includes("service") || lowerName.includes("advisor")) return Handshake
  if (lowerName.includes("nda") || lowerName.includes("non-disclosure")) return Shield
  if (lowerName.includes("founder") || lowerName.includes("partnership")) return Users
  if (lowerName.includes("lease") || lowerName.includes("office")) return Building
  if (lowerName.includes("terms") || lowerName.includes("policy")) return ScrollText
  if (lowerName.includes("assignment") || lowerName.includes("license")) return FileSignature
  return FileText
}

const mapBackendTemplate = (template: any): DocumentTemplate => {
  const fields = Array.isArray(template.fields) && template.fields.length > 0
    ? template.fields
    : Array.isArray(template.placeholders)
      ? template.placeholders.map((placeholder: string) => ({
          name: placeholder.replace(/[^A-Za-z0-9]+/g, "_").toLowerCase(),
          label: placeholder,
          type: placeholder.length > 30 ? "textarea" : "text",
          required: true,
        }))
      : []

  return {
    id: String(template.id || template.file_name || template.name),
    name: String(template.name || template.file_name || template.id),
    icon: getTemplateIcon(String(template.name || template.file_name || template.id)),
    description: String(template.description || `Template loaded from ${template.file_name || template.id}`),
    fields,
    template: String(template.template || template.content || ""),
    file_name: String(template.file_name || ""),
  }
}

const escapeRegExp = (value: string): string => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")

const replaceAllOccurrences = (text: string, token: string, value: string): string => {
  if (!token) return text
  return text.replace(new RegExp(escapeRegExp(token), "g"), value)
}

const extractClauseBlocks = (text: string): { number: number; title: string }[] => {
  const clauses: { number: number; title: string }[] = []
  const seen = new Set<number>()
  for (const line of text.split(/\r?\n/)) {
    const match = line.match(/^\s*(\d+)\.\s+(.+?)\s*$/)
    if (!match) continue
    const number = Number(match[1])
    if (seen.has(number)) continue
    seen.add(number)
    clauses.push({ number, title: match[2].replace(/[:.]+$/, "") })
  }
  return clauses
}

const removeClauseBlockFromText = (text: string, clauseNumber: number): string => {
  const lines = text.split(/\r?\n/)
  const startIndex = lines.findIndex((line) => new RegExp(`^\\s*${clauseNumber}\\.\\s+`).test(line))
  if (startIndex < 0) return text

  let endIndex = lines.length
  for (let i = startIndex + 1; i < lines.length; i += 1) {
    if (/^\s*\d+\.\s+/.test(lines[i]) || /^\s*signatures?:?\s*$/i.test(lines[i])) {
      endIndex = i
      break
    }
  }

  const next = [...lines]
  next.splice(startIndex, endIndex - startIndex)
  return next.join("\n")
}

export default function LegalAnalysisPage() {
  const [activeTab, setActiveTab] = useState<"generate" | "analyze">("generate")
  const [selectedTemplate, setSelectedTemplate] = useState<DocumentTemplate | null>(null)
  const [templateCatalog, setTemplateCatalog] = useState<DocumentTemplate[]>(documentTemplates)
  const [messages, setMessages] = useState<Message[]>([])
  const [currentFieldIndex, setCurrentFieldIndex] = useState(0)
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({})
  const [predictedValues, setPredictedValues] = useState<Record<string, string>>({})
  const [workingTemplateText, setWorkingTemplateText] = useState<string>("")
  const [clauseReviewIndex, setClauseReviewIndex] = useState(0)
  const [clauseItems, setClauseItems] = useState<{ number: number; title: string }[]>([])
  const [removedClauseNumbers, setRemovedClauseNumbers] = useState<number[]>([])
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
  const currentField = selectedTemplate?.fields[currentFieldIndex]

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    let isCancelled = false

    const loadTemplates = async () => {
      try {
        const response = await fetch("http://localhost:5000/api/legal/templates", {
          credentials: "include",
        })

        if (!response.ok) return

        const payload = await response.json()
        const backendTemplates = Array.isArray(payload.templates)
          ? payload.templates.map(mapBackendTemplate)
          : []

        if (!isCancelled && backendTemplates.length > 0) {
          setTemplateCatalog(backendTemplates)
        }
      } catch {
        if (!isCancelled) {
          setTemplateCatalog(documentTemplates)
        }
      }
    }

    void loadTemplates()

    return () => {
      isCancelled = true
    }
  }, [])

  const selectTemplate = (template: DocumentTemplate) => {
    setSelectedTemplate(template)
    setCurrentFieldIndex(0)
    setFieldValues({})
    setPredictedValues({})
    setWorkingTemplateText(template.template || "")
    setClauseItems([])
    setClauseReviewIndex(0)
    setRemovedClauseNumbers([])
    setGeneratedDocument(null)

    if (!template.fields.length) {
      setGeneratedDocument(template.template || "")
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: `I found **${template.name}** in your templates folder, but it does not expose placeholders yet. Please select a different template.`,
          timestamp: new Date(),
        },
      ])
      setInput("")
      return
    }

    const firstField = template.fields[0]
    const startMessages: Message[] = [
      {
        id: "welcome",
        role: "assistant",
        content: `Great! Let's create your **${template.name}**.\n\nI'll ask you for the placeholders one by one.`,
        timestamp: new Date(),
      },
      {
        id: "question-0",
        role: "assistant",
        content: `${(firstField as any).question || `**${firstField.label}**${firstField.required ? " *" : ""}`}${firstField.placeholder ? `\n\nExample: ${firstField.placeholder}` : ""}${(firstField as any).suggestions && (firstField as any).suggestions.length > 0 ? `\n\nSuggested: ${(firstField as any).suggestions.join(", ")}` : ""}`,
        timestamp: new Date(),
        isQuestion: true,
        fieldName: firstField.name,
      },
    ]

    setMessages(startMessages)

    if ((template as any).file_name) {
      ;(async () => {
        try {
          const resp = await fetch("http://localhost:5000/api/legal/infer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ file_name: (template as any).file_name, brief_text: "" }),
          })
          if (!resp.ok) throw new Error("infer-failed")
          const payload = await resp.json()
          const report = payload.report || {}
          const placeholderData = report.placeholder_data || {}

          const prefilled: Record<string, string> = {}
          for (const field of template.fields) {
            const token = (field as any).sourceToken
            if (!token) continue
            const sourceVal = placeholderData[token]
            if (sourceVal === undefined) continue

            if (Array.isArray(sourceVal)) {
              const m = field.name.match(/_(\d+)$/)
              const idx = m ? parseInt(m[1], 10) - 1 : 0
              const chosen = sourceVal[idx] ?? sourceVal[0]
              if (chosen && typeof chosen === "string") prefilled[field.name] = chosen
            } else if (typeof sourceVal === "string") {
              prefilled[field.name] = sourceVal
            }
          }

          setFieldValues((prev) => ({ ...prev, ...prefilled }))
          setPredictedValues(prefilled)
        } catch (e) {
          // keep the local questions even if inference fails
        }
      })()
    }
  }

  const handleSend = async () => {
    if (!input.trim() || !selectedTemplate || selectedTemplate.fields.length === 0) return

    const trimmedInput = input.trim()
    const currentField = selectedTemplate.fields[currentFieldIndex]
    if (!currentField) return

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: trimmedInput,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    
    // Save field value
    setFieldValues((prev) => ({ ...prev, [currentField.name]: trimmedInput }))
    setInput("")
    setIsTyping(true)

    await new Promise((resolve) => setTimeout(resolve, 500))

    const nextIndex = currentFieldIndex + 1
    
    if (nextIndex < selectedTemplate.fields.length) {
      // Ask next question
      const nextField = selectedTemplate.fields[nextIndex]
      setCurrentFieldIndex(nextIndex)
      
      const qText = (nextField as any).question || `**${nextField.label}**${nextField.required ? " *" : ""}`
      const example = (nextField as any).placeholder ? `\n\nExample: ${(nextField as any).placeholder}` : ""
      const optionText = nextField.options ? `\n\nOptions:\n${nextField.options.map((o, i) => `${i + 1}. ${o}`).join("\n")}` : ""
      const suggestionText = (nextField as any).suggestions && (nextField as any).suggestions.length > 0
        ? `\n\nSuggested: ${(nextField as any).suggestions.join(", ")}`
        : ""

      const questionMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Got it! Next question:\n\n${qText}${example}${optionText}${suggestionText}`,
        timestamp: new Date(),
        isQuestion: true,
        fieldName: nextField.name,
      }
      setMessages((prev) => [...prev, questionMessage])
    } else {
      // Generate document
      const allValues = { ...predictedValues, ...fieldValues, [currentField.name]: trimmedInput }
      const document = generateDocument(selectedTemplate, allValues)
      setGeneratedDocument(document)
      
      const completeMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Your **${selectedTemplate.name}** is ready! You can preview it below, copy it, or download it as Word/PDF.\n\nWould you like to create another document or make changes to this one?`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, completeMessage])
    }
    
    setIsTyping(false)
  }

  const generateDocument = (template: DocumentTemplate, values: Record<string, string>): string => {
    let doc = workingTemplateText || template.template
    template.fields.forEach((field) => {
      const value = values[field.name]
      if (typeof value !== "string") return

      doc = doc.replace(new RegExp(`{${field.name}}`, "g"), value)

      if (field.sourceToken) {
        doc = replaceAllOccurrences(doc, field.sourceToken, value)
      }
    })
    return doc
  }

  const getResolvedFieldValues = (): Record<string, string> => ({
    ...predictedValues,
    ...fieldValues,
  })

  const editDocumentDraft = (documentText: string, command: string): string => {
    const lines = documentText.split(/\r?\n/)
    const lowerCommand = command.toLowerCase()

    const getLastClauseNumber = () => {
      let maxClause = 0
      for (const line of lines) {
        const match = line.match(/^\s*(\d+)\.\s+/)
        if (match) {
          maxClause = Math.max(maxClause, Number(match[1]))
        }
      }
      return maxClause
    }

    const insertBeforeSignatures = (text: string) => {
      const signatureIndex = lines.findIndex((line) => /^\s*signatures?:?\s*$/i.test(line))
      const insertionIndex = signatureIndex >= 0 ? signatureIndex : lines.length
      const block = ["", text, ""]
      lines.splice(insertionIndex, 0, ...block)
      return lines.join("\n")
    }

    const removeMatchingClause = (keyword: string) => {
      const normalizedKeyword = keyword.trim().toLowerCase()
      if (!normalizedKeyword) return documentText

      const clauseStartIndexes = lines
        .map((line, index) => ({ line, index }))
        .filter(({ line }) => /^\s*\d+\.\s+/.test(line))

      for (const { line, index } of clauseStartIndexes) {
        if (!line.toLowerCase().includes(normalizedKeyword)) continue

        let endIndex = lines.length
        for (let i = index + 1; i < lines.length; i += 1) {
          if (/^\s*\d+\.\s+/.test(lines[i]) || /^\s*signatures?:?\s*$/i.test(lines[i])) {
            endIndex = i
            break
          }
        }

        lines.splice(index, endIndex - index)
        return lines.join("\n")
      }

      return documentText
    }

    if (/^add\s+clause\b/i.test(command)) {
      const clauseText = command.replace(/^add\s+clause(?:\s+about)?[:\-]?\s*/i, "").trim()
      const nextClauseNumber = getLastClauseNumber() + 1
      const addition = `${nextClauseNumber}. ${clauseText || "Additional clause to be agreed by the parties."}`
      return insertBeforeSignatures(addition)
    }

    if (/^(remove|delete)\s+clause\b/i.test(command)) {
      const keyword = command.replace(/^(remove|delete)\s+clause(?:\s+about)?[:\-]?\s*/i, "").trim()
      return removeMatchingClause(keyword)
    }

    if (/^replace\s+clause\b/i.test(command)) {
      const replacement = command.replace(/^replace\s+clause(?:\s+with)?[:\-]?\s*/i, "").trim()
      if (!replacement) return documentText
      const nextClauseNumber = getLastClauseNumber() + 1
      return insertBeforeSignatures(`${nextClauseNumber}. ${replacement}`)
    }

    return documentText
  }

  const getSuggestedAnswers = (field: DocumentField): string[] => {
    const label = field.label.toLowerCase()
    if (field.options?.length) return field.options
    if ((field as any).suggestions && (field as any).suggestions.length > 0) return (field as any).suggestions
    if (predictedValues[field.name]) return [predictedValues[field.name]]
    if (label.includes("date")) return [new Date().toISOString().slice(0, 10)]
    if (label.includes("jurisdiction") || label.includes("governing law")) return ["Tunisia", "Estonia", "France"]
    if (label.includes("registry code") || label.includes("identification code")) return ["12345678", "87654321"]
    if (label.includes("email")) return ["legal@northstar.com", "founder@company.com"]
    if (label.includes("address")) return ["Tunis, Tunisia", "Tallinn, Estonia"]
    if (label.includes("company") || label.includes("party") || label.includes("provider") || label.includes("client")) {
      return ["North Star LLC", "Acme OÜ"]
    }
    if (label.includes("salary") || label.includes("rent") || label.includes("fee") || label.includes("capital") || label.includes("amount") || label.includes("eur")) {
      return ["10000", "25000"]
    }
    if (label.includes("share") || label.includes("percentage") || label.includes("%")) return ["10", "20", "50"]
    if (label.includes("duration") || label.includes("months") || label.includes("years")) return ["12", "24", "36"]
    if (label.includes("purpose") || label.includes("services") || label.includes("responsibilities")) {
      return ["Advisory services for product and fundraising", "Software development and support"]
    }
    return []
  }

  const applySuggestedAnswer = (suggestion: string) => {
    setInput(suggestion)
    inputRef.current?.focus()
  }

  const resetGenerator = () => {
    setSelectedTemplate(null)
    setMessages([])
    setCurrentFieldIndex(0)
    setFieldValues({})
    setPredictedValues({})
    setWorkingTemplateText("")
    setClauseReviewIndex(0)
    setClauseItems([])
    setRemovedClauseNumbers([])
    setGeneratedDocument(null)
  }

  const copyDocument = () => {
    if (generatedDocument) {
      navigator.clipboard.writeText(generatedDocument)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const downloadDocumentAs = async (format: "docx" | "pdf") => {
    if (!generatedDocument || !selectedTemplate) return

    const response = await fetch("http://localhost:5000/api/legal/export", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify({
        title: selectedTemplate.name,
        file_name: selectedTemplate.file_name,
        content: generatedDocument,
        values: getResolvedFieldValues(),
        remove_clause_numbers: removedClauseNumbers,
        format,
      }),
    })

    if (!response.ok) {
      throw new Error(`Failed to export ${format.toUpperCase()}`)
    }

    const payload = await response.json()
    const fileResponse = await fetch(`http://localhost:5000${payload.download_url}`, {
      credentials: "include",
    })
    const blob = await fileResponse.blob()
    const blobUrl = URL.createObjectURL(blob)
    const anchor = document.createElement("a")
    anchor.href = blobUrl
    anchor.download = payload.file_name || `${selectedTemplate.name.replace(/\s+/g, "_")}.${format}`
    anchor.click()
    URL.revokeObjectURL(blobUrl)
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

    try {
      const formData = new FormData()
      formData.append('file', uploadedDoc.file)
      formData.append('question', '')

      const response = await fetch('http://localhost:5000/api/document/intel-upload', {
        method: 'POST',
        credentials: "include",
        body: formData,
      })
      
      if (!response.ok) {
        throw new Error('Failed to analyze document')
      }
      
      const data = await response.json()
      const sourceName = data.source_name || uploadedDoc.file.name
      
      // Transform backend signature format to frontend format
      const backendSignatures = data.signatures || []
      const signatures: AnalysisResult["signatures"] = backendSignatures
        .slice(0, 5) // Limit to top 5 signatures to avoid clutter
        .map((sig: any) => {
          // Backend returns: box, confidence, class_name, class_id
          // Frontend expects: location, status, confidence
          const box = sig.box || sig.bbox || []
          const location = box.length >= 4 
            ? `Position (${Math.round(box[0])}, ${Math.round(box[1])})` 
            : 'Unknown location'
          
          // Handle confidence as either decimal (0-1) or percentage (0-100)
          let confidence = sig.confidence || 0
          if (confidence <= 1) {
            confidence = Math.round(confidence * 100)
          } else {
            confidence = Math.round(confidence)
          }
          
          // Determine status based on class_name or confidence
          let status: "genuine" | "suspicious" | "unverified" = "unverified"
          if (sig.class_name) {
            const className = sig.class_name.toLowerCase()
            if (className.includes('genuine') || className.includes('real')) {
              status = "genuine"
            } else if (className.includes('fake') || className.includes('forged')) {
              status = "suspicious"
            }
          }
          
          return {
            location,
            status,
            confidence,
          }
        })
      
      const signatureAnnotatedImageUrl = data.signature_annotated_image_url || undefined
      const ocrAnnotatedImageUrl = data.annotated_image_url || undefined

      // Transform key clauses with better formatting
      const keyClauses = (data.key_clauses || [])
        .slice(0, 10) // Limit to top 10 clauses
        .map((clause: any) => ({
          title: clause.title || clause.category || 'Clause',
          content: clause.snippet || clause.content || `${clause.category || 'Clause'} found in document`,
          importance:
            clause.importance ||
            (typeof clause.score === 'number' && clause.score >= 7
              ? 'high'
              : typeof clause.score === 'number' && clause.score >= 5
                ? 'medium'
                : 'low'),
          category: clause.category,
          score: clause.score,
        }))

      // Transform backend response to frontend format
      const transformedResult: AnalysisResult = {
        extractedText: data.extractedText || data.text || data.content || 'No text extracted',
        summary: data.summary || data.extractive_summary || data.extractiveSummary || 'Analysis completed',
        sourceName,
        documentKind: data.document_kind || 'legal document',
        summarySources: data.summary_sources || [],
        extractiveSummary: data.extractive_summary || data.extractiveSummary || '',
        domainTags: data.domain_tags || data.domainTags || [],
        riskFlags: data.risk_flags || data.riskFlags || [],
        openQuestions: data.open_questions || data.openQuestions || [],
        startupSignals: data.startup_signals || data.startupSignals || [],
        keyClauses,
        signatures,
        ocrAnnotatedImageUrl,
        signatureAnnotatedImageUrl,
      }

      setAnalysisResult(transformedResult)
    } catch (error) {
      console.error('Analysis error:', error)
      // Fallback to mock data if analysis fails
      const mockResult: AnalysisResult = {
        extractedText: `Failed to analyze document. Please try again or contact support.`,
        summary: "Error during analysis",
        sourceName: uploadedDoc.file.name,
        summarySources: [],
        extractiveSummary: '',
        domainTags: [],
        riskFlags: [],
        openQuestions: [],
        startupSignals: [],
        keyClauses: [],
        signatures: [],
      }
      setAnalysisResult(mockResult)
    } finally {
      setIsAnalyzing(false)
    }
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
                        {templateCatalog.map((template) => (
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
                                {currentField && getSuggestedAnswers(currentField).length > 0 && (
                                  <div className="mb-3">
                                    <p className="text-xs uppercase tracking-wide text-white/40 mb-2">Suggested answers</p>
                                    <div className="flex flex-wrap gap-2">
                                      {getSuggestedAnswers(currentField).map((suggestion) => (
                                        <button
                                          key={suggestion}
                                          type="button"
                                          onClick={() => applySuggestedAnswer(suggestion)}
                                          className="px-3 py-1.5 rounded-full border border-white/10 bg-white/5 text-white/70 text-xs hover:bg-white/10 hover:text-white transition-colors"
                                        >
                                          {suggestion}
                                        </button>
                                      ))}
                                    </div>
                                  </div>
                                )}
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
                                    onClick={() => void downloadDocumentAs("docx")}
                                    className="bg-white/5 border-white/20 text-white hover:bg-white/10"
                                  >
                                    <Download className="w-4 h-4 mr-2" />
                                    Word
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => void downloadDocumentAs("pdf")}
                                    className="bg-white/5 border-white/20 text-white hover:bg-white/10"
                                  >
                                    <Download className="w-4 h-4 mr-2" />
                                    PDF
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
                              <div className="mb-5 grid gap-3 sm:grid-cols-2 text-sm">
                                <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-white/70">
                                  <p className="text-white/40 text-xs uppercase tracking-wide mb-1">Document kind</p>
                                  <p className="text-white">{analysisResult.documentKind || "legal document"}</p>
                                </div>
                                <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-white/70">
                                  <p className="text-white/40 text-xs uppercase tracking-wide mb-1">Source</p>
                                  <p className="text-white">{analysisResult.sourceName || uploadedDoc?.file.name || "Unknown"}</p>
                                </div>
                              </div>
                              <h3 className="text-xl font-bold text-white mb-4">Document Summary</h3>
                              <p className="text-white/80 leading-relaxed">{analysisResult.summary}</p>
                              {analysisResult.domainTags && analysisResult.domainTags.length > 0 && (
                                <div className="mt-5 flex flex-wrap gap-2">
                                  {analysisResult.domainTags.map((tag) => (
                                    <span key={tag} className="px-3 py-1 rounded-full bg-white/10 border border-white/10 text-white/70 text-xs">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                              {analysisResult.extractiveSummary && analysisResult.extractiveSummary !== analysisResult.summary && (
                                <div className="mt-4 p-4 rounded-lg border border-white/10 bg-white/5">
                                  <p className="text-xs uppercase tracking-wide text-white/40 mb-2">Extractive Summary</p>
                                  <p className="text-white/70 text-sm leading-relaxed">{analysisResult.extractiveSummary}</p>
                                </div>
                              )}
                              {analysisResult.summarySources && analysisResult.summarySources.length > 0 && (
                                <p className="mt-4 text-xs text-white/40">Summary sources: {analysisResult.summarySources.join(', ')}</p>
                              )}
                              {analysisResult.riskFlags && analysisResult.riskFlags.length > 0 && (
                                <div className="mt-6">
                                  <h4 className="text-sm font-semibold text-white mb-3">Important Issues to Review</h4>
                                  <div className="space-y-2">
                                    {analysisResult.riskFlags.map((flag, index) => (
                                      <div key={index} className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-100 text-sm">
                                        {flag}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {analysisResult.startupSignals && analysisResult.startupSignals.length > 0 && (
                                <div className="mt-6">
                                  <h4 className="text-sm font-semibold text-white mb-3">Startup Signals</h4>
                                  <div className="space-y-2">
                                    {analysisResult.startupSignals.map((signal: any, index) => (
                                      <div key={index} className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-100 text-sm">
                                        <div className="font-medium">{signal.title || signal.category || `Signal ${index + 1}`}</div>
                                        {signal.snippet && <div className="mt-1 text-emerald-50/80">{signal.snippet}</div>}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {analysisResult.openQuestions && analysisResult.openQuestions.length > 0 && (
                                <div className="mt-6">
                                  <h4 className="text-sm font-semibold text-white mb-3">Questions to Ask</h4>
                                  <div className="space-y-2">
                                    {analysisResult.openQuestions.map((question, index) => (
                                      <div key={index} className="p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-100 text-sm">
                                        {question}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
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
                                    {(clause.category || typeof clause.score === "number") && (
                                      <p className="mb-2 text-xs text-white/40">
                                        {clause.category ? `Category: ${clause.category}` : ''}
                                        {clause.category && typeof clause.score === 'number' ? ' • ' : ''}
                                        {typeof clause.score === 'number' ? `Score: ${clause.score.toFixed(2)}` : ''}
                                      </p>
                                    )}
                                    <p className="text-white/70 text-sm">{clause.content}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {analysisTab === "signatures" && (
                            <div>
                              <h3 className="text-xl font-bold text-white mb-4">Signature Analysis</h3>
                              <div className="grid gap-4 md:grid-cols-2 mb-5">
                                {analysisResult.ocrAnnotatedImageUrl && (
                                  <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                                    <p className="text-white/70 text-sm mb-2">OCR bounding boxes</p>
                                    <img src={`http://localhost:5000${analysisResult.ocrAnnotatedImageUrl}`} alt="OCR annotated preview" className="w-full rounded-lg border border-white/10" />
                                  </div>
                                )}
                                {analysisResult.signatureAnnotatedImageUrl && (
                                  <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                                    <p className="text-white/70 text-sm mb-2">Signature detection boxes</p>
                                    <img src={`http://localhost:5000${analysisResult.signatureAnnotatedImageUrl}`} alt="Signature detection preview" className="w-full rounded-lg border border-white/10" />
                                  </div>
                                )}
                              </div>
                              <div className="space-y-4">
                                {analysisResult.signatures.length > 0 ? (
                                  analysisResult.signatures.map((sig, index) => (
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
                                  ))
                                ) : (
                                  <div className="p-4 rounded-lg border border-white/10 bg-white/5 text-white/60 text-sm">
                                    No signature was detected for this upload.
                                  </div>
                                )}
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

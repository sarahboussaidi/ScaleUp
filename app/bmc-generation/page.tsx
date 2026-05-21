"use client"

import { useState, useCallback } from "react"
import type { ElementType } from "react"
import { useRouter } from "next/navigation"
import {
  Leaf,
  Sparkles,
  Target,
  Recycle,
  TrendingUp,
  Handshake,
  Cog,
  Package,
  Heart,
  MessageSquare,
  Truck,
  Users,
  DollarSign,
  ArrowLeft,
} from "lucide-react"
import { GlassmorphismNav } from "@/components/glassmorphism-nav"
import Aurora from "@/components/Aurora"
import { Footer } from "@/components/footer"
import UploadSection from "@/components/bmc-generation/upload-section"
import ProgressSection from "@/components/bmc-generation/progress-section"
import DocumentTypeCard from "@/components/bmc-generation/document-type-card"
import TextPreview from "@/components/bmc-generation/text-preview"
import ClassificationResults from "@/components/bmc-generation/classification-results"
import BMCCanvas from "@/components/bmc-generation/bmc-canvas"
import ExportControls from "@/components/bmc-generation/export-controls"
import EditableBMCBlock from "@/components/bmc-generation/editable-bmc-block"

type PipelineStep = "upload" | "classify-document" | "process-bmc" | "completed"
type DocumentType = "bmc" | "handwritten" | "typed" | null

interface SdgPrediction {
  sdg: string
  confidence: number
}

interface RagChunk {
  source?: string
  text?: string
  distance?: number
}

const SDG_NAME_MAP: Record<number, string> = {
  1: "No Poverty",
  2: "Zero Hunger",
  3: "Good Health and Well-being",
  4: "Quality Education",
  5: "Gender Equality",
  6: "Clean Water and Sanitation",
  7: "Affordable and Clean Energy",
  8: "Decent Work and Economic Growth",
  9: "Industry, Innovation and Infrastructure",
  10: "Reduced Inequalities",
  11: "Sustainable Cities and Communities",
  12: "Responsible Consumption and Production",
  13: "Climate Action",
  14: "Life Below Water",
  15: "Life on Land",
  16: "Peace, Justice and Strong Institutions",
  17: "Partnerships for the Goals",
}

const formatSdgLabel = (raw: string) => {
  const label = String(raw || "").trim()
  const match = label.match(/^LABEL_(\d+)$/i)
  if (match) {
    const num = Number(match[1]) + 1
    const name = SDG_NAME_MAP[num] || `SDG ${num}`
    return `SDG ${num}: ${name}`
  }
  return label
}

interface PipelineState {
  currentStep: PipelineStep
  isProcessing: boolean
  isComplete: boolean
}

interface GeneratedBMC {
  keyPartners: string
  keyActivities: string
  keyResources: string
  valueProposition: string
  customerRelationships: string
  channels: string
  customerSegments: string
  costStructure: string
  revenueStreams: string
}

type SustainableSectionKey =
  | "keyPartnerships"
  | "keyActivities"
  | "keyResources"
  | "valueProposition"
  | "customerRelationships"
  | "channels"
  | "customerSegments"
  | "costStructure"
  | "revenueStreams"
  | "sustainabilityImprovements"
  | "targetedSdgs"

const GENERATED_BMC_BLOCKS = [
  { key: "keyPartners", label: "Key Partners" },
  { key: "keyActivities", label: "Key Activities" },
  { key: "keyResources", label: "Key Resources" },
  { key: "valueProposition", label: "Value Proposition" },
  { key: "customerRelationships", label: "Customer Relationships" },
  { key: "channels", label: "Channels" },
  { key: "customerSegments", label: "Customer Segments" },
  { key: "costStructure", label: "Cost Structure" },
  { key: "revenueStreams", label: "Revenue Streams" },
]

const GENERATED_BMC_ALIASES: Record<string, keyof GeneratedBMC> = {
  "key partnerships": "keyPartners",
  "key partners": "keyPartners",
  "key activities": "keyActivities",
  "key resources": "keyResources",
  "value proposition": "valueProposition",
  "customer relationships": "customerRelationships",
  "channels": "channels",
  "customer segments": "customerSegments",
  "cost structure": "costStructure",
  "revenue streams": "revenueStreams",
}

const SUSTAINABLE_BMC_SECTIONS: Array<{ key: SustainableSectionKey; label: string }> = [
  { key: "keyPartnerships", label: "Key Partnerships" },
  { key: "keyActivities", label: "Key Activities" },
  { key: "keyResources", label: "Key Resources" },
  { key: "valueProposition", label: "Value Proposition" },
  { key: "customerRelationships", label: "Customer Relationships" },
  { key: "channels", label: "Channels" },
  { key: "customerSegments", label: "Customer Segments" },
  { key: "costStructure", label: "Cost Structure" },
  { key: "revenueStreams", label: "Revenue Streams" },
  { key: "sustainabilityImprovements", label: "Sustainability Improvements" },
  { key: "targetedSdgs", label: "Targeted SDGs" },
]

const SUSTAINABLE_ICON_MAP: Record<SustainableSectionKey, ElementType> = {
  keyPartnerships: Handshake,
  keyActivities: Cog,
  keyResources: Package,
  valueProposition: Heart,
  customerRelationships: MessageSquare,
  channels: Truck,
  customerSegments: Users,
  costStructure: DollarSign,
  revenueStreams: TrendingUp,
  sustainabilityImprovements: Leaf,
  targetedSdgs: Target,
}

const SUSTAINABLE_BMC_ALIASES: Record<string, SustainableSectionKey> = {
  "key partnerships": "keyPartnerships",
  "key partners": "keyPartnerships",
  "key activities": "keyActivities",
  "key resources": "keyResources",
  "value proposition": "valueProposition",
  "customer relationships": "customerRelationships",
  "channels": "channels",
  "customer segments": "customerSegments",
  "cost structure": "costStructure",
  "revenue streams": "revenueStreams",
  "sustainability improvements": "sustainabilityImprovements",
  "targeted sdgs": "targetedSdgs",
  "target sdgs": "targetedSdgs",
}

function parseGeneratedBmcText(text: string) {
  const parsed: Record<keyof GeneratedBMC, string[]> = {
    keyPartners: [],
    keyActivities: [],
    keyResources: [],
    valueProposition: [],
    customerRelationships: [],
    channels: [],
    customerSegments: [],
    costStructure: [],
    revenueStreams: [],
  }

  let currentKey: keyof GeneratedBMC | null = null
  const lines = text
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => line.trim())

  const resolveHeading = (raw: string) => {
    const cleaned = raw
      .replace(/^#{1,6}\s*/, "")
      .replace(/^\d+\.?\s*/, "")
      .replace(/\*\*/g, "")
      .replace(/[:\-]\s*$/, "")
      .trim()
      .toLowerCase()

    return GENERATED_BMC_ALIASES[cleaned] || null
  }

  for (const line of lines) {
    if (!line) continue

    const inlineMatch = line.match(/^([^:]+):\s*(.+)$/)
    if (inlineMatch) {
      const inlineKey = resolveHeading(inlineMatch[1])
      if (inlineKey) {
        currentKey = inlineKey
        const inlineValue = inlineMatch[2].trim()
        if (inlineValue && !/^[-_\s]+$/.test(inlineValue)) {
          parsed[currentKey].push(inlineValue.replace(/^[-*•]\s*/, ""))
        }
        continue
      }
    }

    const headingMatch = line.match(/^#{1,6}\s*(.+)$/) || line.match(/^\*\*(.+?)\*\*$/) || line.match(/^\d+\.?\s+(.+)$/)
    if (headingMatch) {
      const matchedKey = resolveHeading(headingMatch[1])
      if (matchedKey) {
        currentKey = matchedKey
      }
      continue
    }

    const cleanedLine = line.replace(/^[\-*•]\s*/, "").replace(/\*\*/g, "").trim()
    if (!cleanedLine) continue

    if (/^[-_\s]+$/.test(cleanedLine)) continue

    if (currentKey) {
      parsed[currentKey].push(cleanedLine)
    }
  }

  return parsed
}

function parseSustainableBmcText(text: string) {
  const parsed: Record<SustainableSectionKey, string[]> = {
    keyPartnerships: [],
    keyActivities: [],
    keyResources: [],
    valueProposition: [],
    customerRelationships: [],
    channels: [],
    customerSegments: [],
    costStructure: [],
    revenueStreams: [],
    sustainabilityImprovements: [],
    targetedSdgs: [],
  }

  let currentKey: SustainableSectionKey | null = null
  const lines = text
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => line.trim())

  const resolveHeading = (raw: string) => {
    const cleaned = raw
      .replace(/^#{1,6}\s*/, "")
      .replace(/^\d+\.?\s*/, "")
      .replace(/\*\*/g, "")
      .replace(/[:\-]\s*$/, "")
      .trim()
      .toLowerCase()

    return SUSTAINABLE_BMC_ALIASES[cleaned] || null
  }

  for (const line of lines) {
    if (!line) continue

    const inlineMatch = line.match(/^([^:]+):\s*(.+)$/)
    if (inlineMatch) {
      const inlineKey = resolveHeading(inlineMatch[1])
      if (inlineKey) {
        currentKey = inlineKey
        const inlineValue = inlineMatch[2].trim()
        if (inlineValue && !/^[-_\s]+$/.test(inlineValue)) {
          parsed[currentKey].push(inlineValue.replace(/^[-*•]\s*/, ""))
        }
        continue
      }
    }

    const headingMatch = line.match(/^#{1,6}\s*(.+)$/) || line.match(/^\*\*(.+?)\*\*$/) || line.match(/^\d+\.?\s+(.+)$/)
    if (headingMatch) {
      const matchedKey = resolveHeading(headingMatch[1])
      if (matchedKey) {
        currentKey = matchedKey
      }
      continue
    }

    const cleanedLine = line.replace(/^[\-*•]\s*/, "").replace(/\*\*/g, "").trim()
    if (!cleanedLine) continue

    if (/^[-_\s]+$/.test(cleanedLine)) continue

    if (currentKey) {
      parsed[currentKey].push(cleanedLine)
    }
  }

  return parsed
}

function buildGeneratedBmcFromText(text: string): GeneratedBMC {
  const parsed = parseGeneratedBmcText(text)

  return {
    keyPartners: parsed.keyPartners.join("\n"),
    keyActivities: parsed.keyActivities.join("\n"),
    keyResources: parsed.keyResources.join("\n"),
    valueProposition: parsed.valueProposition.join("\n"),
    customerRelationships: parsed.customerRelationships.join("\n"),
    channels: parsed.channels.join("\n"),
    customerSegments: parsed.customerSegments.join("\n"),
    costStructure: parsed.costStructure.join("\n"),
    revenueStreams: parsed.revenueStreams.join("\n"),
  }
}

function toBackendBmcJson(bmc: GeneratedBMC) {
  const toList = (value: string) =>
    value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((text) => ({ text }))

  return {
    key_partnerships: toList(bmc.keyPartners),
    key_activities: toList(bmc.keyActivities),
    key_resources: toList(bmc.keyResources),
    value_proposition: toList(bmc.valueProposition),
    customer_relationships: toList(bmc.customerRelationships),
    channels: toList(bmc.channels),
    customer_segments: toList(bmc.customerSegments),
    cost_structure: toList(bmc.costStructure),
    revenue_streams: toList(bmc.revenueStreams),
  }
}

export default function BMCGenerationPage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)

  const [pipeline, setPipeline] = useState<PipelineState>({
    currentStep: "upload",
    isProcessing: false,
    isComplete: false,
  })

  const [documentType, setDocumentType] = useState<DocumentType>(null)
  const [extractedText, setExtractedText] = useState<string | null>(null)
  const [classificationResults, setClassificationResults] = useState<Record<string, string[]> | null>(null)
  const [generatedBMC, setGeneratedBMC] = useState<GeneratedBMC | null>(null)
  const [editedBMC, setEditedBMC] = useState<GeneratedBMC | null>(null)
  const [generatedBmcText, setGeneratedBmcText] = useState<string>("")
  const [sustainableBmcText, setSustainableBmcText] = useState<string>("")
  const [isSustainableLoading, setIsSustainableLoading] = useState(false)
  const [sdgPredictions, setSdgPredictions] = useState<SdgPrediction[]>([])
  const [ragContext, setRagContext] = useState<RagChunk[]>([])
  const [sustainableBlocks, setSustainableBlocks] = useState<Record<SustainableSectionKey, string> | null>(null)

  const handleFileUpload = useCallback((uploadedFile: File) => {
    setFile(uploadedFile)
    setPreview(URL.createObjectURL(uploadedFile))
    startPipeline(uploadedFile)
  }, [])

  const startPipeline = async (fileToClassify: File) => {
    if (!fileToClassify) return

    setPipeline({
      currentStep: "classify-document",
      isProcessing: true,
      isComplete: false,
    })

    try {
      // Step 1: Classify Document Type - REAL API CALL
      console.log("📤 Step 1: Sending image to document classifier...")
      console.log("File:", fileToClassify.name, fileToClassify.size, "bytes")
      const formData = new FormData()
      formData.append("file", fileToClassify)

      const classifyResponse = await fetch("http://localhost:5000/api/predict-document-type", {
        method: "POST",
        credentials: "include",
        body: formData,
      })

      if (!classifyResponse.ok) {
        throw new Error(`Classification failed: ${classifyResponse.status}`)
      }

      const classifyResult = await classifyResponse.json()
      console.log("✓ Classification result:", classifyResult)

      const documentTypeResult: DocumentType = classifyResult.document_type as DocumentType
      setDocumentType(documentTypeResult)

      setPipeline({
        currentStep: "process-bmc",
        isProcessing: true,
        isComplete: false,
      })

      // Step 2: Extract Text - REAL API CALL
      console.log("📄 Step 2: Extracting text from document...")
      
      // Auto-select OCR method based on document type
      const selectedDocType = documentTypeResult || "auto";
      const ocrMethod = selectedDocType === "handwritten" ? "trocr" : "easyocr";
      console.log(`   Using ${ocrMethod.toUpperCase()} for ${selectedDocType} document`)
      
      const processFormData = new FormData();
      processFormData.append("file", fileToClassify);
      processFormData.append("document_type", selectedDocType);
      processFormData.append("ocr_method", ocrMethod);
      processFormData.append("confidence_threshold", "0.5");
      processFormData.append("complete", "true")

      const processResponse = await fetch("http://localhost:5000/api/process-bmc", {
        method: "POST",
        credentials: "include",
        body: processFormData,
      })

      if (!processResponse.ok) {
        throw new Error(`BMC processing failed: ${processResponse.status}`)
      }

      const processResult = await processResponse.json()
      console.log("PROCESS RESULT:", processResult)
      console.log("Classification mode:", processResult.classification_mode)
      console.log("YOLO detections:", processResult.yolo_detections_count)
      console.log("LLM output:", processResult.llm_output)

      setExtractedText(processResult.extracted_text || "")

      const bmcCanvas = processResult.bmc_canvas || {}

      const classificationMap: Record<string, string[]> = {
        keyPartners: (bmcCanvas.key_partnerships || []).map((x: { text?: string }) => x.text || ""),
        keyActivities: (bmcCanvas.key_activities || []).map((x: { text?: string }) => x.text || ""),
        keyResources: (bmcCanvas.key_resources || []).map((x: { text?: string }) => x.text || ""),
        valueProposition: (bmcCanvas.value_proposition || []).map((x: { text?: string }) => x.text || ""),
        customerRelationships: (bmcCanvas.customer_relationships || []).map((x: { text?: string }) => x.text || ""),
        channels: (bmcCanvas.channels || []).map((x: { text?: string }) => x.text || ""),
        customerSegments: (bmcCanvas.customer_segments || []).map((x: { text?: string }) => x.text || ""),
        costStructure: (bmcCanvas.cost_structure || []).map((x: { text?: string }) => x.text || ""),
        revenueStreams: (bmcCanvas.revenue_streams || []).map((x: { text?: string }) => x.text || ""),
        other: (bmcCanvas.other || []).map((x: { text?: string }) => x.text || ""),
      }
      setClassificationResults(classificationMap)

      const llmText = processResult.llm_output || ""
      setGeneratedBmcText(llmText)

      const parsedGeneratedBMC = buildGeneratedBmcFromText(llmText)
      setGeneratedBMC(parsedGeneratedBMC)
      setEditedBMC(parsedGeneratedBMC)

      setPipeline({
        currentStep: "completed",
        isProcessing: false,
        isComplete: true,
      })
      console.log("✅ Pipeline complete!")
    } catch (error) {
      console.error("❌ Pipeline error:", error)
      if (error instanceof Error) {
        console.error("Error details:", error.message)
      }
      setPipeline({
        currentStep: pipeline.currentStep,
        isProcessing: false,
        isComplete: false,
      })
    }
  }

  const handleBMCChange = (field: keyof GeneratedBMC, value: string) => {
    setEditedBMC((prev) => (prev ? { ...prev, [field]: value } : null))
  }

  const parsedGeneratedBmc = generatedBmcText ? parseGeneratedBmcText(generatedBmcText) : null
  const parsedSustainableBmc = sustainableBmcText ? parseSustainableBmcText(sustainableBmcText) : null

  const handleRegenerate = async () => {
    if (file) {
      setDocumentType(null)
      setExtractedText(null)
      setClassificationResults(null)
      setGeneratedBMC(null)
      setEditedBMC(null)
      setGeneratedBmcText("")
      setSustainableBmcText("")
      setSustainableBlocks(null)
      setSdgPredictions([])
      setRagContext([])
      await startPipeline(file)
      return
    }

    setDocumentType(null)
    setExtractedText(null)
    setClassificationResults(null)
    setGeneratedBMC(null)
    setEditedBMC(null)
    setGeneratedBmcText("")
    setSustainableBmcText("")
    setSustainableBlocks(null)
    setSdgPredictions([])
    setRagContext([])
    setPipeline({
      currentStep: "upload",
      isProcessing: false,
      isComplete: false,
    })
  }

  const handleGenerateSustainable = async () => {
    if (!editedBMC) return
    setIsSustainableLoading(true)
    try {
      const payload = {
        bmc_json: toBackendBmcJson(editedBMC),
      }

      const response = await fetch("http://localhost:5000/api/generate-sustainable-bmc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error(`Sustainable BMC failed: ${response.status}`)
      }

      const data = await response.json()
      setSustainableBmcText(data.sustainable_bmc || "")
      const parsed = parseSustainableBmcText(data.sustainable_bmc || "")
      setSustainableBlocks({
        keyPartnerships: parsed.keyPartnerships.join("\n"),
        keyActivities: parsed.keyActivities.join("\n"),
        keyResources: parsed.keyResources.join("\n"),
        valueProposition: parsed.valueProposition.join("\n"),
        customerRelationships: parsed.customerRelationships.join("\n"),
        channels: parsed.channels.join("\n"),
        customerSegments: parsed.customerSegments.join("\n"),
        costStructure: parsed.costStructure.join("\n"),
        revenueStreams: parsed.revenueStreams.join("\n"),
        sustainabilityImprovements: parsed.sustainabilityImprovements.join("\n"),
        targetedSdgs: parsed.targetedSdgs.join("\n"),
      })
      setSdgPredictions(Array.isArray(data.sdg_predictions) ? data.sdg_predictions : [])
      setRagContext(Array.isArray(data.rag_context) ? data.rag_context : [])
    } catch (error) {
      console.error("❌ Sustainable BMC error:", error)
    } finally {
      setIsSustainableLoading(false)
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

          <section className="pt-32 pb-16 px-4">
            <div className="max-w-7xl mx-auto">
              <div className="mb-6">
                <button
                  onClick={() => router.push("/bmc")}
                  className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/5 px-4 py-2 text-sm font-medium text-white/90 backdrop-blur-md transition-all hover:bg-white/10 hover:border-white/40"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to BMC Evaluate
                </button>
              </div>

              {/* Header */}
              <div className="text-center mb-12">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm font-medium mb-6">
                  <span className="inline-block w-2 h-2 bg-purple-400 rounded-full mr-2 animate-pulse"></span>
                  BMC AI Generation
                </div>
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
                  Generate Business Model Canvas with{" "}
                  <span className="bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
                    AI
                  </span>
                </h1>
                <p className="text-lg text-white/70 max-w-2xl mx-auto">
                  Upload a BMC image, handwritten notes, or document. Our AI pipeline will analyze, extract, classify,
                  and generate a complete Business Model Canvas for you.
                </p>
              </div>

              {/* Main Content */}
              <div className="space-y-8">
                {/* Upload Section */}
                {pipeline.currentStep === "upload" && !file && (
                  <UploadSection onFileUpload={handleFileUpload} />
                )}

                {/* File Preview + Pipeline */}
                {file && (
                  <div className="grid lg:grid-cols-3 gap-8">
                    {/* Left: File Preview */}
                    <div className="lg:col-span-1">
                      <div className="sticky top-32 space-y-4">
                        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4 overflow-hidden">
                          {preview && (
                            <img
                              src={preview}
                              alt="Uploaded document"
                              className="w-full h-auto rounded-lg object-contain max-h-96 bg-black/20"
                            />
                          )}
                        </div>
                        {file && (
                          <p className="text-white/50 text-xs text-center truncate">
                            {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Right: Pipeline */}
                    <div className="lg:col-span-2 space-y-6">
                      {/* Progress Section */}
                      <ProgressSection currentStep={pipeline.currentStep} isProcessing={pipeline.isProcessing} />

                      {/* Document Type Result */}
                      {documentType && (
                        <DocumentTypeCard documentType={documentType} />
                      )}

                      {/* Text Preview */}
                      {extractedText && (
                        <TextPreview text={extractedText} />
                      )}

                      {/* Classification Results */}
                      {classificationResults && (
                        <ClassificationResults results={classificationResults} />
                      )}

                    </div>
                  </div>
                )}

                {/* Generated BMC Canvas */}
                {generatedBMC && editedBMC && pipeline.isComplete && (
                  <div className="space-y-6">
                    <BMCCanvas bmc={editedBMC} onBMCChange={handleBMCChange} />

                    {/* Export Controls */}
                    <ExportControls
                      bmc={editedBMC}
                      onRegenerate={handleRegenerate}
                      onGenerateSustainable={handleGenerateSustainable}
                      sustainableLoading={isSustainableLoading}
                      sustainableText={sustainableBmcText}
                      sdgPredictions={sdgPredictions}
                      ragContext={ragContext}
                      sustainableBlocks={sustainableBlocks}
                      formatSdgLabel={formatSdgLabel}
                    />

                    {sustainableBmcText && (
                      <div className="relative overflow-hidden rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-slate-950/80 via-emerald-950/20 to-black/90 p-6 backdrop-blur-xl shadow-[0_0_35px_rgba(34,197,94,0.12)]">
                        <div className="pointer-events-none absolute -right-20 -top-16 h-52 w-52 rounded-full bg-emerald-500/12 blur-3xl" />
                        <div className="pointer-events-none absolute bottom-0 left-0 h-40 w-40 rounded-full bg-teal-400/10 blur-2xl" />
                        <div className="pointer-events-none absolute right-10 top-10 h-2 w-2 rounded-full bg-emerald-300/50 shadow-[0_0_16px_rgba(34,197,94,0.6)]" />
                        <div className="mb-5 flex items-center justify-between">
                          <div>
                            <h2 className="text-xl font-semibold text-emerald-100">Sustainable Business Model Canvas</h2>
                            <p className="text-sm text-emerald-100/60">
                              Sustainability-focused refinement based on SDGs and retrieved context
                            </p>
                          </div>
                          <div className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-100 ring-1 ring-emerald-400/20">
                            Sustainable
                          </div>
                        </div>

                        <div className="mb-6 grid gap-4 lg:grid-cols-3">
                          <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-4 shadow-[0_0_20px_rgba(34,197,94,0.12)]">
                            <div className="mb-3 flex items-center gap-2 text-emerald-100">
                              <Target className="h-4 w-4" />
                              <h3 className="text-sm font-semibold uppercase tracking-wide">Predicted SDGs</h3>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {sdgPredictions.length > 0 ? (
                                sdgPredictions.map((sdg) => (
                                  <span
                                    key={sdg.sdg}
                                    className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-100/90"
                                  >
                                    {formatSdgLabel(sdg.sdg)}
                                  </span>
                                ))
                              ) : (
                                <span className="text-xs text-emerald-100/60">No SDG predictions available.</span>
                              )}
                            </div>
                          </div>

                          <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-4 shadow-[0_0_20px_rgba(34,197,94,0.12)]">
                            <div className="mb-3 flex items-center gap-2 text-emerald-100">
                              <TrendingUp className="h-4 w-4" />
                              <h3 className="text-sm font-semibold uppercase tracking-wide">Green Impact</h3>
                            </div>
                            <div className="space-y-2 text-sm text-emerald-100/80">
                              <p className="flex items-center gap-2">
                                <Leaf className="h-4 w-4 text-emerald-200" />
                                Focused on {sdgPredictions.length || "key"} sustainability goal(s)
                              </p>
                              <p className="flex items-center gap-2">
                                <Recycle className="h-4 w-4 text-emerald-200" />
                                {ragContext.length || 0} context signals guiding eco improvements
                              </p>
                            </div>
                          </div>

                          <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-4 shadow-[0_0_20px_rgba(34,197,94,0.12)]">
                            <div className="mb-3 flex items-center gap-2 text-emerald-100">
                              <Sparkles className="h-4 w-4" />
                              <h3 className="text-sm font-semibold uppercase tracking-wide">Eco-friendly Recommendations</h3>
                            </div>
                            <div className="space-y-2 text-sm text-emerald-100/80">
                              {(ragContext.slice(0, 3).map((chunk, index) => (
                                <p key={`rag-${index}`} className="rounded-lg bg-emerald-500/10 px-3 py-2">
                                  {chunk.text || "Recommendation insight"}
                                </p>
                              ))) || (
                                <p className="text-emerald-100/60">No recommendations available.</p>
                              )}
                            </div>
                          </div>
                        </div>

                        {sustainableBlocks ? (
                          <div className="grid gap-4 md:grid-cols-2">
                            {SUSTAINABLE_BMC_SECTIONS.map((section, index) => {
                              const Icon = SUSTAINABLE_ICON_MAP[section.key]
                              return (
                                <EditableBMCBlock
                                  key={section.key}
                                  title={`${index + 1}. ${section.label}`}
                                  content={sustainableBlocks[section.key] || ""}
                                  icon={Icon}
                                  variant="sustainable"
                                  onChange={(value) =>
                                    setSustainableBlocks((prev) =>
                                      prev ? { ...prev, [section.key]: value } : prev
                                    )
                                  }
                                />
                              )
                            })}
                          </div>
                        ) : (
                          <div className="whitespace-pre-wrap leading-7 text-emerald-100/80">{sustainableBmcText}</div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </section>

          <Footer />
        </div>
      </main>
    </div>
  )
}

import { Card, CardContent } from "@/components/ui/card"
import { CheckCircle, FileText, PenTool, Grid3x3 } from "lucide-react"

type DocumentType = "bmc" | "handwritten" | "typed"

interface DocumentTypeCardProps {
  documentType: DocumentType
}

const documentTypeInfo = {
  bmc: {
    label: "Business Model Canvas",
    description: "Detected a BMC image with structured blocks",
    icon: Grid3x3,
    color: "from-blue-500 to-cyan-500",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    textColor: "text-blue-300",
  },
  handwritten: {
    label: "Handwritten Notes",
    description: "Detected handwritten content",
    icon: PenTool,
    color: "from-pink-500 to-rose-500",
    bgColor: "bg-pink-500/10",
    borderColor: "border-pink-500/30",
    textColor: "text-pink-300",
  },
  typed: {
    label: "Typed Document",
    description: "Detected typed or printed text",
    icon: FileText,
    color: "from-green-500 to-emerald-500",
    bgColor: "bg-green-500/10",
    borderColor: "border-green-500/30",
    textColor: "text-green-300",
  },
}

export default function DocumentTypeCard({ documentType }: DocumentTypeCardProps) {
  const info = documentTypeInfo[documentType]
  
  // Safety check for undefined document type
  if (!info) {
    console.error(`Unknown document type: ${documentType}`)
    return (
      <Card className="bg-white/5 backdrop-blur-xl border-white/10 border border-red-500/30">
        <CardContent className="p-6">
          <div className="text-red-400">
            <p className="font-semibold">Error: Unknown Document Type</p>
            <p className="text-sm text-red-300/60">{documentType}</p>
          </div>
        </CardContent>
      </Card>
    )
  }
  
  const IconComponent = info.icon

  return (
    <Card className={`bg-white/5 backdrop-blur-xl border-white/10 ${info.bgColor} border ${info.borderColor}`}>
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div className={`p-3 rounded-lg bg-gradient-to-br ${info.color} bg-opacity-20`}>
            <IconComponent className={`w-6 h-6 ${info.textColor}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-white font-semibold">{info.label}</h3>
              <CheckCircle className={`w-4 h-4 ${info.textColor}`} />
            </div>
            <p className="text-white/60 text-sm">{info.description}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

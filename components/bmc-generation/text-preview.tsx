import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Copy, Check } from "lucide-react"
import { useState } from "react"

interface TextPreviewProps {
  text: string
}

export default function TextPreview({ text }: TextPreviewProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card className="bg-white/5 backdrop-blur-xl border-white/10">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-white">Extracted Text</CardTitle>
            <CardDescription className="text-white/60">Raw text extracted from the document</CardDescription>
          </div>
          <button
            onClick={handleCopy}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/10"
            title="Copy to clipboard"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4 text-white/60" />
            )}
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="bg-black/30 rounded-lg p-4 border border-white/5 max-h-64 overflow-y-auto">
          <p className="text-white/70 text-sm whitespace-pre-wrap font-mono leading-relaxed">{text}</p>
        </div>
        <p className="text-white/40 text-xs mt-3">This text will be classified into BMC blocks in the next step</p>
      </CardContent>
    </Card>
  )
}

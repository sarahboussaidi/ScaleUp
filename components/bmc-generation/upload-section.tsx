import { useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, Image as ImageIcon } from "lucide-react"

interface UploadSectionProps {
  onFileUpload: (file: File) => void
}

export default function UploadSection({ onFileUpload }: UploadSectionProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile && droppedFile.type.startsWith("image/")) {
        onFileUpload(droppedFile)
      }
    },
    [onFileUpload]
  )

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile && selectedFile.type.startsWith("image/")) {
      onFileUpload(selectedFile)
    }
  }

  return (
    <Card className="bg-white/5 backdrop-blur-xl border-white/10 max-w-3xl mx-auto">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Upload className="w-5 h-5 text-purple-400" />
          Upload Your Document
        </CardTitle>
        <CardDescription className="text-white/60">
          Upload a Business Model Canvas image, handwritten notes, or typed document
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
            isDragging ? "border-purple-400 bg-purple-500/20" : "border-white/20 hover:border-purple-400/50 hover:bg-white/5"
          }`}
        >
          <ImageIcon className="w-16 h-16 text-purple-400 mx-auto mb-4 opacity-80" />
          <p className="text-white/80 text-lg mb-2 font-medium">Drag and drop your document here</p>
          <p className="text-white/60 mb-6">or</p>
          <label className="cursor-pointer inline-block">
            <input type="file" accept="image/*" onChange={handleFileSelect} className="hidden" />
            <span className="inline-flex items-center px-8 py-3 bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white rounded-full font-semibold transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-purple-500/50">
              Choose File
            </span>
          </label>
          <p className="text-white/40 text-sm mt-6">Supported formats: JPG, PNG, GIF, WebP, PDF</p>
        </div>
      </CardContent>
    </Card>
  )
}

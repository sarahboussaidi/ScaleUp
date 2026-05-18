import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Edit2, Save, X } from "lucide-react"

interface EditableBMCBlockProps {
  title: string
  content: string
  icon: React.ElementType
  onChange: (value: string) => void
  variant?: "default" | "sustainable"
}

export default function EditableBMCBlock({
  title,
  content,
  icon: IconComponent,
  onChange,
  variant = "default",
}: EditableBMCBlockProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(content)

  const isSustainable = variant === "sustainable"
  const cardClasses = isSustainable
    ? "bg-emerald-950/20 border-emerald-500/20 hover:border-emerald-400/40 shadow-[0_0_22px_rgba(34,197,94,0.12)]"
    : "bg-white/5 border-white/10 hover:border-white/20"
  const iconClasses = isSustainable ? "text-emerald-200" : "text-purple-400"
  const textClasses = isSustainable ? "text-emerald-100/70" : "text-white/70"
  const textareaClasses = isSustainable
    ? "bg-emerald-950/50 border-emerald-500/20 text-emerald-50 placeholder:text-emerald-100/40"
    : "bg-black/30 border-white/10 text-white placeholder:text-white/40"

  const handleSave = () => {
    onChange(editValue)
    setIsEditing(false)
  }

  const handleCancel = () => {
    setEditValue(content)
    setIsEditing(false)
  }

  return (
    <Card
      className={`backdrop-blur-xl transition-all duration-300 h-[240px] flex flex-col ${cardClasses}`}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <IconComponent className={`w-5 h-5 ${iconClasses}`} />
            <CardTitle className="text-white text-sm">{title}</CardTitle>
          </div>
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className={`p-1.5 rounded-lg transition-colors ${
                isSustainable ? "hover:bg-emerald-500/10" : "hover:bg-white/10"
              }`}
              title="Edit block"
            >
              <Edit2 className={`w-4 h-4 ${isSustainable ? "text-emerald-100/70 hover:text-emerald-100" : "text-white/60 hover:text-white"}`} />
            </button>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col overflow-y-auto">
        {isEditing ? (
          <div className="space-y-3 flex-1 flex flex-col">
            <Textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className={`flex-1 resize-none min-h-[150px] ${textareaClasses}`}
              placeholder="Edit content..."
            />
            <div className="flex gap-2">
              <Button
                onClick={handleSave}
                size="sm"
                className={`flex-1 text-white ${isSustainable ? "bg-emerald-600/90 hover:bg-emerald-600" : "bg-green-600 hover:bg-green-700"}`}
              >
                <Save className="w-4 h-4 mr-1" />
                Save
              </Button>
              <Button
                onClick={handleCancel}
                size="sm"
                variant="outline"
                className={`flex-1 text-white ${isSustainable ? "bg-emerald-500/10 border-emerald-500/20 hover:bg-emerald-500/20" : "bg-white/5 border-white/10 hover:bg-white/10"}`}
              >
                <X className="w-4 h-4 mr-1" />
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <p className={`text-sm whitespace-pre-wrap leading-relaxed ${textClasses}`}>{content}</p>
        )}
      </CardContent>
    </Card>
  )
}

import { Card, CardContent } from "@/components/ui/card"
import { Check, Loader2 } from "lucide-react"

type PipelineStep = "upload" | "classify-document" | "process-bmc" | "completed"

interface ProgressSectionProps {
  currentStep: PipelineStep
  isProcessing: boolean
}

const steps: { id: Exclude<PipelineStep, "upload" | "completed">; label: string; description: string }[] = [
  { id: "classify-document", label: "Classify Document", description: "Identifying document type" },
  { id: "process-bmc", label: "Process BMC", description: "Extracting, classifying, and generating BMC" },
]

export default function ProgressSection({ currentStep, isProcessing }: ProgressSectionProps) {
  const currentStepIndex = currentStep === "completed" ? steps.length : steps.findIndex((s) => s.id === currentStep)

  return (
    <Card className="bg-white/5 backdrop-blur-xl border-white/10">
      <CardContent className="p-6">
        <div className="space-y-6">
          {steps.map((step, idx) => {
            const isCompleted = idx < currentStepIndex
            const isCurrent = idx === currentStepIndex
            const isUpcoming = idx > currentStepIndex

            return (
              <div key={step.id} className="flex items-start gap-4">
                {/* Step Indicator */}
                <div className="flex flex-col items-center gap-2 pt-1">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all duration-300 ${
                      isCompleted
                        ? "bg-green-500/20 border border-green-500/50 text-green-400"
                        : isCurrent
                          ? "bg-purple-500/20 border border-purple-500 text-purple-400 animate-pulse"
                          : "bg-white/5 border border-white/10 text-white/60"
                    }`}
                  >
                    {isCompleted ? (
                      <Check className="w-5 h-5" />
                    ) : isCurrent ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      idx + 1
                    )}
                  </div>
                  {idx < steps.length - 1 && (
                    <div
                      className={`w-0.5 h-12 transition-all duration-300 ${
                        isCompleted ? "bg-green-500/50" : isCurrent ? "bg-purple-500/50" : "bg-white/10"
                      }`}
                    />
                  )}
                </div>

                {/* Step Info */}
                <div className="flex-1 pt-1">
                  <h4
                    className={`font-semibold text-sm transition-colors duration-300 ${
                      isCompleted || isCurrent ? "text-white" : "text-white/50"
                    }`}
                  >
                    {step.label}
                  </h4>
                  <p className="text-white/40 text-xs mt-1">{step.description}</p>
                </div>

                {/* Status Badge */}
                {isCurrent && isProcessing && (
                  <div className="px-3 py-1 bg-purple-500/20 border border-purple-500/30 rounded-full">
                    <p className="text-purple-300 text-xs font-medium animate-pulse">Processing...</p>
                  </div>
                )}
                {isCompleted && (
                  <div className="px-3 py-1 bg-green-500/20 border border-green-500/30 rounded-full">
                    <p className="text-green-300 text-xs font-medium">Complete</p>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

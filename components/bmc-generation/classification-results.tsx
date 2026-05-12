import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Handshake,
  Cog,
  Package,
  Heart,
  MessageSquare,
  Truck,
  Users,
  DollarSign,
  TrendingUp,
  AlertCircle,
} from "lucide-react"

interface ClassificationResultsProps {
  results: Record<string, string[]>
}

const blockIcons: Record<string, React.ElementType> = {
  keyPartners: Handshake,
  keyActivities: Cog,
  keyResources: Package,
  valueProposition: Heart,
  customerRelationships: MessageSquare,
  channels: Truck,
  customerSegments: Users,
  costStructure: DollarSign,
  revenueStreams: TrendingUp,
  other: AlertCircle,
}

const blockLabels: Record<string, string> = {
  keyPartners: "Key Partners",
  keyActivities: "Key Activities",
  keyResources: "Key Resources",
  valueProposition: "Value Proposition",
  customerRelationships: "Customer Relationships",
  channels: "Channels",
  customerSegments: "Customer Segments",
  costStructure: "Cost Structure",
  revenueStreams: "Revenue Streams",
  other: "Other",
}

export default function ClassificationResults({ results }: ClassificationResultsProps) {
  return (
    <Card className="bg-white/5 backdrop-blur-xl border-white/10">
      <CardHeader>
        <CardTitle className="text-white">BMC Block Classification</CardTitle>
        <CardDescription className="text-white/60">
          Text extracted from the document has been classified into BMC blocks
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(results).map(([blockKey, items]) => {
            const IconComponent = blockIcons[blockKey] || Cog
            const label = blockLabels[blockKey] || blockKey
            const isOther = blockKey === "other"
            const badgeColor = isOther 
              ? "bg-orange-500/20 border border-orange-500/30 text-orange-200 hover:bg-orange-500/30"
              : "bg-purple-500/20 border border-purple-500/30 text-purple-200 hover:bg-purple-500/30"

            return (
              <div key={blockKey} className="bg-black/20 rounded-lg p-4 border border-white/5">
                <div className="flex items-center gap-2 mb-3">
                  <IconComponent className={`w-4 h-4 ${isOther ? "text-orange-400" : "text-purple-400"}`} />
                  <h4 className="font-semibold text-white text-sm">{label}</h4>
                </div>
                <div className="flex flex-wrap gap-2">
                  {items.length > 0 ? (
                    items.map((item, idx) => (
                      <Badge
                        key={idx}
                        className={`${badgeColor} max-w-full whitespace-normal break-words`}
                      >
                        {item}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-white/40 text-xs italic">No items classified</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

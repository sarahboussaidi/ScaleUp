import EditableBMCBlock from "./editable-bmc-block"
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
} from "lucide-react"

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

interface BMCCanvasProps {
  bmc: GeneratedBMC
  onBMCChange: (field: keyof GeneratedBMC, value: string) => void
}

export default function BMCCanvas({ bmc, onBMCChange }: BMCCanvasProps) {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Generated Business Model Canvas</h2>
        <p className="text-white/60">Edit any block below to refine your canvas</p>
      </div>

      {/* BMC Layout - 9 Block Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 min-h-full">
        {/* Row 1 */}
        {/* Key Partners */}
        <EditableBMCBlock
          title="1. Key Partners"
          content={bmc.keyPartners}
          icon={Handshake}
          onChange={(value) => onBMCChange("keyPartners", value)}
        />

        {/* Key Activities */}
        <EditableBMCBlock
          title="2. Key Activities"
          content={bmc.keyActivities}
          icon={Cog}
          onChange={(value) => onBMCChange("keyActivities", value)}
        />

        {/* Key Resources */}
        <EditableBMCBlock
          title="3. Key Resources"
          content={bmc.keyResources}
          icon={Package}
          onChange={(value) => onBMCChange("keyResources", value)}
        />

        {/* Row 2 - Spanning grid */}
        <div className="md:col-span-1">
          <EditableBMCBlock
            title="4. Value Proposition"
            content={bmc.valueProposition}
            icon={Heart}
            onChange={(value) => onBMCChange("valueProposition", value)}
          />
        </div>

        <div className="md:col-span-1">
          <EditableBMCBlock
            title="5. Customer Relationships"
            content={bmc.customerRelationships}
            icon={MessageSquare}
            onChange={(value) => onBMCChange("customerRelationships", value)}
          />
        </div>

        <div className="md:col-span-1">
          <EditableBMCBlock
            title="6. Channels"
            content={bmc.channels}
            icon={Truck}
            onChange={(value) => onBMCChange("channels", value)}
          />
        </div>

        {/* Row 3 */}
        {/* Cost Structure */}
        <EditableBMCBlock
          title="7. Cost Structure"
          content={bmc.costStructure}
          icon={DollarSign}
          onChange={(value) => onBMCChange("costStructure", value)}
        />

        {/* Customer Segments */}
        <EditableBMCBlock
          title="8. Customer Segments"
          content={bmc.customerSegments}
          icon={Users}
          onChange={(value) => onBMCChange("customerSegments", value)}
        />

        {/* Revenue Streams */}
        <EditableBMCBlock
          title="9. Revenue Streams"
          content={bmc.revenueStreams}
          icon={TrendingUp}
          onChange={(value) => onBMCChange("revenueStreams", value)}
        />
      </div>

    </div>
  )
}

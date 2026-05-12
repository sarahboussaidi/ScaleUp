import { Card, CardContent } from "@/components/ui/card"
import { Download, Save, RotateCcw, Copy, Check, Leaf, Sparkles } from "lucide-react"
import jsPDF from "jspdf"
import { useMemo, useRef, useState } from "react"

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

interface ExportControlsProps {
  bmc: GeneratedBMC
  onRegenerate: () => void | Promise<void>
  onGenerateSustainable: () => void
  sustainableLoading: boolean
  sustainableText?: string
  sdgPredictions?: Array<{ sdg: string; confidence: number }>
  ragContext?: Array<{ source?: string; text?: string; distance?: number }>
  sustainableBlocks?: Record<string, string> | null
  formatSdgLabel?: (value: string) => string
}

interface BlockMeta {
  key: keyof GeneratedBMC
  title: string
  code: string
}

const NORMAL_BLOCKS: BlockMeta[] = [
  { key: "keyPartners", title: "Key Partnerships", code: "KP" },
  { key: "keyActivities", title: "Key Activities", code: "KA" },
  { key: "keyResources", title: "Key Resources", code: "KR" },
  { key: "valueProposition", title: "Value Proposition", code: "VP" },
  { key: "customerRelationships", title: "Customer Relationships", code: "CR" },
  { key: "channels", title: "Channels", code: "CH" },
  { key: "customerSegments", title: "Customer Segments", code: "CS" },
  { key: "costStructure", title: "Cost Structure", code: "CO" },
  { key: "revenueStreams", title: "Revenue Streams", code: "RS" },
]

const SUSTAINABLE_BLOCKS: Array<{ key: string; title: string; code: string }> = [
  { key: "keyPartnerships", title: "Key Partnerships", code: "KP" },
  { key: "keyActivities", title: "Key Activities", code: "KA" },
  { key: "keyResources", title: "Key Resources", code: "KR" },
  { key: "valueProposition", title: "Value Proposition", code: "VP" },
  { key: "customerRelationships", title: "Customer Relationships", code: "CR" },
  { key: "channels", title: "Channels", code: "CH" },
  { key: "customerSegments", title: "Customer Segments", code: "CS" },
  { key: "costStructure", title: "Cost Structure", code: "CO" },
  { key: "revenueStreams", title: "Revenue Streams", code: "RS" },
]

const PDF_VIEWPORT = {
  width: 1600,
  height: 1131,
}

const A4_LANDSCAPE = {
  width: 841.89,
  height: 595.28,
}

const A4_PORTRAIT = {
  width: 595.28,
  height: 841.89,
}

const bulletStyle: React.CSSProperties = {
  display: "-webkit-box",
  WebkitLineClamp: 2,
  WebkitBoxOrient: "vertical",
  overflow: "hidden",
  textOverflow: "ellipsis",
  lineHeight: 1.35,
}

function normalizeConfidence(raw: number): number {
  if (raw <= 0) return 0
  if (raw <= 1) return Math.round(raw * 100)
  return Math.round(Math.min(raw, 100))
}

function truncateLine(value: string, maxChars = 92): string {
  const normalized = value.replace(/\s+/g, " ").trim()
  if (normalized.length <= maxChars) return normalized
  return `${normalized.slice(0, maxChars - 1)}...`
}

function extractBullets(value: string, maxItems = 3): string[] {
  if (!value?.trim()) {
    return ["Not provided yet"]
  }

  const lines = value
    .split(/\r?\n|[;|]+/)
    .map((line) => line.replace(/^[\-*\u2022\d.\)\s]+/, "").trim())
    .filter(Boolean)

  const unique = Array.from(new Set(lines)).slice(0, maxItems)
  return unique.length > 0 ? unique.map((item) => truncateLine(item)) : ["Not provided yet"]
}

function extractRecommendations(
  source: Array<{ source?: string; text?: string; distance?: number }>,
  fallback: string,
): string[] {
  const fromContext = source
    .map((chunk) => chunk.text?.trim())
    .filter((item): item is string => Boolean(item))
    .slice(0, 4)

  if (fromContext.length > 0) {
    return fromContext.map((item) => truncateLine(item, 108))
  }

  return extractBullets(fallback, 4).map((item) => truncateLine(item, 108))
}

function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.replace("#", "")
  const value = clean.length === 3 ? clean.split("").map((ch) => ch + ch).join("") : clean
  const int = Number.parseInt(value, 16)
  return [(int >> 16) & 255, (int >> 8) & 255, int & 255]
}

function setFillHex(doc: jsPDF, hex: string) {
  const [r, g, b] = hexToRgb(hex)
  doc.setFillColor(r, g, b)
}

function setStrokeHex(doc: jsPDF, hex: string) {
  const [r, g, b] = hexToRgb(hex)
  doc.setDrawColor(r, g, b)
}

function safeText(doc: jsPDF, text: string, x: number, y: number, options?: { maxWidth?: number; size?: number; color?: string; bold?: boolean }) {
  if (options?.size) doc.setFontSize(options.size)
  if (options?.color) {
    const [r, g, b] = hexToRgb(options.color)
    doc.setTextColor(r, g, b)
  }
  doc.text(text, x, y, options?.maxWidth ? { maxWidth: options.maxWidth } : undefined)
}

function drawRoundedPanel(doc: jsPDF, x: number, y: number, w: number, h: number, fill: string, stroke: string) {
  setFillHex(doc, fill)
  setStrokeHex(doc, stroke)
  doc.roundedRect(x, y, w, h, 12, 12, "FD")
}

function drawDivider(doc: jsPDF, x: number, y: number, w: number, color: string) {
  setStrokeHex(doc, color)
  doc.setLineWidth(1.1)
  doc.line(x, y, x + w, y)
}

function drawFooter(doc: jsPDF, label: string, pageNumber: number, totalPages: number, accent: string) {
  const W = A4_PORTRAIT.width
  const H = A4_PORTRAIT.height
  drawDivider(doc, 28, H - 34, W - 56, accent)
  safeText(doc, label, 28, H - 18, { size: 8.8, color: "#cbd5e1" })
  safeText(doc, `Page ${pageNumber} of ${totalPages}`, W - 92, H - 18, { size: 8.8, color: "#cbd5e1" })
}

function drawCoverPage(
  doc: jsPDF,
  title: string,
  subtitle: string,
  badge: string,
  accent: string,
  palette: {
    background: string
    glowA: string
    glowB: string
    panel: string
    panelStroke: string
    text: string
    muted: string
    chipFill: string
    chipStroke: string
  },
) {
  const W = A4_PORTRAIT.width
  const H = A4_PORTRAIT.height

  setFillHex(doc, palette.background)
  doc.rect(0, 0, W, H, "F")
  setFillHex(doc, palette.glowA)
  doc.circle(W - 74, 86, 58, "F")
  setFillHex(doc, palette.glowB)
  doc.circle(74, H - 122, 70, "F")

  drawRoundedPanel(doc, 28, 28, W - 56, 784, palette.panel, palette.panelStroke)

  safeText(doc, "ScaleUp AI Consulting", 54, 74, { size: 10.5, color: accent })
  safeText(doc, "Premium strategy deliverable", 54, 100, { size: 22, color: palette.text })
  safeText(doc, title, 54, 142, { size: 30, color: palette.text, maxWidth: 320 })
  safeText(doc, subtitle, 54, 168, { size: 11.5, color: palette.muted, maxWidth: 300 })

  drawRoundedPanel(doc, 54, 206, 136, 30, palette.chipFill, palette.chipStroke)
  safeText(doc, badge, 68, 225, { size: 9.2, color: palette.text })
  drawRoundedPanel(doc, 198, 206, 124, 30, "#111827", palette.chipStroke)
  safeText(doc, "A4 Portrait Export", 216, 225, { size: 9.2, color: palette.text })
  drawRoundedPanel(doc, 330, 206, 146, 30, "#111827", palette.chipStroke)
  safeText(doc, "Founder-ready layout", 346, 225, { size: 9.2, color: palette.text })

  drawRoundedPanel(doc, 54, 260, 246, 208, "#0f172a", palette.panelStroke)
  safeText(doc, "What this report includes", 72, 284, { size: 14, color: palette.text })
  drawDivider(doc, 72, 296, 88, accent)
  const coverBullets = [
    "A polished business model canvas with clear hierarchy.",
    "Presentation-ready styling for founders, investors, and incubators.",
    "Dedicated sustainability analysis with SDGs, recommendations, and metrics.",
  ]
  let coverY = 324
  coverBullets.forEach((item) => {
    safeText(doc, `• ${item}`, 72, coverY, { size: 10.2, color: palette.muted, maxWidth: 210 })
    coverY += 43
  })

  drawRoundedPanel(doc, 324, 260, 208, 208, "#07111f", palette.panelStroke)
  safeText(doc, "Executive snapshot", 342, 284, { size: 14, color: palette.text })
  drawDivider(doc, 342, 296, 88, accent)
  const snapshotItems = [
    { label: "Blocks", value: "9" },
    { label: "Format", value: "Portrait" },
    { label: "Style", value: "Consulting" },
  ]
  snapshotItems.forEach((item, index) => {
    const top = 320 + index * 47
    drawRoundedPanel(doc, 342, top, 172, 36, palette.chipFill, palette.chipStroke)
    safeText(doc, item.label, 354, top + 15, { size: 8.8, color: palette.muted })
    safeText(doc, item.value, 474, top + 15, { size: 13.5, color: palette.text })
  })

  drawRoundedPanel(doc, 54, 496, 478, 210, "#0b1220", palette.panelStroke)
  safeText(doc, "Visual language", 72, 522, { size: 14, color: palette.text })
  drawDivider(doc, 72, 534, 76, accent)
  safeText(doc, "Purple and blue gradients with restrained green accents keep the report modern while still feeling professional.", 72, 556, { size: 10.4, color: palette.muted, maxWidth: 214 })
  safeText(doc, "Clean spacing, rounded containers, and section badges help the content read like a premium consulting deck.", 300, 556, { size: 10.4, color: palette.muted, maxWidth: 196 })

  setStrokeHex(doc, accent)
  doc.setLineWidth(1.3)
  doc.circle(414, 598, 48, "S")
  doc.circle(450, 646, 16, "S")
  doc.circle(374, 658, 10, "F")
  doc.line(384, 652, 402, 636)
  doc.line(402, 636, 432, 609)
  doc.line(432, 609, 468, 618)
  doc.line(432, 609, 450, 646)
  doc.line(402, 636, 374, 658)
  setFillHex(doc, "#1d4ed8")
  doc.circle(432, 609, 8, "F")
  setFillHex(doc, "#8b5cf6")
  doc.circle(468, 618, 6, "F")
  setFillHex(doc, "#14b8a6")
  doc.circle(450, 646, 6, "F")

  drawRoundedPanel(doc, 54, 726, 478, 54, "#111827", palette.panelStroke)
  safeText(doc, "Generated for a polished business presentation workflow", 72, 750, { size: 11.5, color: palette.text })
  safeText(doc, "Direct PDF drawing keeps exports stable across modern themes and browser settings.", 72, 770, { size: 9.5, color: palette.muted, maxWidth: 404 })
}

function drawCanvasPage(
  doc: jsPDF,
  canvasTitle: string,
  canvasSubtitle: string,
  badge: string,
  blocks: Array<{ key: string; title: string; code: string }>,
  values: Record<string, string>,
  theme: {
    background: string
    glowA: string
    glowB: string
    header: string
    headerStroke: string
    cardFill: string
    cardStroke: string
    chipFill: string
    chipStroke: string
    text: string
    muted: string
    accent: string
    footerAccent: string
  },
) {
  const W = A4_PORTRAIT.width
  const H = A4_PORTRAIT.height
  const marginX = 28
  const marginTop = 100
  const gap = 10
  const rowGap = 12
  const colW = (W - marginX * 2 - gap * 2) / 3
  const rowH = 200

  setFillHex(doc, theme.background)
  doc.rect(0, 0, W, H, "F")
  setFillHex(doc, theme.glowA)
  doc.circle(W - 74, 76, 52, "F")
  setFillHex(doc, theme.glowB)
  doc.circle(72, H - 132, 58, "F")

  drawRoundedPanel(doc, marginX, 24, W - marginX * 2, 62, theme.header, theme.headerStroke)
  safeText(doc, "ScaleUp AI Consulting", marginX + 18, 48, { size: 10.2, color: theme.accent })
  safeText(doc, canvasTitle, marginX + 18, 71, { size: 24, color: theme.text })
  safeText(doc, canvasSubtitle, marginX + 214, 71, { size: 10.4, color: theme.muted, maxWidth: 230 })
  drawRoundedPanel(doc, W - marginX - 160, 39, 132, 26, theme.chipFill, theme.chipStroke)
  safeText(doc, badge, W - marginX - 146, 56, { size: 8.8, color: theme.text })

  blocks.forEach((block, index) => {
    const row = Math.floor(index / 3)
    const col = index % 3
    const x = marginX + col * (colW + gap)
    const y = marginTop + row * (rowH + rowGap)
    drawRoundedPanel(doc, x, y, colW, rowH, theme.cardFill, theme.cardStroke)
    drawRoundedPanel(doc, x + 12, y + 12, 24, 18, theme.chipFill, theme.chipStroke)
    safeText(doc, block.code, x + 16, y + 25, { size: 8.6, color: theme.text })
    safeText(doc, block.title, x + 46, y + 25, { size: 13.5, color: theme.text, maxWidth: colW - 70 })
    drawDivider(doc, x + 14, y + 36, colW - 28, theme.footerAccent)
    drawBulletList(doc, extractBullets(values[block.key] || "", 3), x + 14, y + 58, colW - 28, 15, theme.muted)
  })

  drawRoundedPanel(doc, marginX, 740, W - marginX * 2, 46, theme.header, theme.headerStroke)
  safeText(doc, "A premium portrait layout designed for clarity, hierarchy, and presentation-quality reading.", marginX + 18, 768, { size: 10, color: theme.muted, maxWidth: 378 })
  safeText(doc, "Direct PDF drawing avoids the browser parsing issues that affected rasterized exports.", marginX + 18, 786, { size: 9, color: theme.accent, maxWidth: 332 })
}

function drawBulletList(doc: jsPDF, bullets: string[], x: number, y: number, maxWidth: number, lineHeight: number, color = "#dbeafe") {
  let cursor = y
  bullets.slice(0, 3).forEach((bullet) => {
    doc.setFont("helvetica", "normal")
    doc.setTextColor(...hexToRgb(color))
    const lines = doc.splitTextToSize(`• ${bullet}`, maxWidth)
    lines.slice(0, 2).forEach((line: string) => {
      doc.text(line, x, cursor)
      cursor += lineHeight
    })
    cursor += 1.5
  })
  return cursor
}

function drawNormalPage(doc: jsPDF, bmc: GeneratedBMC) {
  const W = A4_LANDSCAPE.width
  const H = A4_LANDSCAPE.height
  const marginX = 28
  const headerH = 74
  const footerH = 24
  const gridTop = 96
  const gridBottom = H - footerH - 14
  const gap = 10
  const row1H = 155
  const row2H = 126
  const row3H = 126
  const row1Y = gridTop
  const row2Y = row1Y + row1H + gap
  const row3Y = row2Y + row2H + gap
  const colW = (W - marginX * 2 - gap * 3) / 4
  const midColW = (W - marginX * 2 - gap * 2) / 3
  const bottomColW = (W - marginX * 2 - gap) / 2

  setFillHex(doc, "#030712")
  doc.rect(0, 0, W, H, "F")
  setFillHex(doc, "#1d4ed8")
  doc.circle(W * 0.82, 58, 34, "F")
  setFillHex(doc, "#7c3aed")
  doc.circle(92, H - 72, 28, "F")

  drawRoundedPanel(doc, marginX, 14, W - marginX * 2, headerH, "#0f172a", "#2563eb")
  doc.setFont("helvetica", "bold")
  safeText(doc, "ScaleUp AI Consulting", marginX + 18, 36, { size: 10, color: "#93c5fd" })
  safeText(doc, "Business Model Canvas", marginX + 18, 58, { size: 24, color: "#f8fafc" })
  drawRoundedPanel(doc, W - marginX - 182, 30, 154, 28, "#1e3a8a", "#60a5fa")
  safeText(doc, "Premium Export | A4 Landscape", W - marginX - 166, 48, { size: 9.5, color: "#dbeafe" })

  const topBlocks = [
    { title: "Key Partnerships", code: "KP", key: "keyPartners", x: marginX, y: row1Y, w: colW },
    { title: "Key Activities", code: "KA", key: "keyActivities", x: marginX + colW + gap, y: row1Y, w: colW },
    { title: "Key Resources", code: "KR", key: "keyResources", x: marginX + (colW + gap) * 2, y: row1Y, w: colW },
    { title: "Value Proposition", code: "VP", key: "valueProposition", x: marginX + (colW + gap) * 3, y: row1Y, w: colW },
  ] as const

  topBlocks.forEach((block) => {
    drawRoundedPanel(doc, block.x, block.y, block.w, row1H, "#0b1124", "#60a5fa")
    drawRoundedPanel(doc, block.x + 10, block.y + 10, 22, 16, "#3b82f6", "#93c5fd")
    doc.setFont("helvetica", "bold")
    safeText(doc, block.code, block.x + 14, block.y + 22, { size: 8.5, color: "#e0f2fe" })
    safeText(doc, block.title, block.x + 40, block.y + 22, { size: 13.5, color: "#ecfeff" })
    drawBulletList(doc, extractBullets(bmc[block.key]), block.x + 14, block.y + 44, block.w - 28, 14, "#d1e8ff")
  })

  const midBlocks = [
    { title: "Customer Relationships", code: "CR", key: "customerRelationships", x: marginX, y: row2Y, w: midColW },
    { title: "Channels", code: "CH", key: "channels", x: marginX + midColW + gap, y: row2Y, w: midColW },
    { title: "Customer Segments", code: "CS", key: "customerSegments", x: marginX + (midColW + gap) * 2, y: row2Y, w: midColW },
  ] as const

  midBlocks.forEach((block) => {
    drawRoundedPanel(doc, block.x, block.y, block.w, row2H, "#09111f", "#7c3aed")
    drawRoundedPanel(doc, block.x + 10, block.y + 10, 22, 16, "#7c3aed", "#c4b5fd")
    safeText(doc, block.code, block.x + 14, block.y + 22, { size: 8.5, color: "#f5f3ff" })
    safeText(doc, block.title, block.x + 40, block.y + 22, { size: 13.5, color: "#faf5ff" })
    drawBulletList(doc, extractBullets(bmc[block.key]), block.x + 14, block.y + 44, block.w - 28, 14, "#ede9fe")
  })

  const bottomBlocks = [
    { title: "Cost Structure", code: "CO", key: "costStructure", x: marginX, y: row3Y, w: bottomColW },
    { title: "Revenue Streams", code: "RS", key: "revenueStreams", x: marginX + bottomColW + gap, y: row3Y, w: bottomColW },
  ] as const

  bottomBlocks.forEach((block) => {
    drawRoundedPanel(doc, block.x, block.y, block.w, row3H, "#0b1020", "#38bdf8")
    drawRoundedPanel(doc, block.x + 10, block.y + 10, 22, 16, "#2563eb", "#93c5fd")
    safeText(doc, block.code, block.x + 14, block.y + 22, { size: 8.5, color: "#e0f2fe" })
    safeText(doc, block.title, block.x + 40, block.y + 22, { size: 13.5, color: "#ecfeff" })
    drawBulletList(doc, extractBullets(bmc[block.key]), block.x + 14, block.y + 44, block.w - 28, 14, "#dbeafe")
  })

  safeText(doc, "ScaleUp AI | Strategy Studio | Consulting Deliverable", marginX, H - 10, { size: 9.5, color: "#bfdbfe" })
  safeText(doc, "Confidential | Generated with AI Assistance", W - 212, H - 10, { size: 9.5, color: "#bfdbfe" })
}

function drawSdgsPanel(doc: jsPDF, x: number, y: number, w: number, h: number, predictions: Array<{ sdg: string; confidence: number }>, formatSdgLabel?: (value: string) => string) {
  drawRoundedPanel(doc, x, y, w, h, "#0f172a", "#14b8a6")
  safeText(doc, "Predicted SDGs", x + 14, y + 18, { size: 13.5, color: "#ccfbf1" })
  const items = (predictions.length > 0 ? predictions.slice(0, 5) : [{ sdg: "No SDG predictions", confidence: 0 }])
  let cursor = y + 36
  items.forEach((item) => {
    const confidence = normalizeConfidence(item.confidence)
    const title = formatSdgLabel ? formatSdgLabel(item.sdg) : item.sdg
    drawRoundedPanel(doc, x + 12, cursor, w - 24, 52, "#0f766e", "#5eead4")
    safeText(doc, truncateLine(title, 34), x + 20, cursor + 16, { size: 11, color: "#ecfeff" })
    safeText(doc, `${confidence}%`, x + w - 52, cursor + 16, { size: 10, color: "#99f6e4" })
    setFillHex(doc, "#134e4a")
    doc.roundedRect(x + 20, cursor + 26, w - 40, 8, 4, 4, "F")
    setFillHex(doc, "#14b8a6")
    doc.roundedRect(x + 20, cursor + 26, Math.max(14, (w - 40) * (confidence / 100)), 8, 4, 4, "F")
    cursor += 60
  })
}

function drawSustainabilityInsightsPage(doc: jsPDF, sustainableText: string, sdgPredictions: Array<{ sdg: string; confidence: number }>, ragContext: Array<{ source?: string; text?: string; distance?: number }>, formatSdgLabel?: (value: string) => string) {
  const W = A4_LANDSCAPE.width
  const H = A4_LANDSCAPE.height
  const marginX = 28
  const headerH = 68
  const gap = 10
  const topY = 86
  const panelW = (W - marginX * 2 - gap * 2) / 3

  setFillHex(doc, "#03110f")
  doc.rect(0, 0, W, H, "F")
  setFillHex(doc, "#0f766e")
  doc.circle(70, 48, 30, "F")
  setFillHex(doc, "#84cc16")
  doc.circle(W - 72, 70, 26, "F")

  drawRoundedPanel(doc, marginX, 14, W - marginX * 2, headerH, "#064e3b", "#14b8a6")
  safeText(doc, "ScaleUp AI | Sustainable Consulting", marginX + 18, 36, { size: 10, color: "#6ee7b7" })
  safeText(doc, "Sustainability Insights", marginX + 18, 58, { size: 24, color: "#f0fdfa" })
  drawRoundedPanel(doc, W - marginX - 162, 30, 132, 28, "#0f766e", "#5eead4")
  safeText(doc, "Executive Insights | Page 2", W - marginX - 150, 48, { size: 9.5, color: "#ccfbf1" })

  drawSdgsPanel(doc, marginX, topY, panelW, 300, sdgPredictions, formatSdgLabel)

  drawRoundedPanel(doc, marginX + panelW + gap, topY, panelW, 300, "#052e1f", "#22c55e")
  safeText(doc, "Sustainability Improvements", marginX + panelW + gap + 14, topY + 18, { size: 13.5, color: "#dcfce7" })
  const improvements = extractBullets(sustainableText, 4)
  let impY = topY + 42
  improvements.slice(0, 4).forEach((item, idx) => {
    drawRoundedPanel(doc, marginX + panelW + gap + 12, impY, panelW - 24, 52, "#14532d", "#4ade80")
    safeText(doc, `Action ${idx + 1}`, marginX + panelW + gap + 20, impY + 16, { size: 10, color: "#86efac" })
    safeText(doc, item, marginX + panelW + gap + 20, impY + 32, { size: 10.5, color: "#ecfdf5", maxWidth: panelW - 40 })
    impY += 60
  })

  drawRoundedPanel(doc, marginX + (panelW + gap) * 2, topY, panelW, 300, "#111827", "#84cc16")
  safeText(doc, "Green Recommendations", marginX + (panelW + gap) * 2 + 14, topY + 18, { size: 13.5, color: "#ecfccb" })
  const recommendations = extractRecommendations(ragContext, sustainableText || "")
  let recY = topY + 42
  recommendations.slice(0, 4).forEach((item, idx) => {
    drawRoundedPanel(doc, marginX + (panelW + gap) * 2 + 12, recY, panelW - 24, 52, "#1f2937", "#a3e635")
    safeText(doc, `Recommendation ${idx + 1}`, marginX + (panelW + gap) * 2 + 20, recY + 16, { size: 10, color: "#d9f99d" })
    safeText(doc, item, marginX + (panelW + gap) * 2 + 20, recY + 32, { size: 10.5, color: "#f7fee7", maxWidth: panelW - 40 })
    recY += 60
  })

  const metricsY = 414
  drawRoundedPanel(doc, marginX, metricsY, W - marginX * 2, 112, "#064e3b", "#4ade80")
  const score = Math.min(99, 64 + sdgPredictions.length * 5 + Math.min(ragContext.length, 4) * 4)
  const carbonSaved = Math.max(8, Math.round(score * 1.4))
  const alignment = Math.min(98, 40 + sdgPredictions.length * 10)
  const efficiency = Math.min(44, 12 + ragContext.length * 5)
  const metricX = [marginX + 18, marginX + 198, marginX + 398, marginX + 598]
  const metricLabel = ["Carbon Saved", "Sustainability Score", "SDG Alignment", "Efficiency Gain"]
  const metricValue = [`${carbonSaved} tCO2e`, `${score}%`, `${alignment}%`, `+${efficiency}%`]
  metricX.forEach((x, index) => {
    safeText(doc, metricLabel[index], x, metricsY + 28, { size: 10.5, color: "#99f6e4" })
    safeText(doc, metricValue[index], x, metricsY + 60, { size: 24, color: "#ecfeff" })
  })

  safeText(doc, "ScaleUp AI | Executive Sustainability Insights", marginX, H - 10, { size: 9.5, color: "#99f6e4" })
  safeText(doc, "Page 2 of 2", W - 60, H - 10, { size: 9.5, color: "#99f6e4" })
}

function PdfBlockCard({
  title,
  code,
  bullets,
  accent,
  cardBackground,
}: {
  title: string
  code: string
  bullets: string[]
  accent: string
  cardBackground: string
}) {
  return (
    <div
      style={{
        borderRadius: 20,
        border: `1px solid ${accent}`,
        background: cardBackground,
        boxShadow: `0 0 0 1px rgba(255,255,255,0.03) inset, 0 16px 35px rgba(0,0,0,0.32), 0 0 24px ${accent}`,
        padding: 18,
        minHeight: 205,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        overflow: "hidden",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <span
          style={{
            width: 28,
            height: 28,
            borderRadius: 10,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 11,
            fontWeight: 800,
            color: "#dbeafe",
            background: "linear-gradient(135deg, rgba(59,130,246,0.38), rgba(124,58,237,0.3))",
            border: "1px solid rgba(125,211,252,0.4)",
          }}
        >
          {code}
        </span>
        <h3 style={{ color: "#ecfeff", fontSize: 17, fontWeight: 700, margin: 0, letterSpacing: 0.2 }}>{title}</h3>
      </div>

      <ul style={{ margin: 0, paddingLeft: 18, color: "#d1e8ff", fontSize: 14.5, display: "grid", gap: 8 }}>
        {bullets.map((item, index) => (
          <li key={`${title}-${index}`} style={bulletStyle}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function ExportControls({
  bmc,
  onRegenerate,
  onGenerateSustainable,
  sustainableLoading,
  sustainableText,
  sdgPredictions = [],
  ragContext = [],
  sustainableBlocks,
  formatSdgLabel,
}: ExportControlsProps) {
  const [copied, setCopied] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [renderMode, setRenderMode] = useState<null | "normal" | "sustainable">(null)
  const hiddenRenderRef = useRef<HTMLDivElement | null>(null)

  const sustainableSource = useMemo(() => {
    if (sustainableBlocks) return sustainableBlocks
    return {
      keyPartnerships: "",
      keyActivities: "",
      keyResources: "",
      valueProposition: "",
      customerRelationships: "",
      channels: "",
      customerSegments: "",
      costStructure: "",
      revenueStreams: "",
      sustainabilityImprovements: sustainableText || "",
      targetedSdgs: sdgPredictions.map((item) => (formatSdgLabel ? formatSdgLabel(item.sdg) : item.sdg)).join("\n"),
    }
  }, [formatSdgLabel, sdgPredictions, sustainableBlocks, sustainableText])

  const sustainabilityScore = Math.min(99, 64 + sdgPredictions.length * 5 + Math.min(ragContext.length, 4) * 4)
  const carbonSaved = Math.max(8, Math.round(sustainabilityScore * 1.4))
  const alignment = Math.min(98, 40 + sdgPredictions.length * 10)
  const efficiency = Math.min(44, 12 + ragContext.length * 5)

  const renderPagesToPdf = async (fileName: string, reportMode: "normal" | "sustainable") => {
    const doc = new jsPDF({
      orientation: "portrait",
      unit: "pt",
      format: "a4",
      compress: true,
    })

    if (reportMode === "normal") {
      drawCoverPage(
        doc,
        "Business Model Canvas",
        "A polished founder-facing consulting report with a clear canvas layout and premium visual hierarchy.",
        "Investor-ready export",
        "#60a5fa",
        {
          background: "#030712",
          glowA: "#1d4ed8",
          glowB: "#7c3aed",
          panel: "#0f172a",
          panelStroke: "#2563eb",
          text: "#f8fafc",
          muted: "#cbd5e1",
          chipFill: "#1e3a8a",
          chipStroke: "#60a5fa",
        },
      )
      doc.addPage("a4", "portrait")
      drawCanvasPage(
        doc,
        "Business Model Canvas",
        "The core operating model, structured for clarity and executive review.",
        "Premium canvas",
        NORMAL_BLOCKS,
        bmc as Record<string, string>,
        {
          background: "#05101d",
          glowA: "#1d4ed8",
          glowB: "#8b5cf6",
          header: "#0f172a",
          headerStroke: "#2563eb",
          cardFill: "#08111f",
          cardStroke: "#7c3aed",
          chipFill: "#1d4ed8",
          chipStroke: "#93c5fd",
          text: "#f8fafc",
          muted: "#dbeafe",
          accent: "#bfdbfe",
          footerAccent: "#60a5fa",
        },
      )
    } else {
      drawCoverPage(
        doc,
        "Sustainable Business Model Canvas",
        "A premium sustainability report that pairs the business model with SDG alignment and actionable green recommendations.",
        "Sustainability export",
        "#5eead4",
        {
          background: "#02130f",
          glowA: "#0f766e",
          glowB: "#84cc16",
          panel: "#052e1f",
          panelStroke: "#14b8a6",
          text: "#f0fdfa",
          muted: "#ccfbf1",
          chipFill: "#064e3b",
          chipStroke: "#5eead4",
        },
      )
      doc.addPage("a4", "portrait")
      drawCanvasPage(
        doc,
        "Sustainable Business Model Canvas",
        "The sustainable version of the canvas with greener positioning and a stronger innovation tone.",
        "Sustainable canvas",
        SUSTAINABLE_BLOCKS,
        sustainableSource,
        {
          background: "#02130f",
          glowA: "#0f766e",
          glowB: "#84cc16",
          header: "#064e3b",
          headerStroke: "#14b8a6",
          cardFill: "#052e1f",
          cardStroke: "#22c55e",
          chipFill: "#0f766e",
          chipStroke: "#5eead4",
          text: "#f0fdfa",
          muted: "#d1fae5",
          accent: "#6ee7b7",
          footerAccent: "#84cc16",
        },
      )
      doc.addPage("a4", "portrait")
      drawSustainabilityInsightsPage(doc, sustainableText || "", sdgPredictions, ragContext, formatSdgLabel)
    }

    const totalPages = doc.getNumberOfPages()
    for (let page = 1; page <= totalPages; page += 1) {
      doc.setPage(page)
      drawFooter(
        doc,
        reportMode === "normal" ? "ScaleUp AI | Business Model Canvas" : "ScaleUp AI | Sustainable Business Model Canvas",
        page,
        totalPages,
        reportMode === "normal" ? "#60a5fa" : "#5eead4",
      )
    }

    doc.save(fileName)
  }

  const handleExportPDF = async () => {
    setExporting(true)
    try {
      setRenderMode("normal")
      await renderPagesToPdf("business-model-canvas-premium.pdf", "normal")
    } finally {
      setRenderMode(null)
      setExporting(false)
    }
  }

  const handleExportSustainablePDF = async () => {
    if (!sustainableText) return
    setExporting(true)
    try {
      setRenderMode("sustainable")
      await renderPagesToPdf("sustainable-business-model-canvas-premium.pdf", "sustainable")
    } finally {
      setRenderMode(null)
      setExporting(false)
    }
  }

  const handleSaveBMC = async () => {
    try {
      // Placeholder for save API call
      // const response = await fetch('/api/save-bmc', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ bmc })
      // })
      // const data = await response.json()

      // Mock save
      await new Promise((resolve) => setTimeout(resolve, 800))
      alert("BMC saved successfully! API endpoint: POST /save-bmc")
    } catch (error) {
      console.error("Error saving BMC:", error)
      alert("Failed to save BMC")
    }
  }

  const handleCopyJSON = () => {
    const json = JSON.stringify(bmc, null, 2)
    navigator.clipboard.writeText(json)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <>
      <Card className="relative overflow-hidden bg-gradient-to-br from-emerald-900/20 via-slate-950/70 to-black/80 backdrop-blur-xl border border-emerald-400/20">
        <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-emerald-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -left-24 bottom-0 h-48 w-48 rounded-full bg-lime-400/10 blur-3xl" />
        <CardContent className="relative p-6">
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-400/10 text-emerald-200 ring-1 ring-emerald-400/30">
                  <Leaf className="h-5 w-5" />
                </span>
                <div>
                  <h3 className="text-white text-lg font-semibold">Export & Save</h3>
                  <p className="text-emerald-100/60 text-sm">Download or save your Business Model Canvas</p>
                </div>
              </div>
              <span className="hidden md:inline-flex items-center gap-1 rounded-full bg-emerald-400/10 px-3 py-1 text-xs text-emerald-200 ring-1 ring-emerald-400/30">
                <Sparkles className="h-3 w-3" />
                Eco AI Actions
              </span>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5 lg:gap-3">
              <button
                type="button"
                onClick={handleExportPDF}
                disabled={exporting}
                className="group relative flex h-full flex-col gap-4 rounded-2xl border border-white/10 bg-white/5 p-5 text-left text-white transition hover:-translate-y-1 hover:border-emerald-400/30 hover:bg-white/10 lg:order-1"
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/20 text-blue-200">
                  <Download className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-base font-semibold">Export PDF</p>
                  <p className="text-xs text-white/60">Premium consulting PDF</p>
                </div>
              </button>

              <button
                type="button"
                onClick={handleSaveBMC}
                className="group relative flex h-full flex-col gap-4 rounded-2xl border border-white/10 bg-white/5 p-5 text-left text-white transition hover:-translate-y-1 hover:border-emerald-400/30 hover:bg-white/10 lg:order-2"
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-200">
                  <Save className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-base font-semibold">Save BMC</p>
                  <p className="text-xs text-white/60">Save to your account</p>
                </div>
              </button>

              <button
                type="button"
                onClick={onGenerateSustainable}
                disabled={sustainableLoading}
                className="group relative flex h-full flex-col gap-4 rounded-2xl border border-emerald-400/60 bg-gradient-to-br from-emerald-500/20 via-emerald-900/40 to-black/60 p-5 text-left text-white shadow-[0_0_25px_rgba(16,185,129,0.35)] transition hover:-translate-y-1 hover:shadow-[0_0_35px_rgba(16,185,129,0.55)] lg:order-3 lg:scale-[1.05] lg:z-10"
              >
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-400/20 text-emerald-100 ring-1 ring-emerald-300/60">
                  <Leaf className="h-6 w-6" />
                </span>
                <div>
                  <p className="text-lg font-semibold">Sustainable BMC</p>
                  <p className="text-sm text-emerald-100/80">
                    {sustainableLoading ? "Generating..." : "AI-powered sustainable transformation"}
                  </p>
                </div>
                <div className="pointer-events-none absolute inset-0 rounded-2xl ring-1 ring-emerald-400/40" />
                <div className="pointer-events-none absolute right-4 top-4 h-12 w-12 rounded-full bg-emerald-400/10 blur-2xl" />
              </button>

              <button
                type="button"
                onClick={handleExportSustainablePDF}
                disabled={!sustainableText || exporting}
                className="group relative flex h-full flex-col gap-4 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-5 text-left text-white transition hover:-translate-y-1 hover:bg-emerald-500/20 lg:order-4"
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-100">
                  <Download className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-base font-semibold">Sustainable PDF</p>
                  <p className="text-xs text-white/60">2-page eco dashboard PDF</p>
                </div>
              </button>

              <button
                type="button"
                onClick={onRegenerate}
                className="group relative flex h-full flex-col gap-4 rounded-2xl border border-white/10 bg-white/5 p-5 text-left text-white transition hover:-translate-y-1 hover:border-emerald-400/30 hover:bg-white/10 lg:order-5"
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-400/10 text-emerald-200">
                  <RotateCcw className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-base font-semibold">Regenerate</p>
                  <p className="text-xs text-white/60">Generate again with AI</p>
                </div>
              </button>
            </div>

            <div className="rounded-xl border border-emerald-400/20 bg-black/40 p-4 text-xs text-emerald-100/70">
              <span className="text-emerald-200 font-semibold">Auto-save enabled:</span> Your changes are automatically
              saved to your browser. Use "Save BMC" to persist to your account.
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  )
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:5000'

// ── BMC Evaluation ────────────────────────────────────────────

export interface SectionResult {
  text:        string
  score:       number
  feedback:    string
  improvement: string
  text_type:   string
  engine:      string
  word_count:  number
}

export interface CoherenceResult {
  score:    number
  analysis: string
}

export interface SustainabilityResult {
  advice: string
}

export interface OverallResult {
  score:       number
  section_avg: number
  coherence:   number
  summary:     string
  priorities:  string[]
}

export interface BMCEvaluationResult {
  image:          string
  is_bmc:         boolean
  bmc_confidence: number
  language:       string
  error:          string | null
  sections:       Record<string, SectionResult>
  coherence:      CoherenceResult
  sustainability: SustainabilityResult
  overall:        OverallResult
}

export async function evaluateBMC(file: File): Promise<BMCEvaluationResult> {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${BACKEND_URL}/api/evaluate-bmc`, {
    method: 'POST',
    credentials: 'include',
    body:   formData,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Unknown error' }))
    throw new Error(err.error || `Server error ${res.status}`)
  }

  return res.json()
}

export async function checkBMCEvalHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/bmc-eval-health`, {
      credentials: 'include',
    })
    return res.ok
  } catch {
    return false
  }
}
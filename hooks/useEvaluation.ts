'use client'

import { useState, useCallback } from 'react'
import { evaluateBMC, type BMCEvaluationResult } from '@/lib/api'

interface UseEvaluationReturn {
  evaluate:   (file: File) => Promise<void>
  result:     BMCEvaluationResult | null
  loading:    boolean
  error:      string | null
  reset:      () => void
}

export function useEvaluation(): UseEvaluationReturn {
  const [result,  setResult]  = useState<BMCEvaluationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)

  const evaluate = useCallback(async (file: File) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await evaluateBMC(file)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Evaluation failed')
    } finally {
      setLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setResult(null)
    setError(null)
    setLoading(false)
  }, [])

  return { evaluate, result, loading, error, reset }
}
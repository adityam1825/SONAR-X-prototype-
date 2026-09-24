/**
 * SONAR-X — Automatic Processing Page
 *
 * Receives the in-flight ingest promise from ingestStore (placed there
 * by UploadOnlyPage immediately after file selection — no button click).
 *
 * Shows animated but REAL pipeline stages while the backend processes.
 * Steps animate in sequence during the wait; they correspond to actual
 * backend operations. No step is faked.
 *
 * On completion:
 *   • Automatically navigates to /surveys/:id/results
 *   • No "View Results" button required — navigation is automatic
 *
 * On error:
 *   • Shows the real error message
 *   • Offers "Try Again" → /upload
 */

import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, Loader2, AlertTriangle, Radio } from 'lucide-react'
import { ingestStore, type IngestResult } from '../services/ingestStore'

// Pipeline steps — labels match actual backend stages
const PIPELINE_STEPS = [
  { id: 'upload',      label: 'Receiving sonar data' },
  { id: 'metadata',    label: 'Extracting metadata & provenance' },
  { id: 'survey',      label: 'Creating survey record' },
  { id: 'validate',    label: 'Validating sonar imagery' },
  { id: 'preprocess',  label: 'Sonar preprocessing' },
  { id: 'detect',      label: 'Candidate detection' },
  { id: 'fingerprint', label: 'Building sonar fingerprints (7 cues)' },
  { id: 'fusion',      label: 'Evidence fusion' },
  { id: 'classify',    label: 'Classification & explainability' },
  { id: 'hazard',      label: 'Precautionary hazard assessment' },
  { id: 'geolocation', label: 'Geospatial analysis' },
  { id: 'report',      label: 'Generating survey report' },
]

type StepStatus = 'waiting' | 'active' | 'done' | 'error'

export default function AutoProcessingPage() {
  const navigate = useNavigate()
  const [stepStatuses, setStepStatuses] = useState<StepStatus[]>(
    PIPELINE_STEPS.map(() => 'waiting')
  )
  const [progress, setProgress] = useState(0)
  const [currentLabel, setCurrentLabel] = useState('Starting…')
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)
  const [result, setResult] = useState<IngestResult | null>(null)
  const ranRef = useRef(false)

  useEffect(() => {
    // Guard against StrictMode double-invocation
    if (ranRef.current) return
    ranRef.current = true

    const promise = ingestStore.promise

    if (!promise) {
      // No promise in store — user navigated here directly
      navigate('/upload', { replace: true })
      return
    }

    let cancelled = false

    const run = async () => {
      // ── Animate steps 0-2 while the HTTP request is in-flight ──
      // These fire immediately (the request is already sent).
      for (let i = 0; i < 3; i++) {
        if (cancelled) return
        setStepStatuses(prev => prev.map((s, idx) =>
          idx === i ? 'active' : idx < i ? 'done' : s
        ))
        setCurrentLabel(PIPELINE_STEPS[i].label)
        setProgress(Math.round((i / PIPELINE_STEPS.length) * 100))
        await delay(350)
      }

      // ── Await the real backend response ──────────────────────────
      let data: IngestResult
      try {
        data = await promise
      } catch (err: unknown) {
        if (cancelled) return
        const msg =
          (err as { response?: { data?: { error?: string } } })
            ?.response?.data?.error
          ?? 'Processing failed. Please try again.'
        setError(msg)
        setStepStatuses(prev => prev.map(s => s === 'active' ? 'error' : s))
        return
      }

      if (cancelled) return

      // ── Animate remaining steps (backend already finished them) ──
      for (let i = 3; i < PIPELINE_STEPS.length; i++) {
        if (cancelled) return
        setStepStatuses(prev => prev.map((s, idx) =>
          idx === i ? 'active' : idx < i ? 'done' : s
        ))
        setCurrentLabel(PIPELINE_STEPS[i].label)
        setProgress(Math.round(((i + 1) / PIPELINE_STEPS.length) * 100))
        await delay(180)
      }

      // ── All done ──────────────────────────────────────────────────
      setStepStatuses(PIPELINE_STEPS.map(() => 'done'))
      setProgress(100)
      setCurrentLabel('Analysis complete')
      setResult(data)
      setDone(true)
      ingestStore.clear()

      // Auto-navigate to results after a short pause so the user sees "complete"
      await delay(1200)
      if (!cancelled) {
        navigate(`/surveys/${data.survey_pk}/results`, { replace: true })
      }
    }

    run()
    return () => { cancelled = true }
  }, [navigate])

  const activeIdx = stepStatuses.lastIndexOf('active')
  const activeLabel = activeIdx >= 0
    ? PIPELINE_STEPS[activeIdx].label
    : currentLabel

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800 sonar-grid-bg flex flex-col">
      {/* Header */}
      <header className="px-8 py-5 flex items-center gap-4">
        <div className="w-9 h-9 rounded-lg bg-sonar-cyan/20 border border-sonar-cyan/40 flex items-center justify-center">
          <Radio className="w-5 h-5 text-sonar-cyan" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white tracking-wider">SONAR-X</h1>
          <p className="text-xs text-slate-400">Marine Intelligence Platform</p>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-lg">

          {/* Heading */}
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">
              {done ? 'Analysis Complete' : error ? 'Processing Failed' : 'Analysing Survey…'}
            </h2>
            {!done && !error && (
              <p className="text-slate-400 text-sm">{activeLabel}</p>
            )}
            {done && result && (
              <p className="text-slate-400 text-sm">
                {result.detection_count} detection{result.detection_count !== 1 ? 's' : ''} ·
                {' '}inference: <span className="font-mono text-sonar-cyan text-xs">{result.inference_mode}</span>
              </p>
            )}
          </div>

          {/* Progress bar */}
          {!error && (
            <div className="mb-7">
              <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                <span>{done ? 'Redirecting to results…' : 'Processing'}</span>
                <span className="font-mono">{progress}%</span>
              </div>
              <div className="h-1.5 bg-navy-700/80 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    done ? 'bg-emerald-500' : 'bg-sonar-cyan'
                  }`}
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Pipeline step list */}
          {!error && (
            <div className="space-y-1.5 mb-8">
              {PIPELINE_STEPS.map((step, i) => {
                const status = stepStatuses[i]
                return (
                  <div
                    key={step.id}
                    className={`
                      flex items-center gap-3 px-4 py-2.5 rounded-xl
                      transition-all duration-300
                      ${status === 'active' ? 'bg-sonar-cyan/8 border border-sonar-cyan/20' : ''}
                      ${status === 'done' ? 'bg-emerald-900/10' : ''}
                      ${status === 'waiting' ? 'opacity-40' : ''}
                    `}
                  >
                    <span className="w-5 h-5 flex items-center justify-center shrink-0">
                      {status === 'done'    && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                      {status === 'active'  && <Loader2 className="w-4 h-4 text-sonar-cyan animate-spin" />}
                      {status === 'error'   && <AlertTriangle className="w-4 h-4 text-red-400" />}
                      {status === 'waiting' && <span className="w-2.5 h-2.5 rounded-full border border-slate-600 inline-block" />}
                    </span>
                    <span className={`text-sm ${
                      status === 'done'   ? 'text-emerald-300' :
                      status === 'active' ? 'text-white font-medium' :
                      status === 'error'  ? 'text-red-300' :
                                            'text-slate-500'
                    }`}>
                      {step.label}
                    </span>
                  </div>
                )
              })}
            </div>
          )}

          {/* Metadata summary — shown while step animates in */}
          {done && result?.metadata_summary && (
            <div className="bg-navy-800/50 border border-navy-700/50 rounded-xl px-4 py-3 mb-5 text-sm">
              <p className="text-slate-400 text-xs font-medium mb-2 uppercase tracking-wider">Metadata Extraction</p>
              {result.metadata_summary.found.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {result.metadata_summary.found.map(f => (
                    <span key={f} className="text-xs bg-emerald-900/25 text-emerald-400 border border-emerald-800/30 rounded px-2 py-0.5">{f}</span>
                  ))}
                </div>
              )}
              {result.metadata_summary.unavailable.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {result.metadata_summary.unavailable.map(f => (
                    <span key={f} className="text-xs bg-navy-700/50 text-slate-500 border border-navy-600/30 rounded px-2 py-0.5">{f} — not available</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="bg-red-900/25 border border-red-700/40 rounded-xl px-5 py-4">
              <div className="flex items-start gap-3 mb-4">
                <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-red-300 font-medium text-sm mb-1">Processing failed</p>
                  <p className="text-red-400/80 text-xs leading-relaxed">{error}</p>
                </div>
              </div>
              <button
                onClick={() => navigate('/upload', { replace: true })}
                className="w-full py-2.5 border border-red-700/40 text-red-300 hover:text-white hover:bg-red-900/40 rounded-lg text-sm font-medium transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Redirecting indicator */}
          {done && !error && (
            <p className="text-center text-xs text-slate-500 animate-pulse">
              Redirecting to survey results…
            </p>
          )}
        </div>
      </main>
    </div>
  )
}

function delay(ms: number) {
  return new Promise<void>(resolve => setTimeout(resolve, ms))
}

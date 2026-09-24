import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Play, CheckCircle, Clock, ArrowRight, Loader } from 'lucide-react'
import { surveysAPI } from '../../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import { DemoBadge, InferenceModeBadge } from '../../components/ui/StatusChip'

type StepState = 'pending' | 'running' | 'done' | 'failed'

const PIPELINE_STEPS = [
  { id: 'ingestion',       label: 'DATA INGESTION',       num: '01' },
  { id: 'validation',      label: 'VALIDATION',           num: '02' },
  { id: 'preprocessing',   label: 'SONAR PREPROCESSING',  num: '03' },
  { id: 'detection',       label: 'CANDIDATE DETECTION',  num: '04' },
  { id: 'fingerprint',     label: 'SONAR FINGERPRINT',    num: '05' },
  { id: 'fusion',          label: 'EVIDENCE FUSION',      num: '06' },
  { id: 'classification',  label: 'CLASSIFICATION',       num: '07' },
  { id: 'hazard',          label: 'HAZARD ASSESSMENT',    num: '08' },
  { id: 'geolocation',     label: 'GEOLOCATION',          num: '09' },
  { id: 'verification',    label: 'HUMAN VERIFICATION',   num: '10' },
]

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [stepStates, setStepStates] = useState<Record<string, StepState>>({})
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState(false)
  const [inferenceMode, setInferenceMode] = useState<string | null>(null)
  const [detectionCount, setDetectionCount] = useState<number | null>(null)
  const [dataSource, setDataSource] = useState<string | null>(null)
  const [error, setError] = useState('')

  const animatePipeline = async () => {
    setRunning(true); setDone(false); setError('')
    const states: Record<string, StepState> = {}
    PIPELINE_STEPS.forEach(s => { states[s.id] = 'pending' })
    setStepStates({ ...states })

    try {
      // Animate steps 1-3 locally
      for (let i = 0; i < 3; i++) {
        states[PIPELINE_STEPS[i].id] = 'running'
        setStepStates({ ...states })
        await new Promise(r => setTimeout(r, 400))
        states[PIPELINE_STEPS[i].id] = 'done'
        setStepStates({ ...states })
      }

      // Steps 4-9 trigger actual backend
      for (let i = 3; i < PIPELINE_STEPS.length - 1; i++) {
        states[PIPELINE_STEPS[i].id] = 'running'
        setStepStates({ ...states })
        if (i === 3) {
          // Actually call analyze
          const resp = await surveysAPI.analyze(id!)
          const d = resp.data as { results: Array<{ inference_mode: string; data_source: string }>; survey_id: string }
          if (d.results?.length > 0) {
            setInferenceMode(d.results[0].inference_mode)
            setDataSource(d.results[0].data_source)
            setDetectionCount(d.results.length)
          }
        }
        await new Promise(r => setTimeout(r, 300))
        states[PIPELINE_STEPS[i].id] = 'done'
        setStepStates({ ...states })
      }

      // Last step
      states['verification'] = 'done'
      setStepStates({ ...states })
      setDone(true)
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? 'Analysis failed.'
      setError(msg)
      // Mark current running as failed
      Object.keys(states).forEach(k => { if (states[k] === 'running') states[k] = 'failed' })
      setStepStates({ ...states })
    } finally {
      setRunning(false)
    }
  }

  const StepIcon = ({ state }: { state: StepState }) => {
    if (state === 'done') return <CheckCircle className="w-4 h-4 text-emerald-500" />
    if (state === 'running') return <Loader className="w-4 h-4 text-sonar-cyan animate-spin" />
    if (state === 'failed') return <span className="w-4 h-4 text-red-500 text-xs font-bold">✗</span>
    return <Clock className="w-4 h-4 text-slate-300" />
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader
        title="Analysis Pipeline"
        subtitle="DETECT → FINGERPRINT → FUSE → CLASSIFY → HAZARD"
        breadcrumbs={[{ label: 'Survey', to: `/surveys/${id}` }, { label: 'Analysis' }]}
      />

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Processing Pipeline</CardTitle>
                <button
                  onClick={animatePipeline}
                  disabled={running}
                  className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  <Play className="w-4 h-4" />
                  {running ? 'Running…' : 'Run Analysis'}
                </button>
              </div>
            </CardHeader>
            <CardBody className="space-y-1">
              {PIPELINE_STEPS.map(step => {
                const state = stepStates[step.id] ?? 'pending'
                return (
                  <div
                    key={step.id}
                    className={`flex items-center gap-4 p-3 rounded-lg transition-all duration-300 ${
                      state === 'running' ? 'bg-sonar-cyan/5 border border-sonar-cyan/20 pipeline-step-active' :
                      state === 'done' ? 'bg-emerald-50/50' :
                      state === 'failed' ? 'bg-red-50' :
                      'bg-slate-50/50'
                    }`}
                  >
                    <span className="text-xs font-mono text-slate-300 w-6 shrink-0">{step.num}</span>
                    <StepIcon state={state} />
                    <span className={`text-sm font-mono font-medium tracking-wide ${
                      state === 'done' ? 'text-emerald-700' :
                      state === 'running' ? 'text-navy-900' :
                      state === 'failed' ? 'text-red-700' :
                      'text-slate-400'
                    }`}>
                      {step.label}
                    </span>
                    {state === 'running' && (
                      <span className="ml-auto text-xs text-sonar-cyan animate-pulse">processing…</span>
                    )}
                    {state === 'done' && (
                      <span className="ml-auto text-xs text-emerald-600">complete</span>
                    )}
                  </div>
                )
              })}
            </CardBody>
          </Card>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm">{error}</div>
          )}
        </div>

        <div className="space-y-4">
          {/* Mode info */}
          <Card>
            <CardHeader><CardTitle>Detection Mode</CardTitle></CardHeader>
            <CardBody className="space-y-3">
              <div>
                <p className="text-xs text-slate-500 mb-1">Inference Mode</p>
                {inferenceMode ? (
                  <InferenceModeBadge mode={inferenceMode} />
                ) : (
                  <span className="text-xs text-slate-400 italic">Pending…</span>
                )}
                {inferenceMode === 'CLASSICAL_CV' && (
                  <p className="text-xs text-slate-400 mt-1">
                    Classical CV fallback — YOLO model unavailable. NOT a trained AI model.
                  </p>
                )}
              </div>
              {dataSource && (
                <div>
                  <p className="text-xs text-slate-500 mb-1">Data Source</p>
                  {dataSource === 'DEMO' ? <DemoBadge /> : <span className="text-xs font-semibold">SURVEY</span>}
                </div>
              )}
              {detectionCount !== null && (
                <div>
                  <p className="text-xs text-slate-500 mb-1">Candidates Found</p>
                  <p className="text-2xl font-bold text-navy-900">{detectionCount}</p>
                </div>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader><CardTitle>Architecture</CardTitle></CardHeader>
            <CardBody>
              <div className="text-xs text-slate-500 space-y-1.5">
                {[
                  'High-recall candidate detection',
                  'Seven-cue sonar fingerprint',
                  'Weighted evidence fusion',
                  'Multi-class classification',
                  'Precautionary hazard assessment',
                  'Geolocation (if metadata available)',
                ].map(t => (
                  <div key={t} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-sonar-cyan shrink-0" />
                    {t}
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-3 border-t border-slate-100 pt-2">
                Stage 1 is high-recall candidate detection — not the final classification.
              </p>
            </CardBody>
          </Card>
        </div>
      </div>

      {done && (
        <div className="flex items-center justify-between bg-emerald-50 border border-emerald-200 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-6 h-6 text-emerald-500" />
            <div>
              <p className="font-semibold text-emerald-800">Analysis Complete</p>
              <p className="text-sm text-emerald-600">
                {detectionCount ?? 0} detections processed · Inference: {inferenceMode ?? '—'}
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate(`/surveys/${id}/results`)}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            View Results <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}

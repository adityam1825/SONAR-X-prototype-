import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { CheckCircle, XCircle, AlertTriangle, Play, ArrowRight } from 'lucide-react'
import { sonarAPI } from '../../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import type { ValidationResult, ValidationCheck } from '../../types'

function CheckRow({ check }: { check: ValidationCheck }) {
  const icons = {
    PASS: <CheckCircle className="w-4 h-4 text-emerald-500" />,
    FAIL: <XCircle className="w-4 h-4 text-red-500" />,
    WARN: <AlertTriangle className="w-4 h-4 text-amber-500" />,
    SKIP: <span className="w-4 h-4 text-slate-300 text-xs">—</span>,
  }
  const colors = {
    PASS: 'text-emerald-700',
    FAIL: 'text-red-700',
    WARN: 'text-amber-700',
    SKIP: 'text-slate-400',
  }
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-slate-50 last:border-0">
      <div className="flex items-center gap-3">
        {icons[check.status]}
        <span className="text-sm text-slate-700">{check.name}</span>
        {check.note && <span className="text-xs text-slate-400">({check.note})</span>}
      </div>
      <div className="flex items-center gap-2">
        {check.value && <span className="text-xs font-mono text-slate-500">{check.value}</span>}
        <span className={`text-xs font-semibold ${colors[check.status]}`}>{check.status}</span>
      </div>
    </div>
  )
}

export default function ValidationPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [fileId, setFileId] = useState('')
  const [result, setResult] = useState<ValidationResult | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  const runValidation = async () => {
    if (!fileId.trim()) { setError('Enter a file ID to validate.'); return }
    setRunning(true); setError('')
    try {
      const resp = await sonarAPI.validate(fileId)
      setResult(resp.data as ValidationResult)
    } catch (e: unknown) {
      setError((e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? 'Validation failed.')
    } finally { setRunning(false) }
  }

  const resultColors = {
    VALID: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    WARNING: 'bg-amber-50 border-amber-200 text-amber-700',
    INVALID: 'bg-red-50 border-red-200 text-red-700',
  }
  const resultIcons = {
    VALID: <CheckCircle className="w-6 h-6 text-emerald-500" />,
    WARNING: <AlertTriangle className="w-6 h-6 text-amber-500" />,
    INVALID: <XCircle className="w-6 h-6 text-red-500" />,
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <PageHeader
        title="Validation Engine"
        subtitle="Validate sonar file quality and metadata"
        breadcrumbs={[{ label: 'Survey', to: `/surveys/${id}` }, { label: 'Validation' }]}
      />

      <Card>
        <CardHeader><CardTitle>File Validation</CardTitle></CardHeader>
        <CardBody className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">File ID (UUID)</label>
            <input
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-ocean-500"
              value={fileId}
              onChange={e => setFileId(e.target.value)}
              placeholder="Enter file UUID from upload…"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            onClick={runValidation}
            disabled={running}
            className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Play className="w-4 h-4" />
            {running ? 'Validating…' : 'Run Validation'}
          </button>
        </CardBody>
      </Card>

      {result && (
        <>
          <div className={`border rounded-xl p-5 ${resultColors[result.result]}`}>
            <div className="flex items-center gap-3">
              {resultIcons[result.result]}
              <div>
                <p className="font-bold text-lg">{result.result}</p>
                <p className="text-sm">{result.filename}</p>
              </div>
            </div>
            {result.warnings.length > 0 && (
              <ul className="mt-3 space-y-1">
                {result.warnings.map((w, i) => <li key={i} className="text-sm">⚠ {w}</li>)}
              </ul>
            )}
            {result.errors.length > 0 && (
              <ul className="mt-3 space-y-1">
                {result.errors.map((e, i) => <li key={i} className="text-sm">✗ {e}</li>)}
              </ul>
            )}
          </div>

          <Card>
            <CardHeader><CardTitle>Validation Checks</CardTitle></CardHeader>
            <CardBody>
              {result.checks.map((c, i) => <CheckRow key={i} check={c} />)}
            </CardBody>
          </Card>

          {result.result !== 'INVALID' && (
            <div className="flex justify-end">
              <button
                onClick={() => navigate(`/surveys/${id}/preprocessing`)}
                className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                Continue to Preprocessing <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

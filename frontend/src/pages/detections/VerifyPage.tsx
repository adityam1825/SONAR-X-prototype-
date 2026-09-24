import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { CheckCircle, XCircle, AlertTriangle, ArrowUpCircle, Shield, ShieldOff } from 'lucide-react'
import { detectionsAPI } from '../../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import { ClassBadge, HazardBadge, DemoBadge } from '../../components/ui/StatusChip'
import { PageLoader } from '../../components/ui/LoadingSpinner'
import HazardPanel from '../../components/ui/HazardPanel'
import type { Detection } from '../../types'

const CLASS_OPTIONS = ['MARINE_DEBRIS', 'NATURAL_FORMATION', 'SONAR_ARTIFACT', 'UNKNOWN_ANOMALY']

export default function VerifyPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [detection, setDetection] = useState<Detection | null>(null)
  const [loading, setLoading] = useState(true)
  const [decision, setDecision] = useState('')
  const [newClass, setNewClass] = useState('')
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (!id) return
    detectionsAPI.get(id).then(r => setDetection(r.data as Detection))
      .catch(console.error).finally(() => setLoading(false))
  }, [id])

  const submit = async () => {
    if (!decision) { setError('Select a decision.'); return }
    if (decision === 'CLASS_CHANGED' && !newClass) { setError('Select the correct class.'); return }
    if (decision === 'HAZARD_DOWNGRADED' && !comment.trim()) {
      setError('A comment is required when downgrading hazard level.'); return
    }
    setSubmitting(true); setError('')
    try {
      await detectionsAPI.verify(id!, { decision, comment, new_class: newClass })
      setDone(true)
      setTimeout(() => navigate(`/detections/${id}`), 2000)
    } catch (e: unknown) {
      setError((e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? 'Verification failed.')
    } finally { setSubmitting(false) }
  }

  if (loading) return <PageLoader text="Loading detection…" />
  if (!detection) return <div className="text-center py-20 text-slate-400">Detection not found.</div>

  const actions = [
    { id: 'CONFIRMED', label: 'Confirm', icon: CheckCircle, color: 'border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100' },
    { id: 'REJECTED', label: 'Reject', icon: XCircle, color: 'border-red-200 bg-red-50 text-red-700 hover:bg-red-100' },
    { id: 'CLASS_CHANGED', label: 'Change Class', icon: AlertTriangle, color: 'border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100' },
    { id: 'ESCALATED', label: 'Escalate', icon: ArrowUpCircle, color: 'border-purple-200 bg-purple-50 text-purple-700 hover:bg-purple-100' },
    { id: 'HAZARD_CONFIRMED', label: 'Confirm Hazard', icon: Shield, color: 'border-red-300 bg-red-100 text-red-800 hover:bg-red-200' },
    { id: 'HAZARD_DOWNGRADED', label: 'Downgrade Hazard', icon: ShieldOff, color: 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100' },
  ]

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader
        title="Human Verification"
        subtitle={detection.detection_uid}
        breadcrumbs={[
          { label: 'Detection', to: `/detections/${id}` },
          { label: 'Verify' },
        ]}
      />

      {done && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 text-center">
          <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
          <p className="font-semibold text-emerald-800">Verification recorded. Redirecting…</p>
        </div>
      )}

      {!done && (
        <>
          {/* Detection summary */}
          <Card>
            <CardHeader><CardTitle>Detection Summary</CardTitle></CardHeader>
            <CardBody>
              <div className="flex items-center gap-4 flex-wrap">
                <ClassBadge c={detection.classification} />
                <HazardBadge level={detection.hazard_level} />
                {detection.data_source === 'DEMO' && <DemoBadge />}
                <span className="text-sm text-slate-600">Confidence*: <strong>{detection.confidence?.toFixed(0)}</strong></span>
                <span className="text-sm text-slate-600">FP Risk: <strong>{detection.false_positive_risk}</strong></span>
              </div>
              {detection.supporting_evidence?.length > 0 && (
                <div className="mt-3 space-y-1">
                  {detection.supporting_evidence.map((e, i) => (
                    <p key={i} className="text-xs text-emerald-700">+ {e}</p>
                  ))}
                </div>
              )}
              {detection.counter_evidence?.length > 0 && (
                <div className="mt-2 space-y-1">
                  {detection.counter_evidence.map((e, i) => (
                    <p key={i} className="text-xs text-amber-700">− {e}</p>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>

          {/* Hazard panel */}
          {detection.hazard_level !== 'NONE' && (
            <HazardPanel
              level={detection.hazard_level}
              score={detection.hazard_score}
              indicators={detection.hazard_indicators}
              limitedData={detection.hazard_limited_data}
              recommendedAction={detection.recommended_action}
            />
          )}

          {/* Decision */}
          <Card>
            <CardHeader><CardTitle>Reviewer Decision</CardTitle></CardHeader>
            <CardBody className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                {actions.map(({ id: aid, label, icon: Icon, color }) => (
                  <button
                    key={aid}
                    onClick={() => setDecision(aid)}
                    className={`flex flex-col items-center gap-2 border-2 rounded-xl p-4 transition-all ${
                      decision === aid ? `${color} ring-2 ring-offset-1` : 'border-slate-100 bg-white hover:bg-slate-50'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="text-xs font-semibold">{label}</span>
                  </button>
                ))}
              </div>

              {decision === 'CLASS_CHANGED' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Correct Classification</label>
                  <select
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-ocean-500"
                    value={newClass} onChange={e => setNewClass(e.target.value)}
                  >
                    <option value="">Select class…</option>
                    {CLASS_OPTIONS.map(c => (
                      <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Comment {decision === 'HAZARD_DOWNGRADED' && <span className="text-red-500">* Required</span>}
                </label>
                <textarea
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-ocean-500"
                  rows={3}
                  value={comment} onChange={e => setComment(e.target.value)}
                  placeholder="Add verification notes… (required for hazard downgrade)"
                />
              </div>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <div className="flex justify-end gap-3">
                <button onClick={() => navigate(-1)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">
                  Cancel
                </button>
                <button
                  onClick={submit}
                  disabled={submitting || !decision}
                  className="px-6 py-2 bg-ocean-600 hover:bg-ocean-700 disabled:opacity-60 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  {submitting ? 'Submitting…' : 'Submit Verification'}
                </button>
              </div>

              <p className="text-xs text-slate-400 border-t border-slate-100 pt-3">
                Verification decisions are stored in the audit trail with reviewer, timestamp, and comment.
              </p>
            </CardBody>
          </Card>
        </>
      )}
    </div>
  )
}
